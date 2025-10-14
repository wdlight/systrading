'use client';

interface OrderBookRow {
  price: number;
  quantity: number;
  orderCount: number;
}

interface OrderBookProps {
  stockCode: string;
  currentPrice: number;
}

export function OrderBook({ stockCode, currentPrice }: OrderBookProps) {
  // Sample data - will be replaced with real API data later
  const sampleAsks: OrderBookRow[] = [
    { price: currentPrice + 500, quantity: 1500, orderCount: 12 },
    { price: currentPrice + 400, quantity: 2300, orderCount: 18 },
    { price: currentPrice + 300, quantity: 3200, orderCount: 25 },
    { price: currentPrice + 200, quantity: 4100, orderCount: 31 },
    { price: currentPrice + 100, quantity: 5500, orderCount: 42 },
  ];

  const sampleBids: OrderBookRow[] = [
    { price: currentPrice - 100, quantity: 6200, orderCount: 45 },
    { price: currentPrice - 200, quantity: 4800, orderCount: 38 },
    { price: currentPrice - 300, quantity: 3500, orderCount: 28 },
    { price: currentPrice - 400, quantity: 2600, orderCount: 21 },
    { price: currentPrice - 500, quantity: 1800, orderCount: 15 },
  ];

  const maxQuantity = Math.max(
    ...sampleAsks.map(a => a.quantity),
    ...sampleBids.map(b => b.quantity)
  );

  return (
    <div className="w-full">
      {/* Header */}
      <div className="grid grid-cols-3 text-[10px] text-gray-400 pb-1 border-b border-gray-700">
        <div className="text-right">가격</div>
        <div className="text-right">수량</div>
        <div className="text-right">건수</div>
      </div>

      {/* Sell Orders (Red) */}
      <div className="space-y-0.5 py-1">
        {sampleAsks.reverse().map((ask, idx) => {
          const widthPercent = (ask.quantity / maxQuantity) * 100;
          return (
            <div key={`ask-${idx}`} className="relative">
              <div
                className="absolute right-0 top-0 h-full bg-red-900/20"
                style={{ width: `${widthPercent}%` }}
              />
              <div className="relative grid grid-cols-3 text-[11px] py-0.5">
                <div className="text-right text-red-400 font-medium">
                  {ask.price.toLocaleString()}
                </div>
                <div className="text-right text-gray-300">
                  {ask.quantity.toLocaleString()}
                </div>
                <div className="text-right text-gray-500 text-[10px]">
                  {ask.orderCount}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Current Price Separator */}
      <div className="py-1 border-y border-gray-600 my-1">
        <div className="text-center text-sm font-bold text-white">
          {currentPrice.toLocaleString()}
        </div>
      </div>

      {/* Buy Orders (Blue) */}
      <div className="space-y-0.5 py-1">
        {sampleBids.map((bid, idx) => {
          const widthPercent = (bid.quantity / maxQuantity) * 100;
          return (
            <div key={`bid-${idx}`} className="relative">
              <div
                className="absolute right-0 top-0 h-full bg-blue-900/20"
                style={{ width: `${widthPercent}%` }}
              />
              <div className="relative grid grid-cols-3 text-[11px] py-0.5">
                <div className="text-right text-blue-400 font-medium">
                  {bid.price.toLocaleString()}
                </div>
                <div className="text-right text-gray-300">
                  {bid.quantity.toLocaleString()}
                </div>
                <div className="text-right text-gray-500 text-[10px]">
                  {bid.orderCount}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}