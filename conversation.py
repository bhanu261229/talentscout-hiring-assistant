"""
Conversation flow engine for TalentScout Hiring Assistant.
Manages the state machine, context injection, and message processing.
"""

import logging
from typing import List, Dict, Tuple, Optional

from config import EXIT_KEYWORDS, CANDIDATE_FIELDS
from models import ConversationState, CandidateInfo
from prompts import (
    SYSTEM_PROMPT,
    GREETING_PROMPT,
    INFO_GATHERING_PROMPT,
    TECH_QUESTIONS_PROMPT,
    FALLBACK_PROMPT,
    CLOSING_PROMPT,
    EXIT_DETECTED_PROMPT,
    SENTIMENT_PROMPT,
    EVALUATE_ANSWER_PROMPT,
)
from llm_client import LLMClient
from utils import (
    sanitize_input,
    extract_json_from_response,
    strip_json_from_response,
    check_exit_intent,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages the full lifecycle of a screening conversation.
    Acts as a state machine that transitions through:
    GREETING → GATHERING_INFO → TECH_QUESTIONS → ANSWERING_QUESTIONS → CLOSING → ENDED
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the conversation manager.
        
        Args:
            llm_client: Instance of the LLM client for API calls
        """
        self.llm = llm_client
        self.state = ConversationState.GREETING
        self.candidate = CandidateInfo()
        self.messages: List[Dict[str, str]] = []
        self.technical_questions_asked = False
        self.current_sentiment = "neutral"
        self.raw_tech_questions = ""  # Store raw questions text for UI parsing

    def _build_system_prompt(self) -> str:
        """Build the system prompt with current context injected."""
        state_descriptions = {
            ConversationState.GREETING: "You are greeting the candidate for the first time. Welcome them and ask for their name.",
            ConversationState.GATHERING_INFO: f"You are collecting candidate information. Missing fields: {', '.join(self.candidate.get_missing_fields())}. Collected: {self.candidate.get_filled_fields()}",
            ConversationState.TECH_QUESTIONS: "You have collected all candidate info and are now presenting technical screening questions based on their tech stack.",
            ConversationState.ANSWERING_QUESTIONS: "The candidate is answering technical questions. Evaluate their responses and guide them through the remaining questions.",
            ConversationState.CLOSING: "The screening is complete. Thank the candidate and inform them about next steps.",
            ConversationState.ENDED: "The conversation has ended.",
        }
        return SYSTEM_PROMPT.format(
            state_context=state_descriptions.get(self.state, ""),
            candidate_context=self.candidate.get_summary(),
        )

    def generate_greeting(self) -> str:
        """Generate the initial greeting message."""
        response = self.llm.get_chat_response(
            messages=[{"role": "user", "content": GREETING_PROMPT}],
            system_prompt=self._build_system_prompt(),
        )
        self.state = ConversationState.GATHERING_INFO
        self.messages.append({"role": "assistant", "content": response})
        return response

    def process_message(self, user_message: str) -> Tuple[str, Optional[str]]:
        """
        Process a user message and return the appropriate response.
        
        Args:
            user_message: The candidate's input text
        
        Returns:
            Tuple of (response_text, sentiment_label or None)
        """
        # Sanitize input
        user_message = sanitize_input(user_message)
        
        # Record the user message
        self.messages.append({"role": "user", "content": user_message})

        # Check for exit intent at ANY stage
        if check_exit_intent(user_message, EXIT_KEYWORDS):
            return self._handle_exit(), self.current_sentiment

        # Analyze sentiment (bonus feature)
        sentiment_label = self._analyze_sentiment(user_message)

        # Route to appropriate handler based on state
        if self.state == ConversationState.GATHERING_INFO:
            response = self._handle_info_gathering(user_message)
        elif self.state in (ConversationState.TECH_QUESTIONS, ConversationState.ANSWERING_QUESTIONS):
            response = self._handle_tech_interaction(user_message)
        elif self.state == ConversationState.CLOSING:
            response = self._handle_closing()
        else:
            response = self._handle_fallback(user_message)

        # Record assistant response
        self.messages.append({"role": "assistant", "content": response})
        return response, sentiment_label

    def _handle_info_gathering(self, user_message: str) -> str:
        """
        Handle messages during the information gathering phase.
        Uses LLM to extract structured data from conversational input.
        """
        # Build the info gathering prompt with current field status
        field_status = {}
        for field in CANDIDATE_FIELDS:
            value = getattr(self.candidate, field)
            field_status[field] = value if value else "❌ Not yet collected"

        prompt = INFO_GATHERING_PROMPT.format(**field_status)

        # Get LLM response with full conversation context
        response = self.llm.get_chat_response(
            messages=self.messages,
            system_prompt=self._build_system_prompt() + "\n\n" + prompt,
        )

        # Extract structured data from LLM response
        extracted_json = extract_json_from_response(response)
        if extracted_json and "extracted" in extracted_json:
            extracted = extracted_json["extracted"]
            for field, value in extracted.items():
                if value and value != "null" and hasattr(self.candidate, field):
                    current = getattr(self.candidate, field)
                    if current is None:
                        setattr(self.candidate, field, str(value))

            # Check if all info is collected
            if extracted_json.get("all_collected") or self.candidate.is_complete():
                self.state = ConversationState.TECH_QUESTIONS

        # Also do a simple heuristic check: if candidate info looks complete, transition
        if self.candidate.is_complete() and self.state != ConversationState.TECH_QUESTIONS:
            self.state = ConversationState.TECH_QUESTIONS

        # Clean response for display (remove JSON block)
        clean_response = strip_json_from_response(response)
        
        # If we just transitioned to tech questions, generate them
        if self.state == ConversationState.TECH_QUESTIONS and not self.technical_questions_asked:
            tech_questions = self._generate_tech_questions()
            self.raw_tech_questions = tech_questions  # Store for UI parsing
            clean_response = clean_response.rstrip() + "\n\n" + tech_questions
            self.technical_questions_asked = True
            self.state = ConversationState.ANSWERING_QUESTIONS

        return clean_response

    def _generate_tech_questions(self) -> str:
        """Generate technical screening questions based on the candidate's tech stack."""
        return self.llm.generate_technical_questions(
            tech_stack=self.candidate.tech_stack or "General Programming",
            name=self.candidate.full_name or "Candidate",
            experience=self.candidate.years_of_experience or "Unknown",
            positions=self.candidate.desired_positions or "Software Engineer",
            prompt_template=TECH_QUESTIONS_PROMPT,
        )

    def _handle_tech_interaction(self, user_message: str) -> str:
        """Handle messages during the technical Q&A phase."""
        # Use the full conversation context so the LLM knows which questions were asked
        response = self.llm.get_chat_response(
            messages=self.messages,
            system_prompt=self._build_system_prompt(),
        )
        return response

    def _handle_closing(self) -> str:
        """Generate the closing message."""
        prompt = CLOSING_PROMPT.format(
            name=self.candidate.full_name or "there",
            positions=self.candidate.desired_positions or "the position",
        )
        response = self.llm.get_chat_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self._build_system_prompt(),
        )
        self.state = ConversationState.ENDED
        return response

    def _handle_exit(self) -> str:
        """Handle when the candidate wants to end the conversation."""
        info_status = (
            "Complete" if self.candidate.is_complete()
            else f"Partial ({self.candidate.get_completion_percentage()}% complete)"
        )
        prompt = EXIT_DETECTED_PROMPT.format(
            name=self.candidate.full_name or "there",
            info_status=info_status,
        )
        response = self.llm.get_chat_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self._build_system_prompt(),
        )
        self.state = ConversationState.ENDED
        return response

    def _handle_fallback(self, user_message: str) -> str:
        """Handle unexpected or off-topic messages."""
        prompt = FALLBACK_PROMPT.format(
            message=user_message,
            state=self.state.value,
        )
        response = self.llm.get_chat_response(
            messages=self.messages[-6:],  # Last 3 exchanges for context
            system_prompt=self._build_system_prompt() + "\n\n" + prompt,
        )
        return response

    def _analyze_sentiment(self, message: str) -> str:
        """
        Analyze the sentiment of the candidate's message.
        Returns the sentiment label.
        """
        try:
            result = self.llm.analyze_sentiment(message, SENTIMENT_PROMPT)
            self.current_sentiment = result.sentiment
            return result.sentiment
        except Exception:
            return "neutral"

    def get_state(self) -> ConversationState:
        """Get current conversation state."""
        return self.state

    def get_candidate_info(self) -> CandidateInfo:
        """Get current candidate information."""
        return self.candidate

    def get_messages(self) -> List[Dict[str, str]]:
        """Get full message history."""
        return self.messages

    def is_ended(self) -> bool:
        """Check if the conversation has ended."""
        return self.state == ConversationState.ENDED
