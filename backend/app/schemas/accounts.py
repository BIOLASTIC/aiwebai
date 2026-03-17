from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List
from datetime import datetime


PROVIDER_ADAPTER_TYPE = {
    "webapi": "gemini-webapi",
    "mcpcli": "gemini-web-mcp-cli",
}

PROVIDER_CAPABILITIES = {
    "webapi": {"chat": True, "image": True, "video": False, "music": False, "research": False},
    "mcpcli": {"chat": True, "image": True, "video": True, "music": True, "research": True},
}


class AccountCapabilities(BaseModel):
    chat: bool = False
    image: bool = False
    video: bool = False
    music: bool = False
    research: bool = False


class AuthMethodBase(BaseModel):
    auth_type: str
    credentials: str # Encrypted string
    expires_at: Optional[datetime] = None

class AuthMethodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    auth_type: str
    last_refreshed: Optional[datetime]
    expires_at: Optional[datetime]

class AccountBase(BaseModel):
    label: str
    email: Optional[str] = None
    provider: str
    region_hint: Optional[str] = None
    language_hint: Optional[str] = None
    chrome_required: bool = False
    status: str = "active"

class AccountCreate(AccountBase):
    owner_user_id: Optional[int] = None
    auth_methods: List[AuthMethodBase]

class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_user_id: int
    health_status: str
    created_at: datetime
    auth_methods: List[AuthMethodResponse]
    adapter_type: Optional[str] = None
    capabilities: Optional[AccountCapabilities] = None

    @model_validator(mode="after")
    def populate_derived_fields(self) -> "AccountResponse":
        provider = self.provider or ""
        self.adapter_type = PROVIDER_ADAPTER_TYPE.get(provider, provider)
        caps = PROVIDER_CAPABILITIES.get(provider, {})
        self.capabilities = AccountCapabilities(**caps)
        return self
