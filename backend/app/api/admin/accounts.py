from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.engine import get_db
from backend.app.db.models import Account, AccountAuthMethod, User
from backend.app.schemas.accounts import AccountCreate, AccountResponse
from backend.app.auth.dependencies import get_current_admin
from pydantic import BaseModel

from backend.app.utils.encryption import encrypt, decrypt
from backend.app.accounts.manager import account_manager
import browser_cookie3

router = APIRouter(prefix="/admin/accounts", tags=["admin-accounts"])

@router.post("/import/browser")
async def import_from_browser(browser: str = "chrome", db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Import Gemini cookies from local browser."""
    _KEYCHAIN_MSG = (
        "Chrome cookie import requires the backend to run on the same machine as your Chrome browser "
        "with access to the OS keychain. Since you are accessing the server remotely, please use "
        "manual cookie entry instead: open Chrome DevTools → Application → Cookies → "
        "gemini.google.com, copy __Secure-1PSID and __Secure-1PSIDTS, then add an account manually."
    )
    try:
        try:
            if browser == "chrome":
                cj = browser_cookie3.chrome(domain_name='.google.com')
            elif browser == "firefox":
                cj = browser_cookie3.firefox(domain_name='.google.com')
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported browser: {browser}")
        except HTTPException:
            raise
        except Exception as e:
            err = str(e).lower()
            if any(kw in err for kw in ("key", "decrypt", "keychain", "keyring", "secret")):
                raise HTTPException(status_code=400, detail=_KEYCHAIN_MSG)
            raise

        secure_1psid = None
        secure_1psidts = None

        try:
            for cookie in cj:
                if cookie.name == "__Secure-1PSID":
                    secure_1psid = cookie.value
                elif cookie.name == "__Secure-1PSIDTS":
                    secure_1psidts = cookie.value
        except Exception as e:
            err = str(e).lower()
            if any(kw in err for kw in ("key", "decrypt", "keychain", "keyring", "secret")):
                raise HTTPException(status_code=400, detail=_KEYCHAIN_MSG)
            raise

        if not secure_1psid or not secure_1psidts:
            raise HTTPException(
                status_code=400,
                detail="Gemini cookies not found in Chrome. Make sure you are logged into gemini.google.com in Chrome on this machine.",
            )

        account = Account(
            label=f"Imported {browser.capitalize()}",
            provider="webapi",
            owner_user_id=admin.id,
            status="active",
            health_status="unknown",
        )
        db.add(account)
        await db.flush()

        auth_method = AccountAuthMethod(
            account_id=account.id,
            auth_type="cookie",
            encrypted_credentials=encrypt(f"{secure_1psid}|{secure_1psidts}"),
        )
        db.add(auth_method)
        await db.commit()

        await account_manager.refresh_accounts()
        return {"status": "success", "account_id": account.id}
    except HTTPException:
        raise
    except Exception as e:
        err = str(e).lower()
        if any(kw in err for kw in ("key", "decrypt", "keychain", "keyring", "secret")):
            raise HTTPException(status_code=400, detail=_KEYCHAIN_MSG)
        raise HTTPException(status_code=500, detail=f"Failed to import cookies: {str(e)}")

@router.post("/{account_id}/validate")
async def validate_account(account_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Force-validate Gemini account credentials."""
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Try to initialize or get adapter
    await account_manager.refresh_accounts()
    adapter = account_manager.get_adapter_for_account(account_id)
    
    if not adapter:
        account.health_status = "unhealthy"
        await db.commit()
        return {"status": "invalid", "error": "Could not initialize adapter"}
    
    error_msg = None
    try:
        await adapter.init()
        await adapter.client.generate_content("hi")
        is_healthy = True
    except Exception as e:
        is_healthy = False
        error_msg = f"{type(e).__name__}: {e}"

    account.health_status = "healthy" if is_healthy else "unhealthy"
    await db.commit()

    return {"status": "valid" if is_healthy else "invalid", "error": error_msg}

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(Account).options(selectinload(Account.auth_methods)))
    accounts = result.scalars().all()
    return accounts

@router.post("/", response_model=AccountResponse)
async def create_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    # If no owner provided, default to current admin
    owner_id = account_in.owner_user_id or admin.id
    
    account = Account(
        label=account_in.label,
        provider=account_in.provider,
        owner_user_id=owner_id,
        region_hint=account_in.region_hint,
        language_hint=account_in.language_hint,
        chrome_required=account_in.chrome_required,
        status=account_in.status,
        health_status="unknown"
    )
    db.add(account)
    await db.flush() # Get account ID
    
    for am in account_in.auth_methods:
        auth_method = AccountAuthMethod(
            account_id=account.id,
            auth_type=am.auth_type,
            encrypted_credentials=encrypt(am.credentials), # Use encryption utility
            expires_at=am.expires_at
        )
        db.add(auth_method)
    
    await db.commit()
    
    # Refresh manager to pick up new account
    await account_manager.refresh_accounts()
    
    # Fetch with eager load to return full model
    result = await db.execute(select(Account).options(selectinload(Account.auth_methods)).where(Account.id == account.id))
    return result.scalar_one()

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    result = await db.execute(select(Account).options(selectinload(Account.auth_methods)).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

class AccountPatch(BaseModel):
    label: Optional[str] = None
    region_hint: Optional[str] = None
    language_hint: Optional[str] = None


@router.patch("/{account_id}", response_model=AccountResponse)
async def patch_account(
    account_id: int,
    patch: AccountPatch,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Rename / update account metadata."""
    result = await db.execute(
        select(Account).options(selectinload(Account.auth_methods)).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if patch.label is not None:
        account.label = patch.label
    if patch.region_hint is not None:
        account.region_hint = patch.region_hint
    if patch.language_hint is not None:
        account.language_hint = patch.language_hint
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}")
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Delete associated auth methods
    # result = await db.execute(select(AccountAuthMethod).where(AccountAuthMethod.account_id == account_id))
    # for am in result.scalars().all():
    #     await db.delete(am)
    
    await db.delete(account)
    await db.commit()
    return {"status": "deleted"}
