from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from backend.app.db.engine import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")  # admin, operator, viewer, developer
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String, nullable=False)  # webapi, mcpcli
    status = Column(String, default="active")
    region_hint = Column(String)
    language_hint = Column(String)
    chrome_required = Column(Boolean, default=False)
    health_status = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)

    auth_methods = relationship("AccountAuthMethod", back_populates="account")


class AccountAuthMethod(Base):
    __tablename__ = "account_auth_methods"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    auth_type = Column(String)  # cookie, apikey, browser, chrome
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
    discovered_at = Column(DateTime, default=datetime.utcnow)


class RequestLog(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    provider = Column(String)
    endpoint = Column(String)
    model_alias = Column(String)
    resolved_model = Column(String)
    feature_type = Column(String)
    stream_mode = Column(Boolean)
    latency_ms = Column(Integer)
    status_code = Column(Integer)
    retry_count = Column(Integer, default=0)
    prompt_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    job_type = Column(String)  # video, music, research
    status = Column(String, default="pending")
    progress_pct = Column(Float, default=0.0)
    result_url = Column(String)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class ConsumerApiKey(Base):
    __tablename__ = "consumer_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key_hash = Column(String, unique=True, index=True, nullable=False)
    label = Column(String)
    scopes = Column(JSON, default=[])
    rate_limit = Column(Integer)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    url = Column(String, nullable=False)
    event_types = Column(JSON, default=["*"])
    secret = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    purpose = Column(String, default="fine-tune")
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
