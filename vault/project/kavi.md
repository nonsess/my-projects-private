---
type: project
slug: kavi
updated: 2026-06-05
stage: прототип
north_star: рабочий онлайн-заказ еды с трекингом для ресторана
bottleneck: UX/дизайн фронта — карточки, мобильный вид, консистентность тем
stack: [Next.js, TypeScript, Python, FastAPI, PostgreSQL, MinIO, Docker]
path: ~/coding/kavi-project
---

# Kavi

## Суть
Онлайн-меню и система заказов для ресторана. Клиент выбирает блюда, оформляет заказ, отслеживает статус по трек-коду. Есть админ-панель с ролями (MANAGER / OWNER / SUPERADMIN), управление меню, заказами, дашборд.

## Что сделано
- JWT auth (httpOnly cookie), роли и права
- Backend: FastAPI + PostgreSQL + MinIO (presigned upload)
- Frontend: Next.js, публичная часть (меню, корзина, трекинг) + admin-панель
- Docker Compose + nginx (API + MinIO через прокси)
- Категории, продукты, заказы — полный CRUD в адмике
- Seed (меню + суперадмин, идемпотентный)

## Следующий шаг
Улучшить карточку последнего заказа (RecentOrder) — тень при ховере, мобильный layout
