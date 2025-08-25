from typing import Any, Optional

from aiogram.types import BufferedInputFile
from dishka import FromDishka
from dishka.integrations.taskiq import inject

from src.core.config.app import AppConfig
from src.core.enums import MediaType, SystemNotificationType, UserRole
from src.core.utils.message_payload import MessagePayload
from src.infrastructure.taskiq.broker import broker
from src.services import NotificationService, UserService


@broker.task
@inject
async def send_system_notification_task(
    ntf_type: SystemNotificationType,
    text_key: str,
    user_service: FromDishka[UserService],
    notification_service: FromDishka[NotificationService],
    **kwargs: Any,
) -> None:
    devs = await user_service.get_by_role(role=UserRole.DEV)
    await notification_service.system_notify(
        devs=devs,
        payload=MessagePayload(
            text_key=text_key,
            auto_delete_after=None,
            add_close_button=True,
            kwargs=kwargs,
        ),
        ntf_type=ntf_type,
    )


@broker.task
@inject
async def send_error_notification_task(
    update_id: int,
    user_id: Optional[str],
    user_name: Optional[str],
    error_type_name: str,
    error_message: str,
    traceback_str: str,
    config: FromDishka[AppConfig],
    user_service: FromDishka[UserService],
    notification_service: FromDishka[NotificationService],
) -> None:
    dev_user = await user_service.get(telegram_id=config.bot.dev_id)

    text = f"{error_type_name}: {error_message}"
    file_data = BufferedInputFile(
        file=traceback_str.encode(),
        filename=f"error_{update_id}.txt",
    )

    await notification_service.notify_super_dev(
        dev=dev_user,
        payload=MessagePayload(
            text_key="ntf-event-error",
            media=file_data,
            media_type=MediaType.DOCUMENT,
            auto_delete_after=None,
            add_close_button=True,
            kwargs={
                "user": bool(user_id),
                "id": user_id,
                "name": user_name,
                "error": text,
            },
        ),
    )
