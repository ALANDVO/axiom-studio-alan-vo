# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

spatial-intel-platform

## Roadmap

### spatial-intel-platform — Multi-Source Spatial Intelligence and Telemetry Platform

Status: done

Acceptance:
- Ingests orbital satellite telemetry, aircraft positions, RF sensors, and public traffic camera feeds with health verification
- Provides viewport queries and camera state persistence for saved and favourite locations
- Executes trajectory anomaly detection with ground-truth ML benchmark evaluation
- Synthesizes verified analyst workflow macros with deterministic candidate detection and drift demotion
- Enforces OIDC/PKCE authentication with Keycloak and local demo mode rejection in production

Implementation: `backend/app/main.py`, `backend/app/api/spatial_routes.py`, `backend/app/api/ml_routes.py`, `backend/app/api/macro_routes.py`, `backend/app/services/spatial_engine.py`, `backend/app/services/anomaly_detector.py`, `backend/app/services/macro_engine.py`, `frontend/src/App.tsx`, `frontend/src/components/GlobeView.tsx`, `frontend/src/components/BookmarksTray.tsx`

Tests: `backend/tests/test_spatial_engine.py`, `backend/tests/test_ml_anomaly.py`, `backend/tests/test_macro_engine.py`, `backend/tests/test_api_workflows.py`, `backend/tests/test_auth.py`, `frontend/src/__tests__/workflows.test.tsx`

### sonde-rf-hardware-sdr — Hardware SDR and SondeHub Web Receiver Integration

Status: planned

Acceptance:
- Local USB WebUSB/WebAudio SDR receiver direct streaming for ADS-B and FM broadcast
- Direct SondeHub radiosonde telemetry layer with balloon flight prediction vectors

### voice-multimodal-hud — Multimodal Voice Assistant and Speech-to-Text Navigation

Status: planned

Acceptance:
- Bidirectional voice commanding via Gemini Live and Whisper/Ollama local models
- Hands-free camera fly-to and entity investigation speech tools

