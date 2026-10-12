"""Deterministic workflow macro synthesis and action receipt runner (Issue #824)."""
import datetime
import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.db_models import ActionReceiptRecord, WorkflowMacroRecord
from app.models.schemas import (
    ActionItem,
    ActionReceiptCreate,
    ActionReceiptResponse,
    MacroCandidate,
    MacroConfirmRequest,
    MacroExecuteResponse,
    WorkflowMacroResponse,
)


class MacroEngine:
    VALID_ACTIONS = {
        "select_entity", "toggle_layer", "fly_to_bookmark",
        "inspect_camera_feed", "filter_altitude", "run_anomaly_scan",
    }

    def record_receipt(self, db: Session, req: ActionReceiptCreate, user_id: str) -> ActionReceiptResponse:
        rec = ActionReceiptRecord(
            session_id=req.session_id, context_fingerprint=req.context_fingerprint,
            action_name=req.action_name, args_json=json.dumps(req.args),
            result_status=req.result_status, duration_ms=req.duration_ms, user_id=user_id,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        args_dict = json.loads(rec.args_json) if rec.args_json else {}
        return ActionReceiptResponse(
            id=rec.id, session_id=rec.session_id, context_fingerprint=rec.context_fingerprint,
            action_name=rec.action_name, args=args_dict, result_status=rec.result_status,
            duration_ms=rec.duration_ms, executed_at=rec.executed_at,
        )

    def detect_candidates(self, db: Session, min_support: int = 2, min_success_rate: float = 0.8) -> List[MacroCandidate]:
        receipts = db.query(ActionReceiptRecord).order_by(ActionReceiptRecord.session_id, ActionReceiptRecord.executed_at).all()
        episodes: Dict[str, List[ActionReceiptRecord]] = {}
        for r in receipts:
            key = f"{r.session_id}:{r.context_fingerprint}"
            episodes.setdefault(key, []).append(r)

        ngram_stats: Dict[Tuple[str, ...], Dict[str, Any]] = {}
        for key, recs in episodes.items():
            context_fp = key.split(":", 1)[1]
            n = len(recs)
            if n < 2: continue
            for length in (2, 3):
                for i in range(n - length + 1):
                    window = recs[i:i + length]
                    seq_key = tuple(f"{w.action_name}:{w.args_json}" for w in window)
                    if seq_key not in ngram_stats:
                        ngram_stats[seq_key] = {
                            "context_fp": context_fp,
                            "items": [ActionItem(name=w.action_name, args=json.loads(w.args_json) if w.args_json else {}) for w in window],
                            "count": 0, "success_count": 0,
                        }
                    ngram_stats[seq_key]["count"] += 1
                    if all(w.result_status == "success" for w in window):
                        ngram_stats[seq_key]["success_count"] += 1

        candidates = []
        for stat in ngram_stats.values():
            if stat["count"] >= min_support:
                rate = stat["success_count"] / float(stat["count"])
                if rate >= min_success_rate:
                    names = " -> ".join(item.name for item in stat["items"])
                    candidates.append(MacroCandidate(
                        context_fingerprint=stat["context_fp"], actions=stat["items"],
                        frequency_count=stat["count"], verified_success_rate=round(rate, 2),
                        suggested_name=f"Workflow: {names}",
                    ))
        candidates.sort(key=lambda c: c.frequency_count, reverse=True)
        return candidates

    def confirm_macro(self, db: Session, req: MacroConfirmRequest) -> WorkflowMacroResponse:
        actions_json = json.dumps([a.model_dump() for a in req.actions])
        now = datetime.datetime.now(datetime.timezone.utc)
        existing = db.query(WorkflowMacroRecord).filter(WorkflowMacroRecord.name == req.name).first()
        if existing:
            existing.actions_json = actions_json
            existing.trigger_context = req.trigger_context
            existing.description = req.description
            existing.status = "active"
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
            return self._to_res(existing)

        macro = WorkflowMacroRecord(
            name=req.name, description=req.description, trigger_context=req.trigger_context,
            actions_json=actions_json, support_count=1, verified_success_rate=1.0,
            status="active", created_at=now, updated_at=now,
        )
        db.add(macro)
        db.commit()
        db.refresh(macro)
        return self._to_res(macro)

    def list_macros(self, db: Session) -> List[WorkflowMacroResponse]:
        return [self._to_res(r) for r in db.query(WorkflowMacroRecord).order_by(WorkflowMacroRecord.created_at.desc()).all()]

    def execute_macro(self, db: Session, macro_id: str) -> MacroExecuteResponse:
        macro = db.query(WorkflowMacroRecord).filter(WorkflowMacroRecord.id == macro_id).first()
        if not macro or macro.status == "demoted":
            return MacroExecuteResponse(
                macro_id=macro_id, executed_actions=0, success=False, results=[], demoted=True,
                demotion_reason="Macro record demoted or not found",
            )
        actions = json.loads(macro.actions_json) if macro.actions_json else []
        results = []
        for act in actions:
            name = act.get("name")
            if name not in self.VALID_ACTIONS:
                macro.status = "demoted"
                db.commit()
                return MacroExecuteResponse(
                    macro_id=macro.id, executed_actions=len(results), success=False, results=results,
                    demoted=True, demotion_reason=f"Action '{name}' invalid; macro demoted.",
                )
            results.append({"action": name, "status": "completed", "args": act.get("args", {})})

        macro.support_count += 1
        macro.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        return MacroExecuteResponse(macro_id=macro.id, executed_actions=len(results), success=True, results=results, demoted=False)

    def demote_macro(self, db: Session, macro_id: str, reason: str) -> Optional[WorkflowMacroResponse]:
        macro = db.query(WorkflowMacroRecord).filter(WorkflowMacroRecord.id == macro_id).first()
        if not macro: return None
        macro.status = "demoted"
        macro.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(macro)
        return self._to_res(macro)

    def _to_res(self, r: WorkflowMacroRecord) -> WorkflowMacroResponse:
        try: items = [ActionItem(**i) for i in json.loads(r.actions_json)]
        except Exception: items = []
        return WorkflowMacroResponse(
            id=r.id, name=r.name, description=r.description or "",
            trigger_context=r.trigger_context, actions=items,
            support_count=r.support_count or 1, verified_success_rate=r.verified_success_rate or 1.0,
            status=r.status or "active", created_at=r.created_at,
        )


macro_engine = MacroEngine()
