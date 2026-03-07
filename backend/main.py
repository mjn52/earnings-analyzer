"""
StreetSignals.ai — FastAPI Backend
Wraps existing analysis engine in a REST API.
"""

from typing import Optional, List, Dict
import re
import difflib

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
from earnings_analyzer import analyze_transcript, load_lm_dictionary
from legal_context import analyze_with_legal_context
from exporters import (
    export_pdf,
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
# Overrides — fixes for scoring bugs and grading scale
# (We don't touch the sacred files; we correct in the mapping layer)
# ---------------------------------------------------------------------------

def _corrected_grade(score: float) -> str:
    """Standard academic grading scale (the sacred code's is too lenient)."""
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 73:
        return "C"
    if score >= 70:
        return "C-"
    if score >= 67:
        return "D+"
    if score >= 60:
        return "D"
    return "F"


def _corrected_red_flags_score(base_analysis: dict) -> int:
    """
    Fix the double-multiplication bug in the sacred code.

    The sacred code computes:
        red_flag_pct = (count / total) * 100   # already a percentage, e.g. 2.5
    Then scores it as:
        scores['red_flags'] = 100 - (red_flag_pct * 100)   # multiplies again!

    So even 1% red flags → 100 - 100 = 0.  We fix that here.
    A score of 100 means NO red flags (good), 0 means lots of red flags (bad).
    """
    deception = base_analysis.get("deception", {})
    red_flag_pct = deception.get("red_flag_pct", 0)
    # red_flag_pct is already multiplied by 100, so treat it as a percentage directly
    # e.g. red_flag_pct = 2.5 means 2.5% of words are red flags
    # Scale: 0% → 100, 5% → 50, 10%+ → 0
    score = max(0, min(100, round(100 - (red_flag_pct * 10))))
    return score


def _corrected_scores(base_analysis: dict) -> dict:
    """Recompute scores with the red_flags bug fixed and new grade scale."""
    raw_scores = base_analysis.get("scores", {})
    fixed_red = _corrected_red_flags_score(base_analysis)

    sentiment = round(raw_scores.get("sentiment", 0))
    confidence = round(raw_scores.get("confidence", 0))
    ownership = round(raw_scores.get("ownership", 0))
    clarity = round(raw_scores.get("clarity", 0))

    weights = {
        "sentiment": 0.25,
        "confidence": 0.25,
        "ownership": 0.15,
        "clarity": 0.15,
        "red_flags": 0.20,
    }
    overall = round(
        sentiment * weights["sentiment"]
        + confidence * weights["confidence"]
        + ownership * weights["ownership"]
        + clarity * weights["clarity"]
        + fixed_red * weights["red_flags"]
    )

    return {
        "overall": overall,
        "grade": _corrected_grade(overall),
        "sentiment": sentiment,
        "confidence": confidence,
        "ownership": ownership,
        "clarity": clarity,
        "red_flags": fixed_red,
    }


# ---------------------------------------------------------------------------
# Rewrite helpers — ensure every flagged issue gets a suggested rewrite
# ---------------------------------------------------------------------------

# Fallback rewrites for common issue types when get_suggested_rewrite() has no match
_HEDGING_REPLACEMENTS = [
    (r"\bmight\b", "will"),
    (r"\bmay\b", "will"),
    (r"\bcould\b", "can"),
    (r"\bpossibly\b", ""),
    (r"\bperhaps\b", ""),
    (r"\bpotentially\b", ""),
    (r"\bsomewhat\b", ""),
    (r"\bgenerally\b", ""),
    (r"\btypically\b", ""),
    (r"\brelatively\b", ""),
    (r"\bapproximately\b", "about"),
    (r"\bcautiously optimistic\b", "optimistic"),
    (r"\bgoing forward\b", "in the coming quarter"),
    (r"\bchallenging environment\b", "competitive market"),
    (r"\bthe company believes\b", "we believe"),
    (r"\bwe believe\b", "we see"),
    (r"\bwe think\b", "we expect"),
    (r"\bwe feel\b", "we expect"),
    (r"\bwe hope\b", "we expect"),
]


def _generate_rewrite(sentence: str, issues: list) -> str:
    """
    Always produce a rewrite. First try the sacred get_suggested_rewrite().
    If that returns nothing, apply our fallback pattern-based rewrites.
    """
    # Try the sacred rewriter first
    rewrite, changes = get_suggested_rewrite(sentence)
    if rewrite and rewrite != sentence:
        return rewrite

    # Fallback: apply hedging replacements
    result = sentence
    for pattern, replacement in _HEDGING_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Clean up extra spaces
    result = re.sub(r"\s+", " ", result).strip()
    result = re.sub(r"\s+([.,;:!?])", r"\1", result)

    if result != sentence:
        return result

    # Last resort: return original with a note
    return sentence


# ---------------------------------------------------------------------------
# Mapping helpers — transform existing output into the spec's JSON shape
# ---------------------------------------------------------------------------

def _build_flagged_issues(text: str, base_analysis: dict) -> list:
    """
    Enrich the base flagged_passages with colour and suggested rewrites.
    Always provides a suggested_rewrite for every flagged issue.
    """
    issues = []
    for fp in base_analysis.get("flagged_passages", []):
        sentence = fp["sentence"]
        color, _ = classify_sentence(sentence)
        rewrite = _generate_rewrite(sentence, fp["issues"])
        issues.append(
            {
                "sentence": sentence,
                "color": color,
                "issues": fp["issues"],
                "suggested_rewrite": rewrite,
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

    # Flatten signal objects into readable strings for the frontend
    pos_signals = []
    for s in gc.get("positive_signals", []):
        if isinstance(s, dict):
            label = s.get("signal", "")
            count = s.get("count", 0)
            pos_signals.append(f"{label} ({count}x)" if count > 1 else label)
        else:
            pos_signals.append(str(s))

    neg_signals = []
    for s in gc.get("negative_signals", []):
        if isinstance(s, dict):
            label = s.get("signal", "")
            count = s.get("count", 0)
            neg_signals.append(f"{label} ({count}x)" if count > 1 else label)
        else:
            neg_signals.append(str(s))

    detail = dict(gc)  # shallow copy so we don't mutate the original
    detail["positive_signals"] = pos_signals
    detail["negative_signals"] = neg_signals

    return {
        "clarity_score": gc.get("clarity_score", 0),
        "grade": _corrected_grade(gc.get("clarity_score", 0)),
        "detail": detail,
    }


def _build_response(
    text: str,
    base_analysis: dict,
    advanced: dict,
    session_id: str,
) -> dict:
    """Assemble the spec-compliant JSON response."""
    return {
        "scores": _corrected_scores(base_analysis),
        "flagged_issues": _build_flagged_issues(text, base_analysis),
        "analyst_qa": _build_analyst_qa(advanced),
        "negative_interpretations": advanced.get("negative_interpretations", []),
        "litigation": _build_litigation(advanced),
        "activist_triggers": _build_activist(advanced),
        "guidance_clarity": _build_guidance(advanced),
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Word export with word-level diffs (replaces sacred export_word)
# ---------------------------------------------------------------------------

def _export_word_improved(text: str, analysis: dict, output_path: str):
    """
    Word export with word-level diffs instead of full-sentence strikethrough.
    Only the changed words are marked, making it far more readable.
    """
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_COLOR_INDEX

    doc = Document()

    doc.add_heading("Earnings Script — Suggested Revisions", 0)
    doc.add_paragraph()

    # Instructions
    instructions = doc.add_paragraph()
    instructions.add_run("Instructions: ").bold = True
    instructions.add_run(
        "This document shows suggested revisions to improve your earnings script. "
        "Red strikethrough text should be removed or replaced. "
        "Green underlined text shows the suggested replacement. "
        "Accept or reject changes as appropriate for your communication style."
    )
    doc.add_paragraph()

    # Legend
    legend = doc.add_paragraph()
    legend.add_run("Legend: ").bold = True
    strike_run = legend.add_run("Strikethrough")
    strike_run.font.strike = True
    strike_run.font.color.rgb = RGBColor(180, 0, 0)
    legend.add_run(" = Remove  |  ")
    add_run = legend.add_run("Green Text")
    add_run.font.underline = True
    add_run.font.color.rgb = RGBColor(0, 128, 0)
    legend.add_run(" = Replacement")
    doc.add_paragraph()
    doc.add_paragraph("\u2500" * 50)
    doc.add_paragraph()

    # Process sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for sentence in sentences:
        if len(sentence.strip()) < 10:
            continue

        color, issues = classify_sentence(sentence)
        rewrite = _generate_rewrite(sentence, issues)

        para = doc.add_paragraph()

        if rewrite and rewrite != sentence:
            # Word-level diff
            orig_words = sentence.split()
            new_words = rewrite.split()
            matcher = difflib.SequenceMatcher(None, orig_words, new_words)

            for op, i1, i2, j1, j2 in matcher.get_opcodes():
                if op == "equal":
                    para.add_run(" ".join(orig_words[i1:i2]) + " ")
                elif op == "replace":
                    # Strikethrough the old words
                    old_run = para.add_run(" ".join(orig_words[i1:i2]) + " ")
                    old_run.font.strike = True
                    old_run.font.color.rgb = RGBColor(180, 0, 0)
                    # Green underline the new words
                    new_run = para.add_run(" ".join(new_words[j1:j2]) + " ")
                    new_run.font.underline = True
                    new_run.font.color.rgb = RGBColor(0, 128, 0)
                elif op == "delete":
                    old_run = para.add_run(" ".join(orig_words[i1:i2]) + " ")
                    old_run.font.strike = True
                    old_run.font.color.rgb = RGBColor(180, 0, 0)
                elif op == "insert":
                    new_run = para.add_run(" ".join(new_words[j1:j2]) + " ")
                    new_run.font.underline = True
                    new_run.font.color.rgb = RGBColor(0, 128, 0)

            if issues:
                comment = para.add_run("  [" + ", ".join(issues) + "]")
                comment.font.size = Pt(8)
                comment.font.italic = True
                comment.font.color.rgb = RGBColor(128, 128, 128)

        elif color in ("RED", "YELLOW") and issues:
            # No rewrite available but flagged — show with highlight + issue note
            run = para.add_run(sentence)
            if color == "RED":
                run.font.highlight_color = WD_COLOR_INDEX.PINK
            else:
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            comment = para.add_run("  [" + ", ".join(issues) + "]")
            comment.font.size = Pt(8)
            comment.font.italic = True
            comment.font.color.rgb = RGBColor(128, 128, 128)
        else:
            para.add_run(sentence)

        para.add_run(" ")

    doc.save(str(output_path))
    return output_path


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
    _export_word_improved(session["text"], session["base_analysis"], tmp.name)
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
