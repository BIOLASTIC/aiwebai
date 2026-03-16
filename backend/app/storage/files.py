from pathlib import Path
from dataclasses import dataclass
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

    def save_bytes(self, data: bytes, filename: str, mime_type: str) -> str:
        file_id = f"file_{uuid4().hex}"
        path = self.base_dir / file_id
        path.write_bytes(data)

        # Save metadata alongside the file
        metadata = {"filename": filename, "mime_type": mime_type}
        metadata_path = self.base_dir / f"{file_id}.meta"
        metadata_path.write_text(json.dumps(metadata))

        return file_id

    def get_metadata(self, file_id: str) -> FileMetadata:
        path = self.base_dir / file_id
        if not path.exists():
            raise FileNotFoundError(f"File {file_id} not found")

        # Read metadata
        metadata_path = self.base_dir / f"{file_id}.meta"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
            filename = metadata.get("filename", "")
            mime_type = metadata.get("mime_type", "")
        else:
            # Fallback if metadata file doesn't exist
            filename = ""
            mime_type = ""

        stat = path.stat()
        return FileMetadata(
            file_id=file_id, filename=filename, mime_type=mime_type, size_bytes=stat.st_size, storage_path=str(path)
        )
