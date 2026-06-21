---
type: decision
slug: flajok-backend-layered-architecture
date: 2026-06-21
project: flazhok
---

# Флажок — слоистая архитектура бэкенда

## Решение
Бэкенд переведён на слои: **router → service → repository → DB**. Классы +
Depends-DI. Рефактор инкрементальный по доменам.

## Правила
- **Router** — только HTTP: распарсить, дёрнуть сервис, отдать схему. Ни одного `select()`.
- **Service** — бизнес-логика (лимиты, гейты, оркестрация). Без FastAPI, без сырого SQL.
- **Repository** — только данные: принимает `AsyncSession`, гоняет SQLAlchemy.
- **deps.py** — DI: session → repo → service (FastAPI кэширует get_session в рамках
  запроса → все репо делят одну сессию).
- Доменные ошибки `app/services/errors.py` (BadRequest/NotFound/Forbidden) →
  единый exception-handler в main.py переводит в HTTP. Роутеры не ловят исключения.

## Сделано (домены)
- subscription, filters, listings — переведены полностью (репо + сервис + тонкий роутер).
- Заодно закрыты находки аудита: IDOR на `/listings/{id}` и `/history` (видимость
  привязана к активным фильтрам юзера), идемпотентность вебхука по `payment_id`
  (повторный webhook не продлевает срок — был Critical: бесплатное продление).

## Осталось
- auth, account, public (399 строк, programmatic SEO) — следующий заход.
- parser отдельный репозиторий, не трогали.

## Связанные
[[flajok-tier-matrix-single-source]], [[flajok-infra-restart-migrations]].
