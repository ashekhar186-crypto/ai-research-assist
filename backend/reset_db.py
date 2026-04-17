import asyncio
from sqlalchemy import text
from app.database.connection import engine, Base
from app.models import User, Project, Paper, Analysis, Proposal, ChatSession, ChatMessage

async def reset():
    print("Connecting to async engine for a hard reset...")
    async with engine.begin() as conn:
        # Nuclear option: Drop the public schema and recreate it
        print("Wiping all existing tables and constraints...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        
        print("Recreating clean tables from models...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Done! Database is now 100% fresh and matches your models.")

if __name__ == "__main__":
    asyncio.run(reset())
