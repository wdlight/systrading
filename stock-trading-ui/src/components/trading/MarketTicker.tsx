'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn, formatNumber, formatPercentage } from '@/lib/utils';
import { useTradingStore, useSelectedSymbol, useMarketTicker } from '@/stores/tradingStore';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Volume2,
  Clock,
  Star,
  Search,
  ChevronDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MarketTickerProps {
  className?: string;
  compact?: boolean;
}

export function MarketTicker({ className, compact = false }: MarketTickerProps) {
  const selectedSymbol = useSelectedSymbol();
  const marketTicker = useMarketTicker(selectedSymbol);
  const [priceFlash, setPriceFlash] = useState<'up' | 'down' | null>(null);
  const [prevPrice, setPrevPrice] = useState<number | null>(null);

  // Flash animation when price changes
  useEffect(() => {
    if (marketTicker && prevPrice !== null && marketTicker.price !== prevPrice) {
      setPriceFlash(marketTicker.price > prevPrice ? 'up' : 'down');
      const timer = setTimeout(() => setPriceFlash(null), 500);
      return () => clearTimeout(timer);
    }
    if (marketTicker) {
      setPrevPrice(marketTicker.price);
    }
  }, [marketTicker?.price, prevPrice]);

  if (!marketTicker) {
    return (
      <Card className={cn("card-professional", className)}>
        <CardContent className={cn(compact ? "p-3" : "p-4")}>
          <div className="text-center text-gray-400">
            <div className="text-sm">Loading market data...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const isPositive = marketTicker.change >= 0;
  const changeColor = isPositive ? 'text-green-400' : 'text-red-400';
  const changeBgColor = isPositive ? 'bg-green-500/10' : 'bg-red-500/10';

  if (compact) {
    return (
      <motion.div
        className={cn(
          "flex items-center gap-4 p-3 bg-gray-800/50 rounded-lg border border-gray-700",
          priceFlash === 'up' && "bg-green-500/20 border-green-500/50",
          priceFlash === 'down' && "bg-red-500/20 border-red-500/50",
          className
        )}
        animate={{
          scale: priceFlash ? 1.02 : 1,
        }}
        transition={{ duration: 0.2 }}
      >
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            className="h-6 w-6 p-0 text-gray-400 hover:text-yellow-400"
          >
            <Star className="h-3 w-3" />
          </Button>
          <span className="font-bold text-white text-sm">{selectedSymbol}</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="font-mono font-bold text-white text-lg">
              ${formatNumber(marketTicker.price, { decimals: 2 })}
            </div>
            <div className={cn("text-xs font-medium", changeColor)}>
              {isPositive ? '+' : ''}{formatNumber(marketTicker.change, { decimals: 2 })}
              {' '}({formatPercentage(marketTicker.changePercent)})
            </div>
          </div>

          <div className={cn("p-1 rounded", changeBgColor)}>
            {isPositive ? (
              <TrendingUp className={cn("h-4 w-4", changeColor)} />
            ) : marketTicker.change < 0 ? (
              <TrendingDown className={cn("h-4 w-4", changeColor)} />
            ) : (
              <Minus className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <Card className={cn("card-professional", className)}>
      <CardContent className="p-0">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant="ghost"
                className="h-8 w-8 p-0 text-gray-400 hover:text-yellow-400"
              >
                <Star className="h-4 w-4" />
              </Button>
              <div>
                <h3 className="font-bold text-white text-lg">{selectedSymbol}</h3>
                <div className="text-xs text-gray-400">Bitcoin / Tether USD</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs text-gray-400 hover:text-white"
              >
                <Search className="h-3 w-3 mr-1" />
                Markets
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0 text-gray-400 hover:text-white"
              >
                <ChevronDown className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>

        {/* Price Display */}
        <motion.div
          className={cn(
            "p-6 transition-colors duration-300",
            priceFlash === 'up' && "bg-green-500/5",
            priceFlash === 'down' && "bg-red-500/5"
          )}
          animate={{
            scale: priceFlash ? 1.01 : 1,
          }}
          transition={{ duration: 0.3 }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Main Price */}
            <div className="space-y-2">
              <div className="flex items-baseline gap-3">
                <motion.div
                  key={marketTicker.price}
                  initial={{ scale: 1.1 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.2 }}
                  className="font-mono font-bold text-white text-3xl"
                >
                  ${formatNumber(marketTicker.price, { decimals: 2 })}
                </motion.div>
                <div className={cn("flex items-center gap-1 px-2 py-1 rounded text-sm font-medium", changeBgColor, changeColor)}>
                  {isPositive ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : marketTicker.change < 0 ? (
                    <TrendingDown className="h-3 w-3" />
                  ) : (
                    <Minus className="h-3 w-3" />
                  )}
                  {isPositive ? '+' : ''}{formatNumber(marketTicker.change, { decimals: 2 })}
                </div>
              </div>

              <div className={cn("text-lg font-medium", changeColor)}>
                {isPositive ? '+' : ''}{formatPercentage(marketTicker.changePercent)} (24h)
              </div>
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-gray-400 mb-1">24h High</div>
                <div className="font-mono font-bold text-white">
                  ${formatNumber(marketTicker.high24h, { decimals: 2 })}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">24h Low</div>
                <div className="font-mono font-bold text-white">
                  ${formatNumber(marketTicker.low24h, { decimals: 2 })}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                  <Volume2 className="h-3 w-3" />
                  24h Volume
                </div>
                <div className="font-mono font-bold text-white">
                  {formatNumber(marketTicker.volume, { compact: true })}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Last Update
                </div>
                <div className="text-xs text-gray-300">
                  {new Date(marketTicker.lastUpdate).toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Market Stats Bar */}
        <div className="px-4 py-3 bg-gray-800/50 border-t border-gray-700">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <div className="text-gray-400">
                Market Cap: <span className="text-white font-mono">$1.23T</span>
              </div>
              <div className="text-gray-400">
                Circulating: <span className="text-white font-mono">19.8M BTC</span>
              </div>
            </div>
            <div className="text-gray-400">
              Powered by CoinGecko API
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Demo data generator for testing
export function useMarketTickerDemo() {
  const updateMarketTicker = useTradingStore(state => state.updateMarketTicker);
  const selectedSymbol = useSelectedSymbol();

  useEffect(() => {
    const generateMarketTicker = () => {
      const basePrice = 50000 + Math.random() * 20000;
      const change = (Math.random() - 0.5) * 2000;
      const changePercent = (change / basePrice) * 100;

      updateMarketTicker({
        symbol: selectedSymbol,
        price: basePrice + change,
        change,
        changePercent,
        volume: Math.random() * 1000000000,
        high24h: basePrice + Math.random() * 3000,
        low24h: basePrice - Math.random() * 3000,
        lastUpdate: Date.now(),
      });
    };

    // Initial data
    generateMarketTicker();

    // Update every 3 seconds
    const interval = setInterval(generateMarketTicker, 3000);
    return () => clearInterval(interval);
  }, [selectedSymbol, updateMarketTicker]);
}