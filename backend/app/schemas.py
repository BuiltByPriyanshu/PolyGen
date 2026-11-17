from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationOptions(BaseModel):
    target_polycount: int = Field(default=10000, ge=500, le=100000)
    texture_resolution: int = Field(default=1024, ge=256, le=4096)


class JobCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    options: Optional[GenerationOptions] = Field(default_factory=GenerationOptions)

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Prompt cannot be empty or whitespace only.")
        return cleaned


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