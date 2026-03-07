#!/usr/bin/env python3
"""
Advanced Analysis Module for Earnings Script Analyzer

Features:
1. Likely Analyst Questions - pattern-based question generation from script topics
2. Proposed Answers - extract relevant data/quotes from script for answer frameworks
3. Negative Interpretations - detect phrases that could be spun negatively
4. Litigation Risk - detect FLS missing safe harbor / cautionary language
5. Activist Triggers - detect language that could attract activist investors
6. Guidance Clarity Score - score specificity of guidance language
"""

import re
from collections import Counter

# ============================================================
# 1. LIKELY ANALYST QUESTIONS
# ============================================================

# Topic triggers: when these appear in the script, generate related questions
TOPIC_QUESTION_MAP = {
    # Revenue / Growth
    'revenue': [
        "Can you break down the revenue drivers by segment and geography?",
        "What's your visibility into revenue sustainability in the coming quarters?",
        "How much of the revenue growth is organic vs. acquisition-driven?",
    ],
    'growth': [
        "Is this growth rate sustainable, and what could cause deceleration?",
        "What are the biggest risks to your growth trajectory?",
    ],
    'decelerat': [
        "Can you quantify the factors behind the deceleration and when you expect to reaccelerate?",
        "Is the deceleration structural or cyclical?",
    ],
    'accelerat': [
        "What's driving the acceleration, and how durable is it?",
    ],

    # Margins
    'margin': [
        "Can you walk us through the margin trajectory and what's driving the change?",
        "Where do you see margins stabilizing over the medium term?",
        "What are the puts and takes on margins going forward?",
    ],
    'gross margin': [
        "What's the mix impact on gross margins, and how should we think about it going forward?",
    ],
    'operating margin': [
        "How should we think about the operating leverage in the model?",
    ],
    'profitab': [
        "When do you expect to reach sustained profitability?",
        "What's the path to profitability improvement from here?",
    ],

    # Costs / Expenses
    'cost': [
        "Can you quantify the cost headwinds and how much is transitory vs. structural?",
        "Where are you seeing the most cost pressure?",
    ],
    'restructur': [
        "What's the expected timeline and savings from the restructuring?",
        "Are there additional restructuring actions being considered?",
    ],
    'headcount': [
        "How should we think about headcount trajectory from here?",
        "Are the reductions complete, or should we expect further cuts?",
    ],
    'expense': [
        "How should we think about the expense growth rate relative to revenue growth?",
    ],

    # Guidance
    'guidance': [
        "Can you provide more color on the assumptions underlying your guidance?",
        "What macro assumptions are embedded in the guidance range?",
        "What would need to happen to come in at the high vs. low end of guidance?",
    ],
    'outlook': [
        "Has anything changed in your outlook since last quarter?",
        "What gives you confidence in the outlook given the current environment?",
    ],
    'expect': [
        "What level of conservatism is built into your expectations?",
    ],

    # Capital Allocation
    'buyback': [
        "How are you thinking about the pace of buybacks going forward?",
        "What's the remaining authorization, and how should we think about timing?",
    ],
    'dividend': [
        "Is there room for dividend increases given the payout ratio?",
        "How do you prioritize dividends vs. buybacks vs. debt reduction?",
    ],
    'capital allocation': [
        "Can you walk us through how you're prioritizing capital allocation?",
        "Has the capital allocation framework changed at all?",
    ],
    'acquisition': [
        "What's your M&A pipeline looking like?",
        "How are you thinking about valuations in the current environment for M&A?",
    ],
    'capex': [
        "How should we think about the CapEx trajectory, and when do you expect to see returns?",
        "Is the elevated CapEx a new baseline, or will it normalize?",
    ],

    # Competition / Market
    'competi': [
        "Are you seeing any changes in the competitive landscape?",
        "How are you differentiating against competitors in this environment?",
    ],
    'market share': [
        "Can you quantify the market share gains and what's driving them?",
        "Are the share gains coming at the expense of margins?",
    ],
    'pricing': [
        "How much pricing power do you have in the current environment?",
        "Are you seeing any pushback from customers on pricing?",
    ],

    # Macro
    'macro': [
        "What are you seeing from a macro perspective across your end markets?",
        "How exposed is the business to a potential macro downturn?",
    ],
    'tariff': [
        "Can you quantify the tariff impact and your mitigation strategies?",
        "How are tariffs affecting your supply chain decisions?",
    ],
    'inflation': [
        "How are you managing inflationary pressures across the business?",
        "Are you able to pass through cost inflation to customers?",
    ],
    'recession': [
        "How resilient is the business model in a recessionary scenario?",
    ],
    'interest rate': [
        "How sensitive is the business to interest rate movements?",
    ],

    # Product / Innovation
    'new product': [
        "Can you give us more detail on the ramp timeline for the new product?",
        "What's the customer reception been like so far?",
    ],
    'pipeline': [
        "Can you update us on the pipeline and expected timing of key milestones?",
    ],
    'innovation': [
        "How are you prioritizing R&D investment across the portfolio?",
    ],
    'ai': [
        "How is AI contributing to revenue today, and how should we think about the trajectory?",
        "What's your AI strategy, and how does it differentiate you?",
    ],
    'artificial intelligence': [
        "Can you size the AI opportunity for us?",
    ],
    'cloud': [
        "What's driving the cloud growth, and how sustainable is it?",
    ],

    # Customers
    'churn': [
        "What's driving the churn, and what actions are you taking to address it?",
        "How does current churn compare to historical levels?",
    ],
    'customer': [
        "Are you seeing any changes in customer behavior or spending patterns?",
        "What does the customer pipeline look like?",
    ],
    'retention': [
        "Can you talk about retention trends and what's driving them?",
    ],
    'backlog': [
        "Can you give us more color on the backlog composition and conversion timeline?",
    ],

    # Supply Chain
    'supply chain': [
        "Are there any remaining supply chain constraints affecting the business?",
        "How are you managing supply chain diversification?",
    ],
    'inventor': [
        "How should we think about inventory levels and any risk of writedowns?",
        "Is the inventory build intentional, or are you seeing demand softness?",
    ],

    # International
    'international': [
        "What's driving the international performance, and where do you see the most opportunity?",
    ],
    'china': [
        "Can you update us on the China outlook given the current geopolitical environment?",
    ],
    'currency': [
        "What's the FX impact you're embedding in guidance?",
    ],
    'foreign exchange': [
        "How are you managing currency risk?",
    ],

    # Regulatory
    'regulat': [
        "How are you preparing for potential regulatory changes?",
        "What's the expected financial impact of the new regulations?",
    ],
    'litigation': [
        "Can you update us on the status of pending litigation?",
    ],
    'antitrust': [
        "How are you thinking about the antitrust risk?",
    ],

    # Cash / Balance Sheet
    'cash flow': [
        "Can you walk us through the free cash flow bridge?",
        "How should we think about cash conversion going forward?",
    ],
    'debt': [
        "What's your target leverage ratio, and how are you thinking about the maturity profile?",
    ],
    'balance sheet': [
        "How do you feel about the current balance sheet positioning?",
    ],
}

# Common analyst follow-up question patterns
FOLLOW_UP_PATTERNS = [
    "Can you quantify that for us?",
    "How does that compare to your internal expectations?",
    "Is there any way to disaggregate that further?",
    "What's the timeline for that?",
    "How does that compare to what you were seeing last quarter?",
]

# Patterns from Q&A sections of earnings calls
QA_TOPIC_PATTERNS = {
    'margin_change': {
        'triggers': [r'margin\w*\s+(?:expand|contract|improv|declin|compress)', r'basis\s+points?'],
        'questions': [
            "Can you quantify the margin impact by category?",
            "What's the right way to think about the margin trajectory from here?",
        ],
    },
    'one_time_items': {
        'triggers': [r'one[- ]time', r'non[- ]recurring', r'unusual', r'extraordinary'],
        'questions': [
            "Can you help us think about the normalized run rate excluding these items?",
            "Should we expect any similar items in future quarters?",
        ],
    },
    'segment_divergence': {
        'triggers': [r'segment\w*', r'division\w*', r'business\s+unit'],
        'questions': [
            "Can you break down the performance by segment and discuss the divergence?",
            "Which segments do you expect to be the biggest contributors going forward?",
        ],
    },
    'guidance_gap': {
        'triggers': [r'miss\w*\s+(?:guidance|expectat)', r'(?:above|below|outside)\s+(?:the\s+)?(?:guidance|range)'],
        'questions': [
            "What specifically drove the variance from guidance?",
            "Have you adjusted your process for setting guidance ranges?",
        ],
    },
}


def generate_analyst_questions(text, analysis=None):
    """
    Generate likely analyst questions based on script content.
    Returns list of dicts with question, topic, confidence, and context.
    """
    text_lower = text.lower()
    questions = []
    seen_questions = set()

    # 1. Topic-based questions from content
    for topic, topic_questions in TOPIC_QUESTION_MAP.items():
        count = text_lower.count(topic)
        if count >= 1:
            # Weight by frequency — more mentions = higher confidence
            confidence = min(0.95, 0.5 + (count * 0.05))
            for q in topic_questions:
                if q not in seen_questions:
                    seen_questions.add(q)
                    # Find the sentence that triggered this
                    context = _find_context_sentence(text, topic)
                    questions.append({
                        'question': q,
                        'topic': topic,
                        'confidence': round(confidence, 2),
                        'trigger_context': context,
                        'source': 'topic_match',
                    })

    # 2. Pattern-based questions from Q&A templates
    for pattern_name, pattern_data in QA_TOPIC_PATTERNS.items():
        for regex in pattern_data['triggers']:
            if re.search(regex, text_lower):
                for q in pattern_data['questions']:
                    if q not in seen_questions:
                        seen_questions.add(q)
                        context = _find_regex_context(text, regex)
                        questions.append({
                            'question': q,
                            'topic': pattern_name,
                            'confidence': 0.75,
                            'trigger_context': context,
                            'source': 'pattern_match',
                        })
                break  # Only need one trigger per pattern

    # 3. Detect notable omissions that analysts would ask about
    omission_questions = _detect_omissions(text_lower)
    for q in omission_questions:
        if q['question'] not in seen_questions:
            seen_questions.add(q['question'])
            questions.append(q)

    # 4. Questions about flagged issues from the main analysis
    if analysis and analysis.get('flagged_passages'):
        for fp in analysis['flagged_passages'][:3]:
            for issue in fp['issues']:
                if 'hedge' in issue.lower():
                    q = f"You mentioned \"{fp['sentence'][:80]}...\" — can you be more specific about what you mean?"
                    if q not in seen_questions:
                        seen_questions.add(q)
                        questions.append({
                            'question': q,
                            'topic': 'hedging_followup',
                            'confidence': 0.85,
                            'trigger_context': fp['sentence'][:150],
                            'source': 'hedging_flag',
                        })

    # Sort by confidence, take top 15
    questions.sort(key=lambda x: x['confidence'], reverse=True)
    return questions[:15]


def _find_context_sentence(text, keyword):
    """Find the first sentence containing the keyword"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for s in sentences:
        if keyword.lower() in s.lower() and len(s.strip()) > 20:
            return s.strip()[:200]
    return None


def _find_regex_context(text, pattern):
    """Find sentence matching regex pattern"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for s in sentences:
        if re.search(pattern, s.lower()) and len(s.strip()) > 20:
            return s.strip()[:200]
    return None


def _detect_omissions(text_lower):
    """Detect topics commonly expected but missing from earnings calls"""
    questions = []

    omission_checks = [
        ('capital allocation', 'capital return', 'buyback', 'dividend',
         "There was no discussion of capital allocation. How are you thinking about returning capital to shareholders?"),
        ('guidance', 'outlook', 'expect for the',
         "You didn't provide specific guidance. Can you give us a framework for how to think about the next quarter?"),
        ('free cash flow', 'cash flow from operations', 'operating cash flow',
         "Cash flow wasn't discussed. Can you walk us through free cash flow generation and uses?"),
        ('competitive', 'competitor', 'market share',
         "Can you discuss the competitive dynamics you're seeing in your key markets?"),
    ]

    for *keywords, question in omission_checks:
        if not any(kw in text_lower for kw in keywords):
            questions.append({
                'question': question,
                'topic': 'omission',
                'confidence': 0.7,
                'trigger_context': 'Topic not discussed in script',
                'source': 'omission_detection',
            })

    return questions


# ============================================================
# 2. PROPOSED ANSWERS
# ============================================================

def generate_proposed_answers(text, questions, analysis=None):
    """
    Generate proposed answer frameworks for each analyst question.
    Pulls relevant data points and quotes from the script.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    answers = []

    for q_item in questions:
        question = q_item['question']
        topic = q_item['topic']

        # Find relevant sentences from the script
        relevant = _find_relevant_sentences(sentences, topic, question)

        # Build answer framework
        answer = _build_answer_framework(question, topic, relevant, analysis)

        answers.append({
            'question': question,
            'proposed_answer': answer['answer'],
            'key_data_points': answer['data_points'],
            'supporting_quotes': answer['quotes'],
            'answer_strategy': answer['strategy'],
            'caution_notes': answer['cautions'],
        })

    return answers


def _find_relevant_sentences(sentences, topic, question):
    """Find sentences relevant to the topic/question"""
    relevant = []
    question_keywords = set(re.findall(r'\b\w{4,}\b', question.lower()))
    # Remove common stop words
    question_keywords -= {'what', 'when', 'where', 'which', 'that', 'this',
                          'have', 'been', 'with', 'from', 'your', 'about',
                          'think', 'should', 'could', 'would', 'more', 'give',
                          'help', 'walk', 'through', 'does', 'expect', 'talk'}

    for s in sentences:
        s_lower = s.lower()
        s_words = set(re.findall(r'\b\w{4,}\b', s_lower))

        # Score relevance by keyword overlap
        overlap = len(question_keywords & s_words)
        has_topic = topic.lower() in s_lower if isinstance(topic, str) else False

        # Also check for numbers/data points
        has_numbers = bool(re.search(r'\$[\d,.]+|\d+%|\d+\.\d+\s*(?:billion|million|percent)', s_lower))

        if overlap >= 2 or (has_topic and len(s.strip()) > 30) or (has_numbers and overlap >= 1):
            relevant.append({
                'sentence': s.strip()[:250],
                'relevance_score': overlap + (2 if has_numbers else 0) + (1 if has_topic else 0),
                'has_data': has_numbers,
            })

    relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
    return relevant[:5]


def _build_answer_framework(question, topic, relevant_sentences, analysis=None):
    """Build a structured answer framework"""
    data_points = []
    quotes = []
    cautions = []

    # Extract data points from relevant sentences
    for r in relevant_sentences:
        if r['has_data']:
            # Extract numbers
            numbers = re.findall(
                r'(?:\$[\d,.]+\s*(?:billion|million|thousand)?|\d+(?:\.\d+)?%|\d+(?:\.\d+)?\s*(?:billion|million|basis\s*points?))',
                r['sentence'], re.IGNORECASE
            )
            data_points.extend(numbers)
        quotes.append(r['sentence'])

    # Determine answer strategy based on topic
    strategy = _get_answer_strategy(topic, question)

    # Add caution notes
    if 'omission' in topic:
        cautions.append("This topic was not addressed in the script — prepare a response in advance")
    if 'hedging' in topic:
        cautions.append("Analyst is probing hedging language — be direct and specific in your response")

    # Build the actual proposed answer
    if relevant_sentences:
        answer_parts = []
        answer_parts.append(strategy['opening'])

        if data_points:
            answer_parts.append(f"Specifically, {', '.join(data_points[:3])}.")

        if quotes:
            # Reference the strongest supporting point
            answer_parts.append(f"As we noted, {quotes[0][:150]}")

        answer_parts.append(strategy['closing'])
        answer = ' '.join(answer_parts)
    else:
        answer = (f"{strategy['opening']} "
                  f"[Prepare specific data points for this topic.] "
                  f"{strategy['closing']}")
        cautions.append("No supporting data found in script — prepare talking points")

    return {
        'answer': answer,
        'data_points': data_points[:5],
        'quotes': quotes[:3],
        'strategy': strategy['name'],
        'cautions': cautions,
    }


ANSWER_STRATEGIES = {
    'revenue': {'name': 'Bridge & Quantify', 'opening': "Let me walk you through the key drivers.", 'closing': "We feel good about the trajectory."},
    'growth': {'name': 'Trend & Context', 'opening': "Great question — let me put the growth in context.", 'closing': "We see multiple vectors supporting continued momentum."},
    'margin': {'name': 'Puts & Takes', 'opening': "There are several moving pieces on margins.", 'closing': "Net-net, we expect the overall trend to be favorable."},
    'cost': {'name': 'Actions & Timeline', 'opening': "We've been very focused on cost management.", 'closing': "We expect these actions to yield results over the coming quarters."},
    'guidance': {'name': 'Framework & Assumptions', 'opening': "Let me share the key assumptions in our framework.", 'closing': "We've tried to balance ambition with prudence in our outlook."},
    'competi': {'name': 'Differentiation', 'opening': "Our competitive position remains strong.", 'closing': "We believe our differentiation is sustainable and growing."},
    'capital allocation': {'name': 'Priority Framework', 'opening': "Our capital allocation framework remains consistent.", 'closing': "We'll continue to be disciplined and shareholder-focused."},
    'omission': {'name': 'Proactive Address', 'opening': "That's an important topic — let me address it directly.", 'closing': "We'll provide more detail on this going forward."},
    'default': {'name': 'Direct Response', 'opening': "Let me address that directly.", 'closing': "We're confident in our positioning on this."},
}


def _get_answer_strategy(topic, question):
    """Get the recommended answer strategy for a topic"""
    for key, strategy in ANSWER_STRATEGIES.items():
        if key in topic.lower():
            return strategy
    return ANSWER_STRATEGIES['default']


# ============================================================
# 3. NEGATIVE INTERPRETATIONS
# ============================================================

# Phrases/patterns that could be interpreted negatively
NEGATIVE_INTERPRETATION_PATTERNS = [
    {
        'pattern': r'cautiously\s+optimistic',
        'interpretation': "Analysts may read 'cautiously optimistic' as management being worried but trying to sound positive",
        'severity': 'medium',
        'suggestion': 'rewrite',
        'rewrite': "Replace with specific, quantified optimism: 'We are optimistic, supported by [specific data]'",
    },
    {
        'pattern': r'challenging\s+(?:environment|market|quarter|period|conditions)',
        'interpretation': "Signals weakness — analysts will probe what specifically is 'challenging' and whether it's getting worse",
        'severity': 'medium',
        'suggestion': 'rewrite',
        'rewrite': "Be specific about the challenge and pair with your response: 'While [specific factor] has pressured [metric], we have [specific action]'",
    },
    {
        'pattern': r'headwinds?\b',
        'interpretation': "Vague negative signal — analysts will want to quantify and determine duration",
        'severity': 'low',
        'suggestion': 'rewrite',
        'rewrite': "Quantify the headwind: 'We estimate [factor] will impact [metric] by approximately [amount] over [timeframe]'",
    },
    {
        'pattern': r'(?:despite|notwithstanding)\s+(?:the\s+)?(?:challenging|difficult|tough)',
        'interpretation': "Framing results as 'despite' challenges may inadvertently emphasize the negative",
        'severity': 'low',
        'suggestion': 'rewrite',
        'rewrite': "Lead with the positive: 'We delivered [result], demonstrating the resilience of our business model'",
    },
    {
        'pattern': r'we\s+(?:remain|continue\s+to\s+be)\s+confident',
        'interpretation': "'Remain confident' can imply there was reason to lose confidence — suggests defensiveness",
        'severity': 'low',
        'suggestion': 'awareness',
        'rewrite': "State confidence directly: 'We are confident in [specific outcome] because [evidence]'",
    },
    {
        'pattern': r'(?:one[- ]time|non[- ]recurring|unusual)\s+(?:charge|item|expense|cost|impact)',
        'interpretation': "Analysts are skeptical of 'one-time' items — they may challenge whether it's truly non-recurring",
        'severity': 'high',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'(?:softness|weakness|soft\s+demand|weaker\s+than)',
        'interpretation': "Direct admission of weakness — analysts will probe depth, duration, and whether guidance accounts for it",
        'severity': 'high',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'(?:transition|transitioning|transition\s+period|pivot)',
        'interpretation': "'Transition' can signal that current performance is weak and future is uncertain",
        'severity': 'medium',
        'suggestion': 'rewrite',
        'rewrite': "Frame as strategic evolution: 'We are executing our [specific] strategy, with [metric] already showing [result]'",
    },
    {
        'pattern': r'(?:right[- ]?sizing|rationali[zs]|streamlin)',
        'interpretation': "Euphemisms for cuts — analysts will want to know the real scope and whether more are coming",
        'severity': 'medium',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'ahead\s+of\s+(?:plan|schedule|expectation)',
        'interpretation': "While positive, may prompt analysts to ask whether the original plan was too conservative",
        'severity': 'low',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'(?:modest|moderate|incremental)\s+(?:growth|improvement|gain|increase)',
        'interpretation': "'Modest' language can signal deceleration or low ambition — analysts may compare to peers",
        'severity': 'medium',
        'suggestion': 'rewrite',
        'rewrite': "Quantify the growth: 'We achieved [X]% growth, driven by [specific factors]'",
    },
    {
        'pattern': r'(?:exploring|evaluating|considering|assessing)\s+(?:options|alternatives|opportunities|strategies)',
        'interpretation': "Signals uncertainty — analysts may interpret as management not having a clear plan",
        'severity': 'medium',
        'suggestion': 'rewrite',
        'rewrite': "Show progress: 'We have identified [specific actions] and are in [stage] of implementation'",
    },
    {
        'pattern': r'longer\s+(?:than\s+)?(?:expected|anticipated|planned)',
        'interpretation': "Admission that timelines have slipped — signals execution risk",
        'severity': 'high',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'(?:mix\s+shift|unfavorable\s+mix|mix\s+headwind)',
        'interpretation': "Mix deterioration is a structural concern — analysts will probe whether it's reversible",
        'severity': 'medium',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'(?:we\'re|we\s+are)\s+(?:not\s+)?(?:immune|insulated|protected)\s+(?:from|against)',
        'interpretation': "Acknowledging vulnerability can amplify concern rather than reassure",
        'severity': 'low',
        'suggestion': 'rewrite',
        'rewrite': "Focus on resilience: 'Our [specific advantage] positions us well to manage [challenge]'",
    },
    {
        'pattern': r'(?:temporarily|short[- ]term|near[- ]term)\s+(?:impact|pressure|headwind|decline|weakness)',
        'interpretation': "Labeling something as 'temporary' without evidence will invite skepticism about duration",
        'severity': 'medium',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'(?:second\s+half|back[- ]?half|back[- ]?end)[- ]?(?:weighted|loaded|recovery|ramp)',
        'interpretation': "Back-half-weighted guidance is a classic red flag — analysts will challenge the hockey stick",
        'severity': 'high',
        'suggestion': 'awareness',
        'rewrite': None,
    },
    {
        'pattern': r'early\s+(?:innings?|days?|stages?)',
        'interpretation': "Can be used to excuse weak results or defer accountability — analysts may push for milestones",
        'severity': 'low',
        'suggestion': 'awareness',
        'rewrite': None,
    },
]


def analyze_negative_interpretations(text):
    """
    Scan the script for phrases that could be interpreted negatively.
    Returns list of findings with severity, context, and suggestions.
    """
    findings = []
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for pattern_info in NEGATIVE_INTERPRETATION_PATTERNS:
        pattern = pattern_info['pattern']

        for sentence in sentences:
            if len(sentence.strip()) < 15:
                continue
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                findings.append({
                    'matched_text': match.group(0),
                    'sentence': sentence.strip()[:250],
                    'interpretation': pattern_info['interpretation'],
                    'severity': pattern_info['severity'],
                    'suggestion_type': pattern_info['suggestion'],  # 'rewrite' or 'awareness'
                    'rewrite_suggestion': pattern_info.get('rewrite'),
                })
                break  # Only flag first occurrence per pattern

    # Sort by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    findings.sort(key=lambda x: severity_order.get(x['severity'], 3))

    return findings


# ============================================================
# 4. LITIGATION RISK ANALYSIS
# ============================================================

# Forward-looking statement indicator words
FLS_WORDS = {
    'expect', 'expects', 'expected', 'expecting', 'expectation', 'expectations',
    'anticipate', 'anticipates', 'anticipated', 'anticipating',
    'believe', 'believes', 'believed', 'believing',
    'estimate', 'estimates', 'estimated', 'estimating',
    'project', 'projects', 'projected', 'projecting', 'projection',
    'forecast', 'forecasts', 'forecasted', 'forecasting',
    'intend', 'intends', 'intended', 'intending',
    'plan', 'plans', 'planned', 'planning',
    'target', 'targets', 'targeting',
    'outlook', 'guidance', 'goal', 'goals',
}

# Words requiring safe harbor / cautionary language
REQUIRES_CAUTIONARY = {
    'will achieve', 'will deliver', 'will grow', 'will increase', 'will improve',
    'will exceed', 'will surpass', 'will reach', 'will generate',
    'guaranteed', 'guarantee', 'ensure', 'assure', 'promise', 'promises',
    'certain to', 'bound to', 'sure to',
}

# Meaningful cautionary language components
CAUTIONARY_ELEMENTS = [
    'forward-looking',
    'risks and uncertainties',
    'actual results may differ',
    'actual results could differ',
    'no obligation to update',
    'private securities litigation reform act',
    'safe harbor',
    'risk factors',
    'sec filing',
    'form 10-k',
    'form 10-q',
    'subject to risks',
    'uncertainties that could cause',
    'caution',
]

# Specificity words that make FLS more legally risky
SPECIFICITY_RISK_WORDS = [
    r'\$[\d,.]+\s*(?:billion|million)',  # Specific dollar amounts in forecasts
    r'\d+(?:\.\d+)?%\s*(?:growth|increase|improvement|margin)',  # Specific growth targets
    r'by\s+(?:Q[1-4]|(?:first|second|third|fourth)\s+quarter|year[- ]end|20\d{2})',  # Specific timelines
]


def analyze_litigation_risk(text):
    """
    Analyze the script for litigation risk related to forward-looking statements.
    Checks for:
    - FLS without proper safe harbor language
    - Overly specific promises without cautionary language
    - Missing meaningful cautionary factors
    - Absolute language about future performance
    """
    text_lower = text.lower()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    findings = []

    # 1. Check for presence of safe harbor statement
    has_safe_harbor = _check_safe_harbor(text_lower)

    if not has_safe_harbor:
        findings.append({
            'issue': 'Missing safe harbor statement',
            'severity': 'critical',
            'detail': 'No forward-looking statement disclaimer detected. The script should include PSLRA safe harbor language.',
            'recommendation': ('Add a safe harbor statement at the beginning of the call: '
                               '"This call contains forward-looking statements within the meaning of '
                               'the Private Securities Litigation Reform Act of 1995. These statements '
                               'involve risks and uncertainties that may cause actual results to differ '
                               'materially from expectations. Please refer to our SEC filings for a '
                               'discussion of these risk factors."'),
            'sentence': None,
        })

    # 2. Check for FLS without cautionary language nearby
    fls_sentences = _find_forward_looking_sentences(sentences)

    for fls in fls_sentences:
        sentence = fls['sentence']
        # Check if cautionary language exists within 3 sentences
        idx = fls['index']
        surrounding = ' '.join(s.lower() for s in sentences[max(0, idx-3):min(len(sentences), idx+3)])

        has_nearby_caution = any(elem in surrounding for elem in CAUTIONARY_ELEMENTS)

        if not has_nearby_caution and not has_safe_harbor:
            findings.append({
                'issue': 'Forward-looking statement without cautionary language',
                'severity': 'high',
                'detail': f'This statement makes forward-looking claims without nearby cautionary language.',
                'recommendation': 'Add qualifying language such as "subject to risks and uncertainties" or reference the safe harbor statement.',
                'sentence': sentence[:250],
            })

    # 3. Check for overly specific promises
    for sentence in sentences:
        s_lower = sentence.lower()
        for pattern in REQUIRES_CAUTIONARY:
            if pattern in s_lower:
                # Check for specificity amplifiers
                has_specificity = any(re.search(p, s_lower) for p in SPECIFICITY_RISK_WORDS)
                severity = 'high' if has_specificity else 'medium'
                findings.append({
                    'issue': 'Absolute language about future performance',
                    'severity': severity,
                    'detail': f'"{pattern}" combined with specific targets creates elevated litigation risk.',
                    'recommendation': 'Replace absolute language with qualified language: "We expect to..." or "Our target is..." with appropriate caveats.',
                    'sentence': sentence.strip()[:250],
                })
                break  # One finding per sentence

    # 4. Check for specific numerical guidance without range
    for sentence in sentences:
        s_lower = sentence.lower()
        has_fls_word = any(w in s_lower for w in ['expect', 'guidance', 'outlook', 'forecast', 'target', 'project'])
        if has_fls_word:
            # Check for point estimate vs. range
            has_number = bool(re.search(r'\$[\d,.]+|\d+(?:\.\d+)?%', s_lower))
            has_range = bool(re.search(r'(?:range|between|to\s+\$|\$[\d,.]+\s+(?:to|and)\s+\$[\d,.]+|\d+%?\s+to\s+\d+%?)', s_lower))

            if has_number and not has_range:
                findings.append({
                    'issue': 'Point estimate guidance without range',
                    'severity': 'medium',
                    'detail': 'Providing specific point estimates (vs. ranges) for forward-looking metrics increases litigation exposure.',
                    'recommendation': 'Consider providing a range: "We expect revenue of $X to $Y" rather than a single number.',
                    'sentence': sentence.strip()[:250],
                })

    # 5. Calculate overall litigation risk score
    risk_score = _calculate_litigation_risk_score(findings, has_safe_harbor)

    return {
        'findings': findings,
        'has_safe_harbor': has_safe_harbor,
        'fls_count': len(fls_sentences),
        'risk_score': risk_score,
        'risk_level': 'High' if risk_score >= 70 else 'Medium' if risk_score >= 40 else 'Low',
    }


def _check_safe_harbor(text_lower):
    """Check for adequate safe harbor statement"""
    count = sum(1 for elem in CAUTIONARY_ELEMENTS if elem in text_lower)
    return count >= 3  # Need at least 3 elements for adequate safe harbor


def _find_forward_looking_sentences(sentences):
    """Find sentences that are forward-looking"""
    fls = []
    for i, sentence in enumerate(sentences):
        words = set(re.findall(r"\b[\w']+\b", sentence.lower()))
        fls_overlap = words & FLS_WORDS
        has_future_ref = bool(re.search(r'\b(next|future|will|upcoming|20\d{2}|fiscal)\b', sentence.lower()))

        if len(fls_overlap) >= 1 and has_future_ref:
            fls.append({
                'sentence': sentence.strip()[:250],
                'index': i,
                'fls_words': list(fls_overlap),
            })
    return fls


def _calculate_litigation_risk_score(findings, has_safe_harbor):
    """Calculate a 0-100 litigation risk score (higher = more risk)"""
    score = 0

    if not has_safe_harbor:
        score += 40

    severity_scores = {'critical': 20, 'high': 10, 'medium': 5, 'low': 2}
    for f in findings:
        score += severity_scores.get(f['severity'], 0)

    return min(100, score)


# ============================================================
# 5. ACTIVIST TRIGGERS
# ============================================================

ACTIVIST_TRIGGER_PATTERNS = {
    'capital_allocation': {
        'patterns': [
            r'(?:excess|substantial|significant)\s+cash\s+(?:on\s+)?(?:hand|balance|position)',
            r'(?:under[- ]?leveraged|under[- ]?levered|low\s+leverage)',
            r'cash\s+(?:build|accumulation|hoard)',
        ],
        'concern': 'Excess capital on balance sheet',
        'activist_angle': 'Activists target companies hoarding cash rather than returning it to shareholders via buybacks or dividends.',
        'severity': 'high',
    },
    'margin_underperformance': {
        'patterns': [
            r'margin\s+(?:below|under|lagging|trailing)\s+(?:peer|industry|sector)',
            r'(?:operating|EBITDA)\s+margin\s+(?:declined?|compressed?|contracted?)',
            r'margin\s+(?:compression|decline|erosion)',
        ],
        'concern': 'Margin underperformance vs. peers',
        'activist_angle': 'Activists push for operational improvements, cost-cutting, or management changes when margins lag peers.',
        'severity': 'high',
    },
    'conglomerate_discount': {
        'patterns': [
            r'(?:diverse|diversified)\s+(?:portfolio|business|segment)',
            r'(?:multiple|several|various)\s+(?:segment|division|business\s+unit)',
            r'(?:non[- ]?core|peripheral)\s+(?:business|asset|segment|operation)',
        ],
        'concern': 'Conglomerate/complexity discount',
        'activist_angle': 'Activists push for spinoffs, divestitures, or simplification to unlock value in diversified businesses.',
        'severity': 'medium',
    },
    'governance_weakness': {
        'patterns': [
            r'(?:founder|family)[- ]?(?:led|controlled|run)',
            r'dual[- ]?class\s+(?:share|stock|structure|voting)',
            r'(?:combined|joint)\s+(?:chairman|chair)\s+(?:and\s+)?(?:CEO|chief)',
            r'(?:long[- ]?tenured|long[- ]?serving)\s+(?:board|director)',
        ],
        'concern': 'Corporate governance concerns',
        'activist_angle': 'Activists target governance structures they view as entrenching management at the expense of shareholders.',
        'severity': 'medium',
    },
    'value_destruction': {
        'patterns': [
            r'(?:write[- ]?down|write[- ]?off|impairment|goodwill\s+(?:charge|impairment))',
            r'(?:destroy|destruction)\s+(?:of\s+)?(?:value|shareholder)',
            r'(?:return\s+on\s+(?:invested\s+)?capital|ROIC)\s+(?:below|under|declined|fell)',
        ],
        'concern': 'Value destruction signal',
        'activist_angle': 'Writedowns and below-cost-of-capital returns signal poor capital allocation that activists will target.',
        'severity': 'high',
    },
    'missed_targets': {
        'patterns': [
            r'(?:miss|missed|below)\s+(?:our\s+)?(?:target|guidance|expectation|plan)',
            r'(?:fell\s+short|shortfall|underperform)',
            r'(?:revise|revised|lower|lowered|reduced?)\s+(?:our\s+)?(?:guidance|outlook|forecast|target|expectation)',
        ],
        'concern': 'Missed targets / guidance reduction',
        'activist_angle': 'Repeated misses create credibility gaps that activists exploit to push for management changes.',
        'severity': 'high',
    },
    'excessive_compensation': {
        'patterns': [
            r'(?:executive|management)\s+(?:compensation|pay|package)',
            r'(?:retention|performance)\s+(?:bonus|award|grant)',
            r'(?:long[- ]?term)\s+(?:incentive|compensation)\s+(?:plan|program)',
        ],
        'concern': 'Executive compensation discussion',
        'activist_angle': 'Compensation discussions can attract scrutiny, especially if results are underperforming.',
        'severity': 'low',
    },
    'strategic_drift': {
        'patterns': [
            r'(?:strategic\s+)?(?:review|alternatives|options|exploration)',
            r'(?:transform|transformation|reimagine|reinvent|pivot)',
            r'(?:new\s+direction|change\s+(?:in\s+)?(?:strategy|direction|course))',
        ],
        'concern': 'Strategic uncertainty / drift',
        'activist_angle': 'Strategic reviews signal uncertainty and create entry points for activists with their own strategic vision.',
        'severity': 'medium',
    },
    'undervaluation': {
        'patterns': [
            r'(?:stock|share)\s+(?:price|value)\s+(?:does\s+not|doesn\'t|fail)\s+(?:reflect|capture)',
            r'(?:intrinsic|underlying|true)\s+value',
            r'(?:undervalued|underappreciated|misunderstood)',
            r'(?:sum[- ]?of[- ]?(?:the[- ]?)?parts|SOTP)',
        ],
        'concern': 'Management acknowledging undervaluation',
        'activist_angle': 'Management acknowledging undervaluation validates the activist thesis and invites engagement.',
        'severity': 'high',
    },
    'low_growth_high_cash': {
        'patterns': [
            r'(?:mature|maturing|stable|steady)\s+(?:business|market|industry)',
            r'(?:cash\s+(?:cow|generative|rich))',
            r'(?:limited|low|slow)\s+(?:growth|opportunities)\s+(?:in|for)',
        ],
        'concern': 'Mature business with limited reinvestment opportunity',
        'activist_angle': 'Low-growth, cash-rich businesses are prime targets for activists demanding capital returns or strategic transactions.',
        'severity': 'medium',
    },
}


def analyze_activist_triggers(text):
    """
    Scan the script for language that could attract activist investor attention.
    Returns list of triggers with severity and context.
    """
    text_lower = text.lower()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    triggers = []

    for trigger_name, trigger_info in ACTIVIST_TRIGGER_PATTERNS.items():
        for pattern in trigger_info['patterns']:
            for sentence in sentences:
                if len(sentence.strip()) < 15:
                    continue
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    triggers.append({
                        'trigger': trigger_name,
                        'matched_text': match.group(0),
                        'sentence': sentence.strip()[:250],
                        'concern': trigger_info['concern'],
                        'activist_angle': trigger_info['activist_angle'],
                        'severity': trigger_info['severity'],
                    })
                    break  # One match per pattern per trigger is enough
            else:
                continue
            break  # Found a match for this trigger

    # Sort by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    triggers.sort(key=lambda x: severity_order.get(x['severity'], 3))

    # Calculate trigger score
    trigger_score = _calculate_activist_score(triggers)

    return {
        'triggers': triggers,
        'trigger_count': len(triggers),
        'risk_score': trigger_score,
        'risk_level': 'High' if trigger_score >= 60 else 'Medium' if trigger_score >= 30 else 'Low',
    }


def _calculate_activist_score(triggers):
    """Calculate an activist risk score 0-100"""
    severity_scores = {'high': 20, 'medium': 10, 'low': 5}
    score = sum(severity_scores.get(t['severity'], 0) for t in triggers)
    return min(100, score)


# ============================================================
# 6. GUIDANCE CLARITY SCORE
# ============================================================

# Guidance-related section indicators
GUIDANCE_INDICATORS = [
    'guidance', 'outlook', 'expect', 'forecast', 'target',
    'project', 'anticipate', 'looking ahead', 'going forward',
    'for the quarter', 'for the year', 'fiscal year',
    'next quarter', 'full year', 'second half', 'first half',
]

# Clarity-positive patterns (specific, quantified guidance)
CLARITY_POSITIVE = [
    (r'\$[\d,.]+\s*(?:billion|million|thousand)?\s*(?:to|and|-)\s*\$[\d,.]+', 'revenue_range', 3),
    (r'\d+(?:\.\d+)?%?\s*(?:to|and|-)\s*\d+(?:\.\d+)?%', 'percentage_range', 3),
    (r'(?:revenue|earnings|EPS|operating income|net income)\s+(?:of|at|approximately)\s+\$[\d,.]+', 'specific_metric', 2),
    (r'(?:revenue|earnings|EPS)\s+(?:growth|increase|improvement)\s+of\s+\d+', 'growth_target', 2),
    (r'(?:margin|margins?)\s+(?:of|at|approximately|around)\s+\d+', 'margin_target', 2),
    (r'(?:between|range\s+of)\s+\$[\d,.]+\s+(?:and|to)\s+\$[\d,.]+', 'explicit_range', 3),
    (r'(?:capex|capital\s+expenditure)\s+(?:of|at|approximately)\s+\$[\d,.]+', 'capex_guidance', 2),
    (r'(?:tax\s+rate|effective\s+tax)\s+(?:of|at|approximately|around)\s+\d+', 'tax_guidance', 2),
    (r'(?:share\s+count|diluted\s+shares)\s+(?:of|at|approximately)\s+\d+', 'share_count', 1),
    (r'(?:free\s+cash\s+flow|FCF)\s+(?:of|at|approximately)\s+\$[\d,.]+', 'fcf_guidance', 2),
]

# Clarity-negative patterns (vague, hedged guidance)
CLARITY_NEGATIVE = [
    (r'(?:we\s+)?(?:hope|aim|aspire|strive)\s+to', 'aspirational_language', -2),
    (r'(?:roughly|approximately|around|about|circa)\s+(?:in\s+line|flat|similar)', 'vague_direction', -2),
    (r'(?:positive|negative|favorable|unfavorable)\s+(?:territory|direction)', 'directional_only', -3),
    (r'(?:meaningfully|significantly|substantially|materially)\s+(?:better|worse|higher|lower|above|below)', 'qualitative_only', -3),
    (r'(?:modest|moderate|incremental|slight)\s+(?:growth|improvement|increase|decline)', 'vague_magnitude', -2),
    (r'(?:trending|tracking)\s+(?:well|in\s+line|ahead|behind)', 'vague_trending', -1),
    (r'(?:similar|comparable|consistent)\s+(?:to|with)\s+(?:last|prior|previous)', 'backward_looking_only', -1),
    (r'(?:we\'ll|we\s+will)\s+(?:update|provide\s+more|share\s+more)', 'deferred_guidance', -3),
    (r'(?:too\s+early|premature|not\s+in\s+a\s+position)\s+to\s+(?:provide|give|quantify)', 'refused_guidance', -4),
    (r'(?:wide\s+range|broad\s+range|range\s+of\s+outcomes)', 'excessively_wide_range', -2),
]

# Metrics that analysts expect guidance on
EXPECTED_GUIDANCE_METRICS = [
    ('revenue', ['revenue', 'sales', 'top line', 'top-line']),
    ('earnings', ['earnings', 'EPS', 'earnings per share', 'net income', 'bottom line']),
    ('margins', ['margin', 'margins', 'gross margin', 'operating margin', 'EBITDA margin']),
    ('capex', ['capex', 'capital expenditure', 'capital spending']),
    ('cash_flow', ['free cash flow', 'FCF', 'cash flow', 'cash generation']),
    ('growth', ['growth rate', 'growth', 'year-over-year', 'organic growth']),
]


def analyze_guidance_clarity(text):
    """
    Score the clarity and specificity of guidance in the script.
    Returns a 0-100 clarity score with breakdown.
    """
    text_lower = text.lower()
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # 1. Find guidance-related sentences
    guidance_sentences = []
    for sentence in sentences:
        s_lower = sentence.lower()
        if any(ind in s_lower for ind in GUIDANCE_INDICATORS):
            has_future = bool(re.search(
                r'\b(next|future|will|upcoming|20\d{2}|fiscal|quarter|year|expect|forecast|target|guidance)\b',
                s_lower
            ))
            if has_future or any(w in s_lower for w in ['guidance', 'outlook', 'forecast']):
                guidance_sentences.append(sentence)

    if not guidance_sentences:
        return {
            'clarity_score': 0,
            'grade': 'F',
            'detail': 'No guidance language detected in the script.',
            'guidance_sentence_count': 0,
            'positive_signals': [],
            'negative_signals': [],
            'metrics_covered': [],
            'metrics_missing': [m[0] for m in EXPECTED_GUIDANCE_METRICS],
            'findings': [{
                'issue': 'No guidance provided',
                'severity': 'critical',
                'detail': 'The script does not appear to contain any forward-looking guidance.',
            }],
        }

    guidance_text = ' '.join(guidance_sentences)
    guidance_lower = guidance_text.lower()

    # 2. Score positive clarity signals
    positive_signals = []
    positive_score = 0
    for pattern, signal_name, points in CLARITY_POSITIVE:
        matches = re.findall(pattern, guidance_lower)
        if matches:
            positive_signals.append({
                'signal': signal_name,
                'count': len(matches),
                'points': points * len(matches),
                'examples': [m if isinstance(m, str) else m[0] for m in matches[:2]],
            })
            positive_score += points * len(matches)

    # 3. Score negative clarity signals
    negative_signals = []
    negative_score = 0
    for pattern, signal_name, points in CLARITY_NEGATIVE:
        matches = re.findall(pattern, guidance_lower)
        if matches:
            negative_signals.append({
                'signal': signal_name,
                'count': len(matches),
                'points': points * len(matches),
            })
            negative_score += points * len(matches)

    # 4. Check metric coverage
    metrics_covered = []
    metrics_missing = []
    for metric_name, keywords in EXPECTED_GUIDANCE_METRICS:
        if any(kw in guidance_lower for kw in keywords):
            # Check if it has numbers
            has_quant = False
            for s in guidance_sentences:
                s_l = s.lower()
                if any(kw in s_l for kw in keywords):
                    if re.search(r'\$[\d,.]+|\d+(?:\.\d+)?%', s_l):
                        has_quant = True
                        break
            metrics_covered.append({
                'metric': metric_name,
                'quantified': has_quant,
            })
        else:
            metrics_missing.append(metric_name)

    # 5. Calculate clarity score
    # Base score
    base_score = 40  # Start at 40 for having any guidance
    metric_score = len(metrics_covered) * 5  # Up to 30 for covering key metrics
    quantified_bonus = sum(3 for m in metrics_covered if m['quantified'])  # Bonus for quantified

    raw_score = base_score + metric_score + positive_score + negative_score + quantified_bonus
    clarity_score = max(0, min(100, raw_score))

    # 6. Generate findings
    findings = []
    if metrics_missing:
        findings.append({
            'issue': f"Missing guidance on: {', '.join(metrics_missing)}",
            'severity': 'medium' if len(metrics_missing) <= 2 else 'high',
            'detail': 'Analysts typically expect guidance on these metrics.',
        })

    unquantified = [m['metric'] for m in metrics_covered if not m['quantified']]
    if unquantified:
        findings.append({
            'issue': f"Qualitative only (no numbers): {', '.join(unquantified)}",
            'severity': 'medium',
            'detail': 'These metrics are mentioned but not quantified. Consider adding specific ranges.',
        })

    for neg in negative_signals:
        findings.append({
            'issue': f"Vague guidance signal: {neg['signal'].replace('_', ' ')}",
            'severity': 'low',
            'detail': f'Detected {neg["count"]} instance(s) of vague guidance language.',
        })

    # Grade
    if clarity_score >= 85:
        grade = 'A'
    elif clarity_score >= 70:
        grade = 'B+'
    elif clarity_score >= 60:
        grade = 'B'
    elif clarity_score >= 50:
        grade = 'C+'
    elif clarity_score >= 40:
        grade = 'C'
    elif clarity_score >= 25:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'clarity_score': clarity_score,
        'grade': grade,
        'guidance_sentence_count': len(guidance_sentences),
        'positive_signals': positive_signals,
        'negative_signals': negative_signals,
        'metrics_covered': metrics_covered,
        'metrics_missing': metrics_missing,
        'findings': findings,
    }


# ============================================================
# MASTER ANALYSIS FUNCTION
# ============================================================

def run_advanced_analysis(text, base_analysis=None):
    """
    Run all advanced analyses on the transcript text.
    Returns a dict with all results.
    """
    # 1 & 2: Analyst questions + proposed answers
    questions = generate_analyst_questions(text, base_analysis)
    answers = generate_proposed_answers(text, questions, base_analysis)

    # 3: Negative interpretations
    negative_interpretations = analyze_negative_interpretations(text)

    # 4: Litigation risk
    litigation_risk = analyze_litigation_risk(text)

    # 5: Activist triggers
    activist_triggers = analyze_activist_triggers(text)

    # 6: Guidance clarity
    guidance_clarity = analyze_guidance_clarity(text)

    return {
        'analyst_questions': questions,
        'proposed_answers': answers,
        'negative_interpretations': negative_interpretations,
        'litigation_risk': litigation_risk,
        'activist_triggers': activist_triggers,
        'guidance_clarity': guidance_clarity,
    }


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":
    import json

    test_text = """
    Good afternoon, everyone. This is Tim Cook, CEO of Apple.

    We delivered an outstanding quarter with revenue of $124.3 billion, an all-time record.
    Our services business generated $23.1 billion, up 14% year over year.
    We're cautiously optimistic about the trajectory going forward.

    The challenging environment has created some headwinds, but our incredible teams
    continue to deliver. We believe our ecosystem is stronger than ever.

    Looking ahead, we expect revenue for Q2 to be in the range of $89 to $93 billion.
    We anticipate gross margin between 46% and 47%.
    Frankly, we see tremendous opportunity ahead.

    We continue to return significant capital to shareholders. During the quarter,
    we returned over $25 billion through dividends and share repurchases.

    The company believes the transition to our new platform will take longer than expected,
    but we remain confident in our strategic direction. We're exploring options for
    our non-core business segments.

    Our CapEx will be approximately $12 billion for the fiscal year.
    We project free cash flow of $110 billion.

    Safe Harbor Statement: This call contains forward-looking statements within the meaning
    of the Private Securities Litigation Reform Act. Actual results may differ materially.
    Please refer to our Form 10-K for risk factors.
    """

    results = run_advanced_analysis(test_text)

    print("=" * 60)
    print("ADVANCED ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\nAnalyst Questions: {len(results['analyst_questions'])}")
    for q in results['analyst_questions'][:5]:
        print(f"  [{q['confidence']:.0%}] {q['question']}")

    print(f"\nNegative Interpretations: {len(results['negative_interpretations'])}")
    for n in results['negative_interpretations'][:5]:
        print(f"  [{n['severity'].upper()}] {n['matched_text']} - {n['interpretation'][:80]}")

    print(f"\nLitigation Risk: {results['litigation_risk']['risk_level']} ({results['litigation_risk']['risk_score']}/100)")
    for f in results['litigation_risk']['findings'][:3]:
        print(f"  [{f['severity'].upper()}] {f['issue']}")

    print(f"\nActivist Triggers: {results['activist_triggers']['risk_level']} ({results['activist_triggers']['trigger_count']} found)")
    for t in results['activist_triggers']['triggers'][:3]:
        print(f"  [{t['severity'].upper()}] {t['concern']}")

    print(f"\nGuidance Clarity: {results['guidance_clarity']['clarity_score']}/100 ({results['guidance_clarity']['grade']})")
    print(f"  Metrics covered: {len(results['guidance_clarity']['metrics_covered'])}")
    print(f"  Metrics missing: {', '.join(results['guidance_clarity']['metrics_missing']) or 'None'}")
