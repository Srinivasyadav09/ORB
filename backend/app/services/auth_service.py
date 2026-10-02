from datetime import timedelta
from uuid import UUID

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    perform_dummy_password_check,
    verify_password,
)
from app.models.customer import Customer
from app.models.farmer import Farmer, VerificationStatus
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CustomerRegistrationRequest, FarmerRegistrationRequest


class DuplicateRegistrationError(Exception):
    """The supplied email or phone is already registered."""


class InvalidCredentialsError(Exception):
    """Credentials or refresh token are not valid for an active account."""


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register_customer(self, request: CustomerRegistrationRequest) -> User:
        user = User(
            email=str(request.email),
            phone=request.phone,
            password_hash=await run_in_threadpool(
                hash_password, request.password.get_secret_value()
            ),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=False,
            customer_profile=Customer(full_name=request.full_name),
        )
        return await self._register(user)

    async def register_farmer(self, request: FarmerRegistrationRequest) -> User:
        user = User(
            email=str(request.email),
            phone=request.phone,
            password_hash=await run_in_threadpool(
                hash_password, request.password.get_secret_value()
            ),
            role=UserRole.FARMER,
            is_active=True,
            is_verified=False,
            farmer_profile=Farmer(
                full_name=request.full_name,
                farm_name=request.farm_name,
                farm_location=request.farm_location,
                farm_description=request.farm_description,
                farm_image_url=request.farm_image_url,
                verification_status=VerificationStatus.SUBMITTED,
            ),
        )
        return await self._register(user)

    async def _register(self, user: User) -> User:
        try:
            async with self.session.begin():
                if await self.users.email_exists(
                    user.email
                ) or await self.users.phone_exists(user.phone):
                    raise DuplicateRegistrationError
                self.users.add(user)
                await self.session.flush()
                registered_user = await self.users.get_by_id(user.id)
        except IntegrityError as exc:
            # Unique constraints close races between the pre-check and insert.
            raise DuplicateRegistrationError from exc
        assert registered_user is not None
        return registered_user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active:
            await run_in_threadpool(perform_dummy_password_check, password)
            raise InvalidCredentialsError
        if not await run_in_threadpool(verify_password, password, user.password_hash):
            raise InvalidCredentialsError
        return user

    def issue_tokens(self, user: User) -> dict[str, str | int | User]:
        return {
            "access_token": create_access_token(str(user.id), user.role.value),
            "refresh_token": create_refresh_token(str(user.id)),
            "token_type": "bearer",
            "expires_in": int(
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds()
            ),
            "user": user,
        }

    async def refresh_access_token(
        self, refresh_token: str
    ) -> dict[str, str | int | User]:
        try:
            claims = decode_token(refresh_token, expected_type="refresh")
            user_id = UUID(claims["sub"])
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            raise InvalidCredentialsError from None
        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError
        # Refresh credentials are stateless in Phase 3. Preserve the submitted refresh
        # token until expiry; session-backed rotation/revocation is a later migration.
        return {
            "access_token": create_access_token(str(user.id), user.role.value),
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds()
            ),
            "user": user,
        }
