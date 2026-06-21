---
type: note
slug: flajok-infra-restart-migrations
updated: 2026-06-21
project: flazhok
---

# Флажок — авто-миграции и restart-политика БД

## Проблема (2026-06-21)
Бэк начал 500-ить: `relation "listings" does not exist`. Причина — postgres и redis
**легли** (`Exited (0)`) и не поднялись сами: у них не было `restart`-политики,
а у backend/parser была (`unless-stopped`). После перезапуска докера/хоста бэк
ожил, БД — нет. Плюс volume пересоздался → схема обнулилась, а накатывать
миграции на старте было некому (команда бэка — голый `uvicorn`).

## Фикс
1. `docker-compose.yml`: команда бэка → `sh -c "alembic upgrade head && uvicorn ..."`
   — миграции докатываются автоматически при каждом старте.
2. `restart: unless-stopped` добавлен postgres и redis.
3. Восстановление вручную (когда уже легло): `alembic upgrade head` →
   `python -m scripts.seed_demo` → `python -m scripts.backfill_districts`.

## Вывод
Любой stateful-сервис в compose обязан иметь `restart: unless-stopped`.
Миграции — часть запуска приложения, а не ручной шаг.
