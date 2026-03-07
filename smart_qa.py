#!/usr/bin/env python3
"""
Smart Q&A Generator

Generates analyst questions based on:
1. Historical analyst questions from prior earnings calls
2. Topics detected in the current script

Generates answers based on:
- ONLY data from the current draft script
- Never uses stale data from prior filings
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PredictedQuestion:
    """A predicted analyst question with context."""
    question: str
    category: str
    confidence: float  # 0-1
    source: str  # 'historical', 'topic_match', 'metric_probe', 'omission'
    trigger_context: Optional[str]  # What in the script triggered this
    historical_context: Optional[str]  # If from prior calls


@dataclass 
class ProposedAnswer:
    """A proposed answer based on script data."""
    question: str
    answer: str
    supporting_data: List[str]  # Specific data points from script
    key_quotes: List[str]  # Relevant quotes from script
    answer_strategy: str
    confidence_notes: List[str]  # Tips for delivery


# ============================================================
# OPERATOR/MODERATOR FILTERING
# ============================================================

OPERATOR_PATTERNS = [
    r'^(?:operator|conference operator|moderator)\s*:',
    r'^(?:thank you|thanks)\.\s*(?:our next question|we\'ll take our next|the next question)',
    r'(?:please (?:hold|stand by)|one moment please)',
    r'(?:we\'ll now|we will now)\s+(?:open|begin|take)\s+(?:the|questions)',
    r'(?:this concludes|that concludes)\s+(?:our|the|today\'s)',
    r'^(?:ladies and gentlemen|good (?:morning|afternoon|evening))',
    r'(?:press \*1|press star one|enter the queue)',
    r'(?:your line is now open|please proceed|go ahead)',
    r'^(?:q\s*[-–—]|question\s*[-–—])\s*(?:and\s*)?(?:a|answer)',
]

SPEAKER_PATTERNS = [
    r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*[-–—:]\s*',  # "John Smith - "
    r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}),\s*(?:CEO|CFO|COO|President|Chairman|Analyst)',
]


def filter_operator_content(text: str) -> str:
    """Remove operator/moderator language from transcript."""
    lines = text.split('\n')
    filtered_lines = []
    skip_next = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Skip empty lines
        if not line_lower:
            filtered_lines.append(line)
            continue
        
        # Check operator patterns
        is_operator = False
        for pattern in OPERATOR_PATTERNS:
            if re.search(pattern, line_lower):
                is_operator = True
                break
        
        if not is_operator:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def identify_speakers(text: str) -> Dict[str, str]:
    """Identify speakers and their roles from the transcript."""
    speakers = {}
    
    # Common role patterns
    role_patterns = [
        (r'(?:CEO|Chief Executive)', 'executive'),
        (r'(?:CFO|Chief Financial)', 'executive'),
        (r'(?:COO|Chief Operating)', 'executive'),
        (r'(?:President)', 'executive'),
        (r'(?:Chairman|Chair)', 'executive'),
        (r'(?:Analyst|Research|Securities|Capital|Bank)', 'analyst'),
        (r'(?:Investor Relations|IR)', 'ir'),
        (r'(?:Operator|Moderator)', 'operator'),
    ]
    
    for pattern in SPEAKER_PATTERNS:
        matches = re.findall(pattern, text)
        for name in matches:
            if name not in speakers:
                # Try to identify role
                context = text[text.find(name):text.find(name)+200]
                role = 'unknown'
                for role_pattern, role_type in role_patterns:
                    if re.search(role_pattern, context, re.IGNORECASE):
                        role = role_type
                        break
                speakers[name] = role
    
    return speakers


# ============================================================
# SCRIPT DATA EXTRACTION
# ============================================================

def extract_metrics_from_script(text: str) -> List[Dict]:
    """Extract specific metrics and data points from the script."""
    metrics = []
    
    # Revenue patterns
    revenue_patterns = [
        r'revenue\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)',
        r'\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)\s+(?:in\s+)?revenue',
        r'revenue\s+(?:grew|increased|rose|declined|decreased)\s+(?:by\s+)?([\d,]+(?:\.\d+)?)\s*%',
    ]
    
    # EPS patterns
    eps_patterns = [
        r'(?:EPS|earnings per share)\s+(?:of\s+)?\$?([\d,]+(?:\.\d+)?)',
        r'\$?([\d,]+(?:\.\d+)?)\s+(?:in\s+)?(?:EPS|earnings per share)',
    ]
    
    # Margin patterns
    margin_patterns = [
        r'(?:gross|operating|net|EBITDA)\s+margin\s+(?:of\s+)?([\d,]+(?:\.\d+)?)\s*%',
        r'([\d,]+(?:\.\d+)?)\s*%\s+(?:gross|operating|net|EBITDA)\s+margin',
        r'margin\s+(?:expanded|improved|contracted|declined)\s+(?:by\s+)?([\d,]+)\s*(?:basis points|bps)',
    ]
    
    # Guidance patterns
    guidance_patterns = [
        r'(?:guidance|outlook|expect)\s+.*?\$?([\d,]+(?:\.\d+)?)\s*(?:to|-)\s*\$?([\d,]+(?:\.\d+)?)',
        r'(?:raise|raising|lower|lowering|maintain|maintaining)\s+.*?guidance',
    ]
    
    # Growth patterns
    growth_patterns = [
        r'(?:grew|growth|increased|up)\s+(?:by\s+)?([\d,]+(?:\.\d+)?)\s*%',
        r'([\d,]+(?:\.\d+)?)\s*%\s+(?:growth|increase|year-over-year|YoY)',
    ]
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    all_patterns = [
        ('revenue', revenue_patterns),
        ('eps', eps_patterns),
        ('margin', margin_patterns),
        ('guidance', guidance_patterns),
        ('growth', growth_patterns),
    ]
    
    for sentence in sentences:
        for metric_type, patterns in all_patterns:
            for pattern in patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    metrics.append({
                        'type': metric_type,
                        'value': match.group(0),
                        'sentence': sentence.strip(),
                        'groups': match.groups(),
                    })
                    break  # One match per type per sentence
    
    return metrics


def extract_key_statements(text: str) -> List[Dict]:
    """Extract key forward-looking and important statements."""
    statements = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Forward-looking indicators
    fls_patterns = [
        r'\b(expect|anticipate|believe|project|forecast|target|outlook|guidance)\b',
        r'\b(will|shall)\s+(achieve|deliver|reach|generate|grow)',
        r'\bgoing forward\b',
        r'\b(next|coming|future)\s+(quarter|year|fiscal)',
    ]
    
    # Confidence indicators
    confidence_patterns = [
        r'\b(confident|conviction|certain|committed|strong|robust)\b',
        r'\b(pleased|proud|excited|encouraged)\b',
    ]
    
    # Concern indicators
    concern_patterns = [
        r'\b(challenging|difficult|headwind|pressure|uncertain)\b',
        r'\b(decline|decrease|lower|weaker|soft)\b',
    ]
    
    for sentence in sentences:
        if len(sentence.strip()) < 30:
            continue
            
        sentence_lower = sentence.lower()
        
        # Check each type
        for pattern in fls_patterns:
            if re.search(pattern, sentence_lower):
                statements.append({
                    'type': 'forward_looking',
                    'sentence': sentence.strip(),
                })
                break
        
        for pattern in confidence_patterns:
            if re.search(pattern, sentence_lower):
                statements.append({
                    'type': 'confident',
                    'sentence': sentence.strip(),
                })
                break
                
        for pattern in concern_patterns:
            if re.search(pattern, sentence_lower):
                statements.append({
                    'type': 'concern',
                    'sentence': sentence.strip(),
                })
                break
    
    return statements


# ============================================================
# HISTORICAL Q&A PATTERNS
# ============================================================

# Common analyst question patterns by topic (learned from earnings calls)
HISTORICAL_QUESTION_PATTERNS = {
    'revenue_drivers': {
        'triggers': ['revenue', 'sales', 'top line', 'growth'],
        'questions': [
            "Can you break down the revenue growth by segment?",
            "What's driving the revenue performance this quarter?",
            "How sustainable is this revenue growth rate?",
            "Can you quantify the volume vs. price contribution?",
        ],
    },
    'margin_trajectory': {
        'triggers': ['margin', 'gross margin', 'operating margin', 'profitability'],
        'questions': [
            "Can you walk us through the margin bridge?",
            "What's the path to margin expansion from here?",
            "How much of the margin pressure is structural vs. temporary?",
            "Where do you see margins stabilizing?",
        ],
    },
    'guidance_assumptions': {
        'triggers': ['guidance', 'outlook', 'expect', 'full year', 'forecast'],
        'questions': [
            "What are the key assumptions in your guidance?",
            "What would cause you to revise guidance?",
            "How conservative is the guidance range?",
            "What's embedded in the high vs. low end of the range?",
        ],
    },
    'capital_allocation': {
        'triggers': ['buyback', 'dividend', 'M&A', 'acquisition', 'capital', 'cash'],
        'questions': [
            "How are you thinking about capital allocation priorities?",
            "What's your appetite for M&A at current valuations?",
            "Can you update us on the buyback program?",
            "What's the right leverage target for the business?",
        ],
    },
    'competitive_dynamics': {
        'triggers': ['competitive', 'market share', 'pricing', 'competitor'],
        'questions': [
            "Are you seeing any changes in the competitive landscape?",
            "How much pricing power do you have?",
            "Are competitors behaving rationally?",
            "Can you quantify market share trends?",
        ],
    },
    'macro_sensitivity': {
        'triggers': ['macro', 'economy', 'recession', 'inflation', 'consumer'],
        'questions': [
            "How exposed is the business to macro weakness?",
            "What are you seeing from a consumer behavior standpoint?",
            "How are you preparing for a potential downturn?",
            "What's the demand elasticity in your business?",
        ],
    },
    'cost_management': {
        'triggers': ['cost', 'expense', 'restructuring', 'efficiency', 'headcount'],
        'questions': [
            "Where are you seeing the most cost pressure?",
            "Are there additional cost actions you're considering?",
            "When do you expect to see the savings flow through?",
            "What's the right cost structure for this revenue level?",
        ],
    },
    'new_products': {
        'triggers': ['new product', 'launch', 'innovation', 'pipeline', 'R&D'],
        'questions': [
            "Can you update us on the product pipeline?",
            "What's the early customer reception?",
            "How should we think about the ramp trajectory?",
            "What's the margin profile of new products vs. existing?",
        ],
    },
}


# ============================================================
# QUESTION GENERATION
# ============================================================

def generate_smart_questions(text: str, historical_data: Optional[Dict] = None) -> List[PredictedQuestion]:
    """
    Generate predicted analyst questions based on script content and historical patterns.
    """
    questions = []
    text_lower = text.lower()
    seen_questions = set()
    
    # Extract metrics and statements for context
    metrics = extract_metrics_from_script(text)
    statements = extract_key_statements(text)
    
    # 1. Match historical patterns to script content
    for topic, pattern_data in HISTORICAL_QUESTION_PATTERNS.items():
        trigger_count = sum(1 for t in pattern_data['triggers'] if t in text_lower)
        
        if trigger_count > 0:
            confidence = min(0.95, 0.5 + (trigger_count * 0.1))
            
            # Find trigger context
            trigger_context = None
            for trigger in pattern_data['triggers']:
                if trigger in text_lower:
                    # Find sentence containing trigger
                    sentences = re.split(r'(?<=[.!?])\s+', text)
                    for s in sentences:
                        if trigger in s.lower():
                            trigger_context = s[:200]
                            break
                    break
            
            for q in pattern_data['questions'][:2]:  # Top 2 per topic
                if q not in seen_questions:
                    seen_questions.add(q)
                    questions.append(PredictedQuestion(
                        question=q,
                        category=topic,
                        confidence=confidence,
                        source='topic_match',
                        trigger_context=trigger_context,
                        historical_context=f"Common question when discussing {topic.replace('_', ' ')}"
                    ))
    
    # 2. Generate metric-specific probing questions
    for metric in metrics[:5]:  # Top 5 metrics
        if metric['type'] == 'revenue':
            q = f"Can you provide more detail on the {metric['value']}?"
            if q not in seen_questions:
                seen_questions.add(q)
                questions.append(PredictedQuestion(
                    question=q,
                    category='metric_probe',
                    confidence=0.8,
                    source='metric_probe',
                    trigger_context=metric['sentence'][:200],
                    historical_context=None
                ))
        elif metric['type'] == 'guidance':
            q = "What gives you confidence in achieving the guidance?"
            if q not in seen_questions:
                seen_questions.add(q)
                questions.append(PredictedQuestion(
                    question=q,
                    category='guidance_probe',
                    confidence=0.85,
                    source='metric_probe',
                    trigger_context=metric['sentence'][:200],
                    historical_context=None
                ))
    
    # 3. Check for omissions (topics not discussed that usually are)
    standard_topics = ['guidance', 'capital allocation', 'margin', 'competitive']
    for topic in standard_topics:
        if topic not in text_lower:
            q = f"Can you discuss your thoughts on {topic}?"
            if q not in seen_questions:
                seen_questions.add(q)
                questions.append(PredictedQuestion(
                    question=q,
                    category='omission',
                    confidence=0.6,
                    source='omission',
                    trigger_context='Topic not addressed in script',
                    historical_context=f"Analysts typically ask about {topic} if not covered"
                ))
    
    # 4. Questions about concerning statements
    concern_statements = [s for s in statements if s['type'] == 'concern']
    for stmt in concern_statements[:2]:
        q = f"Can you elaborate on the challenges you mentioned?"
        if q not in seen_questions:
            seen_questions.add(q)
            questions.append(PredictedQuestion(
                question=q,
                category='concern_followup',
                confidence=0.75,
                source='concern_probe',
                trigger_context=stmt['sentence'][:200],
                historical_context="Analysts probe concerning language"
            ))
    
    # Sort by confidence
    questions.sort(key=lambda x: x.confidence, reverse=True)
    
    return questions[:15]  # Return top 15


# ============================================================
# ANSWER GENERATION
# ============================================================

ANSWER_STRATEGIES = {
    'revenue_drivers': {
        'name': 'Decompose & Quantify',
        'opening': "Let me break that down for you.",
        'structure': "We saw [metric] driven by [drivers]. Specifically, [data point].",
        'closing': "We feel good about the trajectory.",
    },
    'margin_trajectory': {
        'name': 'Bridge & Outlook',
        'opening': "Great question on margins.",
        'structure': "Our margin of [metric] reflects [factors]. Looking ahead, [outlook].",
        'closing': "We expect continued improvement as [reason].",
    },
    'guidance_assumptions': {
        'name': 'Framework & Range',
        'opening': "Let me walk you through our thinking.",
        'structure': "Our guidance of [range] assumes [assumptions]. The key variables are [variables].",
        'closing': "We've tried to balance ambition with prudence.",
    },
    'capital_allocation': {
        'name': 'Priorities & Discipline',
        'opening': "Our capital allocation priorities remain clear.",
        'structure': "We're focused on [priorities]. This quarter, [actions].",
        'closing': "We'll continue to be disciplined and shareholder-focused.",
    },
    'competitive_dynamics': {
        'name': 'Position & Differentiation',
        'opening': "Our competitive position remains strong.",
        'structure': "We're seeing [dynamics]. Our differentiation through [factors] continues to resonate.",
        'closing': "We're confident in our ability to compete and win.",
    },
    'default': {
        'name': 'Direct & Substantive',
        'opening': "Let me address that directly.",
        'structure': "[Key point supported by data from the script].",
        'closing': "Happy to provide more detail if helpful.",
    },
}


def generate_smart_answers(
    questions: List[PredictedQuestion], 
    text: str
) -> List[ProposedAnswer]:
    """
    Generate proposed answers based ONLY on data from the current script.
    Never uses external/historical data for answer content.
    """
    answers = []
    
    # Extract all available data from script
    metrics = extract_metrics_from_script(text)
    statements = extract_key_statements(text)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for q in questions:
        # Get answer strategy
        strategy = ANSWER_STRATEGIES.get(q.category, ANSWER_STRATEGIES['default'])
        
        # Find relevant data from script
        relevant_metrics = []
        relevant_quotes = []
        
        # Search for relevant sentences
        question_keywords = set(re.findall(r'\b\w{4,}\b', q.question.lower()))
        question_keywords -= {'what', 'when', 'where', 'which', 'that', 'this', 
                              'have', 'been', 'with', 'from', 'your', 'about',
                              'think', 'should', 'could', 'would', 'more', 'give',
                              'help', 'walk', 'through', 'does', 'expect', 'talk',
                              'some', 'provide', 'detail', 'color'}
        
        for sentence in sentences:
            if len(sentence.strip()) < 30:
                continue
            sentence_words = set(re.findall(r'\b\w{4,}\b', sentence.lower()))
            overlap = len(question_keywords & sentence_words)
            
            if overlap >= 2:
                relevant_quotes.append(sentence.strip()[:200])
                
                # Check for metrics in this sentence
                for metric in metrics:
                    if metric['sentence'] == sentence.strip():
                        relevant_metrics.append(metric['value'])
        
        # Build the answer
        answer_parts = [strategy['opening']]
        
        if relevant_metrics:
            answer_parts.append(f"Based on our results, {', '.join(relevant_metrics[:3])}.")
        
        if relevant_quotes:
            answer_parts.append(f"As we noted, {relevant_quotes[0][:150]}")
        elif q.trigger_context:
            answer_parts.append(f"Regarding {q.trigger_context[:100]}...")
        
        answer_parts.append(strategy['closing'])
        
        # Confidence notes
        notes = []
        if not relevant_metrics:
            notes.append("Consider adding specific data points from your materials")
        if not relevant_quotes:
            notes.append("Prepare supporting quotes from the script")
        if q.category == 'omission':
            notes.append("This topic wasn't in the script - prepare talking points")
        
        answers.append(ProposedAnswer(
            question=q.question,
            answer=' '.join(answer_parts),
            supporting_data=relevant_metrics[:5],
            key_quotes=relevant_quotes[:3],
            answer_strategy=strategy['name'],
            confidence_notes=notes if notes else ["Strong data support from script"]
        ))
    
    return answers


# ============================================================
# MAIN INTERFACE
# ============================================================

def analyze_script_for_qa(text: str, historical_data: Optional[Dict] = None) -> Dict:
    """
    Main function to analyze a script and generate Q&A prep.
    
    Args:
        text: The draft earnings script
        historical_data: Optional dict with prior call Q&A data
    
    Returns:
        Dict with questions, answers, and supporting analysis
    """
    # Filter operator content first
    filtered_text = filter_operator_content(text)
    
    # Identify speakers
    speakers = identify_speakers(filtered_text)
    
    # Extract metrics and statements
    metrics = extract_metrics_from_script(filtered_text)
    statements = extract_key_statements(filtered_text)
    
    # Generate questions
    questions = generate_smart_questions(filtered_text, historical_data)
    
    # Generate answers
    answers = generate_smart_answers(questions, filtered_text)
    
    # Build response
    return {
        'questions': questions,
        'answers': answers,
        'metrics_extracted': metrics,
        'key_statements': statements,
        'speakers_identified': speakers,
        'filtered_text_length': len(filtered_text),
        'original_text_length': len(text),
        'total_questions': len(questions),
        'high_confidence_count': len([q for q in questions if q.confidence >= 0.8]),
    }


# Test
if __name__ == "__main__":
    sample = """
    Operator: Good afternoon. Welcome to ACME Corp's Q4 2025 earnings call.
    
    John Smith, CEO: Thank you, operator. Good afternoon everyone.
    
    We delivered strong results this quarter with revenue of $2.3 billion, up 15% 
    year-over-year. Gross margin expanded 150 basis points to 42%, reflecting our 
    cost optimization initiatives.
    
    Looking ahead, we're maintaining our full-year guidance of $9.0 to $9.5 billion
    in revenue. We expect continued margin expansion driven by operating leverage.
    
    We're facing some headwinds in our European segment due to challenging macro
    conditions, but we're confident in our overall trajectory.
    
    Jane Doe, CFO: Thanks, John. Let me provide some additional color on the financials.
    
    Operating cash flow was $450 million, and we returned $200 million to shareholders
    through buybacks. Our balance sheet remains strong with $1.2 billion in cash.
    
    Operator: Thank you. We'll now open for questions.
    """
    
    result = analyze_script_for_qa(sample)
    
    print("=" * 60)
    print(f"EXTRACTED {len(result['metrics_extracted'])} METRICS")
    print("=" * 60)
    for m in result['metrics_extracted'][:5]:
        print(f"  [{m['type']}] {m['value']}")
    
    print("\n" + "=" * 60)
    print(f"PREDICTED {result['total_questions']} QUESTIONS ({result['high_confidence_count']} high confidence)")
    print("=" * 60)
    
    for i, (q, a) in enumerate(zip(result['questions'][:5], result['answers'][:5]), 1):
        print(f"\nQ{i} [{q.category}] ({int(q.confidence*100)}%)")
        print(f"   {q.question}")
        print(f"\n   PROPOSED ANSWER:")
        print(f"   {a.answer[:200]}...")
        print(f"\n   Strategy: {a.answer_strategy}")
        print(f"   Data points: {len(a.supporting_data)}")
