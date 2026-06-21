---
type: task
updated: 2026-06-21
---

# Backlog

- **[kavi]** закрыть предоплату с клиентом
- **[restogood-landing]** купить домен restogood.ru
- **[restogood-landing]** получить реальные отзывы (заменить placeholder Kavi)
- **[restogood-landing]** уточнить финальные цены пакетов

## Флажок — безопасность
- **DONE 2026-06-21:** IDOR на /listings/{id} и /history, идемпотентность вебхука, JWT в HttpOnly-cookie, OAuth-callback redirect, secret_key fail-fast, rate-limit за прокси (XFF), Next 14.2.35 (CVE-2025-29927), HSTS, CORS сужен, mock-платежи fail-fast (см. [[2026-06-21_flajok-auth-hardening]])
- **DONE 2026-06-21:** ревокация токена — короткий access (30м) + refresh (30д) с jti в Redis, ротация с reuse-detection, серверный logout, refresh нельзя использовать как access; молчаливый refresh по 401 на фронте (см. [[flajok-refresh-tokens]])
- **[flajok]** миграция Next 14 → 16 (остаточные DoS/cache advisory лечатся только мажором) — отложено осознанно
- **[flajok]** CSP без unsafe-inline (nonce в Next) — риск сломать, отдельно

## Флажок — платежи (из аудита 2026-06-21)
- **[flajok]** Idempotence-Key при Payment.create; сверка суммы платежа; обработка refund/canceled
- **[flajok]** решить: рекуррент (автосписание) vs разовый + email-напоминание о продлении
- **[flajok]** СБП как основной метод (payment_method_data sbp / confirmation qr) — комиссия 0.4-0.7% vs карты

## Флажок — карта объявления
- **DONE 2026-06-21:** карта на странице объявления — виджет Яндекс.Карт (iframe, без ключа), геокод по «город, адрес», CSP frame-src добавлен

## Флажок — рефактор
- **DONE 2026-06-21:** весь бэк переведён на слои (router→service→repository): subscription, filters, listings, auth, account, public

