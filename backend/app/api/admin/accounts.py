from typing import List, Optional

import browser_cookie3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.accounts.manager import account_manager
from backend.app.auth.dependencies import get_current_admin
from backend.app.db.engine import get_db
from backend.app.db.models import Account, AccountAuthMethod, Model, User
from backend.app.schemas.accounts import AccountCreate, AccountResponse
from backend.app.utils.encryption import encrypt

router = APIRouter(prefix="/admin/accounts", tags=["admin-accounts"])


@router.post("/import/browser")
async def import_from_browser(browser: str = "chrome", db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    try:
        if browser == "chrome":
            cookies = browser_cookie3.chrome(domain_name=".google.com")
        elif browser == "firefox":
            cookies = browser_cookie3.firefox(domain_name=".google.com")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported browser: {browser}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Browser import failed: {exc}")

    secure_1psid = next((c.value for c in cookies if c.name == "__Secure-1PSID"), None)
    secure_1psidts = next((c.value for c in cookies if c.name == "__Secure-1PSIDTS"), None)
    if not secure_1psid or not secure_1psidts:
        raise HTTPException(status_code=400, detail="Gemini cookies not found in the selected browser")

    account = Account(label=f"Imported {browser.capitalize()}", provider="webapi", owner_user_id=admin.id, status="active", health_status="unknown")
    db.add(account)
    await db.flush()
    db.add(AccountAuthMethod(account_id=account.id, auth_type="cookie", encrypted_credentials=encrypt(f"{secure_1psid}|{secure_1psidts}")))
    await db.commit()
    await account_manager.refresh_accounts()
    return {"status": "success", "account_id": account.id}


@router.post("/{account_id}/validate")
async def validate_account(account_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await account_manager.refresh_accounts()
    adapter = account_manager.get_adapter_for_account(account_id)
    if not adapter:
        account.health_status = "unhealthy"
        await db.commit()
        return {"status": "invalid", "error": "Could not initialize adapter"}
    is_healthy = await adapter.health_check()
    account.health_status = "healthy" if is_healthy else "unhealthy"
    await db.commit()
    return {"status": "valid" if is_healthy else "invalid", "error": None if is_healthy else "health check failed"}


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    return (await db.execute(select(Account).options(selectinload(Account.auth_methods)))).scalars().all()


@router.post("/", response_model=AccountResponse)
async def create_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = Account(label=account_in.label, provider=account_in.provider, owner_user_id=account_in.owner_user_id or admin.id, region_hint=account_in.region_hint, language_hint=account_in.language_hint, chrome_required=account_in.chrome_required, status=account_in.status, health_status="unknown")
    db.add(account)
    await db.flush()
    for auth_method in account_in.auth_methods:
        db.add(AccountAuthMethod(account_id=account.id, auth_type=auth_method.auth_type, encrypted_credentials=encrypt(auth_method.credentials), expires_at=auth_method.expires_at))
    await db.commit()
    await account_manager.refresh_accounts()
    return (await db.execute(select(Account).options(selectinload(Account.auth_methods)).where(Account.id == account.id))).scalar_one()


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = (await db.execute(select(Account).options(selectinload(Account.auth_methods)).where(Account.id == account_id))).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


class AccountPatch(BaseModel):
    label: Optional[str] = None
    region_hint: Optional[str] = None
    language_hint: Optional[str] = None


@router.patch("/{account_id}", response_model=AccountResponse)
async def patch_account(account_id: int, patch: AccountPatch, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = (await db.execute(select(Account).options(selectinload(Account.auth_methods)).where(Account.id == account_id))).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for field in ["label", "region_hint", "language_hint"]:
        value = getattr(patch, field)
        if value is not None:
            setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}")
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    await db.commit()
    return {"status": "deleted"}


@router.get("/{account_id}/models")
async def get_account_models(account_id: int, feature: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    models = (await db.execute(select(Model).where(Model.status == "active"))).scalars().all()
    if feature:
        feature = feature.lower()
        filtered = []
        for model in models:
            caps = model.capabilities or {}
            cap_name = "images" if feature == "image" else feature
            if feature == "test" or feature in model.provider_model_name.lower() or caps.get(cap_name) or caps.get(feature):
                filtered.append(model)
        models = filtered
    return [{"id": m.id, "provider_model_name": m.provider_model_name, "display_name": m.display_name, "family": m.family, "source_provider": m.source_provider, "capabilities": m.capabilities or {}} for m in models]