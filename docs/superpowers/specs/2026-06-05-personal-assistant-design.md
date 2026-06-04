# Личный ассистент — design doc

**Дата:** 2026-06-05
**Расположение:** `/home/pensioner/coding/my-projcets-private`

## Цель

Персональный AI-ассистент в Claude Code с памятью о проектах и контексте между сессиями. Решает главную боль: при переполнении контекста не нужно объяснять всё заново.

## Архитектура

Один каталог, открывается через `claude`. Никакого бэкенда, никаких сервисов.

```
my-projcets-private/
├── CLAUDE.md              # правила + что грузить при старте
├── schema.md              # форматы файлов памяти
├── vault/
│   ├── profile/
│   │   ├── about.md       # профиль: имя, предпочтения, стиль
│   │   └── USER.md
│   ├── project/
│   │   └── index.md       # список проектов + карточки
│   ├── goals/
│   │   ├── today.md
│   │   └── week.md
│   ├── decisions/         # одно решение = один файл
│   ├── notes/             # атомарные заметки, идеи
│   ├── tasks/
│   │   ├── backlog.md
│   │   └── in_progress.md
│   └── log.md             # лог сессий
└── .claude/
    └── commands/          # slash-команды
```

## Поведение при старте каждой сессии

1. Читает `vault/profile/about.md` — кто пользователь, предпочтения
2. Читает `vault/project/index.md` + активный проект (если был)
3. Читает последние записи `vault/log.md`
4. Приветствует по имени, напоминает где остановились

## Slash-команды

| Команда | Действие |
|---|---|
| `/проект [имя]` | Загружает карточку проекта, делает активным |
| `/сегодня` | `vault/goals/today.md` + активная задача |
| `/помнишь [тема]` | Grep по vault/notes, vault/decisions, vault/log |
| `/идеи` | Все бизнес-идеи и гипотезы из vault/notes |
| `/решения` | Последние 5 из vault/decisions |

## Правила записи памяти

**Сам без спроса:** `vault/log.md`, `vault/notes/`, `vault/decisions/`, `vault/tasks/`

**С подтверждением:** `vault/profile/`, `vault/project/` (поля north_star, stage, bottleneck)

**Никогда не трогает:** `CLAUDE.md`, `schema.md`, `.claude/`

## Тон

Деловой, партнёрский. Без «Конечно!», «Отлично!». Короткие ответы. Без эмодзи.

## Установка

Источник контекста — существующий `bb-private/vault/`. Процесс:

1. Копируем `bb-private/vault/` → в текущую директорию
2. Удаляем BBA-специфичные части: `vault/tasks/skills.md`, всё связанное с MCP/командой
3. Кладём новый `CLAUDE.md` (без BBA MCP, без командной части)
4. Кладём `schema.md` и slash-команды в `.claude/commands/`
5. `git init && git add -A && git commit -m "init: personal assistant"`

## Что берём из bb-private

- `vault/profile/` — полностью
- `vault/project/` — полностью
- `vault/decisions/` — полностью
- `vault/notes/` — полностью
- `vault/goals/` — полностью
- `vault/log.md` — последние 2 недели
- `vault/insights/` — полностью

## Что НЕ берём

- BBA MCP-подключение (`.mcp.json`)
- Командные slash-команды (`/команда`, `/финансы`, `/протокол`, `/бриф`)
- `vault/tasks/skills.md`
- `raw_llm/`
- Хуки дедукции (reconcile agent, deduction_inject.sh) — можно добавить позже
