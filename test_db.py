import asyncio
from app.db.engine import AsyncSessionLocal
from app.db.models import AccountAuthMethod
from app.utils.encryption import encrypt
from sqlalchemy import select
import traceback

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AccountAuthMethod).where(AccountAuthMethod.account_id == 1))
        method = result.scalars().first()
        if method:
            try:
                # Override the credentials with a new mock encryption to test
                method.encrypted_credentials = encrypt('mock|mock')
                await session.commit()
                print('Encrypted credentials overwritten')
            except Exception as e:
                traceback.print_exc()
        else:
            print('No auth method found')

asyncio.run(main())
