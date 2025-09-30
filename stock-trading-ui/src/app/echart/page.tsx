'use client';

import React, { useEffect, useState } from 'react';
import EChartsCandlestickChart from '@/components/trading/EChartsCandlestickChart';
import { fetchCandlestickData } from '@/lib/api/chart';
import { ChartCandle } from '@/types/korean-stocks';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function EChartTestPage() {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadChartData() {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchCandlestickData("005930"); 
        setChartData(data);
      } catch (err) {
        setError("차트 데이터를 불러오는 데 실패했습니다.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadChartData();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-white">ECharts 캔들스틱 차트 테스트</h1>
      <Card className="bg-gray-800 border-gray-700 text-white">
        <CardHeader>
          <CardTitle className="text-xl">삼성전자 (005930) 캔들 차트</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-center py-8">차트 데이터를 불러오는 중...</p>}
          {error && <p className="text-center py-8 text-red-500">{error}</p>}
          {!loading && !error && chartData.length > 0 && (
            <EChartsCandlestickChart chartData={chartData} height={500} />
          )}
          {!loading && !error && chartData.length === 0 && (
            <p className="text-center py-8 text-gray-400">표시할 차트 데이터가 없습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
