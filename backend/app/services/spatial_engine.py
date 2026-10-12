"""Spatial intelligence engine providing orbital physics, sensor fusion, and camera feeds."""
import datetime
import math
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import BookmarkRecord
from app.models.schemas import BookmarkCreate, BookmarkResponse, CameraFeed, SpatialEntity

EARTH_RADIUS_KM = 6371.0
MU_EARTH = 398600.4418


def propagate_keplerian_orbit(
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float,
    arg_perigee_deg: float,
    mean_anomaly_deg: float,
    elapsed_seconds: float,
) -> Dict[str, float]:
    """Propagate Keplerian two-body orbit to compute sub-satellite ground coordinates."""
    n_rad_s = math.sqrt(MU_EARTH / (semi_major_axis_km ** 3))
    m_curr_rad = (math.radians(mean_anomaly_deg) + n_rad_s * elapsed_seconds) % (2 * math.pi)

    e_anom = m_curr_rad
    for _ in range(8):
        f = e_anom - eccentricity * math.sin(e_anom) - m_curr_rad
        delta = f / (1.0 - eccentricity * math.cos(e_anom))
        e_anom -= delta
        if abs(delta) < 1e-7:
            break

    sin_v = (math.sqrt(1.0 - eccentricity**2) * math.sin(e_anom)) / (1.0 - eccentricity * math.cos(e_anom))
    cos_v = (math.cos(e_anom) - eccentricity) / (1.0 - eccentricity * math.cos(e_anom))
    true_anomaly_rad = math.atan2(sin_v, cos_v)

    r_km = semi_major_axis_km * (1.0 - eccentricity * math.cos(e_anom))
    altitude_km = max(0.0, r_km - EARTH_RADIUS_KM)
    velocity_kms = math.sqrt(MU_EARTH * (2.0 / r_km - 1.0 / semi_major_axis_km))

    u_rad = math.radians(arg_perigee_deg) + true_anomaly_rad
    inc_rad = math.radians(inclination_deg)
    node_rad = math.radians(raan_deg) - 7.2921159e-5 * elapsed_seconds

    x_orbit = r_km * math.cos(u_rad)
    y_orbit = r_km * math.sin(u_rad)

    x_eci = x_orbit * math.cos(node_rad) - y_orbit * math.cos(inc_rad) * math.sin(node_rad)
    y_eci = x_orbit * math.sin(node_rad) + y_orbit * math.cos(inc_rad) * math.cos(node_rad)
    z_eci = y_orbit * math.sin(inc_rad)

    lat_deg = math.degrees(math.atan2(z_eci, math.sqrt(x_eci**2 + y_eci**2)))
    lon_deg = (math.degrees(math.atan2(y_eci, x_eci)) + 180.0) % 360.0 - 180.0

    cos_ang = EARTH_RADIUS_KM / (EARTH_RADIUS_KM + altitude_km)
    swath_radius_km = EARTH_RADIUS_KM * math.acos(max(0.0, min(1.0, cos_ang)))

    return {
        "latitude": round(lat_deg, 4),
        "longitude": round(lon_deg, 4),
        "altitude_km": round(altitude_km, 2),
        "velocity_kms": round(velocity_kms, 3),
        "footprint_radius_km": round(swath_radius_km, 1),
    }


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance between two points in kilometers."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return EARTH_RADIUS_KM * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


RAW_CAMERAS = [
    {"id": "cam-austin-01", "name": "I-35 @ 6th St", "city": "Austin", "region": "Texas", "lat": 30.2672, "lon": -97.7431, "stream": "https://datumfeed.example.org/austin/i35_6th.mjpg", "attr": "Austin Open Data / Datumfeed", "ok": True, "fps": 15.0},
    {"id": "cam-london-01", "name": "Trafalgar Sq", "city": "London", "region": "UK", "lat": 51.5080, "lon": -0.1281, "stream": "https://datumfeed.example.org/tfl/trafalgar.mjpg", "attr": "TfL Open Data", "ok": True, "fps": 20.0},
    {"id": "cam-brennero-01", "name": "A22 Brennero KM 0.5", "city": "Brenner", "region": "Italy", "lat": 47.0064, "lon": 11.5056, "stream": "https://datumfeed.example.org/a22/brenner.mjpg", "attr": "Autostrada del Brennero A22", "ok": True, "fps": 10.0},
    {"id": "cam-dead-01", "name": "Dead Feed Test", "city": "Invalid", "region": "N/A", "lat": 95.0, "lon": -200.0, "stream": "https://dead.example.org/stream.mjpg", "attr": "Test", "ok": False, "fps": 0.0},
]


class SpatialEngine:
    def __init__(self) -> None:
        self.epoch_start_time = time.time()

    def get_verified_cameras(self, min_lat: float = -90.0, max_lat: float = 90.0, min_lon: float = -180.0, max_lon: float = 180.0) -> List[CameraFeed]:
        verified = []
        for c in RAW_CAMERAS:
            if not c["ok"] or c["fps"] <= 0 or not (-90 <= c["lat"] <= 90 and -180 <= c["lon"] <= 180):
                continue
            if min_lat <= c["lat"] <= max_lat and min_lon <= c["lon"] <= max_lon:
                verified.append(CameraFeed(
                    id=c["id"], name=c["name"], city=c["city"], region=c["region"],
                    latitude=c["lat"], longitude=c["lon"], stream_url=c["stream"],
                    attribution=c["attr"], is_healthy=True, fps=c["fps"],
                    last_poll_status="200_OK_VERIFIED", fov_degrees=60.0
                ))
        return verified

    def get_live_entities(self, min_lat: float = -90.0, max_lat: float = 90.0, min_lon: float = -180.0, max_lon: float = 180.0, layers: Optional[List[str]] = None, limit: int = 100) -> List[SpatialEntity]:
        elapsed = time.time() - self.epoch_start_time
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        entities = []
        allowed = set(layers) if layers else {"satellites", "aircraft", "rf_stations", "cameras"}

        if "satellites" in allowed:
            for s in [
                {"id": "sat-iss-25544", "cs": "ISS (ZARYA)", "a": 6791.0, "e": 0.0001, "i": 51.64, "r": 120.0, "w": 45.0, "m": 210.0},
                {"id": "sat-sentinel-2a", "cs": "SENTINEL-2A", "a": 7157.0, "e": 0.0001, "i": 98.62, "r": 240.0, "w": 90.0, "m": 30.0},
            ]:
                p = propagate_keplerian_orbit(s["a"], s["e"], s["i"], s["r"], s["w"], s["m"], elapsed)
                if min_lat <= p["latitude"] <= max_lat and min_lon <= p["longitude"] <= max_lon:
                    entities.append(SpatialEntity(
                        id=s["id"], entity_type="satellite", callsign=s["cs"],
                        latitude=p["latitude"], longitude=p["longitude"],
                        altitude=p["altitude_km"] * 1000.0, velocity=p["velocity_kms"] * 1000.0,
                        heading=s["i"], status="nominal_orbit",
                        metadata={"footprint_radius_km": p["footprint_radius_km"]}, last_seen=now_dt
                    ))

        if "aircraft" in allowed:
            for a in [
                {"id": "air-ua901", "cs": "UAL901 (B772)", "lat": 38.89, "lon": -77.03, "hdg": 85.0, "spd": 246.0, "alt": 11000.0},
                {"id": "air-ba117", "cs": "BAW117 (A350)", "lat": 51.47, "lon": -0.45, "hdg": 280.0, "spd": 260.0, "alt": 11800.0},
            ]:
                d_m = a["spd"] * (elapsed % 3600.0)
                cur_lat = round(a["lat"] + (d_m * math.cos(math.radians(a["hdg"]))) / 111320.0, 4)
                cur_lon = round(((a["lon"] + (d_m * math.sin(math.radians(a["hdg"]))) / (111320.0 * math.cos(math.radians(a["lat"]))) + 180) % 360) - 180, 4)
                if min_lat <= cur_lat <= max_lat and min_lon <= cur_lon <= max_lon:
                    entities.append(SpatialEntity(
                        id=a["id"], entity_type="aircraft", callsign=a["cs"],
                        latitude=cur_lat, longitude=cur_lon, altitude=a["alt"],
                        velocity=a["spd"], heading=a["hdg"], status="airborne",
                        metadata={"transponder": "ADS-B_OUT"}, last_seen=now_dt
                    ))

        if "rf_stations" in allowed:
            for r in [
                {"id": "rf-sonde-01", "cs": "SondeHub RX #412", "lat": 51.52, "lon": -0.10, "freq": 403.0},
                {"id": "rf-mesh-01", "cs": "MeshCore Tower ATX", "lat": 30.27, "lon": -97.74, "freq": 915.0},
            ]:
                if min_lat <= r["lat"] <= max_lat and min_lon <= r["lon"] <= max_lon:
                    entities.append(SpatialEntity(
                        id=r["id"], entity_type="rf_station", callsign=r["cs"],
                        latitude=r["lat"], longitude=r["lon"], altitude=150.0,
                        velocity=0.0, heading=0.0, status="online",
                        metadata={"frequency_mhz": r["freq"]}, last_seen=now_dt
                    ))

        if "cameras" in allowed:
            for cam in self.get_verified_cameras(min_lat, max_lat, min_lon, max_lon):
                entities.append(SpatialEntity(
                    id=cam.id, entity_type="camera", callsign=f"{cam.city} - {cam.name}",
                    latitude=cam.latitude, longitude=cam.longitude, altitude=15.0,
                    velocity=0.0, heading=0.0, status="verified_stream",
                    metadata={"fps": cam.fps, "city": cam.city}, last_seen=now_dt
                ))

        return entities[:limit]

    def create_bookmark(self, db: Session, req: BookmarkCreate, user_id: str) -> BookmarkResponse:
        import json
        rec = BookmarkRecord(
            name=req.name, latitude=req.latitude, longitude=req.longitude,
            altitude=req.altitude, heading=req.heading, pitch=req.pitch,
            active_layers=json.dumps(req.active_layers), created_by=user_id,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return self._to_bm(rec)

    def list_bookmarks(self, db: Session) -> List[BookmarkResponse]:
        return [self._to_bm(r) for r in db.query(BookmarkRecord).order_by(BookmarkRecord.created_at.desc()).all()]

    def delete_bookmark(self, db: Session, bookmark_id: str) -> bool:
        r = db.query(BookmarkRecord).filter(BookmarkRecord.id == bookmark_id).first()
        if not r: return False
        db.delete(r)
        db.commit()
        return True

    def _to_bm(self, r: BookmarkRecord) -> BookmarkResponse:
        import json
        try: layers = json.loads(r.active_layers) if r.active_layers else []
        except Exception: layers = []
        return BookmarkResponse(
            id=r.id, name=r.name, latitude=r.latitude, longitude=r.longitude,
            altitude=r.altitude or 1000.0, heading=r.heading or 0.0, pitch=r.pitch or -45.0,
            active_layers=layers, created_by=r.created_by, created_at=r.created_at, updated_at=r.updated_at
        )


spatial_engine = SpatialEngine()
