'use client';

/**
 * 주문 입력 폼 컴포넌트
 * 매수/매도 주문을 입력하고 실행하는 폼
 */

import { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
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
import { TrendingUp, TrendingDown, AlertCircle, Loader2 } from 'lucide-react';
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

      <CardContent className="space-y-2 px-3 pb-3">
        {/* 매수/매도 탭 */}
        <Tabs value={orderSide} onValueChange={(v) => setOrderSide(v as 'buy' | 'sell')}>
          <TabsList className="grid w-full grid-cols-2 bg-[#2a2a2a]">
            <TabsTrigger
              value="buy"
              className="data-[state=active]:bg-red-500 data-[state=active]:text-white"
            >
              <TrendingUp className="w-4 h-4 mr-1" />
              매수
            </TabsTrigger>
            <TabsTrigger
              value="sell"
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
            >
              <TrendingDown className="w-4 h-4 mr-1" />
              매도
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

        {/* 주문 유형 선택 */}
        <div className="space-y-1">
          <Label className="text-gray-300 text-[10px]">주문 유형</Label>
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

        {/* 가격 입력 (지정가만) */}
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

        {/* 수량 입력 */}
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

        {/* 예상 금액 */}
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

        {/* 에러 메시지 */}
        {error && (
          <Alert variant="destructive" className="bg-red-900/20 border-red-500">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* 유효성 검증 메시지 */}
        {validationError && (
          <Alert className="bg-yellow-900/20 border-yellow-500">
            <AlertCircle className="h-4 w-4 text-yellow-500" />
            <AlertDescription className="text-yellow-500">{validationError}</AlertDescription>
          </Alert>
        )}

        {/* Order Book - Show only for limit orders */}
        {orderType === OrderType.LIMIT && currentPrice > 0 && (
          <div className="border-t border-gray-700 pt-2 mt-2">
            {/* <div className="flex items-center justify-between mb-1">
              <Label className="text-gray-300 text-[10px]">호가창--</Label>
              <Badge variant="outline" className="text-[9px] px-1 py-0">
                실시간
              </Badge>
            </div> */}
            <OrderBook stockCode={stockCode} currentPrice={currentPrice} />
          </div>
        )}

        {/* 주문 버튼 */}
        <Button
          onClick={handleSubmit}
          disabled={!!validationError || isLoading}
          size="sm"
          className={cn(
            'w-full font-bold h-9 text-sm',
            orderSide === 'buy'
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-blue-500 hover:bg-blue-600'
          )}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              주문 처리 중...
            </>
          ) : (
            <>
              {orderSide === 'buy' ? '매수' : '매도'} 주문
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
