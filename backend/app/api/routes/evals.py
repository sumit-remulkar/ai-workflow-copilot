from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.eval import EvalRunIn, EvalRunOut
from app.models.document import EvaluationRun
from app.services.eval_service import EvalService

router = APIRouter(tags=["evals"])
eval_service = EvalService()

@router.post("/evals/run", response_model=EvalRunOut)
def run_evals(payload: EvalRunIn, db: Session = Depends(get_db)) -> EvalRunOut:
    run = eval_service.run_eval(db, payload.name)
    db.commit()
    db.refresh(run)
    return EvalRunOut(run_id=run.id, status=run.status, metrics=run.metrics)

@router.get("/evals/results/{run_id}")
def get_eval_results(run_id: int, db: Session = Depends(get_db)) -> dict:
    run = db.get(EvaluationRun, run_id)
    if not run:
        return {"detail": "Run not found"}
    return {
        "run_id": run.id,
        "name": run.name,
        "status": run.status,
        "metrics": run.metrics,
    }
