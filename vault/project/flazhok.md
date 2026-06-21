---
type: project
slug: flazhok
updated: 2026-06-20
stage: прототип
north_star: первые платящие пользователи (хотя бы 3 подписки basic/pro)
bottleneck: нет домена и продакшн-деплоя, нет реальных пользователей, парсер требует прокси для работы
stack:
  - Next.js 14 App Router
  - shadcn/ui + Tailwind CSS
  - FastAPI + SQLAlchemy (async)
  - PostgreSQL + Redis
  - Celery + Beat (парсер)
  - Docker Compose + Caddy
  - ЮKassa (оплата)
  - Postmark (email-алерты)
  - OAuth: Google / VK / Яндекс
  - slowapi (rate limiting)
---

# Флажок

## Суть

SaaS-трекер цен на недвижимость. Пользователь задаёт фильтр (город, районы, тип, бюджет, площадь) — и получает email когда цена на подходящую квартиру снижается. Парсит ЦИАН и Авито. Монетизация через подписку (free/basic/pro).

## Что сделано

- Полная аутентификация: email/пароль (min 8 символов) + OAuth (Google, VK, Яндекс)
- JWT + secure cookie (https-aware)
- Создание/удаление фильтров поиска (до 1 для free, до 3 для basic, до 10 для pro)
- Парсер на Celery Beat — сбор с ЦИАН/Авито, хранение в PG, diff по ценам
- Email-алерты через Postmark при снижении цены
- Страница объявлений с клиентской фильтрацией (цена, площадь) и 4 режимами сортировки
- ListingCard с copy URL и source badge (ЦИАН / Авито)
- Подписка через ЮKassa: checkout, webhook-верификация (Payment.find_one), отмена (DELETE /subscription/cancel)
- Страница настроек: скелетон, смена пароля, апгрейд тарифа, отмена подписки с toast-подтверждением
- Лендинг: тёмный (bg #0C0C0E), split-hero (копия слева, ProductMockup справа), iOS NotifCard, секции проблем/функций/тарифов/FAQ
- Безопасность: rate limiting (5/мин на register, 10/мин на login), закрытые порты БД/Redis, security headers в Caddy (CSP, X-Frame-Options, X-Content-Type-Options), Referrer-Policy, убран --reload из uvicorn, --workers 2
- 404 страница, success-страница после оплаты (Suspense wrapper)
- Все alert()/confirm() заменены на Sonner toast
- Skeleton loading на dashboard, listings, settings
- Docker Compose полный стек (postgres, redis, backend, parser, frontend, caddy)
- .env с полным набором переменных, .env.example задокументирован
- SECRET_KEY обязателен через docker-compose (${SECRET_KEY:?...})

## Архитектура

```
Caddy (порт 80/443)
  ├── /api/* → backend (FastAPI, uvicorn, 2 workers)
  └── /* → frontend (Next.js, standalone build)

PostgreSQL (только docker-сеть, порт не выставлен)
Redis (только docker-сеть, порт не выставлен)
Parser (Celery worker + beat, 1 контейнер)
```

Бэкенд — слоистая архитектура (router → service → repository → DB, классы + Depends-DI),
все домены переведены. Доменные ошибки `services/errors.py` → единый handler в main.py.
Тарифы — единый конфиг `app/plans.py`, раздаётся через `GET /plans`. Миграции
накатываются на старте (`alembic upgrade head` в команде backend). См. решения
flajok-backend-layered-architecture, flajok-tier-matrix-single-source.

## API роуты

- POST /auth/register, /auth/login
- GET /auth/oauth/{provider}, /auth/oauth/{provider}/callback
- GET/POST/DELETE /filters
- GET /filters/{id}/listings
- POST /subscription/checkout, DELETE /subscription/cancel
- POST /subscription/webhook (ЮKassa)
- GET/PUT /account/me, POST /account/change-password

## Тарифы

| | free | basic (299₽/мес) | pro (599₽/мес) |
|---|---|---|---|
| Фильтров | 1 | 3 | 10 |
| Email-алерты | нет | моментальные | моментальные |
| Обновление | раз в 2 часа | раз в час | раз в час |
| История цен | нет | 30 дней | полная |

Единый источник правды по тарифам — `backend/app/plans.py`, раздаётся через `GET /plans`, фронт не хардкодит (см. решение tier-matrix-single-source). Free не получает email-алертов вообще.

## Известные ограничения / что не сделано

- OAuth не тестировался в prod (нет callback URL)
- Парсер без прокси заблокируется на реальных объёмах
- Email-алерты требуют верифицированного Postmark-домена
- Нет CI/CD
- Нет мониторинга (no Sentry, no Grafana)
- Нет тестов (ни unit, ни e2e)

## Следующий шаг

Купить домен → задеплоить на VPS → настроить Postmark + ЮKassa → первые реальные пользователи.
