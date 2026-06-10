"""Train the URLGuard Random Forest classifier on the PhiUSIIL dataset."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.features.constants import FEATURE_NAMES
from app.features.extractor import extract_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")
MODEL_DIR = Path("data/model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "rf_model.joblib"

THRESHOLD = 0.4
RANDOM_STATE = 42


def load_dataset() -> pd.DataFrame:
    """Load the PhiUSIIL CSV dataset."""
    csv_path = DATA_DIR / "PhiUSIIL_Dataset.csv"
    if not csv_path.exists():
        logger.error(
            "Dataset not found at %s. Run scripts/download_data.py first.",
            csv_path,
        )
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.info("Loaded dataset: %s rows, %s columns", df.shape[0], df.shape[1])

    if "URL" not in df.columns or "label" not in df.columns:
        logger.error("Required columns 'URL' and 'label' not found.")
        logger.error("Available columns: %s", list(df.columns))
        raise ValueError("Dataset must have 'URL' and 'label' columns")

    return df


def build_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Extract features from all URLs and return feature matrix + labels."""
    logger.info("Extracting features from %d URLs...", len(df))

    feature_dicts = []
    for url in tqdm(df["URL"], desc="Extracting features"):
        feature_dicts.append(extract_features(str(url)))

    X = np.array(
        [[fd[name] for name in FEATURE_NAMES] for fd in feature_dicts],
        dtype=np.float64,
    )
    y = df["label"].values.astype(np.float64)

    logger.info("Feature matrix shape: %s", X.shape)
    logger.info(
        "Label distribution — Phishing: %d, Legitimate: %d",
        int(y.sum()),
        int((y == 0).sum()),
    )

    return X, y


def train_model(X: np.ndarray, y: np.ndarray) -> tuple[RandomForestClassifier, dict]:
    """Train RandomForest with stratified 80/20 split and return model + metrics."""
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    logger.info("Train: %d, Test: %d", len(X_train), len(X_test))

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    logger.info("Training RandomForest (n_estimators=200, max_depth=20)...")
    start = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start
    logger.info("Training completed in %.1f seconds", train_time)

    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= THRESHOLD).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
    }

    cm = confusion_matrix(y_test, y_pred)

    logger.info("=== Evaluation Report ===")
    logger.info("Accuracy:   %.4f", metrics["accuracy"])
    logger.info("F1 Score:   %.4f", metrics["f1"])
    logger.info("Precision:  %.4f", metrics["precision"])
    logger.info("Recall:     %.4f", metrics["recall"])
    logger.info("ROC-AUC:    %.4f", metrics["roc_auc"])
    logger.info("Confusion Matrix:\n%s", cm)
    logger.info("Threshold:  %.2f", THRESHOLD)

    return model, metrics


def verify_targets(metrics: dict) -> bool:
    """Check if evaluation metrics meet required targets."""
    targets = {
        "f1": 0.93,
        "recall": 0.95,
        "precision": 0.90,
    }

    all_met = True
    for metric_name, target in targets.items():
        actual = metrics.get(metric_name, 0.0)
        status = "PASS" if actual >= target else "FAIL"
        if actual < target:
            all_met = False
        logger.info(
            "  %s: %.4f (target: %.2f) [%s]",
            metric_name.upper(),
            actual,
            target,
            status,
        )

    return all_met


def save_artifact(
    model: RandomForestClassifier,
    metrics: dict,
    dataset_size: int,
) -> None:
    """Save model artifact as joblib dict."""
    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "threshold": THRESHOLD,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_size": dataset_size,
        "metrics": metrics,
    }

    joblib.dump(artifact, MODEL_PATH)
    logger.info("Model artifact saved to %s", MODEL_PATH)


def main() -> None:
    """Run the full training pipeline."""
    logger.info("=== URLGuard Training Pipeline ===")

    df = load_dataset()
    X, y = build_feature_matrix(df)
    model, metrics = train_model(X, y)

    targets_met = verify_targets(metrics)
    if not targets_met:
        logger.warning(
            "Targets NOT met — model saved anyway. "
            "Consider tuning hyperparameters or threshold."
        )
    else:
        logger.info("All evaluation targets met!")

    save_artifact(model, metrics, dataset_size=len(df))
    logger.info("=== Training Complete ===")


if __name__ == "__main__":
    main()
