from typing import Any, Awaitable, Callable

from aiogram.types import TelegramObject
from dishka import AsyncContainer

from src.core.constants import CONTAINER_KEY, USER_KEY
from src.core.enums import MiddlewareEventType
from src.infrastructure.database.models.dto import UserDto
from src.services.access import AccessService

from .base import EventTypedMiddleware


class AccessMiddleware(EventTypedMiddleware):
    __event_types__ = [MiddlewareEventType.MESSAGE, MiddlewareEventType.CALLBACK_QUERY]

    async def middleware_logic(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: AsyncContainer = data[CONTAINER_KEY]
        user: UserDto = data[USER_KEY]

        access_service: AccessService = await container.get(AccessService)

        if not await access_service.is_access_allowed(user=user, event=event):
            return

        return await handler(event, data)
