import uuid
import enum
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, func, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base Class For The Tables"""


class ChatRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class LabStatus(enum.StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    sources: Mapped[list["Source"]] = relationship(
        back_populates="workspace", cascade="all, delete", passive_deletes=True
    )
    labs: Mapped[list["Lab"]] = relationship(
        back_populates="workspace", cascade="all, delete", passive_deletes=True
    )
    chats: Mapped[list["ChatMessages"]] = relationship(
        back_populates="workspace", cascade="all, delete", passive_deletes=True
    )
    settings: Mapped[list["WorkspaceSetting"]] = relationship(
        back_populates="workspace", cascade="all, delete", passive_deletes=True
    )
    edges: Mapped[list["Edges"]] = relationship(
        back_populates="workspace", cascade="all, delete", passive_deletes=True
    )


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )  # Fixed: ondelete goes inside ForeignKey
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text)
    meta_data: Mapped[dict | None] = mapped_column(JSONB)
    cache_id: Mapped[str | None] = mapped_column(Text)
    cache_expires_at: Mapped[datetime | None] = mapped_column()
    canvas_position: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="sources")
    labs: Mapped[list["Lab"]] = relationship(back_populates="source")


class Lab(Base):  # Fixed: should inherit from Base, not DeclarativeBase
    __tablename__ = "labs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )  # Fixed
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"))
    type: Mapped[str] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONB)
    generated_content: Mapped[dict] = mapped_column(JSONB)
    user_state: Mapped[dict] = mapped_column(JSONB)
    canvas_position: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[LabStatus] = mapped_column(Enum(LabStatus))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="labs")
    source: Mapped["Source"] = relationship(back_populates="labs")


class ChatMessages(Base):  # Fixed: should inherit from Base
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )  # Fixed
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole))
    content: Mapped[str] = mapped_column(Text)
    mentions: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="chats")


class WorkspaceSetting(Base):  # Fixed: should inherit from Base
    __tablename__ = "workspace_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )  # Fixed
    default_language: Mapped[str | None] = mapped_column(String(12))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="settings")


class Edges(Base):  # Fixed: should inherit from Base
    __tablename__ = "edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )  # Fixed
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True)
    )  # Fixed: was Mapped[str]
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True)
    )  # Fixed: was Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="edges")
