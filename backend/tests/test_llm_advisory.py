"""Tests for advisory LLM integration with mocked network and error redaction."""
import pytest
from app.core.config import settings
from app.models.schemas import AdvisoryRequest
from app.services.llm_advisory import llm_advisory_service, redact_secrets


def test_offline_deterministic_advisory():
    """When LLM_API_KEY is unset, advisory engine must produce deterministic grounded summary."""
    entities = [
        {"id": "sat-iss", "entity_type": "satellite", "callsign": "ISS", "altitude": 420000.0, "velocity": 7660.0},
        {"id": "air-ua1", "entity_type": "aircraft", "callsign": "UAL1", "altitude": 10000.0, "velocity": 240.0},
    ]
    res = llm_advisory_service.generate_offline_advisory("Identify high-altitude contacts", entities)
    assert res.provider_used == "offline-deterministic-engine"
    assert "ISS" in res.summary
    assert "UAL1" in res.summary
    assert "sat-iss" in res.grounding_entities
    assert res.confidence > 0.80


def test_secret_redaction_safeguard():
    """Ensure sensitive tokens and bearer credentials are sanitized from diagnostic strings."""
    # Generate synthetic key at runtime without literal pattern
    synthetic_key = "synthetic-provider-" + ("0" * 32)
    original_key = settings.llm_api_key
    try:
        settings.llm_api_key = synthetic_key
        raw_error = f"Connection failed with Bearer {synthetic_key} during handshake."
        redacted = redact_secrets(raw_error)
        assert synthetic_key not in redacted
        assert "[REDACTED" in redacted
    finally:
        settings.llm_api_key = original_key


@pytest.mark.asyncio
async def test_advisory_service_fallback_on_network_error(monkeypatch):
    """When external provider fails, advisory service must fall back cleanly without unhandled crash."""
    original_key = settings.llm_api_key
    synthetic_key = "test-provider-" + ("0" * 24)
    try:
        settings.llm_api_key = synthetic_key
        settings.llm_provider = "openai-compatible"

        async def mock_fail(*args, **kwargs):
            raise ConnectionError("Upstream provider network timeout")

        monkeypatch.setattr(llm_advisory_service, "_call_openai", mock_fail)

        req = AdvisoryRequest(query="Status of active airspace")
        res = await llm_advisory_service.get_advisory(req, [{"id": "air-test", "callsign": "TEST01"}])
        assert res.provider_used == "openai-compatible-fallback"
        assert "Switched to offline" in res.summary
    finally:
        settings.llm_api_key = original_key
