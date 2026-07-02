"""
Evaluate URLGuard model on unseen data.
Metrics: accuracy, precision, recall, F1, ROC-AUC, confusion matrix, false positives/negatives.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    precision_recall_curve, roc_curve
)

from app.model.scorer import load_model, score_url, is_loaded
from scripts.unseen_test_set import UNSEEN_URLS


def main():
    # Load model
    load_model()
    if not is_loaded():
        print("ERROR: Model failed to load.")
        sys.exit(1)

    print("=" * 70)
    print("URLGuard — Unseen Data Evaluation")
    print("=" * 70)

    # Parse labels
    true_labels = []
    predictions = []
    probabilities = []
    urls = []

    for url, label in UNSEEN_URLS:
        try:
            result = score_url(url)
            urls.append(url)
            true_labels.append(label)
            # Map label string to int: "PHISHING" -> 1, "LEGITIMATE" -> 0
            pred = 1 if result.label == "PHISHING" else 0
            predictions.append(pred)
            probabilities.append(result.risk_score)
        except Exception as e:
            print(f"  [WARN] Failed to score: {url} — {e}")

    y_true = np.array(true_labels)
    y_pred = np.array(predictions)
    y_proba = np.array(probabilities)

    # Basic counts
    n_phishing_true = int(y_true.sum())
    n_legitimate_true = int(len(y_true) - n_phishing_true)
    n_phishing_pred = int(y_pred.sum())
    n_legitimate_pred = int(len(y_pred) - n_phishing_pred)

    print(f"\nDataset: {len(y_true)} unseen URLs")
    print(f"  Actual phishing:     {n_phishing_true}")
    print(f"  Actual legitimate:   {n_legitimate_true}")
    print(f"  Predicted phishing:  {n_phishing_pred}")
    print(f"  Predicted legit:     {n_legitimate_pred}")

    # Metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    roc_auc = roc_auc_score(y_true, y_proba)

    print(f"\n{'─' * 40}")
    print(f"  Accuracy:   {accuracy:.4f}  ({accuracy*100:.2f}%)")
    print(f"  Precision:  {precision:.4f}  ({precision*100:.2f}%)")
    print(f"  Recall:     {recall:.4f}  ({recall*100:.2f}%)")
    print(f"  F1 Score:   {f1:.4f}  ({f1*100:.2f}%)")
    print(f"  ROC-AUC:    {roc_auc:.4f}  ({roc_auc*100:.2f}%)")
    print(f"{'─' * 40}")

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    print(f"\nConfusion Matrix:")
    print(f"                    Predicted")
    print(f"                 Legit    Phish")
    print(f"  Actual Legit   {tn:5d}    {fp:5d}")
    print(f"  Actual Phish   {fn:5d}    {tp:5d}")

    print(f"\n  True Positives:   {tp}  (correctly flagged phishing)")
    print(f"  True Negatives:   {tn}  (correctly flagged legitimate)")
    print(f"  False Positives:  {fp}  (legitimate flagged as phishing) ← FALSE ALARMS")
    print(f"  False Negatives:  {fn}  (phishing missed) ← SECURITY RISK")

    # False positives (legitimate sites flagged as phishing)
    print(f"\n{'=' * 70}")
    print(f"FALSE POSITIVES (Legitimate URLs Flagged as Phishing):")
    print(f"{'=' * 70}")
    fp_count = 0
    for i in range(len(urls)):
        if y_true[i] == 0 and y_pred[i] == 1:
            fp_count += 1
            print(f"  [{fp_count:3d}] {urls[i][:70]:<70}  risk={probabilities[i]:.4f}")
    if fp_count == 0:
        print("  None!")

    # False negatives (phishing missed)
    print(f"\n{'=' * 70}")
    print(f"FALSE NEGATIVES (Phishing URLs Missed):")
    print(f"{'=' * 70}")
    fn_count = 0
    for i in range(len(urls)):
        if y_true[i] == 1 and y_pred[i] == 0:
            fn_count += 1
            print(f"  [{fn_count:3d}] {urls[i][:70]:<70}  risk={probabilities[i]:.4f}")
    if fn_count == 0:
        print("  None!")

    # Correctly detected phishing (top risk scores)
    print(f"\n{'=' * 70}")
    print(f"CORRECTLY DETECTED PHISHING (Top 10 by risk score):")
    print(f"{'=' * 70}")
    correct_phishing = [(urls[i], probabilities[i]) for i in range(len(urls)) if y_true[i] == 1 and y_pred[i] == 1]
    correct_phishing.sort(key=lambda x: x[1], reverse=True)
    for i, (url, score) in enumerate(correct_phishing[:10], 1):
        print(f"  [{i:3d}] {url[:70]:<70}  risk={score:.4f}")

    # Full classification report
    print(f"\n{'=' * 70}")
    print("DETAILED CLASSIFICATION REPORT:")
    print(f"{'=' * 70}")
    print(classification_report(y_true, y_pred, target_names=["LEGITIMATE", "PHISHING"]))

    # Probability distribution
    print(f"Probability Distribution:")
    print(f"  Risk Score Range: {y_proba.min():.4f} — {y_proba.max():.4f}")
    print(f"  Mean (phishing):  {y_proba[y_true == 1].mean():.4f}")
    print(f"  Mean (legitimate):{y_proba[y_true == 0].mean():.4f}")
    print(f"  Std (phishing):   {y_proba[y_true == 1].std():.4f}")
    print(f"  Std (legitimate): {y_proba[y_true == 0].std():.4f}")

    # Threshold analysis
    print(f"\n{'=' * 70}")
    print("THRESHOLD ANALYSIS:")
    print(f"{'=' * 70}")
    for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        y_pred_t = (y_proba >= threshold).astype(int)
        acc_t = accuracy_score(y_true, y_pred_t)
        prec_t = precision_score(y_true, y_pred_t, zero_division=0)
        rec_t = recall_score(y_true, y_pred_t)
        f1_t = f1_score(y_true, y_pred_t, zero_division=0)
        tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_true, y_pred_t).ravel()
        print(f"  Threshold={threshold:.1f}  Acc={acc_t:.4f}  Prec={prec_t:.4f}  Recall={rec_t:.4f}  F1={f1_t:.4f}  FP={fp_t}  FN={fn_t}")

    # Save full results to CSV
    results_df = pd.DataFrame({
        "url": urls,
        "true_label": y_true,
        "pred_label": y_pred,
        "risk_score": y_proba,
        "correct": (y_true == y_pred).astype(int)
    })
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "unseen_eval_results.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    results_df.to_csv(csv_path, index=False)
    print(f"\nFull results saved to: {csv_path}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"COMPARISON: Train/Test Split vs Unseen Data:")
    print(f"{'=' * 70}")
    print(f"  Metric          PhiUSIIL Test Split    Unseen Data")
    print(f"  ──────────────  ──────────────────    ──────────")
    print(f"  Accuracy        0.9975                 {accuracy:.4f}")
    print(f"  Precision       0.9991                 {precision:.4f}")
    print(f"  Recall          0.9950                 {recall:.4f}")
    print(f"  F1              0.9971                 {f1:.4f}")
    print(f"  ROC-AUC         0.9988                 {roc_auc:.4f}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
