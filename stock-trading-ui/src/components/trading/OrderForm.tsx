'use client';

/**
 * 주문 입력 폼 컴포넌트
 * 매수/매도 주문을 입력하고 실행하는 폼
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import {
  OrderType,
  OrderSide,
  getTickSize,
  adjustPriceToTick,
  calculateNetBuyAmount,
  calculateNetSellAmount,
  getOrderTypeName,
} from '@/lib/types/order';
import { useOrders } from '@/hooks/useOrders';
import { AlertCircle, Loader2 } from 'lucide-react';
import { OrderBook } from './OrderBook';

interface OrderFormProps {
  stockCode: string;
  stockName: string;
  currentPrice?: number;
  availableCash?: number;      // 매수 가능 금액
  availableQuantity?: number;  // 매도 가능 수량
  onOrderSuccess?: () => void;
  className?: string;
}

export function OrderForm({
  stockCode,
  stockName,
  currentPrice = 0,
  availableCash = 0,
  availableQuantity = 0,
  onOrderSuccess,
  className,
}: OrderFormProps) {
  // 상태
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');
  const [orderType, setOrderType] = useState<OrderType>(OrderType.LIMIT);
  const [quantity, setQuantity] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [showConfirm, setShowConfirm] = useState(false);

  // API 훅
  const { placeBuyOrder, placeSellOrder, isLoading, error } = useOrders();

  // 현재가로 가격 초기화
  useEffect(() => {
    if (currentPrice > 0 && orderType === OrderType.LIMIT) {
      setPrice(currentPrice.toString());
    }
  }, [currentPrice, orderType]);

  // 호가 단위
  const tickSize = useMemo(() => {
    const priceNum = parseInt(price) || currentPrice;
    return getTickSize(priceNum);
  }, [price, currentPrice]);

  // 주문 가격 (조정됨)
  const adjustedPrice = useMemo(() => {
    if (orderType === OrderType.MARKET) return 0;
    const priceNum = parseInt(price) || 0;
    return adjustPriceToTick(priceNum);
  }, [price, orderType]);

  // 주문 수량
  const orderQuantity = useMemo(() => {
    return parseInt(quantity) || 0;
  }, [quantity]);

  // 예상 금액 계산
  const estimatedAmount = useMemo(() => {
    if (orderQuantity <= 0) return 0;

    const priceToUse = orderType === OrderType.MARKET ? currentPrice : adjustedPrice;

    if (orderSide === 'buy') {
      return calculateNetBuyAmount(orderQuantity, priceToUse);
    } else {
      return calculateNetSellAmount(orderQuantity, priceToUse);
    }
  }, [orderSide, orderType, orderQuantity, adjustedPrice, currentPrice]);

  // 최대 매수 가능 수량
  const maxBuyQuantity = useMemo(() => {
    if (!currentPrice || currentPrice <= 0) return 0;
    // 수수료 고려 (약 0.015%)
    const effectivePrice = currentPrice * 1.00015;
    return Math.floor(availableCash / effectivePrice);
  }, [availableCash, currentPrice]);

  // 주문 유효성 검증
  const validationError = useMemo(() => {
    if (!orderQuantity || orderQuantity <= 0) {
      return '수량을 입력해주세요';
    }

    if (orderType !== OrderType.MARKET && (!adjustedPrice || adjustedPrice <= 0)) {
      return '가격을 입력해주세요';
    }

    if (orderSide === 'buy') {
      if (orderQuantity > maxBuyQuantity) {
        return `매수 가능 수량을 초과했습니다 (최대: ${maxBuyQuantity.toLocaleString()}주)`;
      }
      if (estimatedAmount > availableCash) {
        return '매수 가능 금액을 초과했습니다';
      }
    } else {
      if (orderQuantity > availableQuantity) {
        return `매도 가능 수량을 초과했습니다 (최대: ${availableQuantity.toLocaleString()}주)`;
      }
    }

    return null;
  }, [orderQuantity, adjustedPrice, orderType, orderSide, maxBuyQuantity, estimatedAmount, availableCash, availableQuantity]);

  // 가격 조정 (호가 단위)
  const adjustPriceInput = (value: string) => {
    const num = parseInt(value) || 0;
    if (num > 0) {
      const adjusted = adjustPriceToTick(num);
      setPrice(adjusted.toString());
    } else {
      setPrice('');
    }
  };

  // 수량 증감
  const changeQuantity = (delta: number) => {
    const current = orderQuantity || 0;
    const newQty = Math.max(0, current + delta);
    setQuantity(newQty > 0 ? newQty.toString() : '');
  };

  // 가격 증감 (호가 단위)
  const changePrice = (delta: number) => {
    const current = adjustedPrice || currentPrice;
    const newPrice = current + (delta * tickSize);
    if (newPrice > 0) {
      setPrice(newPrice.toString());
    }
  };

  const handleSelectPrice = useCallback((priceValue: number, side: 'ask' | 'bid') => {
    setOrderSide(side === 'ask' ? 'sell' : 'buy');
    setOrderType(OrderType.LIMIT);
    setPrice(priceValue.toString());
  }, []);

  // 주문 실행
  const handleSubmit = async () => {
    if (validationError) return;

    try {
      const request = {
        stock_code: stockCode,
        stock_name: stockName,
        order_type: orderType,
        quantity: orderQuantity,
        price: orderType === OrderType.MARKET ? 0 : adjustedPrice,
      };

      if (orderSide === 'buy') {
        await placeBuyOrder(request);
      } else {
        await placeSellOrder(request);
      }

      // 성공 시 초기화
      setQuantity('');
      setShowConfirm(false);

      if (onOrderSuccess) {
        onOrderSuccess();
      }
    } catch (err) {
      console.error('주문 실패:', err);
    }
  };

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
      <CardHeader className="pb-2 px-3 pt-3">
        <CardTitle className="text-white text-sm">주문하기</CardTitle>
      </CardHeader>

      <CardContent className="px-3 pb-3">
        <div className="grid grid-cols-2 gap-3 items-start">
          <div className="bg-[#1f1f20] border border-gray-700 rounded-lg p-2 h-full">
            {currentPrice > 0 ? (
              <OrderBook
                stockCode={stockCode}
                currentPrice={currentPrice}
                onSelectPrice={handleSelectPrice}
              />
            ) : (
              <div className="text-xs text-gray-400 flex items-center justify-center h-full text-center px-2">
                호가 데이터를 불러오는 중입니다.
              </div>
            )}
          </div>

          <div className="flex flex-col space-y-2">
            <Tabs value={orderSide} onValueChange={(v) => setOrderSide(v as 'buy' | 'sell')}>
              <TabsList className="grid w-full grid-cols-2 bg-[#2a2a2a] rounded-md overflow-hidden">
                <TabsTrigger
                  value="buy"
                  className="data-[state=active]:bg-red-500 data-[state=active]:text-white flex items-center justify-center gap-1"
                >
                  <span className="text-white font-extrabold text-sm">＋</span>
                  <span className="text-xs sm:text-[13px] text-white">매수 <span className="text-[10px] text-white/80">(BUY)</span></span>
                </TabsTrigger>
                <TabsTrigger
                  value="sell"
                  className="data-[state=active]:bg-blue-500 data-[state=active]:text-white flex items-center justify-center gap-1"
                >
                  <span className="text-white font-extrabold text-sm">－</span>
                  <span className="text-xs sm:text-[13px] text-white">매도 <span className="text-[10px] text-white/80">(SELL)</span></span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="buy" className="space-y-2 mt-2">
                <div className="text-[10px] text-gray-400">
                  매수 가능: <span className="text-white font-medium">{availableCash.toLocaleString()}원</span>
                  {maxBuyQuantity > 0 && (
                    <span className="ml-2">
                      (최대 {maxBuyQuantity.toLocaleString()}주)
                    </span>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="sell" className="space-y-2 mt-2">
                <div className="text-[10px] text-gray-400">
                  매도 가능: <span className="text-white font-medium">{availableQuantity.toLocaleString()}주</span>
                </div>
              </TabsContent>
            </Tabs>

            <div className="space-y-1">
              <Label className="text-gray-300 text-[14px]">주문 유형</Label>
              <div className="grid grid-cols-2 gap-1">
                <Button
                  type="button"
                  variant={orderType === OrderType.LIMIT ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setOrderType(OrderType.LIMIT)}
                  className={cn(
                    'text-xs h-7 py-1',
                    orderType === OrderType.LIMIT
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-[#2a2a2a] text-gray-300 hover:bg-gray-700'
                  )}
                >
                  {getOrderTypeName(OrderType.LIMIT)}
                </Button>
                <Button
                  type="button"
                  variant={orderType === OrderType.MARKET ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setOrderType(OrderType.MARKET)}
                  className={cn(
                    'text-xs h-7 py-1',
                    orderType === OrderType.MARKET
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-[#2a2a2a] text-gray-300 hover:bg-gray-700'
                  )}
                >
                  {getOrderTypeName(OrderType.MARKET)}
                </Button>
              </div>
            </div>

            {orderType === OrderType.LIMIT && (
              <div className="space-y-1">
                <Label className="text-gray-300 text-[10px]">
                  주문 가격
                  <span className="ml-2 text-gray-500">(호가단위: {tickSize}원)</span>
                </Label>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => changePrice(-1)}
                    className="bg-[#2a2a2a] text-gray-300 hover:bg-gray-700 h-8 w-8 p-0"
                  >
                    -
                  </Button>
                  <Input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    onBlur={(e) => adjustPriceInput(e.target.value)}
                    placeholder="가격 입력"
                    className="bg-[#2a2a2a] text-white border-gray-600 text-right h-8 text-sm"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => changePrice(1)}
                    className="bg-[#2a2a2a] text-gray-300 hover:bg-gray-700 h-8 w-8 p-0"
                  >
                    +
                  </Button>
                </div>
                {adjustedPrice > 0 && adjustedPrice !== parseInt(price) && (
                  <p className="text-[10px] text-yellow-500">
                    호가 단위 조정: {adjustedPrice.toLocaleString()}원
                  </p>
                )}
              </div>
            )}

            <div className="space-y-1">
              <Label className="text-gray-300 text-[10px]">주문 수량</Label>
              <div className="flex gap-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => changeQuantity(-10)}
                  className="bg-[#2a2a2a] text-gray-300 hover:bg-gray-700 h-8 px-2 text-xs"
                >
                  -10
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => changeQuantity(-1)}
                  className="bg-[#2a2a2a] text-gray-300 hover:bg-gray-700 h-8 px-2 text-xs"
                >
                  -1
                </Button>
                <Input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="수량"
                  className="bg-[#2a2a2a] text-white border-gray-600 text-right h-8 text-sm"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => changeQuantity(1)}
                  className="bg-[#2a2a2a] text-gray-300 hover:bg-gray-700 h-8 px-2 text-xs"
                >
                  +1
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => changeQuantity(10)}
                  className="bg-[#2a2a2a] text-gray-300 hover:bg-gray-700 h-8 px-2 text-xs"
                >
                  +10
                </Button>
              </div>
            </div>

            {orderQuantity > 0 && estimatedAmount > 0 && (
              <div className="bg-[#2a2a2a] rounded-lg p-3 space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">예상 {orderSide === 'buy' ? '매수' : '매도'} 금액</span>
                  <span className="text-white font-medium">
                    {estimatedAmount.toLocaleString()}원
                  </span>
                </div>
              </div>
            )}

            {error && (
              <Alert variant="destructive" className="bg-red-900/20 border-red-500">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {validationError && (
              <Alert className="bg-yellow-900/20 border-yellow-500">
                <AlertCircle className="h-4 w-4 text-yellow-500" />
                <AlertDescription className="text-yellow-500">{validationError}</AlertDescription>
              </Alert>
            )}

            <Button
              onClick={handleSubmit}
              disabled={!!validationError || isLoading}
              size="sm"
              className={cn(
                'w-full font-bold h-9 text-sm text-white transition-colors duration-150 shadow-sm',
                orderSide === 'buy'
                  ? 'bg-red-500 hover:bg-red-400 focus-visible:ring-red-200'
                  : 'bg-blue-500 hover:bg-blue-400 focus-visible:ring-blue-200'
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  주문 처리 중...
                </>
              ) : orderSide === 'buy' ? (
                <span className="flex items-center justify-center text-sm">
                  <span className="font-extrabold text-white text-base mr-2 drop-shadow">＋</span>매수(BUY) 주문
                </span>
              ) : (
                <span className="flex items-center justify-center text-sm">
                  <span className="font-extrabold text-white text-base mr-2 drop-shadow">－</span>매도(SELL) 주문
                </span>
              )}
            </Button>
          </div>
        </div>
      </CardContent>

    </Card>
  );
}
