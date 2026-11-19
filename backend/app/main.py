from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers tables on Base)
from app.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    # ponytail: create_all only adds missing tables; switch to Alembic migrations before changing existing columns.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="KahveCell API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "KahveCell API çalışıyor"}


@app.get("/api/v1/health")
def health():
    return {"success": True, "data": {"status": "ok"}, "error": None}
