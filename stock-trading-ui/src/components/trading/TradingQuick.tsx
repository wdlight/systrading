'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Search, TrendingUp, TrendingDown, Settings } from 'lucide-react';
import { Stock, Order } from '@/lib/types/trading';
import { cn } from '@/lib/utils';

interface TradingQuickProps {
  selectedStock?: Stock;
  onOrderSubmit?: (order: Partial<Order>) => Promise<void>;
  className?: string;
}

export function TradingQuick({ selectedStock, onOrderSubmit, className }: TradingQuickProps) {
  const router = useRouter();
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [priceType, setPriceType] = useState<'market' | 'limit'>('market');
  const [quantity, setQuantity] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [stockQuery, setStockQuery] = useState<string>(selectedStock?.name || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 모의 종목 검색 데이터
  const mockStocks = [
    { code: '005930', name: '삼성전자', currentPrice: 73000, changeRate: 1.5 },
    { code: '000660', name: 'SK하이닉스', currentPrice: 127500, changeRate: -2.1 },
    { code: '035420', name: 'NAVER', currentPrice: 185000, changeRate: 0.8 },
  ];

  const filteredStocks = mockStocks.filter(stock =>
    stock.name.includes(stockQuery) || stock.code.includes(stockQuery)
  );

  const handleQuickTrade = async () => {
    if (!stockQuery || !quantity) return;

    setIsSubmitting(true);
    try {
      const orderData: Partial<Order> = {
        stockCode: selectedStock?.code || '005930',
        stockName: selectedStock?.name || stockQuery,
        type: orderType,
        orderType: priceType,
        quantity: parseInt(quantity),
        price: price ? parseFloat(price) : undefined,
        status: 'pending',
        timestamp: new Date(),
      };

      await onOrderSubmit?.(orderData);

      // 성공 시 폼 초기화
      setQuantity('');
      setPrice('');
    } catch (error) {
      console.error('주문 실행 실패:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const estimatedAmount = quantity && selectedStock?.currentPrice
    ? (parseInt(quantity) * (price ? parseFloat(price) : selectedStock.currentPrice)).toLocaleString()
    : '0';

  return (
    <div className={cn('space-y-4', className)}>
      <div className="text-sm text-gray-300">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          빠른 매매
        </h3>

        <div className="space-y-4">
          {/* 종목 검색 */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">
              종목 선택
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                type="text"
                value={stockQuery}
                onChange={(e) => setStockQuery(e.target.value)}
                placeholder="종목명 또는 코드 검색"
                className="pl-10 bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-blue-400 focus:border-transparent"
              />
            </div>

            {/* 검색 결과 드롭다운 */}
            {stockQuery && filteredStocks.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-[#2a2a2a] border border-gray-600 rounded-md shadow-lg max-h-40 overflow-y-auto">
                {filteredStocks.map((stock) => (
                  <div
                    key={stock.code}
                    className="p-2 hover:bg-[#3a3a3a] cursor-pointer"
                    onClick={() => setStockQuery(stock.name)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium text-sm">{stock.name}</span>
                        <span className="text-gray-400 text-xs ml-2">{stock.code}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-white text-sm">{stock.currentPrice.toLocaleString()}원</div>
                        <div className={cn("text-xs",
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

          {/* 현재 선택된 종목 정보 */}
          {selectedStock && (
            <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-white font-medium">{selectedStock.name}</span>
                  <span className="text-gray-400 text-xs ml-2">{selectedStock.code}</span>
                </div>
                <div className="text-right">
                  <div className="text-white font-medium">
                    {selectedStock.currentPrice.toLocaleString()}원
                  </div>
                  <Badge variant={selectedStock.changeRate > 0 ? "destructive" : "default"} className="text-xs">
                    {selectedStock.changeRate > 0 ? '+' : ''}{selectedStock.changeRate}%
                  </Badge>
                </div>
              </div>
            </div>
          )}

          {/* 주문 유형 선택 */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={orderType === 'buy' ? 'default' : 'outline'}
              onClick={() => setOrderType('buy')}
              className={cn(
                'relative overflow-hidden transition-all duration-200',
                orderType === 'buy'
                  ? 'bg-profit hover:bg-profit/90 text-white border-profit shadow-lg shadow-profit/20'
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
                'relative overflow-hidden transition-all duration-200',
                orderType === 'sell'
                  ? 'bg-loss hover:bg-loss/90 text-white border-loss shadow-lg shadow-loss/20'
                  : 'border-loss text-loss-foreground hover:bg-loss/10'
              )}
            >
              <TrendingDown className="w-4 h-4 mr-2" />
              매도
            </Button>
          </div>

          {/* 주문 방식 선택 */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">
              주문 방식
            </label>
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
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">
              수량
            </label>
            <Input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="0"
              className="bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-blue-400 focus:border-transparent"
            />
          </div>

          {/* 가격 입력 (지정가일 때만) */}
          {priceType === 'limit' && (
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2">
                지정가격
              </label>
              <Input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="가격을 입력하세요"
                className="bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-blue-400 focus:border-transparent"
              />
            </div>
          )}

          {/* 예상 거래 금액 */}
          {quantity && selectedStock && (
            <div className="p-3 bg-[#2a2a2a] rounded-lg border border-gray-700">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-400">예상 거래금액:</span>
                <span className="text-white font-medium">
                  {estimatedAmount}원
                </span>
              </div>
            </div>
          )}

          {/* 주문 실행 버튼 */}
          <Button
            onClick={handleQuickTrade}
            disabled={!stockQuery || !quantity || isSubmitting}
            className={cn(
              'w-full font-semibold transition-all duration-200',
              orderType === 'buy'
                ? 'bg-profit hover:bg-profit/90 text-white shadow-lg shadow-profit/20'
                : 'bg-loss hover:bg-loss/90 text-white shadow-lg shadow-loss/20',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isSubmitting ? '처리 중...' : `${orderType === 'buy' ? '즉시 매수' : '즉시 매도'}`}
          </Button>

          {/* 자동매매 설정 링크 */}
          <Button
            variant="outline"
            className="w-full border-gray-600 text-gray-300 hover:bg-gray-800/50 hover:text-white"
            onClick={() => router.push('/trading/conditions')}
          >
            <Settings className="w-4 h-4 mr-2" />
            자동매매 설정
          </Button>
        </div>
      </div>
    </div>
  );
}