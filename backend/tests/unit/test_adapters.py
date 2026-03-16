import inspect
from pathlib import Path
from backend.app.adapters.base import BaseAdapter


def test_generate_video_signature_accepts_references():
    sig = inspect.signature(BaseAdapter.generate_video)
    assert "reference_files" in sig.parameters
