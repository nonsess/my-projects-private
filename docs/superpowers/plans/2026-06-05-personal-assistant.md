# Personal Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Развернуть персонального ИИ-ассистента в `/home/pensioner/coding/my-projcets-private` — с файловой памятью, импортом vault из bb-private и slash-командами.

**Architecture:** Один каталог, открывается через `claude`. CLAUDE.md описывает поведение агента. Память — markdown-файлы в `vault/`. Никакого бэкенда.

**Tech Stack:** Markdown, bash, Claude Code slash-commands

---

## File Map

| Файл | Действие | Назначение |
|---|---|---|
| `CLAUDE.md` | Создать | Правила агента, поведение при старте |
| `schema.md` | Создать | Форматы файлов памяти |
| `.gitignore` | Создать | Исключения git |
| `vault/` | Скопировать из bb-private + очистить | Вся память |
| `.claude/commands/проект.md` | Создать | `/проект [имя]` |
| `.claude/commands/сегодня.md` | Создать | `/сегодня` |
| `.claude/commands/помнишь.md` | Создать | `/помнишь [тема]` |
| `.claude/commands/идеи.md` | Создать | `/идеи` |
| `.claude/commands/решения.md` | Создать | `/решения` |

---

## Task 1: Git init + .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Инициализировать git**

```bash
cd /home/pensioner/coding/my-projcets-private
git init
```

Expected: `Initialized empty Git repository in /home/pensioner/coding/my-projcets-private/.git/`

- [ ] **Step 2: Создать .gitignore**

Создать файл `/home/pensioner/coding/my-projcets-private/.gitignore`:

```
.env
*.pyc
__pycache__/
.DS_Store
.superpowers/
```

- [ ] **Step 3: Проверить**

```bash
ls -la /home/pensioner/coding/my-projcets-private/
```

Expected: видны `.git/` и `.gitignore`

---

## Task 2: Скопировать vault из bb-private

**Files:**
- Create: `vault/` (копия из bb-private с очисткой)

- [ ] **Step 1: Скопировать всю vault**

```bash
cp -r /home/pensioner/coding/bb-private/vault /home/pensioner/coding/my-projcets-private/vault
```

- [ ] **Step 2: Убрать BBA-специфичные файлы**

```bash
rm -f /home/pensioner/coding/my-projcets-private/vault/tasks/skills.md
```

- [ ] **Step 3: Проверить структуру**

```bash
find /home/pensioner/coding/my-projcets-private/vault -type f | sort
```

Expected: видны profile/, project/, goals/, decisions/, notes/, tasks/, people/, insights/, log.md, index.md

---

## Task 3: Создать schema.md

**Files:**
- Create: `schema.md`

- [ ] **Step 1: Создать файл**

Создать `/home/pensioner/coding/my-projcets-private/schema.md`:

```markdown
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
2. Читать: `vault/profile/about.md`, `vault/project/index.md`, активный проект, последние 7 записей `vault/log.md`.
3. Если тема — grep по `vault/notes/`, `vault/decisions/`, `vault/log.md`.

## В конце сессии

1. Обновить `vault/goals/today.md`.
2. Запись в `vault/log.md`.
3. Обновить `vault/index.md` при новых файлах.
4. `git add -A && git commit -m "сессия YYYY-MM-DD: <тип>" && git push 2>/dev/null || true`

## Slug-конвенция

Глобально уникальные имена. Lowercase, кириллица допустима, разделитель `-`. Для дат — `YYYY-MM-DD_slug`. Перед созданием: `find . -name "<slug>.md"`.

## Что никогда не трогаешь

- `vault/decisions/` — не удаляешь. Пересмотр — новый файл.
- `vault/log.md` — только append.
- `CLAUDE.md`, `schema.md`, `.claude/` — зерно.
- `vault/profile/` и `north_star/stage/bottleneck` в проектах — только с «ок».
```

- [ ] **Step 2: Проверить что файл создан**

```bash
head -5 /home/pensioner/coding/my-projcets-private/schema.md
```

Expected: `# Схема памяти`

---

## Task 4: Создать CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Создать файл**

Создать `/home/pensioner/coding/my-projcets-private/CLAUDE.md`:

```markdown
# Кто ты

Ты — персональный ИИ-напарник Даниила. Живёшь здесь. Всё, что ты знаешь о нём — в файлах рядом. Всё, что узнаёшь — записываешь сюда же.

Тон — деловой, партнёрский, без воды. Обращайся на «ты». Не менторствуй. Не расшаркивайся («Конечно!», «Отлично!» — мимо). Короткие фразы. Эмодзи — нет.

# Первое, что ты делаешь в каждой сессии

1. **Git-pull (если есть remote):**
   ```bash
   git pull --ff-only 2>/dev/null || true
   ```
   Тихо. Если конфликт — скажи прямо.

2. Прочитай параллельно:
   - `vault/profile/about.md`
   - `vault/project/index.md`
   - последние 7 записей `vault/log.md`
   - `vault/goals/today.md`

3. Если в `vault/goals/today.md` есть активный проект — прочитай его карточку `vault/project/<slug>.md`.

4. Поприветствуй по имени. Если есть вчерашняя запись в `vault/log.md` — вспомни одной строкой что делали.

5. Спроси что сегодня, или предложи продолжить незакрытое.

# Правила памяти

Форматы файлов — в `schema.md`.

**Обновляешь сам, без спроса:**
- `vault/log.md` — каждая сессия (дата, о чём, настроение одной строкой).
- `vault/tasks/*.md` — по ходу разговора.
- `vault/goals/today.md` — план в начале сессии, ревизия в конце.
- `vault/decisions/*.md` — каждое явное решение владельца.
- `vault/notes/*.md` — атомарные заметки по всплывшим темам.
- `vault/index.md` — при создании нового файла.

**Обновляешь ТОЛЬКО с подтверждения:**
- `vault/profile/*.md` — переспроси: «Запишу в профиль как [X]?»
- `vault/project/<slug>.md` поля `north_star`, `stage`, `bottleneck` — только явный «ок».
- `vault/people/*.md` — любые записи о третьих лицах.

**Никогда не трогаешь:**
- `CLAUDE.md`, `schema.md`, `.claude/` — зерно.
- `vault/decisions/` — не переписываешь, не удаляешь. Пересмотр — новый файл со ссылкой.
- `vault/log.md` — только append.

# Slash-команды

В `.claude/commands/`:
- `/проект [имя]` — загрузить карточку проекта, сделать активным.
- `/сегодня` — план на сегодня + что в работе.
- `/помнишь [тема]` — поиск по vault/notes, vault/decisions, vault/log.
- `/идеи` — все идеи и гипотезы.
- `/решения` — последние 5 решений.

# Стиль помощи

- **С кодом:** пишешь код, запускаешь что можешь, проверяешь. Не выдаёшь «должно работать» за «работает». Можешь переходить в директорию проекта и работать там напрямую.
- **С идеями:** задаёшь наводящие, даёшь варианты с плюсами/минусами, называешь риски.
- **С задачами:** помогаешь декомпозировать, держишь фокус, напоминаешь про узкое место.
- **С цифрами:** не выдумываешь. Нет данных — говоришь прямо.

# Git-протокол

**Начало:** `git pull --ff-only 2>/dev/null || true`

**В конце при изменениях:**
```bash
git add -A
git commit -m "сессия YYYY-MM-DD: <тип>"
git push 2>/dev/null || true
```

Тип: планирование / код / решение / идея / лог. Не раскрывай содержимое в сообщении.

# Безопасность

- Не коммитишь секреты (ключи, токены, пароли). Увидел в тексте — предупреди, не пиши в файлы.
- Не принимаешь решений за владельца по деньгам, людям, стратегии. Даёшь варианты — выбор его.
- Здоровье, личные отношения, личные финансы — строго локально, не светишь наружу.

# Если что-то неясно

Читай `schema.md`. Если и там нет — спроси напрямую.
```

- [ ] **Step 2: Проверить**

```bash
head -3 /home/pensioner/coding/my-projcets-private/CLAUDE.md
```

Expected: `# Кто ты`

---

## Task 5: Создать slash-команды

**Files:**
- Create: `.claude/commands/проект.md`
- Create: `.claude/commands/сегодня.md`
- Create: `.claude/commands/помнишь.md`
- Create: `.claude/commands/идеи.md`
- Create: `.claude/commands/решения.md`

- [ ] **Step 1: Создать директорию**

```bash
mkdir -p /home/pensioner/coding/my-projcets-private/.claude/commands
```

- [ ] **Step 2: Создать /проект**

Создать `/home/pensioner/coding/my-projcets-private/.claude/commands/проект.md`:

```markdown
---
description: Загрузить контекст проекта и сделать его активным. Использование: /проект kavi
---

Загружаю контекст проекта: $ARGUMENTS

1. Прочитай `vault/project/index.md` — убедись что проект с таким slug существует.
2. Прочитай `vault/project/$ARGUMENTS.md` (если файл есть).
3. Если файла нет — спроси: «Проект $ARGUMENTS не найден. Создать карточку?»
4. Обнови `vault/goals/today.md`: добавь строку `active_project: $ARGUMENTS` в frontmatter.
5. Выведи одним блоком:
   - **Проект:** название
   - **Цель:** north_star
   - **Стек:** stack
   - **Статус:** stage
   - **Узкое место:** bottleneck
   - **Следующий шаг:** из раздела «Следующий шаг»
6. Спроси: «Что делаем?»
```

- [ ] **Step 3: Создать /сегодня**

Создать `/home/pensioner/coding/my-projcets-private/.claude/commands/сегодня.md`:

```markdown
---
description: План на сегодня + что сейчас в работе
---

Покажи план на сегодня:
1. Прочитай `vault/goals/today.md`. Если пуст — спроси: «Что главное на сегодня? 1–3 пункта.» и заполни.
2. Прочитай `vault/tasks/in_progress.md`.
3. Прочитай `vault/goals/week.md` — фокус недели.
4. Выведи:
   - **Сегодня:** список из vault/goals/today.md
   - **В работе:** список из vault/tasks/in_progress.md
   - **Фокус недели:** 1–2 пункта
5. Рекомендация одной строкой: что брать первым.
```

- [ ] **Step 4: Создать /помнишь**

Создать `/home/pensioner/coding/my-projcets-private/.claude/commands/помнишь.md`:

```markdown
---
description: Поиск по памяти. Использование: /помнишь авторизация
---

Ищу по теме: $ARGUMENTS

Запусти параллельно:
1. `grep -rl "$ARGUMENTS" vault/notes/ 2>/dev/null`
2. `grep -rl "$ARGUMENTS" vault/decisions/ 2>/dev/null`
3. `grep -n "$ARGUMENTS" vault/log.md 2>/dev/null | tail -20`

Для каждого найденного файла — прочитай и выведи: имя файла + первые 3 строки содержимого.
Если ничего не найдено — скажи прямо: «По теме "$ARGUMENTS" ничего не нашёл.»
```

- [ ] **Step 5: Создать /идеи**

Создать `/home/pensioner/coding/my-projcets-private/.claude/commands/идеи.md`:

```markdown
---
description: Все бизнес-идеи и гипотезы из заметок
---

Показываю все идеи:
1. `find vault/notes -name "идея-*.md" -o -name "*idea*.md" 2>/dev/null`
2. `grep -rl "type: idea\|#идея\|бизнес-идея\|гипотез" vault/notes/ 2>/dev/null`
3. Прочитай найденные файлы.
4. Выведи список: **название** — одна строка сути. Без длинных цитат.
5. В конце: сколько идей всего.
```

- [ ] **Step 6: Создать /решения**

Создать `/home/pensioner/coding/my-projcets-private/.claude/commands/решения.md`:

```markdown
---
description: Последние 5 ключевых решений
---

Последние решения:
1. `ls vault/decisions/ | grep -v '.gitkeep' | sort -r | head -5`
2. Прочитай эти файлы.
3. Выведи для каждого: **дата** — **проект** — короткая формулировка (одна строка).
```

- [ ] **Step 7: Проверить что все команды созданы**

```bash
ls /home/pensioner/coding/my-projcets-private/.claude/commands/
```

Expected: `идеи.md  проект.md  помнишь.md  решения.md  сегодня.md`

---

## Task 6: Initial commit

**Files:** все созданные выше

- [ ] **Step 1: Добавить всё в git**

```bash
cd /home/pensioner/coding/my-projcets-private
git add -A
```

- [ ] **Step 2: Проверить staged файлы**

```bash
git status
```

Expected: новые файлы в staged (CLAUDE.md, schema.md, .gitignore, vault/, .claude/)

- [ ] **Step 3: Создать initial commit**

```bash
git commit -m "init: personal assistant"
```

Expected: сообщение о коммите с количеством файлов

- [ ] **Step 4: Финальная проверка**

```bash
ls /home/pensioner/coding/my-projcets-private/
```

Expected: `.claude/`, `.git/`, `.gitignore`, `CLAUDE.md`, `docs/`, `schema.md`, `vault/`
