from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app import models
from app.routers import (
    cases,
    persons,
    evidence,
    diary,
    search,
    auth,
    chargesheet
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CINTRA API",
    version="1.0.0"
)


# ---------- CORS ----------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ---------- ROUTERS ----------

app.include_router(cases.router)
app.include_router(persons.router)
app.include_router(evidence.router)
app.include_router(diary.router)
app.include_router(search.router)
app.include_router(auth.router)
app.include_router(chargesheet.router)


# ---------- UPLOAD DIRECTORIES ----------

BASE_DIR = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = BASE_DIR / "uploads" / "evidence"
GENERATED_DIR = BASE_DIR / "uploads" / "generated"

EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ---------- EVIDENCE FILES ----------

app.mount(
    "/uploads/evidence",
    StaticFiles(directory=EVIDENCE_DIR),
    name="evidence-files"
)


# ---------- GENERATED CHARGESHEETS ----------

app.mount(
    "/uploads/generated",
    StaticFiles(directory=GENERATED_DIR),
    name="generated-files"
)


# ---------- ROOT ----------

@app.get("/")
def root():
    return {
        "message": "CINTRA API is running"
    }