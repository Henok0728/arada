import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.schemas.auth import HotelRegisterRequest
from app.api.v1.auth import register_hotel

async def test_registration():
    async with AsyncSessionLocal() as db:
        # Create a unique slug to avoid conflict
        unique_id = str(uuid.uuid4())[:8]
        req = HotelRegisterRequest(
            hotel_name=f"Test Hotel {unique_id}",
            hotel_slug=f"test-hotel-{unique_id}",
            city="Addis Ababa",
            address="Test Address 123",
            phone_number="+251911000000",
            admin_email=f"admin-{unique_id}@test.com",
            admin_full_name="Test Admin",
            admin_password="password123"
        )
        
        try:
            print(f"Registering hotel with slug: {req.hotel_slug}")
            response = await register_hotel(req, db)
            print("Registration response:")
            print(f"  Hotel ID: {response.hotel_id}")
            print(f"  API Key: {response.api_key}")
            
            # Verify schema exists
            schema_name = f"hotel_{req.hotel_slug.replace('-', '_')}"
            result = await db.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'")
            exists = result.scalar()
            if exists:
                print(f"SUCCESS: Schema '{schema_name}' was created.")
            else:
                print(f"FAILURE: Schema '{schema_name}' was NOT found.")
                
            # Verify tables exist
            result = await db.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}'")
            tables = [r[0] for r in result.fetchall()]
            print(f"Tables in '{schema_name}': {tables}")
            
        except Exception as e:
            print(f"Error during registration: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(test_registration())
