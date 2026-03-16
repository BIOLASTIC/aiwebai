import asyncio
from sqlalchemy.future import select
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import User
from backend.app.auth.password import get_password_hash
from backend.app.config import settings

async def seed_admin():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@local.host"))
        admin = result.scalars().first()
        if not admin:
            admin = User(
                email="admin@local.host",
                password_hash=get_password_hash("111111"), # Default password from GEMINI.md
                role="admin",
                status="active"
            )
            session.add(admin)
            await session.commit()
            print("Admin user created: admin@local.host / 111111")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(seed_admin())
