from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentOut, ChunkOut
from app.services.document_service import DocumentService

router = APIRouter(tags=["documents"])
document_service = DocumentService()

@router.post("/documents/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    document = document_service.save_upload(
        db=db,
        file_bytes=file_bytes,
        filename=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
    )
    document_service.process_document(db, document)
    db.commit()
    db.refresh(document)
    return document

@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/documents/{document_id}/chunks", response_model=list[ChunkOut])
def get_document_chunks(document_id: int, db: Session = Depends(get_db)) -> list[DocumentChunk]:
    chunks = db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc())
    ).scalars().all()
    return chunks
