"""
Configuration module for TalentScout Hiring Assistant.
Contains all application constants, model settings, and conversation parameters.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# LLM Configuration
# ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.7
MAX_TOKENS = 1024

# ──────────────────────────────────────────────
# Application Settings
# ──────────────────────────────────────────────
APP_TITLE = "TalentScout — Hiring Assistant"
APP_ICON = "🎯"
COMPANY_NAME = "TalentScout"
COMPANY_TAGLINE = "Intelligent Recruitment for Technology Placements"

# ──────────────────────────────────────────────
# Conversation-Ending Keywords
# ──────────────────────────────────────────────
EXIT_KEYWORDS = {
    "bye", "goodbye", "exit", "quit", "end", "stop",
    "thanks bye", "thank you bye", "see you", "later",
    "done", "finish", "end conversation", "close",
    "no more", "that's all", "i'm done", "im done",
}

# ──────────────────────────────────────────────
# Candidate Information Fields
# ──────────────────────────────────────────────
CANDIDATE_FIELDS = {
    "full_name": {
        "label": "Full Name",
        "icon": "👤",
        "required": True,
    },
    "email": {
        "label": "Email Address",
        "icon": "📧",
        "required": True,
    },
    "phone": {
        "label": "Phone Number",
        "icon": "📱",
        "required": True,
    },
    "years_of_experience": {
        "label": "Years of Experience",
        "icon": "📅",
        "required": True,
    },
    "desired_positions": {
        "label": "Desired Position(s)",
        "icon": "💼",
        "required": True,
    },
    "current_location": {
        "label": "Current Location",
        "icon": "📍",
        "required": True,
    },
    "tech_stack": {
        "label": "Tech Stack",
        "icon": "🛠️",
        "required": True,
    },
}

# ──────────────────────────────────────────────
# Sentiment Labels
# ──────────────────────────────────────────────
SENTIMENT_MAP = {
    "positive": {"emoji": "😊", "color": "#4ade80"},
    "neutral": {"emoji": "😐", "color": "#94a3b8"},
    "negative": {"emoji": "😟", "color": "#f87171"},
    "excited": {"emoji": "🤩", "color": "#facc15"},
    "nervous": {"emoji": "😬", "color": "#fb923c"},
    "confident": {"emoji": "💪", "color": "#60a5fa"},
}
