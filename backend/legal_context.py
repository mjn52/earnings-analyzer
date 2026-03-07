#!/usr/bin/env python3
"""
Legal Context Module for Earnings Script Analyzer
Handles PSLRA safe harbor language and forward-looking statement detection
"""

import re

# ============================================================
# SAFE HARBOR DETECTION
# ============================================================

SAFE_HARBOR_PHRASES = [
    'forward-looking statement',
    'forward looking statement',
    'forward-looking information',
    'risks and uncertainties',
    'actual results may differ',
    'actual results could differ',
    'no obligation to update',
    'speaks only as of',
    'form 10-k',
    'form 10-q',
    'form 8-k',
    'sec filing',
    'risk factors',
    'private securities litigation reform act',
    'safe harbor',
]

# These words are LEGALLY REQUIRED to identify forward-looking statements
# They should NOT be penalized when used properly
FLS_IDENTIFIER_WORDS = {
    'expect', 'expects', 'expected', 'expecting',
    'anticipate', 'anticipates', 'anticipated', 'anticipating',
    'believe', 'believes', 'believed', 'believing',
    'estimate', 'estimates', 'estimated', 'estimating',
    'project', 'projects', 'projected', 'projecting',
    'forecast', 'forecasts', 'forecasted', 'forecasting',
    'intend', 'intends', 'intended', 'intending',
    'plan', 'plans', 'planned', 'planning',
    'may', 'might', 'could', 'would', 'should',
    'will', 'shall',
    'outlook', 'guidance', 'target', 'goal',
}

# Phrases that indicate forward-looking content
FLS_CONTEXT_PHRASES = [
    'looking ahead',
    'going forward',  # This is OK in FLS context, not OK elsewhere
    'for the quarter',
    'for the year',
    'for fiscal',
    'we expect',
    'we anticipate',
    'we believe',
    'we project',
    'we estimate',
    'our guidance',
    'our outlook',
    'our forecast',
    'next quarter',
    'next year',
    'coming months',
    'coming quarters',
    'full year',
    'second half',
    'first half',
]

# Section headers that indicate forward-looking content
FLS_SECTION_HEADERS = [
    'guidance',
    'outlook',
    'forward-looking',
    'expectations',
    'forecast',
    'projections',
    'looking ahead',
    'future',
]

# Section headers that indicate historical/factual content (hedging = bad here)
FACTUAL_SECTION_HEADERS = [
    'results',
    'performance',
    'highlights',
    'overview',
    'quarter results',
    'financial results',
    'operating results',
]

# Q&A indicators (hedging = more concerning here)
QA_INDICATORS = [
    'question',
    'q&a',
    'questions and answers',
    'analyst:',
    'operator:',
    '-- analyst',
]


def is_safe_harbor_section(text):
    """Check if text is part of a safe harbor disclaimer"""
    text_lower = text.lower()
    matches = sum(1 for phrase in SAFE_HARBOR_PHRASES if phrase in text_lower)
    return matches >= 2  # Multiple safe harbor phrases = definitely a disclaimer


def is_forward_looking_context(sentence, surrounding_text=""):
    """
    Determine if a sentence is in a forward-looking context
    where hedging language is legally appropriate
    """
    text_lower = sentence.lower()
    context_lower = surrounding_text.lower() if surrounding_text else ""
    
    # Check for FLS context phrases
    fls_phrases = sum(1 for phrase in FLS_CONTEXT_PHRASES if phrase in text_lower)
    
    # Check surrounding context too
    if context_lower:
        fls_phrases += sum(1 for phrase in FLS_CONTEXT_PHRASES if phrase in context_lower)
    
    # Check for temporal future references
    future_refs = len(re.findall(r'\b(next|future|upcoming|coming|will|going to)\b', text_lower))
    
    # Check for guidance-specific language
    guidance_words = len(re.findall(r'\b(guidance|outlook|expect|forecast|target|range)\b', text_lower))
    
    return (fls_phrases >= 1) or (future_refs >= 2) or (guidance_words >= 2)


def is_qa_section(text):
    """Check if text is from the Q&A section"""
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in QA_INDICATORS)


def classify_section(text):
    """
    Classify a block of text as:
    - 'safe_harbor': Legal disclaimer, ignore for scoring
    - 'forward_looking': Guidance/outlook, hedging is appropriate
    - 'qa': Q&A section, hedging is a red flag
    - 'factual': Results discussion, hedging is a red flag
    - 'general': Default
    """
    text_lower = text.lower()
    
    if is_safe_harbor_section(text):
        return 'safe_harbor'
    
    # Check section headers
    for header in FLS_SECTION_HEADERS:
        if header in text_lower[:200]:  # Check near start of section
            return 'forward_looking'
    
    for header in FACTUAL_SECTION_HEADERS:
        if header in text_lower[:200]:
            return 'factual'
    
    if is_qa_section(text):
        return 'qa'
    
    # Check content
    if is_forward_looking_context(text):
        return 'forward_looking'
    
    return 'general'


def split_transcript_sections(text):
    """
    Split a transcript into logical sections with classifications
    Returns list of (section_type, section_text) tuples
    """
    sections = []
    
    # Common section markers
    section_patterns = [
        r'(prepared remarks?:?)',
        r'(questions?\s*(?:and|&)\s*answers?:?)',
        r'(q\s*&\s*a:?)',
        r'(guidance:?)',
        r'(outlook:?)',
        r'(forward[- ]looking:?)',
        r'((?:first|second|third|fourth|q[1-4])\s*(?:quarter\s*)?(?:fiscal\s*)?(?:20\d{2}\s*)?(?:results?|highlights?|overview):?)',
    ]
    
    combined_pattern = '|'.join(section_patterns)
    
    # Split by section headers
    parts = re.split(f'(?i)({combined_pattern})', text)
    
    current_section = 'general'
    current_text = []
    
    for part in parts:
        if not part or not part.strip():
            continue
        
        part_lower = part.lower().strip()
        
        # Check if this is a section header
        is_header = False
        new_section = None
        
        if re.match(r'prepared remarks?:?', part_lower):
            new_section = 'prepared_remarks'
            is_header = True
        elif re.match(r'(questions?\s*(?:and|&)\s*answers?|q\s*&\s*a):?', part_lower):
            new_section = 'qa'
            is_header = True
        elif re.match(r'(guidance|outlook):?', part_lower):
            new_section = 'forward_looking'
            is_header = True
        elif re.match(r'forward[- ]looking:?', part_lower):
            new_section = 'forward_looking'
            is_header = True
        elif 'results' in part_lower or 'highlights' in part_lower:
            new_section = 'factual'
            is_header = True
        
        if is_header and new_section:
            # Save current section
            if current_text:
                sections.append((current_section, '\n'.join(current_text)))
            current_section = new_section
            current_text = [part]
        else:
            current_text.append(part)
    
    # Save final section
    if current_text:
        sections.append((current_section, '\n'.join(current_text)))
    
    # If no sections found, classify the whole text
    if not sections:
        section_type = classify_section(text)
        sections = [(section_type, text)]
    
    return sections


def is_legal_hedging(sentence, section_type='general'):
    """
    Determine if hedging in this sentence is legally appropriate
    Returns (is_legal, reason)
    """
    if section_type == 'safe_harbor':
        return True, "Safe harbor disclaimer"
    
    if section_type == 'forward_looking':
        # Check if this is identifying a forward-looking statement
        text_lower = sentence.lower()
        has_fls_identifier = any(word in text_lower for word in ['expect', 'anticipate', 'believe', 'estimate', 'project', 'forecast', 'guidance', 'outlook'])
        has_future_ref = bool(re.search(r'\b(next|future|will|upcoming|fiscal\s*20\d{2})\b', text_lower))
        
        if has_fls_identifier and has_future_ref:
            return True, "Forward-looking statement identifier"
        elif has_fls_identifier:
            return True, "Guidance language"
    
    return False, None


def get_legal_safe_words():
    """Return set of words that are legally protected in FLS context"""
    return FLS_IDENTIFIER_WORDS


# ============================================================
# SECTION-AWARE ANALYSIS
# ============================================================

def analyze_with_legal_context(text, base_analysis_func, lm_dict):
    """
    Analyze transcript with legal context awareness
    Returns enhanced analysis with section breakdowns
    """
    sections = split_transcript_sections(text)
    
    section_analyses = []
    
    for section_type, section_text in sections:
        if len(section_text.strip()) < 100:
            continue
            
        # Run base analysis
        analysis = base_analysis_func(section_text, lm_dict)
        
        # Adjust scores based on section type
        if section_type == 'safe_harbor':
            # Ignore safe harbor sections entirely
            analysis['section_type'] = 'safe_harbor'
            analysis['legal_note'] = 'Safe harbor disclaimer - excluded from scoring'
            analysis['scores']['adjusted_confidence'] = None
            
        elif section_type == 'forward_looking':
            # Hedging is expected here - don't penalize
            analysis['section_type'] = 'forward_looking'
            analysis['legal_note'] = 'Forward-looking section - hedging is legally appropriate'
            # Boost confidence score for this section
            original_conf = analysis['scores']['confidence']
            analysis['scores']['adjusted_confidence'] = min(100, original_conf + 20)
            
        elif section_type == 'qa':
            # Hedging is concerning here - penalize more
            analysis['section_type'] = 'qa'
            analysis['legal_note'] = 'Q&A section - hedging may signal uncertainty'
            # Reduce confidence score for this section
            original_conf = analysis['scores']['confidence']
            analysis['scores']['adjusted_confidence'] = max(0, original_conf - 10)
            
        elif section_type == 'factual':
            # Hedging about past results is bad
            analysis['section_type'] = 'factual'
            analysis['legal_note'] = 'Results discussion - should be factual, not hedged'
            original_conf = analysis['scores']['confidence']
            analysis['scores']['adjusted_confidence'] = max(0, original_conf - 15)
            
        else:
            analysis['section_type'] = 'general'
            analysis['legal_note'] = None
            analysis['scores']['adjusted_confidence'] = analysis['scores']['confidence']
        
        section_analyses.append({
            'type': section_type,
            'text_preview': section_text[:200] + '...' if len(section_text) > 200 else section_text,
            'analysis': analysis,
        })
    
    # Compute overall adjusted score
    valid_sections = [s for s in section_analyses if s['type'] != 'safe_harbor']
    
    if valid_sections:
        # Weight Q&A and factual sections more heavily
        weights = {
            'qa': 1.5,
            'factual': 1.2,
            'forward_looking': 0.8,
            'general': 1.0,
            'prepared_remarks': 1.0,
        }
        
        weighted_scores = []
        total_weight = 0
        
        for section in valid_sections:
            weight = weights.get(section['type'], 1.0)
            adj_conf = section['analysis']['scores'].get('adjusted_confidence')
            if adj_conf is not None:
                weighted_scores.append(adj_conf * weight)
                total_weight += weight
        
        if total_weight > 0:
            overall_adjusted_confidence = sum(weighted_scores) / total_weight
        else:
            overall_adjusted_confidence = None
    else:
        overall_adjusted_confidence = None
    
    return {
        'sections': section_analyses,
        'overall_adjusted_confidence': overall_adjusted_confidence,
        'section_count': len(section_analyses),
    }


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":
    # Test with sample text
    test_text = """
    Safe Harbor Statement: This call contains forward-looking statements within the meaning 
    of the Private Securities Litigation Reform Act. These statements involve risks and 
    uncertainties that may cause actual results to differ materially.
    
    Q4 Results:
    We delivered strong results this quarter with revenue of $50 billion.
    
    Guidance:
    Looking ahead to Q1, we expect revenue to be in the range of $48 to $52 billion.
    We anticipate continued momentum in our services business.
    
    Q&A:
    Analyst: Can you talk about the competitive environment?
    CEO: You know, it's a challenging environment, and we're sort of cautiously optimistic
    about the trajectory going forward.
    """
    
    sections = split_transcript_sections(test_text)
    
    print("Section Analysis:")
    print("-" * 50)
    for section_type, section_text in sections:
        print(f"\nSection Type: {section_type.upper()}")
        print(f"Preview: {section_text[:100]}...")
        
        # Test individual sentences
        sentences = re.split(r'(?<=[.!?])\s+', section_text)
        for sentence in sentences[:3]:
            is_legal, reason = is_legal_hedging(sentence, section_type)
            if is_legal:
                print(f"  ✓ Legal hedging: {reason}")
