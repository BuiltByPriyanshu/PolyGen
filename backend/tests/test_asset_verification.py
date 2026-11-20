import struct
from pathlib import Path
import pytest

from app.services.asset_verifier import AssetVerificationError, verify_glb_asset


def test_verify_valid_glb_passes(tmp_path: Path):
    glb_file = tmp_path / "valid.glb"
    glb_file.write_bytes(struct.pack("<4sII", b"glTF", 2, 12))

    size = verify_glb_asset(glb_file, "glb")
    assert size == 12


def test_verify_missing_file_fails(tmp_path: Path):
    missing = tmp_path / "does_not_exist.glb"
    with pytest.raises(AssetVerificationError) as exc:
        verify_glb_asset(missing, "glb")
    assert exc.value.code == "ASSET_VERIFICATION_FAILED"


def test_verify_corrupted_header_fails(tmp_path: Path):
    fake_glb = tmp_path / "fake.glb"
    fake_glb.write_bytes(b"NOT_A_GLB_FILE_12345")

    with pytest.raises(AssetVerificationError) as exc:
        verify_glb_asset(fake_glb, "glb")
    assert exc.value.code == "ASSET_VERIFICATION_FAILED"