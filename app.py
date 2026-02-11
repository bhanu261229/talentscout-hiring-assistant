"""
TalentScout Hiring Assistant — Streamlit Application
Main entry point for the intelligent recruitment screening chatbot.

Usage:
    streamlit run app.py
"""

import streamlit as st
import logging
from datetime import datetime

from config import (
    APP_TITLE, APP_ICON, COMPANY_NAME, COMPANY_TAGLINE,
    GROQ_API_KEY, SENTIMENT_MAP,
)
from models import ConversationState, CandidateInfo
from llm_client import LLMClient
from conversation import ConversationManager
from utils import export_candidate_data, parse_technical_questions

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="centered",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS — Premium Dark Theme
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global Styles ── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] [data-testid="stToolbarActions"] {display: none !important;}

    /* ── Sidebar Styling ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #a5b4fc !important;
    }

    /* ── Main Chat Area ── */
    .main .block-container {
        padding-top: 2rem;
        max-width: 800px;
    }

    /* ── Chat Message Styling ── */
    [data-testid="stChatMessage"] {
        background: rgba(15, 15, 35, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
        animation: fadeIn 0.4s ease-out;
    }

    [data-testid="stChatMessage"]:hover {
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* ── Hero Header Card ── */
    .hero-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.05); opacity: 1; }
    }
    .hero-card h1 {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #a78bfa, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        position: relative;
    }
    .hero-card p {
        color: #c4b5fd;
        font-size: 0.95rem;
        font-weight: 300;
        position: relative;
    }

    /* ── Progress Bar ── */
    .progress-container {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    .progress-bar-bg {
        background: rgba(99, 102, 241, 0.15);
        border-radius: 8px;
        height: 8px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa);
        transition: width 0.5s ease;
    }

    /* ── Candidate Info Card ── */
    .info-card {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    .info-card .field-item {
        padding: 0.35rem 0;
        font-size: 0.85rem;
        color: #e2e8f0;
        border-bottom: 1px solid rgba(99, 102, 241, 0.08);
    }
    .info-card .field-item:last-child {
        border-bottom: none;
    }
    .info-card .field-label {
        color: #a5b4fc;
        font-weight: 500;
    }
    .info-card .field-pending {
        color: #64748b;
        font-style: italic;
    }

    /* ── Sentiment Badge ── */
    .sentiment-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.25);
        margin-top: 0.5rem;
    }

    /* ── State Badge ── */
    .state-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.5rem;
    }
    .state-greeting { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .state-gathering { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .state-questions { background: rgba(249, 115, 22, 0.15); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }
    .state-closing { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .state-ended { background: rgba(107, 114, 128, 0.15); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }

    /* ── Privacy Badge ── */
    .privacy-notice {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.75rem 0;
        font-size: 0.8rem;
        color: #6ee7b7;
    }

    /* ── Chat Input Styling ── */
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        background: rgba(15, 15, 35, 0.8) !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15) !important;
    }

    /* ── Button Styling ── */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
    }

    /* ── Divider ── */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.3), transparent);
        margin: 1rem 0;
    }

    /* ── Question Card ── */
    .question-card {
        background: rgba(15, 15, 35, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .question-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
    }
    .tech-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #a78bfa;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(99, 102, 241, 0.15);
    }
    .question-label {
        color: #e2e8f0;
        font-size: 0.9rem;
        font-weight: 400;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────
def init_session_state():
    """Initialize all session state variables."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "api_key_set" not in st.session_state:
        st.session_state.api_key_set = False
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_sentiment" not in st.session_state:
        st.session_state.current_sentiment = "neutral"
    if "greeting_sent" not in st.session_state:
        st.session_state.greeting_sent = False
    if "parsed_questions" not in st.session_state:
        st.session_state.parsed_questions = []
    if "questions_submitted" not in st.session_state:
        st.session_state.questions_submitted = False


def start_conversation(api_key: str = None):
    """Initialize the conversation manager and generate greeting."""
    key = api_key or GROQ_API_KEY
    try:
        llm = LLMClient(api_key=key)
        st.session_state.conversation_manager = ConversationManager(llm)
        st.session_state.api_key_set = True
        st.session_state.initialized = True
        st.session_state.chat_history = []
        st.session_state.greeting_sent = False
        st.session_state.current_sentiment = "neutral"
        st.session_state.parsed_questions = []
        st.session_state.questions_submitted = False
        return True
    except ValueError as e:
        st.error(str(e))
        return False


def reset_conversation():
    """Reset the conversation to start fresh."""
    st.session_state.initialized = False
    st.session_state.api_key_set = False
    st.session_state.conversation_manager = None
    st.session_state.chat_history = []
    st.session_state.greeting_sent = False
    st.session_state.current_sentiment = "neutral"
    st.session_state.parsed_questions = []
    st.session_state.questions_submitted = False


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
def render_sidebar():
    """Render the sidebar with branding, progress, and candidate info."""
    with st.sidebar:
        # Branding
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{APP_ICON}</div>
            <h1 style="font-size: 1.4rem; margin: 0; background: linear-gradient(135deg, #a78bfa, #6366f1);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {COMPANY_NAME}
            </h1>
            <p style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;">
                {COMPANY_TAGLINE}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        if st.session_state.conversation_manager:
            cm = st.session_state.conversation_manager

            # Conversation State
            state = cm.get_state()
            state_labels = {
                ConversationState.GREETING: ("Greeting", "state-greeting"),
                ConversationState.GATHERING_INFO: ("Gathering Info", "state-gathering"),
                ConversationState.TECH_QUESTIONS: ("Tech Questions", "state-questions"),
                ConversationState.ANSWERING_QUESTIONS: ("Tech Q&A", "state-questions"),
                ConversationState.CLOSING: ("Closing", "state-closing"),
                ConversationState.ENDED: ("Completed", "state-ended"),
            }
            label, css_class = state_labels.get(state, ("Unknown", "state-ended"))
            st.markdown(f"""
            <div style="text-align: center;">
                <span style="color: #94a3b8; font-size: 0.75rem;">CURRENT PHASE</span><br>
                <span class="state-badge {css_class}">{label}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # Progress
            candidate = cm.get_candidate_info()
            pct = candidate.get_completion_percentage()
            st.markdown(f"""
            <div class="progress-container">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #a5b4fc; font-size: 0.8rem; font-weight: 500;">Profile Completion</span>
                    <span style="color: #e2e8f0; font-size: 0.8rem; font-weight: 600;">{pct}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Candidate Info Card
            st.markdown("#### Candidate Profile")
            info = candidate.model_dump()
            field_labels = {
                "full_name": "Name",
                "email": "Email",
                "phone": "Phone",
                "years_of_experience": "Experience",
                "desired_positions": "Position",
                "current_location": "Location",
                "tech_stack": "Tech Stack",
            }
            html_fields = ""
            for field, label in field_labels.items():
                value = info.get(field)
                if value:
                    html_fields += f'<div class="field-item"><span class="field-label">{label}:</span> {value}</div>'
                else:
                    html_fields += f'<div class="field-item"><span class="field-label">{label}:</span> <span class="field-pending">Pending...</span></div>'
            st.markdown(f'<div class="info-card">{html_fields}</div>', unsafe_allow_html=True)

            # Sentiment
            sentiment = st.session_state.current_sentiment
            sent_data = SENTIMENT_MAP.get(sentiment, SENTIMENT_MAP["neutral"])
            st.markdown(f"""
            <div style="text-align: center; margin-top: 0.75rem;">
                <span style="color: #94a3b8; font-size: 0.75rem;">CANDIDATE MOOD</span><br>
                <span class="sentiment-badge" style="border-color: {sent_data['color']}30; color: {sent_data['color']};">
                    {sent_data['emoji']} {sentiment.capitalize()}
                </span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # Privacy Notice
            st.markdown("""
            <div class="privacy-notice">
                <strong>Data Privacy</strong><br>
                Your data is encrypted and handled in compliance with GDPR.
                We only collect information relevant to the hiring process.
            </div>
            """, unsafe_allow_html=True)

            # Action Buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("New Chat", use_container_width=True):
                    reset_conversation()
                    st.rerun()
            with col2:
                if candidate.is_complete():
                    if st.button("Export", use_container_width=True):
                        data = export_candidate_data(candidate.model_dump())
                        st.download_button(
                            "Download JSON",
                            data,
                            file_name=f"candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True,
                        )


# ──────────────────────────────────────────────
# Technical Questions Form
# ──────────────────────────────────────────────
def render_question_form():
    """Render individual answer boxes for each technical question."""
    questions = st.session_state.parsed_questions
    if not questions:
        return

    st.markdown("""
    <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 14px; padding: 1rem 1.25rem; margin: 1rem 0;">
        <p style="color: #c4b5fd; font-size: 0.9rem; margin: 0;">
            Please answer the following technical questions. Take your time — you can answer in any order.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("tech_questions_form", clear_on_submit=False):
        all_answers = {}
        for tech_group in questions:
            tech_name = tech_group["technology"]
            tech_questions = tech_group["questions"]

            st.markdown(f"""
            <div class="tech-header">
                {tech_name}
            </div>
            """, unsafe_allow_html=True)

            for i, question in enumerate(tech_questions):
                q_key = f"{tech_name}_{i}"
                st.markdown(f"""
                <div class="question-label">
                    <strong>Q{i+1}.</strong> {question}
                </div>
                """, unsafe_allow_html=True)
                answer = st.text_area(
                    f"Answer for {tech_name} Q{i+1}",
                    key=q_key,
                    height=100,
                    placeholder="Type your answer here...",
                    label_visibility="collapsed",
                )
                all_answers[f"{tech_name} - Q{i+1}: {question}"] = answer

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "Submit All Answers",
            use_container_width=True,
        )

        if submitted:
            # Compile answers into a single message
            answers_text = "Here are my answers to the technical questions:\n\n"
            has_answers = False
            for q_label, answer in all_answers.items():
                if answer.strip():
                    has_answers = True
                    answers_text += f"**{q_label}**\n{answer}\n\n"
                else:
                    answers_text += f"**{q_label}**\n_No answer provided_\n\n"

            if has_answers:
                st.session_state.questions_submitted = True
                # Add to chat and process
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": answers_text,
                })
                cm = st.session_state.conversation_manager
                response, sentiment = cm.process_message(answers_text)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                })
                if sentiment:
                    st.session_state.current_sentiment = sentiment
                st.rerun()
            else:
                st.warning("Please answer at least one question before submitting.")


# ──────────────────────────────────────────────
# Main Chat Interface
# ──────────────────────────────────────────────
def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()

    # Hero Header
    st.markdown(f"""
    <div class="hero-card">
        <h1>{APP_ICON} {COMPANY_NAME}</h1>
        <p>AI-Powered Technical Screening Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # API Key Setup (if not configured via .env)
    if not st.session_state.api_key_set:
        if GROQ_API_KEY:
            # API key from .env file
            start_conversation()
        else:
            st.markdown("""
            <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2);
                        border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
                <h3 style="color: #a5b4fc; margin: 0 0 0.5rem 0; font-size: 1rem;">Setup Required</h3>
                <p style="color: #94a3b8; font-size: 0.85rem; margin: 0;">
                    Enter your Groq API key to start. Get a free key at
                    <a href="https://console.groq.com" target="_blank" style="color: #818cf8;">console.groq.com</a>
                </p>
            </div>
            """, unsafe_allow_html=True)

            api_key = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                label_visibility="collapsed",
            )
            if st.button("Start Screening", use_container_width=True):
                if api_key.strip():
                    if start_conversation(api_key.strip()):
                        st.rerun()
                else:
                    st.warning("Please enter a valid API key.")
            return

    # Ensure conversation manager exists
    if not st.session_state.conversation_manager:
        if not start_conversation():
            return

    cm = st.session_state.conversation_manager

    # Generate greeting if not done yet
    if not st.session_state.greeting_sent:
        with st.spinner("Initializing your screening session..."):
            greeting = cm.generate_greeting()
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": greeting,
            })
            st.session_state.greeting_sent = True
            st.rerun()

    # Display Chat History
    for msg in st.session_state.chat_history:
        avatar = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Check if we need to show question form
    state = cm.get_state()
    show_question_form = (
        state in (ConversationState.TECH_QUESTIONS, ConversationState.ANSWERING_QUESTIONS)
        and st.session_state.parsed_questions
        and not st.session_state.questions_submitted
    )

    if show_question_form:
        # Show individual answer boxes for each question
        render_question_form()
    elif cm.is_ended():
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: #94a3b8;">
            <p>This screening session has ended. Click <strong>New Chat</strong> in the sidebar to start a new one.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        if user_input := st.chat_input("Type your message here..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
            })

            # Get bot response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response, sentiment = cm.process_message(user_input)
                    st.markdown(response)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
            })

            if sentiment:
                st.session_state.current_sentiment = sentiment

            # Check if tech questions were just generated — parse them
            # Must re-check state AFTER process_message since it may have changed
            current_state = cm.get_state()
            if (
                current_state in (ConversationState.TECH_QUESTIONS, ConversationState.ANSWERING_QUESTIONS)
                and not st.session_state.parsed_questions
                and cm.raw_tech_questions
            ):
                parsed = parse_technical_questions(cm.raw_tech_questions)
                if parsed:
                    st.session_state.parsed_questions = parsed

            st.rerun()


if __name__ == "__main__":
    main()
