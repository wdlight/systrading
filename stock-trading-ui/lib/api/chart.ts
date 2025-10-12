import { ChartCandle } from '@/lib/types/korean-stocks';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ChartDataResponse {
  data: ChartCandle[];
  stock_code: string;
  stock_name: string;
}

export async function fetchCandlestickData(stockCode: string): Promise<ChartCandle[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chart/${stockCode}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ChartDataResponse = await response.json();
    return result.data;
  } catch (error) {
    console.error("Failed to fetch candlestick data:", error);
    return [];
  }
}
