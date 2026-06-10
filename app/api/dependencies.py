"""FastAPI dependencies for URLGuard."""

from app.model import scorer


def get_scorer():
    """Return the scorer module for dependency injection."""
    return scorer
