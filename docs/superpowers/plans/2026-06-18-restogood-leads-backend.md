# RestoGood Backend Slice 1 — Захват заявок: план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать FastAPI-бэкенд, который принимает заявки с лендинга, уведомляет в Telegram и отображает их в Jinja2-админке; добавить форму в лендинг.

**Architecture:** Монорепо `restogood/` с двумя сервисами — `backend/` (FastAPI + PostgreSQL) и `frontend/` (Next.js, перенесён из `restogood-landing/`). Корневой `docker-compose.yml` поднимает backend + postgres. Фронтенд запускается отдельно (`npm run dev`) или деплоится статически. Jinja2-adminка защищена header-токеном.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 (asyncio), asyncpg, Alembic, httpx, Jinja2, pytest + pytest-asyncio + aiosqlite (тесты); Next.js 16 / Tailwind v4; Docker + docker-compose.

## Global Constraints

- Монорепо: `/home/pensioner/coding/restogood/`
- Бэкенд: `/home/pensioner/coding/restogood/backend/`
- Фронтенд: `/home/pensioner/coding/restogood/frontend/` (содержимое перенесено из `restogood-landing/`)
- Корневой docker-compose: `/home/pensioner/coding/restogood/docker-compose.yml`
- Каждый сервис содержит свой `Dockerfile`
- Лендинг не меняет `output: 'export'` — форма делает внешний fetch
- `NEXT_PUBLIC_API_URL` — единственный env-ключ фронтенда для бэкенда
- Токены, пароли — только в `.env` / `.env.local`, не в коде и не в git
- `.env` и `.env.local` — в `.gitignore`; в репо только `.env.example`
- Tailwind-классы только из design-system: `bg-dark`, `bg-accent`, `bg-light`, `text-accent`, `text-muted`; не использовать `orange-*`, `slate-*` etc.
- Статусы заявки: строго `new` / `in_progress` / `closed`

---

### Task 1: Scaffolding — монорепо, перенос фронтенда, Docker, зависимости

**Files:**
- Create: `/home/pensioner/coding/restogood/` (git init)
- Create: `/home/pensioner/coding/restogood/docker-compose.yml`
- Create: `/home/pensioner/coding/restogood/.gitignore`
- Create: `/home/pensioner/coding/restogood/.env.example`
- Create: `/home/pensioner/coding/restogood/backend/` (перенос из `restogood-backend/` если существует, иначе создать)
- Create: `/home/pensioner/coding/restogood/backend/requirements.txt`
- Create: `/home/pensioner/coding/restogood/backend/Dockerfile`
- Create: `/home/pensioner/coding/restogood/backend/pytest.ini`
- Create: `/home/pensioner/coding/restogood/backend/app/__init__.py`
- Create: `/home/pensioner/coding/restogood/backend/app/routes/__init__.py`
- Create: `/home/pensioner/coding/restogood/backend/app/main.py` (заглушка)
- Create: `/home/pensioner/coding/restogood/backend/tests/__init__.py`
- Create: `/home/pensioner/coding/restogood/frontend/` (содержимое из `restogood-landing/`)
- Create: `/home/pensioner/coding/restogood/frontend/Dockerfile`

**Interfaces:**
- Produces: монорепо с двумя сервисами; `uvicorn app.main:app --reload` стартует из `backend/` без ошибок

- [ ] **Step 1: Создать монорепо и git-репо**

```bash
mkdir -p /home/pensioner/coding/restogood
cd /home/pensioner/coding/restogood && git init
```

- [ ] **Step 2: Перенести фронтенд из `restogood-landing/`**

```bash
cp -r /home/pensioner/coding/restogood-landing /home/pensioner/coding/restogood/frontend
rm -rf /home/pensioner/coding/restogood/frontend/.git
```

Проверить что файлы на месте:
```bash
ls /home/pensioner/coding/restogood/frontend/app /home/pensioner/coding/restogood/frontend/components
```

Ожидаемый вывод: директории с файлами лендинга.

- [ ] **Step 3: Создать структуру `backend/`**

```bash
mkdir -p /home/pensioner/coding/restogood/backend/app/routes
mkdir -p /home/pensioner/coding/restogood/backend/app/templates/admin
mkdir -p /home/pensioner/coding/restogood/backend/app/static
mkdir -p /home/pensioner/coding/restogood/backend/tests
touch /home/pensioner/coding/restogood/backend/app/__init__.py
touch /home/pensioner/coding/restogood/backend/app/routes/__init__.py
touch /home/pensioner/coding/restogood/backend/tests/__init__.py
```

- [ ] **Step 4: Создать `backend/requirements.txt`**

```
fastapi==0.111.1
uvicorn[standard]==0.30.1
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
aiosqlite==0.20.0
alembic==1.13.2
pydantic-settings==2.3.4
httpx==0.27.0
jinja2==3.1.4
python-multipart==0.0.9
pytest==8.2.2
pytest-asyncio==0.23.8
```

- [ ] **Step 5: Создать `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN useradd -m appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 6: Создать корневой `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: restogood
      POSTGRES_USER: restogood
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U restogood"]
      interval: 5s
      retries: 5

  backend:
    build: ./backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    ports:
      - "8000:8000"

volumes:
  pgdata:
```

- [ ] **Step 7: Создать корневой `.env.example`**

```env
DATABASE_URL=postgresql+asyncpg://restogood:CHANGE_ME@db:5432/restogood
POSTGRES_PASSWORD=CHANGE_ME
ADMIN_TOKEN=CHANGE_ME
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ADMIN_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,https://restogood.ru
```

- [ ] **Step 8: Создать корневой `.gitignore`**

```
.env
.env.local
__pycache__/
*.pyc
.pytest_cache/
.venv/
backend/.venv/
frontend/.next/
frontend/node_modules/
dist/
```

- [ ] **Step 9: Создать `frontend/Dockerfile`** (для будущего production-деплоя)

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

- [ ] **Step 10: Создать `backend/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 11: Создать заглушку `backend/app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="RestoGood Backend")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 12: Проверить что uvicorn стартует**

```bash
cd /home/pensioner/coding/restogood/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Ожидаемый вывод: `Application startup complete.` (затем Ctrl+C).

- [ ] **Step 13: Commit**

```bash
cd /home/pensioner/coding/restogood
git add .
git commit -m "feat: scaffold restogood monorepo — backend skeleton, frontend transfer, Docker"
```

---

### Task 2: Config + Database + Model

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`

**Interfaces:**
- Produces:
  - `settings` — экземпляр `Settings` (импортируется как `from app.config import settings`)
  - `Base` — DeclarativeBase (для Alembic и тестов)
  - `get_db` — FastAPI dependency, yields `AsyncSession`
  - `Lead` — ORM-модель таблицы `leads`

- [ ] **Step 1: Создать `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    admin_token: str
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    admin_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 2: Создать `backend/app/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 3: Создать `backend/app/models.py`**

```python
from datetime import datetime
from sqlalchemy import Text, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    roi_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="new", server_default="new")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

> Используем `JSON` (не `JSONB`) — работает и на PostgreSQL в prod, и на SQLite в тестах.

- [ ] **Step 4: Проверить импорты**

```bash
cd /home/pensioner/coding/restogood/backend
DATABASE_URL=sqlite+aiosqlite:///:memory: ADMIN_TOKEN=x python -c "from app.models import Lead; print(Lead.__tablename__)"
```

Ожидаемый вывод: `leads`

- [ ] **Step 5: Commit**

```bash
cd /home/pensioner/coding/restogood
git add backend/app/config.py backend/app/database.py backend/app/models.py
git commit -m "feat: add config, database, Lead model"
```

---

### Task 3: Alembic — настройка и первая миграция

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/0001_create_leads_table.py`

**Interfaces:**
- Produces: команда `alembic upgrade head` (из `backend/`) создаёт таблицу `leads` в PostgreSQL

- [ ] **Step 1: Инициализировать Alembic из `backend/`**

```bash
cd /home/pensioner/coding/restogood/backend
alembic init alembic
```

Создаёт `alembic/`, `alembic.ini`.

- [ ] **Step 2: Убрать жёстко прописанный sqlalchemy.url из `backend/alembic.ini`**

Найти строку `sqlalchemy.url = driver://user:pass@localhost/dbname` и заменить на:

```ini
sqlalchemy.url =
```

- [ ] **Step 3: Заменить `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Создать `backend/alembic/versions/0001_create_leads_table.py`**

```python
"""create leads table

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("roi_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("leads")
```

- [ ] **Step 5: Проверить что миграция парсится корректно**

```bash
cd /home/pensioner/coding/restogood/backend
DATABASE_URL=sqlite+aiosqlite:///:memory: ADMIN_TOKEN=x alembic check
```

Ожидаемый вывод: нет ошибок.

- [ ] **Step 6: Commit**

```bash
cd /home/pensioner/coding/restogood
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add alembic migrations — create leads table"
```

---

### Task 4: Lead endpoint + тесты

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/routes/leads.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_leads.py`

**Interfaces:**
- Consumes: `Lead` (из `app.models`), `get_db` (из `app.database`), `settings` (из `app.config`)
- Produces:
  - `POST /api/leads` → 201 `{"id": int, "status": "new"}` или 422
  - `LeadCreate` — Pydantic-схема входящего тела
  - `LeadOut` — Pydantic-схема ответа

- [ ] **Step 1: Написать тесты (сначала)**

Перед запуском тестов нужен запущенный PostgreSQL из docker-compose:
`cd /home/pensioner/coding/restogood && docker-compose up -d db`

И создать тестовую БД (один раз):
```bash
docker exec -it restogood-db-1 psql -U restogood -c "CREATE DATABASE restogood_test;"
```

Создать `backend/.env.test`:
```env
DATABASE_URL=postgresql+asyncpg://restogood:CHANGE_ME@localhost:5432/restogood
ADMIN_TOKEN=test-admin-token
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ADMIN_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
TEST_DATABASE_URL=postgresql+asyncpg://restogood:CHANGE_ME@localhost:5432/restogood_test
```

Добавить `backend/.env.test` в `.gitignore` (корневой).

Создать `backend/tests/conftest.py`:

```python
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://restogood:CHANGE_ME@localhost:5432/restogood")
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("TELEGRAM_CHAT_ID", "")
os.environ.setdefault("ADMIN_BASE_URL", "http://localhost:8000")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://restogood:CHANGE_ME@localhost:5432/restogood_test",
)

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_ENGINE = create_async_engine(TEST_DATABASE_URL)
TestSessionFactory = async_sessionmaker(TEST_ENGINE, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(reset_db):
    async def override_get_db():
        async with TestSessionFactory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
```

Создать `backend/tests/test_leads.py`:

```python
async def test_create_lead_success(client):
    response = await client.post(
        "/api/leads",
        json={"name": "Алексей", "phone": "+7 999 123 45 67"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "new"
    assert isinstance(data["id"], int)


async def test_create_lead_with_roi(client):
    response = await client.post(
        "/api/leads",
        json={
            "name": "Мария",
            "phone": "+7 900 000 00 00",
            "roi_data": {"revenue": 500000, "commission": 25, "savings_per_month": 87000},
        },
    )
    assert response.status_code == 201


async def test_create_lead_missing_name(client):
    response = await client.post("/api/leads", json={"phone": "+7 999 000 00 00"})
    assert response.status_code == 422


async def test_create_lead_missing_phone(client):
    response = await client.post("/api/leads", json={"name": "Тест"})
    assert response.status_code == 422


async def test_create_lead_empty_name(client):
    response = await client.post("/api/leads", json={"name": "", "phone": "123"})
    assert response.status_code == 422
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/test_leads.py -v
```

Ожидаемый вывод: ошибка — эндпоинт не существует.

- [ ] **Step 3: Создать `backend/app/schemas.py`**

```python
from typing import Any
from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=50)
    roi_data: dict[str, Any] | None = None


class LeadOut(BaseModel):
    id: int
    status: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Создать `backend/app/routes/leads.py`**

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadOut

router = APIRouter()


@router.post("/api/leads", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(name=body.name, phone=body.phone, roi_data=body.roi_data)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead
```

- [ ] **Step 5: Обновить `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import leads

app = FastAPI(title="RestoGood Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["POST", "GET", "PATCH"],
    allow_headers=["*"],
)

app.include_router(leads.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Запустить тесты — убедиться что проходят**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/test_leads.py -v
```

Ожидаемый вывод: `5 passed`

- [ ] **Step 7: Commit**

```bash
cd /home/pensioner/coding/restogood
git add backend/app/schemas.py backend/app/routes/leads.py backend/app/main.py backend/tests/
git commit -m "feat: add POST /api/leads endpoint with tests"
```

---

### Task 5: Telegram-уведомление

**Files:**
- Create: `backend/app/telegram.py`
- Modify: `backend/app/routes/leads.py`
- Create: `backend/tests/test_telegram.py`

**Interfaces:**
- Consumes: `settings.telegram_bot_token`, `settings.telegram_chat_id`, `settings.admin_base_url`
- Produces: `notify_new_lead(lead_id, name, phone, roi_data)` — async функция, тихо не падает если токен пустой или Telegram недоступен

- [ ] **Step 1: Написать тесты**

Создать `backend/tests/test_telegram.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch
from app.telegram import notify_new_lead


async def test_notify_skips_when_no_token():
    """Если TELEGRAM_BOT_TOKEN пустой — никакого HTTP-запроса."""
    with patch("app.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = ""
        mock_settings.telegram_chat_id = "12345"
        with patch("app.telegram.httpx.AsyncClient") as mock_client_cls:
            await notify_new_lead(1, "Алексей", "+7 999 000 00 00", None)
            mock_client_cls.assert_not_called()


async def test_notify_sends_message_with_roi():
    """Если токен есть — отправляет POST на Telegram API с ROI-строкой."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = "fake-token"
        mock_settings.telegram_chat_id = "12345"
        mock_settings.admin_base_url = "http://localhost:8000"
        with patch("app.telegram.httpx.AsyncClient", return_value=mock_client):
            await notify_new_lead(
                42, "Мария", "+7 900 000 00 00",
                {"revenue": 500000, "savings_per_month": 87000}
            )

    mock_client.post.assert_called_once()
    text = mock_client.post.call_args.kwargs["json"]["text"]
    assert "Мария" in text
    assert "+7 900 000 00 00" in text
    assert "87" in text
    assert "/admin/leads/42" in text


async def test_notify_sends_message_without_roi():
    """Если roi_data нет — строка ROI в сообщении отсутствует."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = "fake-token"
        mock_settings.telegram_chat_id = "12345"
        mock_settings.admin_base_url = "http://localhost:8000"
        with patch("app.telegram.httpx.AsyncClient", return_value=mock_client):
            await notify_new_lead(1, "Иван", "123", None)

    text = mock_client.post.call_args.kwargs["json"]["text"]
    assert "ROI" not in text
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/test_telegram.py -v
```

Ожидаемый вывод: `ModuleNotFoundError: No module named 'app.telegram'`

- [ ] **Step 3: Создать `backend/app/telegram.py`**

```python
import httpx
from app.config import settings


async def notify_new_lead(
    lead_id: int,
    name: str,
    phone: str,
    roi_data: dict | None,
) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    roi_line = ""
    if roi_data:
        parts = []
        if "revenue" in roi_data:
            parts.append(f"оборот {int(roi_data['revenue']):,}₽".replace(",", " "))
        if "commission" in roi_data:
            parts.append(f"комиссия {roi_data['commission']}%")
        if "savings_per_month" in roi_data:
            parts.append(f"экономия {int(roi_data['savings_per_month']):,}₽/мес".replace(",", " "))
        if parts:
            roi_line = f"\nROI: {', '.join(parts)}"

    text = (
        f"🔔 Новая заявка RestoGood\n\n"
        f"Имя: {name}\n"
        f"Тел: {phone}"
        f"{roi_line}\n\n"
        f"Открыть: {settings.admin_base_url}/admin/leads/{lead_id}"
    )

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={"chat_id": settings.telegram_chat_id, "text": text},
                timeout=5.0,
            )
    except Exception:
        pass
```

- [ ] **Step 4: Запустить тесты — убедиться что проходят**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/test_telegram.py -v
```

Ожидаемый вывод: `3 passed`

- [ ] **Step 5: Подключить Telegram к leads endpoint**

Обновить `backend/app/routes/leads.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadOut
from app import telegram

router = APIRouter()


@router.post("/api/leads", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(name=body.name, phone=body.phone, roi_data=body.roi_data)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    try:
        await telegram.notify_new_lead(lead.id, lead.name, lead.phone, lead.roi_data)
    except Exception:
        pass
    return lead
```

- [ ] **Step 6: Убедиться что все тесты проходят**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/ -v
```

Ожидаемый вывод: `8 passed`

- [ ] **Step 7: Commit**

```bash
cd /home/pensioner/coding/restogood
git add backend/app/telegram.py backend/app/routes/leads.py backend/tests/test_telegram.py
git commit -m "feat: add Telegram notification on new lead"
```

---

### Task 6: Admin routes + тесты

**Files:**
- Create: `backend/app/routes/admin.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_admin.py`

**Interfaces:**
- Consumes: `Lead` (из `app.models`), `get_db`, `settings.admin_token`
- Produces:
  - `GET /admin/leads` — HTML, защищён `X-Admin-Token`; query param `status_filter`
  - `GET /admin/leads/{id}` — HTML карточка
  - `POST /admin/leads/{id}` — обновить `status` / `notes`, redirect 303

- [ ] **Step 1: Написать тесты**

Создать `backend/tests/test_admin.py`:

```python
ADMIN_TOKEN = "test-admin-token"  # совпадает с conftest.py


async def test_list_leads_no_token(client):
    response = await client.get("/admin/leads")
    assert response.status_code == 403


async def test_list_leads_wrong_token(client):
    response = await client.get("/admin/leads", headers={"X-Admin-Token": "wrong"})
    assert response.status_code == 403


async def test_list_leads_with_token(client):
    response = await client.get("/admin/leads", headers={"X-Admin-Token": ADMIN_TOKEN})
    assert response.status_code == 200
    assert b"RestoGood Admin" in response.content


async def test_list_leads_shows_created_lead(client):
    await client.post("/api/leads", json={"name": "Тест", "phone": "123"})
    response = await client.get("/admin/leads", headers={"X-Admin-Token": ADMIN_TOKEN})
    assert b"\xd0\xa2\xd0\xb5\xd1\x81\xd1\x82" in response.content  # "Тест" UTF-8


async def test_get_lead_detail(client):
    create_resp = await client.post(
        "/api/leads", json={"name": "Детали", "phone": "+7 000 000 00 00"}
    )
    lead_id = create_resp.json()["id"]
    response = await client.get(
        f"/admin/leads/{lead_id}", headers={"X-Admin-Token": ADMIN_TOKEN}
    )
    assert response.status_code == 200
    assert b"\xd0\x94\xd0\xb5\xd1\x82\xd0\xb0\xd0\xbb\xd0\xb8" in response.content  # "Детали"


async def test_update_lead_status(client):
    create_resp = await client.post(
        "/api/leads", json={"name": "Обновление", "phone": "999"}
    )
    lead_id = create_resp.json()["id"]
    response = await client.post(
        f"/admin/leads/{lead_id}",
        data={"status": "in_progress"},
        headers={"X-Admin-Token": ADMIN_TOKEN},
        follow_redirects=False,
    )
    assert response.status_code == 303
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/test_admin.py -v
```

Ожидаемый вывод: ошибки 404.

- [ ] **Step 3: Создать заглушки шаблонов** (нужны для Jinja2)

```bash
mkdir -p /home/pensioner/coding/restogood/backend/app/templates/admin
```

Создать `backend/app/templates/admin/base.html`:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>RestoGood Admin</title>
</head>
<body>
  <header><a href="/admin/leads">RestoGood Admin</a></header>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

Создать `backend/app/templates/admin/leads.html`:

```html
{% extends "admin/base.html" %}
{% block content %}
<h1>Заявки</h1>
{% for lead in leads %}<p>{{ lead.name }} — {{ lead.phone }} — {{ lead.status }}</p>{% endfor %}
{% endblock %}
```

Создать `backend/app/templates/admin/lead.html`:

```html
{% extends "admin/base.html" %}
{% block content %}
<h1>Заявка #{{ lead.id }}</h1>
<p>{{ lead.name }} — {{ lead.phone }}</p>
<form method="post" action="/admin/leads/{{ lead.id }}">
  <input type="hidden" name="status" value="{{ lead.status }}">
  <button type="submit">Сохранить</button>
</form>
{% endblock %}
```

- [ ] **Step 4: Создать `backend/app/routes/admin.py`**

```python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import Lead

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def verify_admin(request: Request) -> None:
    token = request.headers.get("X-Admin-Token", "")
    if token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/admin/leads", response_class=HTMLResponse)
async def list_leads(
    request: Request,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    q = select(Lead).order_by(Lead.created_at.desc())
    if status_filter and status_filter in ("new", "in_progress", "closed"):
        q = q.where(Lead.status == status_filter)
    result = await db.execute(q)
    leads = result.scalars().all()
    return templates.TemplateResponse(
        request, "admin/leads.html", {"leads": leads, "status_filter": status_filter}
    )


@router.get("/admin/leads/{lead_id}", response_class=HTMLResponse)
async def get_lead(
    lead_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "admin/lead.html", {"lead": lead})


@router.post("/admin/leads/{lead_id}")
async def update_lead(
    lead_id: int,
    request: Request,
    status_val: str | None = Form(None, alias="status"),
    notes: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404)
    if status_val in ("new", "in_progress", "closed"):
        lead.status = status_val
    if notes is not None:
        lead.notes = notes
    lead.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return RedirectResponse(url=f"/admin/leads/{lead_id}", status_code=303)
```

- [ ] **Step 5: Подключить admin-роутер и StaticFiles в `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import leads, admin

app = FastAPI(title="RestoGood Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["POST", "GET", "PATCH"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(admin.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

Создать файл чтобы StaticFiles не падал при пустой директории:

```bash
touch /home/pensioner/coding/restogood/backend/app/static/.gitkeep
```

- [ ] **Step 6: Запустить все тесты**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/ -v
```

Ожидаемый вывод: `13 passed`

- [ ] **Step 7: Commit**

```bash
cd /home/pensioner/coding/restogood
git add backend/app/routes/admin.py backend/app/main.py backend/app/templates/ backend/app/static/.gitkeep backend/tests/test_admin.py
git commit -m "feat: add admin routes with token auth and stub templates"
```

---

### Task 7: Admin UI — полные Jinja2-шаблоны и CSS

**Files:**
- Modify: `backend/app/templates/admin/base.html`
- Modify: `backend/app/templates/admin/leads.html`
- Modify: `backend/app/templates/admin/lead.html`
- Create: `backend/app/static/admin.css`

**Interfaces:**
- Produces: полнофункциональная тёмная веб-админка на `/admin/leads`

- [ ] **Step 1: Создать `backend/app/static/admin.css`**

```css
*, *::before, *::after { box-sizing: border-box; }

:root {
  --bg: #111110;
  --surface: #1c1b19;
  --border: rgba(255,255,255,0.08);
  --text: #f6f3ee;
  --muted: #78716c;
  --accent: #ff4d00;
  --green: #34d399;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

header {
  padding: 16px 32px;
  border-bottom: 1px solid var(--border);
  font-weight: 700;
  font-size: 16px;
}

main { max-width: 1200px; margin: 32px auto; padding: 0 32px; }

.filters { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.filters a {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 13px;
  transition: all .15s;
}
.filters a:hover { border-color: var(--accent); color: var(--text); text-decoration: none; }
.filters a.active { background: var(--accent); border-color: var(--accent); color: #fff; }

table { width: 100%; border-collapse: collapse; }
thead th {
  text-align: left;
  padding: 10px 14px;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .08em;
  border-bottom: 1px solid var(--border);
}
tbody tr {
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background .1s;
}
tbody tr:hover { background: var(--surface); }
tbody td { padding: 12px 14px; }

.status {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.status-new { background: rgba(255,77,0,.15); color: var(--accent); }
.status-in_progress { background: rgba(251,191,36,.12); color: #fbbf24; }
.status-closed { background: rgba(120,113,108,.15); color: var(--muted); }

.lead-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}
.lead-card p { margin: 8px 0; color: var(--muted); }
.lead-card p strong { color: var(--text); }

.roi-block {
  background: rgba(255,77,0,.06);
  border: 1px solid rgba(255,77,0,.15);
  border-radius: 8px;
  padding: 14px;
  margin-top: 12px;
}
.roi-block pre {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--muted);
  white-space: pre-wrap;
}

form.update-form { display: flex; flex-direction: column; gap: 14px; max-width: 400px; }
form.update-form label { display: flex; flex-direction: column; gap: 6px; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
form.update-form select,
form.update-form textarea {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  padding: 8px 12px;
  font-size: 14px;
  font-family: inherit;
}
form.update-form select:focus,
form.update-form textarea:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
form.update-form textarea { min-height: 80px; resize: vertical; }
form.update-form button {
  align-self: flex-start;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity .15s;
}
form.update-form button:hover { opacity: .85; }

.back-link { display: inline-block; margin-top: 20px; color: var(--muted); font-size: 13px; }
.back-link:hover { color: var(--text); }

.empty { color: var(--muted); text-align: center; padding: 40px; }
```

- [ ] **Step 2: Обновить `backend/app/templates/admin/base.html`**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RestoGood Admin</title>
  <link rel="stylesheet" href="/static/admin.css">
</head>
<body>
  <header>
    <a href="/admin/leads">RestoGood Admin</a>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 3: Обновить `backend/app/templates/admin/leads.html`**

```html
{% extends "admin/base.html" %}
{% block content %}
<div class="filters">
  <a href="/admin/leads" {% if not status_filter %}class="active"{% endif %}>Все</a>
  <a href="/admin/leads?status_filter=new"
     {% if status_filter == 'new' %}class="active"{% endif %}>Новые</a>
  <a href="/admin/leads?status_filter=in_progress"
     {% if status_filter == 'in_progress' %}class="active"{% endif %}>В работе</a>
  <a href="/admin/leads?status_filter=closed"
     {% if status_filter == 'closed' %}class="active"{% endif %}>Закрыты</a>
</div>

<table>
  <thead>
    <tr>
      <th>Дата</th>
      <th>Имя</th>
      <th>Телефон</th>
      <th>Экономия/мес</th>
      <th>Статус</th>
    </tr>
  </thead>
  <tbody>
    {% for lead in leads %}
    <tr onclick="location.href='/admin/leads/{{ lead.id }}'">
      <td>{{ lead.created_at.strftime('%d.%m.%Y %H:%M') if lead.created_at else '—' }}</td>
      <td>{{ lead.name }}</td>
      <td>{{ lead.phone }}</td>
      <td>
        {% if lead.roi_data and lead.roi_data.savings_per_month %}
          {{ '{:,.0f}'.format(lead.roi_data.savings_per_month).replace(',', ' ') }} ₽
        {% else %}—{% endif %}
      </td>
      <td><span class="status status-{{ lead.status }}">{{ lead.status }}</span></td>
    </tr>
    {% else %}
    <tr><td colspan="5" class="empty">Заявок нет</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 4: Обновить `backend/app/templates/admin/lead.html`**

```html
{% extends "admin/base.html" %}
{% block content %}
<div class="lead-card">
  <p><strong>Имя:</strong> {{ lead.name }}</p>
  <p><strong>Телефон:</strong> {{ lead.phone }}</p>
  <p><strong>Дата:</strong> {{ lead.created_at.strftime('%d.%m.%Y %H:%M') if lead.created_at else '—' }}</p>
  <p><strong>Статус:</strong> <span class="status status-{{ lead.status }}">{{ lead.status }}</span></p>
  {% if lead.notes %}
  <p><strong>Заметки:</strong> {{ lead.notes }}</p>
  {% endif %}
  {% if lead.roi_data %}
  <div class="roi-block">
    <strong>ROI-данные</strong>
    <pre>{{ lead.roi_data | tojson(indent=2) }}</pre>
  </div>
  {% endif %}
</div>

<form method="post" action="/admin/leads/{{ lead.id }}" class="update-form">
  <label>Статус
    <select name="status">
      <option value="new" {% if lead.status == 'new' %}selected{% endif %}>Новая</option>
      <option value="in_progress" {% if lead.status == 'in_progress' %}selected{% endif %}>В работе</option>
      <option value="closed" {% if lead.status == 'closed' %}selected{% endif %}>Закрыта</option>
    </select>
  </label>
  <label>Заметки
    <textarea name="notes">{{ lead.notes or '' }}</textarea>
  </label>
  <button type="submit">Сохранить</button>
</form>

<a href="/admin/leads" class="back-link">← Все заявки</a>
{% endblock %}
```

- [ ] **Step 5: Запустить все тесты**

```bash
cd /home/pensioner/coding/restogood/backend
pytest tests/ -v
```

Ожидаемый вывод: `13 passed`

- [ ] **Step 6: Commit**

```bash
cd /home/pensioner/coding/restogood
git add backend/app/templates/ backend/app/static/admin.css
git commit -m "feat: full admin UI — Jinja2 templates + dark CSS"
```

---

### Task 8: Фронтенд — LeadForm + интеграция

**Files:**
- Create: `frontend/components/sections/LeadForm.tsx`
- Modify: `frontend/components/sections/Footer.tsx`
- Modify: `frontend/components/sections/RoiCalculator.tsx`
- Create: `frontend/.env.local.example`

**Interfaces:**
- Consumes: `NEXT_PUBLIC_API_URL` из env, `sessionStorage` для ROI-контекста
- Produces: форма в Footer с `id="lead-form"`; RoiCalculator сохраняет контекст в sessionStorage и скроллит к форме

Текущее состояние `frontend/` (перенесено из `restogood-landing/`):
- `Footer.tsx` имеет CTA-блок «Пора вернуть своих клиентов» с двумя кнопками
- `RoiCalculator.tsx` имеет `<div className="flex flex-col gap-3">` с `KpPdfDownloadButton` и ссылкой на Telegram
- `Button` принимает `arrow`, `size`, `variant`, `disabled` пропсы

- [ ] **Step 1: Создать `frontend/.env.local.example`**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Добавить `.env.local` в `frontend/.gitignore` если ещё нет:

```bash
grep -q '.env.local' /home/pensioner/coding/restogood/frontend/.gitignore || echo '.env.local' >> /home/pensioner/coding/restogood/frontend/.gitignore
```

Создать для локальной разработки:

```bash
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > /home/pensioner/coding/restogood/frontend/.env.local
```

- [ ] **Step 2: Создать `frontend/components/sections/LeadForm.tsx`**

```tsx
'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/Button'

type RoiContext = {
  revenue?: number
  commission?: number
  savings_per_month?: number
  selected_package?: string
}

type FormState = 'idle' | 'submitting' | 'success' | 'error'

export function LeadForm() {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [formState, setFormState] = useState<FormState>('idle')
  const [roiContext, setRoiContext] = useState<RoiContext | null>(null)

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('rg_roi_context')
      if (raw) setRoiContext(JSON.parse(raw))
    } catch {
      // sessionStorage недоступен — не страшно
    }
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormState('submitting')
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? ''
      const res = await fetch(`${apiUrl}/api/leads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          phone,
          roi_data: roiContext ?? null,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setFormState('success')
    } catch {
      setFormState('error')
    }
  }

  if (formState === 'success') {
    return (
      <p className="text-white/60 text-sm py-2">
        Заявка отправлена — позвоним в течение рабочего дня
      </p>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 w-full max-w-md">
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          placeholder="Ваше имя"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          disabled={formState === 'submitting'}
          className="flex-1 min-w-0 px-4 py-3 rounded-xl bg-white/6 border border-white/12 text-white placeholder:text-white/30 text-sm focus:border-accent/50 focus:outline-none transition-colors disabled:opacity-50"
        />
        <input
          type="tel"
          placeholder="Телефон"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          required
          disabled={formState === 'submitting'}
          className="flex-1 min-w-0 px-4 py-3 rounded-xl bg-white/6 border border-white/12 text-white placeholder:text-white/30 text-sm focus:border-accent/50 focus:outline-none transition-colors disabled:opacity-50"
        />
      </div>
      <Button
        type="submit"
        arrow
        disabled={formState === 'submitting'}
        className="self-start"
      >
        {formState === 'submitting' ? 'Отправляем...' : 'Получить предложение'}
      </Button>
      {formState === 'error' && (
        <p className="text-red-400/80 text-xs">
          Что-то пошло не так — попробуйте ещё раз или напишите напрямую
        </p>
      )}
    </form>
  )
}
```

- [ ] **Step 3: Обновить `frontend/components/sections/Footer.tsx`**

Добавить импорт в начало файла (после `import { Button } from '@/components/ui/Button'`):

```tsx
import { LeadForm } from '@/components/sections/LeadForm'
```

Заменить блок с двумя кнопками CTA:

Найти:
```tsx
            <div className="flex flex-col sm:flex-row gap-3 shrink-0">
              <Button
                size="lg"
                arrow
                onClick={() =>
                  document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' })
                }
              >
                Рассчитать окупаемость
              </Button>
              <a
                href={site.contacts.telegram}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-full border border-white/15 text-white/70 text-sm font-bold uppercase tracking-wide hover:border-white/30 hover:text-white transition-all cursor-pointer"
              >
                Написать в Telegram
              </a>
            </div>
```

Заменить на:

```tsx
            <div id="lead-form" className="shrink-0 w-full md:w-auto">
              <LeadForm />
              <p className="text-white/25 text-xs mt-3">
                Или{' '}
                <a
                  href={site.contacts.telegram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-white/40 hover:text-white/60 transition-colors underline underline-offset-2"
                >
                  напишите в Telegram
                </a>
              </p>
            </div>
```

- [ ] **Step 4: Обновить `frontend/components/sections/RoiCalculator.tsx`**

Найти блок `{/* CTAs */}` и добавить кнопку «Получить предложение» между `KpPdfDownloadButton` и ссылкой на Telegram:

Найти:
```tsx
            {/* CTAs */}
            <div className="flex flex-col gap-3">
              <KpPdfDownloadButton data={pdfData} />
              <a
                href={site.contacts.telegram}
```

Заменить на:

```tsx
            {/* CTAs */}
            <div className="flex flex-col gap-3">
              <KpPdfDownloadButton data={pdfData} />
              <button
                type="button"
                onClick={() => {
                  try {
                    sessionStorage.setItem(
                      'rg_roi_context',
                      JSON.stringify({
                        revenue,
                        commission,
                        savings_per_month: Math.round(roi.savingsPerMonth),
                        selected_package: selectedPkgId,
                      })
                    )
                  } catch {
                    // sessionStorage недоступен — игнорируем
                  }
                  document.getElementById('lead-form')?.scrollIntoView({ behavior: 'smooth' })
                }}
                className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl border border-accent/40 text-accent text-sm font-semibold hover:bg-accent/8 active:scale-[0.97] transition-all cursor-pointer"
              >
                Получить предложение →
              </button>
              <a
                href={site.contacts.telegram}
```

- [ ] **Step 5: Проверить TypeScript**

```bash
cd /home/pensioner/coding/restogood/frontend
npx tsc --noEmit
```

Ожидаемый вывод: `0 errors`

- [ ] **Step 6: Запустить dev-сервер и проверить вручную**

```bash
cd /home/pensioner/coding/restogood/frontend
npm run dev
```

Открыть `http://localhost:3000`. Проверить:
- Форма в Footer отображается
- Кнопка «Получить предложение» в RoiCalculator скроллит к форме
- При заполнении и отправке: статус меняется на «Отправляем...» → «Заявка отправлена»
  (бэкенд должен быть запущен: `cd backend && DATABASE_URL=sqlite+aiosqlite:///./dev.db ADMIN_TOKEN=admin123 uvicorn app.main:app --reload`)

- [ ] **Step 7: Commit**

```bash
cd /home/pensioner/coding/restogood
git add frontend/components/sections/LeadForm.tsx frontend/components/sections/Footer.tsx frontend/components/sections/RoiCalculator.tsx frontend/.env.local.example frontend/.gitignore
git commit -m "feat: add LeadForm to Footer, ROI context via sessionStorage"
```

---

## Self-Review — соответствие спеку

| Требование | Задача |
|---|---|
| Монорепо `restogood/` с `backend/` и `frontend/` | Task 1 |
| Корневой `docker-compose.yml` | Task 1 |
| `Dockerfile` в каждом сервисе | Task 1 (backend), Task 8 (frontend) |
| `POST /api/leads` с валидацией name/phone/roi_data | Task 4 |
| Response 201 `{id, status}` | Task 4 |
| PostgreSQL таблица leads (8 колонок) | Task 2 + Task 3 |
| Alembic-миграция | Task 3 |
| Telegram-уведомление (тихо если нет токена) | Task 5 |
| ROI-строка только если roi_data есть | Task 5 |
| `GET /admin/leads` — HTML, X-Admin-Token, фильтр | Task 6 + Task 7 |
| `GET /admin/leads/{id}` — детальная карточка | Task 6 + Task 7 |
| `POST /admin/leads/{id}` — статус/заметки, redirect 303 | Task 6 |
| Тёмный CSS без JS-фреймворков | Task 7 |
| CORS | Task 4 (main.py) |
| `.env.example` с ADMIN_BASE_URL | Task 1 |
| `LeadForm` в Footer с `id="lead-form"` | Task 8 |
| ROI-контекст через sessionStorage | Task 8 |
| Кнопка «Получить предложение» в RoiCalculator | Task 8 |
| `NEXT_PUBLIC_API_URL` в фронтенде | Task 8 |
| Тесты: 5 leads + 3 telegram + 6 admin | Tasks 4, 5, 6 |
