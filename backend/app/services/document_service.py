from __future__ import annotations

from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.utils.text import checksum_bytes, chunk_text, ensure_dir, naive_token_count, read_uploaded_text


class DocumentService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    def save_upload(
        self,
        db: Session,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        metadata: dict | None = None,
    ) -> Document:
        ensure_dir(settings.upload_dir)
        file_path = Path(settings.upload_dir) / filename
        file_path.write_bytes(file_bytes)

        document = Document(
            filename=filename,
            content_type=content_type,
            file_path=str(file_path),
            status="uploaded",
            checksum=checksum_bytes(file_bytes),
            metadata=metadata or {},
        )
        db.add(document)
        db.flush()
        return document

    def process_document(self, db: Session, document: Document) -> Document:
        text = read_uploaded_text(document.file_path, document.content_type)
        document.source_text = text
        document.status = "processed"

        chunks = chunk_text(text)
        embeddings = self.embedding_service.embed_batch(chunks)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk,
                    citation=f"{document.filename}#chunk-{i+1}",
                    token_count=naive_token_count(chunk),
                    embedding=embedding,
                )
            )

        return document
