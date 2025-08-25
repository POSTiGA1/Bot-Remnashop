from typing import Optional

from pydantic import Field, SecretStr

from src.core.enums import Currency, PaymentGatewayType

from .base import TrackableModel


class PaymentGatewayDto(TrackableModel):
    id: Optional[int] = Field(default=None, frozen=True)

    type: PaymentGatewayType
    currency: Currency
    is_active: bool

    merchant_id: Optional[str]
    secret: Optional[SecretStr]
