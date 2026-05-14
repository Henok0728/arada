"""
Auth API router — POST /v1/auth/register and POST /v1/auth/token.

Route design:
  POST /v1/auth/register   → Creates Hotel + User (ADMIN) + API key atomically.
                             Returns the plaintext API key ONCE.
  POST /v1/auth/token      → Email/password login, returns JWT token pair.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models.hotel import Hotel, HotelStatus
from app.db.models.user import User, UserRole
from app.db.models.api_key import APIKey, ENV_DEV, VALID_SCOPES
from app.db.repositories.hotel import HotelRepository
from app.db.repositories.user import UserRepository
from app.schemas.auth import HotelRegisterRequest, RegisterResponse, TokenRequest, TokenResponse
from app.services.auth import (
    hash_password,
    verify_password,
    generate_api_key,
    create_token_pair,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new hotel partner",
    description=(
        "Creates a Hotel record, an ADMIN user, and a sandbox API key atomically. "
        "The plaintext API key is returned ONCE — it cannot be recovered after this call."
    ),
)
async def register_hotel(
    req: HotelRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    hotel_repo = HotelRepository(db)
    user_repo = UserRepository(db)

    # -----------------------------------------------------------------------
    # Uniqueness guards
    # -----------------------------------------------------------------------
    if await hotel_repo.is_slug_taken(req.hotel_slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hotel slug '{req.hotel_slug}' is already registered.",
        )
    if await hotel_repo.is_email_taken(req.admin_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{req.admin_email}' is already in use.",
        )
    if await user_repo.is_email_taken(req.admin_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user account with '{req.admin_email}' already exists.",
        )

    # -----------------------------------------------------------------------
    # 1. Create Hotel (starts in SANDBOX — requires KYC for ACTIVE)
    # -----------------------------------------------------------------------
    location_wkt = None
    if req.latitude is not None and req.longitude is not None:
        location_wkt = f"POINT({req.longitude} {req.latitude})"

    hotel = Hotel(
        name=req.hotel_name,
        slug=req.hotel_slug,
        city=req.city,
        address=req.address,
        phone_number=req.phone_number,
        email=req.admin_email,
        country_code=req.country_code.upper(),
        status=HotelStatus.SANDBOX,
        location=location_wkt,
    )
    hotel = await hotel_repo.create(hotel)

    # -----------------------------------------------------------------------
    # 2. Create Admin User
    # -----------------------------------------------------------------------
    user = User(
        hotel_id=hotel.id,
        email=req.admin_email,
        full_name=req.admin_full_name,
        hashed_password=hash_password(req.admin_password),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=False,
    )
    user = await user_repo.create(user)

    # -----------------------------------------------------------------------
    # 3. Bootstrap Private Tenant Schema (bookings, rate_configs)
    # -----------------------------------------------------------------------
    from app.services.tenant import bootstrap_tenant_schema
    await bootstrap_tenant_schema(db, hotel.slug)

    # -----------------------------------------------------------------------
    # 4. Generate API key — SANDBOX env, full MVP scopes
    # -----------------------------------------------------------------------
    plaintext_key, key_hash, key_prefix = generate_api_key(ENV_DEV)

    api_key_record = APIKey(
        hotel_id=hotel.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        environment=ENV_DEV,
        scopes=VALID_SCOPES,  # Full scopes for MVP sandbox
        name="Default sandbox key",
        is_active=True,
    )
    db.add(api_key_record)
    await db.flush()
    await db.refresh(api_key_record)

    # -----------------------------------------------------------------------
    # 5. Issue JWT token pair so the user is immediately logged in
    # -----------------------------------------------------------------------
    tokens = create_token_pair(
        user_id=str(user.id),
        hotel_id=str(hotel.id),
        role=user.role.value,
    )

    # session.py commits on clean exit — no explicit commit needed.

    return RegisterResponse(
        hotel_id=hotel.id,
        user_id=user.id,
        api_key=plaintext_key,
        api_key_prefix=key_prefix,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login and obtain JWT token pair",
    description="Validates email/password and returns a short-lived access token + refresh token.",
)
async def login(
    req: TokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    user_repo = UserRepository(db)

    # -----------------------------------------------------------------------
    # Credential validation
    # -----------------------------------------------------------------------
    user = await user_repo.get_by_email(req.email)

    # Constant-time failure: always verify even if user doesn't exist,
    # to prevent timing-based user enumeration attacks.
    dummy_hash = "$2b$12$dummyhashfortimingattackprevention"
    password_valid = verify_password(
        req.password,
        user.hashed_password if user else dummy_hash,
    )

    if not user or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support.",
        )

    # -----------------------------------------------------------------------
    # Issue token pair
    # -----------------------------------------------------------------------
    tokens = create_token_pair(
        user_id=str(user.id),
        hotel_id=str(user.hotel_id),
        role=user.role.value,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
    )
