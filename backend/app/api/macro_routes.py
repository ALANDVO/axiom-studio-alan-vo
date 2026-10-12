"""Action receipts and deterministic macro synthesis endpoints (Issue #824)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.audit import log_action
from app.core.security import AuthUser, get_current_user, require_roles
from app.models.database import get_db
from app.models.schemas import (
    ActionReceiptCreate,
    ActionReceiptResponse,
    MacroCandidate,
    MacroConfirmRequest,
    MacroExecuteResponse,
    WorkflowMacroResponse,
)
from app.services.macro_engine import macro_engine

router = APIRouter(prefix="/api/macros", tags=["Workflow Macros"])


@router.post("/receipts", response_model=ActionReceiptResponse, status_code=status.HTTP_201_CREATED)
def record_action_receipt(
    payload: ActionReceiptCreate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> ActionReceiptResponse:
    """Record plain-data episode action receipt for repeated workflow detection (Slice 1)."""
    return macro_engine.record_receipt(db, payload, user_id=user.username)


@router.get("/candidates", response_model=List[MacroCandidate])
def detect_workflow_candidates(
    min_support: int = Query(2, ge=1, le=50),
    min_success_rate: float = Query(0.8, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> List[MacroCandidate]:
    """Mine deterministic repeated action sequences across bounded analyst sessions (Slice 2)."""
    return macro_engine.detect_candidates(
        db, min_support=min_support, min_success_rate=min_success_rate
    )


@router.post("/confirm", response_model=WorkflowMacroResponse, status_code=status.HTTP_201_CREATED)
def confirm_macro_shortcut(
    payload: MacroConfirmRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["analyst", "operator", "admin"])),
) -> WorkflowMacroResponse:
    """User confirms a detected routine candidate into an executable macro shortcut (Slice 3)."""
    macro = macro_engine.confirm_macro(db, payload)
    log_action(
        db,
        user_id=user.username,
        action="confirm_macro",
        resource=f"macro:{macro.id}",
        details={"name": macro.name, "actions_count": len(macro.actions)},
        role=user.roles[0] if user.roles else "unknown",
    )
    return macro


@router.get("", response_model=List[WorkflowMacroResponse])
def list_macros(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> List[WorkflowMacroResponse]:
    """List all registered and compiled workflow macros."""
    return macro_engine.list_macros(db)


@router.post("/{macro_id}/execute", response_model=MacroExecuteResponse)
def execute_macro(
    macro_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["analyst", "operator", "admin"])),
) -> MacroExecuteResponse:
    """Execute stored typed sequence with verified result checks and drift demotion (Slice 4 & 5)."""
    result = macro_engine.execute_macro(db, macro_id)
    log_action(
        db,
        user_id=user.username,
        action="execute_macro",
        resource=f"macro:{macro_id}",
        details={"success": result.success, "demoted": result.demoted},
        role=user.roles[0] if user.roles else "unknown",
    )
    return result


@router.post("/{macro_id}/demote", response_model=WorkflowMacroResponse)
def demote_macro(
    macro_id: str,
    reason: str = Query("Manual analyst demotion or drift"),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["admin"])),
) -> WorkflowMacroResponse:
    """Demote a macro when schema or environment preconditions drift (Slice 5)."""
    macro = macro_engine.demote_macro(db, macro_id, reason=reason)
    if not macro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Macro not found.")
    log_action(
        db,
        user_id=user.username,
        action="demote_macro",
        resource=f"macro:{macro_id}",
        details={"reason": reason},
        role=user.roles[0] if user.roles else "unknown",
    )
    return macro
