from pydantic import BaseModel, Field

class EvalRunIn(BaseModel):
    name: str = Field(default="default-eval-suite", min_length=1)

class EvalRunOut(BaseModel):
    run_id: int
    status: str
    metrics: dict | None = None
