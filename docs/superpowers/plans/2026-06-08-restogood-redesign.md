# RestoGood Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Полный визуальный редизайн лендинга RestoGood: новый design system (Onest шрифт, 5 цветовых переменных), обновлённая ROI-формула с параметром shiftRate, починенная PDF-генерация с локальными шрифтами.

**Architecture:** Статический Next.js 16 App Router проект, Tailwind v4 (CSS `@theme` блок — НЕ tailwind.config.ts), `@react-pdf/renderer` для PDF-скачивания. Все секции в `components/sections/`, конфиги в `config/`, бизнес-логика в `lib/`.

**Tech Stack:** Next.js 16, Tailwind v4, TypeScript, Framer Motion, @react-pdf/renderer, Vitest, Onest (Google Fonts via next/font)

**Working directory:** `/home/pensioner/coding/restogood-landing`

---

## File Map

| Файл | Что меняем |
|---|---|
| `app/globals.css` | Новые CSS-переменные, Onest var, цвет слайдера |
| `app/layout.tsx` | Geist → Onest |
| `lib/roi.ts` | Добавить `shiftRate` в `RoiInputs`, обновить `calculateRoi()` |
| `lib/roi.test.ts` | Обновить все тесты + добавить 3 для shiftRate |
| `config/packages.ts` | Добавить `defaultShiftRate: number` в интерфейс и данные |
| `public/fonts/Roboto-Regular.ttf` | Скачать локально |
| `public/fonts/Roboto-Bold.ttf` | Скачать локально |
| `components/KpPdf.tsx` | Локальный шрифт, упрощённый layout, shiftRate в данных |
| `components/sections/Hero.tsx` | Новый копи, accent цвет, типографика |
| `components/sections/Problem.tsx` | bg-light, новый h2, белые карточки |
| `components/sections/Solution.tsx` | bg-dark, glassmorphism карточки, новый копи |
| `components/sections/HowItWorks.tsx` | bg-light, accent номера шагов |
| `components/sections/Packages.tsx` | glassmorphism карточки, accent рекомендованный |
| `components/sections/RoiCalculator.tsx` | shiftRate слайдер, селектор пакета, новый копи |
| `components/sections/Faq.tsx` | bg-dark, белый текст, border-white/10 |
| `components/sections/Testimonials.tsx` | Больший шрифт цитаты |

---

## Task 1: Design System — globals.css + layout.tsx

**Files:**
- Modify: `app/globals.css`
- Modify: `app/layout.tsx`

Tailwind v4: `tailwind.config.ts` не используется. Токены объявляются в `@theme inline {}` блоке globals.css. Переменная `--color-accent` становится классами `bg-accent`, `text-accent`, `border-accent`.

- [ ] **Step 1: Заменить `app/globals.css` полностью**

```css
@import "tailwindcss";

@theme inline {
  --font-sans: var(--font-onest), system-ui, sans-serif;
  --color-dark: #0B0F19;
  --color-accent: #FF4D00;
  --color-light: #F5F5F0;
  --color-surface: #131929;
  --color-muted: #6B7280;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-sans);
}

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
  background: #FF4D00;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

input[type='range']::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FF4D00;
  cursor: pointer;
  border: none;
}
```

- [ ] **Step 2: Заменить `app/layout.tsx` полностью**

```typescript
import type { Metadata } from 'next'
import { Onest } from 'next/font/google'
import './globals.css'
import { site } from '@/config/site'

const onest = Onest({ subsets: ['latin', 'cyrillic'], variable: '--font-onest' })

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
    <html lang="ru" className={onest.variable}>
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

- [ ] **Step 3: Запустить dev-сервер и проверить что шрифт Onest загрузился**

```bash
cd /home/pensioner/coding/restogood-landing
npm run build 2>&1 | tail -20
```

Expected: BUILD SUCCESS, no font-related errors.

- [ ] **Step 4: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add app/globals.css app/layout.tsx
git commit -m "redesign: design system — Onest font, new CSS vars"
```

---

## Task 2: ROI Logic — shiftRate

**Files:**
- Modify: `lib/roi.ts`
- Modify: `lib/roi.test.ts`

`shiftRate` — доля (0.0–1.0) агрегаторных заказов, которые переходят на собственный сайт. Без него формула предполагала 100% переход. Теперь это явный параметр.

- [ ] **Step 1: Написать failing тесты в `lib/roi.test.ts`**

Заменить файл полностью:

```typescript
import { describe, it, expect } from 'vitest'
import { calculateRoi, calculatePayback } from './roi'

describe('calculateRoi', () => {
  it('calculates aggregator savings with full shift (shiftRate=1)', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
      shiftRate: 1,
    })
    expect(result.savingsPerMonth).toBe(75000)
  })

  it('halves aggregator savings when shiftRate=0.5', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
      shiftRate: 0.5,
    })
    expect(result.savingsPerMonth).toBe(37500)
  })

  it('returns only staffSavings when shiftRate=0', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 100,
      shiftRate: 0,
    })
    // staffSavings = 100 × 3 × (500/60) ≈ 2500
    expect(result.savingsPerMonth).toBeCloseTo(2500, 0)
  })

  it('adds staff savings for phone orders (3 min × 500₽/h per order)', () => {
    const result = calculateRoi({
      aggregatorRevenue: 0,
      commission: 0,
      phoneOrders: 100,
      shiftRate: 1,
    })
    expect(result.savingsPerMonth).toBeCloseTo(2500, 0)
  })

  it('combines aggregator and staff savings', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 100,
      shiftRate: 1,
    })
    expect(result.savingsPerMonth).toBeCloseTo(77500, 0)
  })

  it('calculates annual savings as 12× monthly', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
      shiftRate: 1,
    })
    expect(result.savingsPerYear).toBe(900000)
  })

  it('calculates aggregatorAnnualLoss at full shift (shiftRate=1)', () => {
    const result = calculateRoi({
      aggregatorRevenue: 300000,
      commission: 25,
      phoneOrders: 0,
      shiftRate: 1,
    })
    expect(result.aggregatorAnnualLoss).toBe(900000)
  })

  it('returns zero savings when all inputs are zero', () => {
    const result = calculateRoi({
      aggregatorRevenue: 0,
      commission: 0,
      phoneOrders: 0,
      shiftRate: 1,
    })
    expect(result.savingsPerMonth).toBe(0)
    expect(result.savingsPerYear).toBe(0)
  })
})

describe('calculatePayback', () => {
  it('returns ceiling of price divided by monthly savings', () => {
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

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```bash
cd /home/pensioner/coding/restogood-landing
npm test 2>&1 | tail -30
```

Expected: FAIL — `shiftRate` не существует в `RoiInputs`.

- [ ] **Step 3: Обновить `lib/roi.ts`**

```typescript
const OPERATOR_RATE_PER_MINUTE = 500 / 60

export interface RoiInputs {
  aggregatorRevenue: number
  commission: number
  phoneOrders: number
  shiftRate: number  // 0.0–1.0: доля агрегаторных заказов, переходящих на сайт
}

export interface RoiResult {
  savingsPerMonth: number
  savingsPerYear: number
  aggregatorAnnualLoss: number
}

export function calculateRoi(inputs: RoiInputs): RoiResult {
  const aggregatorSavings =
    inputs.aggregatorRevenue * (inputs.commission / 100) * inputs.shiftRate
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

- [ ] **Step 4: Запустить тесты — убедиться что все проходят**

```bash
cd /home/pensioner/coding/restogood-landing
npm test 2>&1 | tail -20
```

Expected: 11 tests passed.

- [ ] **Step 5: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add lib/roi.ts lib/roi.test.ts
git commit -m "feat: add shiftRate to ROI formula"
```

---

## Task 3: Packages Config — defaultShiftRate

**Files:**
- Modify: `config/packages.ts`

Добавляем `defaultShiftRate` в тип `Package` и данные. Значения обоснованы: чем лучше пакет, тем выше конверсия агрегаторных клиентов на прямой сайт.

- [ ] **Step 1: Обновить `config/packages.ts`**

```typescript
export interface PackageFeature {
  label: string
  included: boolean
}

export interface Package {
  id: string
  name: string
  price: number
  recommended: boolean
  defaultShiftRate: number  // 0.0–1.0: ожидаемая доля перехода для этого пакета
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
    defaultShiftRate: 0.40,
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
    defaultShiftRate: 0.65,
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
    defaultShiftRate: 0.85,
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

- [ ] **Step 2: Проверить TypeScript**

```bash
cd /home/pensioner/coding/restogood-landing
npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors (или только ошибки в KpPdf.tsx и RoiCalculator.tsx которые будут исправлены позже).

- [ ] **Step 3: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add config/packages.ts
git commit -m "feat: add defaultShiftRate to packages"
```

---

## Task 4: Download Font Files

**Files:**
- Create: `public/fonts/Roboto-Regular.ttf`
- Create: `public/fonts/Roboto-Bold.ttf`

PDF-генератор (@react-pdf/renderer) не поддерживает WOFF/WOFF2 и не умеет ждать загрузки CDN-шрифта. Скачиваем Roboto с Cyrillic локально — он грузится с localhost без задержек CDN.

- [ ] **Step 1: Скачать шрифты**

```bash
cd /home/pensioner/coding/restogood-landing
mkdir -p public/fonts
curl -L "https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxP.ttf" \
  -o public/fonts/Roboto-Regular.ttf
curl -L "https://fonts.gstatic.com/s/roboto/v30/KFOlCnqEu92Fr1MmEU9fBBc9.ttf" \
  -o public/fonts/Roboto-Bold.ttf
```

- [ ] **Step 2: Проверить размер файлов**

```bash
ls -lh /home/pensioner/coding/restogood-landing/public/fonts/
```

Expected: Roboto-Regular.ttf ~130–170KB, Roboto-Bold.ttf ~130–170KB. Если файл < 10KB — загрузка не удалась.

- [ ] **Step 3: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add public/fonts/
git commit -m "chore: add local Roboto fonts for PDF generation"
```

---

## Task 5: KpPdf Rewrite — локальный шрифт + shiftRate

**Files:**
- Modify: `components/KpPdf.tsx`

Зависит от Task 2 (новый `RoiResult`) и Task 4 (шрифты в `public/fonts/`). Ключевые изменения:
1. Шрифт регистрируется из `/fonts/Roboto-Regular.ttf` (локально) вместо CDN
2. Шрифт предзагружается через `fetch()` перед `pdf()` — blob URL гарантирует доступность
3. Добавлен `shiftRate` в `KpPdfData` для отображения в PDF
4. Layout упрощён — меньше вложенных View

- [ ] **Step 1: Заменить `components/KpPdf.tsx` полностью**

```typescript
'use client'

import React from 'react'
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

const styles = StyleSheet.create({
  coverPage: { padding: 0, backgroundColor: '#0B0F19', fontFamily: 'Roboto' },
  cover: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 60 },
  coverTitle: { fontSize: 36, fontWeight: 700, color: '#FFFFFF', marginBottom: 8 },
  coverSub: { fontSize: 13, color: '#94A3B8', marginBottom: 48 },
  coverFor: { fontSize: 20, fontWeight: 700, color: '#FF4D00' },
  coverDate: { fontSize: 11, color: '#6B7280', marginTop: 8 },
  page: { padding: 48, backgroundColor: '#FFFFFF', fontFamily: 'Roboto' },
  h2: { fontSize: 18, fontWeight: 700, color: '#0B0F19', marginBottom: 16, marginTop: 8 },
  divider: { borderBottomWidth: 1, borderBottomColor: '#E5E7EB', marginBottom: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  label: { fontSize: 11, color: '#6B7280' },
  value: { fontSize: 11, fontWeight: 700, color: '#0B0F19' },
  bigSaving: { fontSize: 28, fontWeight: 700, color: '#16A34A', marginBottom: 4 },
  redValue: { fontSize: 11, fontWeight: 700, color: '#EF4444' },
  pkgRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
  },
  pkgRowHL: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#FF4D00',
    borderRadius: 8,
    backgroundColor: '#FFF7F5',
  },
  pkgName: { fontSize: 12, fontWeight: 700, color: '#0B0F19' },
  pkgDetail: { fontSize: 11, color: '#6B7280' },
  contact: { fontSize: 13, color: '#0B0F19', marginBottom: 8 },
  nextStep: { fontSize: 13, color: '#475569', lineHeight: 1.6, marginBottom: 24 },
})

function formatRub(n: number) {
  return Math.round(n).toLocaleString('ru-RU') + ' ₽'
}

export interface KpPdfData {
  restaurantName: string
  revenue: number
  commission: number
  phoneOrders: number
  shiftRate: number  // 0.0–1.0
  contactName: string
  contactPhone: string
  roi: RoiResult
  packages: Package[]
}

function KpDocument({ data }: { data: KpPdfData }) {
  const today = new Date().toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <Document>
      {/* Cover */}
      <Page size="A4" style={styles.coverPage}>
        <View style={styles.cover}>
          <Text style={styles.coverTitle}>RestoGood</Text>
          <Text style={styles.coverSub}>Система онлайн-заказов для ресторана</Text>
          <Text style={styles.coverFor}>
            Коммерческое предложение
            {data.restaurantName ? ` для ${data.restaurantName}` : ''}
          </Text>
          <Text style={styles.coverDate}>{today}</Text>
        </View>
      </Page>

      {/* ROI + Packages */}
      <Page size="A4" style={styles.page}>
        <Text style={styles.h2}>Ваш расчёт</Text>
        <View style={styles.divider} />

        <View style={styles.row}>
          <Text style={styles.label}>Оборот через агрегаторы/мес</Text>
          <Text style={styles.value}>{formatRub(data.revenue)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Комиссия агрегатора</Text>
          <Text style={styles.value}>{data.commission}%</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Ожидаемый переход на сайт</Text>
          <Text style={styles.value}>{Math.round(data.shiftRate * 100)}%</Text>
        </View>
        {data.phoneOrders > 0 && (
          <View style={styles.row}>
            <Text style={styles.label}>Заказов по телефону/мес</Text>
            <Text style={styles.value}>{data.phoneOrders}</Text>
          </View>
        )}

        <Text style={[styles.bigSaving, { marginTop: 24 }]}>
          {formatRub(data.roi.savingsPerMonth)}
        </Text>
        <Text style={[styles.label, { marginBottom: 8 }]}>экономия в месяц</Text>

        <View style={styles.row}>
          <Text style={styles.label}>Экономия в год</Text>
          <Text style={styles.value}>{formatRub(data.roi.savingsPerYear)}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Отдаёте агрегаторам сейчас/год</Text>
          <Text style={styles.redValue}>{formatRub(data.roi.aggregatorAnnualLoss)}</Text>
        </View>
        <View style={[styles.row, { marginBottom: 32 }]}>
          <Text style={styles.label}>С RestoGood/год</Text>
          <Text style={[styles.value, { color: '#16A34A' }]}>0 ₽</Text>
        </View>

        <Text style={styles.h2}>Пакеты</Text>
        <View style={styles.divider} />

        {data.packages.map((pkg) => {
          const months =
            data.roi.savingsPerMonth > 0
              ? Math.ceil(pkg.price / data.roi.savingsPerMonth)
              : null
          return (
            <View key={pkg.id} style={pkg.recommended ? styles.pkgRowHL : styles.pkgRow}>
              <View>
                <Text style={styles.pkgName}>
                  {pkg.name}{pkg.recommended ? '  ← Рекомендуем' : ''}
                </Text>
                <Text style={styles.pkgDetail}>{formatRub(pkg.price)}</Text>
              </View>
              <Text style={styles.pkgDetail}>
                {months ? `окупится за ${months} мес.` : '—'}
              </Text>
            </View>
          )
        })}
      </Page>

      {/* Contacts */}
      <Page size="A4" style={styles.page}>
        <Text style={styles.h2}>Следующий шаг</Text>
        <View style={styles.divider} />
        <Text style={styles.nextStep}>
          Свяжитесь с нами, чтобы обсудить внедрение.{'\n'}
          Запуск — 5–10 рабочих дней с момента подписания договора.
        </Text>
        <Text style={styles.contact}>Telegram: @restogood</Text>
        <Text style={styles.contact}>Email: hello@restogood.ru</Text>

        {(data.contactName || data.contactPhone) && (
          <View style={{ marginTop: 32 }}>
            <Text style={styles.h2}>Подготовлено для</Text>
            <View style={styles.divider} />
            {data.contactName ? <Text style={styles.contact}>{data.contactName}</Text> : null}
            {data.contactPhone ? <Text style={styles.contact}>{data.contactPhone}</Text> : null}
          </View>
        )}
      </Page>
    </Document>
  )
}

export function KpPdfDownloadButton({ data }: { data: KpPdfData }) {
  async function handleDownload() {
    // Pre-fetch fonts locally to avoid CDN latency / failures
    const [regularBlob, boldBlob] = await Promise.all([
      fetch('/fonts/Roboto-Regular.ttf').then((r) => r.blob()),
      fetch('/fonts/Roboto-Bold.ttf').then((r) => r.blob()),
    ])
    const regularUrl = URL.createObjectURL(regularBlob)
    const boldUrl = URL.createObjectURL(boldBlob)

    Font.register({
      family: 'Roboto',
      fonts: [
        { src: regularUrl, fontWeight: 400 },
        { src: boldUrl, fontWeight: 700 },
      ],
    })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const blob = await pdf(React.createElement(KpDocument, { data }) as any).toBlob()

    URL.revokeObjectURL(regularUrl)
    URL.revokeObjectURL(boldUrl)

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

- [ ] **Step 2: Проверить TypeScript**

```bash
cd /home/pensioner/coding/restogood-landing
npx tsc --noEmit 2>&1 | grep "KpPdf"
```

Expected: no errors for KpPdf.tsx (ошибки в RoiCalculator.tsx ожидаемы — исправим в Task 11).

- [ ] **Step 3: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add components/KpPdf.tsx
git commit -m "fix: KpPdf — local fonts, simplified layout, shiftRate"
```

---

## Task 6: Hero Redesign

**Files:**
- Modify: `components/sections/Hero.tsx`

Использует CSS-переменные из Task 1. `bg-dark` = #0B0F19, `text-accent` = #FF4D00. Радиальный градиент в inline style (Tailwind arbitrary values не поддерживают `radial-gradient` нативно).

- [ ] **Step 1: Заменить `components/sections/Hero.tsx` полностью**

```typescript
'use client'

import { Button } from '@/components/ui/Button'
import { MockOrderDashboard } from '@/components/mocks/MockOrderDashboard'

export function Hero() {
  return (
    <section
      className="min-h-screen bg-dark flex items-center pt-16"
      style={{
        background:
          'radial-gradient(ellipse at 0% 100%, rgba(255,77,0,0.12) 0%, #0B0F19 55%)',
      }}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-24 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-block bg-accent/10 text-accent text-sm font-semibold px-3 py-1 rounded-full mb-8">
            Система онлайн-заказов под ключ
          </div>
          <h1 className="text-5xl sm:text-7xl font-extrabold text-white leading-tight mb-6">
            Хватит отдавать{' '}
            <span className="text-accent">28% агрегаторам.</span>
          </h1>
          <p className="text-xl text-white/60 mb-10 leading-relaxed">
            За 5–10 дней — своя платформа заказов. Навсегда без комиссий.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              size="lg"
              className="bg-accent hover:bg-accent/90 text-white"
              onClick={() =>
                document.querySelector('#calculator')?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              Рассчитать окупаемость
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white/20 text-white/80 hover:bg-white/5"
              onClick={() =>
                document.querySelector('#solution')?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              Узнать подробнее
            </Button>
          </div>
        </div>

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
cd /home/pensioner/coding/restogood-landing
git add components/sections/Hero.tsx
git commit -m "redesign: Hero — new copy, accent color, larger typography"
```

---

## Task 7: Problem Redesign

**Files:**
- Modify: `components/sections/Problem.tsx`

`bg-light` = #F5F5F0. Карточки белые с тенью. Увеличенная иконка и жирный заголовок.

- [ ] **Step 1: Заменить `components/sections/Problem.tsx` полностью**

```typescript
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
    <section className="bg-light py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-dark mb-4">
            Сколько вы теряете прямо сейчас
          </h2>
          <p className="text-muted text-lg max-w-2xl mx-auto">
            Агрегаторы удобны для старта, но с ростом оборота их комиссия становится
            главной статьёй расходов.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {problems.map((p) => (
            <div key={p.title} className="bg-white rounded-2xl p-8 shadow-sm">
              <div className="text-5xl mb-6">{p.icon}</div>
              <h3 className="font-bold text-dark text-xl mb-3">{p.title}</h3>
              <p className="text-muted leading-relaxed">{p.body}</p>
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
cd /home/pensioner/coding/restogood-landing
git add components/sections/Problem.tsx
git commit -m "redesign: Problem — bg-light, new heading, bold cards"
```

---

## Task 8: Solution Redesign

**Files:**
- Modify: `components/sections/Solution.tsx`

Тёмный фон, glassmorphism карточки фич. `bg-white/5 backdrop-blur-sm border border-white/10`.

- [ ] **Step 1: Заменить `components/sections/Solution.tsx` полностью**

```typescript
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
    <section id="solution" className="bg-dark py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Один раз — и заказы ваши.
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            Полная платформа заказов под ваш бренд. Никаких ежемесячных платежей.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="flex justify-center">
            <MockAdminPanel />
          </div>
          <div className="grid grid-cols-2 gap-4">
            {features.map((f) => (
              <div
                key={f.label}
                className="flex items-start gap-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4"
              >
                <span className="text-2xl">{f.icon}</span>
                <span className="text-sm font-medium text-white/80 leading-snug">{f.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add components/sections/Solution.tsx
git commit -m "redesign: Solution — dark bg, glassmorphism cards, new copy"
```

---

## Task 9: HowItWorks Redesign

**Files:**
- Modify: `components/sections/HowItWorks.tsx`

Фон светлый (`bg-light`), номера шагов в цвете акцента (было `text-orange-200` — слишком бледный).

- [ ] **Step 1: Заменить `components/sections/HowItWorks.tsx` полностью**

```typescript
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
    <section className="bg-light py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-dark mb-4">
            Как это работает
          </h2>
          <p className="text-muted text-lg">
            От договора до первого заказа — 5–10 рабочих дней.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <div key={step.number} className="relative">
              {i < steps.length - 1 && (
                <div className="hidden lg:block absolute top-6 left-full w-full h-px bg-dark/10 -translate-y-1/2 z-0" />
              )}
              <div className="relative bg-white rounded-2xl p-6 shadow-sm">
                <div className="text-4xl font-black text-accent mb-4">{step.number}</div>
                <h3 className="font-bold text-dark mb-2">{step.title}</h3>
                <p className="text-sm text-muted leading-relaxed">{step.body}</p>
              </div>
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
cd /home/pensioner/coding/restogood-landing
git add components/sections/HowItWorks.tsx
git commit -m "redesign: HowItWorks — bg-light, accent step numbers"
```

---

## Task 10: Packages Redesign

**Files:**
- Modify: `components/sections/Packages.tsx`

Glassmorphism для обычных карточек. Рекомендованный: gradient + `border-accent`. Бейдж красный (accent), не выступающий (inline в заголовке карточки). Секция уже тёмная — оставляем.

- [ ] **Step 1: Заменить `components/sections/Packages.tsx` полностью**

```typescript
'use client'

import { packages } from '@/config/packages'
import { Button } from '@/components/ui/Button'

function formatPrice(price: number) {
  return price.toLocaleString('ru-RU') + ' ₽'
}

export function Packages() {
  return (
    <section id="packages" className="bg-dark py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Выберите свой пакет
          </h2>
          <p className="text-white/50 text-lg max-w-xl mx-auto">
            Платите один раз. Пользуетесь всегда.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6 items-stretch">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className={`relative rounded-2xl p-6 flex flex-col ${
                pkg.recommended
                  ? 'bg-gradient-to-b from-accent/20 to-transparent border-2 border-accent'
                  : 'bg-white/5 border border-white/10'
              }`}
            >
              {pkg.recommended && (
                <div className="inline-flex self-start mb-4 bg-accent text-white text-xs font-bold px-3 py-1 rounded-full">
                  Популярный
                </div>
              )}
              <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-1">{pkg.name}</h3>
                <div className="text-3xl font-black text-white">{formatPrice(pkg.price)}</div>
                <div className="text-sm mt-1 text-white/40">разовое внедрение</div>
              </div>

              <ul className="flex-1 space-y-2.5 mb-6">
                {pkg.features.map((f) => (
                  <li key={f.label} className="flex items-start gap-2 text-sm">
                    <span
                      className={`mt-0.5 flex-shrink-0 ${
                        f.included ? 'text-accent' : 'text-white/20'
                      }`}
                    >
                      {f.included ? '✓' : '—'}
                    </span>
                    <span
                      className={f.included ? 'text-white/80' : 'text-white/30'}
                    >
                      {f.label}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                variant="outline"
                className={
                  pkg.recommended
                    ? 'bg-accent border-accent text-white hover:bg-accent/90 w-full justify-center'
                    : 'border-white/20 text-white/70 hover:bg-white/5 w-full justify-center'
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
cd /home/pensioner/coding/restogood-landing
git add components/sections/Packages.tsx
git commit -m "redesign: Packages — glassmorphism, accent recommended card"
```

---

## Task 11: RoiCalculator — shiftRate + package selector

**Files:**
- Modify: `components/sections/RoiCalculator.tsx`

Зависит от Task 2 (roi.ts с shiftRate), Task 3 (packages.defaultShiftRate), Task 5 (KpPdf с shiftRate в KpPdfData).

Добавляем:
- Tabs для выбора пакета (Economy / Optimal / Premium)
- Слайдер `shiftRatePct` (10–100%, шаг 5)
- `shiftRateTouched` флаг: при смене пакета сбрасываем до дефолта только если пользователь не трогал слайдер вручную

`formatRub` остаётся локальной функцией (в roi.ts её нет).

- [ ] **Step 1: Заменить `components/sections/RoiCalculator.tsx` полностью**

```typescript
'use client'

import { useState, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { RangeSlider } from '@/components/ui/RangeSlider'
import { Button } from '@/components/ui/Button'
import { calculateRoi, calculatePayback } from '@/lib/roi'
import { packages } from '@/config/packages'

const KpPdfDownloadButton = dynamic(
  () => import('@/components/KpPdf').then((m) => m.KpPdfDownloadButton),
  {
    ssr: false,
    loading: () => (
      <Button variant="outline" className="w-full" disabled>
        Загрузка PDF...
      </Button>
    ),
  }
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

  // shiftRate: % заказов которые перейдут на прямой сайт (10–100)
  const defaultPkg = packages.find((p) => p.recommended) ?? packages[1]
  const [selectedPkgId, setSelectedPkgId] = useState(defaultPkg.id)
  const [shiftRatePct, setShiftRatePct] = useState(
    Math.round(defaultPkg.defaultShiftRate * 100)
  )
  const [shiftRateTouched, setShiftRateTouched] = useState(false)

  function handlePackageSelect(pkgId: string) {
    setSelectedPkgId(pkgId)
    if (!shiftRateTouched) {
      const pkg = packages.find((p) => p.id === pkgId)
      if (pkg) setShiftRatePct(Math.round(pkg.defaultShiftRate * 100))
    }
  }

  function handleShiftRateChange(value: number) {
    setShiftRatePct(value)
    setShiftRateTouched(true)
  }

  const shiftRate = shiftRatePct / 100

  const roi = useMemo(
    () => calculateRoi({ aggregatorRevenue: revenue, commission, phoneOrders, shiftRate }),
    [revenue, commission, phoneOrders, shiftRate]
  )

  const pdfData = {
    restaurantName,
    revenue,
    commission,
    phoneOrders,
    shiftRate,
    contactName,
    contactPhone,
    roi,
    packages,
  }

  return (
    <section id="calculator" className="bg-light py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-dark mb-4">
            Посчитайте, сколько вы вернёте
          </h2>
          <p className="text-muted text-lg">
            Введите данные вашего ресторана — покажем ROI и сформируем КП.
          </p>
        </div>

        {/* Package selector */}
        <div className="flex gap-2 justify-center mb-10">
          {packages.map((pkg) => (
            <button
              key={pkg.id}
              onClick={() => handlePackageSelect(pkg.id)}
              className={`px-5 py-2 rounded-full text-sm font-semibold transition-colors ${
                selectedPkgId === pkg.id
                  ? 'bg-accent text-white'
                  : 'bg-white border border-dark/10 text-muted hover:border-accent hover:text-accent'
              }`}
            >
              {pkg.name}
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-8 items-start">
          {/* Form */}
          <div className="bg-white rounded-2xl p-6 shadow-sm space-y-6">
            <div>
              <label className="block text-sm font-semibold text-dark mb-2">
                Название заведения
              </label>
              <input
                type="text"
                placeholder="Например, Ресторан «Маяк»"
                value={restaurantName}
                onChange={(e) => setRestaurantName(e.target.value)}
                className="w-full border border-dark/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-dark mb-1">
                Оборот через агрегаторы в месяц
              </label>
              <div className="text-2xl font-black text-accent mb-2">{formatRub(revenue)}</div>
              <RangeSlider
                value={revenue}
                min={50000}
                max={5000000}
                step={10000}
                onChange={setRevenue}
                formatLabel={(v) => (v >= 1000000 ? `${v / 1000000}М` : `${v / 1000}К`)}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-dark mb-1">
                Комиссия агрегатора
              </label>
              <div className="text-2xl font-black text-accent mb-2">{commission}%</div>
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
              <label className="block text-sm font-semibold text-dark mb-1">
                % заказов через свой сайт
                <span className="ml-2 font-normal text-muted text-xs">
                  (зависит от пакета и маркетинга)
                </span>
              </label>
              <div className="text-2xl font-black text-accent mb-2">{shiftRatePct}%</div>
              <RangeSlider
                value={shiftRatePct}
                min={10}
                max={100}
                step={5}
                onChange={handleShiftRateChange}
                formatLabel={(v) => `${v}%`}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-dark mb-2">
                Заказов по телефону в месяц{' '}
                <span className="font-normal text-muted">(необязательно)</span>
              </label>
              <input
                type="number"
                min={0}
                placeholder="0"
                value={phoneOrders || ''}
                onChange={(e) => setPhoneOrders(Math.max(0, Number(e.target.value)))}
                className="w-full border border-dark/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-dark mb-1">
                  Ваше имя <span className="font-normal text-muted">(для КП)</span>
                </label>
                <input
                  type="text"
                  placeholder="Иван"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  className="w-full border border-dark/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-dark mb-1">
                  Телефон / Email
                </label>
                <input
                  type="text"
                  placeholder="+7 900 000-00-00"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="w-full border border-dark/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="space-y-4">
            <div className="bg-dark text-white rounded-2xl p-6">
              <div className="text-sm text-white/40 mb-1">Ваша экономия в месяц</div>
              <div className="text-4xl font-black text-emerald-400">
                {formatRub(roi.savingsPerMonth)}
              </div>
              <div className="text-sm text-white/40 mt-3">
                В год:{' '}
                <span className="text-white font-bold">{formatRub(roi.savingsPerYear)}</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-dark/5">
              <div className="text-sm font-semibold text-dark mb-3">Сравнение</div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted">Сейчас отдаёте агрегатору/год</span>
                <span className="font-bold text-red-500">
                  {formatRub(roi.aggregatorAnnualLoss)}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted">С RestoGood/год</span>
                <span className="font-bold text-emerald-600">0 ₽</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 shadow-sm border border-dark/5">
              <div className="text-sm font-semibold text-dark mb-3">
                Срок окупаемости по пакетам
              </div>
              <div className="space-y-2">
                {packages.map((pkg) => {
                  const months = calculatePayback(pkg.price, roi.savingsPerMonth)
                  const isSelected = pkg.id === selectedPkgId
                  return (
                    <div
                      key={pkg.id}
                      className={`flex items-center justify-between text-sm py-1 ${
                        isSelected ? 'text-accent font-semibold' : ''
                      }`}
                    >
                      <span className={`font-medium ${isSelected ? 'text-accent' : 'text-dark'}`}>
                        {pkg.name} {isSelected && '←'}
                      </span>
                      <span className={`font-bold ${isSelected ? 'text-accent' : 'text-dark'}`}>
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

- [ ] **Step 2: Проверить TypeScript**

```bash
cd /home/pensioner/coding/restogood-landing
npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 3: Запустить тесты**

```bash
cd /home/pensioner/coding/restogood-landing
npm test
```

Expected: 11 tests passed.

- [ ] **Step 4: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add components/sections/RoiCalculator.tsx
git commit -m "feat: RoiCalculator — shiftRate slider, package selector, new copy"
```

---

## Task 12: FAQ Redesign

**Files:**
- Modify: `components/sections/Faq.tsx`

Тёмный фон, белый текст, аккордеон с `border-white/10`.

- [ ] **Step 1: Заменить `components/sections/Faq.tsx` полностью**

```typescript
'use client'

import { useState } from 'react'
import { faq } from '@/config/faq'

export function Faq() {
  const [open, setOpen] = useState<number | null>(null)

  return (
    <section className="bg-dark py-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Частые вопросы
          </h2>
        </div>
        <div className="space-y-3">
          {faq.map((item, i) => (
            <div key={i} className="border border-white/10 rounded-2xl overflow-hidden">
              <button
                className="w-full text-left px-6 py-4 flex items-center justify-between font-semibold text-white hover:bg-white/5 transition-colors"
                onClick={() => setOpen(open === i ? null : i)}
              >
                <span>{item.question}</span>
                <span className="text-accent font-bold text-xl ml-4 flex-shrink-0">
                  {open === i ? '−' : '+'}
                </span>
              </button>
              {open === i && (
                <div className="px-6 pb-4 text-white/50 text-sm leading-relaxed">
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

- [ ] **Step 2: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add components/sections/Faq.tsx
git commit -m "redesign: FAQ — dark bg, white text, border accordion"
```

---

## Task 13: Testimonials Typography + Final Build

**Files:**
- Modify: `components/sections/Testimonials.tsx`

Минимальное изменение: цитата `text-xl` вместо `text-lg`, фон меняем на `bg-light` для консистентности.

- [ ] **Step 1: Заменить `components/sections/Testimonials.tsx` полностью**

```typescript
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
    <section className="bg-light py-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-dark mb-4">
            Что говорят клиенты
          </h2>
        </div>
        <div className="grid gap-6">
          {testimonials.map((t) => (
            <div key={t.author} className="bg-white rounded-2xl p-10 shadow-sm">
              <p className="text-xl text-dark/80 leading-relaxed mb-8 italic">
                «{t.quote}»
              </p>
              <div>
                <div className="font-bold text-dark">{t.author}</div>
                <div className="text-sm text-muted">{t.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Запустить production build**

```bash
cd /home/pensioner/coding/restogood-landing
npm run build 2>&1 | tail -30
```

Expected: BUILD SUCCESS, все маршруты.

- [ ] **Step 3: Запустить тесты финально**

```bash
cd /home/pensioner/coding/restogood-landing
npm test
```

Expected: 11 tests passed.

- [ ] **Step 4: Commit**

```bash
cd /home/pensioner/coding/restogood-landing
git add components/sections/Testimonials.tsx
git commit -m "redesign: Testimonials — larger quote, bg-light"
```

- [ ] **Step 5: Итоговый коммит**

```bash
cd /home/pensioner/coding/restogood-landing
git log --oneline -15
```

Убедиться что все 13 задач закоммичены.
