# RestoGood Landing

**Slug:** restogood-landing  
**Статус:** в работе (лендинг готов локально, деплой не делали)  
**Директория:** `~/coding/restogood-landing/`  
**Дата начала:** 2026-06-08

---

## Что это

Лендинг продукта **RestoGood** — система онлайн-заказов для ресторанов, которую Даниил продаёт ресторанам под ключ (разово, не SaaS пока). Лендинг нужен для привлечения клиентов и генерации лидов через ROI-калькулятор + PDF-КП.

**Бизнес-модель:** разовое внедрение. Три пакета: Эконом (49 900), Оптимум (89 900), Премиум (149 900). Возможный переход в SaaS в будущем.

**Целевая аудитория:** владельцы и управляющие МСБ-ресторанов, платящие комиссию агрегаторам (Яндекс.Еда, Delivery Club и др.).

---

## Стек

- **Next.js 16** App Router, статический export
- **Tailwind v4** — конфиг в `app/globals.css @theme inline`, НЕ в `tailwind.config.ts`
- **TypeScript** strict mode
- **Framer Motion** — animated mock UI (MockOrderDashboard, MockAdminPanel)
- **@react-pdf/renderer** — PDF-генерация на клиенте
- **lucide-react** — иконки (заменены все эмодзи)
- **Vitest** — тесты ROI-логики

---

## Design System

**Направление (с 2026-06-18):** «дерзкий + аппетитный» — тёмная база + оранжевый герой, крупная `font-black` типографика, карты-стек. Референс — it-one.ru. Детали и уроки — в memory [[project-restogood-design]].

CSS-переменные в `globals.css` (актуально):
- `--color-dark: #111110` → `bg-dark`, `text-dark` (был #0B0F19 — синил, конфликтовал с оранжевым)
- `--color-accent: #FF4D00` → `bg-accent`, `text-accent`, `border-accent`
- `--color-light: #F6F3EE` → `bg-light`
- `--color-surface: #1C1B19` → `bg-surface`
- `--color-muted: #78716C` → `text-muted`
- Шрифт: **Onest** (Google Fonts, кириллица, `variable: '--font-onest'`)

---

## Структура секций (порядок после переработки 2026-06-18)

Карты-стек (`StackSection`): наезд+скругления у всех, pin (sticky) только на Hero, на мобиле pin off.

| Секция | Фон | Особенности |
|---|---|---|
| Navbar | full-width, dark при скролле | вогнутые углы снизу (inner-radius mask) |
| Hero | bg-dark + оранжевый glow | огромный h1, кнопки pill+arrow, trust-strip (без анимации зачёркивания) |
| Problem | bg-light | боль в деньгах: 84 000 ₽, мостик-инсайт |
| Solution | bg-dark | фичи + MockAdminPanel, инфа про iiko/r_keeper (НЕ удалять) |
| HowItWorks | bg-light | 4 шага |
| **WhyUs** | bg-dark | НОВАЯ: отстройка «Сделаю сам выходит дороже» |
| RoiCalculator | bg-light | **идёт ПЕРЕД Packages** (выгода до цены), PDF download |
| Packages | bg-dark | «Сколько это стоит», якорь на месяц комиссии |
| LiveStats | bg-dark | лайв-счётчик |
| Testimonials | bg-light | 1 отзыв (mock Kavi) |
| FAQ | bg-light | продающие возражения первыми + технические |
| Footer | bg-dark | CTA «Готовы оставлять 28% себе?» + контакты |

---

## ROI-калькулятор

**Формула:**
```
shiftRate          = % заказов, которые уйдут с агрегаторов на свой сайт (0.0–1.0)
aggregatorSavings  = revenue × (commission/100) × shiftRate
staffSavings       = phoneOrders × 3 × (500/60)    # 3 мин × 500₽/ч
savingsPerMonth    = aggregatorSavings + staffSavings
savingsPerYear     = savingsPerMonth × 12
aggregatorAnnualLoss = revenue × (commission/100) × 12  # ПОЛНАЯ текущая комиссия, без shiftRate
payback(pkg)       = ceil(pkg.price / savingsPerMonth)
```

**shiftRate по пакетам (default):**
- Эконом: 40%
- Оптимум: 65%
- Премиум: 85%

`shiftRateTouched` флаг: если пользователь вручную двигал слайдер — не перезаписывать при смене пакета.

**Тесты:** 12 тестов в `lib/roi.test.ts`, Vitest.

---

## PDF-КП

- `components/KpPdf.tsx` → `KpPdfDownloadButton` (динамический импорт `ssr: false`)
- Шрифт: **Roboto** (полная версия с кириллицей), локально в `public/fonts/` (504KB)
- Загрузка: pre-fetch blob → createObjectURL → Font.register → pdf() → download
- `fontFamily: 'Roboto'` на обоих Page стилях (coverPage + page) — иначе кириллица ломается на обложке
- 3 страницы: Обложка / ROI+Пакеты / Контакты
- Скачивается как `restogood-kp-{название}.pdf`

---

## Важные технические нюансы

1. **Tailwind v4**: `tailwind.config.ts` — мёртвый файл. Все токены → `@theme inline {}` в globals.css
2. **PDF Cyrillic**: шрифт должен быть **полный TTF** (504KB), не subset (36KB). URL `KFOmCnqEu92Fr1Mu4mxP.ttf` от Google Fonts = латинский subset, без кириллицы. Взяли с GitHub googlefonts/roboto
3. **aggregatorAnnualLoss**: должен быть полная текущая комиссия без умножения на shiftRate — иначе строка «сейчас отдаёте агрегатору» будет занижена
4. **Font.register в PDF**: вызывать внутри handleDownload (не на уровне модуля) после blob pre-fetch

---

## Текущий статус

- Лендинг готов локально: `http://localhost:3000`
- Деплой на Vercel — не делали (убрали из задач)
- Отзывы — placeholder (Kavi), нужны реальные
- Логотип — нет, используется текст «RestoGood»
- Контакты — placeholder (@restogood, hello@restogood.ru)
- Цены пакетов — placeholder, уточнить
- Домен restogood.ru — не куплен (в config/site.ts)

---

## north_star

Лендинг конвертирует владельца ресторана в лид через ROI-калькулятор. CTA → скачать КП → Даниил звонит/пишет.

## bottleneck

Нет реального трафика и реальных отзывов. Нужен деплой + первые клиенты, которые дадут feedback по конверсии.
