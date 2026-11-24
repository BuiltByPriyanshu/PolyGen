import json
import struct
from pathlib import Path
from app.config import settings


class AssetVerificationError(Exception):
    def __init__(self, code: str, user_message: str, diagnostic: str):
        self.code = code
        self.user_message = user_message
        self.diagnostic = diagnostic
        super().__init__(diagnostic)


def verify_glb_asset(file_path: Path, expected_format: str = "glb") -> int:
    """
    Performs deep verification on a generated .glb asset before publishing:
    1. Confirms agreed format ('glb').
    2. Confirms file exists and is within allowed min/max byte limits.
    3. Validates the 12-byte glTF 2.0 binary header (magic='glTF', version=2, exact total length).
    4. Validates the first chunk is a well-formed JSON chunk containing valid glTF metadata.
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
    if file_size < 20:
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated 3D asset file is empty or incomplete.",
            diagnostic=f"Asset at {file_path} is too small ({file_size} bytes; minimum 20 bytes).",
        )

    if file_size > settings.max_asset_size_bytes:
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated 3D asset exceeded the maximum allowed file size.",
            diagnostic=(
                f"Asset at {file_path} is {file_size} bytes, exceeding limit of "
                f"{settings.max_asset_size_bytes} bytes."
            ),
        )

    with file_path.open("rb") as f:
        header = f.read(12)
        magic, version, declared_length = struct.unpack("<4sII", header)

        if magic != b"glTF":
            raise AssetVerificationError(
                code="ASSET_VERIFICATION_FAILED",
                user_message="Generated file failed 3D asset format verification.",
                diagnostic=f"Invalid .glb header magic bytes {magic!r} in {file_path}.",
            )

        if version != 2:
            raise AssetVerificationError(
                code="ASSET_VERIFICATION_FAILED",
                user_message="Generated 3D asset uses an unsupported glTF version.",
                diagnostic=f"Unsupported glTF version {version} in {file_path}; expected 2.",
            )

        if declared_length != file_size:
            raise AssetVerificationError(
                code="ASSET_VERIFICATION_FAILED",
                user_message="Generated 3D asset appears truncated or corrupted.",
                diagnostic=(
                    f"Declared glTF length ({declared_length} bytes) does not match "
                    f"actual disk size ({file_size} bytes) for {file_path}."
                ),
            )

        # Read first chunk header (must be 'JSON' = 0x4E4F534A)
        chunk_header = f.read(8)
        if len(chunk_header) < 8:
            raise AssetVerificationError(
                code="ASSET_VERIFICATION_FAILED",
                user_message="Generated 3D asset is missing required scene metadata.",
                diagnostic=f"Missing JSON chunk header in {file_path}.",
            )

        json_chunk_len, json_chunk_type = struct.unpack("<II", chunk_header)
        if json_chunk_type != 0x4E4F534A or (20 + json_chunk_len) > file_size:
            raise AssetVerificationError(
                code="ASSET_VERIFICATION_FAILED",
                user_message="Generated 3D asset metadata block is invalid.",
                diagnostic=(
                    f"Invalid JSON chunk type ({hex(json_chunk_type)}) or length "
                    f"({json_chunk_len}) in {file_path}."
                ),
            )

        raw_json = f.read(json_chunk_len)

    try:
        parsed = json.loads(raw_json.decode("utf-8"))
        if not isinstance(parsed, dict) or "asset" not in parsed:
            raise ValueError("Missing top-level 'asset' key in glTF JSON.")
    except Exception as exc:
        raise AssetVerificationError(
            code="ASSET_VERIFICATION_FAILED",
            user_message="Generated 3D asset metadata could not be parsed.",
            diagnostic=f"Corrupted glTF JSON chunk in {file_path}: {exc}",
        )

    return file_size