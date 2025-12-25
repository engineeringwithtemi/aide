import pytest
from httpx import AsyncClient

from tests.conftest import (
    create_workspace,
    create_source,
    create_test_pdf,
    create_pdf_with_toc,
    create_pdf_with_chapter_pattern,
)

pytestmark = pytest.mark.asyncio

FAKE_UUID = "00000000-0000-0000-0000-000000000000"


async def test_create_source(client: AsyncClient):
    """POST creates source with id, workspace_id, type, title, timestamps."""
    workspace = await create_workspace(client, "Source Test Workspace")

    response = await client.post(
        "/v1/sources",
        json={"workspace_id": workspace["id"], "type": "pdf", "title": "My PDF"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["workspace_id"] == workspace["id"]
    assert data["type"] == "pdf"
    assert data["title"] == "My PDF"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["storage_path"] is None  # Not uploaded yet

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_get_source(client: AsyncClient):
    """GET returns source view data."""
    workspace = await create_workspace(client, "Get Source Test")
    source = await create_source(client, workspace["id"], "Get Test PDF")

    response = await client.get(f"/v1/sources/{source['id']}")

    assert response.status_code == 200
    data = response.json()
    # GET returns view data which has different structure than SourceRead
    assert data["type"] == "pdf"
    assert data["title"] == "Get Test PDF"
    assert "chapters" in data
    assert "storage_url" in data

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_update_source(client: AsyncClient):
    """PATCH updates source fields."""
    workspace = await create_workspace(client, "Update Source Test")
    source = await create_source(client, workspace["id"], "Original Title")

    response = await client.patch(
        f"/v1/sources/{source['id']}",
        json={"title": "Updated Title", "canvas_position": {"x": 100, "y": 200}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == source["id"]
    assert data["title"] == "Updated Title"
    assert data["canvas_position"] == {"x": 100, "y": 200}

    # Verify update persisted
    response = await client.get(f"/v1/sources/{source['id']}")
    assert response.json()["title"] == "Updated Title"

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_delete_source(client: AsyncClient):
    """DELETE removes source."""
    workspace = await create_workspace(client, "Delete Source Test")
    source = await create_source(client, workspace["id"], "Delete Me")

    # Delete it
    response = await client.delete(f"/v1/sources/{source['id']}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/v1/sources/{source['id']}")
    assert response.status_code == 404

    # Cleanup workspace
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_create_source_invalid_workspace(client: AsyncClient):
    """POST with non-existent workspace_id fails with integrity error (500).

    Note: The API doesn't pre-validate workspace existence, so DB rejects
    the foreign key constraint violation.
    """
    response = await client.post(
        "/v1/sources",
        json={"workspace_id": FAKE_UUID, "type": "pdf", "title": "Orphan PDF"},
    )
    # Database foreign key constraint violation returns 500
    assert response.status_code == 500


async def test_get_source_not_found(client: AsyncClient):
    """GET non-existent source returns 404."""
    response = await client.get(f"/v1/sources/{FAKE_UUID}")
    assert response.status_code == 404


async def test_update_source_not_found(client: AsyncClient):
    """PATCH non-existent source returns 404."""
    response = await client.patch(
        f"/v1/sources/{FAKE_UUID}", json={"title": "New Title"}
    )
    assert response.status_code == 404


async def test_delete_source_not_found(client: AsyncClient):
    """DELETE non-existent source returns 404."""
    response = await client.delete(f"/v1/sources/{FAKE_UUID}")
    assert response.status_code == 404


# ============ Upload Tests ============


async def test_upload_pdf(client: AsyncClient):
    """POST upload stores file and extracts chapters."""
    workspace = await create_workspace(client, "Upload PDF Test")
    source = await create_source(client, workspace["id"], "Upload Test PDF")

    pdf_bytes = create_test_pdf("Sample PDF content for testing", num_pages=3)

    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "pdf"
    assert data["title"] == "Upload Test PDF"
    assert "chapters" in data
    assert data["storage_url"] == "test/path/file.pdf"  # From mock

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_upload_pdf_extracts_chapters(client: AsyncClient):
    """PDF upload extracts chapter structure."""
    workspace = await create_workspace(client, "Chapters Extract Test")
    source = await create_source(client, workspace["id"], "Chapters Test PDF")

    # Create a 15-page PDF (will get divided into page ranges)
    pdf_bytes = create_test_pdf("Chapter content", num_pages=15)

    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("chapters.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "chapters" in data
    assert len(data["chapters"]) > 0

    # Each chapter should have required fields
    for chapter in data["chapters"]:
        assert "id" in chapter
        assert "title" in chapter
        assert "start_page" in chapter
        assert "end_page" in chapter

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_upload_invalid_file_type(client: AsyncClient):
    """Upload non-PDF returns 400."""
    workspace = await create_workspace(client, "Invalid Upload Test")
    source = await create_source(client, workspace["id"], "Invalid Type Test")

    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("test.txt", b"Not a PDF", "text/plain")},
    )

    assert response.status_code == 400

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_upload_to_already_uploaded_source(client: AsyncClient):
    """Upload to source with existing content returns 409."""
    workspace = await create_workspace(client, "Double Upload Test")
    source = await create_source(client, workspace["id"], "Double Upload PDF")

    pdf_bytes = create_test_pdf("First upload", num_pages=1)

    # First upload
    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("first.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200

    # Second upload should fail
    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("second.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 409

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_upload_source_not_found(client: AsyncClient):
    """Upload to non-existent source returns 404."""
    pdf_bytes = create_test_pdf("Orphan PDF", num_pages=1)

    response = await client.post(
        f"/v1/sources/{FAKE_UUID}/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 404


async def test_get_source_after_upload(client: AsyncClient):
    """GET source after upload returns view data with chapters."""
    workspace = await create_workspace(client, "Get After Upload Test")
    source = await create_source(client, workspace["id"], "View Test PDF")

    pdf_bytes = create_test_pdf("PDF content", num_pages=5)

    # Upload
    await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    # Get source view
    response = await client.get(f"/v1/sources/{source['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "pdf"
    assert "chapters" in data
    assert "storage_url" in data
    assert data["storage_url"] is not None

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_upload_file_too_large(client: AsyncClient):
    """Upload file > 50MB returns 413."""
    workspace = await create_workspace(client, "Large File Test")
    source = await create_source(client, workspace["id"], "Large File PDF")

    # Create fake large content (just need headers to report large size)
    # We'll create a small PDF but lie about content-length won't work with httpx
    # Instead, create actual large bytes (51MB)
    large_content = b"%PDF-1.4\n" + (b"0" * (51 * 1024 * 1024))

    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("large.pdf", large_content, "application/pdf")},
    )

    assert response.status_code == 413

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_delete_source_with_file(client: AsyncClient):
    """DELETE source with uploaded file also deletes from storage."""
    workspace = await create_workspace(client, "Delete With File Test")
    source = await create_source(client, workspace["id"], "Delete With File PDF")

    pdf_bytes = create_test_pdf("Content to delete", num_pages=1)

    # Upload file first
    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200

    # Delete source (should also trigger supabase delete_files)
    response = await client.delete(f"/v1/sources/{source['id']}")
    assert response.status_code == 204

    # Verify source is gone
    response = await client.get(f"/v1/sources/{source['id']}")
    assert response.status_code == 404

    # Cleanup workspace
    await client.delete(f"/v1/workspaces/{workspace['id']}")


# ============ PDF Parsing Strategy Tests ============


async def test_upload_pdf_with_toc(client: AsyncClient):
    """PDF with TOC extracts chapters from table of contents."""
    workspace = await create_workspace(client, "TOC PDF Test")
    source = await create_source(client, workspace["id"], "TOC Test PDF")

    pdf_bytes = create_pdf_with_toc()

    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("toc.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "chapters" in data
    assert len(data["chapters"]) == 3

    # Verify chapter titles from TOC
    titles = [ch["title"] for ch in data["chapters"]]
    assert "Introduction" in titles
    assert "Main Content" in titles
    assert "Conclusion" in titles

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")


async def test_upload_pdf_with_chapter_patterns(client: AsyncClient):
    """PDF with 'Chapter N' text patterns extracts chapters correctly."""
    workspace = await create_workspace(client, "Chapter Pattern PDF Test")
    source = await create_source(client, workspace["id"], "Chapter Pattern Test PDF")

    pdf_bytes = create_pdf_with_chapter_pattern()

    response = await client.post(
        f"/v1/sources/{source['id']}/upload",
        files={"file": ("chapters.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "chapters" in data
    assert len(data["chapters"]) == 2

    # Verify chapter titles from pattern matching
    titles = [ch["title"] for ch in data["chapters"]]
    assert "Chapter 1" in titles
    assert "Chapter 2" in titles

    # Cleanup
    await client.delete(f"/v1/workspaces/{workspace['id']}")
