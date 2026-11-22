import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.schemas import ErrorDetail, JobResponse, JobResult, JobStatus
from app.utils.logger import logger


class JobStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.db_file_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    result_json TEXT,
                    error_json TEXT
                )
                """
            )
            conn.commit()

    def save(self, job: JobResponse) -> None:
        result_json = job.result.model_dump_json() if job.result else None
        error_json = job.error.model_dump_json() if job.error else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, status, created_at, result_json, error_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    status = excluded.status,
                    result_json = excluded.result_json,
                    error_json = excluded.error_json
                """,
                (
                    job.job_id,
                    job.status.value,
                    job.created_at.isoformat(),
                    result_json,
                    error_json,
                ),
            )
            conn.commit()

    def get(self, job_id: str) -> Optional[JobResponse]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def list_recent(self, limit: int = 10) -> List[JobResponse]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_job(r) for r in rows]

    def recover_interrupted_jobs(self) -> int:
        """Marks any jobs stuck in queued/processing after a server crash as failed."""
        interrupted_error = ErrorDetail(
            code="PROVIDER_UNAVAILABLE",
            message="Generation was interrupted by a server restart. Please submit your prompt again.",
        ).model_dump_json()

        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE jobs
                SET status = ?, error_json = ?
                WHERE status IN (?, ?)
                """,
                (
                    JobStatus.FAILED.value,
                    interrupted_error,
                    JobStatus.QUEUED.value,
                    JobStatus.PROCESSING.value,
                ),
            )
            conn.commit()
            recovered = cursor.rowcount

        if recovered > 0:
            logger.warning(
                f"Recovered {recovered} interrupted job(s) and marked them as '{JobStatus.FAILED.value}'."
            )
        return recovered

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> JobResponse:
        result = (
            JobResult.model_validate_json(row["result_json"])
            if row["result_json"]
            else None
        )
        error = (
            ErrorDetail.model_validate_json(row["error_json"])
            if row["error_json"]
            else None
        )
        return JobResponse(
            job_id=row["job_id"],
            status=JobStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            result=result,
            error=error,
        )


job_store = JobStore()