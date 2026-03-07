#!/usr/bin/env python3
"""
Guidance Credibility Score

Analyzes guidance language for credibility signals:
- Guidance range width (wider = less confident)
- Qualifier density in guidance sections
- Specificity vs hedging balance
- Track record indicators (if history provided)
- Assumption transparency
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GuidanceElement:
    """A guidance statement with analysis."""
    text: str
    metric: str  # revenue, EPS, margin, etc.
    range_low: Optional[float]
    range_high: Optional[float]
    range_width_pct: Optional[float]  # width as % of midpoint
    qualifier_count: int
    qualifiers_found: List[str]
    specificity_score: int  # 1-5, higher = more specific
    credibility_flags: List[str]


# Guidance metric patterns
GUIDANCE_PATTERNS = {
    'revenue': r'(revenue|sales|top.?line)\s*(guidance|outlook|expect|range|target)',
    'eps': r'(EPS|earnings per share|diluted earnings)\s*(guidance|outlook|expect|range|target)',
    'margin': r'(margin|gross margin|operating margin|EBITDA margin)\s*(guidance|outlook|expect)',
    'cash_flow': r'(cash flow|FCF|free cash flow|operating cash flow)\s*(guidance|outlook|expect)',
    'growth': r'(growth|year.over.year|YoY)\s*(guidance|outlook|expect|rate)',
    'capex': r'(capex|capital expenditure|investments?)\s*(guidance|outlook|expect)',
}

# Range extraction patterns
RANGE_PATTERNS = [
    r'\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B|K)?\s*(?:to|-)\s*\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B|K)?',
    r'([\d,]+(?:\.\d+)?)\s*%?\s*(?:to|-)\s*([\d,]+(?:\.\d+)?)\s*%',
    r'between\s*\$?([\d,]+(?:\.\d+)?)\s*(?:million|billion|M|B|K)?\s*and\s*\$?([\d,]+(?:\.\d+)?)',
]

# Qualifiers that reduce credibility
CREDIBILITY_QUALIFIERS = [
    (r'\b(approximately|about|around|roughly|nearly)\b', 'approximation'),
    (r'\b(may|might|could|should)\b', 'possibility'),
    (r'\b(expect|anticipate|believe|estimate)\b', 'expectation'),
    (r'\b(assuming|if|provided|contingent|dependent)\b', 'conditionality'),
    (r'\b(current|existing|present)\s+(conditions?|environment|market)', 'environment_dependency'),
    (r'\b(uncertain|visibility|volatile|dynamic)\b', 'uncertainty'),
    (r'\b(subject to|excluding|barring|absent)\b', 'exclusion'),
]

# Positive credibility signals
CREDIBILITY_BOOSTERS = [
    (r'\b(raising|increasing|narrowing)\s+(guidance|outlook|range)', 'guidance_raise'),
    (r'\b(confident|conviction|clear visibility)\b', 'confidence'),
    (r'\b(track record|history of|consistently)\b', 'track_record'),
    (r'\b(reaffirm|confirm|reiterate).*guidance\b', 'reaffirmation'),
    (r'\b(ahead of|above|beat|exceed)\s*(plan|expectations?|guidance)', 'outperformance'),
]

# Range width thresholds (as % of midpoint)
RANGE_WIDTH_THRESHOLDS = {
    'tight': 5,      # < 5% = high credibility
    'normal': 10,    # 5-10% = normal
    'wide': 15,      # 10-15% = concerning
    'very_wide': 20  # > 15% = low credibility
}


def extract_guidance_elements(text: str) -> List[GuidanceElement]:
    """Extract and analyze guidance statements from text."""
    
    elements = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        
        # Check if this is a guidance-related sentence
        for metric, pattern in GUIDANCE_PATTERNS.items():
            if re.search(pattern, sentence, re.IGNORECASE):
                # Extract range
                range_low, range_high, range_width = extract_range(sentence)
                
                # Count qualifiers
                qualifiers = []
                for qual_pattern, qual_type in CREDIBILITY_QUALIFIERS:
                    if re.search(qual_pattern, sentence, re.IGNORECASE):
                        qualifiers.append(qual_type)
                
                # Calculate specificity
                specificity = calculate_specificity(sentence, range_low, range_high)
                
                # Flag credibility issues
                flags = identify_credibility_flags(
                    sentence, range_width, len(qualifiers), specificity
                )
                
                elements.append(GuidanceElement(
                    text=sentence,
                    metric=metric,
                    range_low=range_low,
                    range_high=range_high,
                    range_width_pct=range_width,
                    qualifier_count=len(qualifiers),
                    qualifiers_found=qualifiers,
                    specificity_score=specificity,
                    credibility_flags=flags
                ))
                break  # One metric per sentence
    
    return elements


def extract_range(text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Extract numeric range from guidance text."""
    
    for pattern in RANGE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                # Parse low and high values
                low_str = groups[0].replace(',', '')
                low = float(low_str)
                
                # Handle different pattern structures
                if len(groups) >= 3:
                    high_str = groups[2] if groups[2] else groups[1]
                else:
                    high_str = groups[1]
                high_str = high_str.replace(',', '') if high_str else low_str
                high = float(high_str)
                
                # Adjust for millions/billions
                multiplier_low = 1
                multiplier_high = 1
                if len(groups) > 1 and groups[1]:
                    mult = groups[1].upper()
                    if mult in ['BILLION', 'B']:
                        multiplier_low = 1000
                    elif mult in ['MILLION', 'M']:
                        multiplier_low = 1
                    elif mult == 'K':
                        multiplier_low = 0.001
                
                if len(groups) > 3 and groups[3]:
                    mult = groups[3].upper()
                    if mult in ['BILLION', 'B']:
                        multiplier_high = 1000
                    elif mult in ['MILLION', 'M']:
                        multiplier_high = 1
                
                low = low * multiplier_low
                high = high * multiplier_high
                
                # Calculate range width as % of midpoint
                if low > 0:
                    midpoint = (low + high) / 2
                    width_pct = ((high - low) / midpoint) * 100
                    return low, high, round(width_pct, 2)
                
            except (ValueError, IndexError):
                pass
    
    return None, None, None


def calculate_specificity(text: str, range_low: Optional[float], range_high: Optional[float]) -> int:
    """Calculate specificity score (1-5)."""
    
    score = 3  # Base score
    
    # Has numeric range
    if range_low is not None:
        score += 1
        
        # Tight range
        if range_high and range_low > 0:
            width = (range_high - range_low) / range_low * 100
            if width < 10:
                score += 1
    
    # Has specific timeline
    if re.search(r'\b(Q[1-4]|first|second|third|fourth|full.?year|fiscal)\b', text, re.IGNORECASE):
        score += 0.5
    
    # Vague language reduces score
    vague_patterns = [
        r'\b(roughly|approximately|around|about)\b',
        r'\b(may|might|could)\b',
        r'\b(potential|possible)\b',
    ]
    for pattern in vague_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score -= 0.5
    
    return max(1, min(5, int(score)))


def identify_credibility_flags(
    text: str, 
    range_width: Optional[float], 
    qualifier_count: int,
    specificity: int
) -> List[str]:
    """Identify specific credibility concerns."""
    
    flags = []
    
    # Wide range
    if range_width:
        if range_width > RANGE_WIDTH_THRESHOLDS['very_wide']:
            flags.append(f"Very wide guidance range ({range_width:.1f}%)")
        elif range_width > RANGE_WIDTH_THRESHOLDS['wide']:
            flags.append(f"Wide guidance range ({range_width:.1f}%)")
    
    # Too many qualifiers
    if qualifier_count >= 4:
        flags.append(f"Excessive qualifiers ({qualifier_count} found)")
    elif qualifier_count >= 3:
        flags.append(f"Multiple qualifiers ({qualifier_count} found)")
    
    # Low specificity
    if specificity <= 2:
        flags.append("Low specificity - lacks concrete details")
    
    # Conditional language
    if re.search(r'\b(if|assuming|provided|contingent)\b', text, re.IGNORECASE):
        flags.append("Heavily conditional guidance")
    
    # Widening language
    if re.search(r'\b(widen|broaden|expand).*range\b', text, re.IGNORECASE):
        flags.append("Guidance range widened from prior period")
    
    # Maintaining vs raising
    if re.search(r'\b(maintain|reiterate)\b', text, re.IGNORECASE):
        if not re.search(r'\b(raise|increase|narrow)\b', text, re.IGNORECASE):
            flags.append("Guidance maintained, not raised")
    
    return flags


def check_for_credibility_boosters(text: str) -> List[str]:
    """Find positive credibility signals in guidance."""
    
    boosters = []
    for pattern, booster_type in CREDIBILITY_BOOSTERS:
        if re.search(pattern, text, re.IGNORECASE):
            boosters.append(booster_type)
    
    return boosters


def calculate_credibility_score(elements: List[GuidanceElement], full_text: str) -> Dict:
    """Calculate overall guidance credibility score."""
    
    if not elements:
        return {
            'score': None,
            'grade': 'N/A',
            'assessment': 'No guidance statements detected',
            'elements': [],
            'boosters': [],
            'flags_summary': {}
        }
    
    # Start with base score
    base_score = 70
    
    # Aggregate metrics
    total_qualifiers = sum(e.qualifier_count for e in elements)
    avg_qualifiers = total_qualifiers / len(elements)
    avg_specificity = sum(e.specificity_score for e in elements) / len(elements)
    
    # Collect all flags
    all_flags = []
    for e in elements:
        all_flags.extend(e.credibility_flags)
    
    # Count flags by severity
    flags_summary = {}
    for flag in all_flags:
        flags_summary[flag] = flags_summary.get(flag, 0) + 1
    
    # Score adjustments
    
    # Qualifier penalty
    if avg_qualifiers > 3:
        base_score -= 15
    elif avg_qualifiers > 2:
        base_score -= 10
    elif avg_qualifiers > 1:
        base_score -= 5
    
    # Specificity bonus/penalty
    if avg_specificity >= 4:
        base_score += 10
    elif avg_specificity <= 2:
        base_score -= 10
    
    # Flag penalties
    for flag in all_flags:
        if 'wide' in flag.lower():
            base_score -= 8
        elif 'excessive' in flag.lower():
            base_score -= 5
        elif 'conditional' in flag.lower():
            base_score -= 5
        elif 'maintained' in flag.lower():
            base_score -= 3
    
    # Booster bonuses
    boosters = check_for_credibility_boosters(full_text)
    for booster in boosters:
        if booster == 'guidance_raise':
            base_score += 10
        elif booster == 'track_record':
            base_score += 8
        elif booster == 'outperformance':
            base_score += 5
        elif booster in ['confidence', 'reaffirmation']:
            base_score += 3
    
    # Normalize
    final_score = max(0, min(100, base_score))
    
    # Grade
    if final_score >= 80:
        grade = 'A'
        assessment = 'High credibility guidance with specific, confident language'
    elif final_score >= 70:
        grade = 'B'
        assessment = 'Solid guidance with normal level of caveats'
    elif final_score >= 60:
        grade = 'C'
        assessment = 'Guidance credibility concerns - review qualifier usage'
    elif final_score >= 50:
        grade = 'D'
        assessment = 'Low credibility guidance - excessive hedging or wide ranges'
    else:
        grade = 'F'
        assessment = 'Significant credibility issues - guidance appears unreliable'
    
    return {
        'score': final_score,
        'grade': grade,
        'assessment': assessment,
        'avg_qualifiers': round(avg_qualifiers, 1),
        'avg_specificity': round(avg_specificity, 1),
        'elements': elements,
        'boosters': boosters,
        'flags_summary': flags_summary,
        'total_guidance_statements': len(elements)
    }


def format_for_pdf(analysis: Dict) -> str:
    """Format guidance credibility analysis for PDF report."""
    
    lines = []
    lines.append("=" * 60)
    lines.append("GUIDANCE CREDIBILITY ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    
    if analysis['score'] is None:
        lines.append("No guidance statements detected in script.")
        return '\n'.join(lines)
    
    # Summary
    grade_icons = {'A': '🟢', 'B': '🟢', 'C': '🟡', 'D': '🟠', 'F': '🔴'}
    icon = grade_icons.get(analysis['grade'], '⚪')
    
    lines.append(f"CREDIBILITY SCORE: {icon} {analysis['score']}/100 (Grade: {analysis['grade']})")
    lines.append(f"Assessment: {analysis['assessment']}")
    lines.append("")
    
    # Key metrics
    lines.append("Key Metrics:")
    lines.append(f"  • Guidance statements analyzed: {analysis['total_guidance_statements']}")
    lines.append(f"  • Average qualifiers per statement: {analysis['avg_qualifiers']}")
    lines.append(f"  • Average specificity score: {analysis['avg_specificity']}/5")
    lines.append("")
    
    # Credibility boosters
    if analysis['boosters']:
        lines.append("✅ Positive Signals:")
        for booster in analysis['boosters']:
            lines.append(f"  • {booster.replace('_', ' ').title()}")
        lines.append("")
    
    # Credibility flags
    if analysis['flags_summary']:
        lines.append("⚠️ Credibility Concerns:")
        for flag, count in sorted(analysis['flags_summary'].items(), key=lambda x: -x[1]):
            lines.append(f"  • {flag}" + (f" ({count}x)" if count > 1 else ""))
        lines.append("")
    
    # Detailed elements
    lines.append("-" * 60)
    lines.append("GUIDANCE STATEMENT DETAILS")
    lines.append("-" * 60)
    lines.append("")
    
    for i, elem in enumerate(analysis['elements'], 1):
        spec_bar = "█" * elem.specificity_score + "░" * (5 - elem.specificity_score)
        
        lines.append(f"{i}. [{elem.metric.upper()}]")
        lines.append(f"   \"{elem.text[:150]}{'...' if len(elem.text) > 150 else ''}\"")
        
        if elem.range_low is not None:
            range_str = f"   Range: {elem.range_low:.1f} - {elem.range_high:.1f}"
            if elem.range_width_pct:
                range_str += f" (width: {elem.range_width_pct:.1f}%)"
            lines.append(range_str)
        
        lines.append(f"   Specificity: {spec_bar} ({elem.specificity_score}/5)")
        lines.append(f"   Qualifiers: {elem.qualifier_count} ({', '.join(elem.qualifiers_found) if elem.qualifiers_found else 'none'})")
        
        if elem.credibility_flags:
            for flag in elem.credibility_flags:
                lines.append(f"   ⚠️ {flag}")
        lines.append("")
    
    return '\n'.join(lines)


# Test
if __name__ == "__main__":
    sample = """
    We are raising our full-year revenue guidance to approximately $2.1 to $2.3 billion,
    which assumes current market conditions persist.
    
    We expect gross margin to be in the range of 42% to 44%, subject to supply chain 
    dynamics and foreign exchange impacts.
    
    EPS guidance is being widened to $3.50 to $4.00, reflecting uncertain demand visibility.
    We anticipate capex of approximately $150 to $200 million.
    
    We have a strong track record of meeting or exceeding guidance.
    """
    
    elements = extract_guidance_elements(sample)
    analysis = calculate_credibility_score(elements, sample)
    print(format_for_pdf(analysis))
