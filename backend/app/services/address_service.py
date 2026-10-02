from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.address_repository import AddressRepository
from app.schemas.address import AddressCreateRequest, AddressUpdateRequest


class AddressCustomerNotFound(Exception):
    pass


class AddressNotFound(Exception):
    pass


class AddressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.addresses = AddressRepository(session)

    async def list_addresses(self, user_id: UUID) -> list[Address]:
        customer = await self.addresses.get_customer(user_id)
        if customer is None:
            raise AddressCustomerNotFound
        return await self.addresses.list_for_customer(customer.id)

    async def get_address(self, user_id: UUID, address_id: UUID) -> Address:
        customer = await self.addresses.get_customer(user_id)
        if customer is None:
            raise AddressCustomerNotFound
        address = await self.addresses.get_for_customer(address_id, customer.id)
        if address is None:
            raise AddressNotFound
        return address

    async def get_default_address(self, user_id: UUID) -> Address:
        customer = await self.addresses.get_customer(user_id)
        if customer is None:
            raise AddressCustomerNotFound
        address = await self.addresses.get_default(customer.id)
        if address is None:
            raise AddressNotFound
        return address

    async def create_address(
        self, user_id: UUID, request: AddressCreateRequest
    ) -> Address:
        customer = await self.addresses.get_customer(user_id, for_update=True)
        if customer is None:
            raise AddressCustomerNotFound
        if request.is_default:
            await self.addresses.clear_default(customer.id)
        address = Address(customer_id=customer.id, **request.model_dump())
        self.addresses.add(address)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def update_address(
        self, user_id: UUID, address_id: UUID, request: AddressUpdateRequest
    ) -> Address:
        customer = await self.addresses.get_customer(user_id, for_update=True)
        if customer is None:
            raise AddressCustomerNotFound
        address = await self.addresses.get_for_customer(
            address_id, customer.id, for_update=True
        )
        if address is None:
            raise AddressNotFound
        values = request.model_dump(exclude_unset=True)
        if values.get("is_default") is True:
            await self.addresses.clear_default(customer.id)
        for field, value in values.items():
            setattr(address, field, value)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def set_default(self, user_id: UUID, address_id: UUID) -> Address:
        customer = await self.addresses.get_customer(user_id, for_update=True)
        if customer is None:
            raise AddressCustomerNotFound
        address = await self.addresses.get_for_customer(
            address_id, customer.id, for_update=True
        )
        if address is None:
            raise AddressNotFound
        await self.addresses.clear_default(customer.id)
        address.is_default = True
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def delete_address(self, user_id: UUID, address_id: UUID) -> None:
        customer = await self.addresses.get_customer(user_id, for_update=True)
        if customer is None:
            raise AddressCustomerNotFound
        address = await self.addresses.get_for_customer(
            address_id, customer.id, for_update=True
        )
        if address is None:
            raise AddressNotFound
        was_default = address.is_default
        await self.session.delete(address)
        await self.session.flush()
        if was_default:
            remaining = await self.addresses.list_for_customer(customer.id)
            if remaining:
                remaining[0].is_default = True
                await self.session.flush()
        await self.session.commit()
