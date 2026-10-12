"""Spatial telemetry, camera feeds, and bookmark endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.audit import log_action
from app.core.security import AuthUser, get_current_user, require_roles
from app.models.database import get_db
from app.models.schemas import BookmarkCreate, BookmarkResponse, CameraFeed, SpatialEntity
from app.services.spatial_engine import spatial_engine

router = APIRouter(prefix="/api/spatial", tags=["Spatial Intelligence"])


@router.get("/entities", response_model=List[SpatialEntity])
def query_spatial_entities(
    min_lat: float = Query(-90.0, ge=-90.0, le=90.0),
    max_lat: float = Query(90.0, ge=-90.0, le=90.0),
    min_lon: float = Query(-180.0, ge=-180.0, le=180.0),
    max_lon: float = Query(180.0, ge=-180.0, le=180.0),
    layers: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: AuthUser = Depends(get_current_user),
) -> List[SpatialEntity]:
    """Retrieve live multi-source spatial entities within bounding box coordinates."""
    return spatial_engine.get_live_entities(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        layers=layers,
        limit=limit,
    )


@router.get("/cameras", response_model=List[CameraFeed])
def list_verified_cameras(
    min_lat: float = Query(-90.0, ge=-90.0, le=90.0),
    max_lat: float = Query(90.0, ge=-90.0, le=90.0),
    min_lon: float = Query(-180.0, ge=-180.0, le=180.0),
    max_lon: float = Query(180.0, ge=-180.0, le=180.0),
    user: AuthUser = Depends(get_current_user),
) -> List[CameraFeed]:
    """Retrieve public traffic cameras with verified stream health and CORS headers (Issue #1)."""
    return spatial_engine.get_verified_cameras(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )


@router.get("/bookmarks", response_model=List[BookmarkResponse])
def get_saved_bookmarks(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> List[BookmarkResponse]:
    """Retrieve saved favourite locations and camera viewpoints (Issue #335)."""
    return spatial_engine.list_bookmarks(db)


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_saved_bookmark(
    payload: BookmarkCreate,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["analyst", "operator", "admin"])),
) -> BookmarkResponse:
    """Save the current location, altitude, heading, pitch, and layers as a reusable favourite."""
    bookmark = spatial_engine.create_bookmark(db, payload, user_id=user.username)
    log_action(
        db,
        user_id=user.username,
        action="create_bookmark",
        resource=f"bookmark:{bookmark.id}",
        details={"name": bookmark.name, "lat": bookmark.latitude, "lon": bookmark.longitude},
        role=user.roles[0] if user.roles else "unknown",
    )
    return bookmark


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_bookmark(
    bookmark_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_roles(["analyst", "operator", "admin"])),
) -> None:
    """Delete a saved bookmark by identifier."""
    success = spatial_engine.delete_bookmark(db, bookmark_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found.")
    log_action(
        db,
        user_id=user.username,
        action="delete_bookmark",
        resource=f"bookmark:{bookmark_id}",
        role=user.roles[0] if user.roles else "unknown",
    )
