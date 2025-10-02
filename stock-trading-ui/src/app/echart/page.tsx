'use client';

import React from 'react';
import InfiniteScrollCandlestickChart from '@/components/trading/InfiniteScrollCandlestickChart';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function EChartTestPage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-white">실시간 캔들스틱 차트 (1분마다 자동 갱신)</h1>
      <Card className="bg-gray-800 border-gray-700 text-white">
        <CardHeader>
          <CardTitle className="text-xl">삼성전자 (005930) - 실시간 업데이트</CardTitle>
        </CardHeader>
        <CardContent>
          <InfiniteScrollCandlestickChart
            stockCode="005930"
            height={500}
            timeframe="1m"
            chartLibrary="recharts"
            maxDays={5}
            loadThreshold={20}
            autoRefresh={true}
            refreshInterval={60000}
          />
        </CardContent>
      </Card>
    </div>
  );
}
