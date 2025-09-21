import { useState, useEffect, useCallback } from 'react';
import { 
  TradingConditions, 
  UseTradingConditionsReturn
} from '@/lib/types';
import { apiClient, fetchWithErrorHandling } from '@/lib/api-client';
import { subscribeToTradingStatus } from '@/lib/websocket';
import { debounce } from '@/lib/utils';

/**
 * 매매 조건을 관리하는 훅
 */
export function useTradingConditions(): UseTradingConditionsReturn {
  const [conditions, setConditions] = useState<TradingConditions | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // 매매 조건 로드
  const loadConditions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const { data, error } = await fetchWithErrorHandling(() => 
      apiClient.getTradingConditions()
    );

    if (data) {
      setConditions(data);
    } else if (error) {
      setError(error);
    }

    setIsLoading(false);
  }, []);

  // 매매 조건 업데이트 (디바운스 적용)
  const updateConditions = useCallback(
    debounce(async (newConditions: Partial<TradingConditions>) => {
      if (!conditions) return;

      setIsSaving(true);
      setError(null);

      const updatedConditions = { ...conditions, ...newConditions };

      const { data, error } = await fetchWithErrorHandling(() => 
        apiClient.updateTradingConditions(updatedConditions)
      );

      if (!error) {
        setConditions(updatedConditions);
      } else {
        setError(error);
      }

      setIsSaving(false);
    }, 1000), // 1초 디바운스
    [conditions]
  );

  // 즉시 업데이트 (저장 없이 UI만 업데이트)
  const updateConditionsImmediate = useCallback((newConditions: Partial<TradingConditions>) => {
    if (!conditions) return;
    
    const updatedConditions = { ...conditions, ...newConditions };
    setConditions(updatedConditions);
    
    // 디바운스된 저장 함수 호출
    updateConditions(newConditions);
  }, [conditions, updateConditions]);

  // 자동매매 시작
  const startTrading = useCallback(async () => {
    const { error } = await fetchWithErrorHandling(() => 
      apiClient.startTrading()
    );

    if (error) {
      setError(error);
      return false;
    }

    // 조건 상태 업데이트
    if (conditions) {
      setConditions({
        ...conditions,
        auto_trading_enabled: true,
      });
    }

    return true;
  }, [conditions]);

  // 자동매매 중지
  const stopTrading = useCallback(async () => {
    const { error } = await fetchWithErrorHandling(() => 
      apiClient.stopTrading()
    );

    if (error) {
      setError(error);
      return false;
    }

    // 조건 상태 업데이트
    if (conditions) {
      setConditions({
        ...conditions,
        auto_trading_enabled: false,
      });
    }

    return true;
  }, [conditions]);

  // 매매 조건 초기화
  const resetConditions = useCallback(() => {
    const defaultConditions: TradingConditions = {
      buy_conditions: {
        amount: 100000,
        macd_type: '상향돌파',
        rsi_value: 30,
        rsi_type: '이상',
        enabled: true,
      },
      sell_conditions: {
        macd_type: '하향돌파',
        rsi_value: 70,
        rsi_type: '이하',
        stop_loss_rate: 5,
        take_profit_rate: 10,
        trailing_stop_enabled: false,
        enabled: true,
      },
      auto_trading_enabled: false,
      max_positions: 5,
      risk_management: {
        max_loss_per_trade: 5,
        max_daily_loss: 10,
        position_sizing: 'fixed',
      },
    };

    updateConditionsImmediate(defaultConditions);
  }, [updateConditionsImmediate]);

  // 초기 로드
  useEffect(() => {
    loadConditions();
  }, [loadConditions]);

  // 매매 상태 업데이트 구독
  useEffect(() => {
    const unsubscribe = subscribeToTradingStatus((data) => {
      if (conditions) {
        setConditions({
          ...conditions,
          auto_trading_enabled: data.is_active,
        });
      }
    });

    return unsubscribe;
  }, [conditions]);

  return {
    conditions,
    updateConditions: updateConditionsImmediate,
    startTrading,
    stopTrading,
    resetConditions,
    loadConditions,
    isLoading: isLoading || isSaving,
    error,
  };
}