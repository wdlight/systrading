# OrderBook Re-render Bug Fix

## Problem Summary
WebSocket successfully receives orderbook updates (`useOrderBook.ts:217` logs "📊 호가 실시간 업데이트"), but the OrderBook component doesn't re-render and highlights don't show.

## Root Cause Analysis

### Issue 1: State Reference Identity
**Location**: `/src/hooks/useOrderBook.ts` lines 205-223

**Problem**: Even though `normalizeOrderBook()` creates new objects, React's state comparison might not detect changes because:
1. The returned object structure is identical to the previous state
2. No unique identifier forces React to recognize a state change
3. Shallow comparison can miss nested object changes

**Evidence**:
```typescript
setOrderBook((prev) => {
  const normalized = normalizeOrderBook({ ... });
  if (normalized) {
    return normalized; // ⚠️ May return structurally identical object
  }
  return prev; // Explicitly returns same reference
});
```

### Issue 2: Component Logging Position
**Location**: `/src/components/trading/OrderBook.tsx` line 287

**Problem**: Console log "🔄 호가 배열 생성" appears AFTER all conditional returns (loading, error, no data). If any condition is true, the log never executes, making debugging confusing.

**Evidence**:
```typescript
// Lines 250-281: Early returns for loading, error, no data
if (isLoading) return ...
if (error) return ...
if (!orderBook) return ...

// Line 287: Log only executes if all above conditions are false
console.log('🔄 호가 배열 생성');
```

### Issue 3: useEffect Dependency
**Location**: `/src/components/trading/OrderBook.tsx` line 238

**Problem**: `useEffect` depends on `orderBook` object reference. If the reference doesn't change (Issue 1), the effect never triggers, so highlights never update.

## Solution Implemented

### Fix 1: Force Unique State Update (useOrderBook.ts)

**Added unique identifier to guarantee React re-renders:**

```typescript
setOrderBook((prev) => {
  const updateTime = Date.now();
  const normalized = normalizeOrderBook({ ... });

  if (normalized) {
    // ✅ Force completely new object with unique ID
    return {
      ...normalized,
      _updateId: updateTime, // React MUST detect this change
    } as OrderBookData;
  }

  return prev;
});
```

**Why it works**:
- `_updateId` changes on EVERY update (timestamp-based)
- React ALWAYS detects a state change (object reference changes)
- useEffect dependency `[orderBook]` now triggers reliably

### Fix 2: Enhanced Debugging Logs

**Added strategic console.logs to trace execution flow:**

#### useOrderBook.ts (lines 219-227):
```typescript
console.log(`📊 호가 실시간 업데이트: ${stockCode}`);
console.log(`🔥 매도1: ${prevAsk1} → ${newAsk1} | 매수1: ${prevBid1} → ${newBid1}`);
console.log(`🆔 State 참조 변경: ${prev === normalized ? '❌ 동일 참조' : '✅ 새 객체'}`);
```

#### OrderBook.tsx (lines 73-90):
```typescript
// BEFORE all hooks and conditions
console.log(`🔄 OrderBook 컴포넌트 렌더 시작`);

// AFTER useOrderBook hook
console.log(`📦 orderBook 상태:`, {
  exists: !!orderBook,
  timestamp: orderBook?.timestamp,
  asksCount: orderBook?.asks?.length,
  bid1Price: orderBook?.bids?.[0]?.price,
});
```

#### OrderBook.tsx useEffect (line 161):
```typescript
useEffect(() => {
  console.log(`⚡ useEffect 실행됨 - orderBook 존재: ${!!orderBook}`);
  // ... rest of effect
}, [orderBook, triggerHighlight]);
```

## Verification Steps

### Expected Log Sequence (when update received):

```
1. useOrderBook.ts:226  → 📊 호가 실시간 업데이트: 005930
2. useOrderBook.ts:227  → 🔥 매도1: 50000 → 50100 | 매수1: 49900 → 49950
3. useOrderBook.ts:228  → 🆔 State 참조 변경: ✅ 새 객체 생성 (정상)
4. OrderBook.tsx:74     → 🔄 OrderBook 컴포넌트 렌더 시작
5. OrderBook.tsx:83-90  → 📦 orderBook 상태: { exists: true, ... }
6. OrderBook.tsx:161    → ⚡ useEffect 실행됨 - orderBook 존재: true
7. OrderBook.tsx:158    → ⚡ useEffect 트리거 - timestamp: ...
8. OrderBook.tsx:176    → ✨ 하이라이트 트리거 - 매도 2개 행
9. OrderBook.tsx:287    → 🔄 호가 배열 생성 - asks: 5개, bids: 5개
```

### Test Checklist:

- [ ] WebSocket receives data: Check for "📊 호가 실시간 업데이트"
- [ ] State reference changes: Check for "🆔 State 참조 변경: ✅ 새 객체 생성"
- [ ] Component re-renders: Check for "🔄 OrderBook 컴포넌트 렌더 시작"
- [ ] useEffect triggers: Check for "⚡ useEffect 실행됨"
- [ ] Highlights trigger: Check for "✨ 하이라이트 트리거"
- [ ] Visual highlights appear: Red/blue flashing on price/quantity changes

## Technical Details

### Before Fix:
```typescript
// useOrderBook.ts - State may not change reference
return normalized; // Same structure = React might skip re-render

// OrderBook.tsx - useEffect dependency doesn't trigger
useEffect(() => { ... }, [orderBook]); // orderBook reference unchanged
```

### After Fix:
```typescript
// useOrderBook.ts - State ALWAYS changes reference
return { ...normalized, _updateId: Date.now() }; // Unique object every time

// OrderBook.tsx - useEffect dependency triggers reliably
useEffect(() => { ... }, [orderBook]); // orderBook._updateId changes
```

### Performance Impact:
- **Minimal**: `_updateId` is a single number property (8 bytes)
- **Benefit**: Guarantees React reactivity without complex deep comparison
- **Trade-off**: Slightly more re-renders, but necessary for real-time updates

## Files Modified

1. `/src/hooks/useOrderBook.ts`
   - Added `_updateId` to force unique state updates
   - Enhanced debugging logs with before/after comparison
   - Added state reference identity check

2. `/src/components/trading/OrderBook.tsx`
   - Added component render start log (before hooks)
   - Added orderBook state inspection log (after useOrderBook)
   - Added useEffect execution log

## Testing Notes

**Dev Server**: Run `npm run dev` and monitor browser console

**Expected Behavior**:
1. Every WebSocket message triggers state update
2. State update triggers component re-render
3. Re-render triggers useEffect
4. useEffect triggers highlights
5. Highlights appear visually for 500ms

**If still not working, check**:
- WebSocket connection: `wsManager.isConnected()`
- Subscription status: Look for "✅ 호가 구독 시작"
- Backend sending data: Check backend logs
- Browser console errors: Any React/TypeScript errors

## Related Files

- `/src/lib/websocket.ts` - WebSocket manager
- `/src/lib/types.ts` - OrderBookData type definition
- `/src/components/trading/OrderBook.tsx` - UI component
- `/src/hooks/useOrderBook.ts` - State management hook

## Next Steps if Issue Persists

1. **Verify WebSocket data format** matches OrderBookUpdate type
2. **Check for memoization** elsewhere in component tree
3. **Verify `clsx` and `highlightedKeys`** state management
4. **Test with simpler component** to isolate React re-render issue
5. **Check Next.js React version** for known re-render bugs
