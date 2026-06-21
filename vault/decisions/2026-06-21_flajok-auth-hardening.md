---
type: decision
slug: flajok-auth-hardening
date: 2026-06-21
project: flazhok
---

# Флажок — харденинг аутентификации и безопасности (по аудиту)

## Решение
JWT переведён в HttpOnly-cookie, выставляемую сервером. JS токен не видит →
XSS его не украдёт. Рядом — читаемый флаг `rt_auth` для клиентского роутинга
(секрета не несёт).

## Сделано (проверено smoke)
- **HttpOnly-cookie** `rt_token` (SameSite=Lax, Secure в проде, Max-Age=TTL).
  register/login/oauth ставят cookie, тело ответа токен НЕ содержит.
- **/auth/logout** — сервер чистит обе cookie (раньше logout был только на клиенте).
- **OAuth-callback** теперь `RedirectResponse` на `frontend_url/dashboard` + cookie,
  а не голый JSON с токеном в браузер.
- **get_current_user** читает токен из cookie (фолбэк — Bearer для API-клиентов).
- **secret_key fail-fast**: пустой + `APP_ENV=production` → падаем на старте.
- **rate-limit за прокси**: key_func берёт реальный IP из X-Forwarded-For (последний,
  его дописывает Caddy; спуф клиента левее). Проверено: 5 register → 429.
- **mock-платежи fail-fast**: в проде пустой `YUKASSA_SHOP_ID` → ошибка, а не молчаливая
  бесплатная раздача подписок.
- **Next.js 14.2.3 → 14.2.35** (закрыт CVE-2025-29927 обход middleware).
- **HSTS**-заголовок в Caddy; CORS сужен до `frontend_url`.
- TTL токена 7д → 2д.
- Фронт: `auth.ts` работает с флагом `rt_auth`; все fetch — `credentials: "include"`,
  без Authorization-заголовка; logout через сервер.

## Осталось (backlog)
- Ревокация токена (jti-blacklist в Redis) + refresh-токены — TTL пока «тупой».
- Миграция Next 14 → 16 (остаточные DoS/cache advisory лечатся только мажором).
- CSP без `unsafe-inline` (nonce в Next) — риск сломать, отдельно.

## Связанные
[[flajok-backend-layered-architecture]], [[flajok-tier-matrix-single-source]].
