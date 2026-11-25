import time
from pathlib import Path
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import JobResponse, JobStatus
from app.services.job_store import JobStore
from app.utils.logger import logger

client = TestClient(app)


def test_generation_timeout_sets_timeout_error_and_cleans_up(monkeypatch):
    monkeypatch.setattr(settings, "job_timeout_seconds", 0.05)

    def slow_generator(job_id, normalized_prompt, output_path: Path, options):
        # Write a partial file before timing out to prove cleanup runs
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"glTF_PARTIAL")
        time.sleep(0.25)
        return {"success": True, "output_path": str(output_path), "format": "glb"}

    monkeypatch.setattr(
        "app.services.orchestrator.invoke_generator_module",
        slow_generator,
    )

    res = client.post("/api/v1/jobs", json={"prompt": "A complex clockwork citadel"})
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    poll = client.get(f"/api/v1/jobs/{job_id}").json()
    assert poll["status"] == "failed"
    assert poll["result"] is None
    assert poll["error"]["code"] == "GENERATION_TIMEOUT"

    # Confirm partial file was deleted on timeout
    assert not (settings.storage_path / f"{job_id}.glb").exists()


def test_generator_claims_success_but_asset_missing_fails_verification(monkeypatch):
    def lying_generator(job_id, normalized_prompt, output_path: Path, options):
        # Returns success=True without writing any file to disk
        return {
            "success": True,
            "output_path": str(output_path),
            "format": "glb",
            "metadata": {"polycount": 1000, "has_textures": False},
        }

    monkeypatch.setattr(
        "app.services.orchestrator.invoke_generator_module",
        lying_generator,
    )

    res = client.post("/api/v1/jobs", json={"prompt": "A floating crystal island"})
    job_id = res.json()["job_id"]

    poll = client.get(f"/api/v1/jobs/{job_id}").json()
    assert poll["status"] == "failed"
    assert poll["result"] is None
    assert poll["error"]["code"] == "ASSET_VERIFICATION_FAILED"


def test_reject_invalid_job_id_format():
    res = client.get("/api/v1/jobs/../../etc/passwd")
    assert res.status_code == 404

    res_bad_id = client.get("/api/v1/jobs/not_a_valid_job_id")
    assert res_bad_id.status_code == 404
    data = res_bad_id.json()
    assert data["status"] == "failed"
    assert data["error"]["code"] == "JOB_NOT_FOUND"


def test_reject_unsupported_texture_resolution():
    res = client.post(
        "/api/v1/jobs",
        json={
            "prompt": "A marble chess knight",
            "options": {"target_polycount": 5000, "texture_resolution": 777},
        },
    )
    assert res.status_code == 422
    data = res.json()
    assert data["status"] == "failed"
    assert data["error"]["code"] == "INVALID_PROMPT"


def test_secret_redacting_log_filter_masks_api_key(monkeypatch, caplog):
    monkeypatch.setattr(settings, "ai_provider_api_key", "sk-super-secret-polygen-key-999")
    with caplog.at_level("INFO", logger="polygen.backend"):
        logger.info("Connecting to upstream with key sk-super-secret-polygen-key-999")

    assert "sk-super-secret-polygen-key-999" not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_sqlite_store_recovers_interrupted_jobs(tmp_path: Path):
    from datetime import datetime, timezone

    temp_db = tmp_path / "test_recovery.db"
    store = JobStore(db_path=temp_db)

    stale_job = JobResponse(
        job_id="job_111122223333",
        status=JobStatus.PROCESSING,
        created_at=datetime.now(timezone.utc),
        result=None,
        error=None,
    )
    store.save(stale_job)

    recovered_count = store.recover_interrupted_jobs()
    assert recovered_count == 1

    recovered = store.get("job_111122223333")
    assert recovered is not None
    assert recovered.status == JobStatus.FAILED
    assert recovered.error is not None
    assert recovered.error.code == "PROVIDER_UNAVAILABLE"