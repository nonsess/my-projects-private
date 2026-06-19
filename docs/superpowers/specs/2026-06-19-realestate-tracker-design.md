# Спек: трекер недвижимости для физлиц

**Дата:** 2026-06-19  
**Автор:** Даниил  
**Статус:** согласован

---

## Идея

Веб-сервис для людей, которые активно ищут квартиру в Москве или СПб. Отслеживает новые объявления по сохранённым критериям, хранит историю цен каждого объявления, отправляет email-алерты при новом объявлении или снижении цены.

Аналог: camelcamelcamel.com — трекер цен Amazon, только для недвижимости.

**Не** агрегатор в стиле Авиасейлс — монетизация через подписку физлица, не CPA от агентств.

---

## Рынок (кратко)

- ЦИАН: 20,2 млн MAU, 8 из 10 ищут на ЦИАН
- Москва вторичка: ~11 700 сделок/мес, поиск длится 2–6 месяцев
- Рынок аренды 2026: +32% предложения в Q1, спрос +25–30%
- Прямых B2C конкурентов нет; ЦИАН PRO — для агентств (3 390 руб/мес)
- Детальный анализ: `vault/notes/realestate-tracker-market-analysis.md`

---

## Scope MVP

### IN

- Регистрация / авторизация (Google + VK + Яндекс + email/пароль)
- Создание фильтров поиска
- Парсер Авито + ЦИАН (Москва + СПб), самостоятельный
- История цен каждого объявления (хранится с первого дня)
- Email-алерты: новое объявление + снижение цены
- Дашборд: фильтры + последние совпадения
- Карточка объявления: метаданные + график истории + ссылка на оригинал
- Подписка (ЮKassa), три тарифа

### OUT (после MVP)

- Карта объектов
- Аналитика района (медиана цен)
- Совместный поиск
- Браузерные push-уведомления
- Мобильное приложение
- Ипотечный калькулятор

---

## Тарифы

| | Free | Базовый — 299 руб/мес | Про — 599 руб/мес |
|---|---|---|---|
| Фильтров | 1 | 5 | 20 |
| Алерты | задержка 24 ч | мгновенно | мгновенно |
| История цен | нет | 30 дней | полная |

---

## Архитектура

Три компонента:

```
┌─────────────┐     ┌────��─────────────┐     ┌──��──────────┐
│   Парсер    │────▶│   PostgreSQL     │◀────│   Backend   │
│ (Playwright │     │                  │     │  (FastAPI)  │
│  + Celery)  │     │ listings         │     │             │
└─────────────┘     │ price_history    │     └──────┬──────┘
      │             │ filters          │            │
      │             │ alerts           │            │
   Redis            │ users            │     ┌──────▼──────┐
   (очередь)        │ subscriptions    │     │  Frontend   │
                    └──────────────────┘     │  (Next.js)  │
                                             └──────��──────┘
```

**Инфра:** Docker Compose, один VPS (2–4 CPU, 4 GB RAM) на старте.

---

## Парсер

### Источники и поля

Парсим только метаданные (юридически безопасная зона):

| Поле | Описание |
|---|---|
| `external_id` | ID объявления на площадке |
| `source` | `avito` / `cian` |
| `type` | `sale` / `rent` |
| `price` | руб |
| `area` | м² |
| `floor` / `floors_total` | этаж / этажей в доме |
| `district` | район |
| `city` | Москва / СПб |
| `address` | улица (без контактов) |
| `url` | ссылка на оригинал |

Телефоны, полный текст, фото — не собираем.

### Стратегия против блокировок

- Playwright + playwright-stealth (обход fingerprint detection)
- Пул мобильных прокси (5–10 IP, ротация per-request)
- Случайные задержки 2–7 сек между запросами
- Ротация User-Agent (реальные мобильные UA)
- Парсим страницы поиска, не массовый обход карточек

### Расписание (Celery beat)

Каждые 3 часа:
- `parse_city(city="moscow", source="avito")`
- `parse_city(city="moscow", source="cian")`
- `parse_city(city="spb", source="avito")`
- `parse_city(city="spb", source="cian")`

Оценка нагрузки: ~1 600 запросов каждые 3 часа (~9 запросов/мин) — умеренно.

### Логика upsert

```python
existing = db.get_listing(source, external_id)
if not existing:
    db.insert(listing)
    db.insert(price_history, price=new_price)
    trigger match_filters(listing, event="new")
elif existing.price != new_price:
    db.update(listing, price=new_price)
    db.insert(price_history, price=new_price)
    if new_price < existing.price:
        trigger match_filters(listing, event="price_drop")
```

### Мониторинг парсера

- Счётчики в Redis: `listings_parsed`, `errors`, `blocked_requests`
- Email-алерт разработчику если `errors > 20%` за цикл
- Ротируемые логи

---

## База данных

```sql
listings (
  id              uuid PK,
  source          enum('avito','cian'),
  external_id     text,
  type            enum('sale','rent'),
  city            enum('moscow','spb'),
  price           integer,
  area            numeric(6,1),
  floor           smallint,
  floors_total    smallint,
  district        text,
  address         text,
  url             text,
  is_active       boolean,
  first_seen_at   timestamptz,
  last_seen_at    timestamptz,
  UNIQUE(source, external_id)
)

price_history (
  id          uuid PK,
  listing_id  uuid FK listings,
  price       integer,
  recorded_at timestamptz,
  INDEX(listing_id, recorded_at)
)

filters (
  id          uuid PK,
  user_id     uuid FK users,
  name        text,
  city        enum('moscow','spb'),
  type        enum('sale','rent'),
  districts   text[],
  price_min   integer,
  price_max   integer,
  area_min    numeric(5,1),
  area_max    numeric(5,1),
  floor_min   smallint,
  is_active   boolean,
  created_at  timestamptz
)

alerts (
  id          uuid PK,
  user_id     uuid FK users,
  filter_id   uuid FK filters,
  listing_id  uuid FK listings,
  type        enum('new','price_drop'),
  sent_at     timestamptz,
  INDEX(user_id, listing_id)
)

users (
  id              uuid PK,
  email           text UNIQUE,
  password_hash   text NULL,
  oauth_provider  text,           -- 'google' | 'vk' | 'yandex' | null
  oauth_id        text,
  created_at      timestamptz,
  alert_email     text
)

subscriptions (
  id              uuid PK,
  user_id         uuid FK users,
  plan            enum('free','basic','pro'),
  status          enum('active','cancelled','expired'),
  started_at      timestamptz,
  expires_at      timestamptz,
  yukassa_id      text
)
```

---

## Backend API

```
AUTH
  POST /auth/register
  POST /auth/login
  POST /auth/logout
  GET  /auth/oauth/{provider}          -- redirect to provider
  GET  /auth/oauth/{provider}/callback

FILTERS
  GET    /filters
  POST   /filters
  PUT    /filters/{id}
  DELETE /filters/{id}
  PATCH  /filters/{id}/toggle

LISTINGS
  GET /filters/{id}/listings   ?sort=date|price  ?type=new|price_drop|all
  GET /listings/{id}
  GET /listings/{id}/history

SUBSCRIPTION
  GET  /subscription
  POST /subscription/checkout
  POST /webhooks/yukassa

ACCOUNT
  GET /account
  PUT /account/alert-email
```

### Матчинг фильтров

```python
def match_filters(listing, event):
    filters = db.query("""
        SELECT f.* FROM filters f
        JOIN subscriptions s ON s.user_id = f.user_id
        WHERE f.city = :city AND f.type = :type
          AND f.is_active = true AND s.status = 'active'
    """)
    for filter in filters:
        if not matches(listing, filter):
            continue
        already_sent = db.exists(alerts,
            filter_id=filter.id, listing_id=listing.id, type=event)
        if already_sent:
            continue
        delay = 86400 if filter.user.plan == 'free' else 0
        send_alert.apply_async(
            args=[filter.user_id, filter.id, listing.id, event],
            countdown=delay
        )
```

---

## Фронтенд

**Стек:** Next.js App Router, TypeScript, Tailwind, Recharts (графики), react-select (мультиселект районов).

Серверный рендеринг — только лендинг. Остальное — клиентские страницы за авторизацией.

### Экраны

1. **Лендинг** — проблема → решение → тарифы → CTA «Начать бесплатно»
2. **Авторизация** — кнопки Google / VK / Яндекс + форма email/пароль
3. **Дашборд** — список фильтров, счётчик новых объявлений, кнопка «+ Создать»
4. **Создание / редактирование фильтра** — город, тип, районы (мультиселект), цена, площадь, этаж
5. **Список объявлений по фильтру** — сортировка, фильтр по типу алерта, бейдж «цена снизилась»
6. **Карточка объявления** — метаданные + линейный график истории цены + ссылка на оригинал
7. **Настройки** — alert_email, пароль, управление подпиской

---

## Юридические риски

| Риск | Оценка | Митигация |
|---|---|---|
| Иск за нарушение прав на БД (ст. 1334 ГК РФ) | Реальный, маловероятный | Только метаданные, нет телефонов, ссылка на оригинал |
| Авторские права на контент объявлений | Средний | Не показываем фото и полный текст |
| 152-ФЗ (персональные данные) | Стандартный | Политика конфиденциальности + согласие + РКН |

---

## Стек итого

| Слой | Технология |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind, Recharts |
| Backend | Python, FastAPI |
| Парсер | Python, Playwright, playwright-stealth, Celery |
| Очередь | Redis |
| БД | PostgreSQL |
| Email | Postmark или Resend |
| Платежи | ЮKassa |
| Прокси | Мобильный прокси-пул |
| Инфра | Docker Compose, VPS |

---

## Сроки

| Неделя | Что |
|---|---|
| 1–2 | Парсер: Playwright + прокси, Авито Москва вторичка, upsert + история |
| 2–3 | Бэкенд: FastAPI, схема БД, авторизация, матчинг, алерты; добавляем ЦИАН + С��б |
| 3–4 | Фронтенд: лендинг, авторизация, дашборд, фильтры, список, карточка |
| 4–5 | ЮKassa, тарифные лимиты, настройки, Docker Compose, VPS, бета |
