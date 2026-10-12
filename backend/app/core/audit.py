"""Audit logging service for security compliance and mutation tracking."""
import datetime
import json
import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger("axiom.audit")


def log_action(
    db: Optional[Session],
    user_id: str,
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None,
    role: Optional[str] = None,
) -> None:
    """Record an audit trail event in logger and persistent database."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    details_payload = details or {}
    logger.info(
        "AUDIT: ts=%s user=%s action=%s resource=%s details=%s",
        now_utc.isoformat(),
        user_id,
        action,
        resource,
        json.dumps(details_payload),
    )

    if db is not None:
        try:
            from app.models.db_models import AuditLogRecord
            record = AuditLogRecord(
                timestamp=now_utc,
                user_id=user_id,
                role=role or "unknown",
                action=action,
                target_resource=resource,
                details_json=json.dumps(details_payload),
            )
            db.add(record)
            db.commit()
        except Exception as err:
            logger.error("Failed to commit audit record to database: %s", str(err))
            db.rollback()
