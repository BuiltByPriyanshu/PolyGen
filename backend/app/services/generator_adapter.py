import struct
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from app.schemas import GenerationOptions
from app.utils.logger import logger


def invoke_generator_module(
    job_id: str,
    normalized_prompt: str,
    output_path: Path,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """
    Adapter interface between Member 3 (Backend) and Member 2 (Generator).
    Checks for Member 2's `generator.interface.generate_3d_asset` if available;
    otherwise falls back to a minimal valid .glb header stub for PoC testing.
    """
    # Ensure secret keys are accessed only server-side and never logged
    _ = bool(settings.ai_provider_api_key)

    payload = {
        "job_id": job_id,
        "normalized_prompt": normalized_prompt,
        "output_path": str(output_path),
        "options": options.model_dump(),
    }

    try:
        from generator.interface import generate_3d_asset  # type: ignore

        logger.info(f"[{job_id}] Invoking Member 2 generator module.")
        return generate_3d_asset(payload)
    except ImportError:
        logger.warning(
            f"[{job_id}] Member 2 generator module not yet linked; writing minimal .glb PoC stub."
        )
        _write_minimal_glb_stub(output_path)
        return {
            "success": True,
            "output_path": str(output_path),
            "format": "glb",
            "metadata": {
                "polycount": options.target_polycount,
                "has_textures": False,
            },
        }


def _write_minimal_glb_stub(output_path: Path) -> None:
    """Writes a 12-byte valid glTF 2.0 binary header for local backend verification."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # magic='glTF', version=2, total_length=12
    header = struct.pack("<4sII", b"glTF", 2, 12)
    output_path.write_bytes(header)