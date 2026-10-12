"""Audit log query endpoints for compliance and administrative inspection."""
import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.security import AuthUser, require_roles
from app.models.database import get_db
from app.models.db_models import AuditLogRecord

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    user_id: str
    role: str
    action: str
    target_resource: str
    details: Dict[str, Any]


@router.get("/logs", response_model=List[AuditLogEntry])
def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["admin"])),
) -> List[AuditLogEntry]:
    """Retrieve chronologically ordered audit logs (Admin privilege required)."""
    records = (
        db.query(AuditLogRecord)
        .order_by(AuditLogRecord.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    entries: List[AuditLogEntry] = []
    for r in records:
        details = {}
        try:
            details = json.loads(r.details_json) if r.details_json else {}
        except Exception:
            details = {}
        entries.append(
            AuditLogEntry(
                id=r.id,
                timestamp=r.timestamp.isoformat(),
                user_id=r.user_id,
                role=r.role,
                action=r.action,
                target_resource=r.target_resource,
                details=details,
            )
        )
    return entries
