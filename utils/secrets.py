"""
Unified secrets management using environment variables.

This module provides a consistent interface for accessing configuration
through environment variables, compatible with:
- Hugging Face Spaces
- Local development
- Docker deployments
- CI/CD pipelines
"""

import json
import os
from typing import Any, Optional


def get_secret(key: str, default: Any = None, nested_key: Optional[str] = None) -> Any:
    """
    Get secret from environment variables.

    Args:
        key: The environment variable key to retrieve
        default: Default value if secret is not found
        nested_key: Optional nested key for accessing nested JSON values

    Returns:
        The secret value, or default if not found

    Examples:
        >>> get_secret("STREAMLIT_ENV", "dev")
        'dev'
        >>> get_secret("google", nested_key="folder_id")
        '1SacolvvaTGaj1dd5IvJGXnQAJDxqBCjC'
    """
    # Get from environment variables
    env_key = key.upper().replace(".", "_")
    env_value = os.getenv(env_key)

    if env_value:
        # Try to parse JSON if it looks like JSON
        if isinstance(env_value, str) and env_value.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(env_value)
                if nested_key and isinstance(parsed, dict):
                    return parsed.get(nested_key, default)
                return parsed
            except json.JSONDecodeError:
                pass
        return env_value

    return default


def get_google_credentials_json() -> Optional[dict]:
    """
    Get Google OAuth credentials as a dictionary from environment variables.

    Returns:
        Dictionary containing Google credentials, or None if not found
    """
    creds_str = os.getenv("GOOGLE_CREDENTIALS")
    if creds_str:
        try:
            return json.loads(creds_str)
        except json.JSONDecodeError:
            pass

    return None


def get_google_token_json() -> Optional[dict]:
    """
    Get Google OAuth token as a dictionary from environment variables.

    Returns:
        Dictionary containing Google token, or None if not found
    """
    token_str = os.getenv("GOOGLE_TOKEN")
    if token_str:
        try:
            return json.loads(token_str)
        except json.JSONDecodeError:
            pass

    return None


def get_google_folder_id() -> Optional[str]:
    """
    Get Google Drive folder ID from environment variables.

    Returns:
        Folder ID string, or None if not found
    """
    return os.getenv("GOOGLE_FOLDER_ID")
