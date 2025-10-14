'use client';

/**
 * 주문 목록 컴포넌트
 * 미체결 주문과 체결 내역을 표시
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import {
  OrderDetail,
  OrderStatus,
  getOrderStatusName,
  getOrderTypeName,
} from '@/lib/types/order';
import { useOrders } from '@/hooks/useOrders';
import { RefreshCw, X, Edit, Clock, CheckCircle, XCircle } from 'lucide-react';

interface OrdersListProps {
  stockCode?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onOrderCancel?: (orderNumber: string) => void;
  className?: string;
}

export function OrdersList({
  stockCode,
  autoRefresh = true,
  refreshInterval = 5000,
  onOrderCancel,
  className,
}: OrdersListProps) {
  const [pendingOrders, setPendingOrders] = useState<OrderDetail[]>([]);
  const [orderHistory, setOrderHistory] = useState<OrderDetail[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const formatNumber = (value?: number | string | null, fallback = '0') => {
    const num = typeof value === 'string' ? Number(value) : value;
    if (typeof num === 'number' && Number.isFinite(num)) {
      return num.toLocaleString();
    }
    return fallback;
  };

  const parseNumeric = (v: unknown): number | null => {
    if (v === null || v === undefined) return null;
    if (typeof v === 'number') return Number.isFinite(v) ? v : null;
    const s = String(v);
    const cleaned = s.replace(/,/g, '').trim();
    const n = Number(cleaned);
    return Number.isFinite(n) ? n : null;
  };

  const { getPendingOrders, getOrderHistory } = useOrders();

  // 주문 조회
  const fetchOrders = async () => {
    setIsRefreshing(true);
    try {
      const [pending, history] = await Promise.all([
        getPendingOrders(stockCode),
        getOrderHistory(""), // stockCode 대신 빈 문자열("")을 전달
      ]);

      if (pending.success) {
        setPendingOrders(pending.orders);
      }

      if (history.success) {
        setOrderHistory(history.orders);
      }
    } catch (error) {
      console.error('주문 조회 실패:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // 자동 새로고침
  useEffect(() => {
    fetchOrders();

    if (autoRefresh) {
      const interval = setInterval(fetchOrders, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [stockCode, autoRefresh, refreshInterval]);

  // 주문 상태 배지 색상
  const getStatusBadgeColor = (status: OrderStatus) => {
    switch (status) {
      case OrderStatus.ACCEPTED:
        return 'bg-blue-500';
      case OrderStatus.FILLED:
        return 'bg-green-500';
      case OrderStatus.PARTIAL:
        return 'bg-yellow-500';
      case OrderStatus.CANCELLED:
        return 'bg-gray-500';
      case OrderStatus.REJECTED:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  // 주문 방향 색상
  const getOrderSideColor = (side: string) => {
    return side === 'buy' ? 'text-red-500' : 'text-blue-500';
  };

  const [tabValue, setTabValue] = useState<'pending' | 'history'>('pending');

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
      <CardHeader className="pb-2 px-3 pt-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white text-sm">주문 내역</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchOrders}
            disabled={isRefreshing}
            className="text-gray-400 hover:text-white h-7 w-7 p-0"
          >
            <RefreshCw className={cn('w-4 h-4', isRefreshing && 'animate-spin')} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="px-3 pb-3">
        <Tabs
          defaultValue="pending"
          value={tabValue}
          onValueChange={(v) => {
            const next = (v as 'pending' | 'history');
            setTabValue(next);
            if (next === 'history') {
              // 탭 전환 시 체결 내역을 즉시 새로고침
              fetchOrders();
            }
          }}
          className="space-y-4"
        >
          <TabsList className="grid w-full grid-cols-2 bg-[#2a2a2a]">
            <TabsTrigger value="pending" className="data-[state=active]:bg-blue-600">
              <Clock className="w-4 h-4 mr-1" />
              미체결 ({pendingOrders.length})
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-green-600">
              <CheckCircle className="w-4 h-4 mr-1" />
              체결 내역 ({orderHistory.length})
            </TabsTrigger>
          </TabsList>

          {/* 미체결 주문 */}
          <TabsContent value="pending" className="space-y-2">
            {pendingOrders.length === 0 ? (
              <div className="text-center py-4 text-gray-400 text-xs">
                미체결 주문이 없습니다
              </div>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {pendingOrders.map((order, index) => (
                  <div
                    key={order.order_number || index}
                    className="bg-[#2a2a2a] rounded-lg p-2 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={cn(getStatusBadgeColor(order.order_status), 'text-[9px] px-1 py-0')}>
                          {getOrderStatusName(order.order_status)}
                        </Badge>
                        <span className={cn('font-medium text-xs', getOrderSideColor(order.order_side))}>
                          {order.order_side === 'buy' ? '매수' : '매도'}
                        </span>
                        <span className="text-white text-xs">{order.stock_name}</span>
                      </div>
                      {onOrderCancel && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onOrderCancel(order.order_number)}
                          className="text-red-500 hover:text-red-400 h-6 px-2"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-1 text-[11px]">
                      <div>
                        <span className="text-gray-400">주문가격:</span>
                        <span className="text-white ml-1">
                          {order.order_type === '01' ? '시장가' : `${formatNumber(order.order_price, 'N/A')}원`}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">주문수량:</span>
                        <span className="text-white ml-1">{`${formatNumber(order.quantity)}주`}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">체결수량:</span>
                        <span className="text-green-500 ml-1">{`${formatNumber(order.filled_quantity)}주`}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">미체결:</span>
                        <span className="text-yellow-500 ml-1">{`${formatNumber(order.remaining_quantity)}주`}</span>
                      </div>
                    </div>

                    <div className="text-xs text-gray-400">
                      주문시각: {new Date(order.order_time).toLocaleString('ko-KR')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* 체결 내역 */}
          <TabsContent value="history" className="space-y-2">
            {orderHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                체결 내역이 없습니다
              </div>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {orderHistory.map((order, index) => (
                  <div
                    key={order.order_number || index}
                    className="bg-[#2a2a2a] rounded-lg p-3 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={cn(getStatusBadgeColor(order.order_status), 'text-[9px] px-1 py-0')}>
                          {getOrderStatusName(order.order_status)}
                        </Badge>
                        <span className={cn('font-medium text-xs', getOrderSideColor(order.order_side))}>
                          {order.order_side === 'buy' ? '매수' : '매도'}
                        </span>
                        <span className="text-white text-xs">{order.stock_name}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-1 text-[11px]">
                      {(() => {
                        const filledPrice = parseNumeric(order.filled_price);
                        const rawFilledPrice = parseNumeric(order.raw_filled_price);
                        const displayFilledPrice = filledPrice ?? rawFilledPrice;
                        const filledQty = parseNumeric(order.filled_quantity);
                        const rawFilledQty = parseNumeric(order.raw_filled_quantity);
                        const displayFilledQty = filledQty ?? rawFilledQty ?? 0;
                        const filledAmt = parseNumeric(order.filled_amount);
                        const rawFilledAmt = parseNumeric(order.raw_filled_amount);
                        const displayFilledAmt = filledAmt ?? rawFilledAmt ?? (displayFilledPrice && displayFilledQty ? displayFilledPrice * displayFilledQty : null);
                        const fee = parseNumeric(order.raw_commission);
                        const tax = parseNumeric(order.raw_tax);
                        const displayFeeTax = (order.commission ?? 0) + (order.tax ?? 0);
                        return (
                          <>
                            <div>
                              <span className="text-gray-400">체결가격:</span>
                              <span className="text-white ml-1">
                                {`${formatNumber(displayFilledPrice, 'N/A')}원 (raw: ${order.raw_filled_price || '-'})`}
                                <br />
                                <span className="text-yellow-400">(fe: {formatNumber(rawFilledPrice ?? 0)}원)</span>
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">체결수량:</span>
                              <span className="text-white ml-1">
                                {`${formatNumber(displayFilledQty)}주 (raw: ${order.raw_filled_quantity || '-'})`}
                                <br />
                                <span className="text-yellow-400">(fe: {formatNumber(rawFilledQty ?? 0)}주)</span>
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">체결금액:</span>
                              <span className="text-white ml-1">
                                {`${formatNumber(displayFilledAmt)}원 (raw: ${order.raw_filled_amount || '-'})`}
                                <br />
                                <span className="text-yellow-400">(fe: {formatNumber(rawFilledAmt ?? 0)}원)</span>
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">수수료+세금:</span>
                              <span className="text-red-400 ml-1">
                                {`${formatNumber(displayFeeTax)}원 (raw: ${order.raw_commission || '-'}, ${order.raw_tax || '-'})`}
                                {fee !== null || tax !== null ? (
                                  <>
                                    <br />
                                    <span className="text-yellow-400">(fe: {formatNumber((fee ?? 0) + (tax ?? 0))}원)</span>
                                  </>
                                ) : null}
                              </span>
                            </div>
                          </>
                        );
                      })()}
                    </div>

                    <div className="text-xs text-gray-400">
                      {
                        (() => {
                          const displayTime = order.filled_time || order.order_time;
                          return (
                            <>
                              체결시각: {displayTime ? new Date(displayTime).toLocaleString('ko-KR') : '-'} (raw: {order.raw_filled_time || '-'})
                            </>
                          );
                        })()
                      }
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
