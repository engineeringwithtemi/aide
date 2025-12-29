import uuid
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any
from app.db.tables import ChatRole, LabStatus


# ============ Workspace ============
class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceUpdate(BaseModel):
    name: str | None = None


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


# ============ Source ============
class SourceCreate(BaseModel):
    workspace_id: uuid.UUID
    type: str
    title: str
    storage_path: str | None = None
    meta_data: dict | None = None
    cache_id: str | None = None
    cache_expires_at: datetime | None = None
    canvas_position: dict | None = None


class SourceUpdate(BaseModel):
    type: str | None = None
    title: str | None = None
    storage_path: str | None = None
    meta_data: dict | None = None
    cache_id: str | None = None
    cache_expires_at: datetime | None = None
    canvas_position: dict | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    type: str
    title: str
    storage_path: str | None
    meta_data: dict | None
    cache_id: str | None
    cache_expires_at: datetime | None
    canvas_position: dict | None
    created_at: datetime
    updated_at: datetime


# ============ Lab ============
class LabCreate(BaseModel):
    workspace_id: uuid.UUID
    source_id: uuid.UUID
    type: str
    config: dict
    generated_content: dict
    user_state: dict
    canvas_position: dict
    status: LabStatus


class LabUpdate(BaseModel):
    config: dict | None = None
    generated_content: dict | None = None
    user_state: dict | None = None
    canvas_position: dict | None = None
    status: LabStatus | None = None


class LabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    source_id: uuid.UUID
    type: str
    config: dict
    generated_content: dict
    user_state: dict
    canvas_position: dict
    status: LabStatus
    created_at: datetime
    updated_at: datetime


# ============ ChatMessage ============
class ChatMessageCreate(BaseModel):
    workspace_id: uuid.UUID
    role: ChatRole
    content: str
    mentions: dict | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    role: ChatRole
    content: str
    mentions: dict | None
    created_at: datetime
    updated_at: datetime


# ============ WorkspaceSetting ============
class WorkspaceSettingCreate(BaseModel):
    workspace_id: uuid.UUID
    default_language: str | None = None


class WorkspaceSettingUpdate(BaseModel):
    default_language: str | None = None


class WorkspaceSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    default_language: str | None
    created_at: datetime
    updated_at: datetime


# ============ Edge ============
class EdgeCreate(BaseModel):
    workspace_id: uuid.UUID
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID


class EdgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


@dataclass
class SourceMetadata:
    """Metadata returned after source setup"""

    title: str
    metadata: Dict[str, Any]


@dataclass
class Chapter:
    """PDF Chapter/Section Data"""

    id: str
    title: str
    start_page: int
    end_page: int
    text: str


@dataclass
class CacheResult:
    cache_id: str
    expires_at: datetime
