# book-a-meeting-room

## что есть

- создание брони;
- чтение одной брони;
- список броней по комнате и дате;
- отмена брони;
- список доступных слотов по комнате и дате;
- явный формат ошибок;
- `pytest`-тесты на happy path и негативные сценарии.

## что внутри

- Python
- FastAPI
- Pydantic
- uvicorn
- pytest
- in-memory хранение на стандартной библиотеке python

## cтруктура проекта

```text
app/
  errors.py
  main.py
  models.py
  schemas.py
  service.py
tests/
  test_bookings.py
README.md
requirements.txt
```

## запуск

### 1. создать и активировать виртуальное окружение

macOS / linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. установить зависимости

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. поднять сервис

```bash
uvicorn app.main:app --reload
```

Сервис будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Запуск тестов

```bash
pytest
```

## формат ошибок

все доменные и валидационные ошибки возвращаются в одном формате:

```json
{
  "error": {
    "code": "booking_conflict",
    "message": "booking time intersects with an active booking",
    "details": {
      "conflicting_booking_id": 1,
      "room_id": "room-a",
      "start_at": "2026-04-01T10:30:00",
      "end_at": "2026-04-01T11:30:00"
    }
  }
}
```

## API

### 1. создать бронь

`POST /bookings`

пример тела:

```json
{
  "room_id": "room-a",
  "title": "Backend sync",
  "start_at": "2026-04-01T10:00:00",
  "end_at": "2026-04-01T11:00:00"
}
```

пример ответа:

```json
{
  "id": 1,
  "room_id": "room-a",
  "title": "Backend sync",
  "start_at": "2026-04-01T10:00:00",
  "end_at": "2026-04-01T11:00:00",
  "status": "active"
}
```

### 2. получить одну бронь

`GET /bookings/{booking_id}`

### 3. получить список броней по комнате и дате

`GET /bookings?room_id=room-a&date=2026-04-01`

возвращаются брони выбранной комнаты, которые пересекают выбранную дату. список отсортирован по `start_at`.

### 4. отменить бронь

`DELETE /bookings/{booking_id}`

возвращает обновленную бронь со статусом `cancelled`.

### 5. получить доступные слоты по комнате и дате

`GET /rooms/{room_id}/available-slots?date=2026-04-01`

возвращаются свободные интервалы внутри выбранной даты от `00:00:00` до `24:00:00`.

## для ручной проверки ручной проверки

### успешное создание брони

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "room-a",
    "title": "Daily sync",
    "start_at": "2026-04-01T10:00:00",
    "end_at": "2026-04-01T11:00:00"
  }'
```

ожидание: `201 Created`, в ответе есть `id` и `status=active`.

### запрет пересечения интервалов

после прошлого:

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "room-a",
    "title": "Conflict meeting",
    "start_at": "2026-04-01T10:30:00",
    "end_at": "2026-04-01T11:30:00"
  }'
```

ожидание: `409 Conflict`, код ошибки `booking_conflict`.

### соседние интервалы допустимы

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "room-a",
    "title": "Next meeting",
    "start_at": "2026-04-01T11:00:00",
    "end_at": "2026-04-01T12:00:00"
  }'
```

ожидание: `201 Created`, т.к. первая бронь закончилась ровно в момент начала второй.

### список брони по комнате и дате

```bash
curl "http://127.0.0.1:8000/bookings?room_id=room-a&date=2026-04-01"
```

ожидание: список брони комнаты `room-a` за дату `2026-04-01`, отсортированный по `start_at`.

### отмена брони

```bash
curl -X DELETE http://127.0.0.1:8000/bookings/1
```

ожидание: `200 OK`, в ответе у брони статус `cancelled`.

### освобождение слота после отмены

после сценария отмены брони:

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "room-a",
    "title": "Rebooked slot",
    "start_at": "2026-04-01T10:00:00",
    "end_at": "2026-04-01T11:00:00"
  }'
```

ожидание: `201 Created`, потому что отмененная бронь больше не блокирует слот.

### список доступных слотов

```bash
curl "http://127.0.0.1:8000/rooms/room-a/available-slots?date=2026-04-01"
```

ожидание: свободные интервалы внутри выбранной даты, не занятые активными бронями.

## допущения

1. `room_id` — это строковый идентификатор переговорки. Отдельный справочник комнат не вводился, чтобы не добавлять лишнюю сущность вне ТЗ.
2. Сервис принимает **naive datetime** в формате ISO 8601 без timezone, например `2026-04-01T10:00:00`.
3. Доступные слоты считаются внутри выбранной даты как интервалы в пределах `[00:00, 24:00)`.
4. В списке броней возвращаются все брони комнаты, которые пересекают выбранную дату, включая отмененные: это позволяет видеть текущий статус в одном месте.
5. Повторная отмена уже отмененной брони считается ошибкой `409`, потому что состояние уже изменено ранее.

## как определяется конфликт интервалов

Используется правило полуинтервалов:

```text
[start_at, end_at)
```

две активные брони конфликтуют, если одновременно выполняется:

```text
new_start < existing_end AND existing_start < new_end
```

Следствия:

- `10:00–11:00` и `11:00–12:00` **не конфликтуют**;
- `10:00–11:00` и `10:30–11:30` **конфликтуют**;
- отмененные брони в проверке конфликта **не участвуют**.
