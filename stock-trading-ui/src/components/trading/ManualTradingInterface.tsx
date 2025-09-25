'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Search, TrendingUp, TrendingDown, Calculator } from 'lucide-react';
import { Stock, Order } from '@/lib/types/trading';
import { cn } from '@/lib/utils';

interface ManualTradingInterfaceProps {
  selectedStock?: Stock | null;
  onStockChange?: (stock: Stock) => void;
  className?: string;
}

export function ManualTradingInterface({
  selectedStock,
  onStockChange,
  className
}: ManualTradingInterfaceProps) {
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [priceType, setPriceType] = useState<'market' | 'limit'>('market');
  const [quantity, setQuantity] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [stockQuery, setStockQuery] = useState<string>('');

  // 모의 종목 데이터
  const mockStocks = [
    { code: '005930', name: '삼성전자', currentPrice: 73000, changeRate: 1.5, changeAmount: 1000, volume: 15000000 },
    { code: '000660', name: 'SK하이닉스', currentPrice: 127500, changeRate: -2.1, changeAmount: -2700, volume: 8500000 },
    { code: '035420', name: 'NAVER', currentPrice: 185000, changeRate: 0.8, changeAmount: 1500, volume: 2100000 },
  ];

  const filteredStocks = mockStocks.filter(stock =>
    stock.name.includes(stockQuery) || stock.code.includes(stockQuery)
  );

  const handleStockSelect = (stock: Stock) => {
    onStockChange?.(stock);
    setStockQuery('');
  };

  const calculateTotal = () => {
    if (!quantity || !selectedStock) return 0;
    const orderPrice = priceType === 'market' ? selectedStock.currentPrice : (parseFloat(price) || 0);
    return parseInt(quantity) * orderPrice;
  };

  const handleSubmitOrder = () => {
    if (!selectedStock || !quantity) return;

    console.log('주문 제출:', {
      stock: selectedStock,
      orderType,
      priceType,
      quantity: parseInt(quantity),
      price: priceType === 'limit' ? parseFloat(price) : selectedStock.currentPrice,
      total: calculateTotal()
    });
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* 종목 검색 및 선택 */}
      <Card className="bg-[#2a2a2a] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Search className="w-5 h-5" />
            종목 검색 및 선택
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 검색 입력 */}
          <div className="relative">
            <Input
              type="text"
              value={stockQuery}
              onChange={(e) => setStockQuery(e.target.value)}
              placeholder="종목명 또는 코드를 입력하세요"
              className="bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500"
            />
            {stockQuery && filteredStocks.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-[#2a2a2a] border border-gray-600 rounded-md shadow-lg max-h-60 overflow-y-auto">
                {filteredStocks.map((stock) => (
                  <div
                    key={stock.code}
                    className="p-3 hover:bg-[#3a3a3a] cursor-pointer border-b border-gray-700 last:border-b-0"
                    onClick={() => handleStockSelect(stock)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-white">{stock.name}</div>
                        <div className="text-sm text-gray-400">{stock.code}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-white">
                          {stock.currentPrice.toLocaleString()}원
                        </div>
                        <div className={cn("text-sm",
                          stock.changeRate > 0 ? "text-profit-foreground" : "text-loss-foreground"
                        )}>
                          {stock.changeRate > 0 ? '+' : ''}{stock.changeRate}%
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 선택된 종목 정보 */}
          {selectedStock && (
            <div className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-600">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">{selectedStock.name}</h3>
                  <p className="text-sm text-gray-400">{selectedStock.code}</p>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-white">
                    {selectedStock.currentPrice.toLocaleString()}원
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={selectedStock.changeRate > 0 ? "destructive" : "default"}>
                      {selectedStock.changeRate > 0 ? '+' : ''}{selectedStock.changeRate}%
                    </Badge>
                    <span className={cn("text-sm",
                      selectedStock.changeAmount > 0 ? "text-profit-foreground" : "text-loss-foreground"
                    )}>
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-700">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">거래량:</span>
                  <span className="text-white">{selectedStock.volume?.toLocaleString() || '0'}</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 주문 인터페이스 */}
      <Card className="bg-[#2a2a2a] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calculator className="w-5 h-5" />
            주문 설정
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 매수/매도 선택 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">주문 유형</label>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant={orderType === 'buy' ? 'default' : 'outline'}
                onClick={() => setOrderType('buy')}
                className={cn(
                  'h-12 transition-all duration-200',
                  orderType === 'buy'
                    ? 'bg-profit hover:bg-profit/90 text-white shadow-lg shadow-profit/20'
                    : 'border-profit text-profit-foreground hover:bg-profit/10'
                )}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                매수
              </Button>
              <Button
                variant={orderType === 'sell' ? 'default' : 'outline'}
                onClick={() => setOrderType('sell')}
                className={cn(
                  'h-12 transition-all duration-200',
                  orderType === 'sell'
                    ? 'bg-loss hover:bg-loss/90 text-white shadow-lg shadow-loss/20'
                    : 'border-loss text-loss-foreground hover:bg-loss/10'
                )}
              >
                <TrendingDown className="w-4 h-4 mr-2" />
                매도
              </Button>
            </div>
          </div>

          {/* 주문 방식 선택 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">주문 방식</label>
            <Select value={priceType} onValueChange={(value: 'market' | 'limit') => setPriceType(value)}>
              <SelectTrigger className="bg-[#1a1a1a] border-gray-600 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#2a2a2a] border-gray-600">
                <SelectItem value="market">시장가</SelectItem>
                <SelectItem value="limit">지정가</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 수량 입력 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">주문 수량</label>
            <Input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="수량을 입력하세요"
              className="bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500"
            />
          </div>

          {/* 가격 입력 (지정가일 때만) */}
          {priceType === 'limit' && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">지정 가격</label>
              <Input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="가격을 입력하세요"
                className="bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500"
              />
            </div>
          )}

          {/* 주문 요약 */}
          {selectedStock && quantity && (
            <div className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-600">
              <h4 className="font-medium text-white mb-3">주문 요약</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">종목:</span>
                  <span className="text-white">{selectedStock.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">주문 유형:</span>
                  <span className={orderType === 'buy' ? 'text-profit-foreground' : 'text-loss-foreground'}>
                    {orderType === 'buy' ? '매수' : '매도'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">수량:</span>
                  <span className="text-white">{parseInt(quantity).toLocaleString()}주</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">가격:</span>
                  <span className="text-white">
                    {priceType === 'market' ? '시장가' : `${parseFloat(price || '0').toLocaleString()}원`}
                  </span>
                </div>
                <div className="flex justify-between font-medium pt-2 border-t border-gray-700">
                  <span className="text-gray-300">예상 총액:</span>
                  <span className="text-white">{calculateTotal().toLocaleString()}원</span>
                </div>
              </div>
            </div>
          )}

          {/* 주문 실행 버튼 */}
          <Button
            onClick={handleSubmitOrder}
            disabled={!selectedStock || !quantity}
            className={cn(
              'w-full h-12 font-semibold text-lg transition-all duration-200',
              orderType === 'buy'
                ? 'bg-profit hover:bg-profit/90 text-white shadow-lg shadow-profit/20'
                : 'bg-loss hover:bg-loss/90 text-white shadow-lg shadow-loss/20',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {orderType === 'buy' ? '매수 주문' : '매도 주문'} 실행
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}