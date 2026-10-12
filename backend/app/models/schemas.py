"""Pydantic request and response schemas for all Axiom Studio endpoints."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Authentication schemas
class DemoLoginRequest(BaseModel):
    role: str = Field(default="analyst", description="Role to assume: viewer, analyst, admin")
    username: str = Field(default="demo-analyst")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    roles: List[str]
    username: str
    is_demo: bool = False


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str]
    is_demo: bool


# Spatial & Telemetry schemas
class CameraPose(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude: float = Field(default=1000.0, ge=1.0)
    heading: float = Field(default=0.0, ge=0.0, le=360.0)
    pitch: float = Field(default=-45.0, ge=-90.0, le=90.0)


class BookmarkCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude: float = Field(default=1000.0, ge=1.0)
    heading: float = Field(default=0.0, ge=0.0, le=360.0)
    pitch: float = Field(default=-45.0, ge=-90.0, le=90.0)
    active_layers: List[str] = Field(default_factory=list)


class BookmarkResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    altitude: float
    heading: float
    pitch: float
    active_layers: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class ViewportQuery(BaseModel):
    min_lat: float = Field(-90.0, ge=-90.0, le=90.0)
    max_lat: float = Field(90.0, ge=-90.0, le=90.0)
    min_lon: float = Field(-180.0, ge=-180.0, le=180.0)
    max_lon: float = Field(180.0, ge=-180.0, le=180.0)
    layers: Optional[List[str]] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SpatialEntity(BaseModel):
    id: str
    entity_type: str  # satellite, aircraft, rf_station, camera
    callsign: str
    latitude: float
    longitude: float
    altitude: float
    velocity: float
    heading: float
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_seen: datetime


class CameraFeed(BaseModel):
    id: str
    name: str
    city: str
    region: str
    latitude: float
    longitude: float
    stream_url: str
    attribution: str
    is_healthy: bool
    fps: float
    last_poll_status: str
    fov_degrees: float = 60.0


# Machine Learning & Anomaly schemas
class TrajectoryPoint(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    velocity: float
    timestamp_utc: float
    heading: Optional[float] = 0.0


class AnomalyScore(BaseModel):
    entity_id: str
    entity_type: str
    anomaly_score: float  # 0.0 to 1.0 (calibrated)
    is_anomalous: bool
    confidence: float
    detected_patterns: List[str]
    explanation: str


class AnomalyScanRequest(BaseModel):
    entity_ids: Optional[List[str]] = None
    threshold: float = Field(default=0.65, ge=0.0, le=1.0)


class BenchmarkMetric(BaseModel):
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    false_positive_rate: float
    roc_auc: float
    evaluation_samples: int
    mean_inference_latency_ms: float


class MLBenchmarkResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    dataset_name: str
    dataset_size: int
    evaluated_at: datetime
    baseline_algorithm: str
    model_algorithm: str
    metrics: BenchmarkMetric
    confusion_matrix: Dict[str, int]
    failure_cases: List[Dict[str, Any]]


# Workflow Macros schemas (Issue #824)
class ActionItem(BaseModel):
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)


class ActionReceiptCreate(BaseModel):
    session_id: str
    context_fingerprint: str
    action_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    result_status: str = "success"
    duration_ms: float = 0.0


class ActionReceiptResponse(BaseModel):
    id: str
    session_id: str
    context_fingerprint: str
    action_name: str
    args: Dict[str, Any]
    result_status: str
    duration_ms: float
    executed_at: datetime


class MacroCandidate(BaseModel):
    context_fingerprint: str
    actions: List[ActionItem]
    frequency_count: int
    verified_success_rate: float
    suggested_name: str


class MacroConfirmRequest(BaseModel):
    name: str
    description: str = ""
    trigger_context: str
    actions: List[ActionItem]


class WorkflowMacroResponse(BaseModel):
    id: str
    name: str
    description: str
    trigger_context: str
    actions: List[ActionItem]
    support_count: int
    verified_success_rate: float
    status: str
    created_at: datetime


class MacroExecuteResponse(BaseModel):
    macro_id: str
    executed_actions: int
    success: bool
    results: List[Dict[str, Any]]
    demoted: bool = False
    demotion_reason: Optional[str] = None


# Advisory Assistant schemas
class AdvisoryRequest(BaseModel):
    query: str
    target_entity_id: Optional[str] = None
    include_sensor_context: bool = True


class AdvisoryResponse(BaseModel):
    query: str
    summary: str
    confidence: float
    provider_used: str
    grounding_entities: List[str]
    disclaimer: str = "Advisory AI output is non-binding and grounded in real-time verified records."
