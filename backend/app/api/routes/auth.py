from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    CustomerRegistrationRequest,
    FarmerRegistrationRequest,
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.auth_service import (
    AuthService,
    DuplicateRegistrationError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register/customer",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_customer(
    request: CustomerRegistrationRequest, session: AsyncSession = Depends(get_db)
) -> User:
    try:
        return await AuthService(session).register_customer(request)
    except DuplicateRegistrationError:
        raise HTTPException(
            status_code=409, detail="Email or phone is already registered"
        ) from None


@router.post(
    "/register/farmer",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_farmer(
    request: FarmerRegistrationRequest, session: AsyncSession = Depends(get_db)
) -> User:
    try:
        return await AuthService(session).register_farmer(request)
    except DuplicateRegistrationError:
        raise HTTPException(
            status_code=409, detail="Email or phone is already registered"
        ) from None


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_db)) -> dict:
    try:
        user = await AuthService(session).authenticate(
            str(request.email), request.password.get_secret_value()
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return AuthService(session).issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest, session: AsyncSession = Depends(get_db)
) -> dict:
    try:
        return await AuthService(session).refresh_access_token(request.refresh_token)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.get("/me", response_model=CurrentUserResponse)
async def current_user(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", response_model=LogoutResponse)
async def logout(_: User = Depends(get_current_user)) -> LogoutResponse:
    return LogoutResponse(message="Logged out. Remove stored tokens from this client.")
