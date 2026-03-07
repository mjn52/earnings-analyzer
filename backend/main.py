"""
StreetSignals.ai — FastAPI Backend
Wraps existing analysis engine in a REST API.
"""

from typing import Optional, List, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os
import uuid
import json
from pathlib import Path

# Existing modules — not modified
from earnings_analyzer import analyze_transcript, load_lm_dictionary, get_grade
from legal_context import analyze_with_legal_context
from exporters import (
    export_pdf,
    export_word,
    classify_sentence,
    get_suggested_rewrite,
)
from advanced_analysis import run_advanced_analysis

app = FastAPI(title="StreetSignals.ai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Loughran-McDonald dictionary once at startup
LM_DICT = load_lm_dictionary(Path(__file__).parent / "LM_MasterDictionary.csv")

# In-memory session store — keyed by session_id
SESSIONS: dict = {}


# ---------------------------------------------------------------------------
# Mapping helpers — transform existing output into the spec's JSON shape
# ---------------------------------------------------------------------------

def _build_flagged_issues(text: str, base_analysis: dict) -> list[dict]:
    """
    Enrich the base flagged_passages with colour and suggested rewrites
    using the exporters module (which already knows how to classify and rewrite).
    """
    issues = []
    for fp in base_analysis.get("flagged_passages", []):
        sentence = fp["sentence"]
        color, _ = classify_sentence(sentence)
        rewrite, _ = get_suggested_rewrite(sentence)
        issues.append(
            {
                "sentence": sentence,
                "color": color,
                "issues": fp["issues"],
                "suggested_rewrite": rewrite or sentence,
            }
        )
    return issues


def _build_analyst_qa(advanced: dict) -> dict:
    questions = advanced.get("analyst_questions", [])
    answers = advanced.get("proposed_answers", [])
    return {
        "total_questions": len(questions),
        "questions": questions,
        "answers": answers,
    }


def _build_litigation(advanced: dict) -> dict:
    lit = advanced.get("litigation_risk", {})
    return {
        "risk_level": lit.get("risk_level", "Low"),
        "risk_score": lit.get("risk_score", 0),
        "has_safe_harbor": lit.get("has_safe_harbor", False),
        "findings": lit.get("findings", []),
    }


def _build_activist(advanced: dict) -> dict:
    act = advanced.get("activist_triggers", {})
    return {
        "risk_level": act.get("risk_level", "Low"),
        "triggers": act.get("triggers", []),
    }


def _build_guidance(advanced: dict) -> dict:
    gc = advanced.get("guidance_clarity", {})
    return {
        "clarity_score": gc.get("clarity_score", 0),
        "grade": gc.get("grade", "N/A"),
        "detail": gc,
    }


def _build_response(
    text: str,
    base_analysis: dict,
    advanced: dict,
    session_id: str,
) -> dict:
    """Assemble the spec-compliant JSON response."""
    scores = base_analysis.get("scores", {})
    return {
        "scores": {
            "overall": round(scores.get("overall", 0)),
            "grade": get_grade(scores.get("overall", 0)),
            "sentiment": round(scores.get("sentiment", 0)),
            "confidence": round(scores.get("confidence", 0)),
            "ownership": round(scores.get("ownership", 0)),
            "clarity": round(scores.get("clarity", 0)),
            "red_flags": round(scores.get("red_flags", 0)),
        },
        "flagged_issues": _build_flagged_issues(text, base_analysis),
        "analyst_qa": _build_analyst_qa(advanced),
        "negative_interpretations": advanced.get("negative_interpretations", []),
        "litigation": _build_litigation(advanced),
        "activist_triggers": _build_activist(advanced),
        "guidance_clarity": _build_guidance(advanced),
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/analyze")
async def analyze(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    # Extract transcript text from either source
    transcript = None
    if file is not None:
        raw = await file.read()
        if file.filename and file.filename.endswith(".docx"):
            # Handle .docx via python-docx
            import io
            from docx import Document

            doc = Document(io.BytesIO(raw))
            transcript = "\n".join(p.text for p in doc.paragraphs)
        else:
            transcript = raw.decode("utf-8", errors="replace")
    elif text:
        transcript = text

    if not transcript or len(transcript.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Please provide a transcript of at least 100 characters.",
        )

    # Run base analysis (earnings_analyzer)
    base_analysis = analyze_transcript(transcript, LM_DICT)

    # Run all advanced analyses via the wrapper
    advanced = run_advanced_analysis(transcript, base_analysis)

    # Create session
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "text": transcript,
        "base_analysis": base_analysis,
        "advanced": advanced,
    }

    return _build_response(transcript, base_analysis, advanced, session_id)


@app.get("/api/export/pdf/{session_id}")
async def get_pdf(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    export_pdf(session["text"], session["base_analysis"], tmp.name)
    return FileResponse(
        tmp.name,
        media_type="application/pdf",
        filename="streetsignals_report.pdf",
    )


@app.get("/api/export/word/{session_id}")
async def get_word(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.close()
    export_word(session["text"], session["base_analysis"], tmp.name)
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="streetsignals_report.docx",
    )


@app.get("/api/export/json/{session_id}")
async def get_json(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _build_response(
        session["text"],
        session["base_analysis"],
        session["advanced"],
        session_id,
    )


# ---------------------------------------------------------------------------
# Serve React frontend (production — built files in ./static)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React app — all non-API routes return index.html."""
        index = STATIC_DIR / "index.html"
        return HTMLResponse(index.read_text())

