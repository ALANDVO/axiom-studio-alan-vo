"""Integration workflow tests crossing real HTTP boundaries."""
from app.core.security import generate_pkce_pair, verify_pkce


def test_core_bookmark_create_read_workflow(client, analyst_token):
    """Complete create/read lifecycle for saved favourite location across HTTP boundary (Issue #335)."""
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # 1. Create Bookmark
    create_payload = {
        "name": "London Heathrow Approach",
        "latitude": 51.4700,
        "longitude": -0.4543,
        "altitude": 1500.0,
        "heading": 270.0,
        "pitch": -35.0,
        "active_layers": ["satellites", "aircraft"],
    }
    create_res = client.post("/api/spatial/bookmarks", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    bm_id = create_res.json()["id"]

    # 2. Read list and assert newly created bookmark exists
    list_res = client.get("/api/spatial/bookmarks", headers=headers)
    assert list_res.status_code == 200
    bms = list_res.json()
    assert any(b["id"] == bm_id and b["name"] == "London Heathrow Approach" for b in bms)

    # 3. Clean up by deleting
    del_res = client.delete(f"/api/spatial/bookmarks/{bm_id}", headers=headers)
    assert del_res.status_code == 204


def test_complete_oidc_pkce_and_token_propagation(client):
    """Simulate complete OIDC PKCE flow, assert rejection on invalid verifier, and verify token propagation."""
    # Step 1: Client acquires OIDC config
    cfg_res = client.get("/api/auth/config")
    assert cfg_res.status_code == 200
    cfg = cfg_res.json()
    assert "keycloak_url" in cfg
    assert "client_id" in cfg

    # Step 2: Client generates PKCE challenge
    pkce = generate_pkce_pair()
    assert verify_pkce(pkce["code_verifier"], pkce["code_challenge"]) is True

    # Assert rejection on corrupted PKCE verifier
    assert verify_pkce(pkce["code_verifier"] + "-corrupted", pkce["code_challenge"]) is False

    # Step 3: Local authentication yields Bearer token
    login_res = client.post(
        "/api/auth/demo-login",
        json={"role": "analyst", "username": "analyst-pkce"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Step 4: Token propagation into protected API route
    auth_headers = {"Authorization": f"Bearer {token}"}
    profile_res = client.get("/api/auth/me", headers=auth_headers)
    assert profile_res.status_code == 200
    profile = profile_res.json()
    assert profile["username"] == "analyst-pkce"
    assert "analyst" in profile["roles"]


def test_admin_audit_log_query(client, admin_token, analyst_token):
    """Admin must be able to inspect persistent audit logs while viewers/analysts are rejected."""
    # Viewer/analyst should receive 403 Forbidden on /api/audit/logs
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    forbidden_res = client.get("/api/audit/logs", headers=analyst_headers)
    assert forbidden_res.status_code == 403

    # Admin should receive 200 OK
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_res = client.get("/api/audit/logs", headers=admin_headers)
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)


def test_advisory_context_filtering(client, analyst_token):
    """Advisory endpoint must filter context entities by target_entity_id and honor include_sensor_context."""
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # When include_sensor_context is False, no entities should reach the advisory engine
    no_ctx_res = client.post(
        "/api/ml/advisory",
        json={"query": "What is happening?", "include_sensor_context": False},
        headers=headers,
    )
    assert no_ctx_res.status_code == 200
    no_ctx_data = no_ctx_res.json()
    assert no_ctx_data["grounding_entities"] == []
    assert "0 analyzed" in no_ctx_data["summary"]

    # When target_entity_id is provided, only that entity should be in the grounding set
    entities_res = client.get("/api/spatial/entities", headers=headers)
    entities = entities_res.json()
    assert len(entities) > 0
    target_id = entities[0]["id"]

    targeted_res = client.post(
        "/api/ml/advisory",
        json={"query": "Tell me about this contact", "target_entity_id": target_id},
        headers=headers,
    )
    assert targeted_res.status_code == 200
    targeted_data = targeted_res.json()
    assert len(targeted_data["grounding_entities"]) == 1
    assert targeted_data["grounding_entities"][0] == target_id
    assert "1 analyzed" in targeted_data["summary"]
