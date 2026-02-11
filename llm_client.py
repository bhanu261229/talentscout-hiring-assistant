"""
LLM Client module for TalentScout Hiring Assistant.
Handles all interactions with the Groq API (Llama 3.3 70B).
"""

import json
import logging
from typing import List, Dict, Optional

from groq import Groq

from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE, MAX_TOKENS
from models import SentimentResult

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around the Groq SDK for chat completions.
    Provides methods for general chat, technical question generation,
    and sentiment analysis.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Groq client.
        
        Args:
            api_key: Groq API key. Falls back to config if not provided.
        """
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Please set it in your .env file "
                "or pass it directly. Get a free key at https://console.groq.com"
            )
        self.client = Groq(api_key=self.api_key)
        self.model = MODEL_NAME

    def get_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
    ) -> str:
        """
        Send a chat completion request to the Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: System-level instruction for the model
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in the response
        
        Returns:
            The assistant's response text
        """
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            full_messages.extend(messages)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return (
                "I apologize, but I'm experiencing a brief technical issue. "
                "Could you please repeat your last message? I want to make sure "
                "I capture everything correctly. 🙏"
            )

    def generate_technical_questions(
        self,
        tech_stack: str,
        name: str,
        experience: str,
        positions: str,
        prompt_template: str,
    ) -> str:
        """
        Generate tailored technical questions based on candidate's tech stack.
        
        Args:
            tech_stack: Comma-separated list of technologies
            name: Candidate's name
            experience: Years of experience
            positions: Desired positions
            prompt_template: The prompt template to use
        
        Returns:
            Formatted technical questions
        """
        prompt = prompt_template.format(
            name=name,
            experience=experience,
            positions=positions,
            tech_stack=tech_stack,
        )
        messages = [{"role": "user", "content": prompt}]
        return self.get_chat_response(
            messages=messages,
            temperature=0.6,  # Slightly lower for more focused questions
            max_tokens=2048,  # Allow longer response for multiple tech stacks
        )

    def analyze_sentiment(self, message: str, prompt_template: str) -> SentimentResult:
        """
        Analyze the emotional tone of a candidate's message.
        
        Args:
            message: The candidate's message to analyze
            prompt_template: The sentiment analysis prompt template
        
        Returns:
            SentimentResult with label and confidence
        """
        try:
            prompt = prompt_template.format(message=message)
            response = self.get_chat_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Low temperature for consistent classification
                max_tokens=100,
            )
            # Parse the JSON response
            data = json.loads(response.strip())
            return SentimentResult(
                sentiment=data.get("sentiment", "neutral"),
                confidence=data.get("confidence", 0.5),
            )
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return SentimentResult(sentiment="neutral", confidence=0.5)
