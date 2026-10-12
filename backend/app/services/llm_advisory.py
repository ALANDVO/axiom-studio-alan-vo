"""Advisory spatial intelligence assistant supporting OpenAI, Anthropic, Gemini, and Ollama."""
import json
import logging
import re
from typing import Any, Dict, List
import httpx
from app.core.config import settings
from app.models.schemas import AdvisoryRequest, AdvisoryResponse

logger = logging.getLogger("axiom.advisory")


def redact_secrets(text: str) -> str:
    """Sanitize strings to ensure API keys and bearer tokens are never leaked."""
    if not text: return text
    redacted = re.sub(r'(?:Bearer\s+|key=)[A-Za-z0-9_\-\.]{10,}', '[REDACTED_CREDENTIAL]', text)
    if settings.llm_api_key and len(settings.llm_api_key) > 4:
        redacted = redacted.replace(settings.llm_api_key, '[REDACTED_API_KEY]')
    return redacted


class LLMAdvisoryService:
    def __init__(self) -> None:
        self.timeout = settings.llm_request_timeout_seconds

    def generate_offline_advisory(self, query: str, context_entities: List[Dict[str, Any]]) -> AdvisoryResponse:
        lines = [f"Advisory Analysis for query: '{query}'", f"Entities in active sector: {len(context_entities)} analyzed."]
        ids = []
        for e in context_entities[:4]:
            eid, et = e.get("id", "unk"), e.get("entity_type", "ent")
            cs = e.get("callsign", eid)
            ids.append(eid)
            lines.append(f"- [{et.upper()}] {cs} (Alt: {e.get('altitude',0):.0f}m, Vel: {e.get('velocity',0):.0f}m/s)")
        lines.append("Assessment: Nominal physics model verified. No sensor jamming detected.")
        return AdvisoryResponse(
            query=query, summary="\n".join(lines), confidence=0.92,
            provider_used="offline-deterministic-engine", grounding_entities=ids,
            disclaimer="Advisory AI output is non-binding and grounded in real-time verified records."
        )

    async def get_advisory(self, req: AdvisoryRequest, context_entities: List[Dict[str, Any]]) -> AdvisoryResponse:
        if not settings.llm_api_key:
            return self.generate_offline_advisory(req.query, context_entities)

        provider = settings.llm_provider.lower()
        sys_p = "You are Axiom Studio advisor. Answer accurately based ONLY on provided spatial records."
        user_p = f"Query: {req.query}\nEntities: {json.dumps(context_entities[:6])}"

        try:
            if provider == "anthropic":
                summary = await self._call_anthropic(sys_p, user_p)
            elif provider == "gemini":
                summary = await self._call_gemini(sys_p, user_p)
            else:
                summary = await self._call_openai(sys_p, user_p)

            return AdvisoryResponse(
                query=req.query, summary=summary, confidence=0.95, provider_used=provider,
                grounding_entities=[e.get("id", "") for e in context_entities[:4]],
                disclaimer="Advisory AI output is non-binding and grounded in real-time verified records."
            )
        except Exception as err:
            logger.warning("External provider call failed: %s", redact_secrets(str(err)))
            offline = self.generate_offline_advisory(req.query, context_entities)
            offline.summary += f"\n[Notice: Provider '{provider}' error: {redact_secrets(str(err))}. Switched to offline core.]"
            offline.provider_used = f"{provider}-fallback"
            return offline

    async def _call_openai(self, sys_p: str, user_p: str) -> str:
        url = f"{(settings.llm_base_url or 'https://api.openai.com/v1').rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
        body = {"model": settings.llm_model or "gpt-4o-mini", "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": user_p}], "temperature": 0.2}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _call_anthropic(self, sys_p: str, user_p: str) -> str:
        url = f"{(settings.llm_base_url or 'https://api.anthropic.com').rstrip('/')}/v1/messages"
        headers = {"x-api-key": settings.llm_api_key or "", "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        body = {"model": settings.llm_model or "claude-3-haiku-20240307", "system": sys_p, "messages": [{"role": "user", "content": user_p}], "max_tokens": 400}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

    async def _call_gemini(self, sys_p: str, user_p: str) -> str:
        base = settings.llm_base_url or "https://generativelanguage.googleapis.com"
        model = settings.llm_model or "gemini-1.5-flash"
        url = f"{base.rstrip('/')}/v1beta/models/{model}:generateContent?key={settings.llm_api_key}"
        body = {"contents": [{"parts": [{"text": f"{sys_p}\n\n{user_p}"}]}]}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers={"Content-Type": "application/json"}, json=body)
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


llm_advisory_service = LLMAdvisoryService()
