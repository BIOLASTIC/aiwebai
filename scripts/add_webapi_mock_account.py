import asyncio
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Account, User
from sqlalchemy.future import select


async def add_webapi_mock_account():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@local.host"))
        admin = result.scalars().first()
        if not admin:
            print("Admin not found")
            return

        # Check if already exists
        result = await db.execute(select(Account).where(Account.label == "WebAPI Mock"))
        existing = result.scalars().first()
        if existing:
            print("WebAPI Mock account already exists")
            return

        account = Account(
            label="WebAPI Mock",
            owner_user_id=admin.id,
            provider="webapi",
            status="active",
            health_status="healthy",
        )
        db.add(account)
        await db.commit()
        print("WebAPI Mock account added")


if __name__ == "__main__":
    asyncio.run(add_webapi_mock_account())
