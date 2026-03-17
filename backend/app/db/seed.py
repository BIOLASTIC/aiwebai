import asyncio
from sqlalchemy import select

from backend.app.auth.api_key_auth import hash_key
from backend.app.auth.password import get_password_hash
from backend.app.config import settings
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import ConsumerApiKey, User


async def seed_defaults() -> None:
    async with AsyncSessionLocal() as session:
        users = [
            (settings.DEFAULT_ADMIN_EMAIL, settings.DEFAULT_ADMIN_PASSWORD),
            (settings.DEFAULT_COMPAT_ADMIN_EMAIL, settings.DEFAULT_ADMIN_PASSWORD),
        ]
        admin_ids = []
        for email, password in users:
            user = (await session.execute(select(User).where(User.email == email))).scalars().first()
            if not user:
                user = User(email=email, password_hash=get_password_hash(password), role="admin", status="active")
                session.add(user)
                await session.flush()
            admin_ids.append(user.id)

        existing = {row.key_hash for row in (await session.execute(select(ConsumerApiKey))).scalars().all()}
        for api_key in [settings.DEFAULT_API_KEY, settings.DEFAULT_TEST_API_KEY]:
            hashed = hash_key(api_key)
            if hashed not in existing and api_key not in existing:
                session.add(ConsumerApiKey(user_id=admin_ids[0], key_hash=hashed, label=settings.DEFAULT_API_KEY_LABEL, status="active"))
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_defaults())
