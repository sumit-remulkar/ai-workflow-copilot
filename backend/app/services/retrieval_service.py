from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import DocumentChunk
from app.services.embedding_service import EmbeddingService

class RetrievalService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    def retrieve(self, db: Session, question: str, document_id: int | None = None, top_k: int = 4) -> list[DocumentChunk]:
        query_embedding = self.embedding_service.embed_text(question)

        stmt = select(DocumentChunk)
        if document_id is not None:
            stmt = stmt.where(DocumentChunk.document_id == document_id)

        chunks = db.execute(stmt).scalars().all()
        if not chunks:
            return []

        def score(chunk: DocumentChunk) -> float:
            emb = chunk.embedding or []
            if not emb:
                return -1.0
            return sum(a * b for a, b in zip(query_embedding, emb))

        ranked = sorted(chunks, key=score, reverse=True)
        return ranked[:top_k]
