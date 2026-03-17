from typing import Any, Dict
import time

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.api_key_auth import get_user_by_api_key
from backend.app.config import BASE_DIR
from backend.app.db.engine import get_db
from backend.app.db.models import UploadedFile, User
from backend.app.storage.files import FileStorage

router = APIRouter(tags=["openai-files"])


class FileResponse(BaseModel):
    id: str
    object: str = "file"
    bytes: int
    created_at: int
    filename: str
    purpose: str


@router.post("/v1/files", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), purpose: str = "assistants", user: User = Depends(get_user_by_api_key), db: AsyncSession = Depends(get_db)):
    storage = FileStorage(base_dir=BASE_DIR / "uploads")
    content = await file.read()
    file_id = storage.save_bytes(content, file.filename, file.content_type or "application/octet-stream")
    metadata = storage.get_metadata(file_id)
    uploaded_file = UploadedFile(
        file_id=file_id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        storage_path=metadata.storage_path,
        purpose=purpose,
        owner_user_id=user.id,
    )
    db.add(uploaded_file)
    await db.commit()
    return FileResponse(id=file_id, bytes=len(content), created_at=int(time.time()), filename=file.filename, purpose=purpose)


@router.get("/v1/files", response_model=Dict[str, Any])
async def list_files(user: User = Depends(get_user_by_api_key), db: AsyncSession = Depends(get_db)):
    files = (await db.execute(select(UploadedFile).filter(UploadedFile.owner_user_id == user.id))).scalars().all()
    return {
        "object": "list",
        "data": [
            {
                "id": record.file_id,
                "object": "file",
                "bytes": record.size_bytes,
                "created_at": int(record.created_at.timestamp()) if record.created_at else int(time.time()),
                "filename": record.filename,
                "purpose": record.purpose,
            }
            for record in files
        ],
    }
