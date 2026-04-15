from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def init_db() -> None:
    from app.db.base import Base
    from app import models  # noqa: F401

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
