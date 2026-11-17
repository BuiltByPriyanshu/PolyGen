import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.schemas import (
    ErrorDetail,
    JobCreateRequest,
    JobResponse,
    JobStatus,
)

app = FastAPI(
    title="PolyGen Orchestration Backend",
    version="0.1.0",
    description="Backend API and job orchestration for PolyGen Text-to-3D pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage directory exists and mount static route for .glb asset delivery
STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "assets"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(STORAGE_DIR)), name="assets")

# In-memory job store for Day 1 thin PoC
JOBS_DB: Dict[str, JobResponse] = {}


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "polygen-backend"}


@app.post(
    "/api/v1/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Jobs"],
)
def create_job(payload: JobCreateRequest):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        result=None,
        error=None,
    )
    JOBS_DB[job_id] = job
    return job


@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobResponse,
    tags=["Jobs"],
)
def get_job_status(job_id: str):
    job = JOBS_DB.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code="JOB_NOT_FOUND",
                message=f"No generation job found for ID '{job_id}'.",
            ).model_dump(),
        )
    return job