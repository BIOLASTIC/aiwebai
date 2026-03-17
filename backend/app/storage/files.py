from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
import json


@dataclass
class FileMetadata:
    file_id: str
    filename: str
    mime_type: str
    size_bytes: int
    storage_path: str


class FileStorage:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, data: bytes, filename: str, mime_type: str) -> str:
        file_id = f"file_{uuid4().hex}"
        path = self.base_dir / file_id
        path.write_bytes(data)
        metadata = {"filename": filename, "mime_type": mime_type}
        for meta_name in [f"{file_id}.meta", f"{file_id}.meta.json"]:
            (self.base_dir / meta_name).write_text(json.dumps(metadata))
        return file_id

    def get_metadata(self, file_id: str) -> FileMetadata:
        path = self.base_dir / file_id
        if not path.exists():
            raise FileNotFoundError(f"File {file_id} not found")
        metadata = {}
        for meta_name in [f"{file_id}.meta.json", f"{file_id}.meta"]:
            metadata_path = self.base_dir / meta_name
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text())
                break
        stat = path.stat()
        return FileMetadata(file_id=file_id, filename=metadata.get("filename", ""), mime_type=metadata.get("mime_type", ""), size_bytes=stat.st_size, storage_path=str(path))
