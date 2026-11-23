from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_valid_job_returns_queued():
    res = client.post(
        "/api/v1/jobs",
        json={"prompt": "A medieval broadsword with a blue sapphire hilt"},
    )
    assert res.status_code == 202
    data = res.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "queued"
    assert data["result"] is None
    assert data["error"] is None


def test_reject_blank_prompt_with_contract_error():
    res = client.post("/api/v1/jobs", json={"prompt": "   "})
    assert res.status_code == 422
    data = res.json()
    assert data["status"] == "failed"
    assert data["error"]["code"] == "INVALID_PROMPT"


def test_get_unknown_job_returns_404_contract_error():
    res = client.get("/api/v1/jobs/job_000000000000")
    assert res.status_code == 404
    data = res.json()
    assert data["status"] == "failed"
    assert data["error"]["code"] == "JOB_NOT_FOUND"