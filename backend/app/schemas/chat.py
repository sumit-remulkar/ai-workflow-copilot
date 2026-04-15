from pydantic import BaseModel, Field

class ChatQueryIn(BaseModel):
    question: str = Field(min_length=1)
    document_id: int | None = None
    session_id: int | None = None
    top_k: int = Field(default=4, ge=1, le=10)

class Citation(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    snippet: str

class ChatQueryOut(BaseModel):
    answer: str
    citations: list[Citation] = []
    session_id: int | None = None
    trace_id: str | None = None
    confidence: float = 0.0
