---
date: 2026-05-22
slug: изоком-ci-permissions-job-level
project: изоком
status: done
---

# Решение: перенести permissions с уровня воркфлоу на уровень job

## Контекст

В `new-izokom/.github/workflows/ci.yaml` стояло:

```yaml
permissions:
  contents: read
```

на уровне воркфлоу. Это создавало потолок — ни один job не мог получить права сверх `contents: read`, в том числе `packages: write`, нужный для push в GHCR. Образы не пушились, CI падал.

## Решение

Убрать `permissions` с уровня воркфлоу. Добавить `permissions: contents: read` только на job-ы, которым нужен checkout и не нужен push: `changes`, `lint`, `update-manifests`. Build jobs (`build-agent`, `build-backend`, `build-bot`, `build-frontend`) сохраняют свои полные permissions с `packages: write`.

Коммит: `f0e466c`, запушено 2026-05-22.

## Второй раунд (2026-05-23, коммит `5e33323`)

После первого фикса `changes` и `lint` упали на checkout — implicit `contents: none` при наличии хотя бы одного sibling job с explicit permissions. Решение: добавить `permissions: contents: read` на уровне воркфлоу как floor для всех jobs. Это не конфликтует с первым фиксом: build jobs всё ещё имеют свои explicit permissions, которые расширяют floor.

Итоговая схема: workflow-level `contents: read` (floor) + job-level `packages: write` в build jobs.

## Связи

[[изоком]], [[изоком-ci-permissions-fix]]
