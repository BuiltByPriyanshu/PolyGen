import json
import struct
import sys
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from app.schemas import GenerationOptions
from app.utils.logger import logger

# Ensure repository root is importable so `generator.interface` resolves cleanly
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def invoke_generator_module(
    job_id: str,
    normalized_prompt: str,
    output_path: Path,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """
    Adapter interface between Member 3 (Backend) and Member 2 (Generator).
    Invokes `generator.interface.generate_3d_asset(payload)` when present;
    otherwise generates a valid 3D unit-cube .glb mesh for local integration testing.
    """
    # Keep secret key server-side only; never log its value
    _ = bool(settings.ai_provider_api_key)

    payload = {
        "job_id": job_id,
        "normalized_prompt": normalized_prompt,
        "output_path": str(output_path),
        "options": options.model_dump(),
    }

    try:
        from generator.interface import generate_3d_asset  # type: ignore

        logger.info(f"[{job_id}] Invoking Member 2 generator module (generator.interface).")
        result = generate_3d_asset(payload)
        if not isinstance(result, dict):
            return {
                "success": False,
                "error_code": "PROVIDER_UNAVAILABLE",
                "diagnostic_detail": "Generator returned a non-dictionary response.",
            }
        return result
    except ImportError:
        logger.warning(
            f"[{job_id}] generator.interface not found; generating valid 3D cube .glb test asset."
        )
        _write_valid_cube_glb(output_path)
        return {
            "success": True,
            "output_path": str(output_path),
            "format": "glb",
            "metadata": {
                "polycount": 12,
                "has_textures": False,
            },
        }
    except Exception as exc:
        logger.exception(f"[{job_id}] Unhandled exception inside generator module: {exc}")
        return {
            "success": False,
            "error_code": "PROVIDER_UNAVAILABLE",
            "diagnostic_detail": f"Generator raised exception: {type(exc).__name__}: {exc}",
        }


def _write_valid_cube_glb(output_path: Path) -> None:
    """
    Writes a valid, self-contained glTF 2.0 binary (.glb) containing a 3D unit cube
    (8 vertices, 12 triangles) so Three.js / React-Three-Fiber can render real geometry.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 8 corner vertices of a 1x1x1 cube centered at origin (float32 x 3)
    vertices = [
        -0.5, -0.5,  0.5,
         0.5, -0.5,  0.5,
         0.5,  0.5,  0.5,
        -0.5,  0.5,  0.5,
        -0.5, -0.5, -0.5,
         0.5, -0.5, -0.5,
         0.5,  0.5, -0.5,
        -0.5,  0.5, -0.5,
    ]
    # 12 triangles (36 uint16 indices)
    indices = [
        0, 1, 2, 2, 3, 0,  # front
        1, 5, 6, 6, 2, 1,  # right
        7, 6, 5, 5, 4, 7,  # back
        4, 0, 3, 3, 7, 4,  # left
        4, 5, 1, 1, 0, 4,  # bottom
        3, 2, 6, 6, 7, 3,  # top
    ]

    vertex_bytes = struct.pack(f"<{len(vertices)}f", *vertices)
    index_bytes = struct.pack(f"<{len(indices)}H", *indices)
    bin_data = vertex_bytes + index_bytes
    # Pad BIN chunk to 4-byte alignment with 0x00
    bin_pad = (4 - (len(bin_data) % 4)) % 4
    bin_data += b"\x00" * bin_pad

    gltf_json = {
        "asset": {"version": "2.0", "generator": "PolyGen-Backend-Stub"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "PolyGenFallbackCube"}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "mode": 4,
                    }
                ]
            }
        ],
        "buffers": [{"byteLength": len(bin_data)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(vertex_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(vertex_bytes), "byteLength": len(index_bytes), "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 8,
                "type": "VEC3",
                "min": [-0.5, -0.5, -0.5],
                "max": [0.5, 0.5, 0.5],
            },
            {
                "bufferView": 1,
                "componentType": 5123,
                "count": 36,
                "type": "SCALAR",
            },
        ],
    }

    json_bytes = json.dumps(gltf_json, separators=(",", ":")).encode("utf-8")
    # Pad JSON chunk to 4-byte alignment with spaces (0x20) per glTF 2.0 spec
    json_pad = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b" " * json_pad

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
    header = struct.pack("<4sII", b"glTF", 2, total_length)
    json_chunk_header = struct.pack("<II", len(json_bytes), 0x4E4F534A)  # 'JSON'
    bin_chunk_header = struct.pack("<II", len(bin_data), 0x004E4942)    # 'BIN\0'

    output_path.write_bytes(
        header + json_chunk_header + json_bytes + bin_chunk_header + bin_data
    )