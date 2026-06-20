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

## Структура секций (фон — «акты по смыслу» с 2026-06-18, см. [[2026-06-18_restogood-fon-akty]])

Карты-стек (`StackSection`): наезд+скругления у всех. Фон сгруппирован в **5 актов** (4 перехода вместо 10 — Даниилу рябило от строгого D/L). **Proof-слой (Testimonials + LiveStats) выше цены** — канон «confidence → перед action». **pin (sticky «перелистывание») теперь на стыках актов** — cards 0,1,4,7, только desktop, на мобиле off.

| # | Секция | Фон | Акт | Особенности |
|---|---|---|---|---|
| 0 | Hero | bg-dark + glow | 1 хук · **pin** | H1 «Ваши клиенты — не ваши»; мобильный 3D-скрим снизу (читаемость стат-строки) |
| 1 | Problem | bg-light | 2 боль · **pin** | «Вы арендуете собственный бизнес»: деньги→данные→контроль (3 карточки), мостик |
| 2 | Solution | bg-dark | 3 продукт | «Один раз — и клиенты ваши», фичи, MockAdminPanel, iiko/r_keeper (НЕ удалять) |
| 3 | HowItWorks | **bg-surface** | 3 продукт | 4 шага (Plan по SB7); тёмный, тон surface = лёгкий сдвиг внутри акта |
| 4 | WhyUs | bg-dark | 3 продукт · **pin** | «Сделаю сам выходит дороже» (возражение до цены); hover:bg-surface на ячейках |
| 5 | Testimonials | bg-light | 4 пруф | 1 отзыв (mock Kavi) |
| 6 | LiveStats | **bg-light** | 4 пруф | лайв-счётчик; **стал светлым** (белые ячейки на cream, дот emerald-500) |
| 7 | RoiCalculator | bg-light | 4 пруф · **pin** | выгода до цены, PDF download |
| 8 | Packages | bg-dark | 5 цена | «Сколько это стоит»; hover-подъём карт |
| — | FAQ | **bg-dark** | 5 цена | flat-tail; **стал тёмным** (совпал с tail); вопросы белые, hover→accent |
| — | Footer | bg-dark | 5 финал | CTA «Пора вернуть себе своих клиентов» + контакты |

## Полиш-слой (2026-06-18, сессия дизайна)

- **Фокус-стейты:** глобальный `:focus-visible` outline 2px accent в `globals.css` (не клипается overflow:hidden у кнопок); фокус-ринг слайдера — на thumb через box-shadow.
- **Reduced-motion:** `<MotionConfig reducedMotion="user">` в `page.tsx` (Framer) + media-query в `globals.css` (CSS-переходы).
- **Hover-микро:** кнопки `hover:-translate-y-0.5`; шаги HowItWorks — рост акцентной линии `w-6→w-12`; пакеты — подъём; WhyUs — `hover:bg-surface`.
- **Появление:** карты-сетки получили `scale 0.97→1` к opacity+y («оседание»).
- **Хедер:** вогнутые «нуки» `CORNER` 18→36 = радиус карт (`.stack-card` 36px).

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
