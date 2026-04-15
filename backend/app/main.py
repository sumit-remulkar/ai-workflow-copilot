from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.evals import router as evals_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.db.session import init_db

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    debug=settings.app_debug,
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.on_event("shutdown")
def on_shutdown() -> None:
    # Langfuse flush is handled per request in the tracing service.
    return None


app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(evals_router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "ok",
        "message": "AI Workflow Copilot starter is running",
        "llm_provider": settings.llm_provider,
    }
