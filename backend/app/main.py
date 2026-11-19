from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="KahveCell API", version="0.1.0")

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
