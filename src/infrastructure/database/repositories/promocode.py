from typing import Any, Optional, cast

from sqlalchemy import select
from sqlalchemy.sql.functions import count

from src.core.enums import PromocodeType
from src.infrastructure.database.models.dto import PromocodeDto
from src.infrastructure.database.models.sql import Promocode

from .base import BaseRepository


class PromocodeRepository(BaseRepository):
    async def get(self, promocode_id: int) -> Optional[PromocodeDto]:
        promocode = await self._get_one(Promocode, Promocode.id == promocode_id)
        return self.to_dto(promocode)

    async def get_by_code(self, code: str) -> Optional[PromocodeDto]:
        promocode = await self._get_one(Promocode, Promocode.code == code)
        return self.to_dto(promocode)

    async def update(self, promocode_id: int, **data: Any) -> Optional[PromocodeDto]:
        updated_promocode = await self._update(Promocode, Promocode.id == promocode_id, **data)
        return self.to_dto(updated_promocode)

    async def delete(self, promocode_id: int) -> bool:
        return await self._delete(Promocode, Promocode.id == promocode_id)

    async def count(self) -> int:
        return cast(int, await self.session.scalar(select(count(Promocode.id))))

    async def filter_by_type(self, promocode_type: PromocodeType) -> list[PromocodeDto]:
        promocodes = await self._get_many(Promocode, Promocode.type == promocode_type)
        return self.to_dto_list(promocodes)

    async def filter_active(self, is_active: bool = True) -> list[PromocodeDto]:
        promocodes = await self._get_many(Promocode, Promocode.is_active == is_active)
        return self.to_dto_list(promocodes)

    async def filter_multi_use(self, is_multi_use: bool = True) -> list[PromocodeDto]:
        promocodes = await self._get_many(Promocode, Promocode.is_multi_use == is_multi_use)
        return self.to_dto_list(promocodes)
