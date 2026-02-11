# 🎯 TalentScout — AI Hiring Assistant

> An intelligent, LLM-powered recruitment screening chatbot built with **Streamlit** and **Groq (Llama 3.3 70B)**. Designed for TalentScout, a fictional recruitment agency specializing in technology placements.

![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Technical Details](#-technical-details)
- [Prompt Design](#-prompt-design)
- [Data Privacy & Security](#-data-privacy--security)
- [Challenges & Solutions](#-challenges--solutions)
- [Future Enhancements](#-future-enhancements)

---

## 🚀 Project Overview

**TalentScout Hiring Assistant** is an AI-powered chatbot that automates the initial screening of candidates for technology positions. It conducts a structured, conversational interview that:

1. **Collects candidate information** — name, contact, experience, desired role, location, and tech stack
2. **Generates tailored technical questions** — 3-5 questions per technology, adjusted for experience level
3. **Evaluates responses** in real-time with context-aware follow-ups
4. **Analyzes candidate sentiment** to gauge engagement and comfort level

The chatbot maintains full conversation context, handles off-topic inputs gracefully, and ensures a professional yet approachable screening experience.

---

## ✨ Features

### Core Capabilities
| Feature | Description |
|---------|-------------|
| 👋 **Smart Greeting** | Warm welcome with purpose overview and data privacy reassurance |
| 📋 **Structured Info Gathering** | Collects 7 key fields one-by-one in natural conversation |
| 💻 **Technical Question Generation** | 3-5 questions per technology, difficulty-scaled by experience |
| 🧠 **Context Retention** | Full conversation history maintained for coherent interactions |
| 🛡️ **Fallback Handling** | Graceful redirection for off-topic or unclear inputs |
| 🚪 **Smart Exit Detection** | Recognizes 18+ exit keywords and closes conversation gracefully |

### Bonus Features
| Feature | Description |
|---------|-------------|
| 😊 **Sentiment Analysis** | Real-time mood detection (positive, negative, nervous, confident, etc.) |
| 📊 **Progress Tracking** | Visual progress bar showing profile completion percentage |
| 📥 **Data Export** | Anonymized JSON export of candidate data (GDPR compliant) |
| 🎨 **Premium Dark UI** | Glassmorphism design with gradient accents and micro-animations |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                 Streamlit Frontend                │
│    (app.py — Chat UI, Sidebar, Styling)          │
├──────────────────────────────────────────────────┤
│            Conversation Manager                   │
│   (conversation.py — State Machine & Flow)       │
├──────────┬───────────────┬───────────────────────┤
│ Prompt   │  LLM Client   │    Data Models        │
│ Engine   │  (llm_client)  │    (models.py)       │
│(prompts) │  Groq SDK     │    Pydantic           │
├──────────┴───────────────┴───────────────────────┤
│           Utilities & Configuration              │
│     (utils.py — Validation, Sanitization)        │
│     (config.py — Constants & Settings)           │
└──────────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Groq Cloud    │
              │ Llama 3.3 70B   │
              └─────────────────┘
```

### Module Breakdown

| Module | Lines | Purpose |
|--------|-------|---------|
| `app.py` | ~320 | Streamlit UI with custom CSS, chat interface, sidebar |
| `conversation.py` | ~220 | State machine managing conversation flow |
| `prompts.py` | ~180 | All prompt templates for LLM interactions |
| `llm_client.py` | ~130 | Groq API wrapper with error handling |
| `models.py` | ~75 | Pydantic data models for type safety |
| `utils.py` | ~170 | Validators, sanitizers, JSON extraction |
| `config.py` | ~80 | Application constants and settings |

---

## 💻 Installation

### Prerequisites
- Python 3.9 or higher
- A free [Groq API Key](https://console.groq.com)

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/talentscout-hiring-assistant.git
cd talentscout-hiring-assistant

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and paste your Groq API key

# 5. Run the application
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

> **Note:** If you don't configure `GROQ_API_KEY` in `.env`, the app will prompt you to enter it directly in the UI.

---

## 📖 Usage Guide

### Starting a Screening Session

1. **Launch the app** — the chatbot greets you and explains the screening process
2. **Provide your information** — answer naturally; the bot collects one field at a time:
   - Full Name → Email → Phone → Experience → Desired Position → Location → Tech Stack
3. **Answer technical questions** — the bot generates 3-5 questions per technology
4. **End the conversation** — say "bye", "exit", or "done" at any time

### Sidebar Features

- **📊 Progress Bar** — tracks how much candidate info has been collected
- **👤 Candidate Profile** — live-updating card with all collected info
- **😊 Sentiment Indicator** — real-time mood detection badge
- **🔄 New Chat** — reset and start a fresh screening
- **📥 Export** — download anonymized candidate data as JSON

### Exit Keywords
The chatbot recognizes: `bye`, `goodbye`, `exit`, `quit`, `end`, `stop`, `done`, `finish`, `close`, `see you`, `later`, `that's all`, `i'm done`, and more.

---

## 🔧 Technical Details

### Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Frontend** | Streamlit 1.30+ | Rapid prototyping with built-in chat UI components |
| **LLM** | Groq (Llama 3.3 70B) | Free tier, ultra-fast inference (~200ms), high quality |
| **Data Models** | Pydantic v2 | Type-safe data validation with JSON serialization |
| **Environment** | python-dotenv | Secure API key management |
| **Styling** | Custom CSS | Glassmorphism dark theme with Inter font |

### Key Design Decisions

1. **State Machine Pattern** — The `ConversationManager` uses an explicit state enum (`GREETING → GATHERING_INFO → TECH_QUESTIONS → ANSWERING_QUESTIONS → CLOSING → ENDED`) to ensure predictable conversation flow and prevent state corruption.

2. **Dual-Output LLM Prompting** — During info gathering, the LLM produces both a conversational response (shown to the user) and a JSON extraction block (parsed internally). This allows natural conversation while reliably extracting structured data.

3. **Context Window Management** — Full message history is passed to the LLM for context coherence. For fallback handling, only the last 6 messages are sent to keep context focused and reduce token usage.

4. **Temperature Tuning** — Different temperatures for different tasks:
   - `0.7` for general conversation (natural, varied responses)
   - `0.6` for technical questions (focused but creative)
   - `0.3` for sentiment analysis (consistent classification)

---

## 🧠 Prompt Design

### Design Philosophy

All prompts follow a structured template pattern with:
- **Role definition** — establishes the LLM's persona and boundaries
- **Explicit instructions** — numbered steps for the LLM to follow
- **Guardrails** — prevents deviation from recruitment purpose
- **Context injection** — dynamic data about conversation state

### Prompt Types

#### 1. System Prompt (Role-Playing + Guardrails)
```
You are TalentBot, a professional AI Hiring Assistant for TalentScout...
- NEVER deviate from recruitment purpose
- Ask for ONE piece of information at a time
- NEVER ask for passwords, SSN, or sensitive data
```
The system prompt is dynamically augmented with the current conversation state and collected candidate data.

#### 2. Information Gathering (Few-Shot + JSON Extraction)
The LLM is instructed to:
- Respond conversationally to the candidate
- Append a structured JSON block with extracted fields
- The JSON is parsed and stripped from the displayed response

#### 3. Technical Questions (Chain-of-Thought + Experience Scaling)
```
For each technology in their tech stack:
- 0-2 years: Foundational concepts
- 3-5 years: Intermediate + design decisions
- 6+ years: Advanced + architecture + optimization
```

#### 4. Fallback Handling (Redirection + Empathy)
When off-topic input is detected, the LLM acknowledges the input politely and redirects to the screening purpose with context about what needs to be collected next.

#### 5. Sentiment Analysis (Classification Prompt)
A low-temperature prompt that classifies messages into: `positive`, `neutral`, `negative`, `excited`, `nervous`, `confident` — with a confidence score.

---

## 🔒 Data Privacy & Security

| Practice | Implementation |
|----------|---------------|
| **No persistent storage** | Candidate data exists only in session state (memory) |
| **Anonymized exports** | PII fields are SHA-256 hashed before JSON export |
| **Input sanitization** | All inputs stripped of injection patterns, length-limited to 2000 chars |
| **GDPR compliance** | Privacy notice displayed; only relevant data collected |
| **No logging of PII** | Utility functions never log raw candidate data |
| **API key security** | Keys stored in `.env` (gitignored), never hardcoded |
| **Exit on demand** | Candidates can end the conversation at any time |

---

## 🧩 Challenges & Solutions

### Challenge 1: Extracting Structured Data from Natural Conversation
**Problem:** LLMs produce free-form text, but we need structured candidate fields.
**Solution:** Dual-output prompting — the LLM generates a human response + a JSON extraction block. The `extract_json_from_response()` utility parses the JSON and `strip_json_from_response()` removes it before displaying.

### Challenge 2: Maintaining Context Across Long Conversations
**Problem:** As conversations grow, context can drift or become inconsistent.
**Solution:** Full message history is injected into each LLM call, with the system prompt dynamically updated with the current state and collected data. For secondary tasks (fallback, sentiment), a trimmed context window is used.

### Challenge 3: Preventing Off-Topic Deviation
**Problem:** Users might ask unrelated questions, try prompt injection, or go off-topic.
**Solution:** Multi-layered defense: (1) System prompt guardrails forbid non-recruitment activities, (2) State-aware prompts anchor each response to the current screening phase, (3) Dedicated fallback handler redirects politely.

### Challenge 4: Making Technical Questions Relevant
**Problem:** Generic questions don't properly assess candidates.
**Solution:** Questions are generated with three context variables — tech stack, experience level, and desired position — allowing the LLM to calibrate difficulty and relevance. Temperature is set to 0.6 for focused but non-repetitive output.

### Challenge 5: Graceful Error Recovery
**Problem:** API failures, malformed responses, or edge cases shouldn't break the experience.
**Solution:** Every LLM call has try/catch wrapping that returns a friendly fallback message. JSON extraction gracefully returns `None` on parse failure. The conversation state machine prevents invalid transitions.

---

## 🔮 Future Enhancements

- [ ] **Multilingual support** — detect language and respond accordingly
- [ ] **Resume parsing** — upload and auto-extract candidate info from PDF resumes
- [ ] **Interview scheduling** — integrate with Google Calendar API
- [ ] **Admin dashboard** — view, filter, and rank screened candidates
- [ ] **Cloud deployment** — deploy on Streamlit Cloud or AWS with persistent storage
- [ ] **Scoring system** — AI-powered scoring of technical answers
- [ ] **Voice input** — integrate speech-to-text for accessibility

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ for TalentScout**

*Intelligent Recruitment for Technology Placements*

</div>
