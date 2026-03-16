import asyncio
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.future import select
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Account, AccountAuthMethod
from backend.app.adapters.base import BaseAdapter
from backend.app.adapters.webapi_adapter import WebApiAdapter
from backend.app.adapters.mcpcli_adapter import McpCliAdapter
from backend.app.utils.encryption import decrypt, encrypt
from backend.app.logging.structured import logger

class AccountManager:
    def __init__(self):
        self.adapters: Dict[int, BaseAdapter] = {}
        self._lock = asyncio.Lock()

    async def refresh_accounts(self):
        """Reload all active accounts from DB and initialize adapters."""
        async with self._lock:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Account).where(Account.status == "active")
                )
                accounts = result.scalars().all()
                
                new_adapters = {}
                for account in accounts:
                    try:
                        adapter = await self._initialize_adapter(db, account)
                        if adapter:
                            new_adapters[account.id] = adapter
                        else:
                            logger.warning("Adapter initialization returned None", account_id=account.id, provider=account.provider)
                    except Exception as e:
                        import traceback
                        error_detail = traceback.format_exc()
                        logger.error("Failed to initialize adapter for account", account_id=account.id, error=str(e), traceback=error_detail)
                
                self.adapters = new_adapters
                logger.info("Account manager refreshed", count=len(self.adapters))

    async def _initialize_adapter(self, db, account: Account) -> Optional[BaseAdapter]:
        # Get auth methods
        result = await db.execute(
            select(AccountAuthMethod).where(AccountAuthMethod.account_id == account.id)
        )
        auth_methods = result.scalars().all()
        
        if account.provider == "webapi":
            secure_1psid = None
            secure_1psidts = None
            for am in auth_methods:
                if am.auth_type == "cookie":
                    creds = decrypt(am.encrypted_credentials)
                    # Expected format "1PSID|1PSIDTS" or JSON
                    if "|" in creds:
                        secure_1psid, secure_1psidts = creds.split("|", 1)
            
            if secure_1psid and secure_1psidts:
                return WebApiAdapter(secure_1psid, secure_1psidts)
        
        elif account.provider == "mcpcli":
            # McpCli might use profiles or API keys
            api_key = None
            for am in auth_methods:
                if am.auth_type == "apikey":
                    api_key = decrypt(am.encrypted_credentials)
            
            # McpCliAdapter currently uses 'gemcli' subprocess
            # We might need to pass the API key via env or profile
            return McpCliAdapter(profile=account.label)
            
        return None

    def get_adapter_for_account(self, account_id: int) -> Optional[BaseAdapter]:
        return self.adapters.get(account_id)

    def get_all_adapters(self) -> List[BaseAdapter]:
        return list(self.adapters.values())

account_manager = AccountManager()
