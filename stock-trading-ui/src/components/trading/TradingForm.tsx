'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn, formatNumber } from '@/lib/utils';
import { useTradingStore, useSelectedSymbol, useMarketTicker, usePortfolio } from '@/stores/tradingStore';
import {
  ShoppingCart,
  DollarSign,
  Percent,
  Calculator,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Check
} from 'lucide-react';

interface TradingFormData {
  orderType: 'market' | 'limit';
  quantity: number;
  price?: number;
}

interface TradingFormProps {
  className?: string;
}

export function TradingForm({ className }: TradingFormProps) {
  const [activeTab, setActiveTab] = useState<'buy' | 'sell'>('buy');
  const [percentage, setPercentage] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedSymbol = useSelectedSymbol();
  const marketTicker = useMarketTicker(selectedSymbol);
  const portfolio = usePortfolio();
  const addOrder = useTradingStore(state => state.addOrder);

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<TradingFormData>({
    defaultValues: {
      orderType: 'limit',
      quantity: 0,
      price: marketTicker?.price || 0,
    }
  });

  const watchedOrderType = watch('orderType');
  const watchedQuantity = watch('quantity');
  const watchedPrice = watch('price');

  // Calculate order total
  const orderTotal = watchedQuantity * (watchedPrice || marketTicker?.price || 0);
  const availableCash = portfolio?.availableCash || 0;
  const estimatedFee = orderTotal * 0.001; // 0.1% fee
  const totalCost = orderTotal + estimatedFee;

  // Calculate available quantity for selling
  const position = portfolio?.positions?.find(p => p.symbol === selectedSymbol);
  const availableQuantity = position?.quantity || 0;

  const onSubmit = async (data: TradingFormData) => {
    setIsSubmitting(true);

    try {
      // Simulate order submission
      await new Promise(resolve => setTimeout(resolve, 1000));

      addOrder({
        symbol: selectedSymbol,
        type: activeTab,
        orderType: data.orderType,
        quantity: data.quantity,
        price: data.orderType === 'limit' ? data.price : undefined,
        status: 'pending',
      });

      // Reset form
      setValue('quantity', 0);
      setPercentage(null);
    } catch (error) {
      console.error('Order submission failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePercentageClick = (percent: number) => {
    setPercentage(percent);

    if (activeTab === 'buy') {
      const maxSpendable = availableCash * (percent / 100);
      const price = watchedPrice || marketTicker?.price || 0;
      const maxQuantity = price > 0 ? maxSpendable / price : 0;
      setValue('quantity', Math.floor(maxQuantity * 1000) / 1000);
    } else {
      const sellQuantity = availableQuantity * (percent / 100);
      setValue('quantity', Math.floor(sellQuantity * 1000) / 1000);
    }
  };

  return (
    <Card className={cn("card-professional", className)}>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-white">
          <div className="icon-bg-blue">
            <ShoppingCart className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-bold">Trade {selectedSymbol}</div>
            <div className="text-xs text-gray-400 font-normal">
              {marketTicker ? `$${formatNumber(marketTicker.price, { decimals: 2 })}` : 'Loading...'}
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Buy/Sell Tabs */}
        <div className="flex bg-gray-800 rounded-lg p-1">
          <Button
            className={cn(
              "flex-1 h-9 text-sm font-medium transition-all",
              activeTab === 'buy'
                ? "bg-green-600 text-white shadow-sm hover:bg-green-700"
                : "text-gray-400 hover:text-white hover:bg-gray-700"
            )}
            onClick={() => setActiveTab('buy')}
          >
            <TrendingUp className="h-3 w-3 mr-2" />
            Buy
          </Button>
          <Button
            className={cn(
              "flex-1 h-9 text-sm font-medium transition-all",
              activeTab === 'sell'
                ? "bg-red-600 text-white shadow-sm hover:bg-red-700"
                : "text-gray-400 hover:text-white hover:bg-gray-700"
            )}
            onClick={() => setActiveTab('sell')}
          >
            <TrendingDown className="h-3 w-3 mr-2" />
            Sell
          </Button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Order Type */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-300">Order Type</Label>
            <Select
              value={watchedOrderType}
              onValueChange={(value: 'market' | 'limit') => setValue('orderType', value)}
            >
              <SelectTrigger className="input-professional">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="market">Market Order</SelectItem>
                <SelectItem value="limit">Limit Order</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Price (for limit orders) */}
          {watchedOrderType === 'limit' && (
            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-300">Price (USD)</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="number"
                  step="0.01"
                  className="input-professional pl-10"
                  placeholder="0.00"
                  {...register('price', {
                    required: watchedOrderType === 'limit',
                    min: 0.01
                  })}
                />
              </div>
              {errors.price && (
                <p className="text-xs text-red-400">Price is required</p>
              )}
            </div>
          )}

          {/* Quantity */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-300">
              Quantity
              {activeTab === 'sell' && (
                <span className="text-xs text-gray-400 ml-2">
                  (Available: {formatNumber(availableQuantity, { decimals: 6 })})
                </span>
              )}
            </Label>
            <Input
              type="number"
              step="0.000001"
              className="input-professional"
              placeholder="0.000000"
              {...register('quantity', {
                required: true,
                min: 0.000001,
                max: activeTab === 'sell' ? availableQuantity : undefined
              })}
            />
            {errors.quantity && (
              <p className="text-xs text-red-400">
                {activeTab === 'sell' ? 'Insufficient balance' : 'Quantity is required'}
              </p>
            )}
          </div>

          {/* Percentage Buttons */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-300">Quick Select</Label>
            <div className="grid grid-cols-4 gap-2">
              {[25, 50, 75, 100].map((percent) => (
                <Button
                  key={percent}
                  type="button"
                  size="sm"
                  variant="outline"
                  className={cn(
                    "h-8 text-xs border-gray-600 transition-all",
                    percentage === percent
                      ? "bg-blue-600 border-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-700 hover:border-gray-500"
                  )}
                  onClick={() => handlePercentageClick(percent)}
                >
                  <Percent className="h-3 w-3 mr-1" />
                  {percent}%
                </Button>
              ))}
            </div>
          </div>

          {/* Order Summary */}
          <div className="bg-gray-800 rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <Calculator className="h-4 w-4 text-blue-400" />
              <span className="text-sm font-medium text-white">Order Summary</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Total</span>
                <span className="text-white font-mono">
                  ${formatNumber(orderTotal, { decimals: 2 })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Est. Fee (0.1%)</span>
                <span className="text-white font-mono">
                  ${formatNumber(estimatedFee, { decimals: 2 })}
                </span>
              </div>
              <div className="flex justify-between border-t border-gray-700 pt-2">
                <span className="text-gray-300 font-medium">
                  {activeTab === 'buy' ? 'Total Cost' : 'Total Receive'}
                </span>
                <span className="text-white font-mono font-bold">
                  ${formatNumber(totalCost, { decimals: 2 })}
                </span>
              </div>
            </div>

            {/* Validation Messages */}
            {activeTab === 'buy' && totalCost > availableCash && (
              <div className="flex items-center gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-xs">
                <AlertTriangle className="h-3 w-3" />
                Insufficient funds. Available: ${formatNumber(availableCash, { decimals: 2 })}
              </div>
            )}

            {activeTab === 'sell' && watchedQuantity > availableQuantity && (
              <div className="flex items-center gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-xs">
                <AlertTriangle className="h-3 w-3" />
                Insufficient balance. Available: {formatNumber(availableQuantity, { decimals: 6 })}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className={cn(
              "w-full h-12 font-bold text-white transition-all duration-200",
              activeTab === 'buy'
                ? "buy-button-primary hover:scale-105"
                : "sell-button-primary hover:scale-105"
            )}
            disabled={
              isSubmitting ||
              !watchedQuantity ||
              (activeTab === 'buy' && totalCost > availableCash) ||
              (activeTab === 'sell' && watchedQuantity > availableQuantity)
            }
          >
            {isSubmitting ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4" />
                {activeTab === 'buy' ? 'Place Buy Order' : 'Place Sell Order'}
              </div>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}