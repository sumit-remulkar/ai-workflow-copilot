from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.workflow import AgentWorkflow
from app.schemas.chat import Citation


class AgentService:
    def answer_question(
        self,
        db: Session,
        question: str,
        document_id: int | None = None,
        session_id: int | None = None,
        top_k: int = 4,
    ) -> tuple[str, list[Citation], int | None, str, float]:
        workflow = AgentWorkflow(db)
        return workflow.answer_question(
            question=question,
            document_id=document_id,
            session_id=session_id,
            top_k=top_k,
        )
