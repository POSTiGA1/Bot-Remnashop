from typing import Any, Optional

from pydantic import SecretStr

from src.core.encryption import decrypt, encrypt
from src.core.enums import PaymentGatewayType
from src.infrastructure.database.models.dto import PaymentGatewayDto
from src.infrastructure.database.models.sql import PaymentGateway

from .base import BaseRepository


class PaymentGatewayRepository(BaseRepository):
    def _encrypt_gateway_secret(self, data: dict[str, Any]) -> dict[str, Any]:
        if "secret" in data and data["secret"] and isinstance(data["secret"], SecretStr):
            data["secret"] = encrypt(data["secret"].get_secret_value())
        return data

    def _decrypt_gateway_secret(
        self,
        gateway_dto: Optional[PaymentGatewayDto],
    ) -> Optional[PaymentGatewayDto]:
        if gateway_dto and gateway_dto.secret:
            gateway_dto.secret = SecretStr(decrypt(gateway_dto.secret.get_secret_value()))
        return gateway_dto

    async def get(self, gateway_id: int) -> Optional[PaymentGatewayDto]:
        gateway = await self._get_one(PaymentGateway, PaymentGateway.id == gateway_id)
        return self._decrypt_gateway_secret(self.to_dto(gateway))

    async def get_by_type(self, gateway_type: PaymentGatewayType) -> Optional[PaymentGatewayDto]:
        gateway = await self._get_one(PaymentGateway, PaymentGateway.type == gateway_type)
        return self._decrypt_gateway_secret(self.to_dto(gateway))

    async def get_all(self) -> list[PaymentGatewayDto]:
        gateways = await self._get_many(PaymentGateway, order_by=[PaymentGateway.id.asc()])
        return self.to_dto_list(gateways)

    async def update(
        self,
        gateway_id: PaymentGatewayDto,
        **data: Any,
    ) -> Optional[PaymentGatewayDto]:
        gateway = await self._update(
            PaymentGateway,
            PaymentGateway.id == gateway_id,
            **self._encrypt_gateway_secret(data),
        )
        self._decrypt_gateway_secret(self.to_dto(gateway))

    async def delete(self, gateway_id: int) -> bool:
        return await self._delete(PaymentGateway, PaymentGateway.id == gateway_id)

    async def filter_active(self, is_active: bool = True) -> list[PaymentGatewayDto]:
        gateways = await self._get_many(PaymentGateway, PaymentGateway.is_active == is_active)
        return self.to_dto_list(gateways)
