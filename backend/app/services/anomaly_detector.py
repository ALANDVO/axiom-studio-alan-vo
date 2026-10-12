"""Machine Learning trajectory anomaly detection engine and evaluation benchmark."""
import datetime
import math
import time
from typing import Any, Dict, List, Tuple
import numpy as np
from app.models.schemas import BenchmarkMetric, MLBenchmarkResponse

DOMAIN_PROFILES = {
    "satellite": {"v": (7600.0, 150.0), "a": (550000.0, 150000.0), "c": (0.05, 0.02), "cl": (0.0, 5.0)},
    "aircraft": {"v": (240.0, 35.0), "a": (10500.0, 1500.0), "c": (0.5, 0.4), "cl": (0.0, 8.0)},
    "rf_station": {"v": (0.0, 0.1), "a": (100.0, 50.0), "c": (0.0, 0.01), "cl": (0.0, 0.01)},
    "camera": {"v": (0.0, 0.0), "a": (20.0, 10.0), "c": (0.0, 0.0), "cl": (0.0, 0.0)},
}

BENCHMARK_DATASET: List[Dict[str, Any]] = [
    {"id": "nom-sat-1", "type": "satellite", "vel": 7670.0, "alt": 420000.0, "climb": 0.2, "course_dev": 0.03, "label": 0, "desc": "ISS regular LEO orbit"},
    {"id": "nom-sat-2", "type": "satellite", "vel": 7450.0, "alt": 786000.0, "climb": -0.1, "course_dev": 0.04, "label": 0, "desc": "Sentinel-2A polar orbit"},
    {"id": "nom-sat-3", "type": "satellite", "vel": 7520.0, "alt": 550000.0, "climb": 0.0, "course_dev": 0.02, "label": 0, "desc": "Starlink constellation pass"},
    {"id": "anom-sat-1", "type": "satellite", "vel": 8800.0, "alt": 300000.0, "climb": -120.0, "course_dev": 18.5, "label": 1, "desc": "Uncoordinated deorbit burn"},
    {"id": "anom-sat-2", "type": "satellite", "vel": 6200.0, "alt": 550000.0, "climb": 85.0, "course_dev": 24.0, "label": 1, "desc": "Non-Keplerian cross-plane evasion"},
    {"id": "nom-air-1", "type": "aircraft", "vel": 250.0, "alt": 11000.0, "climb": 1.5, "course_dev": 0.3, "label": 0, "desc": "Boeing 777 cruise flight"},
    {"id": "nom-air-2", "type": "aircraft", "vel": 240.0, "alt": 10500.0, "climb": -2.0, "course_dev": 0.4, "label": 0, "desc": "Airbus A350 level flight"},
    {"id": "nom-air-3", "type": "aircraft", "vel": 210.0, "alt": 9000.0, "climb": 8.0, "course_dev": 0.6, "label": 0, "desc": "Standard terminal climb"},
    {"id": "nom-air-4", "type": "aircraft", "vel": 180.0, "alt": 3000.0, "climb": -7.5, "course_dev": 0.8, "label": 0, "desc": "Approach descent"},
    {"id": "nom-air-5", "type": "aircraft", "vel": 260.0, "alt": 11800.0, "climb": 0.0, "course_dev": 0.2, "label": 0, "desc": "Boeing 787 polar route"},
    {"id": "anom-air-1", "type": "aircraft", "vel": 420.0, "alt": 4000.0, "climb": -65.0, "course_dev": 48.0, "label": 1, "desc": "Emergency dive and rapid turn"},
    {"id": "anom-air-2", "type": "aircraft", "vel": 580.0, "alt": 9000.0, "climb": 45.0, "course_dev": 75.0, "label": 1, "desc": "Supersonic flight envelope breach"},
    {"id": "anom-air-3", "type": "aircraft", "vel": 40.0, "alt": 11000.0, "climb": -95.0, "course_dev": 62.0, "label": 1, "desc": "High altitude aerodynamic stall"},
    {"id": "anom-air-4", "type": "aircraft", "vel": 235.0, "alt": 10500.0, "climb": 0.0, "course_dev": 115.0, "label": 1, "desc": "ADS-B heading spoofing divergence"},
    {"id": "nom-rf-1", "type": "rf_station", "vel": 0.0, "alt": 120.0, "climb": 0.0, "course_dev": 0.0, "label": 0, "desc": "Fixed SondeHub receiver"},
    {"id": "nom-rf-2", "type": "rf_station", "vel": 0.0, "alt": 85.0, "climb": 0.0, "course_dev": 0.0, "label": 0, "desc": "Meshtastic repeater node"},
    {"id": "anom-rf-1", "type": "rf_station", "vel": 180.0, "alt": 120.0, "climb": 0.0, "course_dev": 80.0, "label": 1, "desc": "Fixed beacon broadcasting high velocity"},
    {"id": "nom-cam-1", "type": "camera", "vel": 0.0, "alt": 18.0, "climb": 0.0, "course_dev": 0.0, "label": 0, "desc": "Austin I-35 verified CCTV"},
    {"id": "nom-cam-2", "type": "camera", "vel": 0.0, "alt": 25.0, "climb": 0.0, "course_dev": 0.0, "label": 0, "desc": "London Trafalgar Square stream"},
    {"id": "anom-cam-1", "type": "camera", "vel": 15.0, "alt": 250.0, "climb": 12.0, "course_dev": 45.0, "label": 1, "desc": "Tampered camera coordinate erratic shift"},
]


class AnomalyDetector:
    def __init__(self) -> None:
        self.dataset = BENCHMARK_DATASET

    def score_kinematics(self, entity_type: str, vel_mps: float, alt_m: float, climb_mps: float, course_dev_deg: float) -> Tuple[float, List[str]]:
        prof = DOMAIN_PROFILES.get(entity_type, DOMAIN_PROFILES["aircraft"])
        zv = abs(vel_mps - prof["v"][0]) / max(prof["v"][1], 1e-4)
        za = abs(alt_m - prof["a"][0]) / max(prof["a"][1], 1e-4)
        zc = abs(course_dev_deg - prof["c"][0]) / max(prof["c"][1], 1e-4)
        zcl = abs(climb_mps - prof["cl"][0]) / max(prof["cl"][1], 1e-4)

        weights = np.array([1.5, 0.8, 1.8, 1.2])
        feats = np.array([zv, za, zc, zcl])
        dist = float(np.sqrt(np.sum((feats * weights) ** 2)) / np.sum(weights))

        score = max(0.0, min(1.0, 1.0 / (1.0 + math.exp(-1.4 * (dist - 2.8)))))
        patterns = []
        if zv > 3.0: patterns.append(f"Velocity divergence (Z={zv:.1f})")
        if za > 3.0: patterns.append(f"Altitude anomaly (Z={za:.1f})")
        if zc > 3.0: patterns.append(f"Course deviation (Z={zc:.1f})")
        if zcl > 3.0: patterns.append(f"Vertical rate spike (Z={zcl:.1f})")
        return round(score, 4), patterns

    def evaluate_benchmark(self, threshold: float = 0.65) -> MLBenchmarkResponse:
        y_true, y_pred, y_scores, latencies, failure_cases = [], [], [], [], []
        tp = fp = tn = fn = 0

        for item in self.dataset:
            t0 = time.perf_counter()
            score, pats = self.score_kinematics(item["type"], item["vel"], item["alt"], item["climb"], item["course_dev"])
            latencies.append((time.perf_counter() - t0) * 1000.0)

            gt = item["label"]
            pred = 1 if score >= threshold else 0
            y_true.append(gt)
            y_pred.append(pred)
            y_scores.append(score)

            if pred == 1 and gt == 1: tp += 1
            elif pred == 1 and gt == 0:
                fp += 1
                failure_cases.append({"id": item["id"], "description": item["desc"], "error_type": "False Positive", "score": score, "threshold": threshold, "patterns": pats})
            elif pred == 0 and gt == 0: tn += 1
            else:
                fn += 1
                failure_cases.append({"id": item["id"], "description": item["desc"], "error_type": "False Negative", "score": score, "threshold": threshold, "patterns": pats})

        tot = len(y_true)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) else 0.0
        acc = (tp + tn) / tot if tot else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0

        pos = [y_scores[i] for i in range(tot) if y_true[i] == 1]
        neg = [y_scores[i] for i in range(tot) if y_true[i] == 0]
        conc = sum(1.0 if p > n else (0.5 if p == n else 0.0) for p in pos for n in neg)
        auc = conc / (len(pos) * len(neg)) if pos and neg else 0.5

        return MLBenchmarkResponse(
            dataset_name="Axiom Geospatial Trajectory & Sensor Anomaly Dataset v1.0",
            dataset_size=tot,
            evaluated_at=datetime.datetime.now(datetime.timezone.utc),
            baseline_algorithm="Static Kinematic Limit Rule-based Heuristic",
            model_algorithm="Multi-Feature Calibrated Kinematic Z-Score Distance Classifier",
            metrics=BenchmarkMetric(
                precision=round(prec, 4), recall=round(rec, 4), f1_score=round(f1, 4),
                accuracy=round(acc, 4), false_positive_rate=round(fpr, 4), roc_auc=round(auc, 4),
                evaluation_samples=tot, mean_inference_latency_ms=round(float(np.mean(latencies)), 3)
            ),
            confusion_matrix={"true_positives": tp, "false_positives": fp, "true_negatives": tn, "false_negatives": fn},
            failure_cases=failure_cases,
        )


anomaly_detector = AnomalyDetector()
