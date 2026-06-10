"""URL validation utilities."""

import logging

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """Check if a URL string starts with http:// or https://."""
    if not url or not isinstance(url, str):
        return False
    return url.startswith("http://") or url.startswith("https://")
