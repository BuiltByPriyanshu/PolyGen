import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

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
from app.services.job_store import job_store
from app.utils.logger import logger

# Single-worker semaphore prevents parallel GPU OOM crashes when multiple jobs arrive
_GENERATION_SEMAPHORE = asyncio.Semaphore(1)


def register_job(job_id: str) -> JobResponse:
    job = JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        result=None,
        error=None,
    )
    job_store.save(job)
    logger.info(f"[{job_id}] Job registered with status='{JobStatus.QUEUED.value}'.")
    return job


def get_job(job_id: str) -> Optional[JobResponse]:
    return job_store.get(job_id)


def list_recent_jobs(limit: int = 10) -> List[JobResponse]:
    return job_store.list_recent(limit=limit)


def _cleanup_partial_asset(file_path: Path, job_id: str) -> None:
    """Removes incomplete or invalid .glb files so corrupted artifacts are never kept."""
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info(f"[{job_id}] Cleaned up partial/invalid asset at {file_path}.")
    except OSError as exc:
        logger.warning(f"[{job_id}] Could not remove partial asset {file_path}: {exc}")


async def run_generation_job(
    job_id: str,
    normalized_prompt: str,
    options: GenerationOptions,
) -> None:
    """
    Executes the Text-to-3D pipeline asynchronously in FIFO order:
    queued -> processing -> completed (only after asset verification) | failed.
    """
    job = job_store.get(job_id)
    if not job:
        logger.error(f"[{job_id}] Background worker could not find job record.")
        return

    filename = f"{job_id}.glb"
    output_path = settings.storage_path / filename

    async with _GENERATION_SEMAPHORE:
        job.status = JobStatus.PROCESSING
        job_store.save(job)
        logger.info(f"[{job_id}] Transitioned to status='{JobStatus.PROCESSING.value}'.")

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
                _cleanup_partial_asset(output_path, job_id)
                job.status = JobStatus.FAILED
                job.error = ErrorDetail(
                    code=error_code,
                    message="3D asset generation failed. Please refine your prompt and try again.",
                )
                job_store.save(job)
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
            job_store.save(job)
            logger.info(
                f"[{job_id}] Asset verified ({file_size} bytes). Transitioned to '{JobStatus.COMPLETED.value}'."
            )

        except asyncio.TimeoutError:
            logger.error(
                f"[{job_id}] Generation timed out after {settings.job_timeout_seconds}s."
            )
            _cleanup_partial_asset(output_path, job_id)
            job.status = JobStatus.FAILED
            job.error = ErrorDetail(
                code="GENERATION_TIMEOUT",
                message="3D asset generation exceeded the allowed time limit. Please try again.",
            )
            job_store.save(job)

        except AssetVerificationError as ave:
            logger.error(f"[{job_id}] Asset verification failed: {ave.diagnostic}")
            _cleanup_partial_asset(output_path, job_id)
            job.status = JobStatus.FAILED
            job.error = ErrorDetail(
                code=ave.code,
                message=ave.user_message,
            )
            job_store.save(job)

        except Exception as exc:
            logger.exception(f"[{job_id}] Unexpected orchestration error: {exc}")
            _cleanup_partial_asset(output_path, job_id)
            job.status = JobStatus.FAILED
            job.error = ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred while processing your 3D asset.",
            )
            job_store.save(job)