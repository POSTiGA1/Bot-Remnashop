from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiogram import Bot
from aiogram.types import WebhookInfo
from dishka import AsyncContainer
from fastapi import FastAPI
from loguru import logger

from src.api.endpoints import TelegramWebhookEndpoint
from src.core.enums import SystemNotificationType
from src.infrastructure.taskiq.tasks import send_system_notification_task
from src.services import CommandService, MaintenanceService, WebhookService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    telegram_webhook_endpoint: TelegramWebhookEndpoint = app.state.telegram_webhook_endpoint
    container: AsyncContainer = app.state.dishka_container

    webhook_service: WebhookService = await container.get(WebhookService)
    command_service: CommandService = await container.get(CommandService)
    maintenance_service: MaintenanceService = await container.get(MaintenanceService)

    webhook_info: WebhookInfo = await webhook_service.setup()
    if webhook_service.has_error(webhook_info):
        logger.critical(f"Webhook has a last error message: {webhook_info.last_error_message}")
        await send_system_notification_task.kiq(
            ntf_type=SystemNotificationType.BOT_LIFETIME,
            text_key="ntf-event-error-webhook",
            error=webhook_info.last_error_message,
        )

    await command_service.setup()
    await telegram_webhook_endpoint.startup()

    bot: Bot = await container.get(Bot)
    bot_info = await bot.get_me()
    states: dict[bool | None, str] = {True: "Enabled", False: "Disabled", None: "Unknown"}

    logger.info("Bot settings:")
    logger.info("-----------------------")
    logger.info(f"Groups Mode  - {states[bot_info.can_join_groups]}")
    logger.info(f"Privacy Mode - {states[not bot_info.can_read_all_group_messages]}")
    logger.info(f"Inline Mode  - {states[bot_info.supports_inline_queries]}")
    logger.info("-----------------------")

    maintenance_mode = await maintenance_service.get_current_mode()
    logger.warning(f"Bot in maintenance mode: '{maintenance_mode}'")

    await send_system_notification_task.kiq(
        ntf_type=SystemNotificationType.BOT_LIFETIME,
        text_key="ntf-event-bot-startup",
        mode=maintenance_mode,
    )

    yield

    await send_system_notification_task.kiq(
        ntf_type=SystemNotificationType.BOT_LIFETIME,
        text_key="ntf-event-bot-shutdown",
    )

    await telegram_webhook_endpoint.shutdown()
    await command_service.delete()
    await webhook_service.delete()

    await container.close()
