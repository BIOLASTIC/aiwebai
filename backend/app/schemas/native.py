from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union, Any, Dict, Literal


class ImageGenerationRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: Optional[str] = "gemini-image-latest"
    reference_file_ids: list[str] = []
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = "url"
    user: Optional[str] = None


class VideoGenerationRequest(BaseModel):
    prompt: str
    account_id: int | None = None
    provider: str | None = None
    model: str | None = None
    reference_file_ids: list[str] = []
    duration: int | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    fps: int | None = None
    metadata: dict | None = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    result_url: Optional[str] = None
    error: Optional[str] = None


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
