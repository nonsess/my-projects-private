---
name: izokom-dev-stack
description: Как корректно запускать dev-стек Изоком (Docker Compose, Ollama, Qdrant)
metadata:
  type: project
---

# Изоком — запуск dev-стека

Проект: [[изоком]]

## Порядок запуска

```bash
cd /home/pensioner/coding/new-izokom

# 1. Ollama должна быть запущена на хосте ДО docker compose
#    Проверить: systemctl status ollama
#    Должна слушать на 0.0.0.0:11434 (не 127.0.0.1!)
#    Конфиг: /etc/systemd/system/ollama.service.d/override.conf
#             → Environment="OLLAMA_HOST=0.0.0.0"

# 2. Поднять весь dev-стек (включая qdrant-dev!)
docker compose --profile dev up -d

# 3. Дождаться healthy (agent-dev depends_on: ollama-init-dev, redis, backend)
docker compose --profile dev ps
```

## Критичные зависимости

- **Ollama** — запускается как systemd-сервис на хосте (`ollama.service`), НЕ как Docker-контейнер. Контейнеры достучиваются через `host.docker.internal:11434`.
  - `OLLAMA_HOST=0.0.0.0` в `/etc/systemd/system/ollama.service.d/override.conf` обязателен.
  - `ollama-init-dev` — init-контейнер, делает `ollama pull $AGENT_TEM` (модель эмбеддингов). Это одноразовый запуск, после завершается.

- **qdrant-dev** — должен быть запущен ВМЕСТЕ с агентом. Если qdrant не поднят, agent-dev стартует с ошибкой несовместимости (логи), но продолжает работать. Запросы будут падать с `[Errno -3] Try again`.

- **Версии Qdrant**: клиент 1.16.2 vs сервер 1.18.0 — предупреждение о несовместимости в логах агента, работает несмотря на это.

## Частые проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| `[Errno -3] Try again` в агенте | Ollama или qdrant-dev не запущены | Проверить `systemctl status ollama` + `docker compose --profile dev ps` |
| Ollama не доступна из контейнера | `OLLAMA_HOST=127.0.0.1` (дефолт) | Выставить `OLLAMA_HOST=0.0.0.0` в systemd override |
| agent-dev не стартует | Нет `ollama-init-dev` (зависимость) | `docker compose --profile dev up -d` (не по-сервисно) |
| `HTTP 500` от backend | agent-dev упал или qdrant недоступен | `docker compose --profile dev logs agent-dev --tail=30` |

## Интеграционный тест

```bash
cd /home/pensioner/coding/new-izokom
python3 scripts/test_pre_answer.py
# Требует: backend-dev на :8000, agent-dev healthy, qdrant-dev up, Ollama на 0.0.0.0
```
