"""Tests for the SDR (Software Defined Radio) and SondeHub API routes.

Validates local USB WebUSB/WebAudio SDR receiver direct streaming for ADS-B and FM broadcast,
and direct SondeHub radiosonde telemetry layer with balloon flight prediction vectors.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_sdr_config():
    """Return current SDR receiver settings."""
    resp = client.get("/api/sdr/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["streaming"] is False
    assert body["frequency_mhz"] == 108.0
    assert body["gain_db"] == 10.0
    assert body["mode"] == "fm"
    assert body["sample_rate_sps"] == 2_000_000


def test_post_sdr_start():
    """Start local SDR receiver direct streaming for ADS-B and FM broadcast."""
    resp = client.post(
        "/api/sdr/start",
        json={"frequency_mhz": 108.0, "gain_db": 10.0, "mode": "fm"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "started"
    assert "SDR streaming started" in body["message"]


def test_post_sdr_start_different_params():
    """Start SDR with custom parameters."""
    resp = client.post(
        "/api/sdr/start",
        json={"frequency_mhz": 137.0, "gain_db": 20.0, "mode": "am"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "started"


def test_post_sdr_stop():
    """Stop the SDR receiver streaming."""
    # First start streaming
    client.post("/api/sdr/start", json={"frequency_mhz": 108.0, "gain_db": 10.0, "mode": "fm"})
    # Now stop
    resp = client.post("/api/sdr/stop")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "stopped"
    assert "SDR streaming stopped" in body["message"]


def test_post_sdr_set_frequency():
    """Set the SDR receiver tuning frequency in MHz."""
    resp = client.post("/api/sdr/set-frequency?frequency_mhz=137.0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["frequency_mhz"] == "137.0"


def test_post_sdr_set_mode():
    """Set the SDR reception mode."""
    resp = client.post("/api/sdr/set-mode?mode=am")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["mode"] == "am"

    # Test invalid mode
    resp = client.post("/api/sdr/set-mode?mode=invalid")
    assert resp.status_code == 400


def test_get_ads_b_aircraft():
    """Retrieve ADS-B decoded aircraft positions from SDR stream."""
    resp = client.get("/api/sdr/ads-b/aircraft")
    assert resp.status_code == 200
    body = resp.json()
    assert "aircraft" in body
    assert len(body["aircraft"]) > 0
    # Verify aircraft structure
    aircraft = body["aircraft"][0]
    assert "hex" in aircraft
    assert "altitude" in aircraft
    assert "ground_speed" in aircraft
    assert "track" in aircraft


def test_get_fm_stations():
    """Retrieve FM broadcast station listings from SDR scan."""
    resp = client.get("/api/sdr/fm/stations")
    assert resp.status_code == 200
    body = resp.json()
    assert "stations" in body
    assert len(body["stations"]) > 0
    # Verify station structure
    station = body["stations"][0]
    assert "frequency" in station
    assert "name" in station


def test_get_sondehub_status():
    """Check SondeHub radio connection and telemetry feed status."""
    resp = client.get("/api/sdr/sondehub/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["connected"] is True
    assert "last_balloon" in body
    balloon = body["last_balloon"]
    assert "callsign" in balloon
    assert "altitude" in balloon
    assert "latitude" in balloon
    assert "longitude" in balloon
    assert "timestamp" in balloon
    assert "flight_prediction" in body
    prediction = body["flight_prediction"]
    assert "estimated_landing" in prediction
    assert "landing_zone_km" in prediction
    assert "predicted_path" in prediction
    assert len(prediction["predicted_path"]) > 0
