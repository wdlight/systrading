# Frontend - Next.js Stock Trading System

## 📁 Project Overview
- **Framework**: Next.js 15 (App Router)
- **UI**: shadcn/ui + Tailwind CSS
- **Language**: TypeScript

This is a Next.js project for a stock trading application. It provides a user interface for monitoring stock prices, managing a portfolio, and executing trades.

The main page displays a dashboard with components like Portfolio Summary, Performance, Watchlist, and Market Overview. It also includes a manual trading interface. The application uses a WebSocket for real-time data and a backend API for account data.

---

## 🏗️ Core Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root Layout
│   ├── page.tsx           # Home Page
│   └── globals.css        # Global Styles
├── components/             # React Components
│   ├── common/            # Common Components (e.g., tables, cards)
│   └── ui/                # shadcn/ui Components
├── lib/                    # Utilities & Libraries (e.g., api-client, utils)
└── types/                  # TypeScript Type Definitions
```

---

## 🔧 Development Commands

```bash
# Run the development server (localhost:9000)
npm run dev

# Build for production
npm run build

# Run ESLint for code analysis
npm run lint

# Run TypeScript type checking
npm run type-check
```

---

## 📡 API Integration

### Backend Connection
The frontend connects to a backend server for data. Configure the API and WebSocket URLs in a `.env.local` file.

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
```

**Environment Variables (`.env.local`)**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Core Data Types
Key data structures for the application.

```typescript
// types/trading.ts
export interface WatchlistItem {
  stockCode: string;
  stockName: string;
  currentPrice: number;
  rateOfReturn: number;
  avgPrice: number;
  quantity: number;
  MACD: number;
  RSI: number;
}

export interface AccountInfo {
  stockCode: string;
  stockName: string;
  quantity: number;
  purchasePrice: number;
  rateOfReturn: number;
  currentPrice: number;
}
```

---

## 🎨 UI Components

### shadcn/ui Setup
Install components as needed.

```bash
# Example: Install necessary components
npx shadcn-ui@latest add button card table input
```

### Component Authoring Pattern
Follow this pattern for creating new components.

```typescript
// components/common/StockTable.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface StockTableProps {
  stocks: WatchlistItem[]
  onSelect?: (code: string) => void
}

export function StockTable({ stocks, onSelect }: StockTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>My Stocks</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Table content goes here */}
      </CardContent>
    </Card>
  )
}
```

---

## ⚡ Next.js Best Practices

### 1. **Server vs. Client Components**
- **Server Components (Default)**: Use for data fetching and non-interactive content.
- **Client Components (`'use client'`)**: Use only when client-side interactivity (state, effects, event listeners) is required.

### 2. **Data Fetching Patterns**
- Fetch initial data on the server within Server Components.
- Use Client Components with `useEffect` to handle real-time updates via WebSocket.

### 3. **Routing Structure**
The app uses a file-based routing system.
```
app/
├── page.tsx              # / (Home)
├── stocks/
│   ├── page.tsx         # /stocks (Stock List)
│   └── [code]/
│       └── page.tsx     # /stocks/005930 (Individual Stock)
└── trading/
    ├── page.tsx         # /trading (Trading Interface)
    └── history/
        └── page.tsx     # /trading/history
```

### 4. **Performance Optimization**
- **Images**: Use `next/image`.
- **Fonts**: Use `next/font`.
- **Bundle Size**: Import only necessary libraries.
- **Code Splitting**: Use dynamic `import()` for lazy loading components.

---

## ✅ Development Workflow & Conventions

### Guiding Principles
- **Simplicity First**: Start with the simplest solution.
- **Incremental Improvement**: Add complexity only as needed.
- **Use Standard Patterns**: Prefer official Next.js patterns.
- **Minimal Dependencies**: Only install libraries that are essential.
- **Avoid Premature Optimization**: Optimize only when a performance problem is identified.

### New Feature Workflow
1.  **Create a branch**: `git checkout -b feature/new-feature`
2.  Write the component, starting simple.
3.  Add TypeScript types.
4.  Test manually.
5.  Run `npm run lint` and `npm run type-check`.
6.  Commit: `git commit -m "feat: Describe the new feature"`

### File Naming Conventions
- **Components**: `PascalCase.tsx`
- **Pages**: `page.tsx` (App Router convention)
- **Hooks**: `useHookName.ts`
- **Utilities**: `utilityName.ts`
- **Types**: `*.types.ts`

### Common Problem Solving

**Hydration Mismatch**
To avoid issues with server-rendered vs. client-rendered content, especially with browser-only APIs:
```typescript
const [isMounted, setIsMounted] = useState(false)
useEffect(() => setIsMounted(true), [])
if (!isMounted) return null // or a loading skeleton
```

**WebSocket Connection Management**
Always clean up WebSocket connections in a `useEffect` hook.
```typescript
useEffect(() => {
  const ws = new WebSocket(WS_URL)
  // ... event listeners
  return () => ws.close() // Cleanup function is crucial
}, [])
```

---

## 📋 Checklist

### Before Development
- [ ] Clearly define requirements.
- [ ] Choose the simplest implementation path.
- [ ] Install only necessary libraries.

### During Development
- [ ] Adhere to the Single Responsibility Principle for components.
- [ ] Define all necessary types.
- [ ] Implement error handling.

### After Development
- [ ] Ensure no linting errors (`npm run lint`).
- [ ] Ensure no type errors (`npm run type-check`).
- [ ] Verify that core functionality works as expected.