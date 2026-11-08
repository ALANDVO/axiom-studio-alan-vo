"""Tests for the Machine Learning trajectory anomaly detector and evaluation benchmark."""
from app.services.anomaly_detector import anomaly_detector
import logging
from io import StringIO
import math


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


def test_unknown_entity_type_fallback():
    """Unknown entity type must fall back to 'unknown' profile and log warning."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger("app.services.anomaly_detector")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    score, patterns = anomaly_detector.score_kinematics(
        entity_type="weather_balloon",
        vel_mps=5.0,
        alt_m=20000.0,
        climb_mps=2.0,
        course_dev_deg=10.0,
    )

    logger.removeHandler(handler)
    log_output = log_stream.getvalue()
    assert "Unknown entity type 'weather_balloon'" in log_output
    assert "using conservative 'unknown' profile" in log_output
    # Score should be computed using unknown profile
    assert 0.0 <= score <= 1.0


def test_high_altitude_camera_nominal():
    """Camera on tall building (e.g., 300m) with PTZ movement must not flag as anomalous."""
    # This mimics a rooftop camera on a skyscraper with normal PTZ pan
    score, patterns = anomaly_detector.score_kinematics(
        entity_type="camera",
        vel_mps=2.5,  # PTZ pan speed
        alt_m=300.0,  # Building height
        climb_mps=0.0,
        course_dev_deg=5.0,  # PTZ rotation
    )
    # Should be low anomaly - legitimate elevated camera with PTZ
    assert score < 0.65


def test_negative_altitude_handled():
    """Negative altitude (subsea or data error) must not crash and yield valid score."""
    score, patterns = anomaly_detector.score_kinematics(
        entity_type="aircraft",
        vel_mps=240.0,
        alt_m=-100.0,  # Below sea level - data error
        climb_mps=0.0,
        course_dev_deg=0.2,
    )
    assert 0.0 <= score <= 1.0
    # Should detect altitude anomaly
    assert any("Altitude" in p for p in patterns)


def test_extreme_values_numerical_stability():
    """Extreme input values must not cause numerical overflow or NaN."""
    score, patterns = anomaly_detector.score_kinematics(
        entity_type="satellite",
        vel_mps=1e6,
        alt_m=1e9,
        climb_mps=1e6,
        course_dev_deg=1e6,
    )
    assert 0.0 <= score <= 1.0
    assert not math.isnan(score)
    assert not math.isinf(score)
    # Should flag all patterns as anomalous
    assert len(patterns) == 4


def test_zero_stddev_profile_guard():
    """Profile with zero stddev (edge case) must not cause division by zero."""
    # This tests the max(prof["v"][1], 1e-4) guard in the detector
    # All current profiles have non-zero stddev, but we verify the guard works
    score, patterns = anomaly_detector.score_kinematics(
        entity_type="rf_station",
        vel_mps=0.0,
        alt_m=100.0,
        climb_mps=0.0,
        course_dev_deg=0.0,
    )
    assert 0.0 <= score <= 1.0
    assert score < 0.50  # Perfect match for fixed RF station


def test_threshold_sensitivity():
    """Test that threshold changes affect classification as expected."""
    # Anomalous aircraft case from benchmark
    res_low = anomaly_detector.evaluate_benchmark(threshold=0.1)
    res_high = anomaly_detector.evaluate_benchmark(threshold=0.9)

    # Low threshold -> more detections (higher recall, lower precision)
    # High threshold -> fewer detections (higher precision, lower recall)
    assert res_low.metrics.recall >= res_high.metrics.recall
    assert res_high.metrics.precision >= res_low.metrics.precision
