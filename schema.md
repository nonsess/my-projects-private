# Схема памяти

Вся память — markdown-файлы в `vault/`. Агент ведёт wiki сам, владелец курирует.

## Структура

```
vault/
  index.md             ← каталог заметок
  log.md               ← append-only журнал сессий

  profile/             ← кто владелец (правки только с «ок»)
    about.md
    use_cases.md

  project/             ← проекты (по файлу на проект)
    index.md
    <slug>.md

  goals/
    today.md
    week.md
    month.md
    quarter.md
    year.md

  tasks/
    backlog.md
    in_progress.md
    blocked.md

  decisions/           ← один файл = одно решение
    YYYY-MM-DD_slug.md

  people/
    <slug>.md
    index.md

  notes/               ← атомарные заметки
  insights/            ← паттерны поведения
```

## Форматы

### vault/profile/about.md

```yaml
---
type: profile
updated: YYYY-MM-DD
name: ...
preferred_address: ты
language: ru
agent_name: ...
---
```

### vault/project/<slug>.md

```yaml
---
type: project
slug: ...
updated: YYYY-MM-DD
stage: идея | прототип | первые_клиенты | выручка | масштаб | кризис
north_star: ...
bottleneck: ...
stack: [..., ...]
---

# Название

## Суть
<2–3 предложения>

## Что сделано
- ...

## Следующий шаг
<одно действие>
```

### vault/decisions/YYYY-MM-DD_slug.md

```markdown
---
type: decision
date: YYYY-MM-DD
project: <slug>
status: принято | пересмотрено | отменено
---

# <Короткая формулировка>

## Что решил

## Почему

## Альтернативы
```

### vault/log.md

Append-only.

```markdown
## 2026-06-05
Сессия 45 мин. Проект: kavi. Разобрали авторизацию JWT. Стоп: refresh tokens.
```

### vault/goals/today.md

```markdown
---
type: goal
horizon: today
updated: YYYY-MM-DD
---

# Цель на сегодня

- [ ] ...
```

### vault/tasks/*.md

```markdown
---
type: task
updated: YYYY-MM-DD
---

# In progress

- **[proj-slug]** описание — due: YYYY-MM-DD
```

## Операции (старт сессии)

1. `git pull --ff-only` (если remote).
2. Читать параллельно: `vault/profile/about.md`, `vault/project/index.md`, последние 7 записей `vault/log.md`, `vault/goals/today.md`, последние 10 записей `vault/insights/log.md`.
3. Читать **все** карточки из секции `## Активные` в `vault/project/index.md`.
4. Если тема — grep по `vault/notes/`, `vault/decisions/`, `vault/log.md`.

## В конце сессии

Автоматически, без подтверждения:

1. Append-запись в `vault/log.md`.
2. Обновить `vault/goals/today.md`.
3. `git add -A && git commit -m "сессия YYYY-MM-DD: <тип>" && git push 2>/dev/null || true`

Исключение: секреты в файлах → остановиться, предупредить, не коммить.

## Slug-конвенция

Глобально уникальные имена. Lowercase, кириллица допустима, разделитель `-`. Для дат — `YYYY-MM-DD_slug`. Перед созданием: `find . -name "<slug>.md"`.

## Что никогда не трогаешь

- `vault/decisions/` — не удаляешь. Пересмотр — новый файл.
- `vault/log.md` — только append.
- `CLAUDE.md`, `schema.md`, `.claude/` — зерно.
- `vault/profile/` и `north_star/stage/bottleneck` в проектах — только с «ок».
