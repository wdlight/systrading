'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { History, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { Order } from '@/lib/types/trading';
import { cn } from '@/lib/utils';

interface OrderHistoryCardProps {
  className?: string;
}

export function OrderHistoryCard({ className }: OrderHistoryCardProps) {
  // 모의 주문 내역 데이터
  const mockOrders: Order[] = [
    {
      id: '1',
      stockCode: '005930',
      stockName: '삼성전자',
      type: 'buy',
      orderType: 'market',
      quantity: 10,
      status: 'filled',
      timestamp: new Date('2024-09-24T10:30:00'),
      filledQuantity: 10,
      filledPrice: 72800
    },
    {
      id: '2',
      stockCode: '000660',
      stockName: 'SK하이닉스',
      type: 'sell',
      orderType: 'limit',
      quantity: 5,
      price: 128000,
      status: 'pending',
      timestamp: new Date('2024-09-24T09:15:00'),
    },
    {
      id: '3',
      stockCode: '035420',
      stockName: 'NAVER',
      type: 'buy',
      orderType: 'market',
      quantity: 3,
      status: 'filled',
      timestamp: new Date('2024-09-23T15:45:00'),
      filledQuantity: 3,
      filledPrice: 184500
    },
    {
      id: '4',
      stockCode: '005930',
      stockName: '삼성전자',
      type: 'sell',
      orderType: 'market',
      quantity: 5,
      status: 'cancelled',
      timestamp: new Date('2024-09-23T11:20:00'),
    }
  ];

  const getStatusBadge = (status: Order['status']) => {
    switch (status) {
      case 'filled':
        return <Badge className="bg-profit hover:bg-profit/90">체결완료</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-600 hover:bg-yellow-700">대기중</Badge>;
      case 'cancelled':
        return <Badge variant="secondary">취소됨</Badge>;
      case 'rejected':
        return <Badge variant="destructive">거부됨</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getOrderTypeIcon = (type: Order['type']) => {
    return type === 'buy' ? (
      <TrendingUp className="w-4 h-4 text-profit-foreground" />
    ) : (
      <TrendingDown className="w-4 h-4 text-loss-foreground" />
    );
  };

  return (
    <Card className={cn('bg-[#2a2a2a] border-gray-700', className)}>
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <History className="w-5 h-5" />
          주문 내역
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {mockOrders.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>주문 내역이 없습니다</p>
                <p className="text-sm">첫 번째 주문을 시작해보세요.</p>
              </div>
            ) : (
              mockOrders.map((order) => (
                <div
                  key={order.id}
                  className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-600 hover:border-gray-500 transition-colors"
                >
                  {/* 주문 기본 정보 */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getOrderTypeIcon(order.type)}
                      <div>
                        <div className="font-medium text-white">
                          {order.stockName}
                        </div>
                        <div className="text-sm text-gray-400">
                          {order.stockCode}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      {getStatusBadge(order.status)}
                    </div>
                  </div>

                  {/* 주문 상세 정보 */}
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">주문 유형:</span>
                      <span className="text-white">
                        {order.type === 'buy' ? '매수' : '매도'} •{' '}
                        {order.orderType === 'market' ? '시장가' : '지정가'}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-gray-400">수량:</span>
                      <span className="text-white">
                        {order.status === 'filled' && order.filledQuantity
                          ? `${order.filledQuantity}/${order.quantity}`
                          : order.quantity
                        }주
                      </span>
                    </div>

                    {order.orderType === 'limit' && order.price && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">지정가격:</span>
                        <span className="text-white">
                          {order.price.toLocaleString()}원
                        </span>
                      </div>
                    )}

                    {order.status === 'filled' && order.filledPrice && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">체결가격:</span>
                        <span className="text-white">
                          {order.filledPrice.toLocaleString()}원
                        </span>
                      </div>
                    )}

                    {order.status === 'filled' && order.filledPrice && order.filledQuantity && (
                      <div className="flex justify-between font-medium pt-2 border-t border-gray-700">
                        <span className="text-gray-300">체결금액:</span>
                        <span className="text-white">
                          {(order.filledPrice * order.filledQuantity).toLocaleString()}원
                        </span>
                      </div>
                    )}

                    <div className="flex justify-between">
                      <span className="text-gray-400">주문시간:</span>
                      <span className="text-white">
                        {order.timestamp.toLocaleString('ko-KR', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                  </div>

                  {/* 대기중인 주문의 경우 취소 버튼 */}
                  {order.status === 'pending' && (
                    <div className="mt-3 pt-3 border-t border-gray-700">
                      <button
                        className="text-sm text-red-400 hover:text-red-300 transition-colors"
                        onClick={() => console.log('주문 취소:', order.id)}
                      >
                        주문 취소
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}