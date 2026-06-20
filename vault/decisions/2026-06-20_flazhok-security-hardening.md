---
type: decision
date: 2026-06-20
project: flazhok
status: принято
---

# Security hardening: rate limiting, webhook верификация, закрытые порты

## Что решил

1. **Rate limiting** через slowapi: register 5/мин, login 10/мин. Limiter вынесен в отдельный модуль `app/limiter.py` (иначе circular import: main.py → routers/auth.py → main.py).
2. **Webhook ЮKassa**: проверяем Payment.find_one(payment_id) перед активацией подписки — защита от фейковых payment.succeeded событий.
3. **Порты БД и Redis** убраны из expose в docker-compose — только внутри docker-сети.
4. **uvicorn**: убран --reload, добавлен --workers 2.
5. **SECRET_KEY** обязателен через `${SECRET_KEY:?SECRET_KEY must be set}`.
6. **Secure cookie**: `secure: true` только при https (window.location.protocol === "https:").
7. **Security headers в Caddy**: X-Frame-Options SAMEORIGIN, X-Content-Type-Options nosniff, Referrer-Policy no-referrer, CSP.
8. **Пароль**: минимум 8 символов (Pydantic validator).

## Почему

Продакшн-деплой близко. Базовые меры дёшевы сейчас, дороги после инцидента.

## Альтернативы

- JWT refresh tokens — отложено, не критично для MVP
- Sentry / мониторинг — отложено
- 2FA — отложено
