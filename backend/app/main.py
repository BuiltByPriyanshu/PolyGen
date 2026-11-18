from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.jobs import router as jobs_router
from app.schemas import ErrorDetail, JobResponse, JobStatus

app = FastAPI(
    title="PolyGen Orchestration Backend",
    version="0.2.0",
    description="Backend API and job orchestration for PolyGen Text-to-3D pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_response = JobResponse(
        job_id="unassigned",
        status=JobStatus.FAILED,
        created_at=datetime.now(timezone.utc),
        result=None,
        error=ErrorDetail(
            code="INVALID_PROMPT",
            message="Prompt is empty, malformed, or contains unsupported generation options.",
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json"),
    )


app.mount("/assets", StaticFiles(directory=str(settings.storage_path)), name="assets")
app.include_router(jobs_router)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "polygen-backend",
        "env": settings.app_env,
    }