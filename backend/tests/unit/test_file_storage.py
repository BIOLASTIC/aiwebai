from pathlib import Path
from uuid import uuid4
from backend.app.storage.files import FileStorage, FileMetadata


def test_store_and_lookup_file(tmp_path):
    storage = FileStorage(base_dir=tmp_path)
    file_id = storage.save_bytes(b"abc", filename="ref.png", mime_type="image/png")
    meta = storage.get_metadata(file_id)
    assert meta.filename == "ref.png"
    assert meta.mime_type == "image/png"
