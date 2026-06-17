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

## Сквозной нарратив (с 2026-06-18, сессия копирайта)

**«Аренда своего бизнеса / ваши клиенты — не ваши»** (выбран Даниилом). Стержень: владелец арендует доступ к собственным гостям у агрегатора; RestoGood возвращает клиентов, данные и деньги. По SB7: владелец — герой, RestoGood — проводник. Тон — **уверенно-дерзкий** (бьём по системе, не ноем; агрегаторы по имени не называем — юр.риск). Hero H1 = «Ваши клиенты — не ваши». Фреймворки и канон — в [[selling-landing-pages]].

## Структура секций (порядок после переработки 2026-06-18, 2 итерации)

Карты-стек (`StackSection`): наезд+скругления у всех, pin (sticky) только на Hero, на мобиле pin off. **Proof-слой (Testimonials + LiveStats) перенесён ВЫШЕ цены** — канон «confidence → перед action». Чередование D/L стало идеальным (раньше Packages+LiveStats шли двумя тёмными подряд).

| # | Секция | Фон | Особенности |
|---|---|---|---|
| 0 | Hero | bg-dark + glow | H1 «Ваши клиенты — не ваши», подзаг про аренду гостя |
| 1 | Problem | bg-light | «Вы арендуете собственный бизнес»: деньги→данные→контроль (3 карточки), мостик |
| 2 | Solution | bg-dark | «Один раз — и клиенты ваши», фичи + база клиентов, MockAdminPanel, iiko/r_keeper (НЕ удалять) |
| 3 | HowItWorks | bg-light | 4 шага (Plan по SB7) |
| 4 | WhyUs | bg-dark | отстройка «Сделаю сам выходит дороже» (возражение до цены) |
| 5 | Testimonials | bg-light | **поднят сюда** — 1 отзыв (mock Kavi) |
| 6 | LiveStats | bg-dark | **поднят сюда** — лайв-счётчик (цифры mock, оставлены по решению Даниила) |
| 7 | RoiCalculator | bg-light | выгода до цены, PDF download |
| 8 | Packages | bg-dark | «Сколько это стоит», якорь «дешевле месяца комиссии» |
| — | FAQ | bg-light | flat-tail; первый вопрос «Чьи клиенты и данные» (бьёт в нарратив) |
| — | Footer | bg-dark | CTA «Пора вернуть себе своих клиентов» + контакты |

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
