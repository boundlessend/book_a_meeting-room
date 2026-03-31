from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import BookingStatus


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class BookingCreateRequest(BaseModel):
    room_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    start_at: datetime
    end_at: datetime

    @field_validator("room_id", "title")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @field_validator("start_at", "end_at")
    @classmethod
    def require_naive_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            raise ValueError(
                "timezone-aware datetime is not supported; use naive local datetime"
            )
        return value

    @model_validator(mode="after")
    def validate_interval(self) -> "BookingCreateRequest":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be greater than start_at")
        return self


class BookingResponse(BaseModel):
    id: int
    room_id: str
    title: str
    start_at: datetime
    end_at: datetime
    status: BookingStatus


class AvailableSlotResponse(BaseModel):
    start_at: datetime
    end_at: datetime


class AvailableSlotsResponse(BaseModel):
    room_id: str
    date: date
    slots: list[AvailableSlotResponse]
