from fastapi.testclient import TestClient

from app.main import create_app


def build_client() -> TestClient:
    return TestClient(create_app())


def test_create_and_get_booking() -> None:
    client = build_client()

    create_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Backend sync",
            "start_at": "2026-04-01T10:00:00",
            "end_at": "2026-04-01T11:00:00",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["status"] == "active"

    get_response = client.get("/bookings/1")
    assert get_response.status_code == 200
    assert get_response.json() == created


def test_rejects_overlapping_booking_for_same_room() -> None:
    client = build_client()

    first_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Team 1",
            "start_at": "2026-04-01T10:00:00",
            "end_at": "2026-04-01T11:00:00",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Team 2",
            "start_at": "2026-04-01T10:30:00",
            "end_at": "2026-04-01T11:30:00",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "booking_conflict"


def test_allows_adjacent_bookings() -> None:
    client = build_client()

    first_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Morning",
            "start_at": "2026-04-01T09:00:00",
            "end_at": "2026-04-01T10:00:00",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Next meeting",
            "start_at": "2026-04-01T10:00:00",
            "end_at": "2026-04-01T11:00:00",
        },
    )

    assert second_response.status_code == 201


def test_cancelled_booking_does_not_block_new_booking() -> None:
    client = build_client()

    create_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "To cancel",
            "start_at": "2026-04-01T13:00:00",
            "end_at": "2026-04-01T14:00:00",
        },
    )
    assert create_response.status_code == 201

    cancel_response = client.delete("/bookings/1")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    recreate_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Replacement",
            "start_at": "2026-04-01T13:00:00",
            "end_at": "2026-04-01T14:00:00",
        },
    )
    assert recreate_response.status_code == 201


def test_returns_sorted_bookings_for_room_and_date() -> None:
    client = build_client()

    for title, start_at, end_at in [
        ("Late", "2026-04-02T15:00:00", "2026-04-02T16:00:00"),
        ("Early", "2026-04-02T09:00:00", "2026-04-02T10:00:00"),
        ("Other room", "2026-04-02T11:00:00", "2026-04-02T12:00:00"),
    ]:
        room_id = "room-b" if title != "Other room" else "room-c"
        response = client.post(
            "/bookings",
            json={
                "room_id": room_id,
                "title": title,
                "start_at": start_at,
                "end_at": end_at,
            },
        )
        assert response.status_code == 201

    list_response = client.get(
        "/bookings", params={"room_id": "room-b", "date": "2026-04-02"}
    )
    assert list_response.status_code == 200

    titles = [item["title"] for item in list_response.json()]
    assert titles == ["Early", "Late"]


def test_available_slots_are_built_inside_selected_day() -> None:
    client = build_client()

    for payload in [
        {
            "room_id": "room-a",
            "title": "First",
            "start_at": "2026-04-03T09:00:00",
            "end_at": "2026-04-03T10:00:00",
        },
        {
            "room_id": "room-a",
            "title": "Second",
            "start_at": "2026-04-03T12:00:00",
            "end_at": "2026-04-03T13:30:00",
        },
    ]:
        response = client.post("/bookings", json=payload)
        assert response.status_code == 201

    slots_response = client.get(
        "/rooms/room-a/available-slots", params={"date": "2026-04-03"}
    )
    assert slots_response.status_code == 200

    slots = slots_response.json()["slots"]
    assert slots == [
        {"start_at": "2026-04-03T00:00:00", "end_at": "2026-04-03T09:00:00"},
        {"start_at": "2026-04-03T10:00:00", "end_at": "2026-04-03T12:00:00"},
        {"start_at": "2026-04-03T13:30:00", "end_at": "2026-04-04T00:00:00"},
    ]


def test_returns_clear_errors_for_invalid_input_and_missing_booking() -> None:
    client = build_client()

    invalid_interval_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Broken",
            "start_at": "2026-04-01T11:00:00",
            "end_at": "2026-04-01T10:00:00",
        },
    )
    assert invalid_interval_response.status_code == 422
    assert (
        invalid_interval_response.json()["error"]["code"] == "validation_error"
    )

    invalid_datetime_response = client.post(
        "/bookings",
        json={
            "room_id": "room-a",
            "title": "Broken datetime",
            "start_at": "not-a-datetime",
            "end_at": "2026-04-01T10:00:00",
        },
    )
    assert invalid_datetime_response.status_code == 422

    missing_booking_response = client.delete("/bookings/999")
    assert missing_booking_response.status_code == 404
    assert (
        missing_booking_response.json()["error"]["code"] == "booking_not_found"
    )
