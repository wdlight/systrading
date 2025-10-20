# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time Korean stock trading UI built with Next.js 15, connecting to a FastAPI backend for live market data and automated trading.

**Tech Stack**:
- Next.js 15 (App Router)
- TypeScript
- shadcn/ui + Tailwind CSS
- WebSocket for real-time data
- TanStack Query for server state
- Zustand for client state
- Lightweight Charts & ECharts for visualization

## Development Commands

```bash
# Development server (runs on port 9000)
npm run dev
./scripts/start-server.sh  # Recommended - kills existing servers first

# Production build
npm run build
npm run start

# Code quality
npm run lint

# Server management
npm run stop  # Kill servers on port 9000
```

**Access URLs**:
- Main: http://localhost:9000
- Trading view: http://localhost:9000/trading
- Exchange: http://localhost:9000/exchange

## Critical Architecture Patterns

### Real-Time Data Flow

**Backend → Frontend data flow**:
```
FastAPI Backend (port 8000)
    ↓ WebSocket (ws://localhost:8000/ws)
WebSocketManager (singleton)
    ↓ Message routing by type
Custom Hooks (useOrderBook, useRealtimeMinuteCandles, etc.)
    ↓ React state updates
Components (OrderBook, MinuteChart, etc.)
```

**Key files**:
- `src/lib/websocket.ts` - WebSocket manager singleton with reconnection logic
- `src/lib/types.ts` - Message type definitions matching backend
- `src/hooks/useOrderBook.ts` - Real-time orderbook updates
- `src/hooks/useRealtimeMinuteCandles.ts` - Real-time candle updates

### WebSocket Message Types

All messages follow this structure:
```typescript
interface RealtimeMessage {
  type: string;  // 'price_update' | 'orderbook_update' | 'minute_candle_update' | etc.
  data: any;
  timestamp: string;
}
```

**Critical**: Backend sends Korean field names (e.g., `종목코드`, `현재가`). TypeScript types reflect this.

### React State Update Pattern for Real-Time Data

**CRITICAL BUG FIX PATTERN**: When updating state from WebSocket messages, React may not detect changes if object structure is identical. Always force new references:

```typescript
// ❌ BAD - React may not re-render
setOrderBook(normalizeOrderBook(data));

// ✅ GOOD - Force new reference with unique ID
setOrderBook({
  ...normalizeOrderBook(data),
  _updateId: Date.now()  // Forces React to detect change
} as OrderBookData);
```

**Why**: React's reconciliation uses reference equality for objects. Even if data changed, identical structure = same reference = no re-render.

**See**: `docs/bugfix-orderbook-re-render.md` for detailed analysis.

### React Hooks Rules (CRITICAL)

**All Hooks MUST be declared before any conditional returns**:

```typescript
// ✅ CORRECT
export function Component() {
  // 1. All Hooks first
  const data = useData();
  const [state, setState] = useState();
  const callback = useCallback(() => {}, []);

  useEffect(() => {}, []);

  // 2. Then conditional returns
  if (loading) return <Loading />;
  if (error) return <Error />;

  // 3. Then render logic
  return <div>{data}</div>;
}

// ❌ WRONG - Hook after conditional return
export function Component() {
  if (loading) return <Loading />;
  const data = useData();  // ERROR: Hooks must be called in same order
}
```

**Violation causes**: "React has detected a change in the order of Hooks"

### Time-Based Logic

**Trading hours**: Korean stock market 09:00-15:30 KST

```typescript
// Check if market is open
const isMarketOpen = () => {
  const now = new Date();
  const hour = now.getHours();
  const minute = now.getMinutes();
  const time = hour * 60 + minute;

  return time >= 9 * 60 && time <= 15 * 60 + 30;
};
```

**After-hours trading**: Display data even when `!isMarketOpen()` if backend sends it:

```typescript
const hasValidData = asks.length > 0 || bids.length > 0;
const isMarketClosed = !hasValidData && !isMarketOpen();
```

### Custom Hooks Architecture

**Pattern**: All real-time hooks follow this structure:

```typescript
export function useRealTimeData() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initial REST API load
  useEffect(() => {
    loadInitialData();
  }, []);

  // WebSocket subscription
  useEffect(() => {
    const unsubscribe = subscribeToUpdates((update) => {
      setData({
        ...normalizeData(update),
        _updateId: Date.now()  // Force re-render
      });
    });

    return unsubscribe;
  }, [stockCode]);

  return { data, isLoading, error };
}
```

**Key hooks**:
- `useOrderBook` - Real-time orderbook (호가)
- `useRealtimeMinuteCandles` - Live 1-minute candles
- `useRealTimePrice` - Current price updates
- `useWebSocket` - Direct WebSocket access

### Backend Communication

**Environment variables** (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

**API Client** (`src/lib/api-client.ts`):
```typescript
export const apiClient = {
  getAccountBalance: () => fetch(`${API_URL}/api/account/balance`),
  getCurrentOrderBook: (stockCode) => fetch(`${API_URL}/api/orderbook/${stockCode}`),
  // ... etc
}
```

**WebSocket Manager** (`src/lib/websocket.ts`):
```typescript
// Singleton instance
export const wsManager = new WebSocketManager();

// Subscribe to specific message types
export function subscribeToOrderBookUpdates(
  stockCode: string,
  callback: (data: OrderBookUpdate) => void
) {
  return wsManager.on(`orderbook:${stockCode}`, callback);
}
```

## Common Pitfalls

### 1. useMemo/useCallback with Array Dependencies

**Problem**: Arrays are always new references, causing infinite loops:

```typescript
// ❌ BAD - Re-calculates on every render
const sorted = useMemo(
  () => data.sort(),
  [data]  // data is new array reference every time
);

// ✅ GOOD - Depend on primitive value
const sorted = useMemo(
  () => data.sort(),
  [data.length]  // Or just remove useMemo for small arrays
);
```

**For small datasets (< 100 items)**: Skip useMemo entirely. The memoization overhead exceeds the benefit.

### 2. Throttling Real-Time Updates

**Anti-pattern**: Don't throttle WebSocket updates for trading data:

```typescript
// ❌ BAD - Misses price changes
if (Date.now() - lastUpdate < 1000) return;  // Ignores updates within 1 second

// ✅ GOOD - Show every update
setData(newData);  // Let React handle optimization
```

**Why**: Users expect to see every price tick. Throttling breaks trust in real-time accuracy.

### 3. Zero-Price Data Filtering

**Backend sometimes sends placeholder rows** with `price: 0`. Always filter:

```typescript
const validData = rawData.filter(item => item.price > 0);
```

### 4. Client-Side Component Hydration

**Use `'use client'` directive when**:
- Using useState, useEffect, or any Hook
- Accessing browser APIs (WebSocket, localStorage)
- Using event handlers (onClick, onChange)

**Don't use when**:
- Doing initial data fetching (use Server Components)
- Rendering static content

## Type System

**Import order for types**:
```typescript
// 1. Framework types
import type { ReactNode } from 'react';

// 2. Project types
import type { OrderBookData, WatchlistItem } from '@/lib/types';

// 3. Component-specific types
interface ComponentProps {
  stockCode: string;
  onSelect?: (code: string) => void;
}
```

**Backend response types** match Python FastAPI models with Korean field names preserved.

## Performance Considerations

### Chart Rendering

**Lightweight Charts** (preferred for candlestick charts):
- Faster than TradingView for real-time updates
- Lower memory footprint
- See `src/hooks/useTRViewChart.ts` for usage

**ECharts** (for complex overlays):
- Better for custom indicators
- More styling options
- Heavier - use sparingly

### WebSocket Optimization

**Current optimization** (in `src/lib/websocket.ts`):
- Automatic reconnection with exponential backoff
- Heartbeat to detect stale connections
- Subscription restoration on reconnect
- Message sampling for logging (not all messages logged)

**Polling fallback**: Hooks implement 1-second REST API polling when WebSocket fails.

## Testing & Debugging

### Chrome DevTools MCP

**Setup** (Ubuntu):
```bash
# Start Chrome with remote debugging
chromium-browser --remote-debugging-port=9222 http://localhost:9000 &

# MCP config in ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-chrome-devtools"],
      "env": {
        "CHROME_PATH": "/usr/bin/chromium-browser"
      }
    }
  }
}
```

### Console Logging Pattern

**Structured logs for debugging**:
```typescript
console.log(`📊 [${new Date().toLocaleTimeString()}] Event: ${event}`);
console.log(`🔄 Component render - data: ${data.length} items`);
console.log(`⚡ useEffect triggered - dependency: ${dep}`);
console.log(`✨ Highlight triggered - key: ${key}`);
```

**Emoji prefixes** help visually scan logs:
- 📊 WebSocket messages
- 🔄 Component renders
- ⚡ Effect triggers
- ✨ UI updates
- 🔥 Price changes
- 🆔 State changes

## File Organization

```
src/
├── app/                      # Next.js 15 App Router
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Dashboard home
│   ├── trading/             # Trading view page
│   └── exchange/            # Exchange page
├── components/
│   ├── common/              # Shared components
│   ├── trading/             # Trading-specific (OrderBook, MinuteChart, etc.)
│   └── ui/                  # shadcn/ui primitives
├── hooks/                   # Custom React hooks (all start with 'use')
├── lib/
│   ├── websocket.ts         # WebSocket manager (CRITICAL)
│   ├── api-client.ts        # REST API client
│   ├── types.ts             # Core type definitions
│   ├── constants.ts         # API URLs, message types
│   └── utils/               # Helper functions
└── docs/                    # Documentation and bug reports
    └── plan/mincandle/      # Feature implementation plans
```

## Backend Integration Notes

**CRITICAL**: Never modify backend. Frontend must adapt to backend's data format and timing.

**Backend quirks to handle**:
1. Korean field names in responses
2. Variable number of orderbook rows (3-5 depending on market activity)
3. After-hours data may still arrive
4. WebSocket may send duplicate messages
5. Timestamps in ISO 8601 format but may be missing

## Avoid Over-Engineering

**Don't**:
- Add Redux/MobX (use Zustand for global state, React Query for server state)
- Create deep abstraction layers for simple components
- Premature optimization (measure first)
- Complex folder nesting for < 10 files

**Do**:
- Start simple, refactor when needed
- Colocate related code
- Use TypeScript for contracts, not Java-style interfaces everywhere
- Prefer composition over inheritance

## Known Issues & Workarounds

See `docs/` directory for detailed bug reports. Key issues:

1. **OrderBook not re-rendering**: Force unique state with `_updateId` (see `docs/bugfix-orderbook-re-render.md`)
2. **Minute candle updates**: 1-second polling + WebSocket hybrid approach
3. **WebSocket reconnection**: Handled automatically by WebSocketManager
4. **After-hours display**: Check data availability, not just market hours

## References

- Next.js App Router: https://nextjs.org/docs/app
- shadcn/ui: https://ui.shadcn.com/
- Lightweight Charts: https://tradingview.github.io/lightweight-charts/
- Korean stock market hours: 09:00-15:30 KST
