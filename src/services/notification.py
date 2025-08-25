import asyncio
from typing import Any, Optional, cast

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from src.bot.states import Notification
from src.core.enums import Locale, SystemNotificationType, UserNotificationType, UserRole
from src.core.storage_keys import SystemNotificationSettingsKey, UserNotificationSettingsKey
from src.core.utils.message_payload import MessagePayload
from src.core.utils.types import AnyKeyboard
from src.infrastructure.database.models.dto import UserDto
from src.infrastructure.redis.notification_settings import (
    SystemNotificationDto,
    UserNotificationDto,
)

from .base import BaseService


class NotificationService(BaseService):
    async def notify_user(
        self,
        user: Optional[UserDto],
        payload: MessagePayload,
        ntf_type: Optional[UserNotificationType] = None,
    ) -> bool:
        if not user:
            logger.warning("Skipping user notification: user object is empty")
            return False

        if ntf_type and not await self._is_notification_enabled(ntf_type):
            logger.debug(
                f"Skipping user notification for '{user.telegram_id}': "
                f"notification type is disabled in settings"
            )
            return False

        logger.debug(
            f"Attempting to send user notification '{payload.text_key}' to '{user.telegram_id}'"
        )
        sent_message = await self._send_message(user, payload)

        return bool(sent_message)

    async def system_notify(
        self,
        devs: Optional[list[UserDto]],
        payload: MessagePayload,
        ntf_type: SystemNotificationType,
    ) -> list[bool]:
        if not devs:
            devs.append(self._get_temp_dev())

        if not await self._is_notification_enabled(ntf_type):
            logger.debug("Skipping system notification: notification type is disabled in settings")
            return []

        logger.debug(
            f"Attempting to send system notification '{payload.text_key}' to {len(devs)} devs"
        )

        async def send_to_dev(dev: UserDto) -> bool:
            return bool(await self._send_message(user=dev, payload=payload))

        tasks = [send_to_dev(dev) for dev in devs]
        results = await asyncio.gather(*tasks)

        return cast(list[bool], results)

    async def notify_super_dev(self, dev: Optional[UserDto], payload: MessagePayload) -> bool:
        if not dev:
            dev = self._get_temp_dev()

        if dev.telegram_id != self.config.bot.dev_id:
            logger.warning(
                f"Skipping super dev notification: user ID does not match configured dev_id "
                f"'{self.config.bot.dev_id}'"
            )
            return False

        logger.debug(
            f"Attempting to send super dev notification '{payload.text_key}' to '{dev.telegram_id}'"
        )

        return bool(await self._send_message(user=dev, payload=payload))

    #

    async def get_system_settings(self) -> SystemNotificationDto:
        settings = await self.redis_repository.get(
            key=SystemNotificationSettingsKey(),
            validator=SystemNotificationDto,
            default=SystemNotificationDto(),
        )
        return cast(SystemNotificationDto, settings)

    async def set_system_settings(self, data: SystemNotificationDto) -> None:
        await self.redis_repository.set(key=SystemNotificationSettingsKey(), value=data)

    async def get_user_settings(self) -> UserNotificationDto:
        key = UserNotificationSettingsKey()
        settings = await self.redis_repository.get(
            key=key,
            validator=UserNotificationDto,
            default=UserNotificationDto(),
        )
        return cast(UserNotificationDto, settings)

    async def set_user_settings(self, data: UserNotificationDto) -> None:
        await self.redis_repository.set(key=UserNotificationSettingsKey(), value=data)

    #

    async def _send_message(self, user: UserDto, payload: MessagePayload) -> Optional[Message]:
        i18n = self.translator_hub.get_translator_by_locale(locale=user.language)
        message_text = i18n.get(payload.text_key, **payload.kwargs) if payload.text_key else None
        message_effect_id = payload.message_effect if payload.message_effect is not None else None

        final_reply_markup = self._prepare_reply_markup(
            payload.reply_markup,
            payload.add_close_button,
            payload.auto_delete_after,
            user.language,
            user.telegram_id,
        )

        try:
            if payload.media and payload.media_type:
                send_func = payload.media_type.get_function(self.bot)
                media_arg_name = payload.media_type
                tg_payload = {
                    "chat_id": user.telegram_id,
                    "caption": message_text,
                    "reply_markup": final_reply_markup,
                    "message_effect_id": message_effect_id,
                    media_arg_name: payload.media,
                }
                sent_message = await send_func(**tg_payload)
            else:
                if payload.media and not payload.media_type:
                    logger.warning(
                        f"Validation error: Media provided but media_type is missing "
                        f"for chat '{user.telegram_id}'. Sending as text message"
                    )
                sent_message = await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text,
                    message_effect_id=message_effect_id,
                    reply_markup=final_reply_markup,
                )

            if payload.auto_delete_after is not None:
                asyncio.create_task(
                    self._schedule_message_deletion(
                        chat_id=user.telegram_id,
                        message_id=sent_message.message_id,
                        delay=payload.auto_delete_after,
                    )
                )
            return sent_message

        except Exception as exception:
            logger.error(
                f"Failed to send notification '{payload.text_key}' "
                f"to '{user.telegram_id}': {exception}",
                exc_info=True,
            )
            return None

    def _prepare_reply_markup(
        self,
        reply_markup: Optional[AnyKeyboard],
        add_close_button: bool,
        auto_delete_after: Optional[int],
        locale: Locale,
        chat_id: int,
    ) -> Optional[AnyKeyboard]:
        if not add_close_button or auto_delete_after is not None:
            return reply_markup

        close_button = self._get_close_notification_button(locale=locale)

        if reply_markup is None:
            return self._get_close_notification_keyboard(close_button)

        if isinstance(reply_markup, InlineKeyboardMarkup):
            builder = InlineKeyboardBuilder.from_markup(reply_markup)
            builder.row(close_button)
            return builder.as_markup()

        logger.warning(
            f"Unsupported reply_markup type '{type(reply_markup).__name__}' "
            f"for chat '{chat_id}'. Close button will not be added"
        )
        return reply_markup

    def _get_close_notification_button(self, locale: Locale) -> InlineKeyboardButton:
        i18n = self.translator_hub.get_translator_by_locale(locale=locale)
        button_text = i18n.get("btn-close-notification")
        return InlineKeyboardButton(
            text=button_text,
            callback_data=Notification.CLOSE.state,
        )

    def _get_close_notification_keyboard(
        self,
        button: InlineKeyboardButton,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(button)
        return builder.as_markup()

    def _merge_keyboards_with_close_button(
        self,
        existing_markup: InlineKeyboardMarkup,
        locale: Locale,
    ) -> InlineKeyboardMarkup:
        merged_builder = InlineKeyboardBuilder()

        for row in existing_markup.inline_keyboard:
            merged_builder.row(*row)

        merged_builder.row(self._get_close_notification_button(locale=locale))
        return merged_builder.as_markup()

    async def _schedule_message_deletion(self, chat_id: int, message_id: int, delay: int) -> None:
        logger.debug(
            f"Scheduling message '{message_id}' for auto-deletion in {delay}s (chat {chat_id})"
        )
        try:
            await asyncio.sleep(delay)
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.debug(
                f"Message '{message_id}' in chat '{chat_id}' deleted after {delay} seconds"
            )
        except Exception as exception:
            logger.error(
                f"Failed to delete message '{message_id}' in chat '{chat_id}': {exception}"
            )

    async def _is_notification_enabled(self, ntf_type: Any) -> bool:
        if isinstance(ntf_type, UserNotificationType):
            settings = await self.get_user_settings()
        elif isinstance(ntf_type, SystemNotificationType):
            settings = await self.get_system_settings()
        else:
            return False

        settings_data = settings.model_dump()
        return bool(settings_data.get(ntf_type.value, False))

    def _get_temp_dev(self) -> UserDto:
        temp_dev = UserDto(
            telegram_id=self.config.bot.dev_id,
            name="TempDev",
            role=UserRole.DEV,
            language=Locale.EN,
        )

        logger.warning("Dev is empty! Adding a fallback dev from environment config")
        return temp_dev
