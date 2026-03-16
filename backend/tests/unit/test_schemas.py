import pytest
from app.schemas.native import VideoGenerationRequest, ImageGenerationRequest


def test_video_request_schema():
    req = VideoGenerationRequest(prompt="hi", reference_file_ids=["file_1"], model="vid")
    assert req.reference_file_ids == ["file_1"]


def test_image_request_schema():
    req = ImageGenerationRequest(prompt="hi", reference_file_ids=["file_1"], model="img")
    assert req.reference_file_ids == ["file_1"]
