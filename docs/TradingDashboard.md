# Professional Trading Dashboard - Upbit Style

## 🚀 Overview

A complete Next.js 15 trading dashboard inspired by Upbit exchange, featuring real-time market data, professional charts, order book visualization, and modern trading interfaces.

## 📁 Project Structure

```
src/
├── stores/
│   └── tradingStore.ts          # Zustand state management
├── components/
│   └── trading/
│       ├── TradingChart.tsx     # Professional chart with Lightweight Charts
│       ├── OrderBook.tsx        # Real-time order book visualization
│       ├── TradingForm.tsx      # Buy/sell order form
│       ├── MarketTicker.tsx     # Price ticker with animations
│       └── TradingHistory.tsx   # Trading history table
└── app/
    └── exchange/
        └── page.tsx             # Main exchange interface
```

## 🎨 Design System

### Color Palette

```css
/* Primary Background Colors */
--bg-primary: #0a0a0b     /* Deep black */
--bg-secondary: #1a1a1b   /* Dark gray */
--bg-tertiary: #2a2a2a    /* Medium gray */

/* Trading Colors */
--color-buy: #10b981      /* Green for buy orders */
--color-sell: #ef4444     /* Red for sell orders */
--color-neutral: #6b7280  /* Neutral gray */

/* Accent Colors */
--color-blue: #3b82f6     /* Primary blue */
--color-purple: #8b5cf6   /* Purple accent */
--color-amber: #f59e0b    /* Warning amber */
```

### Typography Scale

```css
.text-heading-lg    /* 20px, font-bold */
.text-heading-md    /* 18px, font-bold */
.text-heading-sm    /* 16px, font-bold */
.text-body-lg       /* 16px */
.text-body-md       /* 14px */
.text-body-sm       /* 12px */
.text-caption-md    /* 12px */
.text-label-md      /* 12px, font-semibold */
```

### Component Classes

```css
/* Cards */
.card-professional                /* Standard card styling */
.card-professional-elevated       /* Elevated card with enhanced shadow */
.card-professional-interactive    /* Interactive card with hover effects */

/* Buttons */
.button-professional             /* Standard button */
.button-professional-lg          /* Large button */
.buy-button-primary             /* Green buy button */
.sell-button-primary            /* Red sell button */

/* Inputs */
.input-professional             /* Professional input styling */
.select-professional            /* Professional select styling */

/* Icons */
.icon-bg-blue                   /* Blue icon background */
.icon-bg-green                  /* Green icon background */
.icon-bg-red                    /* Red icon background */
```

## 🧩 Components

### 1. TradingChart

Professional trading chart powered by Lightweight Charts library.

**Features:**
- Candlestick and line chart modes
- Multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Volume indicator
- Fullscreen mode
- Responsive design

**Usage:**
```tsx
import { TradingChart } from '@/components/trading/TradingChart';

<TradingChart height={500} className="custom-class" />
```

**Props:**
- `height?: number` - Chart height in pixels (default: 400)
- `className?: string` - Additional CSS classes

### 2. OrderBook

Real-time order book with bid/ask visualization.

**Features:**
- Live order book data
- Visual quantity bars
- Spread calculation
- Price level highlighting
- Smooth animations

**Usage:**
```tsx
import { OrderBook } from '@/components/trading/OrderBook';

<OrderBook maxEntries={15} className="h-full" />
```

**Props:**
- `maxEntries?: number` - Max orders to display (default: 15)
- `className?: string` - Additional CSS classes

### 3. TradingForm

Professional buy/sell order form with validation.

**Features:**
- Market and limit orders
- Percentage quick selectors
- Real-time order calculations
- Form validation
- Fee estimation

**Usage:**
```tsx
import { TradingForm } from '@/components/trading/TradingForm';

<TradingForm className="custom-class" />
```

**Props:**
- `className?: string` - Additional CSS classes

### 4. MarketTicker

Animated price ticker with market data.

**Features:**
- Real-time price updates
- Price change animations
- 24h statistics
- Compact and full modes
- Smooth transitions

**Usage:**
```tsx
import { MarketTicker } from '@/components/trading/MarketTicker';

// Compact mode
<MarketTicker compact />

// Full mode
<MarketTicker className="custom-class" />
```

**Props:**
- `compact?: boolean` - Use compact layout (default: false)
- `className?: string` - Additional CSS classes

### 5. TradingHistory

Advanced trading history table with filtering.

**Features:**
- Order history display
- Search and filtering
- Sortable columns
- Status indicators
- Pagination

**Usage:**
```tsx
import { TradingHistory } from '@/components/trading/TradingHistory';

<TradingHistory maxRows={10} className="custom-class" />
```

**Props:**
- `maxRows?: number` - Maximum rows to display
- `className?: string` - Additional CSS classes

## 🏪 State Management (Zustand)

### Store Structure

```typescript
interface TradingState {
  // Market Data
  selectedSymbol: string;
  marketTickers: Map<string, MarketTicker>;
  orderBooks: Map<string, OrderBook>;
  candlestickData: Map<string, CandlestickData[]>;

  // Trading
  orders: TradingOrder[];
  portfolio: Portfolio | null;

  // UI State
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  chartType: 'candlestick' | 'line';
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
}
```

### Key Actions

```typescript
// Market data updates
updateMarketTicker(ticker: MarketTicker)
updateOrderBook(orderBook: OrderBook)
updateCandlestickData(symbol: string, data: CandlestickData[])

// Trading actions
addOrder(order: Omit<TradingOrder, 'id' | 'timestamp'>)
updateOrder(orderId: string, updates: Partial<TradingOrder>)
updatePortfolio(portfolio: Portfolio)

// UI state
setSelectedSymbol(symbol: string)
setChartType(type: 'candlestick' | 'line')
setTimeframe(timeframe: string)
```

### Optimized Selectors

```typescript
// Use optimized selectors to prevent unnecessary re-renders
const selectedSymbol = useSelectedSymbol();
const marketTicker = useMarketTicker(symbol);
const orderBook = useOrderBook(symbol);
const portfolio = usePortfolio();
```

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile */    < 640px  (sm)
/* Tablet */    640px+   (md)
/* Desktop */   1024px+  (lg)
/* Large */     1280px+  (xl)
```

### Layout Strategy

1. **Desktop (lg+)**: Three-column layout
   - Left: Chart + History
   - Center: Order Book
   - Right: Trading Form

2. **Tablet (md-lg)**: Two-column layout
   - Left: Chart + History
   - Right: Trading Form + Order Book (stacked)

3. **Mobile (sm)**: Single-column stack
   - Chart
   - Trading Form
   - Order Book
   - History

### Responsive Classes

```css
/* Hide on mobile, show on desktop */
.hidden .lg:flex

/* Full width on mobile, fixed width on desktop */
.w-full .lg:w-80

/* Stack on mobile, row on desktop */
.flex-col .lg:flex-row
```

## 🎯 Performance Optimizations

### 1. Chart Performance
- Use `useMemo` for expensive calculations
- Debounce real-time updates
- Limit data points rendered
- Implement virtual scrolling for large datasets

### 2. State Updates
- Selective subscriptions with Zustand
- Optimized selectors prevent unnecessary re-renders
- Batch updates for related data

### 3. Animation Performance
- Use CSS transforms instead of changing layout properties
- Implement `will-change` for animated elements
- Use `requestAnimationFrame` for smooth animations

## 🔌 Integration Guide

### Adding Real WebSocket Data

1. **Replace demo data generators:**
```typescript
// Remove demo hooks
// useMarketTickerDemo();
// useTradingChartDemo();
// useOrderBookDemo();

// Add real WebSocket connection
useWebSocketConnection();
```

2. **WebSocket implementation:**
```typescript
// hooks/useWebSocket.ts
export function useWebSocketConnection() {
  const updateMarketTicker = useTradingStore(state => state.updateMarketTicker);

  useEffect(() => {
    const ws = new WebSocket('wss://api.example.com/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'ticker') {
        updateMarketTicker(data.payload);
      }
    };

    return () => ws.close();
  }, []);
}
```

### API Integration

```typescript
// lib/api.ts
export const api = {
  async getOrderBook(symbol: string) {
    const response = await fetch(`/api/orderbook/${symbol}`);
    return response.json();
  },

  async placeOrder(order: OrderRequest) {
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    return response.json();
  }
};
```

## 🚀 Deployment Guide

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws
NEXT_PUBLIC_ENVIRONMENT=production
```

### Build Commands

```bash
# Development
npm run dev

# Production build
npm run build
npm run start

# Type checking
npm run type-check

# Linting
npm run lint
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

## 🧪 Testing Strategy

### Component Testing

```typescript
// __tests__/components/TradingChart.test.tsx
import { render, screen } from '@testing-library/react';
import { TradingChart } from '@/components/trading/TradingChart';

test('renders trading chart', () => {
  render(<TradingChart />);
  expect(screen.getByText('Price Chart')).toBeInTheDocument();
});
```

### Integration Testing

```typescript
// __tests__/pages/exchange.test.tsx
import { render, screen } from '@testing-library/react';
import ExchangePage from '@/app/exchange/page';

test('renders complete exchange interface', () => {
  render(<ExchangePage />);

  expect(screen.getByText('Price Chart')).toBeInTheDocument();
  expect(screen.getByText('Order Book')).toBeInTheDocument();
  expect(screen.getByText('Trade')).toBeInTheDocument();
});
```

## 📊 Monitoring & Analytics

### Performance Metrics

```typescript
// lib/analytics.ts
export function trackOrderPlacement(order: TradingOrder) {
  analytics.track('Order Placed', {
    symbol: order.symbol,
    type: order.type,
    amount: order.quantity,
    timestamp: Date.now(),
  });
}

export function trackChartInteraction(action: string) {
  analytics.track('Chart Interaction', {
    action,
    timestamp: Date.now(),
  });
}
```

### Error Monitoring

```typescript
// lib/errorTracking.ts
export function reportError(error: Error, context: string) {
  console.error(`[${context}]`, error);

  // Send to monitoring service
  errorTracker.captureException(error, {
    tags: { context },
    extra: { timestamp: Date.now() },
  });
}
```

## 🔧 Customization Guide

### Theming

```typescript
// lib/theme.ts
export const tradingTheme = {
  colors: {
    buy: '#10b981',
    sell: '#ef4444',
    neutral: '#6b7280',
    primary: '#3b82f6',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
};
```

### Component Variants

```typescript
// components/ui/Button.tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        buy: "bg-green-600 text-white hover:bg-green-700",
        sell: "bg-red-600 text-white hover:bg-red-700",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);
```

## 📚 Additional Resources

### Libraries Used

- **Next.js 15**: React framework with App Router
- **TypeScript**: Type safety and developer experience
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **Lightweight Charts**: Professional trading charts
- **React Hook Form**: Form handling and validation
- **Framer Motion**: Smooth animations
- **Lucide React**: Professional icon library

### Further Reading

- [Next.js Documentation](https://nextjs.org/docs)
- [Lightweight Charts API](https://tradingview.github.io/lightweight-charts/)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Tailwind CSS Guide](https://tailwindcss.com/docs)

## 🤝 Contributing

### Code Style

1. Use TypeScript for all new code
2. Follow ESLint configuration
3. Use Prettier for code formatting
4. Write descriptive commit messages
5. Add tests for new features

### Component Guidelines

1. Use functional components with hooks
2. Implement proper TypeScript interfaces
3. Add JSDoc comments for complex functions
4. Use CSS modules or Tailwind classes
5. Ensure responsive design
6. Add loading and error states

---

**Total Implementation**: 8 core components, complete state management, responsive design, and professional UI/UX matching Upbit exchange standards.