from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerResponse, CustomerUpdateRequest


class CustomerProfileNotFound(Exception):
    pass


class DuplicatePhoneError(Exception):
    pass


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.customers = CustomerRepository(session)

    async def get_current_customer(self, user_id: UUID) -> CustomerResponse:
        customer = await self.customers.get_by_user_id(user_id)
        if customer is None:
            raise CustomerProfileNotFound
        return self._response(customer)

    async def update_current_customer(
        self, user_id: UUID, request: CustomerUpdateRequest
    ) -> CustomerResponse:
        customer = await self.customers.get_by_user_id(user_id)
        if customer is None:
            raise CustomerProfileNotFound
        values = request.model_dump(exclude_unset=True)
        if "full_name" in values:
            customer.full_name = values["full_name"]
        if "profile_image_url" in values:
            customer.profile_image_url = values["profile_image_url"]
        if "phone" in values:
            customer.user.phone = values["phone"]
        try:
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(customer)
            await self.session.refresh(customer.user)
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicatePhoneError from exc
        return self._response(customer)

    @staticmethod
    def _response(customer: Customer) -> CustomerResponse:
        return CustomerResponse(
            id=customer.id,
            full_name=customer.full_name,
            email=customer.user.email,
            phone=customer.user.phone,
            profile_image_url=customer.profile_image_url,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )
