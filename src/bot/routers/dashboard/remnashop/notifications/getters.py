from enum import Enum
from typing import Any, Type

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.core.enums import SystemNotificationType, UserNotificationType
from src.services import NotificationService


async def _get_notification_types_data(
    settings: Any,
    notification_enum: Type[Enum],
) -> list[dict[str, Any]]:
    return [
        {"type": member.value, "enabled": getattr(settings, member.value)}
        for member in notification_enum
        if hasattr(settings, member.value)
    ]


@inject
async def user_types_getter(
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
    **kwargs: Any,
) -> dict[str, Any]:
    settings = await notification_service.get_user_settings()
    notification_types_data = await _get_notification_types_data(settings, UserNotificationType)
    return {"types": notification_types_data}


@inject
async def system_types_getter(
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
    **kwargs: Any,
) -> dict[str, Any]:
    settings = await notification_service.get_system_settings()
    notification_types_data = await _get_notification_types_data(settings, SystemNotificationType)
    return {"types": notification_types_data}
