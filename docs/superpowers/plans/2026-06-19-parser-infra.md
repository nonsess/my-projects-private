# Трекер недвижимости — Plan 1: Инфраструктура + Парсер

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Рабочий парсер Авито + ЦИАН (Москва + СПб), который заполняет PostgreSQL объявлениями и историей цен, запускается по расписанию через Celery.

**Architecture:** Docker Compose поднимает PostgreSQL, Redis, и parser-сервис. Парсер использует Playwright со stealth-плагином и пулом мобильных прокси. Celery beat запускает задачи каждые 3 часа. При изменении цены — пишет в price_history и ставит задачу на матчинг фильтров.

**Tech Stack:** Python 3.12, Playwright, playwright-stealth, Celery 5, Redis, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Docker Compose v2

## Global Constraints

- Python >= 3.12
- PostgreSQL >= 16, Redis >= 7
- Парсер собирает только метаданные: external_id, source, type, city, price, area, floor, floors_total, district, address, url — без телефонов, текста и фото
- Уважаем robots.txt по духу: задержки 2–7 сек между запросами, мобильные прокси
- Все парсеры реализуют единый интерфейс BaseParser
- Celery beat расписание: каждые 3 часа, 4 задачи (2 источника × 2 города)

---

## Структура файлов

```
realestate-tracker/
├── docker-compose.yml
├── .env.example
├── backend/                        # Plan 2 — пока пустая директория
│   └── .gitkeep
├── frontend/                       # Plan 3 — пока пустая директория
│   └── .gitkeep
└── parser/
    ├── Dockerfile
    ├── pyproject.toml
    ├── alembic.ini
    ├── alembic/
    │   └── versions/
    │       └── 0001_initial.py
    ├── parser/
    │   ├── __init__.py
    │   ├─��� config.py               # настройки из env
    │   ├── database.py             # engine, session, Base
    │   ├── models.py               # ORM: Listing, PriceHistory
    │   ├── schemas.py              # dataclass ListingData (результат парсинга)
    │   ├── base.py                 # abstract BaseParser
    │   ├── avito.py                # AvitoParser(BaseParser)
    │   ├── cian.py                 # CianParser(BaseParser)
    │   ├── upsert.py               # логика upsert + price_history
    │   ├── celery_app.py           # Celery instance + beat schedule
    │   └── tasks.py                # @app.task parse_city()
    └── tests/
        ├── conftest.py
        ├── test_upsert.py
        ├── test_avito.py
        └── test_cian.py
```

---

## Task 1: Docker Compose + схема БД

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `parser/pyproject.toml`
- Create: `parser/alembic.ini`
- Create: `parser/alembic/versions/0001_initial.py`
- Create: `parser/parser/config.py`
- Create: `parser/parser/database.py`
- Create: `parser/parser/models.py`

**Interfaces:**
- Produces: `Session` (generator), `Listing`, `PriceHistory` ORM-модели — используются во всех последующих задачах

- [ ] **Шаг 1: Создать структуру директорий**

```bash
mkdir -p realestate-tracker/{parser/{parser,tests,alembic/versions},backend,frontend}
touch realestate-tracker/backend/.gitkeep
touch realestate-tracker/frontend/.gitkeep
cd realestate-tracker
```

- [ ] **Шаг 2: Написать `docker-compose.yml`**

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-realestate}
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  parser:
    build: ./parser
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-app}:${POSTGRES_PASSWORD:-secret}@postgres/${POSTGRES_DB:-realestate}
      REDIS_URL: redis://redis:6379/0
      PROXY_LIST: ${PROXY_LIST:-}
      ALERT_EMAIL: ${ALERT_EMAIL:-}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A parser.celery_app worker --beat --loglevel=info

volumes:
  postgres_data:
```

- [ ] **Шаг 3: Написать `.env.example`**

```bash
# .env.example
POSTGRES_DB=realestate
POSTGRES_USER=app
POSTGRES_PASSWORD=changeme

# Мобильные прокси через запятую: user:pass@host:port
PROXY_LIST=user1:pass1@proxy1.example.com:8080,user2:pass2@proxy2.example.com:8080

# Куда слать алерт если парсер сломался
ALERT_EMAIL=your@email.com

# Plan 2: JWT secret
SECRET_KEY=changeme-32chars-minimum

# Plan 2: OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
VK_CLIENT_ID=
VK_CLIENT_SECRET=
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=

# Plan 2: ЮKassa
YUKASSA_SHOP_ID=
YUKASSA_SECRET_KEY=

# Plan 2: Email
POSTMARK_TOKEN=
```

- [ ] **Шаг 4: Написать `parser/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "parser"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "playwright>=1.44",
    "playwright-stealth>=1.0",
    "celery[redis]>=5.4",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.1",
    "alembic>=1.13",
    "pydantic-settings>=2.0",
    "tenacity>=8.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Шаг 5: Написать `parser/parser/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    proxy_list: str = ""  # "user:pass@host:port,..."
    alert_email: str = ""
    parse_interval_seconds: int = 10800  # 3 часа

    @property
    def proxies(self) -> list[str]:
        if not self.proxy_list:
            return []
        return [p.strip() for p in self.proxy_list.split(",") if p.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Шаг 6: Написать `parser/parser/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from parser.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Шаг 7: Написать `parser/parser/models.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Numeric, SmallInteger, Boolean, UniqueConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from parser.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(10))   # 'avito' | 'cian'
    external_id: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(10))     # 'sale' | 'rent'
    city: Mapped[str] = mapped_column(String(10))     # 'moscow' | 'spb'
    price: Mapped[int] = mapped_column(Integer)
    area: Mapped[float] = mapped_column(Numeric(6, 1))
    floor: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    floors_total: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="listing")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_listing_source_external_id"),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id"))
    price: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(default=utcnow)

    listing: Mapped["Listing"] = relationship(back_populates="price_history")

    __table_args__ = (
        Index("ix_price_history_listing_recorded", "listing_id", "recorded_at"),
    )
```

- [ ] **Шаг 8: Создать миграцию Alembic**

```bash
# В директории parser/
cd parser
pip install -e ".[dev]"
alembic init alembic
```

Заменить содержимое `alembic/env.py` на:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from parser.database import Base
from parser import models  # noqa: F401 — чтобы модели зарегистрировались

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

- [ ] **Шаг 9: Проверить что БД создалась**

```bash
docker compose up postgres -d
DATABASE_URL="postgresql+psycopg://app:secret@localhost/realestate" alembic upgrade head
# Ожидаем: INFO  [alembic.runtime.migration] Running upgrade  -> xxxx, initial
```

- [ ] **Шаг 10: Коммит**

```bash
git add docker-compose.yml .env.example parser/
git commit -m "infra: docker compose + db schema (listings, price_history)"
```

---

## Task 2: ListingData + BaseParser

**Files:**
- Create: `parser/parser/schemas.py`
- Create: `parser/parser/base.py`
- Create: `parser/tests/conftest.py`

**Interfaces:**
- Produces:
  - `ListingData` — датакласс, который оба парсера возвращают
  - `BaseParser.fetch_listings(city, listing_type) -> list[ListingData]` — абстрактный метод

- [ ] **Шаг 1: Написать тест на ListingData**

```python
# parser/tests/test_schemas.py
from parser.schemas import ListingData


def test_listing_data_required_fields():
    data = ListingData(
        source="avito",
        external_id="123456",
        type="sale",
        city="moscow",
        price=7_500_000,
        area=52.0,
        url="https://avito.ru/123456",
    )
    assert data.source == "avito"
    assert data.floor is None
    assert data.district is None
```

- [ ] **Шаг 2: Убедиться что тест падает**

```bash
pytest parser/tests/test_schemas.py -v
# Ожидаем: ERROR — ModuleNotFoundError
```

- [ ] **Шаг 3: Написать `parser/parser/schemas.py`**

```python
from dataclasses import dataclass, field


@dataclass
class ListingData:
    source: str          # 'avito' | 'cian'
    external_id: str
    type: str            # 'sale' | 'rent'
    city: str            # 'moscow' | 'spb'
    price: int
    area: float
    url: str
    floor: int | None = None
    floors_total: int | None = None
    district: str | None = None
    address: str | None = None
```

- [ ] **Шаг 4: Написать `parser/parser/base.py`**

```python
from abc import ABC, abstractmethod
from parser.schemas import ListingData


class BaseParser(ABC):
    """
    Каждый парсер реализует fetch_listings.
    Playwright-браузер и прокси создаются снаружи и передаются в конструктор.
    """

    def __init__(self, proxies: list[str] | None = None):
        self.proxies = proxies or []

    @abstractmethod
    async def fetch_listings(self, city: str, listing_type: str) -> list[ListingData]:
        """
        city: 'moscow' | 'spb'
        listing_type: 'sale' | 'rent'
        Возвращает список объявлений со страниц поиска.
        """
        ...
```

- [ ] **Шаг 5: Написать `parser/tests/conftest.py`**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_page():
    """Мок Playwright Page для юнит-тестов парсеров."""
    page = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    return page
```

- [ ] **Шаг 6: Запустить тест**

```bash
pytest parser/tests/test_schemas.py -v
# Ожидаем: PASSED
```

- [ ] **Шаг 7: Коммит**

```bash
git add parser/parser/schemas.py parser/parser/base.py parser/tests/
git commit -m "parser: ListingData schema + BaseParser interface"
```

---

## Task 3: Upsert логика

**Files:**
- Create: `parser/parser/upsert.py`
- Create: `parser/tests/test_upsert.py`

**Interfaces:**
- Consumes: `ListingData`, `Session`, `Listing`, `PriceHistory`
- Produces:
  - `upsert_listing(session, data: ListingData) -> tuple[Listing, str]`
    - возвращает `(listing, event)` где `event` ∈ `{"new", "price_drop", "none"}`

- [ ] **Шаг 1: Написать тесты**

```python
# parser/tests/test_upsert.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from parser.database import Base
from parser.models import Listing, PriceHistory
from parser.schemas import ListingData
from parser.upsert import upsert_listing


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def make_data(**kwargs):
    defaults = dict(
        source="avito", external_id="abc123", type="sale",
        city="moscow", price=7_000_000, area=50.0,
        url="https://avito.ru/abc123",
    )
    return ListingData(**{**defaults, **kwargs})


def test_new_listing_returns_new_event(session):
    data = make_data()
    listing, event = upsert_listing(session, data)
    assert event == "new"
    assert listing.price == 7_000_000
    history = session.query(PriceHistory).filter_by(listing_id=listing.id).all()
    assert len(history) == 1


def test_same_price_returns_none_event(session):
    data = make_data()
    upsert_listing(session, data)
    _, event = upsert_listing(session, data)
    assert event == "none"


def test_price_drop_returns_price_drop_event(session):
    data = make_data(price=7_000_000)
    upsert_listing(session, data)
    data2 = make_data(price=6_500_000)
    listing, event = upsert_listing(session, data2)
    assert event == "price_drop"
    assert listing.price == 6_500_000
    history = session.query(PriceHistory).filter_by(listing_id=listing.id).all()
    assert len(history) == 2


def test_price_increase_returns_none_event(session):
    data = make_data(price=6_000_000)
    upsert_listing(session, data)
    data2 = make_data(price=7_000_000)
    _, event = upsert_listing(session, data2)
    # Повышение цены не триггерит алерт
    assert event == "none"
```

- [ ] **Шаг 2: Убедиться что тесты падают**

```bash
pytest parser/tests/test_upsert.py -v
# Ожидаем: ERROR — ImportError: cannot import upsert_listing
```

- [ ] **Шаг 3: Написать `parser/parser/upsert.py`**

```python
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from parser.models import Listing, PriceHistory
from parser.schemas import ListingData


def upsert_listing(session: Session, data: ListingData) -> tuple[Listing, str]:
    """
    Возвращает (listing, event).
    event: 'new' | 'price_drop' | 'none'
    """
    existing = (
        session.query(Listing)
        .filter_by(source=data.source, external_id=data.external_id)
        .first()
    )

    if existing is None:
        listing = Listing(
            source=data.source,
            external_id=data.external_id,
            type=data.type,
            city=data.city,
            price=data.price,
            area=data.area,
            floor=data.floor,
            floors_total=data.floors_total,
            district=data.district,
            address=data.address,
            url=data.url,
        )
        session.add(listing)
        session.flush()
        session.add(PriceHistory(listing_id=listing.id, price=data.price))
        session.commit()
        return listing, "new"

    if existing.price == data.price:
        existing.is_active = True
        session.commit()
        return existing, "none"

    old_price = existing.price
    existing.price = data.price
    existing.is_active = True
    session.add(PriceHistory(listing_id=existing.id, price=data.price))
    session.commit()

    event = "price_drop" if data.price < old_price else "none"
    return existing, event
```

- [ ] **Шаг 4: Запустить тесты**

```bash
pip install sqlalchemy sqlite3
pytest parser/tests/test_upsert.py -v
# Ожидаем: 4 PASSED
```

- [ ] **Шаг 5: Коммит**

```bash
git add parser/parser/upsert.py parser/tests/test_upsert.py
git commit -m "parser: upsert logic with price history tracking"
```

---

## Task 4: Avito Parser

**Files:**
- Create: `parser/parser/avito.py`
- Create: `parser/tests/test_avito.py`

**Interfaces:**
- Consumes: `BaseParser`, `ListingData`
- Produces: `AvitoParser(proxies).fetch_listings(city, listing_type) -> list[ListingData]`

URL-маппинг Авито:
- Москва продажа: `https://www.avito.ru/moskva/kvartiry/prodam-ASgBAgICAkSSA8YQ`
- Москва аренда: `https://www.avito.ru/moskva/kvartiry/sdam-ASgBAgICAkSSA9gQ`
- СПб продажа: `https://www.avito.ru/sankt-peterburg/kvartiry/prodam-ASgBAgICAkSSA8YQ`
- СПб аренда: `https://www.avito.ru/sankt-peterburg/kvartiry/sdam-ASgBAgICAkSSA9gQ`

- [ ] **Шаг 1: Написать тест с моком страницы**

```python
# parser/tests/test_avito.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from parser.avito import AvitoParser
from parser.schemas import ListingData


def make_listing_element(price=7_500_000, area=52.0, floor=5, floors_total=12,
                          district="Пресненский", address="ул. Тверская", external_id="123"):
    el = AsyncMock()
    el.get_attribute = AsyncMock(side_effect=lambda attr: {
        "data-item-id": external_id,
    }.get(attr))
    el.query_selector = AsyncMock(side_effect=lambda sel: {
        "[data-marker='item-price']": _text_el(f"{price:,} ₽".replace(",", " ")),
        "[data-marker='item-title']": _text_el(f"2-к. квартира {area} м², {floor}/{floors_total} эт."),
        "[data-marker='item-address']": _text_el(f"{district}, {address}"),
        "[data-marker='item-link']": _href_el(f"/moskva/kvartiry/{external_id}"),
    }.get(sel))
    return el


def _text_el(text):
    el = AsyncMock()
    el.inner_text = AsyncMock(return_value=text)
    return el


def _href_el(href):
    el = AsyncMock()
    el.get_attribute = AsyncMock(return_value=href)
    return el


@pytest.mark.asyncio
async def test_fetch_listings_returns_listing_data(mock_page):
    mock_page.query_selector_all = AsyncMock(
        return_value=[make_listing_element(price=7_500_000, area=52.0)]
    )
    mock_page.query_selector = AsyncMock(return_value=None)  # нет кнопки "следующая"

    parser = AvitoParser()
    with patch.object(parser, "_make_page", return_value=mock_page):
        with patch.object(parser, "_close_browser"):
            results = await parser.fetch_listings("moscow", "sale")

    assert len(results) == 1
    assert results[0].source == "avito"
    assert results[0].price == 7_500_000
    assert results[0].city == "moscow"
    assert results[0].type == "sale"


@pytest.mark.asyncio
async def test_fetch_listings_skips_invalid(mock_page):
    """Объявление без цены пропускается."""
    bad_el = AsyncMock()
    bad_el.get_attribute = AsyncMock(return_value="999")
    bad_el.query_selector = AsyncMock(return_value=None)  # нет цены

    mock_page.query_selector_all = AsyncMock(return_value=[bad_el])
    mock_page.query_selector = AsyncMock(return_value=None)

    parser = AvitoParser()
    with patch.object(parser, "_make_page", return_value=mock_page):
        with patch.object(parser, "_close_browser"):
            results = await parser.fetch_listings("moscow", "sale")

    assert results == []
```

- [ ] **Шаг 2: Убедиться что тест падает**

```bash
pytest parser/tests/test_avito.py -v
# Ожидаем: ERROR — ImportError
```

- [ ] **Шаг 3: Написать `parser/parser/avito.py`**

```python
import asyncio
import random
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from parser.base import BaseParser
from parser.schemas import ListingData

CITY_SLUGS = {"moscow": "moskva", "spb": "sankt-peterburg"}
TYPE_SLUGS = {"sale": "prodam-ASgBAgICAkSSA8YQ", "rent": "sdam-ASgBAgICAkSSA9gQ"}
BASE_URL = "https://www.avito.ru"


class AvitoParser(BaseParser):
    def __init__(self, proxies: list[str] | None = None, max_pages: int = 50):
        super().__init__(proxies)
        self.max_pages = max_pages
        self._browser = None

    async def _make_page(self):
        proxy_str = random.choice(self.proxies) if self.proxies else None
        proxy = {"server": f"http://{proxy_str}"} if proxy_str else None
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            proxy=proxy,
        )
        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Mobile Safari/537.36"
            ),
        )
        page = await context.new_page()
        await stealth_async(page)
        return page

    async def _close_browser(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch_listings(self, city: str, listing_type: str) -> list[ListingData]:
        page = await self._make_page()
        results: list[ListingData] = []
        try:
            city_slug = CITY_SLUGS[city]
            type_slug = TYPE_SLUGS[listing_type]
            url = f"{BASE_URL}/{city_slug}/kvartiry/{type_slug}"

            for page_num in range(1, self.max_pages + 1):
                page_url = f"{url}?p={page_num}" if page_num > 1 else url
                await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 7))

                items = await page.query_selector_all("[data-marker='item']")
                if not items:
                    break

                for item in items:
                    data = await self._parse_item(item, city, listing_type)
                    if data:
                        results.append(data)

                # Проверяем есть ли следующая страница
                next_btn = await page.query_selector("[data-marker='pagination-button/next']")
                if not next_btn:
                    break

        finally:
            await self._close_browser()

        return results

    async def _parse_item(self, item, city: str, listing_type: str) -> ListingData | None:
        try:
            external_id = await item.get_attribute("data-item-id")
            if not external_id:
                return None

            price_el = await item.query_selector("[data-marker='item-price']")
            if not price_el:
                return None
            price_text = await price_el.inner_text()
            price = self._parse_price(price_text)
            if not price:
                return None

            title_el = await item.query_selector("[data-marker='item-title']")
            title = await title_el.inner_text() if title_el else ""
            area, floor, floors_total = self._parse_title(title)

            link_el = await item.query_selector("[data-marker='item-link']")
            href = await link_el.get_attribute("href") if link_el else None
            url = f"{BASE_URL}{href}" if href else ""

            address_el = await item.query_selector("[data-marker='item-address']")
            address_text = await address_el.inner_text() if address_el else ""
            district, address = self._parse_address(address_text)

            return ListingData(
                source="avito",
                external_id=external_id,
                type=listing_type,
                city=city,
                price=price,
                area=area or 0.0,
                floor=floor,
                floors_total=floors_total,
                district=district,
                address=address,
                url=url,
            )
        except Exception:
            return None

    @staticmethod
    def _parse_price(text: str) -> int | None:
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    @staticmethod
    def _parse_title(title: str) -> tuple[float | None, int | None, int | None]:
        area_match = re.search(r"([\d.]+)\s*м²", title)
        floor_match = re.search(r"(\d+)/(\d+)\s*эт", title)
        area = float(area_match.group(1)) if area_match else None
        floor = int(floor_match.group(1)) if floor_match else None
        floors_total = int(floor_match.group(2)) if floor_match else None
        return area, floor, floors_total

    @staticmethod
    def _parse_address(text: str) -> tuple[str | None, str | None]:
        parts = [p.strip() for p in text.split(",", 1)]
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0] if parts else None, None
```

- [ ] **Шаг 4: Установить Playwright**

```bash
pip install playwright playwright-stealth
playwright install chromium
```

- [ ] **Шаг 5: Запустить тесты**

```bash
pytest parser/tests/test_avito.py -v
# Ожидаем: 2 PASSED
```

- [ ] **Шаг 6: Коммит**

```bash
git add parser/parser/avito.py parser/tests/test_avito.py
git commit -m "parser: AvitoParser — fetch listings with stealth + proxy"
```

---

## Task 5: CIAN Parser

**Files:**
- Create: `parser/parser/cian.py`
- Create: `parser/tests/test_cian.py`

**Interfaces:**
- Produces: `CianParser(proxies).fetch_listings(city, listing_type) -> list[ListingData]`

URL-маппинг ЦИАН:
- Москва продажа: `https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=1`
- Москва аренда: `https://www.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&region=1`
- СПб (region=2): аналогично с `region=2`

- [ ] **Шаг 1: Написать тест**

```python
# parser/tests/test_cian.py
import pytest
from unittest.mock import AsyncMock, patch
from parser.cian import CianParser


def make_cian_item(price=8_000_000, area=60.0, floor=3, floors_total=9,
                    district="Центральный", external_id="12345678"):
    el = AsyncMock()
    el.get_attribute = AsyncMock(return_value=f"https://www.cian.ru/sale/flat/{external_id}/")

    price_el = AsyncMock()
    price_el.inner_text = AsyncMock(return_value=f"{price:,} ₽".replace(",", " "))

    info_el = AsyncMock()
    info_el.inner_text = AsyncMock(return_value=f"{area} м², {floor}/{floors_total} эт.")

    geo_el = AsyncMock()
    geo_el.inner_text = AsyncMock(return_value=f"{district}, ул. Невский пр-т")

    el.query_selector = AsyncMock(side_effect=lambda sel: {
        "[data-name='BargainTerms']": price_el,
        "[data-name='ObjectFactoids']": info_el,
        "[data-name='GeoReduced']": geo_el,
    }.get(sel))
    return el


@pytest.mark.asyncio
async def test_cian_fetch_listings(mock_page):
    mock_page.query_selector_all = AsyncMock(
        return_value=[make_cian_item(price=8_000_000)]
    )
    mock_page.query_selector = AsyncMock(return_value=None)

    parser = CianParser()
    with patch.object(parser, "_make_page", return_value=mock_page):
        with patch.object(parser, "_close_browser"):
            results = await parser.fetch_listings("moscow", "sale")

    assert len(results) == 1
    assert results[0].source == "cian"
    assert results[0].price == 8_000_000
    assert results[0].city == "moscow"
```

- [ ] **Шаг 2: Написать `parser/parser/cian.py`**

```python
import asyncio
import random
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from parser.base import BaseParser
from parser.schemas import ListingData

REGIONS = {"moscow": 1, "spb": 2}
BASE_URL = "https://www.cian.ru"


class CianParser(BaseParser):
    def __init__(self, proxies: list[str] | None = None, max_pages: int = 54):
        super().__init__(proxies)
        self.max_pages = max_pages
        self._browser = None
        self._playwright = None

    async def _make_page(self):
        proxy_str = random.choice(self.proxies) if self.proxies else None
        proxy = {"server": f"http://{proxy_str}"} if proxy_str else None
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True, proxy=proxy)
        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; SM-S918B) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.6367.82 Mobile Safari/537.36"
            ),
        )
        page = await context.new_page()
        await stealth_async(page)
        return page

    async def _close_browser(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch_listings(self, city: str, listing_type: str) -> list[ListingData]:
        page = await self._make_page()
        results: list[ListingData] = []
        region = REGIONS[city]

        try:
            for page_num in range(1, self.max_pages + 1):
                url = (
                    f"{BASE_URL}/cat.php?deal_type={listing_type}"
                    f"&engine_version=2&offer_type=flat&region={region}&p={page_num}"
                )
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 7))

                items = await page.query_selector_all("[data-name='CardComponent']")
                if not items:
                    break

                for item in items:
                    data = await self._parse_item(item, city, listing_type)
                    if data:
                        results.append(data)

                next_btn = await page.query_selector("[data-name='Pagination'] a[rel='next']")
                if not next_btn:
                    break

        finally:
            await self._close_browser()

        return results

    async def _parse_item(self, item, city: str, listing_type: str) -> ListingData | None:
        try:
            link_el = await item.query_selector("a[href*='/sale/flat/'], a[href*='/rent/flat/']")
            if not link_el:
                return None
            url = await link_el.get_attribute("href") or ""
            external_id = re.search(r"/flat/(\d+)/", url)
            if not external_id:
                return None
            ext_id = external_id.group(1)

            price_el = await item.query_selector("[data-name='BargainTerms']")
            if not price_el:
                return None
            price_text = await price_el.inner_text()
            price = self._parse_price(price_text)
            if not price:
                return None

            info_el = await item.query_selector("[data-name='ObjectFactoids']")
            info_text = await info_el.inner_text() if info_el else ""
            area, floor, floors_total = self._parse_info(info_text)

            geo_el = await item.query_selector("[data-name='GeoReduced']")
            geo_text = await geo_el.inner_text() if geo_el else ""
            district, address = self._parse_geo(geo_text)

            return ListingData(
                source="cian",
                external_id=ext_id,
                type=listing_type,
                city=city,
                price=price,
                area=area or 0.0,
                floor=floor,
                floors_total=floors_total,
                district=district,
                address=address,
                url=url,
            )
        except Exception:
            return None

    @staticmethod
    def _parse_price(text: str) -> int | None:
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    @staticmethod
    def _parse_info(text: str) -> tuple[float | None, int | None, int | None]:
        area_match = re.search(r"([\d.]+)\s*м²", text)
        floor_match = re.search(r"(\d+)/(\d+)\s*эт", text)
        area = float(area_match.group(1)) if area_match else None
        floor = int(floor_match.group(1)) if floor_match else None
        floors_total = int(floor_match.group(2)) if floor_match else None
        return area, floor, floors_total

    @staticmethod
    def _parse_geo(text: str) -> tuple[str | None, str | None]:
        parts = [p.strip() for p in text.split(",", 1)]
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0] if parts else None, None
```

- [ ] **Шаг 3: Запустить тесты**

```bash
pytest parser/tests/test_cian.py -v
# Ожидаем: 1 PASSED
```

- [ ] **Шаг 4: Коммит**

```bash
git add parser/parser/cian.py parser/tests/test_cian.py
git commit -m "parser: CianParser — fetch listings with stealth + proxy"
```

---

## Task 6: Celery задачи + расписание

**Files:**
- Create: `parser/parser/celery_app.py`
- Create: `parser/parser/tasks.py`
- Create: `parser/parser/__init__.py`
- Create: `parser/Dockerfile`

**Interfaces:**
- Consumes: `AvitoParser`, `CianParser`, `upsert_listing`, `SessionLocal`, `settings`
- Produces:
  - Celery beat расписание: 4 задачи каждые 3 часа
  - `parse_city(city, source, listing_type)` — Celery task
  - `notify_match(listing_id, event)` — Celery task (заглушка, Plan 2 заполнит логику)

- [ ] **Шаг 1: Написать `parser/parser/celery_app.py`**

```python
from celery import Celery
from celery.schedules import crontab
from parser.config import settings

app = Celery("parser", broker=settings.redis_url, backend=settings.redis_url)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    beat_schedule={
        "avito-moscow-sale": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("moscow", "avito", "sale"),
        },
        "avito-moscow-rent": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("moscow", "avito", "rent"),
        },
        "cian-moscow-sale": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("moscow", "cian", "sale"),
        },
        "cian-moscow-rent": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("moscow", "cian", "rent"),
        },
        "avito-spb-sale": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("spb", "avito", "sale"),
        },
        "avito-spb-rent": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("spb", "avito", "rent"),
        },
        "cian-spb-sale": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("spb", "cian", "sale"),
        },
        "cian-spb-rent": {
            "task": "parser.tasks.parse_city",
            "schedule": settings.parse_interval_seconds,
            "args": ("spb", "cian", "rent"),
        },
    },
)
```

- [ ] **Шаг 2: Написать `parser/parser/tasks.py`**

```python
import asyncio
import logging
from parser.celery_app import app
from parser.config import settings
from parser.database import SessionLocal
from parser.upsert import upsert_listing
from parser.avito import AvitoParser
from parser.cian import CianParser

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=300)
def parse_city(self, city: str, source: str, listing_type: str):
    """Парсит один источник+город+тип и сохраняет в БД."""
    logger.info(f"Parsing {source}/{city}/{listing_type}")
    parsed = 0
    errors = 0

    try:
        parser_cls = AvitoParser if source == "avito" else CianParser
        parser = parser_cls(proxies=settings.proxies)
        listings = asyncio.run(parser.fetch_listings(city, listing_type))

        session = SessionLocal()
        try:
            for data in listings:
                try:
                    listing, event = upsert_listing(session, data)
                    if event in ("new", "price_drop"):
                        notify_match.delay(str(listing.id), event)
                    parsed += 1
                except Exception as e:
                    errors += 1
                    logger.error(f"Upsert failed for {data.external_id}: {e}")
        finally:
            session.close()

    except Exception as exc:
        logger.error(f"Parse task failed: {exc}")
        raise self.retry(exc=exc)

    logger.info(f"Done {source}/{city}/{listing_type}: {parsed} parsed, {errors} errors")
    return {"parsed": parsed, "errors": errors}


@app.task
def notify_match(listing_id: str, event: str):
    """
    Заглушка — Plan 2 (backend) регистрирует реальный обработчик.
    Пока просто логируем.
    """
    logger.info(f"notify_match: listing={listing_id} event={event}")
```

- [ ] **Шаг 3: Написать `parser/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install -e .
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .
```

- [ ] **Шаг 4: Проверить запуск в Docker**

```bash
docker compose build parser
docker compose up postgres redis parser -d
docker compose logs parser -f
# Ожидаем: [INFO] celery@... ready.
# Через несколько секунд: [INFO] Parsing avito/moscow/sale
```

- [ ] **Шаг 5: Убедиться что объявления появляются в БД**

```bash
docker compose exec postgres psql -U app -d realestate \
  -c "SELECT source, city, type, count(*) FROM listings GROUP BY 1,2,3;"
# Ожидаем: строки с avito/moscow/sale и т.д.
```

- [ ] **Шаг 6: Коммит**

```bash
git add parser/
git commit -m "parser: celery tasks + beat schedule, all 8 city/source/type combinations"
```

---

## Task 7: Мониторинг парсера

**Files:**
- Modify: `parser/parser/tasks.py`
- Create: `parser/parser/monitor.py`

**Interfaces:**
- Produces: Redis-счётчики `parser:stats:{source}:{city}:{type}`, email-алерт при error_rate > 20%

- [ ] **Шаг 1: Написать `parser/parser/monitor.py`**

```python
import logging
import smtplib
from email.message import EmailMessage
import redis
from parser.config import settings

logger = logging.getLogger(__name__)
_redis = redis.from_url(settings.redis_url)


def record_stats(source: str, city: str, listing_type: str, parsed: int, errors: int):
    key = f"parser:stats:{source}:{city}:{listing_type}"
    _redis.hset(key, mapping={"parsed": parsed, "errors": errors})
    _redis.expire(key, 86400 * 7)

    if parsed + errors > 0:
        error_rate = errors / (parsed + errors)
        if error_rate > 0.2:
            _send_alert(source, city, listing_type, parsed, errors, error_rate)


def _send_alert(source, city, listing_type, parsed, errors, error_rate):
    if not settings.alert_email:
        return
    logger.warning(
        f"HIGH ERROR RATE {source}/{city}/{listing_type}: "
        f"{errors}/{parsed+errors} ({error_rate:.0%})"
    )
    # В продакшне заменить на Postmark/SES
    # Здесь просто логируем — достаточно для MVP
```

- [ ] **Шаг 2: Подключить в `tasks.py`**

Добавить в конец функции `parse_city` перед `return`:

```python
    from parser.monitor import record_stats
    record_stats(source, city, listing_type, parsed, errors)
    return {"parsed": parsed, "errors": errors}
```

- [ ] **Шаг 3: Проверить счётчики**

```bash
docker compose exec redis redis-cli HGETALL "parser:stats:avito:moscow:sale"
# Ожидаем: "parsed" "143" "errors" "2" (числа примерные)
```

- [ ] **Шаг 4: Коммит**

```bash
git add parser/parser/monitor.py parser/parser/tasks.py
git commit -m "parser: redis stats + error rate alerting"
```
