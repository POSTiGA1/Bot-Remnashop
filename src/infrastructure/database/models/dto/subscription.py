from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .plan import PlanDto, PlanSnapshotDto
    from .user import BaseUserDto

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.enums import PlanType, SubscriptionStatus

from .base import TrackableDto


class BaseSubscriptionDto(TrackableDto):
    id: Optional[int] = Field(default=None, frozen=True)

    user_remna_id: UUID

    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    is_trial: bool = False

    traffic_limit: int
    device_limit: int
    internal_squads: list[UUID]

    expire_at: datetime
    url: str

    plan: "PlanSnapshotDto"

    created_at: Optional[datetime] = Field(default=None, frozen=True)
    updated_at: Optional[datetime] = Field(default=None, frozen=True)

    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def is_unlimited(self) -> bool:
        return self.expire_at.year == 2099

    @property
    def get_subscription_type(self) -> PlanType:
        has_traffic = self.traffic_limit > 0
        has_devices = self.device_limit > 0

        if has_traffic and has_devices:
            return PlanType.BOTH
        elif has_traffic:
            return PlanType.TRAFFIC
        elif has_devices:
            return PlanType.DEVICES
        else:
            return PlanType.UNLIMITED

    @property
    def has_devices_limit(self) -> bool:
        return self.get_subscription_type in (PlanType.DEVICES, PlanType.BOTH)

    @property
    def has_traffic_limit(self) -> bool:
        return self.get_subscription_type in (PlanType.TRAFFIC, PlanType.BOTH)

    def has_same_plan(self, plan: "PlanDto") -> bool:
        if plan is None or self.plan is None:
            return False

        return (
            self.plan.id == plan.id
            and self.plan.name == plan.name
            and self.plan.type == plan.type
            and self.plan.traffic_limit == plan.traffic_limit
            and self.plan.device_limit == plan.device_limit
            and self.plan.internal_squads == plan.internal_squads
        )

    def find_matching_plan(self, plans: list[PlanDto]) -> Optional[PlanDto]:
        return next((plan for plan in plans if self.has_same_plan(plan)), None)


class SubscriptionDto(BaseSubscriptionDto):
    user: Optional["BaseUserDto"] = None
