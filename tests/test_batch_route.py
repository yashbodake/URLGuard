"""Tests for batch prediction endpoint."""

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


def test_batch_three_urls_returns_three_results() -> None:
    """POST /predict/batch with 3 URLs should return 3 results in order."""
    _load_dummy_model()
    urls = [
        "https://www.google.com",
        "http://paypal.verify-account.tk/login",
        "https://amazon.com/products",
    ]
    response = client.post("/predict/batch", json={"urls": urls})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3
    assert data["summary"]["total"] == 3
    assert data["results"][0]["url"] == urls[0]
    assert data["results"][1]["url"] == urls[1]
    assert data["results"][2]["url"] == urls[2]


def test_batch_returns_summary_with_counts() -> None:
    """Batch response should include phishing_count and legitimate_count."""
    _load_dummy_model()
    response = client.post(
        "/predict/batch",
        json={"urls": ["https://www.google.com", "http://test.tk/evil"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "phishing_count" in data["summary"]
    assert "legitimate_count" in data["summary"]
    assert data["summary"]["phishing_count"] + data["summary"]["legitimate_count"] == 2
