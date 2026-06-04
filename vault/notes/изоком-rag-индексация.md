---
name: изоком-rag-индексация
description: Результаты индексации базы знаний Изоком в Qdrant, стек и нюансы
metadata:
  type: project
---

# Индексация базы знаний Изоком

Проект: `/home/pensioner/coding/new-izokom`

## Стек

- Embeddings: Ollama `bge-m3` (CPU, локально)
- Vector DB: Qdrant (Docker, `izokom-qdrant-dev`, порт 6333)
- Коллекции: `izokom_products`, `izokom_normatives`

## Что добавлено

Новый скрипт `apps/agent/src/agent/rag/ingest_docs.py` + `scripts/ingest_docs.sh`.
Обрабатывает: PDF (pymupdf), DOCX (python-docx), XLSX (openpyxl), MD.
Добавлена зависимость `python-docx>=1.1.2` в pyproject.toml + uv.lock обновлён.

## Результаты индексации (финальные, 2026-05-19)

| Коллекция | Чанков | Источник |
|---|---|---|
| `izokom_normatives` | 2000 | 14 PDF (ГОСТ + СП) |
| `izokom_products` | 3318 | 76 файлов (каталоги, презентации, отчёты, DOCX, MD) |

Коллекция `izokom_products` пересоздана с нуля (без дублей). 5 файлов с расширением `.docx` оказались UTF-8 Markdown — переименованы в `.md` и проиндексированы.

## Пропущенные файлы

- Скан-PDF без текстового слоя (сертификаты, большинство протоколов испытаний) — ожидаемо
- 5 файлов в `04_Дополнительные_материалы` имеют расширение `.docx`, но на самом деле UTF-8 текст с Markdown-разметкой (экспорт из LLM/Notion). Переименованы в `.md` и проиндексированы:
  - `analiticheskaya_zapiska_itog.md`
  - `article_izokom_rso_forum.md`
  - `obosnovanie_c-pentane_mo.md`
  - `obosnovanie_cyclopentane.md`
  - `pismo_c-pentane_minenergo_2025-12-01.md`
- Все остальные DOCX в `04_Дополнительные_материалы` переименованы в латиницу (были кириллические имена).

## Запуск ingest (обход Ollama-проблемы)

Ollama запущен как системный сервис (пользователь `ollama`), слушает только `127.0.0.1`. Docker не может достучаться через `host.docker.internal`. Обходной путь — запускать через `docker run --network host`:

```bash
CUSTOMER_REAL="$(readlink -f data/customer)"
docker run --rm --network host \
  -v "$(pwd)/data:/app/apps/agent/data:ro" \
  -v "$CUSTOMER_REAL:/app/apps/agent/data/customer:ro" \
  -e AGENT_OLLAMA_URL=http://localhost:11434 \
  -e AGENT_QDRANT_HOST=localhost \
  -e AGENT_QDRANT_PRODUCTS_COLLECTION=izokom_products \
  -e AGENT_QDRANT_NORMATIVES_COLLECTION=izokom_normatives \
  -e AGENT_LLM=gpt-4o -e AGENT_API_KEY=dummy \
  -e AGENT_TEM=bge-m3 -e AGENT_MAX_TOKENS=4000 \
  -e AGENT_REDIS_HOST=localhost \
  new-izokom-agent-dev \
  python -m src.agent.rag.ingest_docs
```

Долгосрочный фикс: добавить `OLLAMA_HOST=0.0.0.0` в `/etc/systemd/system/ollama.service.d/override.conf`.

## Перенос на деплой

1. **Qdrant Snapshots API** (рекомендуется):
   ```bash
   curl -X POST http://localhost:6333/collections/izokom_products/snapshots
   curl -X POST http://localhost:6333/collections/izokom_normatives/snapshots
   # Загрузить .snapshot на сервер через upload API
   ```
2. **Volume backup**: `docker run --rm -v new-izokom_qdrant-data:/data alpine tar czf /backup/qdrant.tar.gz /data`
3. **Переиндексация**: положить `data/customer/` на сервер, прогнать ingest-скрипты заново

## Сохранность данных

Документы в `data/customer/` — источник истины. Qdrant — производное. Если Qdrant упал → переиндексировать (~20-30 мин на CPU).
