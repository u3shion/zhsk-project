# Backend — документация

## Обзор

Бэкенд построен как набор независимых микросервисов. Каждый сервис — отдельное FastAPI-приложение со своей базой данных. Все сервисы используют один инстанс PostgreSQL с раздельными БД.

```
backend/
├── docker-compose.yml       # оркестрация backend-слоя
├── postgres/
│   └── init-databases.sh    # скрипт создания БД и пользователей при первом запуске
├── users/                   # сервис управления пользователями (порт 8001)
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                 # для локального запуска
│   ├── auth/
│   │   ├── router.py        # эндпоинты /auth/register, /auth/login
│   │   ├── schemas.py       # Pydantic-схемы запросов
│   │   ├── security.py      # хэширование паролей, JWT (encode/decode)
│   │   └── dependencies.py  # FastAPI dependency get_current_user
│   ├── core/
│   │   ├── config.py        # переменные окружения
│   │   └── database.py      # SQLAlchemy engine, сессия, get_db
│   ├── models/
│   │   └── user.py          # ORM-модель User
│   └── users/
│       └── router.py        # эндпоинты /users/me
├── meters/                  # сервис показаний и счётчиков (порт 8002)
│   ├── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   ├── auth/
│   │   ├── security.py      # decode_token (только декодирование JWT)
│   │   └── dependencies.py  # get_current_user → TokenData, require_admin
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── reading.py       # ORM-модель MeterReading
│   │   └── water_meter.py   # ORM-модель WaterMeter
│   ├── readings/
│   │   ├── schemas.py
│   │   └── router.py        # эндпоинты /readings/...
│   └── water_meters/
│       ├── schemas.py
│       └── router.py        # эндпоинты /water-meters/...
└── announcements/           # сервис объявлений (порт 8003)
    ├── main.py
    ├── Dockerfile
    ├── requirements.txt
    ├── .env
    ├── auth/
    │   ├── security.py
    │   └── dependencies.py
    ├── core/
    │   ├── config.py
    │   └── database.py
    ├── models/
    │   └── announcement.py  # ORM-модель Announcement
    └── announcements/
        ├── schemas.py
        └── router.py        # эндпоинты /announcements/...
```

### Аутентификация между сервисами

JWT-токен выдаётся сервисом `users` и принимается всеми остальными сервисами. `SECRET_KEY` — общий для всех, берётся из корневого `.env`. В сервисе `meters` при проверке токена нет обращения к БД — декодируется только пейлоад (`user_id`, `role`).

---

## Сервис `users`

### Переменные окружения

| Переменная     | Описание                              | Пример                                                               |
|----------------|---------------------------------------|----------------------------------------------------------------------|
| `DATABASE_URL` | Строка подключения к PostgreSQL       | `postgresql+psycopg2://users_service:pw@localhost:5432/users_db`     |
| `ADMIN_SECRET` | Секрет для выдачи роли `admin`        | `supersecret123`                                                     |
| `SECRET_KEY`   | Ключ подписи JWT                      | `supersecretkey`                                                     |

### Модель `User`

| Поле              | Тип     | Описание                              |
|-------------------|---------|---------------------------------------|
| `id`              | int PK  | Первичный ключ                        |
| `email`           | str     | Уникальный email, индексирован        |
| `hashed_password` | str     | Пароль, хэшированный Argon2           |
| `role`            | str     | `resident` (по умолчанию) или `admin` |
| `full_name`       | str?    | Полное имя (опционально)              |
| `apartment`       | str?    | Номер квартиры (опционально)          |

### API

#### `POST /auth/register`

Регистрация нового пользователя. Если передан верный `admin_secret` — выдаётся роль `admin` (председатель/бухгалтер), иначе — `resident`.

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword",
  "admin_secret": "supersecret123"
}
```

**Ответ `200`:**
```json
{ "message": "user created", "role": "admin" }
```

**Ошибки:** `400` — пользователь с таким email уже существует.

---

#### `POST /auth/login`

Авторизация. Возвращает JWT Bearer-токен.

**Тело запроса:**
```json
{ "email": "user@example.com", "password": "strongpassword" }
```

**Ответ `200`:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

**Ошибки:** `401` — неверный email или пароль.

**Структура JWT-пейлоада:**
```json
{ "user_id": 1, "role": "resident", "exp": "<timestamp>" }
```

---

#### `GET /users/me`

Получение профиля текущего пользователя. Требует заголовок `Authorization: Bearer <token>`.

**Ответ `200`:**
```json
{
  "email": "user@example.com",
  "role": "resident",
  "full_name": "Иван Иванов",
  "apartment": "42"
}
```

**Ошибки:** `401` — токен отсутствует, просрочен или невалиден.

---

#### `PUT /users/me`

Обновление профиля текущего пользователя. Требует заголовок `Authorization: Bearer <token>`.

**Тело запроса:**
```json
{ "full_name": "Иван Иванов", "apartment": "42" }
```

**Ответ `200`:**
```json
{ "message": "updated" }
```

**Ошибки:** `401` — токен отсутствует, просрочен или невалиден.

---

### Безопасность

- Пароли хэшируются через **Argon2** (passlib).
- JWT подписывается алгоритмом **HS256**, срок действия — 60 минут.
- `SECRET_KEY` читается из переменной окружения.
- Защищённые эндпоинты получают пользователя через dependency `get_current_user` (`auth/dependencies.py`), которая декодирует Bearer-токен из заголовка `Authorization` и подгружает объект `User` из БД.
- `get_db` централизован в `core/database.py` и используется везде через `Depends(get_db)`.

---

## Запуск

### Docker (весь стек из корня проекта)
```bash
docker compose up --build
```

| Сервис          | URL                       |
|-----------------|---------------------------|
| `users`         | http://localhost:8001      |
| `meters`        | http://localhost:8002      |
| `announcements` | http://localhost:8003      |

### Локально (без Docker)
```bash
# users
cd backend/users
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# meters (в другом терминале)
cd backend/meters
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# announcements (в другом терминале)
cd backend/announcements
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```
Требует запущенного PostgreSQL с базами `users_db`, `meters_db`, `announcements_db` и соответствующими пользователями (параметры из `.env` каждого сервиса).

---

## Сервис `meters`

### Переменные окружения

| Переменная     | Описание                             | Пример                                                                |
|----------------|--------------------------------------|-----------------------------------------------------------------------|
| `DATABASE_URL` | Строка подключения к PostgreSQL      | `postgresql+psycopg2://meters_service:pw@localhost:5432/meters_db`    |
| `SECRET_KEY`   | Ключ подписи JWT (общий с `users`)   | `supersecretkey`                                                      |

### Модель `MeterReading`

| Поле           | Тип      | Описание                                                    |
|----------------|----------|-------------------------------------------------------------|
| `id`           | int PK   | Первичный ключ                                              |
| `user_id`      | int      | ID пользователя из JWT                                      |
| `apartment`    | str      | Номер квартиры                                              |
| `period`       | str      | Период в формате `YYYY-MM`                                  |
| `meter_type`   | str      | `electricity` / `cold_water` / `hot_water` / `heating` / `gas` |
| `value`        | float    | Показание счётчика                                          |
| `submitted_at` | datetime | Время подачи (ставится автоматически)                       |

Уникальное ограничение: один жилец не может подать два показания одного типа за один период.

### Модель `WaterMeter`

| Поле                   | Тип   | Описание                                     |
|------------------------|-------|----------------------------------------------|
| `id`                   | int PK | Первичный ключ                              |
| `user_id`              | int   | ID владельца из JWT                          |
| `apartment`            | str   | Номер квартиры                               |
| `meter_type`           | str   | `cold` / `hot`                               |
| `serial_number`        | str   | Серийный номер счётчика                      |
| `installed_at`         | date  | Дата установки                               |
| `last_verified_at`     | date? | Дата последней поверки (опционально)         |
| `next_verification_at` | date  | Дата следующей поверки                       |
| `is_active`            | bool  | Активен ли счётчик (снятый = `false`)        |

### API

Все эндпоинты требуют заголовок `Authorization: Bearer <token>`.

---

#### `POST /readings/` — жилец

Подача показания. Повторная подача за тот же период и тип вернёт `400`.

**Тело запроса:**
```json
{
  "apartment": "42",
  "period": "2026-05",
  "meter_type": "cold_water",
  "value": 123.45
}
```
**Ответ `201`:** объект `ReadingResponse`.

---

#### `GET /readings/me` — жилец

Список своих показаний. Опциональные query-параметры: `period` (`2026-05`), `meter_type`.

**Ответ `200`:**
```json
{
  "readings": [
    {
      "id": 1,
      "user_id": 3,
      "apartment": "42",
      "period": "2026-05",
      "meter_type": "cold_water",
      "value": 123.45,
      "submitted_at": "2026-05-09T17:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### `GET /readings/summary?period=YYYY-MM` — только admin

Сводная таблица по квартирам: что сдано, чего не хватает.

**Ответ `200`:**
```json
{
  "period": "2026-05",
  "total_apartments": 3,
  "complete": 1,
  "incomplete": 2,
  "apartments": [
    {
      "apartment": "10",
      "submitted": ["electricity", "cold_water"],
      "missing": ["hot_water", "heating", "gas"],
      "complete": false
    }
  ]
}
```

---

#### `POST /water-meters/` — жилец

Регистрация счётчика воды.

**Тело запроса:**
```json
{
  "apartment": "42",
  "meter_type": "cold",
  "serial_number": "AB-123456",
  "installed_at": "2022-01-15",
  "next_verification_at": "2028-01-15"
}
```
**Ответ `201`:** объект `WaterMeterResponse`.

---

#### `GET /water-meters/me` — жилец

Список активных счётчиков текущего пользователя, отсортированных по дате поверки.

**Ответ `200`:** массив `WaterMeterResponse`.

---

#### `PUT /water-meters/{id}` — жилец

Обновление дат после поверки счётчика.

**Тело запроса:**
```json
{
  "last_verified_at": "2026-05-01",
  "next_verification_at": "2032-05-01"
}
```
**Ответ `200`:** обновлённый `WaterMeterResponse`. `404` — если счётчик не найден или принадлежит другому пользователю.

---

#### `DELETE /water-meters/{id}` — жилец

Деактивация счётчика (при замене). Счётчик остаётся в базе с `is_active = false`.

**Ответ `200`:**
```json
{ "message": "Meter deactivated", "id": 3 }
```
**Ошибки:** `404` — счётчик не найден или принадлежит другому пользователю.

---

#### `GET /water-meters/summary` — только admin

Сводная таблица всех активных счётчиков, отсортированная по дате поверки. Счётчики с просроченной или приближающейся датой (≤ 60 дней) помечены отдельно.

**Ответ `200`:**
```json
{
  "total": 10,
  "overdue_count": 1,
  "needs_attention_count": 2,
  "meters": [
    {
      "id": 3,
      "apartment": "15",
      "meter_type": "cold",
      "serial_number": "AB-123456",
      "next_verification_at": "2026-04-01",
      "days_until_verification": -36,
      "needs_attention": true,
      "overdue": true
    }
  ]
}
```

---

## Сервис `announcements`

### Переменные окружения

| Переменная     | Описание                           | Пример                                                                            |
|----------------|------------------------------------|-----------------------------------------------------------------------------------|
| `DATABASE_URL` | Строка подключения к PostgreSQL    | `postgresql+psycopg2://announcements_service:pw@localhost:5432/announcements_db`  |
| `SECRET_KEY`   | Ключ подписи JWT (общий с `users`) | `supersecretkey`                                                                  |

### Модель `Announcement`

| Поле          | Тип      | Описание                                                        |
|---------------|----------|-----------------------------------------------------------------|
| `id`          | int PK   | Первичный ключ                                                  |
| `author_id`   | int      | ID автора из JWT                                                |
| `author_role` | str      | Роль автора на момент создания (`admin` / `resident`)           |
| `type`        | str      | `news` — новость от управления, `ad` — объявление жильца        |
| `subtype`     | str?     | Только для `ad`: `service` — услуга, `noise` — шум              |
| `title`       | str      | Заголовок                                                       |
| `content`     | str      | Текст объявления                                                |
| `is_active`   | bool     | Видимость (мягкое удаление)                                     |
| `created_at`  | datetime | Время создания (авто)                                           |
| `updated_at`  | datetime | Время последнего изменения (авто)                               |

**Права на создание:**
- `admin` — может создавать и `news`, и `ad`
- `resident` — только `ad`; поле `subtype` обязательно

### API

Все эндпоинты требуют заголовок `Authorization: Bearer <token>`.

---

#### `POST /announcements/`

Создание объявления.

**Тело запроса (news от admin):**
```json
{ "type": "news", "title": "Плановое отключение воды", "content": "5 мая с 10:00 до 14:00" }
```

**Тело запроса (ad от жильца):**
```json
{ "type": "ad", "subtype": "noise", "title": "Ремонт", "content": "Буду шуметь 10 мая с 10:00 до 18:00" }
```

**Ответ `201`:** объект `AnnouncementResponse`.  
**Ошибки:** `403` — жилец пытается создать `news`.

---

#### `GET /announcements/`

Список активных объявлений с пагинацией.

| Query-параметр | По умолчанию | Описание                       |
|----------------|--------------|--------------------------------|
| `type`         | —            | Фильтр: `news` / `ad`          |
| `subtype`      | —            | Фильтр: `service` / `noise`    |
| `page`         | `1`          | Номер страницы                 |
| `page_size`    | `20`         | Размер страницы (макс. 100)    |

**Ответ `200`:**
```json
{ "items": [...], "total": 42, "page": 1, "page_size": 20 }
```

---

#### `GET /announcements/{id}`

Получение одного объявления. **Ошибки:** `404`.

---

#### `PUT /announcements/{id}`

Редактирование. Разрешено автору или любому `admin`. Все поля опциональны.

```json
{ "title": "Новый заголовок", "content": "Новый текст", "subtype": "service" }
```

**Ответ `200`:** обновлённый объект. **Ошибки:** `403`, `404`.

---

#### `DELETE /announcements/{id}`

Мягкое удаление (`is_active = false`). Разрешено автору или любому `admin`.

**Ответ `200`:**
```json
{ "message": "Announcement deleted", "id": 5 }
```
**Ошибки:** `403`, `404`.
