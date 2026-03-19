"""
validators.py
Input validation for all API endpoints.
Prevents malicious input and ensures data integrity.
"""

import re


def validate_text_input(text):
    """Validate text input for prediction endpoints."""
    errors = []

    if not text:
        errors.append("Text cannot be empty")
        return False, errors

    if not isinstance(text, str):
        errors.append("Text must be a string")
        return False, errors

    if len(text.strip()) == 0:
        errors.append("Text cannot be only whitespace")
        return False, errors

    if len(text) > 5000:
        errors.append("Text too long. Maximum 5000 characters allowed")
        return False, errors

    if len(text) < 3:
        errors.append("Text too short. Minimum 3 characters required")
        return False, errors

    return True, []


def validate_credentials(username, password):
    """Validate username and password."""
    errors = []

    if not username or not isinstance(username, str):
        errors.append("Username is required")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters")
    elif len(username) > 50:
        errors.append("Username too long. Maximum 50 characters")
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username can only contain letters, numbers and underscores")

    if not password or not isinstance(password, str):
        errors.append("Password is required")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters")
    elif len(password) > 100:
        errors.append("Password too long. Maximum 100 characters")

    return len(errors) == 0, errors


def validate_audio_duration(duration):
    """Validate audio recording duration."""
    errors = []

    if not isinstance(duration, int):
        try:
            duration = int(duration)
        except:
            errors.append("Duration must be a number")
            return False, errors, duration

    if duration < 1:
        errors.append("Duration must be at least 1 second")
    elif duration > 30:
        errors.append("Duration cannot exceed 30 seconds")

    return len(errors) == 0, errors, duration


def sanitize_text(text):
    """Basic text sanitization."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace('\x00', '')
    # Strip excessive whitespace
    text = ' '.join(text.split())
    return text.strip()