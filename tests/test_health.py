"""Tests for health endpoint."""

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
    scorer._model = None
    scorer._model_artifact = None
    yield
    scorer._model = None
    scorer._model_artifact = None


def _load_dummy_model():
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


def test_health_returns_model_loaded_false() -> None:
    """GET /health should show model_loaded=false without model."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is False
    assert data["status"] == "ok"


def test_health_returns_model_loaded_true() -> None:
    """GET /health should show model_loaded=true after loading."""
    _load_dummy_model()
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is True
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] > 0
