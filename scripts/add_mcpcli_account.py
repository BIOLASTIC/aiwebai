import asyncio
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.models import Account, User
from sqlalchemy.future import select

async def add_mcpcli_account():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@local.host"))
        admin = result.scalars().first()
        if not admin:
            print("Admin not found")
            return
            
        # Check if already exists
        result = await db.execute(select(Account).where(Account.provider == "mcpcli"))
        existing = result.scalars().first()
        if existing:
            print("MCP CLI account already exists")
            return
            
        account = Account(
            label="MCP CLI",
            owner_user_id=admin.id,
            provider="mcpcli",
            status="active",
            health_status="healthy"
        )
        db.add(account)
        await db.commit()
        print("MCP CLI account added")

if __name__ == "__main__":
    asyncio.run(add_mcpcli_account())
