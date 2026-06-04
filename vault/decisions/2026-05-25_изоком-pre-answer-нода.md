---
date: 2026-05-25
project: изоком
slug: изоком-pre-answer-нода
status: принято
---

# Решение: universal pre_answer нода в агенте Изоком

Принято решение добавить ноду `pre_answer` как универсальное RAG-звено после роутера.

## Суть

`general_response` удаляется. Вместо неё — `pre_answer` с RAG по обеим коллекциям (products + normatives).

## Новый граф

```
router(engineering)  → pre_answer → completeness_check → product_selection → ...
router(general)      → pre_answer → END
router(escalation)   → escalation_response → ...
```

## Что решает

1. **Баг роутера**: engineering-сообщения с прямыми вопросами (ГОСТ, КИС, маркировка) теряли вопросы в completeness_check — теперь pre_answer отвечает на них перед проверкой полноты.
2. **Недоработка general_response**: текущая нода без RAG, отвечала из параметрической памяти LLM — что неприемлемо для ИЗОКОМ-специфики.

## Альтернативы, отклонённые

- Патч prompt'а completeness_check — нет RAG, низкое качество
- Multi-intent routing (intents: list) — 2^3 комбинации, взрывная сложность
- `pre_answer` только для engineering + отдельный патч general_response — дублирование логики, вариант B чище

## Связи

[[изоком]], [[2026-05-22_изоком-контекст-фикс-ноды]]
