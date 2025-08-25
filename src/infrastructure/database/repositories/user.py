from typing import Any, Optional, cast

from sqlalchemy import func, or_, select
from sqlalchemy.sql.functions import count

from src.core.enums import UserRole
from src.infrastructure.database.models.dto import UserDto
from src.infrastructure.database.models.sql import User

from .base import BaseRepository


class UserRepository(BaseRepository):
    async def create(self, user_dto: UserDto) -> UserDto:
        user = User(**user_dto.model_dump())
        created_user = await self.create_instance(user)
        return self.to_dto(created_user)

    async def get(self, telegram_id: int) -> Optional[UserDto]:
        user = await self._get_one(User, User.telegram_id == telegram_id)
        return self.to_dto(user)

    async def get_by_partial_name(self, query: str) -> list[UserDto]:
        search_pattern = f"%{query.lower()}%"
        conditions = [func.lower(User.name).like(search_pattern)]
        users = await self._get_many(User, or_(*conditions))
        return self.to_dto_list(users)

    async def update(self, telegram_id: int, **data: Any) -> Optional[UserDto]:
        updated_user = await self._update(User, User.telegram_id == telegram_id, **data)
        return self.to_dto(updated_user)

    async def delete(self, telegram_id: int) -> int:
        return await self._delete(User, User.telegram_id == telegram_id)

    async def count(self) -> int:
        return cast(int, await self.session.scalar(select(count(User.id))))

    async def filter_by_role(self, role: UserRole) -> list[UserDto]:
        users = await self._get_many(User, User.role == role)
        return self.to_dto_list(users)

    async def filter_by_blocked(self, blocked: bool = True) -> list[UserDto]:
        users = await self._get_many(User, User.is_blocked == blocked)
        return self.to_dto_list(users)
