from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatQueryIn, ChatQueryOut
from app.services.agent_service import AgentService

router = APIRouter(tags=["chat"])
agent_service = AgentService()

@router.post("/chat/query", response_model=ChatQueryOut)
def chat_query(payload: ChatQueryIn, db: Session = Depends(get_db)) -> ChatQueryOut:
    answer, citations, session_id, trace_id, confidence = agent_service.answer_question(
        db=db,
        question=payload.question,
        document_id=payload.document_id,
        session_id=payload.session_id,
        top_k=payload.top_k,
    )
    db.commit()
    return ChatQueryOut(
        answer=answer,
        citations=citations,
        session_id=session_id,
        trace_id=trace_id,
        confidence=confidence,
    )
