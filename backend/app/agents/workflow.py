
from __future__ import annotations

from typing import Any, Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.document import ChatMessage, ChatSession, DocumentChunk
from app.schemas.chat import Citation
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.services.tracing_service import TracingService


class PlannerDecision(BaseModel):
    route: Literal["retrieve", "direct", "clarify"] = "retrieve"
    needs_retrieval: bool = True
    direct_answer: str | None = None
    clarification_question: str | None = None
    reason: str = Field(default="")


class ReviewDecision(BaseModel):
    approved: bool = True
    confidence: float = 0.7
    final_answer: str | None = None
    notes: str = ""


class WorkflowState(TypedDict, total=False):
    question: str
    document_id: int | None
    session_id: int | None
    top_k: int
    trace_id: str
    decision: dict[str, Any]
    retrieved_chunks: list[DocumentChunk]
    answer: str
    citations: list[Citation]
    confidence: float
    review_notes: str


class AgentWorkflow:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMService()
        self.tracer = TracingService()
        self.retrieval = RetrievalService()
        self.graph = self._build_graph()

    def answer_question(
        self,
        question: str,
        document_id: int | None = None,
        session_id: int | None = None,
        top_k: int = 4,
    ) -> tuple[str, list[Citation], int | None, str, float]:
        if session_id is None:
            session = ChatSession(document_id=document_id, title=question[:80] or "Chat session")
            self.db.add(session)
            self.db.flush()
            session_id = session.id

        self.db.add(ChatMessage(session_id=session_id, role="user", content=question))
        trace_id = f"trace_{uuid4().hex[:12]}"

        state: WorkflowState = {
            "question": question,
            "document_id": document_id,
            "session_id": session_id,
            "top_k": top_k,
            "trace_id": trace_id,
        }

        with self.tracer.span(
            "chat-query",
            as_type="span",
            input={"question": question, "document_id": document_id, "session_id": session_id},
            metadata={"provider": self.llm.provider, "model": self.llm.model},
        ):
            result = self.graph.invoke(state)

        answer = result.get("answer", "")
        citations = result.get("citations", [])
        confidence = float(result.get("confidence", 0.0))

        self.db.add(ChatMessage(session_id=session_id, role="assistant", content=answer))
        self.tracer.flush()
        return answer, citations, session_id, trace_id, confidence

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("planner", self._planner_node)
        graph.add_node("retriever", self._retriever_node)
        graph.add_node("draft", self._draft_node)
        graph.add_node("review", self._review_node)

        graph.add_edge(START, "planner")
        graph.add_edge("planner", "retriever")
        graph.add_edge("retriever", "draft")
        graph.add_edge("draft", "review")
        graph.add_edge("review", END)
        return graph.compile()

    def _planner_node(self, state: WorkflowState) -> dict[str, Any]:
        question = state["question"]
        document_id = state.get("document_id")
        system_prompt = (
            "You are a planner for an AI workflow copilot. "
            "Classify the user request into retrieve, direct, or clarify. "
            "Return only JSON with keys: route, needs_retrieval, direct_answer, clarification_question, reason."
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Document ID: {document_id}\n"
            "Use retrieve when the answer should be grounded in the document. "
            "Use direct only for generic questions that do not need evidence. "
            "Use clarify when the request is underspecified."
        )
        fallback = {
            "route": "retrieve" if document_id is not None else "direct",
            "needs_retrieval": document_id is not None,
            "direct_answer": None,
            "clarification_question": None,
            "reason": "fallback",
        }

        with self.tracer.span("planner", as_type="generation", input=user_prompt, model=self.llm.model) as obs:
            payload = self.llm.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, fallback=fallback)
            decision = PlannerDecision.model_validate(payload)
            obs.update(output=decision.model_dump())

        return {"decision": decision.model_dump()}

    def _retriever_node(self, state: WorkflowState) -> dict[str, Any]:
        decision = state.get("decision", {})
        if not decision.get("needs_retrieval", True):
            return {"retrieved_chunks": []}

        with self.tracer.span(
            "retrieval",
            as_type="span",
            input={"question": state["question"], "document_id": state.get("document_id"), "top_k": state.get("top_k", 4)},
        ) as obs:
            chunks = self.retrieval.retrieve(
                self.db,
                state["question"],
                document_id=state.get("document_id"),
                top_k=state.get("top_k", 4),
            )
            obs.update(output={"chunk_ids": [chunk.id for chunk in chunks], "count": len(chunks)})
        return {"retrieved_chunks": chunks}

    def _draft_node(self, state: WorkflowState) -> dict[str, Any]:
        decision = state.get("decision", {})
        chunks = state.get("retrieved_chunks", [])
        citations = [
            Citation(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                snippet=chunk.content[:220],
            )
            for chunk in chunks
        ]

        if decision.get("route") == "clarify":
            answer = decision.get("clarification_question") or "Could you share a bit more detail?"
            confidence = 0.2
            return {"answer": answer, "citations": [], "confidence": confidence}

        if decision.get("route") == "direct" and decision.get("direct_answer"):
            return {"answer": decision["direct_answer"], "citations": [], "confidence": 0.9}

        evidence = "\n\n".join(
            f"[Source {i+1}] Chunk {chunk.chunk_index}: {chunk.content[:900]}"
            for i, chunk in enumerate(chunks)
        ) or "No supporting evidence was retrieved."

        system_prompt = (
            "You are an AI engineer copilot. Write a concise, grounded answer using only the evidence provided. "
            "If evidence is insufficient, say so clearly. Return only JSON with keys: answer, confidence, notes."
        )
        user_prompt = (
            f"Question: {state['question']}\n\n"
            f"Evidence:\n{evidence}\n\n"
            "Keep the answer short, grounded, and practical."
        )
        fallback_answer = (
            "Based on the retrieved evidence, the answer is grounded in the selected document. "
            "Review the sources shown above for the exact supporting text."
        )
        fallback = {"answer": fallback_answer, "confidence": 0.72, "notes": "fallback"}

        with self.tracer.span("answer-generation", as_type="generation", input=user_prompt, model=self.llm.model) as obs:
            payload = self.llm.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, fallback=fallback)
            answer = str(payload.get("answer") or fallback_answer)
            confidence = float(payload.get("confidence") or 0.72)
            obs.update(output={"answer": answer, "confidence": confidence})

        return {"answer": answer, "citations": citations, "confidence": confidence}

    def _review_node(self, state: WorkflowState) -> dict[str, Any]:
        answer = state.get("answer", "")
        chunks = state.get("retrieved_chunks", [])
        citations = state.get("citations", [])

        grounded = bool(chunks) and bool(citations)
        confidence = float(state.get("confidence", 0.0))
        notes = "reviewed"
        if not grounded:
            confidence = min(confidence, 0.35)
            notes = "Low grounding: no retrieved evidence available."
        elif confidence > 0.95:
            confidence = 0.95

        if not answer:
            answer = "I could not produce a reliable answer from the available context."
            confidence = 0.15
            notes = "empty-answer-fallback"

        with self.tracer.span("review", as_type="span", input={"answer_preview": answer[:300], "confidence": confidence}) as obs:
            obs.update(output={"approved": grounded, "confidence": confidence, "notes": notes})

        return {"answer": answer, "confidence": confidence, "review_notes": notes}
