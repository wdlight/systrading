'use client';

import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ShoppingCart,
  DollarSign,
  Calculator,
  AlertTriangle,
  CheckCircle,
  Info,
  Percent,
  Target,
  Zap,
  Clock
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  KoreanStock,
  KoreanTradingOrder,
  formatStockPrice,
  formatKoreanWon
} from '@/lib/types/korean-stocks';

interface KoreanTradingFormProps {
  className?: string;
  stock?: KoreanStock | null;
  onOrder?: (order: Partial<KoreanTradingOrder>) => void;
}

type OrderType = '지정가' | '시장가' | '조건부지정가';
type OrderSide = '매수' | '매도';

interface OrderCalculation {
  quantity: number;
  price: number;
  orderAmount: number;
  commission: number;
  tax: number;
  totalAmount: number;
  availableAfterOrder: number;
}

export function KoreanTradingForm({ className, stock, onOrder }: KoreanTradingFormProps) {
  const [activeTab, setActiveTab] = useState<OrderSide>('매수');
  const [orderType, setOrderType] = useState<OrderType>('지정가');
  const [price, setPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [orderAmount, setOrderAmount] = useState('');
  const [useAllCash, setUseAllCash] = useState(false);
  const [useAllShares, setUseAllShares] = useState(false);

  // Mock user data
  const mockUserData = {
    cash: 5000000, // 5백만원
    holdings: stock ? {
      [stock.code]: {
        quantity: 100,
        avgPrice: stock.currentPrice * 0.9,
        value: stock.currentPrice * 100
      }
    } : {}
  };

  const currentHolding = stock ? mockUserData.holdings[stock.code] : null;
  
  useEffect(() => {
    if (stock) {
      setPrice(stock.currentPrice.toString());
      setQuantity('');
      setOrderAmount('');
    }
  }, [stock]);


  // Calculate order details
  const orderCalculation = useMemo((): OrderCalculation | null => {
    if (!stock) return null;

    const orderPrice = orderType === '시장가' ? stock.currentPrice : (parseFloat(price) || 0);
    const orderQuantity = parseInt(quantity) || 0;
    const baseAmount = orderPrice * orderQuantity;

    if (orderQuantity <= 0 || orderPrice <= 0) {
      return null;
    }
    
    const commissionRate = 0.00015; // 0.015%
    const taxRate = activeTab === '매도' ? 0.0023 : 0; // 0.23%
    
    const commission = baseAmount * commissionRate;
    const tax = baseAmount * taxRate;
    
    let totalAmount = 0;
    if (activeTab === '매수') {
      totalAmount = baseAmount + commission;
    } else { // 매도
      totalAmount = baseAmount - commission - tax;
    }

    const availableAfterOrder = activeTab === '매수' 
      ? mockUserData.cash - totalAmount 
      : mockUserData.cash + totalAmount;

    return {
      quantity: orderQuantity,
      price: orderPrice,
      orderAmount: baseAmount,
      commission,
      tax,
      totalAmount,
      availableAfterOrder
    };
  }, [price, quantity, orderType, activeTab, stock, mockUserData.cash]);

  const handleOrder = () => {
    if (!stock || !orderCalculation) return;
    
    const order: Partial<KoreanTradingOrder> = {
      stockCode: stock.code,
      stockName: stock.name,
      orderType: orderType,
      orderSide: activeTab,
      quantity: orderCalculation.quantity,
      price: orderCalculation.price,
      orderTime: new Date().toISOString(),
    };
    console.log("Placing Order:", order);
    onOrder?.(order);
  };

  const renderTabButton = (side: OrderSide, label: string) => (
    <Button
      onClick={() => setActiveTab(side)}
      className={cn(
        'flex-1 rounded-md text-base font-bold',
        activeTab === side
          ? (side === '매수' ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white')
          : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
      )}
    >
      {label}
    </Button>
  );

  const renderOrderTypeButton = (type: OrderType) => (
    <Button
      key={type}
      onClick={() => setOrderType(type)}
      variant={orderType === type ? 'default' : 'outline'}
      size="sm"
      className={cn(
        'text-xs h-7',
        orderType === type && 'bg-gray-500 border-gray-400'
      )}
    >
      {type}
    </Button>
  );

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700 text-white', className)}>
      <CardHeader className="p-4">
        <div className="flex gap-2">
          {renderTabButton('매수', '매수')}
          {renderTabButton('매도', '매도')}
        </div>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
        {/* Order Type Selection */}
        <div className="flex items-center justify-center gap-2">
          {['지정가', '시장가', '조건부지정가'].map(type => renderOrderTypeButton(type as OrderType))}
        </div>

        {/* Input Fields */}
        <div className="space-y-4">
          {orderType !== '시장가' && (
            <div className="grid gap-2">
              <Label htmlFor="price" className="text-gray-400">주문단가</Label>
              <Input 
                id="price" 
                type="number" 
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="주문 가격 입력"
                className="bg-gray-800 border-gray-600 text-white text-right"
              />
            </div>
          )}
          <div className="grid gap-2">
            <Label htmlFor="quantity" className="text-gray-400">주문수량</Label>
            <Input 
              id="quantity" 
              type="number" 
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="주문 수량 입력"
              className="bg-gray-800 border-gray-600 text-white text-right"
            />
          </div>
        </div>

        <Separator className="bg-gray-700" />

        {/* Calculation Details */}
        {orderCalculation && (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">주문금액</span>
              <span>{formatKoreanWon(orderCalculation.orderAmount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">수수료</span>
              <span>{formatKoreanWon(orderCalculation.commission)}</span>
            </div>
            {activeTab === '매도' && (
              <div className="flex justify-between">
                <span className="text-gray-400">세금</span>
                <span>{formatKoreanWon(orderCalculation.tax)}</span>
              </div>
            )}
            <Separator className="bg-gray-700 my-1" />
            <div className="flex justify-between font-bold text-base">
              <span className="text-gray-300">총 {activeTab === '매수' ? '정산금액' : '예상금액'}</span>
              <span className={activeTab === '매수' ? 'text-red-500' : 'text-blue-500'}>
                {formatKoreanWon(orderCalculation.totalAmount)}
              </span>
            </div>
          </div>
        )}

        {/* Action Button */}
        <Button 
          onClick={handleOrder}
          disabled={!stock || !orderCalculation}
          className={cn(
            'w-full text-lg font-bold h-12',
            activeTab === '매수' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
          )}
        >
          {stock ? `${stock.name} ${activeTab}` : '종목을 선택하세요'}
        </Button>

        {/* User Balance Info */}
        <div className="text-xs text-gray-400 text-center pt-2">
          <p>주문가능 현금: {formatKoreanWon(mockUserData.cash)}</p>
          {currentHolding && <p>보유수량: {currentHolding.quantity}주</p>}
        </div>
      </CardContent>
    </Card>
  );
}
