#!/usr/bin/env python3
"""
Earnings Script Analyzer v2
Now with historical comparison and transcript fetching
"""

import re
import csv
import json
import sys
import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import quote

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
        'modal_strong': set(),
        'modal_weak': set(),
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
            modal = row.get('Modal', '0')
            if modal == '1':
                categories['modal_strong'].add(word)
            elif modal in ('2', '3'):
                categories['modal_weak'].add(word)
    
    return categories

# ============================================================
# TRANSCRIPT FETCHING
# ============================================================

def fetch_fool_transcript(ticker, year, quarter):
    """
    Fetch transcript from The Motley Fool
    Returns transcript text or None if not found
    """
    # Motley Fool URL pattern
    # They use URLs like: /earnings/call-transcripts/2025/01/30/apple-aapl-q1-2025-earnings-call-transcript/
    
    # First, search for the transcript
    search_url = f"https://www.fool.com/search/?q={ticker}+earnings+call+transcript+Q{quarter}+{year}"
    
    try:
        req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        # This is a simplified approach - real implementation would parse search results
        # For MVP, we'll indicate this needs API access
        return None
    except Exception as e:
        return None

def fetch_fmp_transcript(ticker, year, quarter, api_key):
    """
    Fetch transcript from Financial Modeling Prep API
    Requires API key (free tier available)
    """
    url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}?quarter={quarter}&year={year}&apikey={api_key}"
    
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req, timeout=10)
        data = json.loads(response.read().decode())
        
        if data and len(data) > 0:
            return data[0].get('content', None)
        return None
    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        return None

def fetch_last_n_transcripts(ticker, n=4, api_key=None):
    """
    Fetch the last N earnings transcripts for a ticker
    Returns list of (quarter_label, transcript_text) tuples
    """
    transcripts = []
    
    # Calculate last N quarters
    now = datetime.now()
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    
    quarters_to_fetch = []
    y, q = current_year, current_quarter
    for _ in range(n + 1):  # +1 to include current
        quarters_to_fetch.append((y, q))
        q -= 1
        if q == 0:
            q = 4
            y -= 1
    
    if not api_key:
        api_key = os.environ.get('FMP_API_KEY')
    
    if not api_key:
        print("Warning: No API key provided. Set FMP_API_KEY env var or pass --api-key", file=sys.stderr)
        return []
    
    for year, quarter in quarters_to_fetch:
        label = f"Q{quarter} {year}"
        print(f"Fetching {ticker} {label}...", file=sys.stderr)
        
        text = fetch_fmp_transcript(ticker, year, quarter, api_key)
        if text:
            transcripts.append((label, text))
            print(f"  ✓ Found ({len(text)} chars)", file=sys.stderr)
        else:
            print(f"  ✗ Not found", file=sys.stderr)
        
        if len(transcripts) >= n:
            break
    
    return transcripts

# ============================================================
# CUSTOM PATTERN LISTS
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
    words = re.findall(r"\b[\w']+\b", text)
    return words

def get_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def count_syllables(word):
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    if len(word) == 0:
        return 1
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
    fog = 0.4 * (avg_sentence_length + complex_word_pct)
    return round(fog, 1)

# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

def analyze_sentiment(words, lm_dict):
    words_upper = [w.upper() for w in words]
    positive = sum(1 for w in words_upper if w in lm_dict['positive'])
    negative = sum(1 for w in words_upper if w in lm_dict['negative'])
    uncertainty = sum(1 for w in words_upper if w in lm_dict['uncertainty'])
    litigious = sum(1 for w in words_upper if w in lm_dict['litigious'])
    constraining = sum(1 for w in words_upper if w in lm_dict['constraining'])
    total = len(words)
    
    return {
        'positive': positive,
        'negative': negative,
        'uncertainty': uncertainty,
        'litigious': litigious,
        'constraining': constraining,
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
        'distancing_pct': round(distancing / total * 100, 2) if total else 0,
        'ownership_ratio': round(first_person_total / (distancing + 1), 2),
    }

def analyze_deception_markers(text, words):
    text_lower = text.lower()
    consensus_markers = sum(text_lower.count(phrase) for phrase in DECEPTION_MARKERS)
    extreme_pos = sum(1 for w in words if w in EXTREME_POSITIVE)
    total = len(words)
    
    return {
        'false_consensus_markers': consensus_markers,
        'extreme_positive_words': extreme_pos,
        'total_red_flags': consensus_markers + extreme_pos,
        'red_flag_pct': round((consensus_markers + extreme_pos) / total * 100, 3) if total else 0,
    }

def find_flagged_passages(text):
    sentences = get_sentences(text)
    flagged = []
    
    for sentence in sentences:
        issues = []
        sentence_lower = sentence.lower()
        words = tokenize(sentence)
        
        hedge_count = sum(1 for w in words if w in HEDGING_WORDS)
        hedge_count += sum(1 for phrase in HEDGING_PHRASES if phrase in sentence_lower)
        if hedge_count >= 3:
            issues.append(f"Triple hedge detected ({hedge_count} hedging markers)")
        
        distancing = sum(1 for phrase in DISTANCING_PHRASES if phrase in sentence_lower)
        if distancing >= 1 and not any(w in words for w in FIRST_PERSON_PLURAL):
            issues.append("Distancing language without ownership")
        
        deception = sum(1 for phrase in DECEPTION_MARKERS if phrase in sentence_lower)
        if deception >= 1:
            issues.append("False consensus/overselling marker")
        
        extreme = sum(1 for w in words if w in EXTREME_POSITIVE)
        if extreme >= 2:
            issues.append("Excessive superlatives")
        
        if issues:
            flagged.append({'sentence': sentence, 'issues': issues})
    
    return flagged

def calculate_scores(analysis):
    scores = {}
    net_sent = analysis['sentiment']['net_sentiment']
    scores['sentiment'] = min(100, max(0, 50 + (net_sent * 25)))
    
    conf_ratio = analysis['hedging']['confidence_ratio']
    scores['confidence'] = min(100, max(0, conf_ratio * 30 + 40))
    
    own_ratio = analysis['ownership']['ownership_ratio']
    scores['ownership'] = min(100, max(0, own_ratio * 10 + 30))
    
    fog = analysis['readability']['fog_index']
    scores['clarity'] = min(100, max(0, 100 - (fog - 8) * 5))
    
    red_flag_pct = analysis['deception']['red_flag_pct']
    scores['red_flags'] = min(100, max(0, 100 - (red_flag_pct * 100)))
    
    weights = {
        'sentiment': 0.25,
        'confidence': 0.25,
        'ownership': 0.15,
        'clarity': 0.15,
        'red_flags': 0.20,
    }
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
        'deception': analyze_deception_markers(text, words),
        'readability': {'fog_index': fog_index(text)},
    }
    
    analysis['scores'] = calculate_scores(analysis)
    analysis['flagged_passages'] = find_flagged_passages(text)
    
    return analysis

# ============================================================
# HISTORICAL COMPARISON
# ============================================================

def compare_analyses(current, historical):
    """
    Compare current analysis to list of historical analyses
    Returns comparison metrics with trends
    """
    if not historical:
        return None
    
    comparison = {
        'quarters_compared': len(historical),
        'trends': {},
        'alerts': [],
    }
    
    # Key metrics to track
    metrics = [
        ('net_sentiment', 'sentiment', 'Net Sentiment'),
        ('hedging_pct', 'hedging', 'Hedging'),
        ('confidence_ratio', 'hedging', 'Confidence Ratio'),
        ('ownership_ratio', 'ownership', 'Ownership'),
        ('red_flag_pct', 'deception', 'Red Flags'),
    ]
    
    for metric_key, category, display_name in metrics:
        current_val = current[category][metric_key]
        hist_vals = [h['analysis'][category][metric_key] for h in historical]
        avg_hist = sum(hist_vals) / len(hist_vals)
        
        # Calculate change
        if avg_hist != 0:
            pct_change = ((current_val - avg_hist) / abs(avg_hist)) * 100
        else:
            pct_change = 0 if current_val == 0 else 100
        
        # Determine direction
        if pct_change > 5:
            direction = '↑'
        elif pct_change < -5:
            direction = '↓'
        else:
            direction = '→'
        
        comparison['trends'][metric_key] = {
            'current': round(current_val, 3),
            'historical_avg': round(avg_hist, 3),
            'change_pct': round(pct_change, 1),
            'direction': direction,
            'display_name': display_name,
        }
        
        # Generate alerts for significant changes
        if metric_key == 'hedging_pct' and pct_change > 20:
            comparison['alerts'].append(f"⚠️ Hedging up {pct_change:.0f}% vs historical average")
        elif metric_key == 'confidence_ratio' and pct_change < -20:
            comparison['alerts'].append(f"⚠️ Confidence down {abs(pct_change):.0f}% vs historical average")
        elif metric_key == 'net_sentiment' and pct_change < -30:
            comparison['alerts'].append(f"⚠️ Sentiment dropped {abs(pct_change):.0f}% vs historical average")
        elif metric_key == 'red_flag_pct' and pct_change > 30:
            comparison['alerts'].append(f"🔴 Red flags up {pct_change:.0f}% vs historical average")
    
    return comparison

def format_comparison_report(current_analysis, historical, comparison):
    """Generate comparison report"""
    report = []
    report.append("")
    report.append("=" * 60)
    report.append("HISTORICAL COMPARISON")
    report.append("=" * 60)
    report.append("")
    report.append(f"Comparing to: {', '.join(h['label'] for h in historical)}")
    report.append("")
    
    # Trend table
    report.append("METRIC TRENDS:")
    report.append("-" * 50)
    for key, data in comparison['trends'].items():
        arrow = data['direction']
        change = data['change_pct']
        sign = '+' if change > 0 else ''
        report.append(f"  {data['display_name']:20s} {arrow} {sign}{change:.1f}% vs avg")
        report.append(f"    Current: {data['current']:.3f}  |  Hist Avg: {data['historical_avg']:.3f}")
    report.append("")
    
    # Alerts
    if comparison['alerts']:
        report.append("ALERTS:")
        for alert in comparison['alerts']:
            report.append(f"  {alert}")
        report.append("")
    else:
        report.append("✅ No significant deviations from historical patterns")
        report.append("")
    
    # Quarter-by-quarter scores
    report.append("HISTORICAL SCORES:")
    report.append("-" * 50)
    for h in historical:
        scores = h['analysis']['scores']
        report.append(f"  {h['label']:10s}  Overall: {int(scores['overall']):3d}/100 ({get_grade(scores['overall'])})")
    report.append(f"  {'CURRENT':10s}  Overall: {int(current_analysis['scores']['overall']):3d}/100 ({get_grade(current_analysis['scores']['overall'])})")
    
    return "\n".join(report)

# ============================================================
# REPORT FORMATTING
# ============================================================

def format_report(analysis, comparison=None, historical=None):
    scores = analysis['scores']
    
    report = []
    report.append("=" * 60)
    report.append("EARNINGS SCRIPT ANALYSIS REPORT")
    report.append("=" * 60)
    report.append("")
    
    grade = get_grade(scores['overall'])
    report.append(f"OVERALL SCORE: {int(scores['overall'])}/100 ({grade})")
    report.append("")
    
    report.append("DIMENSION SCORES:")
    report.append(f"  Sentiment:   {int(scores['sentiment']):3d}/100  {'🟢' if scores['sentiment'] >= 60 else '🟡' if scores['sentiment'] >= 40 else '🔴'}")
    report.append(f"  Confidence:  {int(scores['confidence']):3d}/100  {'🟢' if scores['confidence'] >= 60 else '🟡' if scores['confidence'] >= 40 else '🔴'}")
    report.append(f"  Ownership:   {int(scores['ownership']):3d}/100  {'🟢' if scores['ownership'] >= 60 else '🟡' if scores['ownership'] >= 40 else '🔴'}")
    report.append(f"  Clarity:     {int(scores['clarity']):3d}/100  {'🟢' if scores['clarity'] >= 60 else '🟡' if scores['clarity'] >= 40 else '🔴'}")
    report.append(f"  Red Flags:   {int(scores['red_flags']):3d}/100  {'🟢' if scores['red_flags'] >= 80 else '🟡' if scores['red_flags'] >= 60 else '🔴'}")
    report.append("")
    
    # Add comparison section if available
    if comparison and historical:
        report.append(format_comparison_report(analysis, historical, comparison))
    
    report.append("-" * 60)
    report.append("DETAILED METRICS")
    report.append("-" * 60)
    report.append("")
    
    report.append("SENTIMENT (Loughran-McDonald):")
    s = analysis['sentiment']
    report.append(f"  Positive words:    {s['positive']:4d} ({s['positive_pct']:.2f}%)")
    report.append(f"  Negative words:    {s['negative']:4d} ({s['negative_pct']:.2f}%)")
    report.append(f"  Net sentiment:     {s['net_sentiment']:+.2f}%")
    report.append(f"  Uncertainty words: {s['uncertainty']:4d}")
    report.append("")
    
    report.append("CONFIDENCE vs HEDGING:")
    h = analysis['hedging']
    report.append(f"  Hedging words:     {h['hedge_words']:4d}")
    report.append(f"  Hedging phrases:   {h['hedge_phrases']:4d}")
    report.append(f"  Certainty words:   {h['certainty_words']:4d}")
    report.append(f"  Confidence ratio:  {h['confidence_ratio']:.2f} (higher = better)")
    report.append("")
    
    report.append("OWNERSHIP (First-Person Language):")
    o = analysis['ownership']
    report.append(f"  'I/me/my':         {o['first_person_singular']:4d}")
    report.append(f"  'We/us/our':       {o['first_person_plural']:4d}")
    report.append(f"  Distancing:        {o['distancing_phrases']:4d}")
    report.append(f"  Ownership ratio:   {o['ownership_ratio']:.2f} (higher = better)")
    report.append("")
    
    report.append("READABILITY:")
    report.append(f"  Fog Index:         {analysis['readability']['fog_index']:.1f}")
    report.append("")
    
    report.append("RED FLAGS (Deception Markers):")
    d = analysis['deception']
    report.append(f"  False consensus:   {d['false_consensus_markers']:4d}")
    report.append(f"  Extreme positive:  {d['extreme_positive_words']:4d}")
    report.append("")
    
    if analysis['flagged_passages']:
        report.append("-" * 60)
        report.append("FLAGGED PASSAGES")
        report.append("-" * 60)
        for i, fp in enumerate(analysis['flagged_passages'][:10], 1):
            report.append(f"\n{i}. \"{fp['sentence'][:100]}{'...' if len(fp['sentence']) > 100 else ''}\"")
            for issue in fp['issues']:
                report.append(f"   ⚠️  {issue}")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)

# ============================================================
# CLI ENTRY POINT
# ============================================================

def print_usage():
    print("""
Earnings Script Analyzer v2

USAGE:
  python analyzer_v2.py <transcript_file>
  python analyzer_v2.py <transcript_file> --compare TICKER [--api-key KEY]
  python analyzer_v2.py --fetch TICKER [--quarters N] [--api-key KEY]

OPTIONS:
  --compare TICKER   Compare against last 4 quarters for TICKER
  --fetch TICKER     Fetch and analyze last N transcripts
  --quarters N       Number of quarters to fetch (default: 4)
  --api-key KEY      Financial Modeling Prep API key
  --json             Output as JSON

EXAMPLES:
  python analyzer_v2.py my_script.txt
  python analyzer_v2.py my_script.txt --compare AAPL --api-key YOUR_KEY
  python analyzer_v2.py --fetch AAPL --quarters 4 --api-key YOUR_KEY

Get a free API key at: https://financialmodelingprep.com/developer/docs/
""")

if __name__ == "__main__":
    if len(sys.argv) < 2 or '--help' in sys.argv:
        print_usage()
        sys.exit(0)
    
    script_dir = Path(__file__).parent
    lm_dict = load_lm_dictionary(script_dir / "LM_MasterDictionary.csv")
    
    # Parse arguments
    api_key = None
    ticker = None
    quarters = 4
    compare_mode = False
    fetch_mode = False
    json_output = '--json' in sys.argv
    
    args = sys.argv[1:]
    i = 0
    input_file = None
    
    while i < len(args):
        arg = args[i]
        if arg == '--api-key' and i + 1 < len(args):
            api_key = args[i + 1]
            i += 2
        elif arg == '--compare' and i + 1 < len(args):
            compare_mode = True
            ticker = args[i + 1]
            i += 2
        elif arg == '--fetch' and i + 1 < len(args):
            fetch_mode = True
            ticker = args[i + 1]
            i += 2
        elif arg == '--quarters' and i + 1 < len(args):
            quarters = int(args[i + 1])
            i += 2
        elif arg == '--json':
            i += 1
        elif arg == '-':
            input_file = '-'
            i += 1
        elif not arg.startswith('-'):
            input_file = arg
            i += 1
        else:
            i += 1
    
    # Fetch mode: just fetch and analyze historical transcripts
    if fetch_mode and ticker:
        print(f"Fetching last {quarters} transcripts for {ticker}...", file=sys.stderr)
        transcripts = fetch_last_n_transcripts(ticker, quarters, api_key)
        
        if not transcripts:
            print("No transcripts found. Check your API key.", file=sys.stderr)
            sys.exit(1)
        
        print(f"\nFound {len(transcripts)} transcripts\n", file=sys.stderr)
        
        for label, text in transcripts:
            analysis = analyze_transcript(text, lm_dict)
            print(f"\n{'='*60}")
            print(f"{ticker} - {label}")
            print(f"{'='*60}")
            scores = analysis['scores']
            print(f"Overall: {int(scores['overall'])}/100 ({get_grade(scores['overall'])})")
            print(f"  Sentiment: {analysis['sentiment']['net_sentiment']:+.2f}%")
            print(f"  Hedging: {analysis['hedging']['hedging_pct']:.2f}%")
            print(f"  Confidence ratio: {analysis['hedging']['confidence_ratio']:.2f}")
        
        sys.exit(0)
    
    # Read input transcript
    if input_file == '-':
        text = sys.stdin.read()
    elif input_file:
        with open(input_file, 'r') as f:
            text = f.read()
    else:
        print("Error: No input file specified", file=sys.stderr)
        print_usage()
        sys.exit(1)
    
    # Analyze current transcript
    analysis = analyze_transcript(text, lm_dict)
    
    # Compare mode: fetch historical and compare
    historical = []
    comparison = None
    
    if compare_mode and ticker:
        print(f"Fetching historical transcripts for {ticker}...", file=sys.stderr)
        transcripts = fetch_last_n_transcripts(ticker, quarters, api_key)
        
        for label, hist_text in transcripts:
            hist_analysis = analyze_transcript(hist_text, lm_dict)
            historical.append({
                'label': label,
                'analysis': hist_analysis,
            })
        
        if historical:
            comparison = compare_analyses(analysis, historical)
    
    # Output
    if json_output:
        output = {
            'current': analysis,
            'comparison': comparison,
            'historical': [{'label': h['label'], 'scores': h['analysis']['scores']} for h in historical] if historical else None,
        }
        # Limit flagged passages for JSON
        output['current']['flagged_passages'] = output['current']['flagged_passages'][:5]
        print(json.dumps(output, indent=2))
    else:
        print(format_report(analysis, comparison, historical))
