from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.models import User

router = APIRouter(prefix="/admin/parity", tags=["admin-parity"])

@router.get("/")
async def get_parity_matrix(admin: User = Depends(get_current_admin)):
    # This would ideally come from a test suite result database
    # For now, we return a canonical matrix based on current knowledge
    return [
        {"feature": "Chat Completions", "webapi": "healthy", "mcpcli": "healthy", "notes": "Full streaming support"},
        {"feature": "Streaming", "webapi": "healthy", "mcpcli": "partial", "notes": "webapi preferred for SSE"},
        {"feature": "Image Generation", "webapi": "healthy", "mcpcli": "healthy", "notes": "Different providers internally"},
        {"feature": "Image Editing", "webapi": "healthy", "mcpcli": "unsupported", "notes": "Only webapi supports editing"},
        {"feature": "Video Generation", "webapi": "unsupported", "mcpcli": "healthy", "notes": "Requires polling"},
        {"feature": "Music Generation", "webapi": "unsupported", "mcpcli": "healthy", "notes": "Requires polling"},
        {"feature": "Deep Research", "webapi": "unsupported", "mcpcli": "healthy", "notes": "Exclusive to mcp-cli"},
        {"feature": "Gems CRUD", "webapi": "healthy", "mcpcli": "partial", "notes": "Full management in webapi"},
        {"feature": "History Management", "webapi": "healthy", "mcpcli": "unsupported", "notes": "webapi only"},
        {"feature": "File Uploads", "webapi": "healthy", "mcpcli": "healthy", "notes": "Images and Docs supported"},
    ]
