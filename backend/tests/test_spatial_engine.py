"""Domain tests for spatial calculations, orbital physics, and camera filtering."""
import math
from app.services.spatial_engine import (
    haversine_distance_km,
    propagate_keplerian_orbit,
    spatial_engine,
)


def test_propagate_keplerian_orbit_validity():
    """Verify Keplerian two-body orbital propagation outputs realistic coordinates and velocity."""
    res = propagate_keplerian_orbit(
        semi_major_axis_km=6791.0,  # ~420km ISS orbit
        eccentricity=0.0001,
        inclination_deg=51.64,
        raan_deg=120.0,
        arg_perigee_deg=45.0,
        mean_anomaly_deg=210.0,
        elapsed_seconds=1200.0,
    )
    assert -90.0 <= res["latitude"] <= 90.0
    assert -180.0 <= res["longitude"] <= 180.0
    # Orbital altitude for 6791km SMA should be around 420km
    assert 400.0 <= res["altitude_km"] <= 440.0
    # Orbital velocity for LEO should be ~7.6 to 7.8 km/s
    assert 7.5 <= res["velocity_kms"] <= 7.8
    assert res["footprint_radius_km"] > 0


def test_haversine_distance_calculation():
    """Test Great-Circle distance between Austin and London."""
    # Austin, TX: (30.2672, -97.7431) -> London: (51.5074, -0.1278)
    dist = haversine_distance_km(30.2672, -97.7431, 51.5074, -0.1278)
    # Expected Great Circle distance is ~7920 km
    assert 7800.0 < dist < 8100.0


def test_camera_dead_feed_filtering():
    """Ensure dead feeds and coordinates outside bounds are provably filtered out (Issue #1)."""
    cameras = spatial_engine.get_verified_cameras()
    assert len(cameras) >= 3
    for cam in cameras:
        assert cam.is_healthy is True
        assert cam.fps > 0
        assert -90.0 <= cam.latitude <= 90.0
        assert -180.0 <= cam.longitude <= 180.0
        assert cam.id != "cam-dead-01"


def test_viewport_spatial_filtering():
    """Verify entities are correctly filtered when bounding box is constrained."""
    # Query Europe-focused bounding box
    entities = spatial_engine.get_live_entities(
        min_lat=40.0, max_lat=60.0, min_lon=-10.0, max_lon=30.0, limit=50
    )
    for e in entities:
        assert 40.0 <= e.latitude <= 60.0
        assert -10.0 <= e.longitude <= 30.0
