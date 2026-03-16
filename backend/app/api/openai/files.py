from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Any, Dict
import time
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.auth.api_key_auth import get_user_by_api_key
from backend.app.db.models import User, UploadedFile
from backend.app.storage.files import FileStorage
from backend.app.db.engine import get_db
from pydantic import BaseModel

router = APIRouter(tags=["openai-files"])


class FileResponse(BaseModel):
    id: str
    object: str = "file"
    bytes: int
    created_at: int
    filename: str
    purpose: str


@router.post("/v1/files", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = "fine-tune",
    user: User = Depends(get_user_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.config import BASE_DIR

    storage_dir = BASE_DIR / "uploads"
    storage = FileStorage(base_dir=storage_dir)

    content = await file.read()

    # Save file using FileStorage
    file_id = storage.save_bytes(content, file.filename, file.content_type or "application/octet-stream")

    # Save metadata to database
    uploaded_file = UploadedFile(
        file_id=file_id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size=len(content),
        purpose=purpose,
        user_id=user.id,
    )
    db.add(uploaded_file)
    await db.commit()
    await db.refresh(uploaded_file)

    return FileResponse(
        id=file_id, bytes=len(content), created_at=int(time.time()), filename=file.filename, purpose=purpose
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return FileResponse(
        id=file_id, bytes=len(content), created_at=int(time.time()), filename=file.filename, purpose=purpose
    )


@router.get("/v1/files", response_model=Dict[str, Any])
async def list_files(user: User = Depends(get_user_by_api_key), db: AsyncSession = Depends(get_db)):
    # Get uploaded files for the current user
    result = await db.execute(select(UploadedFile).filter(UploadedFile.user_id == user.id))
    files = result.scalars().all()

    file_responses = []
    for file_record in files:
        file_responses.append(
            {
                "id": file_record.file_id,
                "object": "file",
                "bytes": file_record.size,
                "created_at": int(file_record.created_at.timestamp()) if file_record.created_at else int(time.time()),
                "filename": file_record.filename,
                "purpose": file_record.purpose,
            }
        )

    return {"object": "list", "data": file_responses}
