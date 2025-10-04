'use client';

import { useState, useEffect } from 'react';

interface StockItem {
  value: string; // 종목코드
  label: string; // 종목명
}

interface UseStockListResult {
  stockList: StockItem[];
  isLoading: boolean;
  error: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useStockList(): UseStockListResult {
  const [stockList, setStockList] = useState<StockItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStockList = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE_URL}/api/stocks/list`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: StockItem[] = await response.json();
        setStockList(data);
      } catch (err) {
        console.error("Failed to fetch stock list:", err);
        setError(err instanceof Error ? err.message : "알 수 없는 오류 발생");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStockList();
  }, []);

  return { stockList, isLoading, error };
}
