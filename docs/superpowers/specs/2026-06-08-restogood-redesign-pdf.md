# RestoGood — Редизайн + PDF-скачивание

**Дата:** 2026-06-08  
**Статус:** утверждён  
**Проект:** ~/coding/restogood-landing/

---

## Цель

Полный визуальный редизайн лендинга: новые цвета, шрифт, копирайтинг. Починить PDF-генерацию: кнопка «Скачать КП» должна скачивать файл напрямую без диалога печати.

---

## 1. Design System

### Цвета

```css
--color-bg-dark:    #0B0F19   /* hero, тёмные секции, footer */
--color-accent:     #FF4D00   /* CTA, акценты, ключевые цифры */
--color-bg-light:   #F5F5F0   /* светлые секции */
--color-text-dark:  #0B0F19   /* текст на светлом */
--color-text-light: #FFFFFF   /* текст на тёмном */
--color-muted:      #6B7280   /* второстепенный текст */
--color-surface:    #131929   /* карточки на тёмном фоне */
```

Обновить в `app/globals.css` блок `@theme inline`.

### Шрифт

**Onest** (Google Fonts, кириллица). Заменить Geist в `app/layout.tsx`:

```typescript
import { Onest } from 'next/font/google'
const onest = Onest({ subsets: ['latin', 'cyrillic'], variable: '--font-onest' })
```

В globals.css: `--font-sans: var(--font-onest), system-ui, sans-serif;`

---

## 2. Типографическая шкала

| Роль | Размер | Вес |
|---|---|---|
| Hero headline | 72–96px (text-7xl/text-8xl) | 800 (font-extrabold) |
| Section h2 | 40–48px (text-4xl/text-5xl) | 700 |
| Card h3 | 20–24px | 700 |
| Body | 16–18px | 400 |
| Caption | 13–14px | 400 |

Больше воздуха: padding секций `py-24` вместо `py-20`.

---

## 3. Секции — изменения

### Navbar
- Без изменений в структуре
- Цвет логотипа: белый на тёмном hero, slate на светлых секциях (уже работает через scroll)

### Hero
- Фон: `#0B0F19` + subtle radial gradient `from-[#1a0a00] via-[#0B0F19]` в левом нижнем углу (тепло от акцента)
- H1: **«Хватит отдавать 28% агрегаторам.»** — слово «28%» в цвете акцента `#FF4D00`
- Subtitle: «Собственный сайт заказов для ресторана. За 5–10 дней. Навсегда.»
- CTA primary: «Рассчитать окупаемость» (bg-accent)
- CTA secondary: «Узнать подробнее» (border, белый текст)

### Problem
- Фон: `#F5F5F0`
- H2: **«Сколько вы теряете прямо сейчас»**
- Карточки: белые, крупная иконка, bold заголовок

### Solution
- Фон: `#0B0F19`
- H2: **«Один раз — и заказы ваши.»**
- Фич-карточки: glassmorphism (bg-white/5, backdrop-blur, border border-white/10)

### HowItWorks
- Фон: `#F5F5F0`
- H2: «Как это работает» (без изменений)
- Номера шагов: крупный цветной `#FF4D00`

### Packages
- Фон: `#0B0F19`
- Карточки: glassmorphism (bg-white/5, border border-white/10)
- Рекомендованный (Оптимум): border-2 border-accent, bg с gradient `from-[#FF4D00]/20 to-transparent`
- Бейдж: «Популярный» красный

### ROI Calculator
- Фон: `#F5F5F0`
- H2: **«Посчитайте, сколько вы вернёте»**
- Форма: белые карточки, оранжевые слайдеры
- Добавить слайдер «% заказов через свой сайт» (см. раздел 6)
- Кнопка PDF: «Скачать КП» → скачивает файл напрямую

### Testimonials
- Фон: `#F5F5F0`
- Без кардинальных изменений — увеличить шрифт цитаты

### FAQ
- Фон: `#0B0F19`
- Аккордеон на тёмном фоне (border-white/10)
- H2 белый

### Footer
- Фон: `#0B0F19`
- «Готовы уйти от агрегаторов?» → без изменений (уже хорошо)

---

## 4. Обновлённый копирайтинг

| Секция | Старый заголовок | Новый заголовок |
|---|---|---|
| Hero h1 | «Ваши клиенты заказывают напрямую...» | **«Хватит отдавать 28% агрегаторам.»** |
| Hero sub | «Собственный сайт заказов...» | «За 5–10 дней — своя платформа заказов. Навсегда без комиссий.» |
| Problem h2 | «Почему это нельзя игнорировать» | **«Сколько вы теряете прямо сейчас»** |
| Solution h2 | «RestoGood — ваш собственный канал» | **«Один раз — и заказы ваши.»** |
| Solution sub | «Готовое решение: ресторан получает...» | «Полная платформа заказов под ваш бренд. Никаких ежемесячных платежей.» |
| Packages h2 | «Пакеты» | **«Выберите свой пакет»** |
| Packages sub | «Цены фиксированные...» | «Платите один раз. Пользуетесь всегда.» |
| Calculator h2 | «Рассчитайте окупаемость...» | **«Посчитайте, сколько вы вернёте»** |
| Calculator sub | «Введите данные...» | «Введите данные вашего ресторана — покажем ROI и сформируем КП.» |

---

## 6. Обновлённая формула ROI

### Проблема текущей формулы

`экономия_месяц = оборот × (комиссия / 100)` предполагает, что 100% заказов с агрегаторов мгновенно перейдут на собственный сайт. Это нереалистично и снижает доверие к цифрам.

### Новый параметр: shift_rate

**Что такое:** доля агрегаторных заказов, которые ресторан ожидает перевести на прямой сайт.

**Слайдер в калькуляторе:** «Ожидаемый % заказов через свой сайт», диапазон 10–100%, шаг 5%.

**Дефолт зависит от выбранного пакета:**

| Пакет | Дефолт shift_rate | Обоснование |
|---|---|---|
| Эконом | 40% | Базовый UX, ограниченный функционал |
| Оптимум | 65% | Полный бренд, хорошая конверсия |
| Премиум | 85% | Лучший UX, интеграции, максимум конверсии |

Пользователь может менять слайдер вручную — дефолт только начальное значение.

### Обновлённые формулы (`lib/roi.ts`)

```typescript
// Новое поле в RoiInputs:
shiftRate: number  // 0.1 – 1.0 (доля, не %)

// Обновлённый расчёт:
const aggregatorSavings = monthlyRevenue * (commissionRate / 100) * shiftRate
const staffSavings = phoneOrders * 3 * (500 / 60)
const totalMonthly = aggregatorSavings + staffSavings
const totalYearly = totalMonthly * 12
const paybackMonths = (packagePrice: number) => Math.ceil(packagePrice / totalMonthly)
```

### Дефолты по пакету в `components/sections/RoiCalculator.tsx`

```typescript
const DEFAULT_SHIFT_BY_PACKAGE = {
  econom:  0.40,
  optimum: 0.65,
  premium: 0.85,
}
```

При смене пакета (radio/tabs в калькуляторе) — обновить sliftRate до дефолта пакета, **если пользователь не трогал слайдер вручную** (флаг `shiftRateTouched`).

### Обновить тесты (`lib/roi.test.ts`)

- Существующие тесты: добавить `shiftRate` в `RoiInputs`
- Новые тесты:
  - `shiftRate=1.0` → результат совпадает с текущей логикой (regression)
  - `shiftRate=0.5` → экономия вдвое меньше
  - `shiftRate=0.0` → только staffSavings (агрегаторные 0)

### Файлы

- `lib/roi.ts` — добавить `shiftRate` в `RoiInputs`, обновить `calculateRoi()`
- `lib/roi.test.ts` — обновить + добавить тесты
- `components/sections/RoiCalculator.tsx` — слайдер + дефолты по пакету + `shiftRateTouched`
- `config/packages.ts` — добавить поле `defaultShiftRate: number` в тип `Package`

---

## 5. PDF — Fix @react-pdf/renderer

### Проблема оригинальной реализации

1. Шрифт Roboto грузился с `fonts.gstatic.com` — мог не загрузиться до генерации, что ломало Cyrillic
2. Сложная вложенная верстка с `StyleSheet.create` → плохой layout в PDF
3. Тип `any` в `pdf()` вызове — признак нестабильного кода

### Решение: локальный шрифт + упрощённая верстка

**Шрифт — локально:**
- Скачать `Onest-Regular.ttf` и `Onest-Bold.ttf` в `public/fonts/`
- Регистрировать через `Font.register({ src: '/fonts/Onest-Regular.ttf' })` — синхронная загрузка, без CDN

**Верстка PDF:**
- Плоская структура: минимум вложенных View
- Фиксированные размеры там где нужно, не `flex` повсюду
- 3 страницы (обложка, расчёт + пакеты, контакты)

**Флоу (без изменений):**
1. Пользователь заполняет калькулятор
2. Нажимает «Скачать КП»
3. `pdf(<KpDocument />).toBlob()` → `URL.createObjectURL()` → `a.click()`
4. Файл скачивается напрямую как `restogood-kp-[название].pdf`

### Файлы

- `public/fonts/Onest-Regular.ttf` — добавить
- `public/fonts/Onest-Bold.ttf` — добавить
- `components/KpPdf.tsx` — переписать: локальный шрифт, упрощённый layout, убрать `any`
- `app/kp/` — не создаём (не нужно)
- `@react-pdf/renderer` — остаётся в зависимостях

### Структура PDF (3 страницы)

**Страница 1: Обложка**
- Тёмный фон `#0B0F19`
- Логотип «RestoGood» крупно
- «Коммерческое предложение»
- «Для: [название]» оранжевым
- Дата

**Страница 2: Расчёт + Пакеты**
- Секция «Ваш расчёт»: таблица оборот/комиссия/экономия/год/сравнение
- Секция «Пакеты»: три строки с ценой и сроком окупаемости, рекомендованный выделен

**Страница 3: Контакты**
- «Следующий шаг» — текст
- Telegram, WhatsApp, Email
- «Подготовлено для: [имя/телефон]» если заполнено

---

## Файлы которые меняются

| Файл | Действие |
|---|---|
| `app/globals.css` | Новые CSS-переменные, Onest font var |
| `app/layout.tsx` | Заменить Geist → Onest |
| `lib/roi.ts` | Добавить `shiftRate` в `RoiInputs`, обновить `calculateRoi()` |
| `lib/roi.test.ts` | Обновить тесты + новые для shiftRate |
| `config/packages.ts` | Добавить поле `defaultShiftRate` в тип `Package` |
| `components/sections/Hero.tsx` | Новый копи, цвета, типографика |
| `components/sections/Problem.tsx` | Новый заголовок, цвета |
| `components/sections/Solution.tsx` | Новый копи, glassmorphism карточки |
| `components/sections/HowItWorks.tsx` | Цвета номеров |
| `components/sections/Packages.tsx` | Glassmorphism, gradient рекомендованный |
| `components/sections/RoiCalculator.tsx` | Новый копи, слайдер shift_rate, дефолты по пакету |
| `components/sections/Testimonials.tsx` | Размер текста |
| `components/sections/Faq.tsx` | Тёмный фон, белый текст |
| `components/sections/Footer.tsx` | Без изменений |
| `components/Navbar.tsx` | Без изменений |
| `components/KpPdf.tsx` | Переписать: локальный шрифт, упрощённый layout |
| `public/fonts/Onest-Regular.ttf` | Добавить |
| `public/fonts/Onest-Bold.ttf` | Добавить |

---

## Вне скоупа

- Mock компоненты (MockOrderDashboard, MockAdminPanel) — не трогаем
- Логика ROI — не трогаем
- Config файлы — не трогаем
- SEO/sitemap — не трогаем
