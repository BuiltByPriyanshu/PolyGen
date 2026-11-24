import json
import struct
from pathlib import Path
import pytest

from app.config import settings
from app.services.asset_verifier import AssetVerificationError, verify_glb_asset


def _build_valid_glb(gltf_obj: dict) -> bytes:
    json_bytes = json.dumps(gltf_obj).encode("utf-8")
    pad = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b" " * pad
    total_len = 12 + 8 + len(json_bytes)
    header = struct.pack("<4sII", b"glTF", 2, total_len)
    chunk_hdr = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    return header + chunk_hdr + json_bytes


def test_verify_valid_glb_passes(tmp_path: Path):
    glb_file = tmp_path / "valid.glb"
    raw = _build_valid_glb({"asset": {"version": "2.0"}, "meshes": []})
    glb_file.write_bytes(raw)

    size = verify_glb_asset(glb_file, "glb")
    assert size == len(raw)


def test_verify_missing_file_fails(tmp_path: Path):
    missing = tmp_path / "does_not_exist.glb"
    with pytest.raises(AssetVerificationError) as exc:
        verify_glb_asset(missing, "glb")
    assert exc.value.code == "ASSET_VERIFICATION_FAILED"


def test_verify_corrupted_header_fails(tmp_path: Path):
    fake_glb = tmp_path / "fake.glb"
    fake_glb.write_bytes(b"NOT_A_GLB_FILE_1234567890")

    with pytest.raises(AssetVerificationError) as exc:
        verify_glb_asset(fake_glb, "glb")
    assert exc.value.code == "ASSET_VERIFICATION_FAILED"


def test_verify_truncated_glb_fails(tmp_path: Path):
    glb_file = tmp_path / "truncated.glb"
    raw = _build_valid_glb({"asset": {"version": "2.0"}})
    # Strip last 4 bytes so declared_length != actual disk size
    glb_file.write_bytes(raw[:-4])

    with pytest.raises(AssetVerificationError) as exc:
        verify_glb_asset(glb_file, "glb")
    assert "truncated" in exc.value.user_message.lower()


def test_verify_oversized_glb_fails(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "max_asset_size_mb", 0)
    glb_file = tmp_path / "oversized.glb"
    glb_file.write_bytes(_build_valid_glb({"asset": {"version": "2.0"}}))

    with pytest.raises(AssetVerificationError) as exc:
        verify_glb_asset(glb_file, "glb")
    assert "maximum allowed file size" in exc.value.user_message.lower()