import asyncio
from typing import Dict, List, Optional

from sqlalchemy import select

from backend.app.adapters.base import BaseAdapter
from backend.app.adapters.mcpcli_adapter import McpCliAdapter
from backend.app.adapters.webapi_adapter import WebApiAdapter
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Account, AccountAuthMethod
from backend.app.logging.structured import logger
from backend.app.utils.encryption import decrypt


class AccountManager:
    def __init__(self):
        self.adapters: Dict[int, BaseAdapter] = {}
        self._lock = asyncio.Lock()

    async def refresh_accounts(self):
        async with self._lock:
            async with AsyncSessionLocal() as db:
                accounts = (await db.execute(select(Account).where(Account.status == "active"))).scalars().all()
                new_adapters: Dict[int, BaseAdapter] = {}
                for account in accounts:
                    try:
                        adapter = await self._initialize_adapter(db, account)
                        if adapter:
                            new_adapters[account.id] = adapter
                    except Exception as exc:
                        logger.error("Failed to initialize adapter", account_id=account.id, provider=account.provider, error=str(exc))
                self.adapters = new_adapters
                logger.info("Account manager refreshed", count=len(self.adapters))

    async def _initialize_adapter(self, db, account: Account) -> Optional[BaseAdapter]:
        auth_methods = (await db.execute(select(AccountAuthMethod).where(AccountAuthMethod.account_id == account.id))).scalars().all()
        if account.provider == "webapi":
            secure_1psid = None
            secure_1psidts = None
            for auth_method in auth_methods:
                if auth_method.auth_type == "cookie":
                    creds = decrypt(auth_method.encrypted_credentials)
                    if "|" in creds:
                        secure_1psid, secure_1psidts = creds.split("|", 1)
            return WebApiAdapter(secure_1psid, secure_1psidts, mock_mode=not (secure_1psid and secure_1psidts))
        if account.provider == "mcpcli":
            return McpCliAdapter(profile=account.label)
        return None

    def get_adapter_for_account(self, account_id: int) -> Optional[BaseAdapter]:
        return self.adapters.get(account_id)

    def get_all_adapters(self) -> List[BaseAdapter]:
        return list(self.adapters.values())


account_manager = AccountManager()
