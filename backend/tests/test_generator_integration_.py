import struct
import sys
import types
from pathlib import Path
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.asset_verifier import verify_glb_asset

client = TestClient(app)


def test_adapter_invokes_member2_generator_module(monkeypatch):
    captured_payload = {}

    fake_generator_pkg = types.ModuleType("generator")
    fake_interface_mod = types.ModuleType("generator.interface")

    def mock_generate_3d_asset(payload: dict) -> dict:
        captured_payload.update(payload)
        out = Path(payload["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(struct.pack("<4sII", b"glTF", 2, 12))
        return {
            "success": True,
            "output_path": str(out),
            "format": "glb",
            "metadata": {"polycount": 4200, "has_textures": True},
        }

    fake_interface_mod.generate_3d_asset = mock_generate_3d_asset
    monkeypatch.setitem(sys.modules, "generator", fake_generator_pkg)
    monkeypatch.setitem(sys.modules, "generator.interface", fake_interface_mod)

    res = client.post(
        "/api/v1/jobs",
        json={
            "prompt": "   A   crystal   dragon   statue  ",
            "options": {"target_polycount": 5000, "texture_resolution": 512},
        },
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    poll = client.get(f"/api/v1/jobs/{job_id}").json()
    assert poll["status"] == "completed"
    assert poll["result"]["metadata"]["polycount"] == 4200
    assert poll["result"]["metadata"]["has_textures"] is True
    assert captured_payload["normalized_prompt"] == "A crystal dragon statue"
    assert captured_payload["options"]["target_polycount"] == 5000

    # Cleanup
    artifact = settings.storage_path / f"{job_id}.glb"
    if artifact.exists():
        artifact.unlink()


def test_adapter_catches_generator_crash_safely(monkeypatch):
    fake_generator_pkg = types.ModuleType("generator")
    fake_interface_mod = types.ModuleType("generator.interface")

    def crashing_generator(payload: dict) -> dict:
        raise RuntimeError("Simulated TripoSR CUDA kernel panic")

    fake_interface_mod.generate_3d_asset = crashing_generator
    monkeypatch.setitem(sys.modules, "generator", fake_generator_pkg)
    monkeypatch.setitem(sys.modules, "generator.interface", fake_interface_mod)

    res = client.post("/api/v1/jobs", json={"prompt": "A stone gargoyle"})
    job_id = res.json()["job_id"]

    poll = client.get(f"/api/v1/jobs/{job_id}").json()
    assert poll["status"] == "failed"
    assert poll["error"]["code"] == "PROVIDER_UNAVAILABLE"
    assert "CUDA" not in poll["error"]["message"]


def test_fallback_cube_glb_passes_verification():
    res = client.post("/api/v1/jobs", json={"prompt": "A simple test cube"})
    job_id = res.json()["job_id"]

    poll = client.get(f"/api/v1/jobs/{job_id}").json()
    assert poll["status"] == "completed"
    assert poll["result"]["file_size_bytes"] > 100

    artifact = settings.storage_path / f"{job_id}.glb"
    assert verify_glb_asset(artifact, "glb") == poll["result"]["file_size_bytes"]
    artifact.unlink()