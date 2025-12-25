import pytest
from httpx import AsyncClient

from tests.conftest import create_workspace

pytestmark = pytest.mark.asyncio

FAKE_UUID = "00000000-0000-0000-0000-000000000000"


async def test_create_workspace(client: AsyncClient):
    """POST returns workspace with id, name, timestamps."""
    response = await client.post("/v1/workspaces", json={"name": "My Workspace"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Workspace"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Cleanup
    await client.delete(f"/v1/workspaces/{data['id']}")


async def test_get_workspace(client: AsyncClient):
    """GET returns the created workspace."""
    workspace = await create_workspace(client, "Get Test")

    response = await client.get(f"/v1/workspaces/{workspace['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workspace["id"]
    assert data["name"] == workspace["name"]

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_list_workspaces(client: AsyncClient):
    """GET returns list of workspaces."""
    # Create a few workspaces
    created = []
    for i in range(3):
        ws = await create_workspace(client, f"List Test {i}")
        created.append(ws)

    # List workspaces
    response = await client.get("/v1/workspaces")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 3

    # Verify our workspaces are in the list
    created_ids = {ws["id"] for ws in created}
    returned_ids = {ws["id"] for ws in data}
    assert created_ids.issubset(returned_ids)

    # Cleanup
    for ws in created:
        await client.delete(f"/v1/workspaces/{ws['id']}")


async def test_list_workspaces_pagination(client: AsyncClient):
    """Pagination params work correctly."""
    # Create 5 workspaces
    created = []
    for i in range(5):
        ws = await create_workspace(client, f"Page Test {i}")
        created.append(ws)

    # Test limit
    response = await client.get("/v1/workspaces", params={"limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test offset
    response = await client.get("/v1/workspaces", params={"limit": 2, "offset": 2})
    assert response.status_code == 200
    data_offset = response.json()
    assert len(data_offset) == 2

    # Verify offset returns different workspaces
    first_page_ids = {ws["id"] for ws in data}
    second_page_ids = {ws["id"] for ws in data_offset}
    assert first_page_ids.isdisjoint(second_page_ids)

    # Cleanup
    for ws in created:
        await client.delete(f"/v1/workspaces/{ws['id']}")


async def test_update_workspace(client: AsyncClient):
    """PATCH updates name, returns updated data."""
    workspace = await create_workspace(client, "Update Test")

    response = await client.patch(
        f"/v1/workspaces/{workspace['id']}", json={"name": "Updated Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workspace["id"]
    assert data["name"] == "Updated Name"

    # Verify update persisted
    response = await client.get(f"/v1/workspaces/{workspace['id']}")
    assert response.json()["name"] == "Updated Name"

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_delete_workspace(client: AsyncClient):
    """DELETE removes workspace."""
    workspace = await create_workspace(client, "Delete Test")

    # Delete it
    response = await client.delete(f"/v1/workspaces/{workspace['id']}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/v1/workspaces/{workspace['id']}")
    assert response.status_code == 404


async def test_delete_workspace_cascades(client: AsyncClient):
    """DELETE workspace removes all sources."""
    workspace = await create_workspace(client, "Cascade Test")

    # Create source in workspace
    response = await client.post(
        "/v1/sources",
        json={"workspace_id": workspace["id"], "type": "pdf", "title": "Test PDF"},
    )
    assert response.status_code == 201
    source = response.json()

    # Delete workspace
    response = await client.delete(f"/v1/workspaces/{workspace['id']}")
    assert response.status_code == 204

    # Verify source is gone
    response = await client.get(f"/v1/sources/{source['id']}")
    assert response.status_code == 404


async def test_get_workspace_not_found(client: AsyncClient):
    """GET non-existent workspace returns 404."""
    response = await client.get(f"/v1/workspaces/{FAKE_UUID}")
    assert response.status_code == 404


async def test_update_workspace_not_found(client: AsyncClient):
    """PATCH non-existent workspace returns 404."""
    response = await client.patch(
        f"/v1/workspaces/{FAKE_UUID}", json={"name": "New Name"}
    )
    assert response.status_code == 404


async def test_delete_workspace_not_found(client: AsyncClient):
    """DELETE non-existent workspace returns 404."""
    response = await client.delete(f"/v1/workspaces/{FAKE_UUID}")
    assert response.status_code == 404
