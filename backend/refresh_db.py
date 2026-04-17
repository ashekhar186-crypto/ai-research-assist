import asyncio
from app.database.connection import engine, Base
from app.models.user import User
from app.models.paper import Paper
# Import other models if you have them

async def refresh():
    async with engine.begin() as conn:
        # Warning: This deletes existing papers/users
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database synced with new schema!")

if __name__ == "__main__":
    asyncio.run(refresh())
