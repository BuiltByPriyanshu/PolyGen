from pathlib import Path
import pytest
from app.config import settings
from app.services.job_store import job_store


@pytest.fixture(autouse=True)
def isolate_test_storage(tmp_path: Path, monkeypatch):
    test_assets = tmp_path / "assets"
    test_assets.mkdir(parents=True, exist_ok=True)
    test_db = tmp_path / "test_jobs.db"

    monkeypatch.setattr(settings, "asset_storage_dir", str(test_assets))
    monkeypatch.setattr(job_store, "db_path", test_db)
    job_store._init_db()
    yield