import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def wait_for_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    # Standardize for SQLAlchemy
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not url.startswith("postgresql+asyncpg://"):
        # Fallback if somehow it's just the host
        url = f"postgresql+asyncpg://{url}"
        
    print(f"Connecting to database...")
    engine = create_async_engine(url)
    
    retries = 30
    for i in range(retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("✓ Database is ready")
            await engine.dispose()
            return
        except Exception as e:
            print(f"[{i+1}/{retries}] Waiting for database... ({e})")
            await asyncio.sleep(2)
    
    print("ERROR: Database connection timed out")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(wait_for_db())
