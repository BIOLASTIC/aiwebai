from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.engine import get_db
from backend.app.db.models import Model, User
from backend.app.auth.dependencies import get_current_admin
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ModelBase(BaseModel):
    provider_model_name: str
    display_name: str
    family: str
    source_provider: str
    status: str = "active"

class ModelResponse(ModelBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    discovered_at: datetime

from backend.app.models.registry import model_registry

router = APIRouter(prefix="/admin/models", tags=["admin-models"])

@router.post("/refresh")
async def refresh_models(admin: User = Depends(get_current_admin)):
    """Trigger model discovery from all adapters."""
    await model_registry.discover_models()
    return {"status": "success"}

@router.get("/", response_model=List[ModelResponse])
async def list_models(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(Model))
    return result.scalars().all()

@router.post("/", response_model=ModelResponse)
async def create_model(model_in: ModelBase, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(Model).where(Model.provider_model_name == model_in.provider_model_name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Model already exists")
    
    model = Model(**model_in.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model
