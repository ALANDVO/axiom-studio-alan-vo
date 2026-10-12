"""Reproducible evaluation CLI for Axiom ML trajectory anomaly detector."""
import json
import sys
from app.services.anomaly_detector import anomaly_detector


def main() -> None:
    """Execute reproducible evaluation against ground-truth dataset and display report."""
    print("=" * 70)
    print("Axiom Studio - Machine Learning Anomaly Detection Evaluation")
    print("=" * 70)
    res = anomaly_detector.evaluate_benchmark(threshold=0.65)

    print(f"Dataset:            {res.dataset_name}")
    print(f"Sample Count:       {res.dataset_size} labeled tracks")
    print(f"Baseline Algorithm: {res.baseline_algorithm}")
    print(f"Model Algorithm:    {res.model_algorithm}")
    print("-" * 70)
    print("EVALUATION METRICS:")
    print(f"  Precision:           {res.metrics.precision:.4f} ({res.metrics.precision*100:.2f}%)")
    print(f"  Recall:              {res.metrics.recall:.4f} ({res.metrics.recall*100:.2f}%)")
    print(f"  F1-Score:            {res.metrics.f1_score:.4f}")
    print(f"  Accuracy:            {res.metrics.accuracy:.4f} ({res.metrics.accuracy*100:.2f}%)")
    print(f"  False Positive Rate: {res.metrics.false_positive_rate:.4f}")
    print(f"  ROC-AUC:             {res.metrics.roc_auc:.4f}")
    print(f"  Mean Latency/Sample: {res.metrics.mean_inference_latency_ms:.3f} ms")
    print("-" * 70)
    print("CONFUSION MATRIX:")
    print(f"  True Positives:  {res.confusion_matrix['true_positives']}")
    print(f"  False Positives: {res.confusion_matrix['false_positives']}")
    print(f"  True Negatives:  {res.confusion_matrix['true_negatives']}")
    print(f"  False Negatives: {res.confusion_matrix['false_negatives']}")
    print("-" * 70)
    if res.failure_cases:
        print(f"FAILURE / BOUNDARY CASES ({len(res.failure_cases)} cases):")
        for f in res.failure_cases:
            print(f"  - [{f['error_type']}] {f['id']}: {f['description']} (score: {f['score']:.4f})")
    else:
        print("FAILURE / BOUNDARY CASES: None detected (100% convergence).")
    print("=" * 70)


if __name__ == "__main__":
    main()
