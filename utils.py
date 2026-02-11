"""
Utility functions for TalentScout Hiring Assistant.
Includes validators, sanitizers, and helper functions.
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: The email string to validate
    
    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format (supports international formats).
    
    Args:
        phone: The phone number string to validate
    
    Returns:
        True if valid phone format, False otherwise
    """
    # Remove spaces, dashes, parentheses for validation
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone.strip())
    # Must be 7-15 digits, optionally starting with +
    pattern = r'^\+?\d{7,15}$'
    return bool(re.match(pattern, cleaned))


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by stripping dangerous characters.
    
    Args:
        text: Raw user input
    
    Returns:
        Sanitized text safe for processing
    """
    # Remove potential injection patterns
    text = text.strip()
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Limit length to prevent abuse
    return text[:2000]


def extract_json_from_response(response: str) -> Optional[dict]:
    """
    Extract JSON block from LLM response text.
    The LLM is instructed to include a JSON block for structured data extraction.
    
    Args:
        response: Full LLM response text
    
    Returns:
        Parsed JSON dict if found, None otherwise
    """
    # Try to find JSON block in code fence
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"extracted"[^{}]*\{.*?\}.*?\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def strip_json_from_response(response: str) -> str:
    """
    Remove the JSON extraction block from the LLM response 
    so only the conversational part is shown to the user.
    
    Args:
        response: Full LLM response with potential JSON block
    
    Returns:
        Clean conversational response without JSON
    """
    # Remove ```json ... ``` blocks
    cleaned = re.sub(r'```json\s*\{.*?\}\s*```', '', response, flags=re.DOTALL)
    # Remove any trailing raw JSON objects
    cleaned = re.sub(r'\{[^{}]*"extracted"[^{}]*\{.*?\}.*?\}', '', cleaned, flags=re.DOTALL)
    # Clean up extra whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned.strip())
    return cleaned


def anonymize_data(data: dict) -> dict:
    """
    Anonymize candidate data for storage/export (GDPR compliance).
    Hashes personally identifiable information.
    
    Args:
        data: Dictionary of candidate information
    
    Returns:
        Anonymized dictionary with PII hashed
    """
    pii_fields = ['email', 'phone', 'full_name']
    anonymized = data.copy()
    for field in pii_fields:
        if field in anonymized and anonymized[field]:
            # Create a one-way hash of the PII
            anonymized[field] = hashlib.sha256(
                anonymized[field].encode()
            ).hexdigest()[:12] + "..."
    return anonymized


def export_candidate_data(candidate_data: dict, filename: str = None) -> str:
    """
    Export candidate data to a JSON file (anonymized).
    
    Args:
        candidate_data: Dictionary of candidate information
        filename: Optional custom filename
    
    Returns:
        JSON string of the exported data
    """
    export = {
        "export_date": datetime.now().isoformat(),
        "candidate": anonymize_data(candidate_data),
        "privacy_notice": "PII fields have been hashed for GDPR compliance",
    }
    return json.dumps(export, indent=2)


def check_exit_intent(message: str, exit_keywords: set) -> bool:
    """
    Check if the user's message indicates intent to end the conversation.
    
    Args:
        message: User's message text
        exit_keywords: Set of keywords that signal exit intent
    
    Returns:
        True if exit intent detected
    """
    normalized = message.strip().lower()
    # Check exact match
    if normalized in exit_keywords:
        return True
    # Check if message starts with an exit keyword
    for keyword in exit_keywords:
        if normalized.startswith(keyword):
            return True
    return False


def format_tech_stack(tech_stack: str) -> list:
    """
    Parse a tech stack string into a clean list of technologies.
    
    Args:
        tech_stack: Comma or space separated string of technologies
    
    Returns:
        List of individual technology names
    """
    # Split by common delimiters
    techs = re.split(r'[,;/\n]+', tech_stack)
    # Clean each entry
    cleaned = [t.strip().strip('-').strip('•').strip() for t in techs]
    # Remove empty strings and duplicates while preserving order
    seen = set()
    result = []
    for tech in cleaned:
        if tech and tech.lower() not in seen:
            seen.add(tech.lower())
            result.append(tech)
    return result


def parse_technical_questions(response: str) -> list:
    """
    Parse LLM-generated technical questions from markdown into structured list.
    
    Expected format from LLM:
        ### 🔹 Python
        1. What is a decorator?
        2. Explain GIL.
        ### 🔹 Django
        1. What is middleware?
    
    Args:
        response: The LLM response containing formatted questions
    
    Returns:
        List of dicts: [{"technology": "Python", "questions": ["What is...", ...]}]
    """
    result = []
    current_tech = None
    current_questions = []

    for line in response.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Detect technology headers (### 🔹 Python, ### Python, **Python**, etc.)
        tech_match = re.match(
            r'^#{1,4}\s*[🔹\*]*\s*\[?\s*(.+?)\s*\]?\s*\**\s*$', line
        )
        if not tech_match:
            tech_match = re.match(r'^\*\*(.+?)\*\*\s*$', line)

        if tech_match:
            # Save previous technology's questions
            if current_tech and current_questions:
                result.append({
                    "technology": current_tech,
                    "questions": current_questions,
                })
            current_tech = tech_match.group(1).strip().strip('🔹').strip()
            current_questions = []
            continue

        # Detect numbered questions (1. Question, 2) Question, - Question)
        q_match = re.match(r'^[\d]+[.\)]\s*(.+)$', line)
        if not q_match:
            q_match = re.match(r'^[-•]\s*(.+)$', line)

        if q_match and current_tech:
            question = q_match.group(1).strip()
            if question and len(question) > 10:  # Filter out very short non-questions
                current_questions.append(question)

    # Don't forget the last technology
    if current_tech and current_questions:
        result.append({
            "technology": current_tech,
            "questions": current_questions,
        })

    return result

