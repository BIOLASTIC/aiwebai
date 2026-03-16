from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Dict
from backend.app.adapters.router import adapter_router
from backend.app.auth.api_key_auth import get_user_by_api_key
from backend.app.db.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/native/extensions", tags=["native-extensions"])

class ExtensionRun(BaseModel):
    extension_id: str
    prompt: str

@router.get("/")
async def list_extensions(user: User = Depends(get_user_by_api_key)):
    # Static list or discover from client
    return [
        {"id": "google_search", "name": "Google Search"},
        {"id": "youtube", "name": "YouTube"},
        {"id": "google_maps", "name": "Google Maps"},
        {"id": "google_workspace", "name": "Google Workspace"},
    ]

@router.post("/run")
async def run_extension(req: ExtensionRun, user: User = Depends(get_user_by_api_key)):
    adapter = adapter_router.get_best_adapter("chat")
    # Simplified: gemini-webapi handles extensions via tools/plugins
    return {"status": "success", "result": f"Simulated run of {req.extension_id}"}
