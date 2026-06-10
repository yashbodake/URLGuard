"""Model scoring — singleton pattern for loading and scoring URLs."""

import logging
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.config import settings
from app.features.constants import FEATURE_NAMES
from app.features.extractor import extract_features, features_to_vector
from app.features.validator import validate_url

from .explainer import get_top_features, init_explainer, is_explainer_loaded
from .schemas import PredictResultSchema

logger = logging.getLogger(__name__)

_model_artifact: dict | None = None
_model: RandomForestClassifier | None = None
_feature_names: list[str] = FEATURE_NAMES
_threshold: float = settings.risk_threshold


def load_model(path: str | Path | None = None) -> bool:
    """Load model artifact from disk and initialize SHAP explainer."""
    global _model_artifact, _model, _feature_names, _threshold

    model_path = Path(path) if path else settings.model_path

    if not model_path.exists():
        logger.error("Model file not found: %s", model_path)
        return False

    try:
        _model_artifact = joblib.load(model_path)
        _model = _model_artifact["model"]
        _feature_names = _model_artifact.get("feature_names", FEATURE_NAMES)
        _threshold = _model_artifact.get("threshold", settings.risk_threshold)

        init_explainer(_model)

        logger.info(
            "Model loaded from %s (trained: %s, threshold: %.2f)",
            model_path,
            _model_artifact.get("trained_at", "unknown"),
            _threshold,
        )
        return True
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)
        _model_artifact = None
        _model = None
        return False


def is_loaded() -> bool:
    """Check if the model is loaded and ready for scoring."""
    return _model is not None


def get_artifact() -> dict | None:
    """Return the raw model artifact dict (for /model/info)."""
    return _model_artifact


def get_threshold() -> float:
    """Return the current scoring threshold."""
    return _threshold


def _confidence(score: float, threshold: float) -> str:
    """Determine confidence level from risk score and threshold."""
    if score > 0.75 or score < 0.25:
        return "HIGH"
    if 0.5 <= score <= 0.75 or 0.25 <= score < 0.5:
        return "MEDIUM"
    return "LOW"


def score_url(url: str) -> PredictResultSchema:
    """
    Full scoring pipeline: validate → extract → predict → explain.
    Returns PredictResultSchema with label, score, features, and top contributors.
    """
    start = time.perf_counter()

    features = extract_features(url)
    vector = features_to_vector(features)

    proba = _model.predict_proba(vector)[0]
    risk_score = float(proba[1])

    label = "PHISHING" if risk_score >= _threshold else "LEGITIMATE"
    confidence = _confidence(risk_score, _threshold)

    top_features = get_top_features(vector, _feature_names, n=5)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return PredictResultSchema(
        url=url,
        label=label,
        risk_score=round(risk_score, 4),
        confidence=confidence,
        top_features=top_features,
        features=features,
        processing_ms=round(elapsed_ms, 2),
    )
