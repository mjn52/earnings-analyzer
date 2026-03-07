"""
StreetSignals.ai — FastAPI Backend
Wraps existing analysis engine in a REST API.
Integrates Claude for institutional-grade analyst Q&A.
"""

from typing import Optional, List, Dict
import asyncio
import re
import difflib
import logging
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os
import uuid
import json
from pathlib import Path

import httpx
import anthropic

# Existing modules — not modified
from earnings_analyzer import analyze_transcript, load_lm_dictionary
from legal_context import analyze_with_legal_context
from exporters import (
    export_pdf,
    classify_sentence,
    get_suggested_rewrite,
)
from advanced_analysis import run_advanced_analysis

logger = logging.getLogger("streetsignals")

app = FastAPI(title="StreetSignals.ai API")

# ---------------------------------------------------------------------------
# API keys from environment (set in Railway dashboard)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")

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

# ---------------------------------------------------------------------------
# Claude-powered rewrites — context-aware, respects legal language
# ---------------------------------------------------------------------------

_REWRITE_SYSTEM_PROMPT = """You are an expert IR (Investor Relations) editor reviewing an earnings call script.

Your job: Suggest targeted rewrites for flagged sentences to make management sound more confident and direct — BUT only when appropriate.

CRITICAL RULES:
1. NEVER modify safe harbor statements, forward-looking statement disclaimers, or legal boilerplate. These MUST stay exactly as written. Words like "may", "could", "might" in legal disclaimers are legally required.
2. NEVER change cautionary risk disclosures. If management is intentionally flagging a risk or uncertainty, preserve that intent.
3. ONLY rewrite hedging language that genuinely weakens the message without serving a legal or cautionary purpose.
4. Preserve grammatical correctness — every rewrite must read naturally.
5. Preserve the original meaning. Don't turn uncertain statements into definitive claims.
6. Make minimal changes — change as few words as possible.
7. If a sentence is fine as-is (legal language, appropriate caution, or already clear), return it UNCHANGED.

EXAMPLES OF WHAT TO FIX:
- "We are cautiously optimistic about growth" → "We are optimistic about growth"
- "We hope to see improvement" → "We expect to see improvement" (only if context supports it)
- Removing unnecessary filler: "somewhat", "relatively", "generally" when they add no meaning

EXAMPLES OF WHAT TO LEAVE ALONE:
- "Actual results may differ materially" — LEGAL, do not touch
- "We may not achieve the level of adoption" — INTENTIONAL RISK DISCLOSURE
- "Factors that could cause results to differ" — LEGAL, do not touch
- "We believe our approach positions us well" — APPROPRIATE, "believe" is fine here

Return ONLY valid JSON — no markdown, no code fences:
{
  "rewrites": [
    {"index": 0, "rewrite": "The rewritten sentence or exact original if no change needed"},
    {"index": 1, "rewrite": "..."}
  ]
}

The "index" must match the sentence index from the input. Include ALL sentences in the output."""


async def _generate_rewrites_with_claude(flagged_sentences: list) -> Optional[dict]:
    """
    Send all flagged sentences to Claude in one batch for context-aware rewriting.
    Returns a dict mapping sentence text → rewrite (or same text if no change).
    """
    if not ANTHROPIC_API_KEY or not flagged_sentences:
        return None

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        # Build the prompt with numbered sentences
        parts = ["Here are the flagged sentences from an earnings call script. For each one, suggest a rewrite or return it unchanged:\n"]
        for i, item in enumerate(flagged_sentences):
            parts.append(f"[{i}] Issues: {', '.join(item['issues'])}")
            parts.append(f"    Sentence: {item['sentence']}")
            parts.append("")

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=_REWRITE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n".join(parts)}],
        )

        response_text = response.content[0].text.strip()

        # Handle potential markdown code fences
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text)

        data = json.loads(response_text)
        rewrites = data.get("rewrites", [])

        # Build a mapping: original sentence → rewrite
        result = {}
        for r in rewrites:
            idx = r.get("index", -1)
            if 0 <= idx < len(flagged_sentences):
                result[flagged_sentences[idx]["sentence"]] = r.get("rewrite", flagged_sentences[idx]["sentence"])

        logger.info(f"Claude generated {len(result)} rewrites")
        return result

    except Exception as e:
        logger.error(f"Claude rewrite generation failed: {type(e).__name__}: {e}")
        return None


def _generate_rewrite_fallback(sentence: str, issues: list) -> str:
    """Simple fallback rewrite when Claude is unavailable. Returns original if no good rewrite."""
    rewrite, changes = get_suggested_rewrite(sentence)
    if rewrite and rewrite != sentence:
        return rewrite
    return sentence


# ---------------------------------------------------------------------------
# Mapping helpers — transform existing output into the spec's JSON shape
# ---------------------------------------------------------------------------

def _build_flagged_issues(text: str, base_analysis: dict, claude_rewrites: Optional[dict] = None) -> list:
    """
    Enrich the base flagged_passages with colour and suggested rewrites.
    Uses Claude rewrites when available, falls back to sacred rewriter.
    """
    issues = []
    for fp in base_analysis.get("flagged_passages", []):
        sentence = fp["sentence"]
        color, _ = classify_sentence(sentence)

        # Use Claude rewrite if available, otherwise fallback
        if claude_rewrites and sentence in claude_rewrites:
            rewrite = claude_rewrites[sentence]
        else:
            rewrite = _generate_rewrite_fallback(sentence, fp["issues"])

        # Only include rewrite if it's actually different
        issues.append(
            {
                "sentence": sentence,
                "color": color,
                "issues": fp["issues"],
                "suggested_rewrite": rewrite if rewrite != sentence else None,
            }
        )
    return issues


def _build_analyst_qa_fallback(advanced: dict) -> dict:
    """Template-based Q&A from the sacred code — used as fallback."""
    questions = advanced.get("analyst_questions", [])
    answers = advanced.get("proposed_answers", [])
    return {
        "total_questions": len(questions),
        "questions": questions,
        "answers": answers,
    }


# ---------------------------------------------------------------------------
# FMP transcript fetching — auto-pull prior earnings call transcripts
# ---------------------------------------------------------------------------

async def _fetch_prior_transcripts(ticker: str, num_quarters: int = 4) -> List[dict]:
    """Fetch the last N quarterly earnings call transcripts from Financial Modeling Prep."""
    if not FMP_API_KEY or not ticker:
        return []

    ticker = ticker.strip().upper()

    # Calculate the last N quarters
    now = datetime.now()
    quarters = []
    year, quarter = now.year, (now.month - 1) // 3  # 0-indexed current quarter
    # Start from the most recently completed quarter
    for _ in range(num_quarters):
        if quarter == 0:
            quarter = 4
            year -= 1
        quarters.append((year, quarter))
        quarter -= 1

    transcripts = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for yr, qtr in quarters:
            try:
                resp = await client.get(
                    f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}",
                    params={"quarter": qtr, "year": yr, "apikey": FMP_API_KEY},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        content = data[0].get("content", "")
                        if content and len(content) > 200:
                            transcripts.append({
                                "quarter": f"Q{qtr} {yr}",
                                "content": content,
                            })
            except Exception as e:
                logger.warning(f"FMP fetch failed for {ticker} Q{qtr} {yr}: {e}")
                continue

    return transcripts


# ---------------------------------------------------------------------------
# Claude-powered analyst Q&A generation
# ---------------------------------------------------------------------------

_QA_SYSTEM_PROMPT = """You are a panel of senior sell-side equity research analysts preparing for an upcoming earnings call Q&A session. You have deep expertise in financial analysis and have covered this company for years.

Your task: Based on the company's prepared remarks (and optionally prior call transcripts), generate the toughest, most probing questions that analysts will ask — and draft proposed management responses.

QUESTION GUIDELINES:
- Ask specific, data-driven questions (reference actual numbers and claims from the script)
- Follow up on commitments or guidance from prior calls when available
- Probe hedging language, vague promises, or evasive areas
- Ask about topics conspicuously absent from the prepared remarks
- Challenge overly optimistic framing with requests for specifics
- Each question should feel like it comes from a real analyst who does this for a living

ANSWER GUIDELINES:
- Responses should be what a well-prepared IR/management team would say
- Be direct, confident, and data-driven — avoid corporate waffle
- Reference specific metrics, timelines, and commitments where possible
- Flag areas where management should have data ready but shouldn't speculate

Return ONLY valid JSON in this exact format (no markdown, no code fences):
{
  "questions": [
    {
      "question": "The specific analyst question",
      "topic": "Short topic label (e.g., Revenue, Margins, Guidance)",
      "confidence": 0.85
    }
  ],
  "answers": [
    {
      "answer_strategy": "Short strategy label (e.g., Redirect to Data, Acknowledge & Pivot)",
      "proposed_answer": "The full proposed management response",
      "key_data_points": ["Data point 1 to have ready", "Data point 2"],
      "caution_notes": "What to avoid saying or any risk in this area"
    }
  ]
}

Generate 8-10 questions, ordered by likelihood of being asked. The questions and answers arrays must have the same length (one answer per question)."""


async def _generate_qa_with_claude(
    current_script: str,
    prior_transcripts: List[dict],
    base_analysis: dict,
) -> Optional[dict]:
    """Generate institutional-grade analyst Q&A using Claude API."""
    if not ANTHROPIC_API_KEY:
        return None

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        # Build the user prompt
        parts = []

        # Include prior transcripts if available
        if prior_transcripts:
            parts.append("PRIOR EARNINGS CALL TRANSCRIPTS (most recent first):")
            parts.append("=" * 60)
            for t in prior_transcripts:
                # Cap each transcript to ~5000 words to manage token usage
                words = t["content"].split()
                truncated = " ".join(words[:5000])
                parts.append(f"\n--- {t['quarter']} EARNINGS CALL ---")
                parts.append(truncated)
                if len(words) > 5000:
                    parts.append(f"[...truncated from {len(words)} words]")
            parts.append("=" * 60)
            parts.append("")

        # Include analysis context (scores and flagged issues help Claude target weak spots)
        scores = base_analysis.get("scores", {})
        parts.append("ANALYSIS CONTEXT (weak areas to probe):")
        parts.append(f"- Sentiment score: {scores.get('sentiment', 'N/A')}/100")
        parts.append(f"- Confidence score: {scores.get('confidence', 'N/A')}/100")
        parts.append(f"- Clarity score: {scores.get('clarity', 'N/A')}/100")
        flagged = base_analysis.get("flagged_passages", [])
        if flagged:
            parts.append(f"- {len(flagged)} passages flagged for hedging/vagueness")
        parts.append("")

        # The current script
        parts.append("CURRENT PREPARED REMARKS FOR UPCOMING CALL:")
        parts.append("=" * 60)
        # Cap at ~8000 words
        script_words = current_script.split()
        if len(script_words) > 8000:
            parts.append(" ".join(script_words[:8000]))
            parts.append(f"[...truncated from {len(script_words)} words]")
        else:
            parts.append(current_script)
        parts.append("=" * 60)

        parts.append("")
        if prior_transcripts:
            parts.append(
                f"You have {len(prior_transcripts)} prior call transcripts above. "
                "Reference specific prior commitments, guidance changes, and analyst concerns from those calls."
            )
        else:
            parts.append(
                "No prior transcripts available. Focus on the current prepared remarks — "
                "identify weak spots, hedging, vagueness, missing topics, and overly optimistic claims."
            )

        parts.append("\nGenerate 8-10 analyst questions with proposed management responses.")

        user_prompt = "\n".join(parts)

        # Call Claude (API data is never used for training per Anthropic's API terms)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=_QA_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Parse the JSON response
        response_text = response.content[0].text.strip()

        # Handle potential markdown code fences
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text)

        qa_data = json.loads(response_text)

        questions = qa_data.get("questions", [])
        answers = qa_data.get("answers", [])

        # Validate structure
        if not questions or not answers:
            logger.warning("Claude returned empty Q&A")
            return None

        return {
            "total_questions": len(questions),
            "questions": questions,
            "answers": answers,
            "source": "claude",
            "prior_calls_used": len(prior_transcripts),
        }

    except json.JSONDecodeError as e:
        logger.error(f"Claude Q&A JSON parse error: {e}")
        return None
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude Q&A generation failed: {e}")
        return None


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
    claude_qa: Optional[dict] = None,
    claude_rewrites: Optional[dict] = None,
) -> dict:
    """Assemble the spec-compliant JSON response."""
    return {
        "scores": _corrected_scores(base_analysis),
        "flagged_issues": _build_flagged_issues(text, base_analysis, claude_rewrites),
        "analyst_qa": claude_qa if claude_qa else _build_analyst_qa_fallback(advanced),
        "negative_interpretations": advanced.get("negative_interpretations", []),
        "litigation": _build_litigation(advanced),
        "activist_triggers": _build_activist(advanced),
        "guidance_clarity": _build_guidance(advanced),
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Word export with word-level diffs (replaces sacred export_word)
# ---------------------------------------------------------------------------

def _export_word_improved(text: str, analysis: dict, output_path: str, claude_rewrites: Optional[dict] = None):
    """
    Word export with word-level diffs instead of full-sentence strikethrough.
    Uses Claude rewrites when available for context-aware suggestions.
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

        # Use Claude rewrite if available, otherwise fallback
        if claude_rewrites and sentence in claude_rewrites:
            rewrite = claude_rewrites[sentence]
        else:
            rewrite = _generate_rewrite_fallback(sentence, issues)

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

@app.get("/api/health")
async def health():
    """Diagnostic endpoint — check if API keys are configured."""
    return {
        "status": "ok",
        "anthropic_key_set": bool(ANTHROPIC_API_KEY),
        "anthropic_key_prefix": ANTHROPIC_API_KEY[:12] + "..." if ANTHROPIC_API_KEY else "NOT SET",
        "fmp_key_set": bool(FMP_API_KEY),
    }


@app.get("/api/test-claude")
async def test_claude():
    """Test Claude API connectivity — makes a tiny call to verify the key works."""
    if not ANTHROPIC_API_KEY:
        return {"status": "error", "detail": "ANTHROPIC_API_KEY not set"}
    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say hello in exactly 5 words."}],
        )
        return {
            "status": "ok",
            "model": response.model,
            "response": response.content[0].text,
        }
    except Exception as e:
        return {"status": "error", "error_type": type(e).__name__, "detail": str(e)}


@app.post("/api/analyze")
async def analyze(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    ticker: Optional[str] = Form(None),
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

    # Run base analysis (earnings_analyzer) — synchronous, fast
    base_analysis = analyze_transcript(transcript, LM_DICT)

    # Run all advanced analyses via the wrapper — synchronous, fast
    advanced = run_advanced_analysis(transcript, base_analysis)

    # Fetch prior transcripts + generate Claude Q&A + rewrites (async, parallel)
    claude_qa = None
    claude_rewrites = None
    prior_transcripts = []
    if ANTHROPIC_API_KEY:
        logger.info(f"Claude API key present, ticker={ticker}")

        # Fetch prior call transcripts if ticker provided
        if ticker and ticker.strip():
            try:
                prior_transcripts = await _fetch_prior_transcripts(ticker.strip())
                logger.info(
                    f"Fetched {len(prior_transcripts)} prior transcripts for {ticker.strip().upper()}"
                )
            except Exception as e:
                logger.error(f"Prior transcript fetch failed: {type(e).__name__}: {e}")

        # Prepare flagged sentences for rewrite
        flagged_for_rewrite = [
            {"sentence": fp["sentence"], "issues": fp["issues"]}
            for fp in base_analysis.get("flagged_passages", [])
        ]

        # Run Claude Q&A and rewrites IN PARALLEL
        logger.info("Calling Claude for Q&A + rewrites (parallel)...")

        async def _safe_qa():
            try:
                return await _generate_qa_with_claude(transcript, prior_transcripts, base_analysis)
            except Exception as e:
                logger.error(f"Claude Q&A failed: {type(e).__name__}: {e}")
                return None

        async def _safe_rewrites():
            try:
                return await _generate_rewrites_with_claude(flagged_for_rewrite)
            except Exception as e:
                logger.error(f"Claude rewrites failed: {type(e).__name__}: {e}")
                return None

        claude_qa, claude_rewrites = await asyncio.gather(_safe_qa(), _safe_rewrites())

        if claude_qa:
            logger.info(
                f"Claude generated {claude_qa['total_questions']} questions "
                f"(used {claude_qa.get('prior_calls_used', 0)} prior calls)"
            )
        if claude_rewrites:
            logger.info(f"Claude generated {len(claude_rewrites)} rewrites")
    else:
        logger.info("No ANTHROPIC_API_KEY — using fallback Q&A and rewrites")

    # Create session
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "text": transcript,
        "base_analysis": base_analysis,
        "advanced": advanced,
        "claude_qa": claude_qa,
        "claude_rewrites": claude_rewrites,
    }

    return _build_response(transcript, base_analysis, advanced, session_id, claude_qa, claude_rewrites)


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
    _export_word_improved(
        session["text"],
        session["base_analysis"],
        tmp.name,
        session.get("claude_rewrites"),
    )
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
        session.get("claude_qa"),
        session.get("claude_rewrites"),
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
