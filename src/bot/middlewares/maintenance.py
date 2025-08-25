from typing import Any, Awaitable, Callable

from aiogram.types import TelegramObject
from dishka import AsyncContainer

from src.core.constants import CONTAINER_KEY, USER_KEY
from src.core.enums import MiddlewareEventType
from src.core.utils.message_payload import MessagePayload
from src.infrastructure.database.models.dto import UserDto
from src.services import MaintenanceService, NotificationService

from .base import EventTypedMiddleware


class MaintenanceMiddleware(EventTypedMiddleware):
    __event_types__ = [MiddlewareEventType.MESSAGE, MiddlewareEventType.CALLBACK_QUERY]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: AsyncContainer = data[CONTAINER_KEY]
        user: UserDto = data[USER_KEY]

        maintenance_service: MaintenanceService = await container.get(MaintenanceService)
        notification_service: NotificationService = await container.get(NotificationService)

        if not await maintenance_service.is_access_allowed(user=user, event=event):
            await notification_service.notify_user(
                telegram_id=user.telegram_id,
                payload=MessagePayload(text_key="ntf-maintenance-denied-global"),
            )
            return

        return await handler(event, data)
