from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.jobs import router as jobs_router
from app.schemas import ErrorDetail, JobResponse, JobStatus
from app.services.job_store import job_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mark any stale jobs interrupted by a prior restart as failed on startup
    job_store.recover_interrupted_jobs()
    yield


app = FastAPI(
    title="PolyGen Orchestration Backend",
    version="0.3.0",
    description="Backend API and job orchestration for PolyGen Text-to-3D pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
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


@app.get("/ready", tags=["System"])
def readiness_check():
    """Verifies storage writability, database connectivity, and generator module status."""
    storage_ok = False
    db_ok = False
    generator_linked = False

    try:
        probe_file = settings.storage_path / ".write_probe"
        probe_file.write_text("ok", encoding="utf-8")
        probe_file.unlink()
        storage_ok = True
    except OSError:
        storage_ok = False

    try:
        job_store.list_recent(limit=1)
        db_ok = True
    except Exception:
        db_ok = False

    try:
        import importlib
        importlib.import_module("generator.interface")
        generator_linked = True
    except ImportError:
        generator_linked = False

    ready = storage_ok and db_ok
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if ready else "degraded",
            "checks": {
                "storage_writable": storage_ok,
                "database_connected": db_ok,
                "generator_module_linked": generator_linked,
            },
        },
    )