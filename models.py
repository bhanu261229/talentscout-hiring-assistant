"""
Data models for TalentScout Hiring Assistant.
Defines Pydantic models for candidate information and conversation state.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class ConversationState(str, Enum):
    """Tracks the current phase of the screening conversation."""
    GREETING = "greeting"
    GATHERING_INFO = "gathering_info"
    TECH_QUESTIONS = "tech_questions"
    ANSWERING_QUESTIONS = "answering_questions"
    CLOSING = "closing"
    ENDED = "ended"


class CandidateInfo(BaseModel):
    """
    Structured model for candidate information collected during screening.
    All fields start as None and are populated as the conversation progresses.
    """
    full_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = Field(None, description="Candidate's email address")
    phone: Optional[str] = Field(None, description="Candidate's phone number")
    years_of_experience: Optional[str] = Field(None, description="Years of professional experience")
    desired_positions: Optional[str] = Field(None, description="Position(s) the candidate is applying for")
    current_location: Optional[str] = Field(None, description="Candidate's current city/country")
    tech_stack: Optional[str] = Field(None, description="Technologies, languages, frameworks, tools")

    def get_filled_fields(self) -> dict:
        """Return only the fields that have been filled in."""
        return {k: v for k, v in self.model_dump().items() if v is not None}

    def get_missing_fields(self) -> list:
        """Return the names of fields that still need to be collected."""
        return [k for k, v in self.model_dump().items() if v is None]

    def is_complete(self) -> bool:
        """Check if all required fields have been collected."""
        return len(self.get_missing_fields()) == 0

    def get_completion_percentage(self) -> int:
        """Return the percentage of fields that have been filled."""
        total = len(self.model_dump())
        filled = len(self.get_filled_fields())
        return int((filled / total) * 100)

    def get_summary(self) -> str:
        """Generate a human-readable summary of collected information."""
        lines = []
        field_labels = {
            "full_name": "👤 Name",
            "email": "📧 Email",
            "phone": "📱 Phone",
            "years_of_experience": "📅 Experience",
            "desired_positions": "💼 Position(s)",
            "current_location": "📍 Location",
            "tech_stack": "🛠️ Tech Stack",
        }
        for field, label in field_labels.items():
            value = getattr(self, field)
            if value:
                lines.append(f"**{label}**: {value}")
            else:
                lines.append(f"**{label}**: _Pending..._")
        return "\n".join(lines)


class SentimentResult(BaseModel):
    """Result of sentiment analysis on a candidate's message."""
    sentiment: str = "neutral"
    confidence: float = 0.5
