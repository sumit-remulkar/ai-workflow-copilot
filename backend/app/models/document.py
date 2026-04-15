from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="New chat", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_name: Mapped[str] = mapped_column(String(255), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
