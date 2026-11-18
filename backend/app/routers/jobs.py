import uuid
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.schemas import (
    ErrorDetail,
    JobCreateRequest,
    JobResponse,
    JobStatus,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

# Shared in-memory job registry (replaced by persistent/worker store in Phase 2)
JOBS_DB: Dict[str, JobResponse] = {}


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
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


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job_status(job_id: str):
    job = JOBS_DB.get(job_id)
    if not job:
        error_payload = JobResponse(
            job_id=job_id,
            status=JobStatus.FAILED,
            created_at=datetime.now(timezone.utc),
            result=None,
            error=ErrorDetail(
                code="JOB_NOT_FOUND",
                message=f"No generation job found for ID '{job_id}'.",
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_payload.model_dump(mode="json"),
        )
    return job