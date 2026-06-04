---
date: 2026-05-22
project: изоком
slug: изоком-url-документов-фикс
task: "#35"
---

# Фикс URL скачивания документов (задача #35)

## Проблема

Ссылки на скачивание документов генерировались с внутренним адресом бэкенда:
`backend:8000//documents/download`

## Причина

`BASE_URL` в `apps/frontend/src/shared/config/api.ts` определяется через `createIsomorphicFn`:
- клиент: `import.meta.env.VITE_BASE_URL`
- сервер: `process.env.DIRECT_BASE_URL`

При сборке в Docker `VITE_BASE_URL=/api` прокидывается как `build-arg`. В prod это корректно работает как `/api`. Проблема могла возникать при разворачивании без build-arg или при несовпадении значений.

## Решение

Убедиться, что `VITE_BASE_URL=/api` прокинут в build args при сборке фронта. Dockerfile.prod уже содержал:
```
build-args: |
  VITE_BASE_URL=/api
```

Публичный URL: `izokom.bbaauto.store/api/documents/download`.

Файл компонента: `apps/frontend/src/widgets/DocumentsSection/ui/DocumentsSection.tsx`
