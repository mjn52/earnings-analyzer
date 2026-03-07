#!/usr/bin/env python3
"""
Earnings Script Analyzer — Streamlit Cloud Compatible Version
Uses native Streamlit components for reliability
"""

import streamlit as st
import re
import tempfile
from pathlib import Path
from datetime import datetime

# Import analyzer modules
from earnings_analyzer import analyze_transcript, load_lm_dictionary, get_grade
from legal_context import analyze_with_legal_context
from exporters import export_pdf, export_word, classify_sentence, get_suggested_rewrite

# Import advanced analysis module
from advanced_analysis import (
    generate_analyst_questions,
    generate_proposed_answers,
    analyze_negative_interpretations,
    analyze_litigation_risk,
    analyze_activist_triggers,
    analyze_guidance_clarity
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Earnings Script Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# LOAD RESOURCES
# ============================================================

@st.cache_resource
def load_dictionary():
    script_dir = Path(__file__).parent
    return load_lm_dictionary(script_dir / "LM_MasterDictionary.csv")

lm_dict = load_dictionary()

# ============================================================
# SESSION STATE
# ============================================================

if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'text' not in st.session_state:
    st.session_state.text = ""

# ============================================================
# LANDING PAGE
# ============================================================

if not st.session_state.analyzed:
    
    # Header
    st.markdown("### ✨ Enterprise Grade")
    st.title("Earnings Script Analyzer")
    st.markdown("*Institutional-grade sentiment analysis powered by Loughran-McDonald financial dictionary.*")
    st.markdown("---")
    
    # Input section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Upload Script")
        uploaded_file = st.file_uploader(
            "Upload your earnings script",
            type=["txt", "md", "docx"],
            help="Upload your earnings script (.txt, .md, or .docx)"
        )
    
    with col2:
        st.subheader("✏️ Or Paste Script")
        text_input = st.text_area(
            "Paste your script here",
            height=200,
            placeholder="Paste your earnings call script here... (minimum 100 characters)"
        )
    
    # Process input
    final_text = ""
    if uploaded_file:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'docx':
            # Handle Word documents
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(uploaded_file.read()))
                final_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            except Exception as e:
                st.error(f"Error reading .docx file: {e}")
                final_text = ""
        else:
            # Handle plain text files (.txt, .md)
            try:
                final_text = uploaded_file.read().decode("utf-8")
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0)
                    final_text = uploaded_file.read().decode("latin-1")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    final_text = ""
        
        if final_text:
            st.success(f"✓ Loaded {uploaded_file.name} ({len(final_text):,} characters)")
    elif text_input:
        final_text = text_input
    
    # Analyze button
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Analyze Script", use_container_width=True, type="primary"):
            if len(final_text) >= 100:
                st.session_state.text = final_text
                with st.spinner("Analyzing your script..."):
                    # Core analysis
                    st.session_state.analysis = analyze_transcript(final_text, lm_dict)
                    st.session_state.legal_analysis = analyze_with_legal_context(
                        final_text, analyze_transcript, lm_dict
                    )
                    
                    # Advanced analyses
                    analyst_questions = generate_analyst_questions(final_text, st.session_state.analysis)
                    st.session_state.analyst_qa = {
                        'questions': analyst_questions,
                        'answers': generate_proposed_answers(final_text, analyst_questions, st.session_state.analysis),
                        'total_questions': len(analyst_questions)
                    }
                    st.session_state.negative_interp = analyze_negative_interpretations(final_text)
                    st.session_state.litigation = analyze_litigation_risk(final_text)
                    st.session_state.activist = analyze_activist_triggers(final_text)
                    st.session_state.guidance_credibility = analyze_guidance_clarity(final_text)
                    
                    st.session_state.analyzed = True
                    st.rerun()
            else:
                st.error("⚠️ Please provide at least 100 characters to analyze")
    
    st.markdown("---")
    
    # Features
    st.subheader("What You Get")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Sentiment Scoring**")
        st.caption("Loughran-McDonald dictionary with 86,000+ financial terms")
        
        st.markdown("**⚖️ Legal Compliance**")
        st.caption("PSLRA-aware scoring for safe harbor analysis")
    
    with col2:
        st.markdown("**🎯 Confidence Detection**")
        st.caption("Identify hedging language and weak phrasing")
        
        st.markdown("**📝 Smart Suggestions**")
        st.caption("AI-powered rewrites for problematic passages")
    
    with col3:
        st.markdown("**🚨 Red Flag Analysis**")
        st.caption("Spot deception markers analysts notice")
        
        st.markdown("**📈 Dimensional Breakdown**")
        st.caption("Multi-factor scoring across 5 dimensions")

# ============================================================
# RESULTS PAGE
# ============================================================

else:
    analysis = st.session_state.analysis
    text = st.session_state.text
    scores = analysis['scores']
    grade = get_grade(scores['overall'])
    
    # Back button
    if st.button("← New Analysis"):
        st.session_state.analyzed = False
        st.session_state.analysis = None
        st.session_state.text = ""
        st.rerun()
    
    # Overall Score
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.metric(
            label="Overall Score",
            value=f"{int(scores['overall'])}/100",
            delta=grade
        )
    
    with col2:
        st.subheader("Performance Breakdown")
        
        dimensions = [
            ('Sentiment', scores['sentiment']),
            ('Confidence', scores['confidence']),
            ('Ownership', scores['ownership']),
            ('Clarity', scores['clarity']),
            ('Red Flags', scores['red_flags']),
        ]
        
        for name, score in dimensions:
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.write(f"**{name}**")
            with col_b:
                st.progress(int(score) / 100)
                st.caption(f"{int(score)}/100")
    
    st.markdown("---")
    
    # Flagged Issues
    st.subheader("🚨 Flagged Issues")
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    shown = 0
    
    for sentence in sentences:
        if len(sentence.strip()) < 15 or shown >= 6:
            continue
        
        color, issues = classify_sentence(sentence)
        
        if color == 'RED':
            shown += 1
            suggested, _ = get_suggested_rewrite(sentence)
            
            with st.expander(f"⚠️ {issues[0] if issues else 'Needs Review'}", expanded=False):
                st.markdown(f"**Original:** {sentence[:250]}")
                if suggested and suggested != sentence:
                    st.markdown(f"**Suggested:** {suggested[:250]}")
    
    if shown == 0:
        st.success("✅ No critical issues detected!")
    
    st.markdown("---")
    
    # Analyst Q&A Section
    if 'analyst_qa' in st.session_state and st.session_state.analyst_qa:
        qa_data = st.session_state.analyst_qa
        st.subheader(f"🎤 Likely Analyst Questions ({qa_data['total_questions']} predicted)")
        
        for i, q in enumerate(qa_data['questions'][:5], 1):
            confidence = q.get('confidence', 0.5)
            topic = q.get('topic', 'general')
            
            with st.expander(f"Q{i}: {q['question']}", expanded=False):
                st.caption(f"Topic: {topic.upper()} | Confidence: {int(confidence*100)}%")
                
                if qa_data.get('answers') and i <= len(qa_data['answers']):
                    answer_data = qa_data['answers'][i-1]
                    st.markdown(f"**Proposed Response:**")
                    st.write(answer_data.get('proposed_answer', 'No response generated')[:500])
    
    st.markdown("---")
    
    # Negative Interpretations
    if 'negative_interp' in st.session_state and st.session_state.negative_interp:
        neg_data = st.session_state.negative_interp
        high_count = len([n for n in neg_data if n.get('severity') == 'high'])
        
        st.subheader(f"⚠️ Negative Interpretation Risks ({high_count} High Severity)")
        
        for interp in neg_data[:4]:
            severity = interp.get('severity', 'medium')
            with st.expander(f"{'🔴' if severity == 'high' else '🟡'} {interp.get('interpretation', '')[:60]}", expanded=False):
                st.markdown(f"**Statement:** {interp.get('sentence', '')[:200]}")
                if interp.get('rewrite_suggestion'):
                    st.markdown(f"**Suggested Rewrite:** {interp.get('rewrite_suggestion', '')[:200]}")
    
    st.markdown("---")
    
    # Litigation Risk
    if 'litigation' in st.session_state and st.session_state.litigation:
        lit_data = st.session_state.litigation
        has_safe_harbor = lit_data.get('has_safe_harbor', False)
        risk_level = lit_data.get('risk_level', 'Unknown')
        
        st.subheader(f"⚖️ Litigation Risk: {risk_level}")
        st.write(f"Safe Harbor: {'✅ Present' if has_safe_harbor else '❌ Missing'}")
        
        for finding in lit_data.get('findings', [])[:3]:
            with st.expander(f"📋 {finding.get('issue', '')}", expanded=False):
                st.write(finding.get('detail', ''))
                if finding.get('recommendation'):
                    st.info(f"**Recommendation:** {finding.get('recommendation', '')[:250]}")
    
    st.markdown("---")
    
    # Activist Triggers
    if 'activist' in st.session_state and st.session_state.activist:
        act_data = st.session_state.activist
        risk_level = act_data.get('risk_level', 'Low')
        
        st.subheader(f"🎯 Activist Vulnerability: {risk_level}")
        
        for trigger in act_data.get('triggers', [])[:4]:
            with st.expander(f"⚔️ {trigger.get('concern', '')}", expanded=False):
                st.markdown(f"**Statement:** {trigger.get('sentence', '')[:150]}")
                st.markdown(f"**Activist Angle:** {trigger.get('activist_angle', '')}")
    
    st.markdown("---")
    
    # Guidance Credibility
    if 'guidance_credibility' in st.session_state and st.session_state.guidance_credibility:
        guid_data = st.session_state.guidance_credibility
        clarity_score = guid_data.get('clarity_score', 0)
        grade = guid_data.get('grade', 'N/A')
        
        st.subheader(f"📊 Guidance Clarity: {clarity_score}/100 (Grade: {grade})")
        st.write(guid_data.get('detail', ''))
    
    st.markdown("---")
    
    # Export Section
    st.subheader("📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            export_pdf(text, analysis, tmp.name)
            with open(tmp.name, 'rb') as f:
                st.download_button(
                    "📄 PDF Report",
                    f.read(),
                    file_name=f"earnings_analysis_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    with col2:
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            export_word(text, analysis, tmp.name)
            with open(tmp.name, 'rb') as f:
                st.download_button(
                    "📝 Word + Edits",
                    f.read(),
                    file_name=f"earnings_revisions_{datetime.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
    
    with col3:
        import json
        st.download_button(
            "💾 JSON Data",
            json.dumps(analysis, indent=2, default=str),
            file_name=f"earnings_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
