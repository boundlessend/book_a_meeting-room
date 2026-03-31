from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BookingStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


@dataclass()
class Booking:
    id: int
    room_id: str
    title: str
    start_at: datetime
    end_at: datetime
    status: BookingStatus
