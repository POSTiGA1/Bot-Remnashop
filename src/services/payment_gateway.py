from typing import Optional

from aiogram import Bot
from fluentogram import TranslatorHub
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.core.enums import Currency, PaymentGatewayType
from src.core.storage_keys import DefaultCurrencyKey
from src.infrastructure.database import UnitOfWork
from src.infrastructure.database.models.dto import PaymentGatewayDto
from src.infrastructure.redis import RedisRepository

from .base import BaseService

# TODO: Make payment gateway sorting customizable for display


class PaymentGatewayService(BaseService):
    def __init__(
        self,
        uow: UnitOfWork,
        config: AppConfig,
        bot: Bot,
        redis_client: Redis,
        redis_repository: RedisRepository,
        translator_hub: TranslatorHub,
    ) -> None:
        super().__init__(config, bot, redis_client, redis_repository, translator_hub)
        self.uow = uow

    async def get(self, gateway_id: int) -> Optional[PaymentGatewayDto]:
        return await self.uow.repository.gateways.get(gateway_id)

    async def get_by_type(self, gateway_type: PaymentGatewayType) -> Optional[PaymentGatewayDto]:
        return await self.uow.repository.gateways.get_by_type(gateway_type)

    async def get_all(self) -> list[PaymentGatewayDto]:
        return await self.uow.repository.gateways.get_all()

    async def update(self, gateway: PaymentGatewayDto) -> Optional[PaymentGatewayDto]:
        return await self.uow.repository.gateways.update(
            gateway_id=gateway.id,
            **gateway.changed_data,
        )

    async def filter_active(self, is_active: bool = True) -> list[PaymentGatewayDto]:
        return await self.uow.repository.gateways.filter_active(is_active)

    async def get_default_currency(self) -> Currency:
        return await self.redis_repository.get(
            key=DefaultCurrencyKey(),
            validator=Currency,
            default=Currency.RUB,
        )

    async def set_default_currency(self, currency: Currency) -> None:
        await self.redis_repository.set(key=DefaultCurrencyKey(), value=currency.value)
