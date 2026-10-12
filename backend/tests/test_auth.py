"""Authentication and authorization security tests."""
import pytest
from app.core.config import Settings
from app.core.security import generate_pkce_pair, verify_pkce


def test_unauthenticated_request_rejected(client):
    """Unauthenticated requests to protected endpoints must return 401 Unauthorized."""
    res = client.get("/api/spatial/entities")
    assert res.status_code == 401
    assert "detail" in res.json()


def test_role_based_denial_for_viewer(client, viewer_token):
    """Viewers must be denied from mutating bookmarks (403 Forbidden)."""
    headers = {"Authorization": f"Bearer {viewer_token}"}
    payload = {
        "name": "Unauthorized Test",
        "latitude": 30.0,
        "longitude": -97.0,
        "altitude": 1000.0,
        "heading": 0.0,
        "pitch": -45.0,
        "active_layers": [],
    }
    res = client.post("/api/spatial/bookmarks", json=payload, headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


def test_role_authorization_for_analyst(client, analyst_token):
    """Analysts must be permitted to create and delete favourite bookmarks."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    payload = {
        "name": "Austin Mission Hub",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "altitude": 1200.0,
        "heading": 180.0,
        "pitch": -30.0,
        "active_layers": ["satellites", "cameras"],
    }
    res = client.post("/api/spatial/bookmarks", json=payload, headers=headers)
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == "Austin Mission Hub"
    assert created["latitude"] == 30.2672

    # Cleanup
    del_res = client.delete(f"/api/spatial/bookmarks/{created['id']}", headers=headers)
    assert del_res.status_code == 204


def test_pkce_challenge_verification_and_rejection():
    """PKCE verification must accept valid S256 verifiers and reject mismatches."""
    pair = generate_pkce_pair()
    assert pair["method"] == "S256"
    assert verify_pkce(pair["code_verifier"], pair["code_challenge"]) is True
    # Tampered verifier must fail
    assert verify_pkce(pair["code_verifier"] + "tampered", pair["code_challenge"]) is False
    assert verify_pkce("", pair["code_challenge"]) is False


def test_production_startup_refuses_demo_mode():
    """Startup check must raise ValueError if demo_mode is True in production."""
    with pytest.raises(ValueError, match="strictly forbidden in production"):
        prod_settings = Settings(ENVIRONMENT="production", DEMO_MODE=True)
        prod_settings.validate_production_safety()


def test_demo_login_endpoint(client):
    """Local demo login endpoint should issue valid signed JWTs with requested role."""
    res = client.post("/api/auth/demo-login", json={"role": "analyst", "username": "analyst-local"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert "analyst" in data["roles"]
