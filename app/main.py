from datetime import date

from fastapi import FastAPI, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.schemas import (
    AvailableSlotResponse,
    AvailableSlotsResponse,
    BookingCreateRequest,
    BookingResponse,
)
from app.service import BookingService


def create_app() -> FastAPI:
    app = FastAPI(title="Meeting Room Booking Service")
    app.state.booking_service = BookingService()

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "request validation failed",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @app.post(
        "/bookings",
        response_model=BookingResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_booking(payload: BookingCreateRequest) -> BookingResponse:
        booking = app.state.booking_service.create_booking(
            room_id=payload.room_id,
            title=payload.title,
            start_at=payload.start_at,
            end_at=payload.end_at,
        )
        return BookingResponse.model_validate(booking, from_attributes=True)

    @app.get("/bookings/{booking_id}", response_model=BookingResponse)
    def get_booking(booking_id: int) -> BookingResponse:
        booking = app.state.booking_service.get_booking(booking_id)
        return BookingResponse.model_validate(booking, from_attributes=True)

    @app.get("/bookings", response_model=list[BookingResponse])
    def list_bookings(
        room_id: str = Query(min_length=1),
        date: date = Query(),
    ) -> list[BookingResponse]:
        bookings = app.state.booking_service.list_bookings(
            room_id=room_id.strip(), day=date
        )
        return [
            BookingResponse.model_validate(item, from_attributes=True)
            for item in bookings
        ]

    @app.delete("/bookings/{booking_id}", response_model=BookingResponse)
    def cancel_booking(booking_id: int) -> BookingResponse:
        booking = app.state.booking_service.cancel_booking(booking_id)
        return BookingResponse.model_validate(booking, from_attributes=True)

    @app.get(
        "/rooms/{room_id}/available-slots",
        response_model=AvailableSlotsResponse,
    )
    def get_available_slots(
        room_id: str,
        date: date = Query(),
    ) -> AvailableSlotsResponse:
        normalized_room_id = room_id.strip()
        slots = app.state.booking_service.get_available_slots(
            room_id=normalized_room_id, day=date
        )
        return AvailableSlotsResponse(
            room_id=normalized_room_id,
            date=date,
            slots=[
                AvailableSlotResponse(start_at=start_at, end_at=end_at)
                for start_at, end_at in slots
            ],
        )

    return app


app = create_app()
