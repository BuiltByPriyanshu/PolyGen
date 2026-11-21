import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional

from app.config import settings
from app.schemas import (
    AssetMetadata,
    ErrorDetail,
    GenerationOptions,
    JobResponse,
    JobResult,
    JobStatus,
)
from app.services.asset_verifier import AssetVerificationError, verify_glb_asset
from app.services.generator_adapter import invoke_generator_module
from app.utils.logger import logger

# Shared in-memory job store
JOBS_DB: Dict[str, JobResponse] = {}


def register_job(job_id: str) -> JobResponse:
    job = JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        result=None,
        error=None,
    )
    JOBS_DB[job_id] = job
    logger.info(f"[{job_id}] Job registered with status='{JobStatus.QUEUED.value}'.")
    return job


def get_job(job_id: str) -> Optional[JobResponse]:
    return JOBS_DB.get(job_id)


async def run_generation_job(
    job_id: str,
    normalized_prompt: str,
    options: GenerationOptions,
) -> None:
    """
    Executes the Text-to-3D pipeline asynchronously in the background:
    queued -> processing -> completed (only after asset verification) | failed.
    """
    job = JOBS_DB.get(job_id)
    if not job:
        logger.error(f"[{job_id}] Background worker could not find job record.")
        return

    job.status = JobStatus.PROCESSING
    logger.info(f"[{job_id}] Transitioned to status='{JobStatus.PROCESSING.value}'.")

    filename = f"{job_id}.glb"
    output_path = settings.storage_path / filename

    try:
        gen_response = await asyncio.wait_for(
            asyncio.to_thread(
                invoke_generator_module,
                job_id,
                normalized_prompt,
                output_path,
                options,
            ),
            timeout=settings.job_timeout_seconds,
        )

        if not isinstance(gen_response, dict) or not gen_response.get("success"):
            error_code = (
                gen_response.get("error_code", "PROVIDER_UNAVAILABLE")
                if isinstance(gen_response, dict)
                else "PROVIDER_UNAVAILABLE"
            )
            diagnostic = (
                gen_response.get("diagnostic_detail", "Generator returned failure.")
                if isinstance(gen_response, dict)
                else "Invalid non-dict response from generator module."
            )
            logger.error(f"[{job_id}] Generator failed ({error_code}): {diagnostic}")
            job.status = JobStatus.FAILED
            job.error = ErrorDetail(
                code=error_code,
                message="3D asset generation failed. Please refine your prompt and try again.",
            )
            return

        asset_format = gen_response.get("format", "glb")
        file_size = verify_glb_asset(output_path, expected_format=asset_format)

        raw_meta = gen_response.get("metadata") or {}
        metadata = AssetMetadata(
            polycount=raw_meta.get("polycount"),
            has_textures=bool(raw_meta.get("has_textures", False)),
        )

        job.result = JobResult(
            asset_url=f"/assets/{filename}",
            filename=filename,
            format="glb",
            file_size_bytes=file_size,
            metadata=metadata,
        )
        job.status = JobStatus.COMPLETED
        logger.info(
            f"[{job_id}] Asset verified ({file_size} bytes). Transitioned to '{JobStatus.COMPLETED.value}'."
        )

    except asyncio.TimeoutError:
        logger.error(
            f"[{job_id}] Generation timed out after {settings.job_timeout_seconds}s."
        )
        job.status = JobStatus.FAILED
        job.error = ErrorDetail(
            code="GENERATION_TIMEOUT",
            message="3D asset generation exceeded the allowed time limit. Please try again.",
        )

    except AssetVerificationError as ave:
        logger.error(f"[{job_id}] Asset verification failed: {ave.diagnostic}")
        job.status = JobStatus.FAILED
        job.error = ErrorDetail(
            code=ave.code,
            message=ave.user_message,
        )

    except Exception as exc:
        logger.exception(f"[{job_id}] Unexpected orchestration error: {exc}")
        job.status = JobStatus.FAILED
        job.error = ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred while processing your 3D asset.",
        )