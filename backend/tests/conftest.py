import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pymupdf
from httpx import AsyncClient, ASGITransport
from alembic.config import Config
from alembic import command

from app.main import app
from app.config.settings import settings


def create_test_pdf(text: str = "Test PDF content", num_pages: int = 1) -> bytes:
    """Create a simple PDF with text content."""
    doc = pymupdf.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"{text}\nPage {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_pdf_with_toc() -> bytes:
    """Create a PDF with table of contents for testing TOC extraction."""
    doc = pymupdf.open()

    # Create pages with content
    for i in range(3):
        page = doc.new_page()
        page.insert_text((72, 72), f"Content for chapter {i + 1}\nPage {i + 1}")

    # Add TOC entries (level, title, page_number)
    toc = [
        [1, "Introduction", 1],
        [1, "Main Content", 2],
        [1, "Conclusion", 3],
    ]
    doc.set_toc(toc)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_pdf_with_chapter_pattern() -> bytes:
    """Create a PDF with 'Chapter N' text patterns for testing pattern extraction."""
    doc = pymupdf.open()

    # Page 1 with Chapter 1
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Chapter 1\nThis is the first chapter content.")

    # Page 2 with more content
    page2 = doc.new_page()
    page2.insert_text((72, 72), "More content for chapter 1.")

    # Page 3 with Chapter 2
    page3 = doc.new_page()
    page3.insert_text((72, 72), "Chapter 2\nThis is the second chapter content.")

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(scope="session")
def setup_database():
    """Run migrations once before all tests."""
    alembic_cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_cfg, "head")
    yield


@pytest.fixture(scope="session")
def mock_supabase_service():
    """Mock SupabaseService for tests."""
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="test/path/file.pdf")
    mock.delete_files = AsyncMock(return_value=None)
    return mock


@pytest.fixture(scope="session")
async def client(setup_database, mock_supabase_service):
    """Async test client for API requests."""
    app.state.supabase_service = mock_supabase_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def create_workspace(client: AsyncClient, name: str = "Test Workspace") -> dict:
    """Helper to create a workspace."""
    response = await client.post("/v1/workspaces", json={"name": name})
    assert response.status_code == 201, f"Failed to create workspace: {response.text}"
    return response.json()


async def delete_workspace(client: AsyncClient, workspace_id: str) -> None:
    """Helper to delete a workspace."""
    await client.delete(f"/v1/workspaces/{workspace_id}")


async def create_source(
    client: AsyncClient,
    workspace_id: str,
    title: str = "Test Source",
    source_type: str = "pdf",
) -> dict:
    """Helper to create a source."""
    response = await client.post(
        "/v1/sources",
        json={"workspace_id": workspace_id, "type": source_type, "title": title},
    )
    assert response.status_code == 201, f"Failed to create source: {response.text}"
    return response.json()


async def delete_source(client: AsyncClient, source_id: str) -> None:
    """Helper to delete a source."""
    await client.delete(f"/v1/sources/{source_id}")
