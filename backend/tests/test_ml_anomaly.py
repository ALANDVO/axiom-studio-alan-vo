"""Tests for the Machine Learning trajectory anomaly detector and evaluation benchmark."""
from app.services.anomaly_detector import anomaly_detector


def test_nominal_aircraft_scoring():
    """Nominal cruise kinematics must yield a low anomaly score (< 0.50)."""
    score, patterns = anomaly_detector.score_kinematics(
        entity_type="aircraft",
        vel_mps=240.0,
        alt_m=10500.0,
        climb_mps=0.0,
        course_dev_deg=0.2,
    )
    assert score < 0.50
    assert len(patterns) == 0


def test_anomalous_aircraft_dive_and_divergence():
    """Extreme rate of dive and course deviation must flag high anomaly score (> 0.70)."""
    score, patterns = anomaly_detector.score_kinematics(
        entity_type="aircraft",
        vel_mps=450.0,
        alt_m=3000.0,
        climb_mps=-70.0,
        course_dev_deg=55.0,
    )
    assert score >= 0.70
    assert len(patterns) > 0
    assert any("Velocity" in p or "Course" in p or "Vertical" in p for p in patterns)


def test_ml_benchmark_evaluation_metrics():
    """Evaluation benchmark must achieve high F1, positive recall, and low latency."""
    res = anomaly_detector.evaluate_benchmark(threshold=0.65)
    assert res.dataset_size >= 15
    assert res.metrics.precision >= 0.85
    assert res.metrics.recall >= 0.85
    assert res.metrics.f1_score >= 0.85
    assert res.metrics.accuracy >= 0.85
    assert res.metrics.roc_auc >= 0.90
    assert res.metrics.mean_inference_latency_ms < 5.0
    assert res.confusion_matrix["true_positives"] > 0
    assert res.confusion_matrix["true_negatives"] > 0
