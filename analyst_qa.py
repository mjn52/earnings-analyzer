#!/usr/bin/env python3
"""
Analyst Q&A Generator

Analyzes earnings scripts to:
1. Identify key themes and potential concern areas
2. Generate likely analyst questions
3. Propose management responses

Based on patterns from real earnings call Q&A sessions.
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class AnalystQuestion:
    """Represents a predicted analyst question with context."""
    question: str
    category: str  # revenue, margins, guidance, capital_allocation, etc.
    trigger_text: str  # The text that triggered this question
    severity: str  # high, medium, low - likelihood of being asked
    suggested_response: str
    response_notes: str  # Tips for delivering the response


# Common analyst question patterns by category
QUESTION_PATTERNS = {
    'revenue': [
        {
            'triggers': [r'revenue (growth|decline|flat)', r'top.?line', r'sales (increased|decreased|grew)'],
            'questions': [
                "Can you break down the revenue growth between volume and price?",
                "What's driving the change in revenue mix this quarter?",
                "How sustainable is this revenue trajectory going forward?",
            ],
            'severity': 'high'
        },
        {
            'triggers': [r'new (customer|client|contract)', r'customer (acquisition|wins)', r'pipeline'],
            'questions': [
                "Can you quantify the contribution from new customer wins?",
                "What does the pipeline look like for the next few quarters?",
                "Are you seeing any changes in customer acquisition costs?",
            ],
            'severity': 'medium'
        },
    ],
    'margins': [
        {
            'triggers': [r'margin (expansion|compression|pressure)', r'gross margin', r'operating margin'],
            'questions': [
                "What's the path to margin recovery?",
                "Can you walk us through the puts and takes on margins?",
                "How much of the margin change is structural vs. temporary?",
            ],
            'severity': 'high'
        },
        {
            'triggers': [r'cost (savings|reduction|efficiency)', r'operating leverage', r'restructuring'],
            'questions': [
                "What inning are we in on the cost reduction program?",
                "When do you expect to see the full benefit of these initiatives?",
                "Are there additional cost actions you're considering?",
            ],
            'severity': 'medium'
        },
    ],
    'guidance': [
        {
            'triggers': [r'(raise|lower|maintain|reiterate).*guidance', r'outlook', r'expect.*(full year|quarter)'],
            'questions': [
                "What are the key assumptions embedded in your guidance?",
                "What would cause you to revisit guidance?",
                "How conservative is this guidance range?",
            ],
            'severity': 'high'
        },
        {
            'triggers': [r'uncertainty', r'visibility', r'volatile', r'challenging environment'],
            'questions': [
                "Given the uncertainty you mentioned, why maintain guidance?",
                "How has your visibility changed since last quarter?",
                "What gives you confidence in the outlook despite the headwinds?",
            ],
            'severity': 'high'
        },
    ],
    'capital_allocation': [
        {
            'triggers': [r'buyback|repurchase', r'dividend', r'return.*capital', r'shareholder return'],
            'questions': [
                "How should we think about capital returns going forward?",
                "What's the priority between buybacks and dividends?",
                "At what point would you consider increasing the dividend?",
            ],
            'severity': 'medium'
        },
        {
            'triggers': [r'M&A|acquisition|deal', r'inorganic', r'strategic.*transaction'],
            'questions': [
                "What's your appetite for M&A at current valuations?",
                "Are you seeing more actionable opportunities in the market?",
                "How are you thinking about the integration timeline?",
            ],
            'severity': 'medium'
        },
    ],
    'competition': [
        {
            'triggers': [r'market share', r'competitive', r'pricing (pressure|environment)', r'competitor'],
            'questions': [
                "Are you seeing any changes in the competitive landscape?",
                "How are you thinking about pricing power in this environment?",
                "What's your market share trajectory?",
            ],
            'severity': 'medium'
        },
    ],
    'segment_performance': [
        {
            'triggers': [r'segment|division|business unit', r'geographic.*mix', r'international|domestic'],
            'questions': [
                "Can you provide more color on segment performance?",
                "What's driving the divergence between segments?",
                "How should we think about segment margins going forward?",
            ],
            'severity': 'medium'
        },
    ],
    'working_capital': [
        {
            'triggers': [r'inventory', r'receivable', r'working capital', r'cash (flow|conversion)'],
            'questions': [
                "What's driving the change in working capital?",
                "How should we think about inventory levels going forward?",
                "When do you expect cash conversion to normalize?",
            ],
            'severity': 'low'
        },
    ],
    'macro': [
        {
            'triggers': [r'macro', r'recession', r'inflation', r'interest rate', r'consumer (spending|sentiment)'],
            'questions': [
                "What are you seeing from a macro perspective?",
                "How exposed is the business to a potential recession?",
                "Are you seeing any changes in customer behavior?",
            ],
            'severity': 'medium'
        },
    ],
}

# Response templates by category
RESPONSE_TEMPLATES = {
    'revenue': {
        'template': """Thank you for the question. {acknowledgment}

On the revenue front, {key_point}. 

Looking ahead, {forward_looking}. As always, {qualifier}.""",
        'notes': "Be specific with numbers where possible. Avoid vague qualifiers."
    },
    'margins': {
        'template': """Great question. {acknowledgment}

Regarding margins, {key_point}.

We expect {forward_looking}. {qualifier}.""",
        'notes': "Quantify margin drivers. Be clear about temporary vs structural factors."
    },
    'guidance': {
        'template': """I appreciate the question. {acknowledgment}

Our guidance reflects {key_point}.

We've built in {assumptions}. {qualifier}.""",
        'notes': "Be transparent about assumptions. Don't overpromise."
    },
    'capital_allocation': {
        'template': """Thanks for asking. {acknowledgment}

Our capital allocation priorities remain {key_point}.

Going forward, {forward_looking}. {qualifier}.""",
        'notes': "Be consistent with prior messaging. Emphasize discipline."
    },
    'default': {
        'template': """Thank you for that question. {acknowledgment}

{key_point}

{forward_looking}. {qualifier}.""",
        'notes': "Stay on message. Bridge back to key themes."
    },
}


def extract_key_themes(text: str) -> Dict[str, List[str]]:
    """Extract key themes and their supporting text from the script."""
    themes = {}
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for category, patterns in QUESTION_PATTERNS.items():
        matches = []
        for pattern_group in patterns:
            for trigger in pattern_group['triggers']:
                for sentence in sentences:
                    if re.search(trigger, sentence, re.IGNORECASE):
                        if sentence not in matches:
                            matches.append(sentence)
        if matches:
            themes[category] = matches
    
    return themes


def extract_numbers_and_metrics(text: str) -> List[Dict]:
    """Extract specific numbers and metrics that analysts will probe."""
    metrics = []
    
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*%', 'percentage'),
        (r'\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)', 'dollar_amount'),
        (r'(\d+(?:\.\d+)?)\s*(basis points|bps)', 'basis_points'),
        (r'(\d+(?:\.\d+)?)[xX]\s*(leverage|multiple|times)', 'multiple'),
    ]
    
    for pattern, metric_type in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            metrics.append({
                'value': match.group(0),
                'type': metric_type,
                'context': context.strip()
            })
    
    return metrics


def identify_hedging_language(text: str) -> List[str]:
    """Find hedging language that analysts will probe."""
    hedge_patterns = [
        r'we (believe|think|expect|anticipate|hope)',
        r'(approximately|roughly|about|around)\s+\d',
        r'(may|might|could|should)\s+(see|experience|achieve)',
        r'(challenging|difficult|uncertain)\s+(environment|conditions|market)',
        r'(modest|moderate|slight)\s+(growth|improvement|decline)',
    ]
    
    hedges = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        for pattern in hedge_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                if sentence not in hedges:
                    hedges.append(sentence)
    
    return hedges


def generate_questions(text: str) -> List[AnalystQuestion]:
    """Generate likely analyst questions based on the script content."""
    questions = []
    themes = extract_key_themes(text)
    hedges = identify_hedging_language(text)
    metrics = extract_numbers_and_metrics(text)
    
    # Generate questions for each theme found
    for category, trigger_texts in themes.items():
        for pattern_group in QUESTION_PATTERNS.get(category, []):
            # Check if any triggers match
            for trigger in pattern_group['triggers']:
                for trigger_text in trigger_texts:
                    if re.search(trigger, trigger_text, re.IGNORECASE):
                        # Add questions from this pattern group
                        for q in pattern_group['questions']:
                            # Avoid duplicates
                            if not any(existing.question == q for existing in questions):
                                response_template = RESPONSE_TEMPLATES.get(
                                    category, 
                                    RESPONSE_TEMPLATES['default']
                                )
                                
                                questions.append(AnalystQuestion(
                                    question=q,
                                    category=category,
                                    trigger_text=trigger_text[:200],
                                    severity=pattern_group['severity'],
                                    suggested_response=generate_response_draft(
                                        q, category, trigger_text
                                    ),
                                    response_notes=response_template['notes']
                                ))
                        break
    
    # Add questions for hedging language
    if hedges:
        questions.append(AnalystQuestion(
            question="You used several qualifiers in your prepared remarks. Can you help us understand what's driving the uncertainty?",
            category="hedging",
            trigger_text=hedges[0][:200] if hedges else "",
            severity="high",
            suggested_response=generate_response_draft(
                "uncertainty question", "hedging", hedges[0] if hedges else ""
            ),
            response_notes="Be direct. Acknowledge uncertainty but provide concrete guardrails."
        ))
    
    # Add questions for specific metrics
    for metric in metrics[:3]:  # Top 3 metrics
        questions.append(AnalystQuestion(
            question=f"Can you provide more detail on the {metric['value']} you mentioned?",
            category="metrics",
            trigger_text=metric['context'],
            severity="medium",
            suggested_response=f"Certainly. The {metric['value']} reflects [specific driver]. Breaking this down further, [component analysis]. Going forward, [outlook with appropriate caveats].",
            response_notes="Have the backup detail ready. Analysts will dig into specific numbers."
        ))
    
    # Sort by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    questions.sort(key=lambda x: severity_order.get(x.severity, 3))
    
    return questions


def generate_response_draft(question: str, category: str, context: str) -> str:
    """Generate a draft response for a predicted question."""
    
    # Get template for category
    template_data = RESPONSE_TEMPLATES.get(category, RESPONSE_TEMPLATES['default'])
    
    # Create a basic response structure
    # In production, this would call Claude API for better responses
    
    base_response = f"""Thank you for the question. 

Regarding {category.replace('_', ' ')}, let me provide some additional color. [Insert specific detail from prepared materials]

Looking ahead, [forward-looking statement with appropriate safe harbor language]. 

I'd also note that [supporting context or qualifier]."""
    
    return base_response


def generate_qa_section(text: str) -> Dict:
    """Generate complete Q&A prep section for the earnings call."""
    
    questions = generate_questions(text)
    themes = extract_key_themes(text)
    metrics = extract_numbers_and_metrics(text)
    hedges = identify_hedging_language(text)
    
    # Group questions by category
    questions_by_category = {}
    for q in questions:
        if q.category not in questions_by_category:
            questions_by_category[q.category] = []
        questions_by_category[q.category].append(q)
    
    return {
        'questions': questions,
        'questions_by_category': questions_by_category,
        'themes_detected': list(themes.keys()),
        'key_metrics': metrics[:10],  # Top 10 metrics
        'hedging_statements': hedges[:5],  # Top 5 hedges to be aware of
        'high_priority_count': len([q for q in questions if q.severity == 'high']),
        'total_questions': len(questions)
    }


def format_qa_for_document(qa_data: Dict) -> str:
    """Format Q&A data for inclusion in Word document."""
    
    lines = []
    lines.append("=" * 60)
    lines.append("LIKELY ANALYST QUESTIONS & SUGGESTED RESPONSES")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Total Questions Predicted: {qa_data['total_questions']}")
    lines.append(f"High Priority: {qa_data['high_priority_count']}")
    lines.append(f"Themes Detected: {', '.join(qa_data['themes_detected'])}")
    lines.append("")
    
    for i, q in enumerate(qa_data['questions'], 1):
        severity_indicator = "🔴" if q.severity == 'high' else "🟡" if q.severity == 'medium' else "🟢"
        
        lines.append(f"Q{i}. [{q.category.upper()}] {severity_indicator}")
        lines.append(f"    {q.question}")
        lines.append("")
        lines.append(f"    TRIGGER: \"{q.trigger_text[:100]}...\"")
        lines.append("")
        lines.append(f"    SUGGESTED RESPONSE:")
        for resp_line in q.suggested_response.split('\n'):
            lines.append(f"    {resp_line}")
        lines.append("")
        lines.append(f"    💡 TIP: {q.response_notes}")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
    
    return '\n'.join(lines)


# Test
if __name__ == "__main__":
    sample = """
    We delivered revenue growth of 12% this quarter, driven by strong performance 
    in our enterprise segment. Gross margins expanded by 150 basis points to 42%, 
    reflecting our cost optimization initiatives. 
    
    Looking ahead, we expect modest growth in Q4 given the challenging macro environment.
    We're maintaining our full-year guidance of $2.1 to $2.3 billion in revenue.
    
    On capital allocation, we repurchased $50 million of shares during the quarter
    and increased our dividend by 5%.
    
    We believe our market position remains strong despite increased competition.
    """
    
    qa_data = generate_qa_section(sample)
    print(format_qa_for_document(qa_data))
