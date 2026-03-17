from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: Optional[str] = "gemini-image-latest"
    reference_file_ids: list[str] = Field(default_factory=list)
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = "url"
    user: Optional[str] = None


class VideoGenerationRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: str | None = None
    reference_file_ids: list[str] = Field(default_factory=list)
    duration: int | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    fps: int | None = None
    metadata: dict[str, Any] | None = None


class MusicGenerationRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: str | None = None
    reference_file_ids: list[str] = Field(default_factory=list)
    style: str | None = None
    metadata: dict[str, Any] | None = None


class ResearchRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: str | None = None
    reference_file_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    result_url: Optional[str] = None
    error: Optional[str] = None


class VideoResult(BaseModel):
    video_paths: list[Path] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelCapability(BaseModel):
    text: bool = True
    images: bool = False
    image_edit: bool = False
    video: bool = False
    music: bool = False
    research: bool = False
    extensions: bool = False
    streaming: bool = True
    code_exec: bool = False
    thinking: bool = False
    max_tokens: Optional[int] = None
