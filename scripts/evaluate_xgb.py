"""Evaluate XGBoost model on unseen data without SHAP (to avoid explainer issues)."""

import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.features.constants import FEATURE_NAMES
from app.features.extractor import extract_features
from scripts.unseen_test_set import UNSEEN_URLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = Path("data/model/rf_model.joblib")
THRESHOLD = 0.4  # same as used in training

def load_model():
    """Load model artifact (ignore explainer)."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    feature_names = artifact.get("feature_names", FEATURE_NAMES)
    threshold = artifact.get("threshold", THRESHOLD)
    return model, feature_names, threshold

def main():
    model, feature_names, threshold = load_model()
    logger.info("Model loaded: %s", type(model).__name__)

    # Prepare data
    urls = []
    y_true = []
    y_proba = []

    for url, label in UNSEEN_URLS:
        try:
            features = extract_features(url)
            # Ensure order matches FEATURE_NAMES
            vector = np.array([[features[name] for name in feature_names]], dtype=np.float64)
            proba = model.predict_proba(vector)[0, 1]  # probability of class 1 (phishing)
            urls.append(url)
            y_true.append(label)
            y_proba.append(proba)
        except Exception as e:
            logger.warning("Failed to process %s: %s", url, e)
            continue

    y_true = np.array(y_true, dtype=int)
    y_proba = np.array(y_proba, dtype=float)
    y_pred = (y_proba >= threshold).astype(int)

    # Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, y_proba)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    logger.info("=== Unseen Data Evaluation (XGBoost) ===")
    logger.info("Samples: %d (legit=%d, phish=%d)", len(y_true), (y_true==0).sum(), (y_true==1).sum())
    logger.info("Accuracy:  %.4f", acc)
    logger.info("Precision: %.4f", prec)
    logger.info("Recall:    %.4f", rec)
    logger.info("F1 Score:  %.4f", f1)
    logger.info("ROC-AUC:   %.4f", roc_auc)
    logger.info("Confusion Matrix:")
    logger.info("              Pred Legit  Pred Phish")
    logger.info("Actual Legit      %5d       %5d", tn, fp)
    logger.info("Actual Phish      %5d       %5d", fn, tp)
    logger.info("False Positives: %d", fp)
    logger.info("False Negatives: %d", fn)

    # Show some false positives for inspection
    if fp > 0:
        logger.info("\nFirst 5 false positives (legitimate URLs flagged as phishing):")
        shown = 0
        for i in range(len(urls)):
            if y_true[i] == 0 and y_pred[i] == 1:
                logger.info("  %s (risk=%.4f)", urls[i], y_proba[i])
                shown += 1
                if shown >= 5:
                    break

    # Show some false negatives
    if fn > 0:
        logger.info("\nFirst 5 false negatives (phishing URLs missed):")
        shown = 0
        for i in range(len(urls)):
            if y_true[i] == 1 and y_pred[i] == 0:
                logger.info("  %s (risk=%.4f)", urls[i], y_proba[i])
                shown += 1
                if shown >= 5:
                    break

if __name__ == "__main__":
    main()
