"""Shared helper functions."""
import hashlib
import os
import uuid
from datetime import datetime


def generate_unique_filename(filename: str) -> str:
    """Generate a unique filename using UUID while preserving extension."""
    ext = os.path.splitext(filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def avatar_upload_path(instance, filename: str) -> str:
    """Return upload path for user avatars."""
    unique_name = generate_unique_filename(filename)
    return f"profiles/{unique_name}"


def get_client_ip(request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def hash_sensitive_value(value: str) -> str:
    """Return SHA-256 hash of a sensitive value (for safe logging)."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]
