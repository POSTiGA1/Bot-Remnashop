from typing import Optional

from aiogram import Bot
from fluentogram import TranslatorHub
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.core.enums import PlanAvailability
from src.infrastructure.database import UnitOfWork
from src.infrastructure.database.models.dto import PlanDto, UserDto
from src.infrastructure.redis import RedisRepository

from .base import BaseService

# TODO: Make plan sorting customizable for display


class PlanService(BaseService):
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

    async def create(self, plan: PlanDto) -> PlanDto:
        return await self.uow.repository.plans.create(plan)

    async def get(self, plan_id: int) -> Optional[PlanDto]:
        return await self.uow.repository.plans.get(plan_id)

    async def get_by_name(self, name: str) -> Optional[PlanDto]:
        return await self.uow.repository.plans.get_by_name(name)

    async def get_all(self) -> list[PlanDto]:
        return await self.uow.repository.plans.get_all()

    async def update(self, plan: PlanDto) -> Optional[PlanDto]:
        return await self.uow.repository.plans.update(plan)

    async def delete(self, plan_id: int) -> bool:
        return await self.uow.repository.plans.delete(plan_id)

    async def count(self) -> int:
        return await self.uow.repository.plans.count()

    async def get_available_plans(self, user: UserDto) -> list[PlanDto]:
        plans: list[PlanDto] = await self.uow.repository.plans.filter_active()

        # is_new_user = user_dto.subscription_status is None
        # is_existing_user = user_dto.subscription_status is not None
        # is_invited_user = user_dto.is_invited

        filtered_plans = []
        for plan in plans:
            match plan.availability:
                case PlanAvailability.ALL:
                    filtered_plans.append(plan)
                # case PlanAvailability.NEW if is_new_user:
                #     filtered_plans.append(plan)
                # case PlanAvailability.EXISTING if is_existing_user:
                #     filtered_plans.append(plan)
                # case PlanAvailability.INVITED if is_invited_user:
                #     filtered_plans.append(plan)
                case PlanAvailability.ALLOWED if user.telegram_id in plan.allowed_user_ids:
                    filtered_plans.append(plan)

        return filtered_plans
