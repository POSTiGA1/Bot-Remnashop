from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .plan import PlanSnapshotDto
    from .user import BaseUserDto

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from src.core.enums import Currency, PaymentGatewayType, PurchaseType, TransactionStatus

from .base import TrackableDto


class PriceDetailsDto(TrackableDto):
    original_amount: Decimal = Decimal(1)
    discount_percent: int = 0
    final_amount: Decimal = Decimal(1)

    @property
    def is_free(self) -> bool:
        return self.final_amount == 0


class BaseTransactionDto(TrackableDto):
    id: Optional[int] = Field(default=None, frozen=True)
    payment_id: UUID

    status: TransactionStatus
    is_test: bool = False

    purchase_type: PurchaseType
    gateway_type: PaymentGatewayType

    pricing: PriceDetailsDto
    currency: Currency
    plan: "PlanSnapshotDto"

    created_at: Optional[datetime] = Field(default=None, frozen=True)
    updated_at: Optional[datetime] = Field(default=None, frozen=True)

    @property
    def is_completed(self) -> bool:
        return self.status == TransactionStatus.COMPLETED


class TransactionDto(BaseTransactionDto):
    user: Optional["BaseUserDto"] = None
