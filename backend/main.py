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

# Load score→price impact lookup table (research-based benchmarks)
_IMPACT_TABLE_PATH = Path(__file__).parent / "data" / "score_impact_table.json"
SCORE_IMPACT_TABLE = {}
if _IMPACT_TABLE_PATH.exists():
    with open(_IMPACT_TABLE_PATH) as _f:
        SCORE_IMPACT_TABLE = json.load(_f)
    logger.info(f"Loaded score impact table ({len(SCORE_IMPACT_TABLE.get('overall_score_bins', {}))} bins)")

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
# Stock Impact Prediction (research-based)
# ---------------------------------------------------------------------------

def _get_score_bin(score: int) -> str:
    """Map a 0-100 score to its lookup table bin key."""
    bin_start = (score // 10) * 10
    bin_end = min(bin_start + 9, 100)
    if bin_start >= 90:
        return "90-100"
    return f"{bin_start}-{bin_end}"


def _predict_impact(scores: dict) -> dict:
    """
    Given analysis scores, return predicted stock price impact
    based on research-derived lookup table.

    Returns both a "current script" prediction and an "improved script"
    projection so users can see the value of making changes.
    """
    bins = SCORE_IMPACT_TABLE.get("overall_score_bins", {})
    if not bins:
        return None

    overall = scores.get("overall", 50)
    bin_key = _get_score_bin(overall)
    current_bin = bins.get(bin_key)

    if not current_bin:
        return None

    # Estimate the "improved" score: assume making all suggested changes
    # lifts the score by 10-15 points (capped at 95)
    improved_overall = min(95, overall + 12)
    improved_bin_key = _get_score_bin(improved_overall)
    improved_bin = bins.get(improved_bin_key, current_bin)

    # Find the weakest dimensions to highlight as improvement opportunities
    dimensions = ["sentiment", "confidence", "ownership", "clarity", "red_flags"]
    dim_scores = [(d, scores.get(d, 50)) for d in dimensions]
    dim_scores.sort(key=lambda x: x[1])
    weakest = [{"dimension": d, "score": s} for d, s in dim_scores[:3]]

    return {
        "current": {
            "overall_score": overall,
            "bin": bin_key,
            "label": current_bin.get("label", ""),
            "median_1d_pct": current_bin["median_1d_pct"],
            "median_2d_pct": current_bin["median_2d_pct"],
            "range_1d": [current_bin["p25_1d"], current_bin["p75_1d"]],
        },
        "improved": {
            "overall_score": improved_overall,
            "bin": improved_bin_key,
            "label": improved_bin.get("label", ""),
            "median_1d_pct": improved_bin["median_1d_pct"],
            "median_2d_pct": improved_bin["median_2d_pct"],
            "range_1d": [improved_bin["p25_1d"], improved_bin["p75_1d"]],
        },
        "improvement_delta_1d": round(improved_bin["median_1d_pct"] - current_bin["median_1d_pct"], 2),
        "weakest_dimensions": weakest,
        "disclaimer": SCORE_IMPACT_TABLE.get("disclaimer", "Historical patterns only. Not financial advice."),
    }


# ---------------------------------------------------------------------------
# Rewrite helpers — ensure every flagged issue gets a suggested rewrite
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Claude-powered rewrites — context-aware, respects legal language
# ---------------------------------------------------------------------------

_REWRITE_SYSTEM_PROMPT = """You are an expert IR (Investor Relations) editor reviewing an earnings call script.

Your job: For each flagged sentence, propose a concrete rewrite that addresses the flagged issues while respecting legal and contextual constraints.

CRITICAL RULES:
1. NEVER modify safe harbor statements, forward-looking statement disclaimers, or legal boilerplate. For these, propose a rewrite that adds context or strengthens the surrounding language while keeping the legally required words intact.
2. NEVER change cautionary risk disclosures into definitive claims. Instead, tighten the language to sound more deliberate and less uncertain.
3. Preserve grammatical correctness — every rewrite must read naturally.
4. Preserve the original meaning. Don't turn uncertain statements into definitive claims.
5. Make minimal changes — change as few words as possible.
6. EVERY sentence MUST get a rewrite that improves it, even if the improvement is subtle. No sentence should be returned unchanged.

STRATEGIES FOR DIFFERENT ISSUE TYPES:
- Hedging (unnecessary): Remove filler words like "somewhat", "relatively", "generally" when they add no meaning.
- Hedging (legal/cautionary): Keep the hedging words but tighten the sentence structure, remove redundancy, or add specificity.
- Weak verbs: "We hope" → "We expect", "We feel" → "We are confident", "We think" → "We believe"
- Vague language: Add specificity or restructure for directness.
- Safe harbor boilerplate: Rewrite surrounding context to be more direct while preserving required legal language verbatim.

EXAMPLES:
- "We are cautiously optimistic about growth" → "We are optimistic about growth"
- "We hope to see improvement" → "We expect to see improvement"
- "We believe our AI systems may be contributing to engagement" → "We believe our AI systems are contributing to engagement"
- "Actual results may differ materially from those anticipated." → "Actual results may differ materially from those anticipated, and we encourage investors to review the risk factors in our SEC filings."

Return your rewrites in this EXACT numbered format — one rewrite per line:
[0] The improved first sentence
[1] The improved second sentence

CRITICAL: Include ALL indices from the input. Every sentence MUST appear. Do NOT add any explanations, commentary, or extra text — ONLY the numbered rewrites."""


async def _generate_rewrites_with_claude(flagged_sentences: list) -> Optional[dict]:
    """
    Send all flagged sentences to Claude in one batch for context-aware rewriting.
    Returns a dict mapping sentence text → rewrite (or same text if no change).
    """
    if not ANTHROPIC_API_KEY or not flagged_sentences:
        logger.info(f"Skipping Claude rewrites: key={'set' if ANTHROPIC_API_KEY else 'MISSING'}, "
                     f"sentences={len(flagged_sentences) if flagged_sentences else 0}")
        return None

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        logger.info(f"Sending {len(flagged_sentences)} flagged sentences to Claude for rewriting")

        # Build the prompt with numbered sentences
        parts = [
            "Here are the flagged sentences from an earnings call script.",
            "For EVERY sentence, propose a concrete rewrite that addresses the flagged issues.",
            "Do NOT return any sentence unchanged.\n",
        ]
        for i, item in enumerate(flagged_sentences):
            parts.append(f"[{i}] Issues: {', '.join(item['issues'])}")
            parts.append(f"    Sentence: {item['sentence']}")
            parts.append("")

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=_REWRITE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n".join(parts)}],
        )

        response_text = response.content[0].text.strip()
        logger.info(f"Claude rewrite response: {len(response_text)} chars, "
                     f"stop_reason={response.stop_reason}")

        # Parse numbered format: [idx] rewrite text
        # Far more robust than JSON — handles preamble, code fences, partial output
        result = {}
        pattern = re.compile(r'^\[(\d+)\]\s*(.+)$', re.MULTILINE)
        for match in pattern.finditer(response_text):
            idx = int(match.group(1))
            rewrite_text = match.group(2).strip()
            if 0 <= idx < len(flagged_sentences):
                original = flagged_sentences[idx]["sentence"]
                result[original] = rewrite_text
                norm_key = ' '.join(original.split())
                if norm_key != original:
                    result[norm_key] = rewrite_text

        logger.info(f"Claude: {len(result)} rewrites parsed for {len(flagged_sentences)} sentences "
                     f"(stop_reason={response.stop_reason})")

        if not result:
            logger.error(f"0 rewrites parsed! Response starts with: {response_text[:500]}")

        return result if result else None

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
# Claude-powered negative interpretations + guidance extraction (3rd call)
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM_PROMPT = """You are a senior sell-side equity research analyst who specializes in identifying language in earnings call scripts that could be spun negatively by bearish analysts or short sellers.

You will analyze an earnings call script and provide TWO analyses:

PART 1 — NEGATIVE INTERPRETATIONS:
Identify 5-15 passages in the script that a bearish analyst could use to build a negative narrative. For each:
- Quote the problematic text (exact words from the script)
- Explain how a bear analyst would spin it
- Suggest a rewrite that neutralizes the negative spin
- Rate severity: "high" (actively harmful), "medium" (concerning), "low" (minor risk)
- Categorize: hedging_language, vague_commitments, mixed_messaging, defensiveness, omission_signal, metric_avoidance, blame_shifting, over_promising

PART 2 — GUIDANCE EXTRACTION:
Extract any forward-looking guidance, outlook, or targets from the script. Only include ACTUAL guidance — where management is providing a forecast or target for a future metric. Do NOT include past results or general commentary.
For each metric with guidance:
- Metric name (e.g., "Revenue", "EPS", "Gross Margin")
- The specific guidance value or range given
- Whether it's quantified (true = specific number/range, false = directional only like "growth" or "improvement")
- The exact quote from the script

If NO forward-looking guidance is provided in the script, return an empty array for guidance_metrics.

Return ONLY valid JSON in this exact format (no markdown, no code fences):
{
  "negative_interpretations": [
    {
      "category": "hedging_language",
      "original_text": "exact quote from script",
      "negative_spin": "How a bear analyst would frame this",
      "suggested_rewrite": "Improved version that neutralizes the spin",
      "severity": "medium"
    }
  ],
  "guidance_metrics": [
    {
      "metric": "Revenue",
      "value": "$4.2B - $4.4B",
      "quantified": true,
      "quote": "We expect revenue in the range of $4.2 billion to $4.4 billion"
    }
  ]
}"""


async def _generate_analysis_with_claude(
    script: str,
    base_negative_interps: list,
) -> Optional[dict]:
    """
    3rd parallel Claude call: generates context-aware negative interpretations
    and extracts actual guidance metrics from the script.
    """
    if not ANTHROPIC_API_KEY:
        return None

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        parts = []

        # Include base pattern-matched negative interps as context
        if base_negative_interps:
            parts.append("PATTERN-BASED FINDINGS (for context — build on these, don't just repeat them):")
            for item in base_negative_interps[:10]:
                parts.append(f"- [{item.get('severity', 'medium')}] \"{item.get('matched_text', '')}\" — {item.get('interpretation', '')}")
            parts.append("")

        # The script
        parts.append("EARNINGS CALL SCRIPT:")
        parts.append("=" * 60)
        script_words = script.split()
        if len(script_words) > 8000:
            parts.append(" ".join(script_words[:8000]))
            parts.append(f"[...truncated from {len(script_words)} words]")
        else:
            parts.append(script)
        parts.append("=" * 60)

        parts.append("\nAnalyze this script and return negative interpretations + guidance extraction as specified.")

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=_ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n".join(parts)}],
        )

        response_text = response.content[0].text.strip()

        # Handle markdown code fences
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text)

        data = json.loads(response_text)

        neg_interps = data.get("negative_interpretations", [])
        guidance = data.get("guidance_metrics", [])

        logger.info(f"Claude analysis: {len(neg_interps)} negative interps, {len(guidance)} guidance metrics")

        return {
            "negative_interpretations": neg_interps,
            "guidance_metrics": guidance,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Claude analysis JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"Claude analysis generation failed: {type(e).__name__}: {e}")
        return None


# ---------------------------------------------------------------------------
# FMP consensus estimates fetch
# ---------------------------------------------------------------------------

async def _fetch_consensus_estimates(ticker: str) -> Optional[dict]:
    """Fetch analyst consensus estimates from FMP. Returns None if unavailable."""
    if not FMP_API_KEY or not ticker:
        return None

    ticker = ticker.strip().upper()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://financialmodelingprep.com/api/v3/analyst-estimates/{ticker}",
                params={"apikey": FMP_API_KEY, "limit": 1},
            )
            if resp.status_code != 200:
                logger.warning(f"FMP consensus fetch returned {resp.status_code} for {ticker}")
                return None

            data = resp.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                return None

            est = data[0]
            return {
                "revenue": est.get("estimatedRevenueAvg"),
                "earnings": est.get("estimatedEpsAvg"),
                "net_income": est.get("estimatedNetIncomeAvg"),
                "ebitda": est.get("estimatedEbitdaAvg"),
                "sga": est.get("estimatedSgaExpenseAvg"),
                "date": est.get("date"),
                "source": "fmp",
            }
    except Exception as e:
        logger.warning(f"FMP consensus fetch failed for {ticker}: {type(e).__name__}: {e}")
        return None


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

        # Use Claude rewrite if available (try exact match, then normalized)
        rewrite = None
        if claude_rewrites:
            rewrite = claude_rewrites.get(sentence) or claude_rewrites.get(' '.join(sentence.split()))
        if not rewrite or rewrite == sentence:
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
    raw_triggers = act.get("triggers", [])

    # Map sacred code fields → frontend expected fields
    mapped = []
    for t in raw_triggers:
        category = (t.get("trigger", "") or "").replace("_", " ").title()
        concern = t.get("concern", "")
        mapped.append({
            "category": category,
            "trigger_type": category,
            "original_text": t.get("sentence", t.get("matched_text", "")),
            "matched_text": t.get("matched_text", ""),
            "activist_narrative": t.get("activist_angle", ""),
            "defense_suggestion": (
                f"Consider proactively addressing this by providing specific data points "
                f"and timeline commitments related to {concern.lower()}."
                if concern else ""
            ),
            "severity": t.get("severity", "medium"),
        })

    return {
        "risk_level": act.get("risk_level", "Low"),
        "triggers": mapped,
    }


def _build_guidance(
    advanced: dict,
    claude_guidance: Optional[list] = None,
    consensus: Optional[dict] = None,
) -> dict:
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

    # Build metrics list from Claude guidance extraction (preferred) or sacred code fallback
    metrics = []
    no_guidance_given = False

    if claude_guidance is not None:
        # Claude extracted actual guidance — use it as the source of truth
        if len(claude_guidance) == 0:
            no_guidance_given = True
        for gm in claude_guidance:
            metric_name = gm.get("metric", "Unknown")
            company_value = gm.get("value", "")
            quantified = gm.get("quantified", False)
            quote = gm.get("quote", "")

            # Try to match against consensus for status
            status = "unknown"
            consensus_value = None
            if consensus:
                consensus_value = _match_consensus(metric_name, consensus)

            if consensus_value is not None and quantified and company_value:
                status = _compare_guidance_to_consensus(company_value, consensus_value, metric_name)

            metrics.append({
                "metric": metric_name,
                "company_guidance": company_value if company_value else ("Directional" if not quantified else "—"),
                "quote": quote,
                "quantified": quantified,
                "consensus": _format_consensus(consensus_value, metric_name) if consensus_value is not None else None,
                "status": status,
            })
    else:
        # Fallback to sacred code metrics
        for m in gc.get("metrics_covered", []):
            metric_name = m.get("metric", m) if isinstance(m, dict) else str(m)
            quantified = m.get("quantified", False) if isinstance(m, dict) else False
            metrics.append({
                "metric": metric_name.title(),
                "company_guidance": "Quantified" if quantified else "Qualitative",
                "quote": "",
                "quantified": quantified,
                "consensus": None,
                "status": "unknown",
            })
        for m in gc.get("metrics_missing", []):
            metric_name = m.get("metric", m) if isinstance(m, dict) else str(m)
            metrics.append({
                "metric": metric_name.title(),
                "company_guidance": None,
                "quote": "",
                "quantified": False,
                "consensus": None,
                "status": "missing",
            })

    return {
        "clarity_score": gc.get("clarity_score", 0),
        "grade": _corrected_grade(gc.get("clarity_score", 0)),
        "metrics": metrics,
        "has_consensus": consensus is not None,
        "no_guidance_given": no_guidance_given,
        "positive_signals": pos_signals,
        "negative_signals": neg_signals,
    }


def _match_consensus(metric_name: str, consensus: dict) -> Optional[float]:
    """Match a guidance metric name to the closest FMP consensus field."""
    name_lower = metric_name.lower()
    if any(k in name_lower for k in ("revenue", "sales", "top line")):
        return consensus.get("revenue")
    if any(k in name_lower for k in ("eps", "earnings per share")):
        return consensus.get("earnings")
    if any(k in name_lower for k in ("net income",)):
        return consensus.get("net_income")
    if any(k in name_lower for k in ("ebitda",)):
        return consensus.get("ebitda")
    return None


def _format_consensus(value: Optional[float], metric_name: str) -> str:
    """Format a consensus value for display."""
    if value is None:
        return "N/A"
    name_lower = metric_name.lower()
    if any(k in name_lower for k in ("eps", "earnings per share")):
        return f"${value:.2f}"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    return f"${value:,.0f}"


def _compare_guidance_to_consensus(guidance_str: str, consensus_val: float, metric_name: str) -> str:
    """Compare guidance value to consensus. Returns status string."""
    # Try to extract a numeric value from the guidance string
    numbers = re.findall(r'[\d,]+\.?\d*', guidance_str.replace(",", ""))
    if not numbers:
        return "unknown"

    parsed = []
    for n in numbers:
        try:
            val = float(n)
            # Handle billions/millions in the original string
            if "billion" in guidance_str.lower() or "b" in guidance_str.lower():
                val *= 1_000_000_000
            elif "million" in guidance_str.lower() or "m" in guidance_str.lower():
                val *= 1_000_000
            parsed.append(val)
        except ValueError:
            continue

    if not parsed:
        return "unknown"

    # If it's a range, use the midpoint
    if len(parsed) >= 2:
        guidance_val = (parsed[0] + parsed[-1]) / 2
    else:
        guidance_val = parsed[0]

    # Normalize: if consensus is in absolute terms and guidance looks like EPS
    if consensus_val == 0:
        return "unknown"

    pct_diff = (guidance_val - consensus_val) / abs(consensus_val)

    if pct_diff > 0.02:
        return "above"
    elif pct_diff > -0.02:
        return "inline"
    elif pct_diff > -0.05:
        return "low_end"
    else:
        return "below"


def _build_response(
    text: str,
    base_analysis: dict,
    advanced: dict,
    session_id: str,
    claude_qa: Optional[dict] = None,
    claude_rewrites: Optional[dict] = None,
    claude_analysis: Optional[dict] = None,
    consensus: Optional[dict] = None,
) -> dict:
    """Assemble the spec-compliant JSON response."""
    flagged_passages = base_analysis.get("flagged_passages", [])
    scores = _corrected_scores(base_analysis)

    # Use Claude negative interps if available, fall back to sacred code pattern matches
    if claude_analysis and claude_analysis.get("negative_interpretations"):
        neg_interps = claude_analysis["negative_interpretations"]
    else:
        # Map sacred code format to frontend format
        neg_interps = []
        for item in advanced.get("negative_interpretations", []):
            neg_interps.append({
                "category": item.get("suggestion_type", "awareness"),
                "original_text": item.get("sentence", item.get("matched_text", "")),
                "negative_spin": item.get("interpretation", ""),
                "suggested_rewrite": item.get("rewrite_suggestion"),
                "severity": item.get("severity", "medium"),
            })

    # Extract Claude guidance metrics for the guidance builder
    claude_guidance = None
    if claude_analysis and "guidance_metrics" in claude_analysis:
        claude_guidance = claude_analysis["guidance_metrics"]

    return {
        "scores": scores,
        "stock_impact": _predict_impact(scores),
        "flagged_issues": _build_flagged_issues(text, base_analysis, claude_rewrites),
        "analyst_qa": claude_qa if claude_qa else _build_analyst_qa_fallback(advanced),
        "negative_interpretations": neg_interps,
        "litigation": _build_litigation(advanced),
        "activist_triggers": _build_activist(advanced),
        "guidance_clarity": _build_guidance(advanced, claude_guidance, consensus),
        "session_id": session_id,
        "_debug": {
            "flagged_passage_count": len(flagged_passages),
            "claude_rewrites_is_none": claude_rewrites is None,
            "claude_rewrites_count": len(claude_rewrites) if claude_rewrites else 0,
            "claude_analysis_available": claude_analysis is not None,
            "consensus_available": consensus is not None,
        },
    }


# ---------------------------------------------------------------------------
# Word export with word-level diffs (replaces sacred export_word)
# ---------------------------------------------------------------------------

def _export_word_improved(
    text: str,
    analysis: dict,
    output_path: str,
    claude_rewrites: Optional[dict] = None,
    advanced: Optional[dict] = None,
):
    """
    Word export with word-level diffs instead of full-sentence strikethrough.
    Uses Claude rewrites when available for context-aware suggestions.
    Includes litigation risk and activist trigger analyses.
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
        "Blue underlined text shows proposed additions or replacements. "
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
    add_run = legend.add_run("Blue Text")
    add_run.font.underline = True
    add_run.font.color.rgb = RGBColor(26, 86, 219)
    legend.add_run(" = Addition")
    doc.add_paragraph()
    doc.add_paragraph("\u2500" * 50)
    doc.add_paragraph()

    # Build rewrite lookup from flagged_passages + claude_rewrites.
    # Key insight: use the EXACT sentence strings from flagged_passages
    # (same strings sent to Claude) to look up in claude_rewrites, then
    # store with normalized keys for matching against re-split sentences.
    _passage_rewrites = {}  # norm_key → rewrite
    _flagged_count = 0
    for fp in analysis.get("flagged_passages", []):
        sent = fp["sentence"]
        _flagged_count += 1
        rewrite = None
        if claude_rewrites:
            # Exact match — these keys come from the same flagged_passages list
            rewrite = claude_rewrites.get(sent)
        if not rewrite or rewrite == sent:
            rewrite = _generate_rewrite_fallback(sent, fp["issues"])
        if rewrite and rewrite != sent:
            _passage_rewrites[' '.join(sent.split())] = rewrite

    # Also add any claude_rewrites that aren't from flagged_passages
    # (these come from classify_sentence()-flagged sentences added at analyze time)
    _extra_from_claude = 0
    if claude_rewrites:
        for sent, rewrite in claude_rewrites.items():
            norm_key = ' '.join(sent.split())
            if norm_key not in _passage_rewrites and rewrite and rewrite != sent:
                _passage_rewrites[norm_key] = rewrite
                _extra_from_claude += 1

    logger.info(f"Word export: {_flagged_count} flagged passages, "
                 f"{len(_passage_rewrites)} with rewrites "
                 f"({_extra_from_claude} extra from classify_sentence via claude_rewrites), "
                 f"claude_rewrites={'None' if claude_rewrites is None else len(claude_rewrites)}")

    # Process sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    _exact_hits = 0
    _fuzzy_hits = 0

    for sentence in sentences:
        if len(sentence.strip()) < 10:
            continue

        color, issues = classify_sentence(sentence)

        # Step 1: Try normalized exact match
        norm_sentence = ' '.join(sentence.split())
        rewrite = _passage_rewrites.get(norm_sentence)

        if rewrite:
            _exact_hits += 1
        elif color in ("RED", "YELLOW") and _passage_rewrites:
            # Step 2: Fuzzy match — sentence boundaries from regex splitter
            # may differ from sacred code's splitter
            best_ratio = 0
            best_rw = None
            for key, rw in _passage_rewrites.items():
                if abs(len(key) - len(norm_sentence)) > 30:
                    continue
                ratio = difflib.SequenceMatcher(None, norm_sentence, key).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_rw = rw
            if best_ratio > 0.8:
                rewrite = best_rw
                _fuzzy_hits += 1

        if not rewrite or rewrite == sentence:
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
                    new_run.font.color.rgb = RGBColor(26, 86, 219)
                elif op == "delete":
                    old_run = para.add_run(" ".join(orig_words[i1:i2]) + " ")
                    old_run.font.strike = True
                    old_run.font.color.rgb = RGBColor(180, 0, 0)
                elif op == "insert":
                    new_run = para.add_run(" ".join(new_words[j1:j2]) + " ")
                    new_run.font.underline = True
                    new_run.font.color.rgb = RGBColor(26, 86, 219)

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

    logger.info(f"Word export complete: {_exact_hits} exact + {_fuzzy_hits} fuzzy matches "
                 f"out of {len(sentences)} sentences")

    # --- Litigation Risk Analysis Section ---
    if advanced:
        lit = advanced.get("litigation_risk", {})
        findings = lit.get("findings", [])
        has_safe_harbor = lit.get("has_safe_harbor", False)

        if findings or not has_safe_harbor:
            doc.add_paragraph()
            doc.add_paragraph("\u2500" * 50)
            doc.add_heading("Litigation Risk Analysis", level=1)

            # Safe harbor status
            sh_para = doc.add_paragraph()
            if has_safe_harbor:
                sh_run = sh_para.add_run("\u2713 Safe Harbor Statement Present")
                sh_run.font.color.rgb = RGBColor(5, 150, 105)  # success green
                sh_run.bold = True
            else:
                sh_run = sh_para.add_run("\u2717 No Safe Harbor Statement Detected")
                sh_run.font.color.rgb = RGBColor(220, 38, 38)  # danger red
                sh_run.bold = True
                rec = doc.add_paragraph()
                rec.add_run(
                    "Recommendation: Add a PSLRA-compliant forward-looking statement disclaimer "
                    "at the beginning of the prepared remarks."
                ).font.italic = True

            risk_level = lit.get("risk_level", "Low")
            risk_score = lit.get("risk_score", 0)
            doc.add_paragraph(f"Overall Risk: {risk_level} (Score: {risk_score}/100)")

            # Individual findings
            for f in findings:
                doc.add_paragraph()
                issue_para = doc.add_paragraph()
                issue_run = issue_para.add_run(f.get("issue", "Finding"))
                issue_run.bold = True
                severity = f.get("severity", "medium")
                sev_run = issue_para.add_run(f"  [{severity.upper()}]")
                sev_run.font.size = Pt(9)
                sev_run.font.italic = True
                if severity in ("critical", "high"):
                    sev_run.font.color.rgb = RGBColor(220, 38, 38)
                elif severity == "medium":
                    sev_run.font.color.rgb = RGBColor(217, 119, 6)
                else:
                    sev_run.font.color.rgb = RGBColor(107, 114, 128)

                if f.get("detail"):
                    doc.add_paragraph(f["detail"])
                if f.get("sentence"):
                    quote_para = doc.add_paragraph()
                    quote_run = quote_para.add_run(f'"{f["sentence"]}"')
                    quote_run.font.italic = True
                    quote_run.font.color.rgb = RGBColor(107, 114, 128)
                if f.get("recommendation"):
                    rec_para = doc.add_paragraph()
                    rec_para.add_run("Recommendation: ").bold = True
                    rec_para.add_run(f["recommendation"])

        # --- Activist Vulnerability Analysis Section ---
        act = advanced.get("activist_triggers", {})
        triggers = act.get("triggers", [])

        if triggers:
            doc.add_paragraph()
            doc.add_paragraph("\u2500" * 50)
            doc.add_heading("Activist Vulnerability Analysis", level=1)

            risk_level = act.get("risk_level", "Low")
            doc.add_paragraph(f"Overall Risk: {risk_level}")

            for t in triggers:
                doc.add_paragraph()
                trigger_name = (t.get("trigger", "") or "").replace("_", " ").title()
                t_para = doc.add_paragraph()
                t_run = t_para.add_run(trigger_name)
                t_run.bold = True
                severity = t.get("severity", "medium")
                sev_run = t_para.add_run(f"  [{severity.upper()}]")
                sev_run.font.size = Pt(9)
                sev_run.font.italic = True

                if t.get("sentence"):
                    quote_para = doc.add_paragraph()
                    quote_run = quote_para.add_run(f'"{t["sentence"]}"')
                    quote_run.font.italic = True
                    quote_run.font.color.rgb = RGBColor(107, 114, 128)
                if t.get("activist_angle"):
                    angle_para = doc.add_paragraph()
                    angle_para.add_run("Activist Narrative: ").bold = True
                    angle_para.add_run(t["activist_angle"])
                if t.get("concern"):
                    def_para = doc.add_paragraph()
                    def_para.add_run("Defense: ").bold = True
                    def_para.add_run(
                        f"Consider proactively addressing this by providing specific data points "
                        f"and timeline commitments related to {t['concern'].lower()}."
                    )

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


@app.get("/api/debug-session/{session_id}")
async def debug_session(session_id: str):
    """Diagnostic: shows rewrite pipeline status for a session."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    claude_rewrites = session.get("claude_rewrites")
    flagged = session["base_analysis"].get("flagged_passages", [])

    # Check how many flagged passages would get rewrites
    match_count = 0
    if claude_rewrites and flagged:
        for fp in flagged:
            sent = fp["sentence"]
            if sent in claude_rewrites or ' '.join(sent.split()) in claude_rewrites:
                match_count += 1

    # Count how many classify_sentence would flag beyond flagged_passages
    text = session.get("text", "")
    classify_extra = 0
    flagged_norm = {' '.join(fp["sentence"].split()) for fp in flagged}
    if text:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            if len(sent.strip()) < 10:
                continue
            norm = ' '.join(sent.split())
            if norm in flagged_norm:
                continue
            color, _ = classify_sentence(sent)
            if color in ("RED", "YELLOW"):
                classify_extra += 1

    return {
        "flagged_passage_count": len(flagged),
        "classify_sentence_extra": classify_extra,
        "total_sent_to_claude": len(flagged) + classify_extra,
        "flagged_sample": [fp["sentence"][:100] for fp in flagged[:5]],
        "claude_rewrites_is_none": claude_rewrites is None,
        "claude_rewrites_count": len(claude_rewrites) if claude_rewrites else 0,
        "claude_rewrite_keys_sample": [k[:100] for k in list(claude_rewrites.keys())[:5]] if claude_rewrites else [],
        "matched_rewrites": match_count,
        "claude_qa_source": session.get("claude_qa", {}).get("source", "fallback") if session.get("claude_qa") else "fallback",
    }


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
        fname = (file.filename or "").lower()
        if fname.endswith(".docx"):
            import io
            from docx import Document
            doc = Document(io.BytesIO(raw))
            transcript = "\n".join(p.text for p in doc.paragraphs)
        elif fname.endswith(".pdf"):
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            transcript = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
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

    # Fetch prior transcripts + generate Claude Q&A + rewrites + analysis (async, parallel)
    claude_qa = None
    claude_rewrites = None
    claude_analysis = None
    consensus = None
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

        # Prepare flagged sentences for rewrite — start with flagged_passages
        flagged_for_rewrite = [
            {"sentence": fp["sentence"], "issues": fp["issues"]}
            for fp in base_analysis.get("flagged_passages", [])
        ]

        # Also include sentences that classify_sentence() would flag in the Word export
        # but aren't in flagged_passages — ensures ALL highlighted sentences get rewrites
        _fp_count = len(flagged_for_rewrite)
        existing_norm = {' '.join(fp["sentence"].split()) for fp in flagged_for_rewrite}
        all_sentences = re.split(r"(?<=[.!?])\s+", transcript)
        for sent in all_sentences:
            if len(sent.strip()) < 10:
                continue
            norm_sent = ' '.join(sent.split())
            if norm_sent in existing_norm:
                continue
            color, issues = classify_sentence(sent)
            if color in ("RED", "YELLOW") and issues:
                flagged_for_rewrite.append({"sentence": sent, "issues": issues})
                existing_norm.add(norm_sent)

        logger.info(f"Sentences for rewrite: {len(flagged_for_rewrite)} total "
                     f"({_fp_count} from flagged_passages + "
                     f"{len(flagged_for_rewrite) - _fp_count} from classify_sentence)")

        # Cap at 80 sentences to manage Claude API costs/token limits
        if len(flagged_for_rewrite) > 80:
            logger.warning(f"Capping rewrite batch from {len(flagged_for_rewrite)} to 80 sentences")
            flagged_for_rewrite = flagged_for_rewrite[:80]

        # Run Claude Q&A, rewrites, and analysis IN PARALLEL (3 calls)
        logger.info("Calling Claude for Q&A + rewrites + analysis (parallel)...")

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

        async def _safe_analysis():
            try:
                base_neg = advanced.get("negative_interpretations", [])
                return await _generate_analysis_with_claude(transcript, base_neg)
            except Exception as e:
                logger.error(f"Claude analysis failed: {type(e).__name__}: {e}")
                return None

        async def _safe_consensus():
            try:
                if ticker and ticker.strip():
                    return await _fetch_consensus_estimates(ticker.strip())
                return None
            except Exception as e:
                logger.warning(f"Consensus fetch failed: {type(e).__name__}: {e}")
                return None

        claude_qa, claude_rewrites, claude_analysis, consensus = await asyncio.gather(
            _safe_qa(), _safe_rewrites(), _safe_analysis(), _safe_consensus()
        )

        if claude_qa:
            logger.info(
                f"Claude generated {claude_qa['total_questions']} questions "
                f"(used {claude_qa.get('prior_calls_used', 0)} prior calls)"
            )
        if claude_rewrites:
            logger.info(f"Claude generated {len(claude_rewrites)} rewrites")
        if claude_analysis:
            logger.info(f"Claude analysis: {len(claude_analysis.get('negative_interpretations', []))} neg interps, "
                         f"{len(claude_analysis.get('guidance_metrics', []))} guidance metrics")
        if consensus:
            logger.info(f"FMP consensus available for {ticker}: date={consensus.get('date')}")
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
        "claude_analysis": claude_analysis,
        "consensus": consensus,
    }

    return _build_response(
        transcript, base_analysis, advanced, session_id,
        claude_qa, claude_rewrites, claude_analysis, consensus,
    )


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
        session.get("advanced"),
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
        session.get("claude_analysis"),
        session.get("consensus"),
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
