import asyncio

from aiogram import Bot
from dishka.integrations.taskiq import FromDishka, inject

from src.core.constants import BATCH_DELAY, BATCH_SIZE
from src.core.enums import BroadcastMessageStatus, BroadcastStatus
from src.core.utils.iterables import chunked
from src.core.utils.message_payload import MessagePayload
from src.infrastructure.database.models.dto import BroadcastDto, BroadcastMessageDto, UserDto
from src.infrastructure.taskiq.broker import broker
from src.services.broadcast import BroadcastService
from src.services.notification import NotificationService


@broker.task
@inject
async def send_broadcast_task(
    broadcast: BroadcastDto,
    users: list[UserDto],
    payload: MessagePayload,
    notification_service: FromDishka[NotificationService],
    broadcast_service: FromDishka[BroadcastService],
) -> None:
    broadcast_messages = await broadcast_service.create_messages(
        broadcast.id,  # type: ignore[arg-type]
        [
            BroadcastMessageDto(user_id=user.telegram_id, status=BroadcastMessageStatus.PENDING)
            for user in users
        ],
    )

    try:
        for batch in chunked(list(zip(users, broadcast_messages)), BATCH_SIZE):
            for user, message in batch:
                status = await broadcast_service.get_status(broadcast.task_id)

                if status == BroadcastStatus.CANCELED:
                    return

                try:
                    tg_message = await notification_service.notify_user(user=user, payload=payload)
                    if tg_message:
                        message.message_id = tg_message.message_id
                        message.status = BroadcastMessageStatus.SENT
                        broadcast.success_count += 1
                    else:
                        message.status = BroadcastMessageStatus.FAILED
                        broadcast.failed_count += 1
                except Exception:
                    message.status = BroadcastMessageStatus.FAILED
                    broadcast.failed_count += 1

                await broadcast_service.update_message(broadcast.id, message)  # type: ignore[arg-type]

            await asyncio.sleep(BATCH_DELAY)
            await broadcast_service.update(broadcast)

        broadcast.status = BroadcastStatus.COMPLETED
        await broadcast_service.update(broadcast)

    except Exception:
        broadcast.status = BroadcastStatus.ERROR
        await broadcast_service.update(broadcast)


@broker.task
@inject
async def delete_broadcast_task(
    broadcast: BroadcastDto,
    bot: FromDishka[Bot],
    broadcast_service: FromDishka[BroadcastService],
) -> tuple[int, int, int]:
    deleted_count = 0
    failed_count = 0

    if not broadcast.messages:
        raise ValueError(f"Broadcast '{broadcast.id}' messages is empty")

    for message in broadcast.messages:
        if message.status not in (BroadcastMessageStatus.SENT, BroadcastMessageStatus.EDITED):
            continue

        if not message.message_id:
            continue

        try:
            deleted = await bot.delete_message(
                chat_id=message.user_id, message_id=message.message_id
            )

            if deleted:
                message.status = BroadcastMessageStatus.DELETED
                await broadcast_service.update_message(
                    broadcast_id=broadcast.id,  # type: ignore[arg-type]
                    message=message,
                )
                deleted_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

    return len(broadcast.messages), deleted_count, failed_count
