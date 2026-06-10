"""Tests for the model scorer module."""

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from app.features.constants import FEATURE_NAMES
from app.model import scorer
from app.model.explainer import _explainer, init_explainer


@pytest.fixture(autouse=True)
def _reset_scorer():
    """Reset scorer module state between tests."""
    scorer._model = None
    scorer._model_artifact = None
    yield
    scorer._model = None
    scorer._model_artifact = None


def _create_dummy_model() -> RandomForestClassifier:
    """Create a small dummy RandomForest for testing."""
    rng = np.random.RandomState(42)
    X = rng.rand(100, len(FEATURE_NAMES))
    y = rng.randint(0, 2, 100)
    model = RandomForestClassifier(
        n_estimators=10,
        max_depth=5,
        random_state=42,
        n_jobs=1,
    )
    model.fit(X, y)
    return model


def _load_dummy_model():
    """Load a dummy model directly into the scorer for testing."""
    model = _create_dummy_model()
    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "threshold": 0.4,
        "trained_at": "2024-01-01T00:00:00Z",
        "dataset_size": 100,
        "metrics": {
            "accuracy": 0.96,
            "f1": 0.95,
            "precision": 0.94,
            "recall": 0.96,
            "roc_auc": 0.98,
        },
    }
    scorer._model = model
    scorer._model_artifact = artifact
    scorer._threshold = 0.4
    scorer._feature_names = FEATURE_NAMES
    init_explainer(model)


def test_is_loaded_false() -> None:
    """is_loaded should return False when no model is loaded."""
    assert scorer.is_loaded() is False


def test_is_loaded_true() -> None:
    """is_loaded should return True after loading a model."""
    _load_dummy_model()
    assert scorer.is_loaded() is True


def test_score_url_returns_result() -> None:
    """score_url should return a PredictResultSchema with expected fields."""
    _load_dummy_model()
    result = scorer.score_url("https://www.google.com")
    assert result.url == "https://www.google.com"
    assert result.label in ("PHISHING", "LEGITIMATE")
    assert 0.0 <= result.risk_score <= 1.0
    assert result.confidence in ("HIGH", "MEDIUM", "LOW")
    assert len(result.top_features) == 5
    assert len(result.features) == 15


def test_score_url_risk_score_range() -> None:
    """risk_score should always be in [0.0, 1.0]."""
    _load_dummy_model()
    for url in [
        "https://www.google.com",
        "http://paypal.verify-account.tk/login",
        "http://192.168.1.1/admin",
    ]:
        result = scorer.score_url(url)
        assert 0.0 <= result.risk_score <= 1.0


def test_score_url_top_features_count() -> None:
    """top_features should have exactly 5 items."""
    _load_dummy_model()
    result = scorer.score_url("https://www.google.com")
    assert len(result.top_features) == 5


def test_score_url_processing_ms() -> None:
    """processing_ms should be a positive number."""
    _load_dummy_model()
    result = scorer.score_url("https://www.google.com")
    assert result.processing_ms > 0
