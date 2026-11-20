from pathlib import Path
from typing import Tuple


class AssetVerificationError(Exception):
    def __init__(self, code: str, user_message: str, diagnostic: str):
        self.code = code
        self.user_message = user_message
        self.diagnostic = diagnostic
        super().__init__(diagnostic)


def verify_glb_asset(file_path: Path, expected_format: str = "glb") -> int:
    """
    Validates that the generated 3D asset exists, is non-empty,
    matches the agreed .glb format, and starts with valid glTF binary header bytes.
    Returns the verified file size in bytes.
    """
    if expected_format.lower() != "glb":
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated asset format is unsupported.",
            diagnostic=f"Unsupported format '{expected_format}'; expected 'glb'.",
        )

    if not file_path.exists() or not file_path.is_file():
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated 3D asset could not be located on the server.",
            diagnostic=f"Missing asset file at path: {file_path}",
        )

    file_size = file_path.stat().st_size
    if file_size < 12:
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated 3D asset file is empty or corrupted.",
            diagnostic=f"Asset at {file_path} is too small ({file_size} bytes).",
        )

    # Binary glTF (.glb) files always start with the 4-byte ASCII magic 'glTF' (0x46546C67)
    with file_path.open("rb") as f:
        magic = f.read(4)

    if magic != b"glTF":
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated file failed 3D asset format verification.",
            diagnostic=f"Invalid .glb header magic bytes {magic!r} in {file_path}.",
        )

    return file_size