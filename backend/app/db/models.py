from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .engine import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    provider = Column(String, nullable=False)
    status = Column(String, default="active")
    region_hint = Column(String)
    language_hint = Column(String)
    chrome_required = Column(Boolean, default=False)
    health_status = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)

    auth_methods = relationship("AccountAuthMethod", back_populates="account", cascade="all, delete-orphan")


class AccountAuthMethod(Base):
    __tablename__ = "account_auth_methods"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    auth_type = Column(String)
    encrypted_credentials = Column(Text)
    last_refreshed = Column(DateTime)
    expires_at = Column(DateTime)

    account = relationship("Account", back_populates="auth_methods")


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    provider_model_name = Column(String, unique=True, index=True)
    display_name = Column(String)
    family = Column(String)
    source_provider = Column(String)
    status = Column(String, default="active")
    capabilities = Column(JSON, default=dict)
    discovered_at = Column(DateTime, default=datetime.utcnow)


class RequestLog(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    provider = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    model_alias = Column(String, nullable=True)
    resolved_model = Column(String, nullable=True)
    feature_type = Column(String, nullable=True)
    stream_mode = Column(Boolean, default=False)
    latency_ms = Column(Integer, default=0)
    status_code = Column(Integer, default=200)
    retry_count = Column(Integer, default=0)
    prompt_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    job_type = Column(String)
    status = Column(String, default="pending")
    progress_pct = Column(Float, default=0.0)
    result_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")


class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    status = Column(String, nullable=False)
    progress_pct = Column(Float, default=0.0)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="events")


class ConsumerApiKey(Base):
    __tablename__ = "consumer_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    label = Column(String)
    scopes = Column(JSON, default=list)
    rate_limit = Column(Integer, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=True)
    purpose = Column(String(50), nullable=False)
    owner_user_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        if "size" in kwargs and "size_bytes" not in kwargs:
            kwargs["size_bytes"] = kwargs.pop("size")
        if "user_id" in kwargs and "owner_user_id" not in kwargs:
            kwargs["owner_user_id"] = kwargs.pop("user_id")
        super().__init__(**kwargs)

    @hybrid_property
    def size(self) -> int:
        return self.size_bytes

    @size.setter
    def size(self, value: int) -> None:
        self.size_bytes = value

    @hybrid_property
    def user_id(self) -> Optional[int]:
        return self.owner_user_id

    @user_id.setter
    def user_id(self, value: Optional[int]) -> None:
        self.owner_user_id = value


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    url = Column(String, nullable=False)
    event_types = Column(JSON, default=lambda: ["*"])
    secret = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


