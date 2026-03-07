#!/usr/bin/env python3
"""
Negative Interpretations Scanner

Identifies statements that could be interpreted negatively by analysts,
short-sellers, or media, and suggests defensive rewrites.
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class NegativeInterpretation:
    """A statement with potential negative spin."""
    original_text: str
    negative_spin: str
    category: str  # growth, margins, execution, guidance, etc.
    risk_level: str  # high, medium, low
    suggested_rewrite: str
    rationale: str


# Patterns that can be spun negatively
NEGATIVE_SPIN_PATTERNS = {
    'weak_growth_language': {
        'patterns': [
            (r'modest (growth|improvement|increase)', 
             "Growth is slowing / company struggling to grow"),
            (r'moderate (growth|improvement|gains)',
             "Momentum is fading"),
            (r'stable|flat|consistent',
             "Company is stagnating / no growth"),
            (r'in line with expectations',
             "Failed to beat / no upside surprise"),
            (r'met (our|guidance|expectations)',
             "Barely scraped by / no beat"),
        ],
        'category': 'growth',
        'risk_level': 'high'
    },
    'margin_pressure': {
        'patterns': [
            (r'investing (in|for) (the future|growth|long.?term)',
             "Margins under pressure / profitability sacrificed"),
            (r'strategic investments?',
             "Spending is out of control"),
            (r'near.?term (pressure|headwinds?|challenges?)',
             "Problems are ongoing with no end in sight"),
            (r'(elevated|higher) (costs?|expenses?|spending)',
             "Cost discipline has broken down"),
        ],
        'category': 'margins',
        'risk_level': 'high'
    },
    'execution_concerns': {
        'patterns': [
            (r'(learning|ramping|building|developing)',
             "Still figuring it out / execution risk"),
            (r'work (to do|ahead|remaining)',
             "Behind schedule / not delivering"),
            (r'(transition|pivot|shift)ing',
             "Business model is broken / forced to change"),
            (r'repositioning',
             "Prior strategy failed"),
        ],
        'category': 'execution',
        'risk_level': 'medium'
    },
    'demand_weakness': {
        'patterns': [
            (r'(cautious|careful|selective) (customers?|clients?|buyers?)',
             "Demand is weak / customers pulling back"),
            (r'(longer|extended|elongated) (sales? )?cycles?',
             "Deals are harder to close"),
            (r'(softness|weakness) in',
             "Business is deteriorating"),
            (r'normalizing',
             "Growth tailwinds are gone"),
        ],
        'category': 'demand',
        'risk_level': 'high'
    },
    'guidance_hedging': {
        'patterns': [
            (r'(wide|wider|broad|broader) (range|guidance)',
             "Management has no visibility / uncertain"),
            (r'(maintaining|reiterating) guidance',
             "Failed to raise / no confidence to raise"),
            (r'(appropriate|prudent) to (be )?(conservative|cautious)',
             "Downside risk is real"),
            (r'embedded (conservatism|cushion)',
             "Will likely miss and blame macro"),
        ],
        'category': 'guidance',
        'risk_level': 'high'
    },
    'competitive_pressure': {
        'patterns': [
            (r'(competitive|pricing) (environment|pressure|dynamics)',
             "Losing to competitors / pricing power eroding"),
            (r'rational (competitors?|pricing|behavior)',
             "Price war brewing"),
            (r'market share (stable|maintained|held)',
             "Not growing share / competitors winning"),
        ],
        'category': 'competition',
        'risk_level': 'medium'
    },
    'macro_blame': {
        'patterns': [
            (r'(macro|macroeconomic) (headwinds?|challenges?|environment)',
             "Blaming the economy for poor execution"),
            (r'(challenging|difficult|uncertain) (environment|conditions|backdrop)',
             "Management excuses incoming"),
            (r'(factors? )?(beyond|outside) (our )?control',
             "Taking no responsibility"),
        ],
        'category': 'macro',
        'risk_level': 'medium'
    },
    'vague_optimism': {
        'patterns': [
            (r'(excited|optimistic|confident|encouraged) about',
             "No concrete evidence to support optimism"),
            (r'(well.?positioned|poised) (for|to)',
             "Vague promises with no specifics"),
            (r'(believe|think|expect) we (can|will)',
             "Hope is not a strategy"),
        ],
        'category': 'credibility',
        'risk_level': 'low'
    },
}


# Suggested rewrites to be more defensible
REWRITE_SUGGESTIONS = {
    'growth': {
        'weak': {
            'avoid': ['modest', 'moderate', 'stable', 'flat'],
            'prefer': ['solid', 'consistent with our plan', 'on track'],
            'template': "We delivered {metric} growth, which {context}. Importantly, {forward_statement}."
        },
    },
    'margins': {
        'investment': {
            'avoid': ['investing for the future', 'strategic investments'],
            'prefer': ['targeted investments with clear ROI', 'disciplined growth investments'],
            'template': "We made targeted investments in {area}, which we expect to yield {benefit} by {timeframe}."
        },
    },
    'guidance': {
        'hedging': {
            'avoid': ['maintaining guidance', 'conservative', 'prudent'],
            'prefer': ['reaffirming our outlook', 'our guidance reflects', 'visibility supports'],
            'template': "Our guidance reflects {assumptions}. We have {visibility_statement}."
        },
    },
}


def find_negative_interpretations(text: str) -> List[NegativeInterpretation]:
    """Scan text for statements that could be spun negatively."""
    
    interpretations = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        for pattern_group_name, pattern_group in NEGATIVE_SPIN_PATTERNS.items():
            for pattern, negative_spin in pattern_group['patterns']:
                if re.search(pattern, sentence, re.IGNORECASE):
                    # Generate suggested rewrite
                    rewrite = generate_defensive_rewrite(
                        sentence, 
                        pattern_group['category'],
                        pattern
                    )
                    
                    interpretations.append(NegativeInterpretation(
                        original_text=sentence.strip(),
                        negative_spin=negative_spin,
                        category=pattern_group['category'],
                        risk_level=pattern_group['risk_level'],
                        suggested_rewrite=rewrite,
                        rationale=f"Pattern detected: {pattern_group_name}"
                    ))
                    break  # Only one interpretation per sentence per group
    
    # Sort by risk level
    risk_order = {'high': 0, 'medium': 1, 'low': 2}
    interpretations.sort(key=lambda x: risk_order.get(x.risk_level, 3))
    
    return interpretations


def generate_defensive_rewrite(sentence: str, category: str, pattern: str) -> str:
    """Generate a more defensible version of the statement."""
    
    rewrite = sentence
    
    # Apply category-specific rewrites
    rewrites = {
        # Growth language
        r'modest (growth|improvement|increase)': r'solid \1',
        r'moderate (growth|improvement|gains)': r'steady \1',
        r'stable|flat': 'consistent with our plan',
        r'in line with expectations': 'on track with our targets',
        
        # Margin language  
        r'investing (in|for) (the future|growth|long.?term)': 
            r'making targeted investments in \2 with clear return timelines',
        r'strategic investments?': 'disciplined growth investments with defined ROI',
        r'near.?term (pressure|headwinds?|challenges?)': 
            r'temporary \1 that we expect to moderate by [timeframe]',
        
        # Execution language
        r'work (to do|ahead|remaining)': r'continued opportunity for improvement',
        r'(transition|pivot|shift)ing': r'strategically evolving',
        
        # Demand language
        r'(cautious|careful|selective) (customers?|clients?|buyers?)': 
            r'\2 who are being thoughtful about their investments',
        r'(longer|extended|elongated) (sales? )?cycles?': 
            r'more comprehensive evaluation periods',
        r'(softness|weakness) in': 'normalization in',
        
        # Guidance language
        r'(maintaining|reiterating) guidance': r'reaffirming our outlook',
        r'(appropriate|prudent) to (be )?(conservative|cautious)': 
            'our guidance appropriately reflects current visibility',
        
        # Competitive language
        r'(competitive|pricing) (environment|pressure|dynamics)': 
            r'an active competitive landscape where we continue to win',
        r'market share (stable|maintained|held)': 'market position remains strong',
        
        # Macro language
        r'(macro|macroeconomic) (headwinds?|challenges?|environment)': 
            r'broader market conditions',
        r'(challenging|difficult|uncertain) (environment|conditions|backdrop)': 
            r'dynamic operating \2',
        r'(factors? )?(beyond|outside) (our )?control': 'external factors',
    }
    
    for old_pattern, new_text in rewrites.items():
        rewrite = re.sub(old_pattern, new_text, rewrite, flags=re.IGNORECASE)
    
    # If no specific rewrite applied, provide generic guidance
    if rewrite == sentence:
        rewrite = f"[REWRITE NEEDED] Consider rephrasing to be more specific and forward-looking: {sentence}"
    
    return rewrite


def analyze_negative_density(text: str) -> Dict:
    """Calculate density of potentially negative language."""
    
    interpretations = find_negative_interpretations(text)
    word_count = len(text.split())
    
    # Count by category
    by_category = {}
    for interp in interpretations:
        if interp.category not in by_category:
            by_category[interp.category] = []
        by_category[interp.category].append(interp)
    
    # Count by risk level
    high_risk = len([i for i in interpretations if i.risk_level == 'high'])
    medium_risk = len([i for i in interpretations if i.risk_level == 'medium'])
    low_risk = len([i for i in interpretations if i.risk_level == 'low'])
    
    return {
        'total_flags': len(interpretations),
        'high_risk_count': high_risk,
        'medium_risk_count': medium_risk,
        'low_risk_count': low_risk,
        'flags_per_1000_words': round(len(interpretations) / (word_count / 1000), 2),
        'by_category': {k: len(v) for k, v in by_category.items()},
        'interpretations': interpretations
    }


def format_for_pdf(analysis: Dict) -> str:
    """Format negative interpretation analysis for PDF report."""
    
    lines = []
    lines.append("=" * 60)
    lines.append("NEGATIVE INTERPRETATION RISK ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Total Flags: {analysis['total_flags']}")
    lines.append(f"  🔴 High Risk: {analysis['high_risk_count']}")
    lines.append(f"  🟡 Medium Risk: {analysis['medium_risk_count']}")
    lines.append(f"  🟢 Low Risk: {analysis['low_risk_count']}")
    lines.append(f"Flags per 1,000 words: {analysis['flags_per_1000_words']}")
    lines.append("")
    lines.append("By Category:")
    for cat, count in analysis['by_category'].items():
        lines.append(f"  • {cat.title()}: {count}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("DETAILED FLAGS")
    lines.append("-" * 60)
    lines.append("")
    
    for i, interp in enumerate(analysis['interpretations'], 1):
        risk_icon = "🔴" if interp.risk_level == 'high' else "🟡" if interp.risk_level == 'medium' else "🟢"
        
        lines.append(f"{i}. {risk_icon} [{interp.category.upper()}]")
        lines.append(f"   ORIGINAL: \"{interp.original_text[:150]}{'...' if len(interp.original_text) > 150 else ''}\"")
        lines.append(f"   ⚠️  COULD BE SPUN AS: \"{interp.negative_spin}\"")
        lines.append(f"   ✏️  SUGGESTED: \"{interp.suggested_rewrite[:150]}{'...' if len(interp.suggested_rewrite) > 150 else ''}\"")
        lines.append("")
    
    return '\n'.join(lines)


# Test
if __name__ == "__main__":
    sample = """
    We delivered modest growth this quarter despite a challenging macro environment.
    We're investing for the future, which has created some near-term margin pressure.
    
    Our guidance maintains a wide range given the uncertain conditions.
    We believe we're well-positioned for the long term and remain cautious about
    the near-term outlook given cautious customers and longer sales cycles.
    
    Competitive dynamics remain rational and our market share has been stable.
    We have work to do but are optimistic about our trajectory.
    """
    
    analysis = analyze_negative_density(sample)
    print(format_for_pdf(analysis))
