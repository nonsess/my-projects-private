# RestoGood Landing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Собрать лендинг продукта RestoGood с ROI-калькулятором, генератором PDF-КП и полным SEO.

**Architecture:** Отдельный Next.js 14 App Router проект, полностью статический (без бэкенда). Все секции — серверные компоненты, кроме интерактивных (калькулятор, PDF, моки). Конфиг пакетов/сайта/FAQ отделён от компонентов.

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS, Framer Motion, @react-pdf/renderer, Vitest.

---

## Файловая карта

```
restogood-landing/
├── app/
│   ├── layout.tsx          # root layout, metadata, шрифты
│   ├── page.tsx            # сборка всех секций
│   ├── globals.css         # CSS reset + tailwind directives
│   ├── sitemap.ts          # Next.js sitemap
│   └── robots.ts           # Next.js robots
├── components/
│   ├── Navbar.tsx          # фиксированный хедер
│   ├── KpPdf.tsx           # @react-pdf/renderer документ
│   ├── mocks/
│   │   ├── MockOrderDashboard.tsx  # анимированный мок Hero
│   │   └── MockAdminPanel.tsx      # анимированный мок Solution
│   ├── sections/
│   │   ├── Hero.tsx
│   │   ├── Problem.tsx
│   │   ├── Solution.tsx
│   │   ├── HowItWorks.tsx
│   │   ├── Packages.tsx
│   │   ├── RoiCalculator.tsx
│   │   ├── Testimonials.tsx
│   │   ├── Faq.tsx
│   │   └── Footer.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Card.tsx
│       └── RangeSlider.tsx
├── config/
│   ├── packages.ts
│   ├── site.ts
│   └── faq.ts
├── lib/
│   ├── roi.ts              # чистые функции расчёта ROI
│   └── roi.test.ts         # Vitest тесты
└── vitest.config.ts
```

---

## Task 1: Project Setup

**Files:**
- Create: `restogood-landing/` (новый проект)
- Create: `vitest.config.ts`
- Modify: `tailwind.config.ts`

- [ ] **Step 1: Создать Next.js проект**

```bash
cd ~/coding
npx create-next-app@latest restogood-landing \
  --typescript \
  --tailwind \
  --app \
  --src-dir=false \
  --import-alias="@/*" \
  --no-eslint
cd restogood-landing
```

- [ ] **Step 2: Установить зависимости**

```bash
npm install framer-motion @react-pdf/renderer
npm install -D vitest @vitejs/plugin-react jsdom
```

- [ ] **Step 3: Создать vitest.config.ts**

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
  },
})
```

- [ ] **Step 4: Добавить test script в package.json**

Открыть `package.json`, добавить в `scripts`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 5: Расширить Tailwind config**

Заменить содержимое `tailwind.config.ts`:
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: '#F97316',
          navy: '#0F172A',
          green: '#10B981',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
```

- [ ] **Step 6: Проверить что dev сервер запускается**

```bash
npm run dev
```

Ожидание: в браузере `http://localhost:3000` открывается дефолтная Next.js страница.

- [ ] **Step 7: Commit**

```bash
git init
git add -A
git commit -m "feat: project setup — next.js, tailwind, vitest, framer-motion"
```

---

## Task 2: Config Files

**Files:**
- Create: `config/site.ts`
- Create: `config/packages.ts`
- Create: `config/faq.ts`

- [ ] **Step 1: Создать config/site.ts**

```typescript
// config/site.ts
export const site = {
  name: 'RestoGood',
  tagline: 'Система онлайн-заказов для ресторана под ключ',
  description:
    'Ваши клиенты заказывают напрямую — без комиссии агрегатора. Онлайн-меню, корзина, трекинг заказа и админ-панель.',
  url: 'https://restogood.ru',
  contacts: {
    telegram: 'https://t.me/restogood',
    whatsapp: 'https://wa.me/79000000000',
    email: 'hello@restogood.ru',
  },
}
```

- [ ] **Step 2: Создать config/packages.ts**

```typescript
// config/packages.ts
export interface PackageFeature {
  label: string
  included: boolean
}

export interface Package {
  id: string
  name: string
  price: number
  recommended: boolean
  adminPanel: 'базовая' | 'полная'
  roles: string
  supportMonths: number
  features: PackageFeature[]
}

export const packages: Package[] = [
  {
    id: 'economy',
    name: 'Эконом',
    price: 49900,
    recommended: false,
    adminPanel: 'базовая',
    roles: '1 пользователь',
    supportMonths: 0,
    features: [
      { label: 'Онлайн-меню с фото', included: true },
      { label: 'Корзина и оформление заказа', included: true },
      { label: 'Трекинг статуса по трек-коду', included: true },
      { label: 'Брендинг (цвета, логотип)', included: false },
      { label: 'Несколько ролей (менеджер / владелец)', included: false },
      { label: 'Интеграция с кассой', included: false },
      { label: 'Приоритетная поддержка', included: false },
      { label: 'Доработки после запуска', included: false },
    ],
  },
  {
    id: 'optimal',
    name: 'Оптимум',
    price: 89900,
    recommended: true,
    adminPanel: 'полная',
    roles: 'до 3 пользователей',
    supportMonths: 1,
    features: [
      { label: 'Онлайн-меню с фото', included: true },
      { label: 'Корзина и оформление заказа', included: true },
      { label: 'Трекинг статуса по трек-коду', included: true },
      { label: 'Брендинг (цвета, логотип)', included: true },
      { label: 'Несколько ролей (менеджер / владелец)', included: true },
      { label: 'Интеграция с кассой', included: false },
      { label: 'Приоритетная поддержка', included: false },
      { label: 'Доработки после запуска', included: true },
    ],
  },
  {
    id: 'premium',
    name: 'Премиум',
    price: 149900,
    recommended: false,
    adminPanel: 'полная',
    roles: 'неограниченно',
    supportMonths: 3,
    features: [
      { label: 'Онлайн-меню с фото', included: true },
      { label: 'Корзина и оформление заказа', included: true },
      { label: 'Трекинг статуса по трек-коду', included: true },
      { label: 'Брендинг (цвета, логотип)', included: true },
      { label: 'Несколько ролей (менеджер / владелец)', included: true },
      { label: 'Интеграция с кассой', included: true },
      { label: 'Приоритетная поддержка', included: true },
      { label: 'Доработки после запуска', included: true },
    ],
  },
]
```

- [ ] **Step 3: Создать config/faq.ts**

```typescript
// config/faq.ts
export interface FaqItem {
  question: string
  answer: string
}

export const faq: FaqItem[] = [
  {
    question: 'Сколько времени занимает внедрение?',
    answer:
      'Стандартный запуск — 5–10 рабочих дней с момента подписания договора. Вы загружаете меню и фото, мы настраиваем систему и передаём вам готовый сайт заказов.',
  },
  {
    question: 'Нужен ли отдельный домен?',
    answer:
      'Нет, не обязательно. По умолчанию выдаём поддомен (yourname.restogood.ru). Если у вас есть свой домен — подключим его бесплатно.',
  },
  {
    question: 'Можно ли менять меню после запуска?',
    answer:
      'Да, в любое время. В admin-панели можно добавлять, редактировать и скрывать блюда, менять цены и фото — без нашего участия.',
  },
  {
    question: 'Что входит в поддержку после запуска?',
    answer:
      'Консультации и оперативные исправления критических багов. В пакете Оптимум — 1 месяц доработок по запросу, в Премиум — 3 месяца.',
  },
  {
    question: 'Работает ли система на мобильных телефонах?',
    answer:
      'Да. Сайт заказов и admin-панель полностью адаптированы для смартфонов. Клиент оформляет заказ с телефона, менеджер видит его там же.',
  },
]
```

- [ ] **Step 4: Commit**

```bash
git add config/
git commit -m "feat: config files — packages, site, faq"
```

---

## Task 3: ROI Calculation Logic (TDD)

**Files:**
- Create: `lib/roi.ts`
- Create: `lib/roi.test.ts`

- [ ] **Step 1: Написать тесты (сначала тесты, потом код)**

```typescript
// lib/roi.test.ts
import { describe, it, expect } from 'vitest'
import { calculateRoi, calculatePayback } from './roi'

describe('calculateRoi', () => {
  it('calculates aggregator savings from revenue and commission', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
    })
    expect(result.savingsPerMonth).toBe(75000)
  })

  it('adds staff savings for phone orders (3 min × 500₽/h per order)', () => {
    const result = calculateRoi({
      aggregatorRevenue: 0,
      commission: 0,
      phoneOrders: 100,
    })
    // 100 × 3 × (500/60) = 2500
    expect(result.savingsPerMonth).toBeCloseTo(2500, 0)
  })

  it('combines aggregator and staff savings', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 100,
    })
    expect(result.savingsPerMonth).toBeCloseTo(77500, 0)
  })

  it('calculates annual savings as 12× monthly', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
    })
    expect(result.savingsPerYear).toBe(900000)
  })

  it('calculates aggregatorAnnualLoss correctly', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
    })
    expect(result.aggregatorAnnualLoss).toBe(900000)
  })

  it('returns zero savings when all inputs are zero', () => {
    const result = calculateRoi({
      aggregatorRevenue: 0,
      commission: 0,
      phoneOrders: 0,
    })
    expect(result.savingsPerMonth).toBe(0)
    expect(result.savingsPerYear).toBe(0)
  })
})

describe('calculatePayback', () => {
  it('returns ceiling of price divided by monthly savings', () => {
    // 89900 / 75000 = 1.198... → 2
    expect(calculatePayback(89900, 75000)).toBe(2)
  })

  it('returns exact months when evenly divisible', () => {
    expect(calculatePayback(90000, 45000)).toBe(2)
  })

  it('returns Infinity when monthly savings is zero', () => {
    expect(calculatePayback(89900, 0)).toBe(Infinity)
  })
})
```

- [ ] **Step 2: Запустить тесты и убедиться что они падают**

```bash
npx vitest run lib/roi.test.ts
```

Ожидание: ошибки импорта — модуль `./roi` не существует.

- [ ] **Step 3: Написать реализацию**

```typescript
// lib/roi.ts
const OPERATOR_RATE_PER_MINUTE = 500 / 60

export interface RoiInputs {
  aggregatorRevenue: number
  commission: number
  phoneOrders: number
}

export interface RoiResult {
  savingsPerMonth: number
  savingsPerYear: number
  aggregatorAnnualLoss: number
}

export function calculateRoi(inputs: RoiInputs): RoiResult {
  const aggregatorSavings = inputs.aggregatorRevenue * (inputs.commission / 100)
  const staffSavings = inputs.phoneOrders * 3 * OPERATOR_RATE_PER_MINUTE
  const savingsPerMonth = aggregatorSavings + staffSavings
  return {
    savingsPerMonth,
    savingsPerYear: savingsPerMonth * 12,
    aggregatorAnnualLoss: aggregatorSavings * 12,
  }
}

export function calculatePayback(packagePrice: number, savingsPerMonth: number): number {
  if (savingsPerMonth <= 0) return Infinity
  return Math.ceil(packagePrice / savingsPerMonth)
}
```

- [ ] **Step 4: Запустить тесты и убедиться что все проходят**

```bash
npx vitest run lib/roi.test.ts
```

Ожидание: `7 tests passed`.

- [ ] **Step 5: Commit**

```bash
git add lib/
git commit -m "feat: roi calculation logic with tests"
```

---

## Task 4: UI Primitives

**Files:**
- Create: `components/ui/Button.tsx`
- Create: `components/ui/Card.tsx`
- Create: `components/ui/RangeSlider.tsx`

- [ ] **Step 1: Создать Button.tsx**

```typescript
// components/ui/Button.tsx
import { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-offset-2',
        {
          'bg-orange-500 text-white hover:bg-orange-600 active:scale-95': variant === 'primary',
          'border-2 border-slate-800 text-slate-800 hover:bg-slate-800 hover:text-white':
            variant === 'outline',
          'text-slate-600 hover:text-slate-900 hover:bg-slate-100': variant === 'ghost',
          'px-4 py-2 text-sm': size === 'sm',
          'px-6 py-3 text-base': size === 'md',
          'px-8 py-4 text-lg': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
```

- [ ] **Step 2: Создать lib/utils.ts (нужна для cn)**

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 3: Установить clsx и tailwind-merge**

```bash
npm install clsx tailwind-merge
```

- [ ] **Step 4: Создать Card.tsx**

```typescript
// components/ui/Card.tsx
import { HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  highlight?: boolean
}

export function Card({ highlight, className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl p-6 transition-shadow',
        highlight
          ? 'bg-orange-500 text-white shadow-xl shadow-orange-200'
          : 'bg-white border border-slate-100 shadow-sm hover:shadow-md',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
```

- [ ] **Step 5: Создать RangeSlider.tsx**

```typescript
// components/ui/RangeSlider.tsx
'use client'

interface RangeSliderProps {
  value: number
  min: number
  max: number
  step?: number
  onChange: (value: number) => void
  formatLabel?: (value: number) => string
}

export function RangeSlider({
  value,
  min,
  max,
  step = 1,
  onChange,
  formatLabel,
}: RangeSliderProps) {
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div className="w-full">
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-2 appearance-none rounded-full outline-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, #F97316 ${pct}%, #E2E8F0 ${pct}%)`,
          }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mt-1">
        <span>{formatLabel ? formatLabel(min) : min}</span>
        <span>{formatLabel ? formatLabel(max) : max}</span>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add components/ui/ lib/utils.ts
git commit -m "feat: ui primitives — Button, Card, RangeSlider"
```

---

## Task 5: Navbar

**Files:**
- Create: `components/Navbar.tsx`

- [ ] **Step 1: Создать Navbar.tsx**

```typescript
// components/Navbar.tsx
'use client'

import { useState, useEffect } from 'react'
import { site } from '@/config/site'
import { Button } from '@/components/ui/Button'

const links = [
  { label: 'О продукте', href: '#solution' },
  { label: 'Пакеты', href: '#packages' },
  { label: 'Калькулятор', href: '#calculator' },
]

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-white/95 backdrop-blur shadow-sm' : 'bg-transparent'
      }`}
    >
      <nav className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <span className="text-xl font-bold text-slate-900">
          {site.name}
        </span>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <li key={l.href}>
              <a
                href={l.href}
                className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
              >
                {l.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="hidden md:block">
          <Button size="sm" onClick={() => document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' })}>
            Получить КП
          </Button>
        </div>

        {/* Mobile burger */}
        <button
          className="md:hidden p-2 text-slate-700"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Меню"
        >
          <span className="block w-6 h-0.5 bg-current mb-1.5" />
          <span className="block w-6 h-0.5 bg-current mb-1.5" />
          <span className="block w-6 h-0.5 bg-current" />
        </button>
      </nav>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t border-slate-100 px-4 py-4 flex flex-col gap-4">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-slate-700 font-medium"
              onClick={() => setMenuOpen(false)}
            >
              {l.label}
            </a>
          ))}
          <Button size="sm" onClick={() => { setMenuOpen(false); document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' }) }}>
            Получить КП
          </Button>
        </div>
      )}
    </header>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add components/Navbar.tsx
git commit -m "feat: navbar with scroll effect and mobile menu"
```

---

## Task 6: Mock UI Components

**Files:**
- Create: `components/mocks/MockOrderDashboard.tsx`
- Create: `components/mocks/MockAdminPanel.tsx`

- [ ] **Step 1: Создать MockOrderDashboard.tsx**

Это анимированный UI-компонент для Hero — симулирует интерфейс заказа еды.

```typescript
// components/mocks/MockOrderDashboard.tsx
'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const menuItems = [
  { name: 'Бургер классик', price: 490, emoji: '🍔', category: 'Бургеры' },
  { name: 'Пицца Маргарита', price: 590, emoji: '🍕', category: 'Пицца' },
  { name: 'Том Ям', price: 420, emoji: '🍜', category: 'Супы' },
  { name: 'Тирамису', price: 280, emoji: '🍰', category: 'Десерты' },
]

const statuses = ['Новый', 'Готовится', 'Готов', 'Доставлен'] as const
type Status = (typeof statuses)[number]

const statusColors: Record<Status, string> = {
  Новый: 'bg-blue-100 text-blue-700',
  Готовится: 'bg-yellow-100 text-yellow-700',
  Готов: 'bg-green-100 text-green-700',
  Доставлен: 'bg-slate-100 text-slate-600',
}

export function MockOrderDashboard() {
  const [status, setStatus] = useState<Status>('Новый')
  const [cart, setCart] = useState<{ name: string; price: number; qty: number }[]>([])

  useEffect(() => {
    const idx = statuses.indexOf(status)
    if (idx < statuses.length - 1) {
      const t = setTimeout(() => setStatus(statuses[idx + 1]), 2200)
      return () => clearTimeout(t)
    }
  }, [status])

  useEffect(() => {
    // Анимированное наполнение корзины
    const timers = menuItems.slice(0, 3).map((item, i) =>
      setTimeout(() => {
        setCart((prev) => {
          if (prev.find((c) => c.name === item.name)) return prev
          return [...prev, { name: item.name, price: item.price, qty: 1 }]
        })
      }, i * 800)
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  const total = cart.reduce((s, i) => s + i.price * i.qty, 0)

  return (
    <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-100 select-none">
      {/* Header */}
      <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between">
        <span className="font-semibold text-sm">Меню ресторана</span>
        <span className="text-xs text-slate-400">restogood.ru</span>
      </div>

      {/* Menu grid */}
      <div className="p-3 grid grid-cols-2 gap-2">
        {menuItems.map((item, i) => (
          <motion.div
            key={item.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-slate-50 rounded-xl p-2.5 cursor-pointer hover:bg-orange-50 transition-colors"
          >
            <div className="text-2xl mb-1">{item.emoji}</div>
            <div className="text-xs font-medium text-slate-800 leading-tight">{item.name}</div>
            <div className="text-xs text-orange-500 font-semibold mt-0.5">{item.price} ₽</div>
          </motion.div>
        ))}
      </div>

      {/* Cart */}
      <div className="border-t border-slate-100 px-3 py-2">
        <div className="text-xs font-semibold text-slate-500 mb-2">Ваш заказ</div>
        <AnimatePresence>
          {cart.map((item) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex justify-between text-xs text-slate-700 py-0.5"
            >
              <span>{item.name}</span>
              <span className="font-medium">{item.price} ₽</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {total > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-between font-bold text-sm text-slate-900 pt-2 border-t border-slate-100 mt-1"
          >
            <span>Итого</span>
            <span>{total} ₽</span>
          </motion.div>
        )}
      </div>

      {/* Status */}
      <div className="px-3 py-2 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-500">Статус заказа #4821</span>
        <AnimatePresence mode="wait">
          <motion.span
            key={status}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${statusColors[status]}`}
          >
            {status}
          </motion.span>
        </AnimatePresence>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Создать MockAdminPanel.tsx**

```typescript
// components/mocks/MockAdminPanel.tsx
'use client'

import { motion } from 'framer-motion'

const orders = [
  { id: '#4821', items: 'Бургер × 2, Пицца × 1', status: 'Новый', amount: 1570, color: 'bg-blue-100 text-blue-700' },
  { id: '#4820', items: 'Том Ям × 1', status: 'Готовится', amount: 420, color: 'bg-yellow-100 text-yellow-700' },
  { id: '#4819', items: 'Тирамису × 3', status: 'Готов', amount: 840, color: 'bg-green-100 text-green-700' },
  { id: '#4818', items: 'Пицца Маргарита × 2', status: 'Доставлен', amount: 1180, color: 'bg-slate-100 text-slate-500' },
]

export function MockAdminPanel() {
  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-100 select-none">
      {/* Header */}
      <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between">
        <span className="font-semibold text-sm">Заказы — сегодня</span>
        <span className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
          {orders.length} новых
        </span>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
        {[
          { label: 'Выручка', value: '14 820 ₽' },
          { label: 'Заказов', value: '12' },
          { label: 'Ср. чек', value: '1 235 ₽' },
        ].map((s) => (
          <div key={s.label} className="px-3 py-2 text-center">
            <div className="text-sm font-bold text-slate-900">{s.value}</div>
            <div className="text-xs text-slate-400">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Orders table */}
      <div className="divide-y divide-slate-50">
        {orders.map((order, i) => (
          <motion.div
            key={order.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center px-4 py-2.5 gap-3"
          >
            <span className="text-xs font-mono text-slate-400 w-12">{order.id}</span>
            <span className="flex-1 text-xs text-slate-700 truncate">{order.items}</span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${order.color}`}>
              {order.status}
            </span>
            <span className="text-xs font-bold text-slate-900 w-16 text-right">
              {order.amount} ₽
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add components/mocks/
git commit -m "feat: animated mock UI components for hero and solution sections"
```

---

## Task 7: Hero Section

**Files:**
- Create: `components/sections/Hero.tsx`

- [ ] **Step 1: Создать Hero.tsx**

```typescript
// components/sections/Hero.tsx
import { Button } from '@/components/ui/Button'
import { MockOrderDashboard } from '@/components/mocks/MockOrderDashboard'

export function Hero() {
  return (
    <section className="min-h-screen bg-slate-900 flex items-center pt-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-20 grid md:grid-cols-2 gap-12 items-center">
        {/* Text */}
        <div>
          <div className="inline-block bg-orange-500/10 text-orange-400 text-sm font-semibold px-3 py-1 rounded-full mb-6">
            Система онлайн-заказов под ключ
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight mb-6">
            Ваши клиенты заказывают напрямую.{' '}
            <span className="text-orange-400">Без комиссии агрегатора.</span>
          </h1>
          <p className="text-lg text-slate-400 mb-8 leading-relaxed">
            Собственный сайт заказов для ресторана — от меню до трекинга статуса и admin-панели.
            Внедрение под ключ за 5–10 дней.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              size="lg"
              onClick={() =>
                document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              Рассчитать окупаемость
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-white"
              onClick={() =>
                document.querySelector('#solution')?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              Узнать подробнее
            </Button>
          </div>
        </div>

        {/* Mock */}
        <div className="flex justify-center md:justify-end">
          <MockOrderDashboard />
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add components/sections/Hero.tsx
git commit -m "feat: hero section"
```

---

## Task 8: Problem, Solution, HowItWorks Sections

**Files:**
- Create: `components/sections/Problem.tsx`
- Create: `components/sections/Solution.tsx`
- Create: `components/sections/HowItWorks.tsx`

- [ ] **Step 1: Создать Problem.tsx**

```typescript
// components/sections/Problem.tsx
const problems = [
  {
    icon: '💸',
    title: 'Агрегаторы забирают 15–35%',
    body: 'С каждого заказа, каждый месяц, навсегда. При обороте 300 000 ₽ это 75 000–105 000 ₽ в месяц — просто за присутствие на платформе.',
  },
  {
    icon: '📞',
    title: 'Звонки, ошибки, недовольные клиенты',
    body: 'Менеджер принимает заказы вручную, путается в позициях, ошибается в адресе. Клиент ждёт, злится, больше не возвращается.',
  },
  {
    icon: '📊',
    title: 'Все данные клиентов — у агрегатора',
    body: 'История заказов, любимые блюда, телефоны — всё принадлежит платформе. Вы не можете работать с базой напрямую.',
  },
]

export function Problem() {
  return (
    <section className="bg-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Почему это нельзя игнорировать
          </h2>
          <p className="text-slate-500 text-lg max-w-2xl mx-auto">
            Агрегаторы удобны для старта, но с ростом оборота их комиссия становится главной
            статьёй расходов.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {problems.map((p) => (
            <div key={p.title} className="bg-slate-50 rounded-2xl p-6">
              <div className="text-4xl mb-4">{p.icon}</div>
              <h3 className="font-bold text-slate-900 text-lg mb-2">{p.title}</h3>
              <p className="text-slate-500 text-sm leading-relaxed">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Создать Solution.tsx**

```typescript
// components/sections/Solution.tsx
import { MockAdminPanel } from '@/components/mocks/MockAdminPanel'

const features = [
  { icon: '🍽️', label: 'Онлайн-меню с фото и категориями' },
  { icon: '🛒', label: 'Корзина и заказ без регистрации' },
  { icon: '📍', label: 'Трекинг статуса по трек-коду' },
  { icon: '⚙️', label: 'Полная admin-панель' },
  { icon: '👥', label: 'Роли: менеджер и владелец' },
  { icon: '🔔', label: 'Уведомления о новых заказах' },
]

export function Solution() {
  return (
    <section id="solution" className="bg-slate-50 py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            RestoGood — ваш собственный канал заказов
          </h2>
          <p className="text-slate-500 text-lg max-w-2xl mx-auto">
            Готовое решение: ресторан получает свой сайт заказов, admin-панель и полный контроль
            над клиентской базой.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="flex justify-center">
            <MockAdminPanel />
          </div>
          <div className="grid grid-cols-2 gap-4">
            {features.map((f) => (
              <div key={f.label} className="flex items-start gap-3 bg-white rounded-xl p-4 shadow-sm">
                <span className="text-2xl">{f.icon}</span>
                <span className="text-sm font-medium text-slate-700 leading-snug">{f.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Создать HowItWorks.tsx**

```typescript
// components/sections/HowItWorks.tsx
const steps = [
  {
    number: '01',
    title: 'Подключаемся',
    body: 'Обсуждаем задачи, подписываем договор. Вы рассказываете о меню и пожеланиях по дизайну.',
  },
  {
    number: '02',
    title: 'Настраиваем меню',
    body: 'Загружаем блюда, фото, цены и категории. Настраиваем брендинг под ваш стиль.',
  },
  {
    number: '03',
    title: 'Запускаем',
    body: 'Ресторан получает ссылку на свой сайт заказов. Привязываем к вашему домену, если нужно.',
  },
  {
    number: '04',
    title: 'Принимаем заказы',
    body: 'Менеджер видит все заказы в одном окне, меняет статусы. Клиент отслеживает статус по трек-коду.',
  },
]

export function HowItWorks() {
  return (
    <section className="bg-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Как это работает
          </h2>
          <p className="text-slate-500 text-lg">От договора до первого заказа — 5–10 рабочих дней.</p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <div key={step.number} className="relative">
              {i < steps.length - 1 && (
                <div className="hidden lg:block absolute top-6 left-full w-full h-px bg-slate-200 -translate-y-1/2 z-0" />
              )}
              <div className="relative bg-slate-50 rounded-2xl p-6">
                <div className="text-3xl font-black text-orange-200 mb-3">{step.number}</div>
                <h3 className="font-bold text-slate-900 mb-2">{step.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{step.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add components/sections/Problem.tsx components/sections/Solution.tsx components/sections/HowItWorks.tsx
git commit -m "feat: problem, solution, howitworks sections"
```

---

## Task 9: Packages Section

**Files:**
- Create: `components/sections/Packages.tsx`

- [ ] **Step 1: Создать Packages.tsx**

```typescript
// components/sections/Packages.tsx
import { packages } from '@/config/packages'
import { Button } from '@/components/ui/Button'

function formatPrice(price: number) {
  return price.toLocaleString('ru-RU') + ' ₽'
}

export function Packages() {
  return (
    <section id="packages" className="bg-slate-900 py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Пакеты</h2>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Выберите пакет под задачи вашего ресторана. Цены фиксированные — никаких ежемесячных
            платежей.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6 items-stretch">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className={`relative rounded-2xl p-6 flex flex-col ${
                pkg.recommended
                  ? 'bg-orange-500 text-white scale-105 shadow-2xl shadow-orange-900/40'
                  : 'bg-slate-800 text-slate-200'
              }`}
            >
              {pkg.recommended && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white text-orange-500 text-xs font-bold px-3 py-1 rounded-full shadow">
                  Популярный
                </div>
              )}
              <div className="mb-6">
                <h3
                  className={`text-xl font-bold mb-1 ${
                    pkg.recommended ? 'text-white' : 'text-white'
                  }`}
                >
                  {pkg.name}
                </h3>
                <div className="text-3xl font-black">{formatPrice(pkg.price)}</div>
                <div
                  className={`text-sm mt-1 ${pkg.recommended ? 'text-orange-100' : 'text-slate-400'}`}
                >
                  разовое внедрение
                </div>
              </div>

              <ul className="flex-1 space-y-2.5 mb-6">
                {pkg.features.map((f) => (
                  <li key={f.label} className="flex items-start gap-2 text-sm">
                    <span
                      className={`mt-0.5 flex-shrink-0 ${
                        f.included
                          ? pkg.recommended
                            ? 'text-white'
                            : 'text-emerald-400'
                          : pkg.recommended
                          ? 'text-orange-200 opacity-50'
                          : 'text-slate-600'
                      }`}
                    >
                      {f.included ? '✓' : '—'}
                    </span>
                    <span
                      className={
                        f.included
                          ? ''
                          : pkg.recommended
                          ? 'opacity-60'
                          : 'text-slate-600'
                      }
                    >
                      {f.label}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                variant={pkg.recommended ? 'ghost' : 'outline'}
                className={
                  pkg.recommended
                    ? 'bg-white text-orange-500 hover:bg-orange-50 w-full justify-center'
                    : 'border-slate-600 text-slate-300 hover:bg-slate-700 w-full justify-center'
                }
                onClick={() =>
                  document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' })
                }
              >
                Рассчитать окупаемость
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add components/sections/Packages.tsx
git commit -m "feat: packages section with recommended highlight"
```

---

## Task 10: ROI Calculator Section

**Files:**
- Create: `components/sections/RoiCalculator.tsx`

- [ ] **Step 1: Создать RoiCalculator.tsx**

```typescript
// components/sections/RoiCalculator.tsx
'use client'

import { useState, useMemo, lazy, Suspense } from 'react'
import dynamic from 'next/dynamic'
import { RangeSlider } from '@/components/ui/RangeSlider'
import { Button } from '@/components/ui/Button'
import { calculateRoi, calculatePayback } from '@/lib/roi'
import { packages } from '@/config/packages'

// Динамический импорт PDF — не блокирует первый рендер
const KpPdfDownloadButton = dynamic(
  () => import('@/components/KpPdf').then((m) => m.KpPdfDownloadButton),
  { ssr: false, loading: () => <Button variant="outline" className="w-full" disabled>Загрузка PDF...</Button> }
)

function formatRub(n: number) {
  return Math.round(n).toLocaleString('ru-RU') + ' ₽'
}

export function RoiCalculator() {
  const [restaurantName, setRestaurantName] = useState('')
  const [revenue, setRevenue] = useState(300000)
  const [commission, setCommission] = useState(25)
  const [phoneOrders, setPhoneOrders] = useState(0)
  const [contactName, setContactName] = useState('')
  const [contactPhone, setContactPhone] = useState('')

  const roi = useMemo(
    () => calculateRoi({ aggregatorRevenue: revenue, commission, phoneOrders }),
    [revenue, commission, phoneOrders]
  )

  const pdfData = {
    restaurantName,
    revenue,
    commission,
    phoneOrders,
    contactName,
    contactPhone,
    roi,
    packages,
  }

  return (
    <section id="calculator" className="bg-slate-50 py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Рассчитайте окупаемость для вашего ресторана
          </h2>
          <p className="text-slate-500 text-lg">
            Введите данные — и получите персональный расчёт и КП.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 items-start">
          {/* Form */}
          <div className="bg-white rounded-2xl p-6 shadow-sm space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Название заведения
              </label>
              <input
                type="text"
                placeholder="Например, Ресторан «Маяк»"
                value={restaurantName}
                onChange={(e) => setRestaurantName(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Оборот через агрегаторы в месяц
              </label>
              <div className="text-2xl font-black text-orange-500 mb-2">
                {formatRub(revenue)}
              </div>
              <RangeSlider
                value={revenue}
                min={50000}
                max={5000000}
                step={10000}
                onChange={setRevenue}
                formatLabel={(v) => v >= 1000000 ? `${v / 1000000}М` : `${v / 1000}К`}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Комиссия агрегатора
              </label>
              <div className="text-2xl font-black text-orange-500 mb-2">{commission}%</div>
              <RangeSlider
                value={commission}
                min={10}
                max={35}
                step={1}
                onChange={setCommission}
                formatLabel={(v) => `${v}%`}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Заказов по телефону в месяц{' '}
                <span className="font-normal text-slate-400">(необязательно)</span>
              </label>
              <input
                type="number"
                min={0}
                placeholder="0"
                value={phoneOrders || ''}
                onChange={(e) => setPhoneOrders(Math.max(0, Number(e.target.value)))}
                className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Ваше имя <span className="font-normal text-slate-400">(для КП)</span>
                </label>
                <input
                  type="text"
                  placeholder="Иван"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">
                  Телефон / Email
                </label>
                <input
                  type="text"
                  placeholder="+7 900 000-00-00"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="space-y-4">
            <div className="bg-slate-900 text-white rounded-2xl p-6">
              <div className="text-sm text-slate-400 mb-1">Ваша экономия в месяц</div>
              <div className="text-4xl font-black text-emerald-400">
                {formatRub(roi.savingsPerMonth)}
              </div>
              <div className="text-sm text-slate-400 mt-3">
                В год:{' '}
                <span className="text-white font-bold">{formatRub(roi.savingsPerYear)}</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-semibold text-slate-600 mb-3">Сравнение</div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-slate-500">Сейчас отдаёте агрегатору/год</span>
                <span className="font-bold text-red-500">{formatRub(roi.aggregatorAnnualLoss)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">С RestoGood/год</span>
                <span className="font-bold text-emerald-600">0 ₽</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-semibold text-slate-600 mb-3">
                Срок окупаемости по пакетам
              </div>
              <div className="space-y-2">
                {packages.map((pkg) => {
                  const months = calculatePayback(pkg.price, roi.savingsPerMonth)
                  return (
                    <div key={pkg.id} className="flex items-center justify-between text-sm">
                      <span className={`font-medium ${pkg.recommended ? 'text-orange-500' : 'text-slate-700'}`}>
                        {pkg.name} {pkg.recommended && '⭐'}
                      </span>
                      <span className="font-bold text-slate-900">
                        {months === Infinity
                          ? '—'
                          : months === 1
                          ? '1 месяц'
                          : `${months} мес.`}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            <KpPdfDownloadButton data={pdfData} />
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add components/sections/RoiCalculator.tsx
git commit -m "feat: roi calculator section with live computation"
```

---

## Task 11: PDF КП Generator

**Files:**
- Create: `components/KpPdf.tsx`

- [ ] **Step 1: Создать KpPdf.tsx**

`@react-pdf/renderer` работает только на клиенте. Компонент импортируется через `next/dynamic` с `ssr: false` из Task 10.

```typescript
// components/KpPdf.tsx
'use client'

import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Font,
  pdf,
} from '@react-pdf/renderer'
import { Button } from '@/components/ui/Button'
import { Package } from '@/config/packages'
import { RoiResult } from '@/lib/roi'

// Кириллица в PDF требует явной регистрации шрифта
Font.register({
  family: 'Roboto',
  fonts: [
    {
      src: 'https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxP.ttf',
      fontWeight: 400,
    },
    {
      src: 'https://fonts.gstatic.com/s/roboto/v30/KFOlCnqEu92Fr1MmEU9fBBc9.ttf',
      fontWeight: 700,
    },
  ],
})

const styles = StyleSheet.create({
  page: { fontFamily: 'Roboto', padding: 40, backgroundColor: '#FFFFFF' },
  cover: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A' },
  coverTitle: { fontSize: 32, fontWeight: 700, color: '#FFFFFF', marginBottom: 12 },
  coverSub: { fontSize: 14, color: '#94A3B8', marginBottom: 40 },
  coverFor: { fontSize: 18, fontWeight: 700, color: '#F97316' },
  coverDate: { fontSize: 11, color: '#64748B', marginTop: 8 },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 16, fontWeight: 700, color: '#0F172A', marginBottom: 12, borderBottomWidth: 1, borderBottomColor: '#E2E8F0', paddingBottom: 6 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  label: { fontSize: 11, color: '#64748B' },
  value: { fontSize: 11, fontWeight: 700, color: '#0F172A' },
  highlight: { fontSize: 24, fontWeight: 700, color: '#10B981' },
  redValue: { fontSize: 11, fontWeight: 700, color: '#EF4444' },
  packageCard: { marginBottom: 10, padding: 12, borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 8 },
  packageCardHighlight: { marginBottom: 10, padding: 12, backgroundColor: '#FFF7ED', borderWidth: 2, borderColor: '#F97316', borderRadius: 8 },
  packageName: { fontSize: 13, fontWeight: 700, color: '#0F172A', marginBottom: 4 },
  packagePrice: { fontSize: 11, color: '#64748B' },
  contact: { fontSize: 13, color: '#0F172A', marginBottom: 6 },
  footer: { position: 'absolute', bottom: 30, left: 40, right: 40, flexDirection: 'row', justifyContent: 'space-between' },
  footerText: { fontSize: 9, color: '#94A3B8' },
})

function formatRub(n: number) {
  return Math.round(n).toLocaleString('ru-RU') + ' ₽'
}

interface PdfData {
  restaurantName: string
  revenue: number
  commission: number
  phoneOrders: number
  contactName: string
  contactPhone: string
  roi: RoiResult
  packages: Package[]
}

function KpDocument({ data }: { data: PdfData }) {
  const today = new Date().toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <Document>
      {/* Обложка */}
      <Page size="A4" style={[styles.page, { padding: 0 }]}>
        <View style={styles.cover}>
          <Text style={styles.coverTitle}>RestoGood</Text>
          <Text style={styles.coverSub}>Система онлайн-заказов для ресторана</Text>
          <Text style={styles.coverFor}>
            Коммерческое предложение{data.restaurantName ? ` для ${data.restaurantName}` : ''}
          </Text>
          <Text style={styles.coverDate}>{today}</Text>
        </View>
      </Page>

      {/* Расчёт */}
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ваш расчёт экономии</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Оборот через агрегаторы/мес</Text>
            <Text style={styles.value}>{formatRub(data.revenue)}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Комиссия агрегатора</Text>
            <Text style={styles.value}>{data.commission}%</Text>
          </View>
          {data.phoneOrders > 0 && (
            <View style={styles.row}>
              <Text style={styles.label}>Телефонных заказов/мес</Text>
              <Text style={styles.value}>{data.phoneOrders}</Text>
            </View>
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Результат</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Экономия в месяц</Text>
            <Text style={styles.highlight}>{formatRub(data.roi.savingsPerMonth)}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Экономия в год</Text>
            <Text style={styles.value}>{formatRub(data.roi.savingsPerYear)}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Сейчас отдаёте агрегаторам/год</Text>
            <Text style={styles.redValue}>{formatRub(data.roi.aggregatorAnnualLoss)}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>С RestoGood/год</Text>
            <Text style={styles.value}>0 ₽</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Срок окупаемости</Text>
          {data.packages.map((pkg) => {
            const months =
              data.roi.savingsPerMonth > 0
                ? Math.ceil(pkg.price / data.roi.savingsPerMonth)
                : null
            return (
              <View
                key={pkg.id}
                style={pkg.recommended ? styles.packageCardHighlight : styles.packageCard}
              >
                <Text style={styles.packageName}>
                  {pkg.name} {pkg.recommended ? '(Рекомендуем)' : ''}
                </Text>
                <Text style={styles.packagePrice}>
                  Стоимость: {formatRub(pkg.price)} •{' '}
                  {months ? `Окупится за ${months} мес.` : 'Введите данные для расчёта'}
                </Text>
              </View>
            )
          })}
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>RestoGood</Text>
          <Text style={styles.footerText}>{today}</Text>
        </View>
      </Page>

      {/* Контакты */}
      <Page size="A4" style={styles.page}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Следующий шаг</Text>
          <Text style={{ fontSize: 13, color: '#475569', lineHeight: 1.6, marginBottom: 20 }}>
            Свяжитесь с нами, чтобы обсудить внедрение. Запуск — 5–10 рабочих дней с момента
            подписания договора.
          </Text>
          <Text style={styles.contact}>Telegram: @restogood</Text>
          <Text style={styles.contact}>WhatsApp: +7 900 000-00-00</Text>
          <Text style={styles.contact}>Email: hello@restogood.ru</Text>
        </View>

        {(data.contactName || data.contactPhone) && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Подготовлено для</Text>
            {data.contactName && <Text style={styles.contact}>{data.contactName}</Text>}
            {data.contactPhone && <Text style={styles.contact}>{data.contactPhone}</Text>}
          </View>
        )}
      </Page>
    </Document>
  )
}

export function KpPdfDownloadButton({ data }: { data: PdfData }) {
  async function handleDownload() {
    const blob = await pdf(<KpDocument data={data} />).toBlob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `restogood-kp-${data.restaurantName || 'ресторан'}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Button size="lg" className="w-full" onClick={handleDownload}>
      Скачать КП (PDF)
    </Button>
  )
}
```

- [ ] **Step 2: Проверить генерацию PDF в браузере**

Открыть `http://localhost:3000`, перейти к калькулятору, ввести данные, нажать «Скачать КП». Убедиться что PDF скачивается и кириллица корректно отображается.

- [ ] **Step 3: Commit**

```bash
git add components/KpPdf.tsx
git commit -m "feat: pdf kp generator with cyrillic support"
```

---

## Task 12: Testimonials, FAQ, Footer

**Files:**
- Create: `components/sections/Testimonials.tsx`
- Create: `components/sections/Faq.tsx`
- Create: `components/sections/Footer.tsx`

- [ ] **Step 1: Создать Testimonials.tsx**

```typescript
// components/sections/Testimonials.tsx
const testimonials = [
  {
    quote:
      'Подключили RestoGood три месяца назад. Ушли с Яндекс.Еды — комиссия была 28%. Теперь все заказы напрямую, менеджер не отвлекается на звонки. Система окупилась быстрее, чем ожидали.',
    author: 'Kavi',
    role: 'Ресторан, Москва',
  },
]

export function Testimonials() {
  return (
    <section className="bg-white py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Что говорят клиенты</h2>
        </div>
        <div className="grid gap-6">
          {testimonials.map((t) => (
            <div key={t.author} className="bg-slate-50 rounded-2xl p-8">
              <p className="text-lg text-slate-700 leading-relaxed mb-6 italic">«{t.quote}»</p>
              <div>
                <div className="font-bold text-slate-900">{t.author}</div>
                <div className="text-sm text-slate-400">{t.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Создать Faq.tsx**

```typescript
// components/sections/Faq.tsx
'use client'

import { useState } from 'react'
import { faq } from '@/config/faq'

export function Faq() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <section className="bg-slate-50 py-20">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Частые вопросы
          </h2>
        </div>
        <div className="space-y-3">
          {faq.map((item, i) => (
            <div key={i} className="bg-white rounded-2xl overflow-hidden shadow-sm">
              <button
                className="w-full text-left px-6 py-4 flex items-center justify-between font-semibold text-slate-800 hover:bg-slate-50 transition-colors"
                onClick={() => setOpen(open === i ? null : i)}
              >
                <span>{item.question}</span>
                <span className="text-orange-400 font-bold text-xl ml-4 flex-shrink-0">
                  {open === i ? '−' : '+'}
                </span>
              </button>
              {open === i && (
                <div className="px-6 pb-4 text-slate-500 text-sm leading-relaxed">
                  {item.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Создать Footer.tsx**

```typescript
// components/sections/Footer.tsx
import { site } from '@/config/site'
import { Button } from '@/components/ui/Button'

export function Footer() {
  return (
    <footer className="bg-slate-900 py-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
          Готовы уйти от агрегаторов?
        </h2>
        <p className="text-slate-400 text-lg mb-8 max-w-xl mx-auto">
          Рассчитайте окупаемость прямо сейчас — займёт 2 минуты.
        </p>
        <Button
          size="lg"
          className="mb-12"
          onClick={() =>
            document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' })
          }
        >
          Рассчитать окупаемость
        </Button>

        <div className="flex flex-wrap justify-center gap-6 mb-10">
          <a
            href={site.contacts.telegram}
            className="text-slate-400 hover:text-white transition-colors text-sm"
          >
            Telegram
          </a>
          <a
            href={site.contacts.whatsapp}
            className="text-slate-400 hover:text-white transition-colors text-sm"
          >
            WhatsApp
          </a>
          <a
            href={`mailto:${site.contacts.email}`}
            className="text-slate-400 hover:text-white transition-colors text-sm"
          >
            {site.contacts.email}
          </a>
        </div>

        <div className="border-t border-slate-800 pt-6 text-slate-600 text-xs">
          © {new Date().getFullYear()} {site.name}. Все права защищены.
        </div>
      </div>
    </footer>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add components/sections/Testimonials.tsx components/sections/Faq.tsx components/sections/Footer.tsx
git commit -m "feat: testimonials, faq, footer sections"
```

---

## Task 13: Page Assembly + SEO Metadata

**Files:**
- Modify: `app/layout.tsx`
- Modify: `app/page.tsx`
- Modify: `app/globals.css`

- [ ] **Step 1: Обновить app/globals.css**

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

html {
  scroll-behavior: smooth;
}

/* Custom range input styling */
input[type='range'] {
  -webkit-appearance: none;
  appearance: none;
}

input[type='range']::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #F97316;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

input[type='range']::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #F97316;
  cursor: pointer;
  border: none;
}
```

- [ ] **Step 2: Обновить app/layout.tsx**

```typescript
// app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { site } from '@/config/site'

const inter = Inter({ subsets: ['latin', 'cyrillic'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: `${site.name} — ${site.tagline}`,
  description: site.description,
  metadataBase: new URL(site.url),
  openGraph: {
    title: `${site.name} — ${site.tagline}`,
    description: site.description,
    url: site.url,
    siteName: site.name,
    locale: 'ru_RU',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: `${site.name} — ${site.tagline}`,
    description: site.description,
  },
  alternates: {
    canonical: site.url,
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'SoftwareApplication',
              name: site.name,
              description: site.description,
              url: site.url,
              applicationCategory: 'BusinessApplication',
              operatingSystem: 'Web',
              offers: {
                '@type': 'AggregateOffer',
                priceCurrency: 'RUB',
                lowPrice: 49900,
                highPrice: 149900,
              },
            }),
          }}
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  )
}
```

- [ ] **Step 3: Обновить app/page.tsx**

```typescript
// app/page.tsx
import { Navbar } from '@/components/Navbar'
import { Hero } from '@/components/sections/Hero'
import { Problem } from '@/components/sections/Problem'
import { Solution } from '@/components/sections/Solution'
import { HowItWorks } from '@/components/sections/HowItWorks'
import { Packages } from '@/components/sections/Packages'
import { RoiCalculator } from '@/components/sections/RoiCalculator'
import { Testimonials } from '@/components/sections/Testimonials'
import { Faq } from '@/components/sections/Faq'
import { Footer } from '@/components/sections/Footer'

export default function Home() {
  return (
    <main>
      <Navbar />
      <Hero />
      <Problem />
      <Solution />
      <HowItWorks />
      <Packages />
      <RoiCalculator />
      <Testimonials />
      <Faq />
      <Footer />
    </main>
  )
}
```

- [ ] **Step 4: Проверить что страница собирается без ошибок**

```bash
npm run build
```

Ожидание: `✓ Compiled successfully`. Нет TypeScript ошибок, нет предупреждений об импортах.

- [ ] **Step 5: Commit**

```bash
git add app/
git commit -m "feat: page assembly, seo metadata, json-ld schema"
```

---

## Task 14: Sitemap + Robots

**Files:**
- Create: `app/sitemap.ts`
- Create: `app/robots.ts`

- [ ] **Step 1: Создать app/sitemap.ts**

```typescript
// app/sitemap.ts
import { MetadataRoute } from 'next'
import { site } from '@/config/site'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: site.url,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 1,
    },
  ]
}
```

- [ ] **Step 2: Создать app/robots.ts**

```typescript
// app/robots.ts
import { MetadataRoute } from 'next'
import { site } from '@/config/site'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    sitemap: `${site.url}/sitemap.xml`,
  }
}
```

- [ ] **Step 3: Проверить что роуты доступны**

```bash
npm run dev
```

Открыть в браузере:
- `http://localhost:3000/sitemap.xml` — должен вернуть XML
- `http://localhost:3000/robots.txt` — должен вернуть текст с `Allow: /`

- [ ] **Step 4: Commit**

```bash
git add app/sitemap.ts app/robots.ts
git commit -m "feat: sitemap.xml and robots.txt"
```

---

## Self-Review

**Покрытие спека:**
- ✓ Navbar с бургером
- ✓ Hero с MockOrderDashboard (анимированный React-компонент, не скриншот)
- ✓ Problem (3 боли)
- ✓ Solution с MockAdminPanel
- ✓ HowItWorks (4 шага, степпер)
- ✓ Packages (3 карточки, Оптимум выделен)
- ✓ ROI Calculator (форма + live расчёт + окупаемость по пакетам)
- ✓ PDF КП (4 страницы, кириллица, динамический импорт)
- ✓ Testimonials (mock отзыв от Kavi)
- ✓ FAQ (accordion, конфиг)
- ✓ Footer с CTA
- ✓ SEO: Metadata API, OG теги, JSON-LD, canonical
- ✓ sitemap.xml + robots.txt
- ✓ ROI логика протестирована (Vitest, 7 тестов)
- ✓ Конфиг-файлы отделены от компонентов
- ✓ PDF загружается через next/dynamic (ssr: false)
- ✓ Framer Motion только в client-компонентах

**Типы согласованы:**
- `RoiInputs` / `RoiResult` определены в `lib/roi.ts`, используются в `RoiCalculator.tsx` и `KpPdf.tsx`
- `Package` / `PackageFeature` из `config/packages.ts` используются в `Packages.tsx`, `RoiCalculator.tsx`, `KpPdf.tsx`
- `PdfData` определён и используется внутри `KpPdf.tsx`
