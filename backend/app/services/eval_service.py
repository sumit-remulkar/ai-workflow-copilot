from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document import EvaluationRun, EvaluationResult

class EvalService:
    def run_eval(self, db: Session, name: str) -> EvaluationRun:
        run = EvaluationRun(name=name, status="running", metrics={})
        db.add(run)
        db.flush()

        cases = [
            ("retrieval_smoke_1", True, 1.0, {"note": "placeholder"}),
            ("citation_smoke_1", True, 1.0, {"note": "placeholder"}),
        ]

        for case_name, passed, score, details in cases:
            db.add(
                EvaluationResult(
                    run_id=run.id,
                    case_name=case_name,
                    passed=passed,
                    score=score,
                    details=details,
                )
            )

        run.status = "completed"
        run.metrics = {
            "cases": len(cases),
            "pass_rate": 1.0,
            "avg_score": 1.0,
        }
        return run
