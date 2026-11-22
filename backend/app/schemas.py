import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

ALLOWED_TEXTURE_RESOLUTIONS = {256, 512, 1024, 2048}
JOB_ID_PATTERN = re.compile(r"^job_[a-f0-9]{12}$")


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationOptions(BaseModel):
    target_polycount: int = Field(default=10000, ge=500, le=100000)
    texture_resolution: int = Field(default=1024)

    @field_validator("texture_resolution")
    @classmethod
    def validate_texture_resolution(cls, value: int) -> int:
        if value not in ALLOWED_TEXTURE_RESOLUTIONS:
            raise ValueError(
                f"texture_resolution must be one of {sorted(ALLOWED_TEXTURE_RESOLUTIONS)}."
            )
        return value


class JobCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    options: Optional[GenerationOptions] = Field(default_factory=GenerationOptions)

    @field_validator("prompt")
    @classmethod
    def normalize_and_validate_prompt(cls, value: str) -> str:
        # Reject null bytes or ASCII control characters (except standard whitespace)
        if any(ord(ch) < 32 and ch not in ("\n", "\r", "\t") for ch in value):
            raise ValueError("Prompt contains invalid control characters.")

        # Collapse repeated whitespace/newlines into clean single spaces
        normalized = " ".join(value.split())
        if len(normalized) < 3:
            raise ValueError("Prompt must contain at least 3 non-whitespace characters.")
        return normalized


class AssetMetadata(BaseModel):
    polycount: Optional[int] = None
    has_textures: bool = False


class JobResult(BaseModel):
    asset_url: str
    filename: str
    format: str = "glb"
    file_size_bytes: int
    metadata: Optional[AssetMetadata] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    result: Optional[JobResult] = None
    error: Optional[ErrorDetail] = None