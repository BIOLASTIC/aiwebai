import inspect
from pathlib import Path
from backend.app.adapters.base import BaseAdapter


def test_generate_video_signature_accepts_references():
    sig = inspect.signature(BaseAdapter.generate_video)
    assert "reference_files" in sig.parameters
    # Also verify all required parameters are present
    params = sig.parameters
    assert "prompt" in params
    assert "model" in params
    assert "account_id" in params
    assert "reference_files" in params
    assert "options" in params
