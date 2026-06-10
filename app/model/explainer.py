"""SHAP TreeExplainer singleton for feature importance."""

import logging

import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier

from .schemas import FeatureContributionSchema

logger = logging.getLogger(__name__)

_explainer: shap.TreeExplainer | None = None


def init_explainer(model: RandomForestClassifier) -> None:
    """Create SHAP TreeExplainer singleton from a trained model."""
    global _explainer
    _explainer = shap.TreeExplainer(model)
    logger.info("SHAP TreeExplainer initialized.")


def get_top_features(
    feature_vector: np.ndarray,
    feature_names: list[str],
    n: int = 5,
) -> list[FeatureContributionSchema]:
    """Return top-n features by absolute SHAP value for a single prediction."""
    if _explainer is None:
        logger.warning("SHAP explainer not initialized — returning empty list.")
        return []

    shap_values = _explainer.shap_values(feature_vector)

    # shap_values can be:
    # - A list [class_0_values, class_1_values] for binary classification
    # - An ndarray with shape (1, n_features) or (1, n_features, 2)
    if isinstance(shap_values, list):
        # Binary classification: class 1 = PHISHING
        values = np.asarray(shap_values[1][0]).flatten()
    else:
        # Single output case
        values = np.asarray(shap_values[0]).flatten()

    contributions = sorted(
        zip(feature_names, values.tolist()),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:n]

    return [
        FeatureContributionSchema(
            feature=name,
            shap_value=round(float(val), 4),
            direction="phishing" if val > 0 else "legitimate",
        )
        for name, val in contributions
    ]


def is_explainer_loaded() -> bool:
    """Check if SHAP explainer has been initialized."""
    return _explainer is not None
