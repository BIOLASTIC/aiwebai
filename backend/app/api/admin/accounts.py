import json
from pathlib import Path
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


def _read_gemcli_auth(profile: str = "default") -> dict:
    """Read gemcli auth.json for the given profile. Returns parsed dict or raises."""
    auth_path = Path.home() / ".gemini-web-mcp-cli" / "profiles" / profile / "auth.json"
    if not auth_path.exists():
        raise FileNotFoundError(f"gemcli profile '{profile}' not found. Run 'gemcli login' first.")
    with open(auth_path) as f:
        return json.load(f)


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


@router.get("/gemcli-status")
async def gemcli_status(admin: User = Depends(get_current_admin)):
    """Check if gemcli is logged in and return email if available."""
    try:
        auth = _read_gemcli_auth()
        email = auth.get("email")
        cookies = auth.get("cookies", {})
        has_session = bool(cookies.get("__Secure-1PSID") or cookies.get("SID"))
        return {"logged_in": has_session, "email": email, "profile": "default"}
    except FileNotFoundError:
        return {"logged_in": False, "email": None, "profile": "default"}
    except Exception as exc:
        return {"logged_in": False, "email": None, "error": str(exc)}


@router.post("/import/gemcli")
async def import_from_gemcli(profile: str = "default", db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Import the gemcli default profile as an mcpcli account."""
    try:
        auth = _read_gemcli_auth(profile)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    email = auth.get("email")
    cookies = auth.get("cookies", {})
    secure_1psid = cookies.get("__Secure-1PSID") or cookies.get("SID")
    if not secure_1psid:
        raise HTTPException(status_code=400, detail="gemcli auth has no valid session cookie. Run 'gemcli login' again.")

    label = email or f"gemcli-{profile}"

    # Upsert: if an mcpcli account with this email already exists, update its credentials
    existing = (await db.execute(select(Account).where(Account.provider == "mcpcli", Account.email == email))).scalar_one_or_none() if email else None
    if existing:
        account = existing
    else:
        account = Account(label=label, email=email, provider="mcpcli", owner_user_id=admin.id, status="active", health_status="unknown")
        db.add(account)
        await db.flush()

    # Store the profile name as credentials (mcpcli adapter uses profile)
    existing_auth = (await db.execute(select(AccountAuthMethod).where(AccountAuthMethod.account_id == account.id, AccountAuthMethod.auth_type == "profile"))).scalar_one_or_none()
    if existing_auth:
        existing_auth.encrypted_credentials = encrypt(profile)
    else:
        db.add(AccountAuthMethod(account_id=account.id, auth_type="profile", encrypted_credentials=encrypt(profile)))

    await db.commit()
    await account_manager.refresh_accounts()
    return {"status": "success", "account_id": account.id, "email": email, "label": label}


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


@router.get("/capabilities")
async def list_account_capabilities(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    from backend.app.schemas.accounts import PROVIDER_ADAPTER_TYPE, PROVIDER_CAPABILITIES, AccountCapabilities
    accounts = (await db.execute(select(Account).options(selectinload(Account.auth_methods)))).scalars().all()
    result = []
    for account in accounts:
        provider = account.provider or ""
        caps = PROVIDER_CAPABILITIES.get(provider, {})
        result.append({
            "id": account.id,
            "label": account.label,
            "provider": provider,
            "adapter_type": PROVIDER_ADAPTER_TYPE.get(provider, provider),
            "capabilities": AccountCapabilities(**caps).model_dump(),
            "health_status": account.health_status,
        })
    return result


@router.post("/", response_model=AccountResponse)
async def create_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = Account(label=account_in.label, email=account_in.email, provider=account_in.provider, owner_user_id=account_in.owner_user_id or admin.id, region_hint=account_in.region_hint, language_hint=account_in.language_hint, chrome_required=account_in.chrome_required, status=account_in.status, health_status="unknown")
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