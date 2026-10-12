"""Tests for action receipts and deterministic macro synthesis (Issue #824)."""
from app.models.schemas import ActionItem, ActionReceiptCreate, MacroConfirmRequest
from app.services.macro_engine import macro_engine


def test_action_receipts_and_candidate_detection(db_session):
    """Frequent repeated action sequences across sessions must be mined into candidates."""
    # Simulate repeated sequence: toggle_layer -> fly_to_bookmark across 3 sessions
    for session_idx in range(3):
        sid = f"session-{session_idx}"
        macro_engine.record_receipt(
            db_session,
            ActionReceiptCreate(
                session_id=sid,
                context_fingerprint="tactical-hud",
                action_name="toggle_layer",
                args={"layer": "satellites"},
                result_status="success",
                duration_ms=10.0,
            ),
            user_id="analyst-1",
        )
        macro_engine.record_receipt(
            db_session,
            ActionReceiptCreate(
                session_id=sid,
                context_fingerprint="tactical-hud",
                action_name="fly_to_bookmark",
                args={"name": "Austin Hub"},
                result_status="success",
                duration_ms=20.0,
            ),
            user_id="analyst-1",
        )

    candidates = macro_engine.detect_candidates(db_session, min_support=2)
    assert len(candidates) >= 1
    top = candidates[0]
    assert top.frequency_count >= 2
    assert top.verified_success_rate == 1.0
    assert len(top.actions) >= 2


def test_macro_confirmation_and_execution(db_session):
    """User confirmed macro must execute deterministically."""
    macro = macro_engine.confirm_macro(
        db_session,
        MacroConfirmRequest(
            name="Inspect Austin Satellites",
            description="Toggle satellites and focus",
            trigger_context="tactical-hud",
            actions=[
                ActionItem(name="toggle_layer", args={"layer": "satellites"}),
                ActionItem(name="fly_to_bookmark", args={"name": "Austin"}),
            ],
        ),
    )
    assert macro.status == "active"

    # Execute macro
    exec_res = macro_engine.execute_macro(db_session, macro.id)
    assert exec_res.success is True
    assert exec_res.executed_actions == 2
    assert exec_res.demoted is False


def test_macro_drift_demotion(db_session):
    """Macro with unrecognized or invalid action schema must be automatically demoted."""
    macro = macro_engine.confirm_macro(
        db_session,
        MacroConfirmRequest(
            name="Drift Test Macro",
            description="Contains invalid action",
            trigger_context="tactical-hud",
            actions=[
                ActionItem(name="non_existent_deprecated_action", args={}),
            ],
        ),
    )

    exec_res = macro_engine.execute_macro(db_session, macro.id)
    assert exec_res.success is False
    assert exec_res.demoted is True
    assert "invalid; macro demoted" in exec_res.demotion_reason
