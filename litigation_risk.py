#!/usr/bin/env python3
"""
Litigation Risk Highlighter

Identifies forward-looking statements that may lack proper PSLRA safe harbor
protection and flags areas needing cautionary language.

Key focus areas:
- Forward-looking statements without qualifiers
- Specific projections without safe harbor
- "Fact" statements that are actually predictions
- Missing cautionary language
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class LitigationRisk:
    """A statement with potential litigation exposure."""
    original_text: str
    risk_type: str  # forward_looking, specific_projection, implicit_promise, etc.
    risk_level: str  # high, medium, low
    issue: str
    suggested_fix: str
    safe_harbor_needed: bool


# Forward-looking statement indicators
FLS_INDICATORS = [
    r'\b(will|shall)\s+(be|have|achieve|reach|deliver|generate|grow|increase|decrease)',
    r'\b(expect|anticipate|project|forecast|estimate|plan|intend|target|aim)\s+(to|that)',
    r'\bgoing forward\b',
    r'\b(next|coming|future)\s+(quarter|year|period|fiscal)',
    r'\bby (year|fiscal|Q[1-4]|20\d{2})\s*end',
    r'\b(guidance|outlook|target|goal)\s+(of|is|remains)',
    r'\bwe (believe|think|see|view)\s+.*(will|should|could)',
    r'\bon track (to|for)',
    r'\bpoised (to|for)',
    r'\bposition(ed|ing)\s+(us|ourselves|the company)\s+(to|for)',
]

# Specific/precise language that increases risk
SPECIFICITY_PATTERNS = [
    (r'\$[\d,]+\s*(million|billion|M|B|K)', 'specific_dollar_amount'),
    (r'(\d+(?:\.\d+)?)\s*%', 'specific_percentage'),
    (r'(\d+(?:\.\d+)?)[xX]', 'specific_multiple'),
    (r'by\s+(Q[1-4]|January|February|March|April|May|June|July|August|September|October|November|December|20\d{2})', 'specific_timeline'),
    (r'(\d+)\s+(basis points|bps)', 'specific_basis_points'),
]

# Qualifiers that provide some protection
PROTECTIVE_QUALIFIERS = [
    r'\b(approximately|about|around|roughly|nearly|close to)\b',
    r'\b(may|might|could)\b',
    r'\b(expect|anticipate|believe|estimate)\b',
    r'\b(subject to|dependent on|contingent upon)\b',
    r'\b(assuming|if|provided that)\b',
    r'\bassuming (no|current|similar)\b',
    r'\bexcluding (the impact|effects|one-time)\b',
]

# Required cautionary themes for full PSLRA protection
CAUTIONARY_THEMES = [
    'economic conditions',
    'competition',
    'regulatory',
    'customer demand',
    'supply chain',
    'foreign exchange',
    'interest rates',
    'operational execution',
    'key personnel',
    'cybersecurity',
    'litigation',
    'acquisition integration',
]


def has_qualifier(sentence: str) -> bool:
    """Check if sentence has protective qualifying language."""
    for pattern in PROTECTIVE_QUALIFIERS:
        if re.search(pattern, sentence, re.IGNORECASE):
            return True
    return False


def is_forward_looking(sentence: str) -> bool:
    """Check if sentence contains forward-looking language."""
    for pattern in FLS_INDICATORS:
        if re.search(pattern, sentence, re.IGNORECASE):
            return True
    return False


def get_specificity_level(sentence: str) -> Tuple[int, List[str]]:
    """Calculate specificity level and identify specific claims."""
    specific_items = []
    for pattern, item_type in SPECIFICITY_PATTERNS:
        matches = re.findall(pattern, sentence, re.IGNORECASE)
        if matches:
            specific_items.append(item_type)
    return len(specific_items), specific_items


def analyze_litigation_risk(text: str) -> List[LitigationRisk]:
    """Analyze text for litigation risk in forward-looking statements."""
    
    risks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # Skip very short sentences
            continue
            
        is_fls = is_forward_looking(sentence)
        has_qual = has_qualifier(sentence)
        specificity, specific_items = get_specificity_level(sentence)
        
        # High risk: Forward-looking + specific + no qualifier
        if is_fls and specificity > 0 and not has_qual:
            risks.append(LitigationRisk(
                original_text=sentence,
                risk_type='unqualified_specific_fls',
                risk_level='high',
                issue=f"Forward-looking statement with specific {', '.join(specific_items)} but no qualifying language",
                suggested_fix=add_qualifiers(sentence, specific_items),
                safe_harbor_needed=True
            ))
        
        # High risk: Definitive future statement ("will achieve", "shall deliver")
        elif re.search(r'\b(will|shall)\s+(achieve|deliver|reach|hit|meet|exceed)\b', sentence, re.IGNORECASE):
            risks.append(LitigationRisk(
                original_text=sentence,
                risk_type='definitive_commitment',
                risk_level='high',
                issue="Definitive commitment language ('will achieve/deliver') creates expectation",
                suggested_fix=re.sub(
                    r'\b(will|shall)\s+(achieve|deliver|reach|hit|meet|exceed)',
                    r'expect to \2',
                    sentence,
                    flags=re.IGNORECASE
                ),
                safe_harbor_needed=True
            ))
        
        # Medium risk: Forward-looking without qualifier
        elif is_fls and not has_qual:
            risks.append(LitigationRisk(
                original_text=sentence,
                risk_type='unqualified_fls',
                risk_level='medium',
                issue="Forward-looking statement without protective qualifier",
                suggested_fix=add_qualifiers(sentence, []),
                safe_harbor_needed=True
            ))
        
        # Medium risk: Specific numbers in general statements
        elif specificity > 1 and not has_qual:
            risks.append(LitigationRisk(
                original_text=sentence,
                risk_type='specific_without_qualifier',
                risk_level='medium',
                issue=f"Multiple specific claims ({', '.join(specific_items)}) without qualifier",
                suggested_fix=add_qualifiers(sentence, specific_items),
                safe_harbor_needed=False
            ))
        
        # Low risk: Implicit promises
        if re.search(r'\b(committed to|dedicated to|focused on) (deliver|achiev|provid)', sentence, re.IGNORECASE):
            risks.append(LitigationRisk(
                original_text=sentence,
                risk_type='implicit_promise',
                risk_level='low',
                issue="Implicit promise language that could be construed as commitment",
                suggested_fix=re.sub(
                    r'committed to (deliver|achiev)',
                    r'focused on \1',
                    sentence,
                    flags=re.IGNORECASE
                ),
                safe_harbor_needed=False
            ))
    
    # Sort by risk level
    risk_order = {'high': 0, 'medium': 1, 'low': 2}
    risks.sort(key=lambda x: risk_order.get(x.risk_level, 3))
    
    return risks


def add_qualifiers(sentence: str, specific_items: List[str]) -> str:
    """Add appropriate qualifiers to make statement safer."""
    
    # Add "approximately" before specific numbers
    sentence = re.sub(
        r'(\$)([\d,]+)',
        r'approximately \1\2',
        sentence
    )
    sentence = re.sub(
        r'(\d+(?:\.\d+)?)\s*(%)',
        r'approximately \1\2',
        sentence
    )
    
    # Soften definitive language
    sentence = re.sub(r'\bwill be\b', 'is expected to be', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\bwill (achieve|reach|deliver|generate)', 
                     r'expects to \1', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\bshall\b', 'is expected to', sentence, flags=re.IGNORECASE)
    
    # Add caveat if not present
    if 'subject to' not in sentence.lower() and 'assuming' not in sentence.lower():
        sentence = sentence.rstrip('.') + ', subject to the risks described in our SEC filings.'
    
    return sentence


def check_safe_harbor_coverage(text: str) -> Dict:
    """Check if text has adequate safe harbor disclosure."""
    
    text_lower = text.lower()
    
    # Check for safe harbor statement
    has_safe_harbor = any([
        'forward-looking statements' in text_lower,
        'safe harbor' in text_lower,
        'private securities litigation reform act' in text_lower,
        'pslra' in text_lower,
    ])
    
    # Check for cautionary factors
    covered_themes = []
    missing_themes = []
    
    for theme in CAUTIONARY_THEMES:
        if theme.lower() in text_lower or any(
            word in text_lower for word in theme.lower().split()
        ):
            covered_themes.append(theme)
        else:
            missing_themes.append(theme)
    
    coverage_score = len(covered_themes) / len(CAUTIONARY_THEMES) * 100
    
    return {
        'has_safe_harbor_statement': has_safe_harbor,
        'covered_themes': covered_themes,
        'missing_themes': missing_themes,
        'coverage_score': round(coverage_score, 1),
        'recommendation': get_safe_harbor_recommendation(has_safe_harbor, coverage_score)
    }


def get_safe_harbor_recommendation(has_statement: bool, coverage: float) -> str:
    """Generate recommendation based on safe harbor analysis."""
    
    if not has_statement:
        return "CRITICAL: No safe harbor statement detected. Add PSLRA-compliant forward-looking statement disclosure."
    elif coverage < 50:
        return "WARNING: Safe harbor coverage is thin. Expand cautionary factors to include more risk themes."
    elif coverage < 75:
        return "MODERATE: Consider expanding cautionary language to cover additional risk factors."
    else:
        return "ADEQUATE: Safe harbor coverage appears sufficient, but review for company-specific risks."


def format_for_pdf(risks: List[LitigationRisk], safe_harbor: Dict) -> str:
    """Format litigation risk analysis for PDF report."""
    
    lines = []
    lines.append("=" * 60)
    lines.append("LITIGATION RISK ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    
    # Safe harbor summary
    lines.append("SAFE HARBOR STATUS")
    lines.append("-" * 40)
    status = "✅ PRESENT" if safe_harbor['has_safe_harbor_statement'] else "❌ MISSING"
    lines.append(f"Safe Harbor Statement: {status}")
    lines.append(f"Cautionary Theme Coverage: {safe_harbor['coverage_score']}%")
    lines.append(f"Recommendation: {safe_harbor['recommendation']}")
    lines.append("")
    
    if safe_harbor['missing_themes']:
        lines.append("Missing Cautionary Themes:")
        for theme in safe_harbor['missing_themes'][:5]:
            lines.append(f"  • {theme}")
    lines.append("")
    
    # Risk summary
    high_risk = len([r for r in risks if r.risk_level == 'high'])
    medium_risk = len([r for r in risks if r.risk_level == 'medium'])
    low_risk = len([r for r in risks if r.risk_level == 'low'])
    
    lines.append("FORWARD-LOOKING STATEMENT RISKS")
    lines.append("-" * 40)
    lines.append(f"Total Flags: {len(risks)}")
    lines.append(f"  🔴 High Risk: {high_risk}")
    lines.append(f"  🟡 Medium Risk: {medium_risk}")
    lines.append(f"  🟢 Low Risk: {low_risk}")
    lines.append("")
    
    # Detailed risks
    if risks:
        lines.append("-" * 60)
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 60)
        lines.append("")
        
        for i, risk in enumerate(risks, 1):
            icon = "🔴" if risk.risk_level == 'high' else "🟡" if risk.risk_level == 'medium' else "🟢"
            
            lines.append(f"{i}. {icon} [{risk.risk_type.upper().replace('_', ' ')}]")
            lines.append(f"   ORIGINAL: \"{risk.original_text[:150]}{'...' if len(risk.original_text) > 150 else ''}\"")
            lines.append(f"   ⚠️  ISSUE: {risk.issue}")
            lines.append(f"   ✏️  SUGGESTED: \"{risk.suggested_fix[:150]}{'...' if len(risk.suggested_fix) > 150 else ''}\"")
            if risk.safe_harbor_needed:
                lines.append(f"   📋 Requires safe harbor reference")
            lines.append("")
    
    return '\n'.join(lines)


# Suggested safe harbor statement
SAMPLE_SAFE_HARBOR = """
This presentation contains forward-looking statements within the meaning of Section 27A 
of the Securities Act of 1933 and Section 21E of the Securities Exchange Act of 1934. 
These statements involve known and unknown risks, uncertainties, and other factors that 
may cause actual results to differ materially from those expressed or implied. Factors 
that could cause actual results to differ include: general economic conditions; 
competitive factors; changes in customer demand; regulatory changes; supply chain 
disruptions; foreign exchange fluctuations; interest rate changes; operational 
execution risks; dependence on key personnel; cybersecurity risks; and other factors 
described in our SEC filings. We undertake no obligation to update forward-looking 
statements to reflect events after the date of this presentation.
"""


# Test
if __name__ == "__main__":
    sample = """
    We will achieve $500 million in revenue by Q4 2026. The company shall deliver 
    25% margin expansion through our cost initiatives. 
    
    Going forward, we expect to generate approximately $100 million in free cash flow.
    We believe we will hit our targets.
    
    We are committed to delivering shareholder value and will reach profitability 
    by next year. Our guidance of $2.1 to $2.3 billion assumes current market conditions.
    """
    
    risks = analyze_litigation_risk(sample)
    safe_harbor = check_safe_harbor_coverage(sample)
    print(format_for_pdf(risks, safe_harbor))
