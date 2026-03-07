#!/usr/bin/env python3
"""
Activist Trigger Scanner

Identifies language in earnings scripts that activists could use 
against the company in a campaign. Focuses on:
- Capital allocation inefficiency signals
- Operational underperformance admissions
- Strategic direction uncertainty
- Governance/compensation red flags
- Margin/cost structure weaknesses
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ActivistTrigger:
    """A statement that could fuel activist criticism."""
    original_text: str
    trigger_type: str
    severity: str  # high, medium, low
    activist_narrative: str  # How an activist would spin this
    defense_suggestion: str  # How to strengthen the language


# Activist trigger patterns by category
ACTIVIST_PATTERNS = {
    'capital_allocation': {
        'patterns': [
            (r'(balance sheet|cash|liquidity)\s+(flexibility|strength|position|optionality)',
             "Company hoarding cash instead of returning to shareholders"),
            (r'(evaluating|considering|exploring)\s+(options|opportunities|alternatives)',
             "Management lacks clear capital allocation strategy"),
            (r'(maintain|preserve)\s+(financial flexibility|optionality)',
             "Cash is being inefficiently deployed"),
            (r'(opportunistic|selective)\s+(about|with|in)\s+(buybacks|repurchases|M&A)',
             "Management not committed to returning capital"),
            (r'(no current plans?|not (currently )?planning)\s+.*(buyback|dividend|repurchase)',
             "Shareholders being deprioritized"),
        ],
        'severity': 'high',
        'category': 'Capital Allocation'
    },
    'margin_inefficiency': {
        'patterns': [
            (r'(investing|investment)\s+(in|for)\s+(growth|future|long.?term|capabilities)',
             "Spending out of control / management empire-building"),
            (r'(elevated|higher|increased)\s+(costs?|expenses?|spending|SG&A)',
             "Cost discipline has broken down"),
            (r'margin\s+(pressure|compression|headwinds?|challenges?)',
             "Business model fundamentally broken"),
            (r'(scale|operating leverage)\s+(benefits?|improvements?)\s+(will|expected|should).*(time|future)',
             "Promises of future efficiency never materialize"),
            (r'(temporarily|near.?term|short.?term)\s+(elevated|higher|depressed)',
             "'Temporary' issues that become permanent"),
        ],
        'severity': 'high',
        'category': 'Margins & Efficiency'
    },
    'strategic_drift': {
        'patterns': [
            (r'(pivot|shift|transition|evolv)ing\s+(our|the)\s+(strategy|focus|model|approach)',
             "Prior strategy failed, management scrambling"),
            (r'(refin|reshap|reimagin|transform)ing\s+(our|the)',
             "Admitting the business needs fixing"),
            (r'(learning|ramping|building|developing|early)\s+(stage|innings|phase|days)',
             "Still figuring it out after years of execution"),
            (r'(long.?term|multi.?year)\s+(journey|transformation|process)',
             "No end in sight to underperformance"),
            (r'(strategic review|portfolio review|options)',
             "Company doesn't know what it wants to be"),
        ],
        'severity': 'medium',
        'category': 'Strategy'
    },
    'operational_underperformance': {
        'patterns': [
            (r'(below|missed|short of)\s+(expectations?|targets?|guidance)',
             "Management can't execute"),
            (r'(work|room|opportunity)\s+(to do|for improvement|ahead)',
             "Acknowledging underperformance"),
            (r'(disappointed|not satisfied|frustrated)\s+(with|by)',
             "Even management admits results are poor"),
            (r'(challenges?|headwinds?|obstacles?)\s+(we face|in|with)',
             "Excuses for poor performance"),
            (r'(behind|slower than)\s+(plan|expectations?|schedule)',
             "Execution issues persist"),
        ],
        'severity': 'high',
        'category': 'Execution'
    },
    'governance_red_flags': {
        'patterns': [
            (r'(compensation|pay|incentive)\s+(align|tied|linked).*(long.?term|performance)',
             "Management pay not actually tied to performance"),
            (r'(board|director)\s+(refresh|renewal|succession|independence)',
             "Governance issues require attention"),
            (r'(management|executive|leadership)\s+(transition|change|succession)',
             "Leadership instability"),
            (r'(shareholder|investor)\s+(engagement|outreach|feedback)',
             "Company on defensive with shareholders"),
        ],
        'severity': 'medium',
        'category': 'Governance'
    },
    'competitive_weakness': {
        'patterns': [
            (r'(market share|share)\s+(stable|flat|consistent|maintained)',
             "Company losing competitive battle"),
            (r'(competitive|pricing)\s+(pressure|environment|dynamics|intensity)',
             "Being outmaneuvered by competitors"),
            (r'(rational|disciplined)\s+(competition|competitors?|pricing)',
             "Hoping competitors don't attack further"),
            (r'(differentiat|defend|protect)ing\s+(our|the)\s+(position|moat|advantage)',
             "Defensive posture signals weakness"),
        ],
        'severity': 'medium',
        'category': 'Competition'
    },
    'complacency_signals': {
        'patterns': [
            (r'(pleased|satisfied|proud)\s+(with|of)\s+(our|these|the)\s+(results?|performance|progress)',
             "Management satisfied with mediocre results"),
            (r'(good|solid|decent|respectable)\s+(quarter|results?|performance)',
             "Low bar for success"),
            (r'(remain|continue to be)\s+(confident|optimistic|encouraged)',
             "Vague optimism without substance"),
            (r'(on track|progressing|advancing)\s+(with|toward|on)',
             "Meaningless progress claims"),
        ],
        'severity': 'low',
        'category': 'Management Tone'
    },
    'conglomerate_discount': {
        'patterns': [
            (r'(synerg|cross.?sell|integration)\s+(opportunities?|benefits?|potential)',
             "Promised synergies that never materialize"),
            (r'(portfolio|diversif|segment)\s+(strength|benefit|approach)',
             "Conglomerate structure destroying value"),
            (r'(strategic fit|complement|enhance)\s+(each other|one another|overall)',
             "Hodgepodge of businesses with no focus"),
        ],
        'severity': 'medium',
        'category': 'Portfolio Structure'
    },
}


def find_activist_triggers(text: str) -> List[ActivistTrigger]:
    """Scan text for language activists could exploit."""
    
    triggers = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        
        for pattern_group_name, pattern_group in ACTIVIST_PATTERNS.items():
            for pattern, activist_spin in pattern_group['patterns']:
                if re.search(pattern, sentence, re.IGNORECASE):
                    triggers.append(ActivistTrigger(
                        original_text=sentence,
                        trigger_type=pattern_group['category'],
                        severity=pattern_group['severity'],
                        activist_narrative=activist_spin,
                        defense_suggestion=generate_defense(sentence, pattern_group_name)
                    ))
                    break  # One trigger per sentence per category
    
    # Sort by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    triggers.sort(key=lambda x: severity_order.get(x.severity, 3))
    
    return triggers


def generate_defense(sentence: str, pattern_type: str) -> str:
    """Generate defensive rewrite to minimize activist attack surface."""
    
    defenses = {
        'capital_allocation': {
            'strategy': "Be specific about capital allocation priorities with numbers",
            'rewrite_patterns': [
                (r'(evaluating|considering|exploring)\s+(options|opportunities|alternatives)',
                 'executing on our clearly defined capital allocation framework'),
                (r'(maintain|preserve)\s+(financial flexibility|optionality)',
                 'deploying capital to maximize shareholder returns'),
                (r'(opportunistic|selective)',
                 'disciplined and returns-focused'),
            ]
        },
        'margin_inefficiency': {
            'strategy': "Quantify investments and expected returns with timelines",
            'rewrite_patterns': [
                (r'(investing|investment)\s+(in|for)\s+(growth|future|long.?term)',
                 'making targeted investments with clear ROI expectations'),
                (r'(elevated|higher|increased)\s+(costs?|expenses?)',
                 'investments that we expect to yield [X]% returns by [timeframe]'),
                (r'margin\s+(pressure|compression)',
                 'temporary margin dynamics that we expect to reverse by [timeframe]'),
            ]
        },
        'strategic_drift': {
            'strategy': "Emphasize continuity and conviction, not change",
            'rewrite_patterns': [
                (r'(pivot|shift|transition)ing',
                 'accelerating our long-standing strategy'),
                (r'(strategic review|portfolio review)',
                 'ongoing portfolio optimization as part of our regular discipline'),
            ]
        },
        'operational_underperformance': {
            'strategy': "Focus on actions and accountability, not excuses",
            'rewrite_patterns': [
                (r'(challenges?|headwinds?|obstacles?)',
                 'factors we are actively addressing through [specific actions]'),
                (r'(work|room|opportunity)\s+(to do|for improvement)',
                 'specific opportunities we have identified and are executing against'),
            ]
        },
        'governance_red_flags': {
            'strategy': "Emphasize alignment and shareholder focus",
            'rewrite_patterns': [
                (r'(compensation|pay)\s+(align|tied)',
                 'compensation directly tied to measurable shareholder value creation'),
                (r'(shareholder|investor)\s+(engagement|outreach)',
                 'our ongoing dialogue with shareholders who support our strategy'),
            ]
        },
        'competitive_weakness': {
            'strategy': "Lead with wins and differentiation, not defense",
            'rewrite_patterns': [
                (r'(market share|share)\s+(stable|flat)',
                 'strong market position with [X] competitive wins this quarter'),
                (r'(competitive|pricing)\s+(pressure|environment)',
                 'a market where our differentiation continues to win'),
            ]
        },
        'complacency_signals': {
            'strategy': "Show urgency and ambition, not satisfaction",
            'rewrite_patterns': [
                (r'(pleased|satisfied|proud)\s+(with|of)',
                 'encouraged by our progress and focused on doing more'),
                (r'(good|solid|decent)',
                 'results that demonstrate our momentum toward [ambitious goal]'),
            ]
        },
        'conglomerate_discount': {
            'strategy': "Prove value creation from portfolio, don't just assert it",
            'rewrite_patterns': [
                (r'(synerg|cross.?sell)',
                 'quantifiable value creation of $[X] from our integrated approach'),
            ]
        },
    }
    
    defense = defenses.get(pattern_type, {})
    rewrite = sentence
    
    for old_pattern, new_text in defense.get('rewrite_patterns', []):
        rewrite = re.sub(old_pattern, new_text, rewrite, flags=re.IGNORECASE)
    
    strategy = defense.get('strategy', 'Consider rephrasing to be more specific and action-oriented')
    
    if rewrite == sentence:
        return f"[STRATEGY: {strategy}] Original language may need revision."
    return rewrite


def calculate_activist_vulnerability_score(triggers: List[ActivistTrigger]) -> Dict:
    """Calculate overall vulnerability score."""
    
    high_risk = len([t for t in triggers if t.severity == 'high'])
    medium_risk = len([t for t in triggers if t.severity == 'medium'])
    low_risk = len([t for t in triggers if t.severity == 'low'])
    
    # Weighted score (high=3, medium=2, low=1)
    weighted_score = (high_risk * 3) + (medium_risk * 2) + (low_risk * 1)
    
    # Normalize to 0-100 scale (assuming max ~30 triggers)
    vulnerability_score = min(100, (weighted_score / 30) * 100)
    
    # Categorize by trigger type
    by_type = {}
    for t in triggers:
        if t.trigger_type not in by_type:
            by_type[t.trigger_type] = []
        by_type[t.trigger_type].append(t)
    
    # Determine overall risk level
    if high_risk >= 3 or vulnerability_score > 60:
        risk_level = "HIGH"
        assessment = "Script contains multiple statements activists could exploit"
    elif high_risk >= 1 or vulnerability_score > 30:
        risk_level = "MODERATE"
        assessment = "Some activist-sensitive language present"
    else:
        risk_level = "LOW"
        assessment = "Limited activist attack surface"
    
    return {
        'vulnerability_score': round(vulnerability_score, 1),
        'risk_level': risk_level,
        'assessment': assessment,
        'high_risk_count': high_risk,
        'medium_risk_count': medium_risk,
        'low_risk_count': low_risk,
        'total_triggers': len(triggers),
        'by_type': {k: len(v) for k, v in by_type.items()},
        'triggers': triggers
    }


def format_for_pdf(analysis: Dict) -> str:
    """Format activist trigger analysis for PDF report."""
    
    lines = []
    lines.append("=" * 60)
    lines.append("ACTIVIST VULNERABILITY ANALYSIS")
    lines.append("=" * 60)
    lines.append("")
    
    # Summary
    risk_icon = "🔴" if analysis['risk_level'] == 'HIGH' else "🟡" if analysis['risk_level'] == 'MODERATE' else "🟢"
    lines.append(f"OVERALL RISK: {risk_icon} {analysis['risk_level']}")
    lines.append(f"Vulnerability Score: {analysis['vulnerability_score']}/100")
    lines.append(f"Assessment: {analysis['assessment']}")
    lines.append("")
    
    # Breakdown
    lines.append("Trigger Summary:")
    lines.append(f"  🔴 High Severity: {analysis['high_risk_count']}")
    lines.append(f"  🟡 Medium Severity: {analysis['medium_risk_count']}")
    lines.append(f"  🟢 Low Severity: {analysis['low_risk_count']}")
    lines.append("")
    
    if analysis['by_type']:
        lines.append("By Category:")
        for cat, count in sorted(analysis['by_type'].items(), key=lambda x: -x[1]):
            lines.append(f"  • {cat}: {count}")
    lines.append("")
    
    # Detailed triggers
    if analysis['triggers']:
        lines.append("-" * 60)
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 60)
        lines.append("")
        
        for i, trigger in enumerate(analysis['triggers'], 1):
            icon = "🔴" if trigger.severity == 'high' else "🟡" if trigger.severity == 'medium' else "🟢"
            
            lines.append(f"{i}. {icon} [{trigger.trigger_type.upper()}]")
            lines.append(f"   STATEMENT: \"{trigger.original_text[:150]}{'...' if len(trigger.original_text) > 150 else ''}\"")
            lines.append(f"   ⚔️  ACTIVIST SPIN: \"{trigger.activist_narrative}\"")
            lines.append(f"   🛡️  DEFENSE: {trigger.defense_suggestion[:150]}{'...' if len(trigger.defense_suggestion) > 150 else ''}")
            lines.append("")
    
    return '\n'.join(lines)


# Test
if __name__ == "__main__":
    sample = """
    We are pleased with our solid results this quarter. We're maintaining balance 
    sheet flexibility and evaluating strategic options. 
    
    We're investing for the future and see margin pressure as temporary.
    Our market share has been stable despite competitive pressure.
    
    We have work to do but remain confident in our long-term journey.
    The board is focused on shareholder engagement and compensation alignment.
    
    We're transitioning our business model and the transformation is in early innings.
    """
    
    triggers = find_activist_triggers(sample)
    analysis = calculate_activist_vulnerability_score(triggers)
    print(format_for_pdf(analysis))
