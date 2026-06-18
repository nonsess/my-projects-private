# Решение: монорепо для RestoGood

**Дата:** 2026-06-18  
**Статус:** принято

## Решение

Вместо раздельных репозиториев (`restogood-landing/` + `restogood-backend/`) — монорепо:

```
restogood/
  backend/          # FastAPI (Dockerfile внутри)
  frontend/         # Next.js (перенесён из restogood-landing/)
  docker-compose.yml  # только backend + postgres; frontend запускается отдельно npm run dev
```

## Причина

Даниил хочет одну директорию — проще запускать, деплоить, переключаться между сервисами.

## Последствия

- `restogood-landing/` становится архивом (не удалять пока не перенесём)
- Все пути в плане изменены: `restogood-backend/` → `restogood/backend/`, `restogood-landing/` → `restogood/frontend/`
- `feat/lead-form` ветка в `restogood-landing/` — закрыта; работа продолжается в `restogood/`
- Фронтенд-Dockerfile добавляется в Task 8 для полноты
