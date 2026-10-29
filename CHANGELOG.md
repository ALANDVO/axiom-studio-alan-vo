# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-10-17

### Fixed
- ML advisory endpoint now honors `target_entity_id` to filter context to a single selected telemetry contact, and respects `include_sensor_context=false` to omit entity context entirely. Frontend client and dashboard pass the currently selected entity ID to the advisory assistant.

## [1.0.0] - 2026-10-12

### Added
- Initial production release of Axiom Studio.
- Multi-source spatial intelligence engine supporting orbital satellites, aerial flights, RF transponders, and verified public camera feeds with health polling.
- Saved and favourite locations manager with persistent camera poses (lat, lon, altitude, heading, pitch) and viewport restoration.
- Trajectory anomaly detection engine combining deterministic heuristics and ML scoring for orbital drift and transponder anomalies.
- AI/ML evaluation benchmark suite with reproducible CLI and labeled ground-truth dataset.
- Deterministic analyst workflow macro synthesizer supporting plain-data action receipts, candidate detection, and drift demotion.
- Secure Keycloak OIDC authentication with PKCE, SAML brokering architecture, and role-based access control (viewer, analyst, admin).
- Offline-first deterministic core with optional advisory LLM integration supporting OpenAI, Anthropic, Gemini, and Ollama.
