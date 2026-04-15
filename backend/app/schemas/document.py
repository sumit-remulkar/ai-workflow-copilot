from pydantic import BaseModel
from typing import Any

class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    status: str
    checksum: str | None = None
    metadata: dict[str, Any] | None = None

class ChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    citation: str | None = None
    token_count: int = 0
