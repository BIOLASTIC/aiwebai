import asyncio
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import User
from backend.app.auth.password import get_password_hash
from sqlalchemy.future import select

async def reset_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@local.host"))
        user = result.scalars().first()
        if user:
            user.password_hash = get_password_hash("111111")
            await db.commit()
            print("Admin password reset to 111111")
        else:
            print("Admin user not found")

if __name__ == "__main__":
    asyncio.run(reset_admin())
