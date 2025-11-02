from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from src.core.enums import BroadcastAudience, BroadcastMessageStatus, BroadcastStatus
from src.core.utils.message_payload import MessagePayload

from .base import TrackableDto


class BroadcastDto(TrackableDto):
    id: Optional[int] = Field(default=None, frozen=True)
    task_id: UUID

    status: BroadcastStatus
    audience: BroadcastAudience

    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    payload: MessagePayload

    messages: Optional[list["BroadcastMessageDto"]] = []

    created_at: Optional[datetime] = Field(default=None, frozen=True)
    updated_at: Optional[datetime] = Field(default=None, frozen=True)


class BroadcastMessageDto(TrackableDto):
    id: Optional[int] = Field(default=None, frozen=True)

    user_id: int
    message_id: Optional[int] = None

    status: BroadcastMessageStatus
