---
type: note
slug: flajok-refresh-tokens
updated: 2026-06-21
project: flazhok
---

# Флажок — refresh-токены и ревокация

## Что внедрено
Короткий **access** (30 мин, JWT type=access) + длинный **refresh** (30 дней,
JWT type=refresh с jti). jti хранится в Redis (`refresh:{jti}` → user_id) — это
даёт серверную ревокацию и обнаружение повторного использования.

## Механика
- `app/services/tokens.py` `TokenService`: `issue_pair`, `rotate`, `revoke`.
- **Ротация**: каждый `/auth/refresh` удаляет старый jti и выдаёт новую пару.
  Если jti уже нет в Redis (повторное использование/отзыв) → 401.
- **Запрет подмены**: `decode_token` принимает только type=access — refresh-токен,
  подсунутый как access-cookie, отклоняется.
- **logout**: `/auth/logout` удаляет jti из Redis (реальный серверный отзыв).
- Cookie: `rt_token` (access, path=/), `rt_refresh` (path=/api/auth — уходит только
  на refresh/logout), `rt_auth` (читаемый флаг).
- Фронт `api.ts`: на 401 один молчаливый `POST /auth/refresh` (single-flight),
  затем повтор запроса; провал → редирект на /login.

## Redis
Клиент `app/redis_client.py` (`redis.asyncio`, пакет ставится через celery[redis]).

## Проверено (curl)
выдача 3 cookie · access→200 · ротация→200 · reuse старого refresh→401 ·
refresh как access→401 · logout→refresh→401.

## Связанные
[[flajok-auth-hardening]], [[flajok-backend-layered-architecture]].
