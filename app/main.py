from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from .database import Base, engine
from .routers import auth, blogs


def _ensure_schema() -> None:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "users" in tables:
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "oauth_provider" not in columns:
            Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


_ensure_schema()

app = FastAPI(title="Blog API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(blogs.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
