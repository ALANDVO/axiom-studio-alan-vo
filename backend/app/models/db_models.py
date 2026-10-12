"""SQLAlchemy ORM models for spatial entities, bookmarks, macros, and audit logs."""
import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.models.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class BookmarkRecord(Base):
    """Saved / favourite geospatial locations with restored camera pose."""
    __tablename__ = "bookmarks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, default=1000.0)
    heading = Column(Float, default=0.0)
    pitch = Column(Float, default=-45.0)
    active_layers = Column(Text, default="[]")
    created_by = Column(String(100), default="anonymous")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class SpatialEntityRecord(Base):
    """Persistent catalog of tracked satellites, aircraft, RF towers, and camera sensors."""
    __tablename__ = "spatial_entities"

    id = Column(String(64), primary_key=True)
    entity_type = Column(String(32), nullable=False, index=True)  # satellite, aircraft, rf_station, camera
    callsign = Column(String(64), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, default=0.0)
    velocity = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    status = Column(String(32), default="active")
    metadata_json = Column(Text, default="{}")
    last_seen = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class ActionReceiptRecord(Base):
    """Bounded plain-data episode action receipt format (Issue #824)."""
    __tablename__ = "action_receipts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), nullable=False, index=True)
    context_fingerprint = Column(String(128), nullable=False, index=True)
    action_name = Column(String(64), nullable=False, index=True)
    args_json = Column(Text, nullable=False, default="{}")
    result_status = Column(String(32), nullable=False, default="success")  # success, error, undone
    duration_ms = Column(Float, default=0.0)
    user_id = Column(String(100), default="anonymous")
    executed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class WorkflowMacroRecord(Base):
    """Deterministic compiled workflow shortcut synthesized from repeated verified actions."""
    __tablename__ = "workflow_macros"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), default="")
    trigger_context = Column(String(128), nullable=False)
    actions_json = Column(Text, nullable=False)  # JSON array of typed actions
    support_count = Column(Integer, default=1)
    verified_success_rate = Column(Float, default=1.0)
    status = Column(String(20), default="active")  # active, demoted
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class AuditLogRecord(Base):
    """Audit log entry for compliance and security traceability."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    user_id = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target_resource = Column(String(200), nullable=False)
    details_json = Column(Text, default="{}")
