import time
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_end_to_end_job_completes_and_serves_glb():
    create_res = client.post(
        "/api/v1/jobs",
        json={"prompt": "A wooden treasure chest with iron bands"},
    )
    assert create_res.status_code == 202
    job_id = create_res.json()["job_id"]

    # Poll until background task completes
    final_data = None
    for _ in range(10):
        poll_res = client.get(f"/api/v1/jobs/{job_id}")
        assert poll_res.status_code == 200
        final_data = poll_res.json()
        if final_data["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    assert final_data is not None
    assert final_data["status"] == "completed"
    assert final_data["result"]["format"] == "glb"
    assert final_data["result"]["file_size_bytes"] >= 12
    assert final_data["result"]["asset_url"] == f"/assets/{job_id}.glb"

    # Verify the generated .glb file is actually downloadable via /assets
    asset_res = client.get(final_data["result"]["asset_url"])
    assert asset_res.status_code == 200
    assert asset_res.content[:4] == b"glTF"

    # Clean up generated test artifact
    generated_file = settings.storage_path / f"{job_id}.glb"
    if generated_file.exists():
        generated_file.unlink()


def test_generator_failure_sets_failed_status_safely(monkeypatch):
    def fake_failing_generator(*args, **kwargs):
        return {
            "success": False,
            "error_code": "PROVIDER_UNAVAILABLE",
            "diagnostic_detail": "Simulated GPU worker crash with secret_token_123",
        }

    monkeypatch.setattr(
        "app.services.orchestrator.invoke_generator_module",
        fake_failing_generator,
    )

    create_res = client.post(
        "/api/v1/jobs",
        json={"prompt": "A futuristic hoverbike"},
    )
    job_id = create_res.json()["job_id"]

    poll_res = client.get(f"/api/v1/jobs/{job_id}")
    data = poll_res.json()
    assert data["status"] == "failed"
    assert data["result"] is None
    assert data["error"]["code"] == "PROVIDER_UNAVAILABLE"
    # Ensure internal diagnostic/secrets never leak to the browser
    assert "secret_token_123" not in data["error"]["message"]
