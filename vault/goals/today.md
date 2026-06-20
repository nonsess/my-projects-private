---
type: goal
horizon: today
updated: 2026-06-20
active_projects: [kavi]
---

# Сегодня

- [x] Рефакторинг vault — автоматизация агента
- [ ] Закрыть предоплату по Кави
- [ ] Определиться со стратегией конвейера (Кворк / продуктизация)

## 2026-06-14 — сделано по Кави

- [x] Слоты доставки + часы работы (блокировка вне часов, иркутское время)
- [x] Хиты и дашборд только для COMPLETED заказов + cancel rate
- [x] Уведомления: браузер (админ + клиент) с beep-звуком
- [x] PWA манифест + иконки + service worker
- [x] Web Push уведомления (VAPID, pywebpush, push_subscriptions таблица)
- [x] SEO: robots, sitemap, OG, JSON-LD Restaurant + FAQPage, FAQ аккордион
- [x] Юридика: /privacy, /offer, текст согласия под кнопкой
- [x] Футер: реальные контакты + SEO-текст

## 2026-06-20 — Флажок (трекер недвижимости)

- [x] Продающий лендинг (PAS/StoryBrand), название «Флажок»
- [x] shadcn/ui + Lucide на всех экранах
- [x] Skeleton loading: dashboard, listings, settings, detail
- [x] Toast (sonner) вместо alert/confirm везде
- [x] Клиентская фильтрация объявлений (цена мин/макс, площадь, 4 режима сортировки)
- [x] Copy URL на карточках и детальной странице
- [x] Source badge ЦИАН/Авито
- [x] Отмена подписки с toast-confirm, API cancel endpoint
- [x] Мобильная адаптация на всех страницах
- [x] TypeScript без ошибок, коммит

## Доделано по Флажку (финал 2026-06-20)

- [x] Безопасность: rate limiting (slowapi), webhook верификация ЮKassa, закрытые порты БД/Redis, security headers Caddy, secure cookie, пароль min 8 символов
- [x] Checkout bug исправлен (checkout_url → confirmation_url)
- [x] Cancel subscription endpoint (DELETE /subscription/cancel)
- [x] Circular import исправлен (app/limiter.py)
- [x] 502 на логин исправлен (ALTER USER + env выровнен)
- [x] Лендинг полный редизайн: ProductMockup (браузер-хром + дашборд), iOS NotifCard, split-hero
- [x] .env с полным набором переменных
- [x] TypeScript чистый

## Следующий шаг по Флажку

- [ ] Купить домен flazhok.ru → задеплоить на VPS → настроить Postmark + ЮKassa prod

## Осталось по Кави (не срочно)

- [ ] Заполнить ИНН/ОГРН в /privacy и /offer
- [ ] Добавить VAPID ключи в .env на сервере
- [ ] Подать уведомление в РКН (pd.rkn.gov.ru)
- [ ] Зарегистрировать Яндекс.Бизнес + Google Business Profile
