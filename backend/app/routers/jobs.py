import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse

from app.schemas import (
    ErrorDetail,
    GenerationOptions,
    JobCreateRequest,
    JobResponse,
    JobStatus,
)
from app.services.orchestrator import get_job, register_job, run_generation_job

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_job(payload: JobCreateRequest, background_tasks: BackgroundTasks):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = register_job(job_id)

    options = payload.options or GenerationOptions()
    background_tasks.add_task(
        run_generation_job,
        job_id,
        payload.prompt,
        options,
    )
    return job


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job_status(job_id: str):
    job = get_job(job_id)
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