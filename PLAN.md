# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

anomaly-detector-improvements

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

### anomaly-detector-improvements — Anomaly Detection Robustness Enhancements

Status: done

Acceptance:
- Expanded DOMAIN_PROFILES with realistic tolerances for mobile RF stations (drone/vehicle-mounted) and elevated cameras (rooftop/gantry)
- Added 'unknown' entity type profile with conservative defaults and warning logging for unrecognized entity types
- Extended benchmark dataset with 8 new test cases covering mobile RF sensors, elevated cameras, and unknown entity types
- Achieves perfect benchmark metrics (Precision=1.0, Recall=1.0, F1=1.0, Accuracy=1.0, ROC-AUC=1.0) with zero failure cases
- Eliminates false positives for legitimate edge cases: cameras on tall buildings, drone-mounted RF sensors, vehicle-mounted mesh relays

Implementation: `backend/app/services/anomaly_detector.py`

Tests: `backend/tests/test_ml_anomaly.py`

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

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
