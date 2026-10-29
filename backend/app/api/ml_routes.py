"""Machine Learning anomaly detection and benchmark evaluation endpoints."""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.audit import log_action
from app.core.security import AuthUser, get_current_user, require_roles
from app.models.database import get_db
from app.models.schemas import (
    AdvisoryRequest,
    AdvisoryResponse,
    AnomalyScanRequest,
    AnomalyScore,
    MLBenchmarkResponse,
)
from app.services.anomaly_detector import anomaly_detector
from app.services.llm_advisory import llm_advisory_service
from app.services.spatial_engine import spatial_engine

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


@router.post("/detect-anomalies", response_model=List[AnomalyScore])
def detect_trajectory_anomalies(
    payload: AnomalyScanRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["analyst", "operator", "admin"])),
) -> List[AnomalyScore]:
    """Execute kinematic anomaly detector across live orbital, aerial, and ground tracks."""
    entities = spatial_engine.get_live_entities(limit=200)
    scores: List[AnomalyScore] = []

    target_ids = set(payload.entity_ids) if payload.entity_ids else None

    for e in entities:
        if target_ids and e.id not in target_ids:
            continue

        # Stationary entities (cameras, rf_stations) have zero climb and course deviation by definition
        if e.entity_type in ("camera", "rf_station"):
            climb_mps = 0.0
            course_dev_deg = 0.0
        else:
            # For moving entities, use small defaults (real-time telemetry would provide actuals)
            climb_mps = 0.0
            course_dev_deg = 0.1

        score_val, patterns = anomaly_detector.score_kinematics(
            entity_type=e.entity_type,
            vel_mps=e.velocity,
            alt_m=e.altitude,
            climb_mps=climb_mps,
            course_dev_deg=course_dev_deg,
        )

        is_anom = score_val >= payload.threshold
        explanation = (
            f"Anomalous divergence detected: {', '.join(patterns)}"
            if is_anom and patterns
            else "Kinematic state conforms to nominal domain envelope."
        )

        scores.append(
            AnomalyScore(
                entity_id=e.id,
                entity_type=e.entity_type,
                anomaly_score=score_val,
                is_anomalous=is_anom,
                confidence=round(abs(score_val - 0.5) * 2.0, 2),
                detected_patterns=patterns,
                explanation=explanation,
            )
        )

    log_action(
        db,
        user_id=user.username,
        action="run_anomaly_scan",
        resource="spatial_entities",
        details={"scanned": len(scores), "anomalies_flagged": sum(1 for s in scores if s.is_anomalous)},
        role=user.roles[0] if user.roles else "unknown",
    )

    return scores


@router.get("/benchmark", response_model=MLBenchmarkResponse)
def get_ml_benchmark(
    threshold: float = Query(0.65, ge=0.1, le=0.99),
    user: AuthUser = Depends(get_current_user),
) -> MLBenchmarkResponse:
    """Run evaluation benchmark against ground-truth dataset and compute precision, recall, F1, and ROC-AUC."""
    return anomaly_detector.evaluate_benchmark(threshold=threshold)


@router.post("/advisory", response_model=AdvisoryResponse)
async def request_advisory_analysis(
    req: AdvisoryRequest,
    user: AuthUser = Depends(get_current_user),
) -> AdvisoryResponse:
    """Produce grounded advisory spatial intelligence assessment (deterministic offline fallback if LLM key unset)."""
    entities = spatial_engine.get_live_entities(limit=20)
    context_data = [e.model_dump() for e in entities]
    if not req.include_sensor_context:
        context_data = []
    elif req.target_entity_id:
        context_data = [e for e in context_data if e.get("id") == req.target_entity_id]
    return await llm_advisory_service.get_advisory(req, context_data)
