"""Tests for the predict API routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.model import scorer
from app.model.explainer import init_explainer
from app.features.constants import FEATURE_NAMES

import numpy as np
from sklearn.ensemble import RandomForestClassifier


@pytest.fixture(autouse=True)
def _reset_scorer():
    """Reset scorer module state between tests."""
    scorer._model = None
    scorer._model_artifact = None
    yield
    scorer._model = None
    scorer._model_artifact = None


def _load_dummy_model():
    """Load a dummy model for testing API routes."""
    rng = np.random.RandomState(42)
    X = rng.rand(100, len(FEATURE_NAMES))
    y = rng.randint(0, 2, 100)
    model = RandomForestClassifier(
        n_estimators=10, max_depth=5, random_state=42, n_jobs=1,
    )
    model.fit(X, y)

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


client = TestClient(app)


def test_predict_no_model_returns_503() -> None:
    """POST /predict with no model loaded should return 503."""
    response = client.post("/predict", json={"url": "https://www.google.com"})
    assert response.status_code == 503


def test_predict_invalid_url_returns_422() -> None:
    """POST /predict with invalid URL format should return 422."""
    _load_dummy_model()
    response = client.post("/predict", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_predict_returns_200() -> None:
    """POST /predict with valid URL should return 200 with expected fields."""
    _load_dummy_model()
    response = client.post(
        "/predict", json={"url": "https://www.google.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "risk_score" in data
    assert "features" in data
    assert data["label"] in ("PHISHING", "LEGITIMATE")


def test_predict_batch_too_large_returns_413() -> None:
    """POST /predict/batch with more than 100 URLs should return 413."""
    _load_dummy_model()
    urls = [f"http://example{i}.com" for i in range(101)]
    response = client.post("/predict/batch", json={"urls": urls})
    assert response.status_code == 413


def test_health_model_not_loaded() -> None:
    """GET /health should show model_loaded=false when no model."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is False


def test_health_model_loaded() -> None:
    """GET /health should show model_loaded=true after loading."""
    _load_dummy_model()
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is True
