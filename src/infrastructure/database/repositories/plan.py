from typing import Optional, cast

from sqlalchemy import select
from sqlalchemy.sql.functions import count

from src.core.enums import PlanAvailability, PlanType
from src.infrastructure.database.models.dto import PlanDto
from src.infrastructure.database.models.sql import Plan, PlanDuration, PlanPrice

from .base import BaseRepository


class PlanRepository(BaseRepository):
    async def create(self, plan_dto: PlanDto) -> PlanDto:
        created_plan = Plan(**plan_dto.model_dump(exclude={"durations"}))

        for duration_dto in plan_dto.durations:
            db_duration = PlanDuration(**duration_dto.model_dump(exclude={"prices"}))
            created_plan.durations.append(db_duration)
            db_duration.plan = created_plan

            for price_dto in duration_dto.prices:
                db_price = PlanPrice(**price_dto.model_dump())
                db_duration.prices.append(db_price)
                db_price.plan_duration = db_duration

        await self.create_instance(created_plan)
        return self.to_dto(created_plan)

    async def get(self, plan_id: int) -> Optional[PlanDto]:
        plan = await self._get_one(Plan, Plan.id == plan_id)
        return self.to_dto(plan)

    async def get_by_name(self, name: str) -> Optional[PlanDto]:
        plan = await self._get_one(Plan, Plan.name == name)
        return self.to_dto(plan)

    async def get_all(self) -> list[PlanDto]:
        plans = await self._get_many(Plan)
        return self.to_dto_list(plans)

    async def update(self, plan_dto: PlanDto) -> Optional[PlanDto]:
        plan_instance = Plan(**plan_dto.model_dump(exclude={"durations"}))

        plan_instance.durations = []
        for duration_dto in plan_dto.durations:
            duration_instance = PlanDuration(
                **duration_dto.model_dump(exclude={"prices"}),
                plan=plan_instance,
            )

            duration_instance.prices = []
            for price_dto in duration_dto.prices:
                price_instance = PlanPrice(
                    **price_dto.model_dump(),
                    plan_duration=duration_instance,
                )
                duration_instance.prices.append(price_instance)

            plan_instance.durations.append(duration_instance)

        updated_plan = await self.merge_instance(plan_instance)
        return self.to_dto(updated_plan)

    async def delete(self, plan_id: int) -> bool:
        return await self._delete(Plan, Plan.id == plan_id)

    async def count(self) -> int:
        return cast(int, await self.session.scalar(select(count(Plan.id))))

    async def filter_by_type(self, plan_type: PlanType) -> list[PlanDto]:
        plans = await self._get_many(Plan, Plan.type == plan_type)
        return self.to_dto_list(plans)

    async def filter_by_availability(self, availability: PlanAvailability) -> list[PlanDto]:
        plans = await self._get_many(Plan, Plan.availability == availability)
        return self.to_dto_list(plans)

    async def filter_active(self, is_active: bool = True) -> list[PlanDto]:
        plans = await self._get_many(Plan, Plan.is_active == is_active)
        return self.to_dto_list(plans)
