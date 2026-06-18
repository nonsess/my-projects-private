# Спек: RestoGood Backend — Slice 1 (захват заявок)

**Дата:** 2026-06-18  
**Автор:** Даниил + Claude  
**Статус:** approved

---

## Контекст

Лендинг RestoGood (Next.js, static export) сейчас не собирает заявки — CTA ведёт в никуда. Slice 1 добавляет минимальный бэкенд для:
1. Приёма заявок с лендинга (имя + телефон + ROI-контекст)
2. Мгновенного уведомления Даниила в Telegram
3. Управления заявками через веб-админку

Slice 2 (аналитика: события от Kavi и др.) — отдельный спек после деплоя Slice 1.

---

## Что в скоупе

- FastAPI-сервис + PostgreSQL + Docker
- Публичный endpoint: приём заявки
- Telegram-бот: уведомление о новой заявке
- Jinja2-админка: список заявок, смена статуса, заметки
- Изменения в лендинге: компонент формы, передача ROI-контекста

## Что НЕ в скоупе

- Аналитика от ресторанных платформ (Slice 2)
- Email-уведомления
- Мультипользовательская авторизация (только Даниил)
- Деплой (пока)

---

## Архитектура

```
[Лендинг Next.js]
      │  fetch POST /api/leads
      ▼
[FastAPI сервис]
      │
      ├── PostgreSQL (таблица leads)
      │
      └── Telegram Bot API (httpx, уведомление)

[Даниил]
      │  браузер → /admin/leads (X-Admin-Token)
      ▼
[FastAPI Jinja2 Admin]
```

Лендинг остаётся static export. Форма делает внешний fetch-запрос. CORS настроен под домен лендинга.

---

## Структура репозитория

Новый репо: `restogood-backend/`

```
restogood-backend/
  app/
    main.py              # FastAPI app, CORS, роутеры
    config.py            # Pydantic Settings (env)
    database.py          # SQLAlchemy engine + session
    models.py            # ORM-модели
    schemas.py           # Pydantic схемы (in/out)
    telegram.py          # отправка уведомлений
    routes/
      leads.py           # POST /api/leads
      admin.py           # /admin/*
    templates/
      admin/
        base.html
        leads.html       # список заявок
        lead.html        # детальная карточка
    static/
      admin.css
  docker-compose.yml
  Dockerfile
  requirements.txt
  .env.example
  alembic/               # миграции
  alembic.ini
```

---

## База данных

### Таблица `leads`

| Колонка    | Тип               | Ограничения              |
|------------|-------------------|--------------------------|
| id         | SERIAL            | PRIMARY KEY              |
| name       | TEXT              | NOT NULL                 |
| phone      | TEXT              | NOT NULL                 |
| roi_data   | JSONB             | NULLABLE                 |
| status     | TEXT              | DEFAULT 'new', NOT NULL  |
| notes      | TEXT              | NULLABLE                 |
| created_at | TIMESTAMPTZ       | DEFAULT now()            |
| updated_at | TIMESTAMPTZ       | DEFAULT now()            |

Статусы: `new` / `in_progress` / `closed`.

`roi_data` — произвольный JSON с полями из калькулятора:
```json
{
  "revenue": 500000,
  "commission": 25,
  "savings_per_month": 87000,
  "selected_package": "optimum"
}
```
Поля опциональны внутри объекта — зависит от того, что передал лендинг.

---

## API

### `POST /api/leads`

Публичный. CORS: разрешён домен лендинга (и localhost:3000 для разработки).

**Request body (JSON):**
```json
{
  "name": "Алексей",
  "phone": "+7 999 123 45 67",
  "roi_data": { ... }  // опционально
}
```

**Валидация:**
- `name`: непустая строка, max 200 символов
- `phone`: непустая строка, max 50 символов
- `roi_data`: любой dict или null

**Response 201:**
```json
{ "id": 42, "status": "new" }
```

**Response 422:** стандартная Pydantic ошибка валидации.

После сохранения в БД → вызов `telegram.notify_new_lead(lead)` (fire-and-forget через `asyncio.create_task`; если Telegram недоступен — заявка всё равно сохранилась).

---

### `GET /admin/leads`

Защищённый. Header: `X-Admin-Token: <токен из env>`.

Query params:
- `status` (опционально): `new` / `in_progress` / `closed`
- `page` (default 1), `per_page` (default 50)

Возвращает HTML (Jinja2-шаблон) — таблица заявок.

---

### `PATCH /admin/leads/{id}`

Защищённый. Тело: form-data (для работы без JS).

Поля: `status` (опционально), `notes` (опционально).

Redirect обратно на `/admin/leads` после сохранения.

---

### `GET /admin/leads/{id}`

Защищённый. HTML: детальная карточка заявки — все поля, ROI-данные, история.

---

## Авторизация админки

Одна env-переменная `ADMIN_TOKEN`. Middleware проверяет `X-Admin-Token` header для `/admin/*` маршрутов. Если не совпадает — 403. Простого хватает: один пользователь, внутренний инструмент.

---

## Telegram-уведомление

Переменные окружения: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

Сообщение при новой заявке:
```
🔔 Новая заявка RestoGood

Имя: Алексей
Тел: +7 999 123 45 67
ROI: оборот 500K₽, комиссия 25%, экономия 87K₽/мес

Открыть: https://admin.restogood.ru/admin/leads/42
```

Если `roi_data` нет — строка ROI пропускается. Если Telegram-токенов нет в env — уведомление тихо пропускается (не падает).

Реализация: `httpx.AsyncClient.post()` на `api.telegram.org/bot{token}/sendMessage`. Без библиотеки python-telegram-bot — один запрос.

---

## Adminka UI (Jinja2)

**Список заявок (`/admin/leads`):**
- Фильтр по статусу (ссылки: Все / Новые / В работе / Закрыты)
- Таблица: дата, имя, телефон, экономия (из roi_data если есть), статус
- Клик по строке → детальная карточка

**Детальная карточка (`/admin/leads/{id}`):**
- Все поля + полный roi_data
- Форма смены статуса + заметки (form POST, без JS)

**Стиль:** тёмный минимализм (совпадает с брендом RestoGood), plain CSS, без фреймворков. Один файл `admin.css`.

---

## Изменения в лендинге

### Новый компонент `LeadForm`

Путь: `components/sections/LeadForm.tsx`

Поля: имя (text), телефон (tel), кнопка «Получить предложение».

Передача ROI-контекста: компонент принимает опциональный проп `roiData` (тип совпадает с `RoiCalculatorResult`). Если проп передан — данные уходят в `roi_data` поля запроса.

**UX:**
- inline-валидация: оба поля обязательны
- state машина: `idle → submitting → success | error`
- success: «Заявка отправлена — позвоним в течение рабочего дня»
- error: «Что-то пошло не так — попробуйте ещё раз или напишите напрямую»

### Размещение

`LeadForm` встраивается в `Footer.tsx` (уже есть CTA-блок «Пора вернуть своих клиентов»). Footer рендерится в `page.tsx` вне StackSection — изменений в stack-логике нет.

Дополнительно: в `RoiCalculator.tsx` добавляется CTA-кнопка «Получить КП» внизу — открывает якорную ссылку `#lead-form` (скролл к форме в Footer).

### Env

Добавляется `NEXT_PUBLIC_API_URL` — базовый URL бэкенда. При разработке: `http://localhost:8000`. В конфиге `config/site.ts` или `.env.local`.

---

## Docker

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
    env_file: .env

  backend:
    build: .
    depends_on: [db]
    env_file: .env
    ports: ["8000:8000"]

volumes:
  pgdata:
```

`Dockerfile`: Python 3.12-slim, uvicorn, не root-пользователь.

---

## .env.example

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/restogood
ADMIN_TOKEN=change_me
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ADMIN_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,https://restogood.ru
```

---

## Зависимости (requirements.txt)

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
pydantic-settings
httpx
jinja2
python-multipart
```

---

## Тесты

Минимальный набор (pytest + httpx.AsyncClient):
- `POST /api/leads` — happy path, сохранение в БД
- `POST /api/leads` — невалидные данные → 422
- `GET /admin/leads` — без токена → 403
- `GET /admin/leads` — с токеном → 200

Telegram-вызов мокируется.

---

## Порядок сборки

1. Scaffolding: структура, Docker, alembic, config
2. Модель БД + миграция
3. `POST /api/leads` endpoint
4. Telegram-нотификация
5. Jinja2-админка (список + детали + смена статуса)
6. Изменения в лендинге: `LeadForm`, интеграция в Footer, CTA в RoiCalculator
7. Тесты
