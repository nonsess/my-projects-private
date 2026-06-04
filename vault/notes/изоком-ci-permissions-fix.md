---
date: 2026-05-23
project: изоком
slug: изоком-ci-permissions-fix
---

# Фикс permissions в GitHub Actions CI (new-izokom)

## Проблема

Workflow-level `permissions: contents: read` выступал потолком и блокировал `packages: write` в job-ах `build-agent`, `build-backend`, `build-bot`, `build-frontend`. Манифесты не пушились, CI падал.

## Решение

Убрать `permissions` с уровня воркфлоу. Перенести `contents: read` только на job-ы, которым это нужно (`changes`, `lint`, `update-manifests`). Build jobs сохраняют свои полные permissions.

Файл: `.github/workflows/ci.yaml`. Коммит: `f0e466c`, запушено в `brain-boost-academy/new-izokom`.

## Второй раунд фикса (2026-05-23, коммит `5e33323`)

После первого фикса (`f0e466c`) упал checkout в job-ах `changes` и `lint` — они не имели явных permissions и при наличии хотя бы одного job с explicit permissions получали implicit `contents: none`. Решение: добавить `permissions: contents: read` на уровне воркфлоу как базовый уровень (floor) для всех jobs.

Это противоположное направление первого фикса (там убирали workflow-level), но другой симптом: первый фикс решал конфликт floor vs ceiling для `packages: write`, второй обеспечивает минимум для checkout.

## Суть правила

Workflow-level permissions — потолок для всех job-ов. Если поставить `contents: read` глобально — ни один job не получит прав сверх этого, даже если в нём прописано `packages: write`.

При этом jobs без explicit permissions получают `none` по всем scope, если хотя бы один sibling job имеет explicit permissions. Workflow-level `contents: read` нужен как floor для базового checkout.
