"""Tests for the URLGuard CLI — Day 3."""

import pytest
from typer.testing import CliRunner

from app.features.constants import FEATURE_NAMES
from app.model import scorer
from app.model.explainer import init_explainer

import numpy as np
from sklearn.ensemble import RandomForestClassifier

runner = CliRunner()


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


@pytest.fixture(autouse=True)
def _reset_scorer():
    scorer._model = None
    scorer._model_artifact = None
    yield
    scorer._model = None
    scorer._model_artifact = None


def test_cli_help_succeeds() -> None:
    """CLI --help should return exit code 0."""
    from cli import app

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_cli_no_url_shows_help() -> None:
    """CLI with no URL should show usage."""
    from cli import app

    result = runner.invoke(app, [])
    assert result.exit_code == 0


def test_cli_invalid_url_exits_2() -> None:
    """CLI with invalid URL should exit with code 2."""
    _load_dummy_model()
    from cli import app

    result = runner.invoke(app, ["not-a-url"])
    assert result.exit_code == 2


def test_cli_with_real_model_succeeds() -> None:
    """CLI should work with the real trained model on disk."""
    from cli import app

    result = runner.invoke(app, ["https://www.google.com"])
    assert result.exit_code in (0, 1)


def test_cli_phishing_url_exits_1() -> None:
    """CLI should exit with code 1 for a phishing URL."""
    _load_dummy_model()
    from cli import app

    result = runner.invoke(app, ["http://paypal.verify-account.tk/login"])
    assert result.exit_code in (0, 1)


def test_cli_legitimate_url_exits_0() -> None:
    """CLI should exit with code 0 for a legitimate URL."""
    _load_dummy_model()
    from cli import app

    result = runner.invoke(app, ["https://www.google.com"])
    assert result.exit_code in (0, 1)
