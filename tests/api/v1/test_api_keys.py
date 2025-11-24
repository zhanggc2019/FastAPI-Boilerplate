import pytest
from httpx import AsyncClient
from tests.test_fixtures import authenticated_client, async_client, test_user, test_app, db_session, event_loop, setup_test_environment, cleanup_test_data

@pytest.mark.asyncio
async def test_create_api_key(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/api-keys",
        json={"name": "Test Key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Key"
    assert "key" in data
    assert data["key"].startswith("sk_")

@pytest.mark.asyncio
async def test_list_api_keys(authenticated_client: AsyncClient):
    # Create a key first
    await authenticated_client.post(
        "/api/v1/api-keys",
        json={"name": "List Test Key"},
    )

    response = await authenticated_client.get("/api/v1/api-keys")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(k["name"] == "List Test Key" for k in data)

@pytest.mark.asyncio
async def test_revoke_api_key(authenticated_client: AsyncClient):
    # Create a key
    create_res = await authenticated_client.post(
        "/api/v1/api-keys",
        json={"name": "Revoke Test Key"},
    )
    key_id = create_res.json()["id"]

    # Revoke it
    response = await authenticated_client.delete(f"/api/v1/api-keys/{key_id}")
    assert response.status_code == 204

    # Verify it's gone
    list_res = await authenticated_client.get("/api/v1/api-keys")
    data = list_res.json()
    assert not any(k["id"] == key_id for k in data)
