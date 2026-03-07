#!/usr/bin/env python3
"""
Earnings Script Analyzer - Full Version
Analyzes earnings call transcripts with historical comparison

Features:
- Loughran-McDonald sentiment analysis
- Hedging/confidence detection
- Ownership (first-person) analysis
- Deception marker detection
- Historical trend comparison
- Auto-fetch transcripts from Motley Fool

Usage:
  python earnings_analyzer.py my_script.txt
  python earnings_analyzer.py my_script.txt --compare AAPL
  python earnings_analyzer.py --analyze AAPL --quarters 4
"""

import re
import csv
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Import modules
from fetcher import fetch_transcripts
from legal_context import (
    analyze_with_legal_context, 
    split_transcript_sections,
    is_legal_hedging,
    is_forward_looking_context,
)

# ============================================================
# LOAD LOUGHRAN-MCDONALD DICTIONARY
# ============================================================

def load_lm_dictionary(path="LM_MasterDictionary.csv"):
    """Load the Loughran-McDonald Master Dictionary"""
    categories = {
        'negative': set(),
        'positive': set(),
        'uncertainty': set(),
        'litigious': set(),
        'constraining': set(),
    }
    
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row['Word'].upper()
            if row['Negative'] != '0':
                categories['negative'].add(word)
            if row['Positive'] != '0':
                categories['positive'].add(word)
            if row['Uncertainty'] != '0':
                categories['uncertainty'].add(word)
            if row['Litigious'] != '0':
                categories['litigious'].add(word)
            if row['Constraining'] != '0':
                categories['constraining'].add(word)
    
    return categories

# ============================================================
# WORD LISTS
# ============================================================

HEDGING_WORDS = {
    'might', 'may', 'could', 'possibly', 'perhaps', 'potentially',
    'somewhat', 'relatively', 'approximately', 'around', 'about',
    'generally', 'typically', 'usually', 'sometimes', 'occasionally',
    'likely', 'unlikely', 'probable', 'possible', 'uncertain',
    'believe', 'think', 'feel', 'hope', 'expect', 'anticipate',
    'estimate', 'appear', 'seem', 'suggest', 'indicate',
}

HEDGING_PHRASES = [
    'going forward', 'at this time', 'as you know', 'you know',
    'in a sense', 'kind of', 'sort of', 'more or less',
    'to some extent', 'in some ways', 'challenging environment',
    'headwinds', 'cautiously optimistic',
]

CERTAINTY_WORDS = {
    'will', 'shall', 'must', 'definitely', 'certainly', 'absolutely',
    'clearly', 'obviously', 'undoubtedly', 'confident', 'committed',
    'guaranteed', 'assured', 'determined', 'convinced', 'sure',
    'always', 'never', 'every', 'all', 'none',
}

FIRST_PERSON_SINGULAR = {'i', "i'm", "i've", "i'll", "i'd", 'me', 'my', 'mine', 'myself'}
FIRST_PERSON_PLURAL = {'we', "we're", "we've", "we'll", "we'd", 'us', 'our', 'ours', 'ourselves'}

DISTANCING_PHRASES = [
    'the company', 'the team', 'the organization', 
    'management', 'the business', 'the firm',
]

DECEPTION_MARKERS = [
    'you know', 'as you know', 'everyone knows', 'obviously',
    'of course', 'clearly', 'frankly', 'honestly',
    'to be honest', 'truthfully', 'the fact is', 'the reality is',
]

EXTREME_POSITIVE = {
    'tremendous', 'incredible', 'fantastic', 'amazing', 'extraordinary',
    'exceptional', 'outstanding', 'remarkable', 'phenomenal', 'spectacular',
    'unbelievable', 'unprecedented',
}

# ============================================================
# TEXT PROCESSING
# ============================================================

def tokenize(text):
    text = text.lower()
    return re.findall(r"\b[\w']+\b", text)

def get_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def count_syllables(word):
    word = word.lower()
    if not word:
        return 1
    count = 0
    vowels = 'aeiouy'
    if word[0] in vowels:
        count += 1
    for i in range(1, len(word)):
        if word[i] in vowels and word[i-1] not in vowels:
            count += 1
    if word.endswith('e'):
        count -= 1
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1
    return max(1, count)

def fog_index(text):
    words = tokenize(text)
    sentences = get_sentences(text)
    if not words or not sentences:
        return 0
    avg_sentence_length = len(words) / len(sentences)
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)
    complex_word_pct = (complex_words / len(words)) * 100
    return round(0.4 * (avg_sentence_length + complex_word_pct), 1)

# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

def analyze_sentiment(words, lm_dict):
    words_upper = [w.upper() for w in words]
    positive = sum(1 for w in words_upper if w in lm_dict['positive'])
    negative = sum(1 for w in words_upper if w in lm_dict['negative'])
    uncertainty = sum(1 for w in words_upper if w in lm_dict['uncertainty'])
    total = len(words)
    
    return {
        'positive': positive,
        'negative': negative,
        'uncertainty': uncertainty,
        'positive_pct': round(positive / total * 100, 2) if total else 0,
        'negative_pct': round(negative / total * 100, 2) if total else 0,
        'net_sentiment': round((positive - negative) / total * 100, 2) if total else 0,
    }

def analyze_hedging(text, words):
    text_lower = text.lower()
    hedge_words = sum(1 for w in words if w in HEDGING_WORDS)
    hedge_phrases = sum(text_lower.count(phrase) for phrase in HEDGING_PHRASES)
    certainty = sum(1 for w in words if w in CERTAINTY_WORDS)
    total = len(words)
    
    return {
        'hedge_words': hedge_words,
        'hedge_phrases': hedge_phrases,
        'total_hedging': hedge_words + hedge_phrases,
        'certainty_words': certainty,
        'hedging_pct': round((hedge_words + hedge_phrases) / total * 100, 2) if total else 0,
        'certainty_pct': round(certainty / total * 100, 2) if total else 0,
        'confidence_ratio': round(certainty / (hedge_words + hedge_phrases + 1), 2),
    }

def analyze_ownership(text, words):
    text_lower = text.lower()
    first_singular = sum(1 for w in words if w in FIRST_PERSON_SINGULAR)
    first_plural = sum(1 for w in words if w in FIRST_PERSON_PLURAL)
    first_person_total = first_singular + first_plural
    distancing = sum(text_lower.count(phrase) for phrase in DISTANCING_PHRASES)
    total = len(words)
    
    return {
        'first_person_singular': first_singular,
        'first_person_plural': first_plural,
        'first_person_total': first_person_total,
        'distancing_phrases': distancing,
        'ownership_pct': round(first_person_total / total * 100, 2) if total else 0,
        'ownership_ratio': round(first_person_total / (distancing + 1), 2),
    }

def analyze_deception(text, words):
    text_lower = text.lower()
    consensus = sum(text_lower.count(phrase) for phrase in DECEPTION_MARKERS)
    extreme = sum(1 for w in words if w in EXTREME_POSITIVE)
    total = len(words)
    
    return {
        'false_consensus': consensus,
        'extreme_positive': extreme,
        'total_red_flags': consensus + extreme,
        'red_flag_pct': round((consensus + extreme) / total * 100, 3) if total else 0,
    }

def find_flagged_passages(text, max_flags=10):
    sentences = get_sentences(text)
    flagged = []
    
    for sentence in sentences:
        if len(flagged) >= max_flags:
            break
            
        issues = []
        sentence_lower = sentence.lower()
        words = tokenize(sentence)
        
        # Triple hedge
        hedge_count = sum(1 for w in words if w in HEDGING_WORDS)
        hedge_count += sum(1 for phrase in HEDGING_PHRASES if phrase in sentence_lower)
        if hedge_count >= 3:
            issues.append(f"Triple hedge ({hedge_count} markers)")
        
        # Distancing without ownership
        distancing = sum(1 for phrase in DISTANCING_PHRASES if phrase in sentence_lower)
        has_we = any(w in words for w in FIRST_PERSON_PLURAL)
        if distancing >= 1 and not has_we:
            issues.append("Distancing language")
        
        # Deception markers
        deception = sum(1 for phrase in DECEPTION_MARKERS if phrase in sentence_lower)
        if deception >= 1:
            issues.append("False consensus marker")
        
        # Excessive superlatives
        extreme = sum(1 for w in words if w in EXTREME_POSITIVE)
        if extreme >= 2:
            issues.append("Excessive superlatives")
        
        if issues:
            flagged.append({
                'sentence': sentence[:150] + ('...' if len(sentence) > 150 else ''),
                'issues': issues,
            })
    
    return flagged

def calculate_scores(analysis):
    scores = {}
    
    # Sentiment: net sentiment normalized
    net_sent = analysis['sentiment']['net_sentiment']
    scores['sentiment'] = min(100, max(0, 50 + (net_sent * 25)))
    
    # Confidence: based on ratio
    conf_ratio = analysis['hedging']['confidence_ratio']
    scores['confidence'] = min(100, max(0, conf_ratio * 30 + 40))
    
    # Ownership: based on ratio
    own_ratio = analysis['ownership']['ownership_ratio']
    scores['ownership'] = min(100, max(0, own_ratio * 5 + 40))
    
    # Clarity: inverse of Fog Index
    fog = analysis['readability']['fog_index']
    scores['clarity'] = min(100, max(0, 100 - (fog - 8) * 5))
    
    # Red flags: inverse
    red_pct = analysis['deception']['red_flag_pct']
    scores['red_flags'] = min(100, max(0, 100 - (red_pct * 100)))
    
    # Overall
    weights = {'sentiment': 0.25, 'confidence': 0.25, 'ownership': 0.15, 'clarity': 0.15, 'red_flags': 0.20}
    scores['overall'] = round(sum(scores[k] * weights[k] for k in weights), 0)
    
    return scores

def get_grade(score):
    if score >= 90: return 'A'
    if score >= 80: return 'B+'
    if score >= 70: return 'B'
    if score >= 60: return 'C+'
    if score >= 50: return 'C'
    if score >= 40: return 'D'
    return 'F'

# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_transcript(text, lm_dict):
    words = tokenize(text)
    
    analysis = {
        'word_count': len(words),
        'sentence_count': len(get_sentences(text)),
        'sentiment': analyze_sentiment(words, lm_dict),
        'hedging': analyze_hedging(text, words),
        'ownership': analyze_ownership(text, words),
        'deception': analyze_deception(text, words),
        'readability': {'fog_index': fog_index(text)},
    }
    
    analysis['scores'] = calculate_scores(analysis)
    analysis['flagged_passages'] = find_flagged_passages(text)
    
    return analysis

# ============================================================
# HISTORICAL COMPARISON
# ============================================================

def compare_to_history(current, historical):
    """Compare current analysis to historical analyses"""
    if not historical:
        return None
    
    metrics = [
        ('net_sentiment', 'sentiment', 'Net Sentiment', False),  # Higher = better
        ('hedging_pct', 'hedging', 'Hedging %', True),  # Lower = better
        ('confidence_ratio', 'hedging', 'Confidence', False),
        ('ownership_ratio', 'ownership', 'Ownership', False),
        ('red_flag_pct', 'deception', 'Red Flags', True),
    ]
    
    comparison = {
        'quarters_compared': len(historical),
        'trends': {},
        'alerts': [],
    }
    
    for metric_key, category, display_name, lower_is_better in metrics:
        current_val = current[category][metric_key]
        hist_vals = [h['analysis'][category][metric_key] for h in historical]
        avg_hist = sum(hist_vals) / len(hist_vals)
        
        if avg_hist != 0:
            pct_change = ((current_val - avg_hist) / abs(avg_hist)) * 100
        else:
            pct_change = 0 if current_val == 0 else 100
        
        # Direction arrow
        if abs(pct_change) < 5:
            direction = '→'
            status = 'stable'
        elif pct_change > 0:
            direction = '↑'
            status = 'worse' if lower_is_better else 'better'
        else:
            direction = '↓'
            status = 'better' if lower_is_better else 'worse'
        
        comparison['trends'][metric_key] = {
            'current': round(current_val, 3),
            'historical_avg': round(avg_hist, 3),
            'change_pct': round(pct_change, 1),
            'direction': direction,
            'status': status,
            'display_name': display_name,
        }
        
        # Generate alerts
        if abs(pct_change) > 20 and status == 'worse':
            if metric_key == 'hedging_pct':
                comparison['alerts'].append(f"⚠️ HEDGING UP {pct_change:.0f}% vs historical avg — may signal uncertainty")
            elif metric_key == 'confidence_ratio':
                comparison['alerts'].append(f"⚠️ CONFIDENCE DOWN {abs(pct_change):.0f}% vs historical avg")
            elif metric_key == 'net_sentiment':
                comparison['alerts'].append(f"⚠️ SENTIMENT DOWN {abs(pct_change):.0f}% vs historical avg")
            elif metric_key == 'red_flag_pct':
                comparison['alerts'].append(f"🔴 RED FLAGS UP {pct_change:.0f}% vs historical avg — possible deception markers")
    
    return comparison

# ============================================================
# REPORT FORMATTING
# ============================================================

def format_report(analysis, ticker=None, quarter=None, comparison=None, historical=None, legal_analysis=None):
    lines = []
    scores = analysis['scores']
    
    # Header
    lines.append("=" * 65)
    if ticker:
        lines.append(f"EARNINGS SCRIPT ANALYSIS: {ticker} {quarter or ''}")
    else:
        lines.append("EARNINGS SCRIPT ANALYSIS REPORT")
    lines.append("=" * 65)
    lines.append("")
    
    # Overall score
    grade = get_grade(scores['overall'])
    lines.append(f"OVERALL SCORE: {int(scores['overall'])}/100 ({grade})")
    
    # Show legal-adjusted confidence if available
    if legal_analysis and legal_analysis.get('overall_adjusted_confidence') is not None:
        adj_conf = legal_analysis['overall_adjusted_confidence']
        lines.append(f"LEGAL-ADJUSTED CONFIDENCE: {int(adj_conf)}/100")
        lines.append("  (Accounts for appropriate hedging in forward-looking sections)")
    
    lines.append("")
    
    # Dimension scores
    lines.append("DIMENSION SCORES:")
    dims = [
        ('Sentiment', 'sentiment', 60),
        ('Confidence', 'confidence', 60),
        ('Ownership', 'ownership', 60),
        ('Clarity', 'clarity', 60),
        ('Red Flags', 'red_flags', 80),
    ]
    for label, key, threshold in dims:
        score = int(scores[key])
        emoji = '🟢' if score >= threshold else '🟡' if score >= 40 else '🔴'
        lines.append(f"  {label:12s} {score:3d}/100  {emoji}")
    
    # Section-by-section analysis if available
    if legal_analysis and legal_analysis.get('sections'):
        lines.append("")
        lines.append("-" * 65)
        lines.append("SECTION-BY-SECTION ANALYSIS (Legal Context)")
        lines.append("-" * 65)
        
        section_labels = {
            'safe_harbor': '⚖️  SAFE HARBOR',
            'forward_looking': '📈 FORWARD-LOOKING',
            'qa': '❓ Q&A',
            'factual': '📊 RESULTS/FACTUAL',
            'general': '📝 GENERAL',
            'prepared_remarks': '📋 PREPARED REMARKS',
        }
        
        for section in legal_analysis['sections']:
            section_type = section['type']
            section_scores = section['analysis']['scores']
            label = section_labels.get(section_type, section_type.upper())
            
            lines.append(f"\n{label}")
            
            if section_type == 'safe_harbor':
                lines.append("  [Excluded from scoring - legal disclaimer]")
            else:
                raw_conf = section_scores.get('confidence', 0)
                adj_conf = section_scores.get('adjusted_confidence')
                
                if adj_conf is not None and adj_conf != raw_conf:
                    lines.append(f"  Raw Confidence:      {int(raw_conf)}/100")
                    lines.append(f"  Adjusted Confidence: {int(adj_conf)}/100")
                    
                    if section_type == 'forward_looking':
                        lines.append("  ✓ Hedging appropriate for forward-looking statements")
                    elif section_type == 'qa':
                        lines.append("  ⚠️ Hedging in Q&A may signal uncertainty")
                    elif section_type == 'factual':
                        lines.append("  ⚠️ Results should be stated with confidence")
                else:
                    lines.append(f"  Confidence: {int(raw_conf)}/100")
                
                # Show section note if available
                note = section['analysis'].get('legal_note')
                if note:
                    lines.append(f"  Note: {note}")
    lines.append("")
    
    # Historical comparison
    if comparison:
        lines.append("-" * 65)
        lines.append("HISTORICAL COMPARISON")
        lines.append("-" * 65)
        lines.append(f"Comparing to: {', '.join(h['quarter'] for h in historical)}")
        lines.append("")
        
        lines.append("METRIC TRENDS:")
        for key, data in comparison['trends'].items():
            sign = '+' if data['change_pct'] > 0 else ''
            status_emoji = '✓' if data['status'] == 'better' else '⚠' if data['status'] == 'worse' else '·'
            lines.append(f"  {data['display_name']:15s} {data['direction']} {sign}{data['change_pct']:.1f}%  (now: {data['current']:.2f}, avg: {data['historical_avg']:.2f}) {status_emoji}")
        lines.append("")
        
        if comparison['alerts']:
            lines.append("ALERTS:")
            for alert in comparison['alerts']:
                lines.append(f"  {alert}")
            lines.append("")
        else:
            lines.append("✅ No significant deviations from historical patterns")
            lines.append("")
        
        # Historical scores
        lines.append("HISTORICAL SCORES:")
        for h in historical:
            s = h['analysis']['scores']
            lines.append(f"  {h['quarter']:12s} Overall: {int(s['overall']):3d}/100 ({get_grade(s['overall'])})")
        lines.append(f"  {'CURRENT':12s} Overall: {int(scores['overall']):3d}/100 ({grade})")
        lines.append("")
    
    # Detailed metrics
    lines.append("-" * 65)
    lines.append("DETAILED METRICS")
    lines.append("-" * 65)
    lines.append("")
    
    s = analysis['sentiment']
    lines.append("SENTIMENT (Loughran-McDonald):")
    lines.append(f"  Positive words:    {s['positive']:4d} ({s['positive_pct']:.2f}%)")
    lines.append(f"  Negative words:    {s['negative']:4d} ({s['negative_pct']:.2f}%)")
    lines.append(f"  Net sentiment:     {s['net_sentiment']:+.2f}%")
    lines.append("")
    
    h = analysis['hedging']
    lines.append("CONFIDENCE vs HEDGING:")
    lines.append(f"  Hedging words:     {h['hedge_words']:4d}")
    lines.append(f"  Hedging phrases:   {h['hedge_phrases']:4d}")
    lines.append(f"  Certainty words:   {h['certainty_words']:4d}")
    lines.append(f"  Confidence ratio:  {h['confidence_ratio']:.2f}")
    lines.append("")
    
    o = analysis['ownership']
    lines.append("OWNERSHIP:")
    lines.append(f"  'I/me/my':         {o['first_person_singular']:4d}")
    lines.append(f"  'We/us/our':       {o['first_person_plural']:4d}")
    lines.append(f"  Distancing:        {o['distancing_phrases']:4d}")
    lines.append(f"  Ownership ratio:   {o['ownership_ratio']:.2f}")
    lines.append("")
    
    # Flagged passages
    if analysis['flagged_passages']:
        lines.append("-" * 65)
        lines.append("FLAGGED PASSAGES")
        lines.append("-" * 65)
        for i, fp in enumerate(analysis['flagged_passages'][:8], 1):
            lines.append(f"\n{i}. \"{fp['sentence']}\"")
            for issue in fp['issues']:
                lines.append(f"   ⚠️  {issue}")
    
    lines.append("")
    lines.append("=" * 65)
    
    return "\n".join(lines)

# ============================================================
# CLI
# ============================================================

def print_usage():
    print("""
Earnings Script Analyzer

USAGE:
  python earnings_analyzer.py <transcript.txt>
  python earnings_analyzer.py <transcript.txt> --compare TICKER
  python earnings_analyzer.py --analyze TICKER [--quarters N]

OPTIONS:
  --compare TICKER   Compare your script against TICKER's last 4 quarters
  --analyze TICKER   Fetch and analyze TICKER's last N transcripts
  --quarters N       Number of historical quarters (default: 4)
  --legal            Enable legal-aware analysis (section-by-section)
  --pdf FILE         Export highlighted PDF report
  --word FILE        Export Word doc with track changes
  --json             Output as JSON

EXAMPLES:
  python earnings_analyzer.py my_script.txt
  python earnings_analyzer.py my_script.txt --pdf report.pdf --word revisions.docx
  python earnings_analyzer.py my_script.txt --compare AAPL
  python earnings_analyzer.py --analyze NVDA --quarters 4
""")

if __name__ == "__main__":
    if len(sys.argv) < 2 or '--help' in sys.argv:
        print_usage()
        sys.exit(0)
    
    # Load dictionary
    script_dir = Path(__file__).parent
    lm_dict = load_lm_dictionary(script_dir / "LM_MasterDictionary.csv")
    
    # Parse args
    input_file = None
    compare_ticker = None
    analyze_ticker = None
    quarters = 4
    json_output = '--json' in sys.argv
    legal_mode = '--legal' in sys.argv
    pdf_output = None
    word_output = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--compare' and i + 1 < len(sys.argv):
            compare_ticker = sys.argv[i + 1].upper()
            i += 2
        elif arg == '--analyze' and i + 1 < len(sys.argv):
            analyze_ticker = sys.argv[i + 1].upper()
            i += 2
        elif arg == '--quarters' and i + 1 < len(sys.argv):
            quarters = int(sys.argv[i + 1])
            i += 2
        elif arg == '--pdf' and i + 1 < len(sys.argv):
            pdf_output = sys.argv[i + 1]
            i += 2
        elif arg == '--word' and i + 1 < len(sys.argv):
            word_output = sys.argv[i + 1]
            i += 2
        elif arg in ('--json', '--legal'):
            i += 1
        elif not arg.startswith('-'):
            input_file = arg
            i += 1
        else:
            i += 1
    
    # Mode: Analyze a ticker's historical transcripts
    if analyze_ticker:
        print(f"\nFetching {quarters} transcripts for {analyze_ticker}...\n", file=sys.stderr)
        transcripts = fetch_transcripts(analyze_ticker, quarters)
        
        if not transcripts:
            print(f"No transcripts found for {analyze_ticker}", file=sys.stderr)
            sys.exit(1)
        
        # Analyze all
        analyses = []
        for t in transcripts:
            analysis = analyze_transcript(t['text'], lm_dict)
            analyses.append({
                'quarter': t['quarter'],
                'url': t['url'],
                'analysis': analysis,
            })
        
        # Compare most recent to historical
        if len(analyses) > 1:
            current = analyses[0]['analysis']
            historical = analyses[1:]
            comparison = compare_to_history(current, historical)
            
            print(format_report(
                current, 
                ticker=analyze_ticker, 
                quarter=analyses[0]['quarter'],
                comparison=comparison,
                historical=historical
            ))
        else:
            print(format_report(analyses[0]['analysis'], ticker=analyze_ticker, quarter=analyses[0]['quarter']))
        
        sys.exit(0)
    
    # Mode: Analyze input file
    if not input_file:
        print("Error: No input file specified", file=sys.stderr)
        print_usage()
        sys.exit(1)
    
    with open(input_file, 'r') as f:
        text = f.read()
    
    analysis = analyze_transcript(text, lm_dict)
    
    # Legal-aware analysis if requested
    legal_analysis = None
    if legal_mode:
        legal_analysis = analyze_with_legal_context(text, analyze_transcript, lm_dict)
    
    # Compare to ticker if requested
    comparison = None
    historical = None
    
    if compare_ticker:
        print(f"\nFetching historical transcripts for {compare_ticker}...\n", file=sys.stderr)
        transcripts = fetch_transcripts(compare_ticker, quarters)
        
        if transcripts:
            historical = []
            for t in transcripts:
                hist_analysis = analyze_transcript(t['text'], lm_dict)
                historical.append({
                    'quarter': t['quarter'],
                    'analysis': hist_analysis,
                })
            comparison = compare_to_history(analysis, historical)
    
    # Export PDF if requested
    if pdf_output:
        from exporters import export_pdf
        export_pdf(text, analysis, pdf_output, ticker=compare_ticker)
        print(f"✓ PDF exported to: {pdf_output}", file=sys.stderr)
    
    # Export Word if requested
    if word_output:
        from exporters import export_word
        export_word(text, analysis, word_output, ticker=compare_ticker)
        print(f"✓ Word doc exported to: {word_output}", file=sys.stderr)
    
    # Output
    if json_output:
        output = {
            'analysis': analysis,
            'comparison': comparison,
            'legal_analysis': legal_analysis,
        }
        output['analysis']['flagged_passages'] = output['analysis']['flagged_passages'][:5]
        print(json.dumps(output, indent=2, default=str))
    elif not (pdf_output or word_output):
        # Only print report if not exporting
        print(format_report(analysis, comparison=comparison, historical=historical, legal_analysis=legal_analysis))
    else:
        # Print brief summary when exporting
        scores = analysis['scores']
        print(f"\nAnalysis complete: {int(scores['overall'])}/100 ({get_grade(scores['overall'])})", file=sys.stderr)
        if legal_analysis and legal_analysis.get('overall_adjusted_confidence'):
            print(f"Legal-adjusted confidence: {int(legal_analysis['overall_adjusted_confidence'])}/100", file=sys.stderr)
