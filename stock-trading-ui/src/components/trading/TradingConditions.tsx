'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useTradingConditions } from '@/hooks/useTradingConditions';
import { cn, formatCurrency } from '@/lib/utils';
import { CONDITION_TYPES, DEFAULTS } from '@/lib/constants';
import { Target, Play, Square, Settings, AlertTriangle } from 'lucide-react';

interface TradingConditionsProps {
  className?: string;
}

export function TradingConditions({ className }: TradingConditionsProps) {
  const {
    conditions,
    updateConditions,
    startTrading,
    stopTrading,
    resetConditions,
    isLoading,
    error,
  } = useTradingConditions();

  const [localConditions, setLocalConditions] = useState(conditions);

  // 조건이 로드되면 로컬 상태 업데이트
  useEffect(() => {
    if (conditions) {
      setLocalConditions(conditions);
    }
  }, [conditions]);

  const handleBuyConditionChange = (field: string, value: any) => {
    if (!localConditions) return;

    const newConditions = {
      ...localConditions,
      buy_conditions: {
        ...localConditions.buy_conditions,
        [field]: value,
      },
    };

    setLocalConditions(newConditions);
    updateConditions(newConditions);
  };

  const handleSellConditionChange = (field: string, value: any) => {
    if (!localConditions) return;

    const newConditions = {
      ...localConditions,
      sell_conditions: {
        ...localConditions.sell_conditions,
        [field]: value,
      },
    };

    setLocalConditions(newConditions);
    updateConditions(newConditions);
  };

  const handleAutoTradingToggle = async (enabled: boolean) => {
    if (enabled) {
      const success = await startTrading();
      if (!success) return;
    } else {
      const success = await stopTrading();
      if (!success) return;
    }
  };

  if (isLoading) {
    return (
      <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Target className="h-5 w-5 text-blue-400" />
            매매 조건
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-700 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!localConditions) {
    return (
      <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Target className="h-5 w-5 text-blue-400" />
            매매 조건
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <AlertTriangle className="h-12 w-12 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400">
              매매 조건을 불러올 수 없습니다.
            </p>
            <Button
              onClick={resetConditions}
              variant="outline"
              className="mt-4 border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              기본값으로 재설정
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-400" />
            <span className="text-white">매매 조건</span>
          </div>
          
          {/* 자동매매 토글 */}
          <div className="flex items-center gap-2">
            <Switch
              checked={localConditions.auto_trading_enabled}
              onCheckedChange={handleAutoTradingToggle}
              disabled={isLoading}
            />
            <span className={cn(
              'text-sm font-medium',
              localConditions.auto_trading_enabled
                ? 'text-green-400'
                : 'text-gray-400'
            )}>
              {localConditions.auto_trading_enabled ? '자동매매 ON' : '자동매매 OFF'}
            </span>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 에러 표시 */}
        {error && (
          <div className="p-3 bg-red-900/20 border border-red-800 rounded-lg">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        {/* 매수 조건 */}
        <BuyConditionsSection
          conditions={localConditions.buy_conditions}
          onChange={handleBuyConditionChange}
          disabled={isLoading}
        />

        {/* 매도 조건 */}
        <SellConditionsSection
          conditions={localConditions.sell_conditions}
          onChange={handleSellConditionChange}
          disabled={isLoading}
        />

        {/* 제어 버튼 */}
        <div className="flex gap-2 pt-4 border-t border-gray-600">
          <Button
            onClick={() => handleAutoTradingToggle(!localConditions.auto_trading_enabled)}
            disabled={isLoading}
            className="flex-1"
            variant={localConditions.auto_trading_enabled ? "destructive" : "default"}
          >
            {localConditions.auto_trading_enabled ? (
              <>
                <Square className="h-4 w-4 mr-2" />
                자동매매 중지
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                자동매매 시작
              </>
            )}
          </Button>

          <Button
            onClick={resetConditions}
            variant="outline"
            disabled={isLoading}
            className="border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white"
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>

        {/* 상태 표시 */}
        {localConditions.auto_trading_enabled && (
          <div className="p-3 bg-green-900/20 border border-green-800 rounded-lg">
            <div className="flex items-center gap-2 text-green-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium">
                자동매매가 활성화되었습니다. 설정된 조건에 따라 자동으로 매매됩니다.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BuyConditionsSection({
  conditions,
  onChange,
  disabled,
}: {
  conditions: any;
  onChange: (field: string, value: any) => void;
  disabled: boolean;
}) {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-white flex items-center gap-2">
        📈 매수 조건
        <Switch
          checked={conditions.enabled}
          onCheckedChange={(enabled) => onChange('enabled', enabled)}
          disabled={disabled}
          size="sm"
        />
      </h4>

      <div className="grid gap-4">
        {/* 매수 금액 */}
        <div>
          <Label className="text-xs text-gray-300">매수 금액</Label>
          <Input
            type="number"
            value={conditions.amount}
            onChange={(e) => onChange('amount', Number(e.target.value))}
            disabled={disabled}
            className="h-8 text-xs bg-gray-800 border-gray-600 text-white placeholder-gray-400 focus:border-blue-400 focus:ring-blue-400"
            placeholder={formatCurrency(DEFAULTS.BUY_AMOUNT)}
          />
        </div>

        {/* MACD 조건 */}
        <div>
          <Label className="text-xs text-gray-300">MACD Signal Line</Label>
          <Select
            value={conditions.macd_type}
            onValueChange={(value) => onChange('macd_type', value)}
            disabled={disabled}
          >
            <SelectTrigger className="h-8 text-xs bg-gray-800 border-gray-600 text-white hover:bg-gray-700 focus:border-blue-400">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-600">
              {Object.entries(CONDITION_TYPES.MACD).map(([key, value]) => (
                <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* RSI 조건 */}
        <div>
          <Label className="text-xs text-gray-300">RSI 조건</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              value={conditions.rsi_value}
              onChange={(e) => onChange('rsi_value', Number(e.target.value))}
              disabled={disabled}
              className="h-8 text-xs flex-1 bg-gray-800 border-gray-600 text-white placeholder-gray-400 focus:border-blue-400 focus:ring-blue-400"
              min="0"
              max="100"
            />
            <Select
              value={conditions.rsi_type}
              onValueChange={(value) => onChange('rsi_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="h-8 text-xs w-24 bg-gray-800 border-gray-600 text-white hover:bg-gray-700 focus:border-blue-400">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-600">
                {Object.entries(CONDITION_TYPES.RSI).map(([key, value]) => (
                  <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  );
}

function SellConditionsSection({
  conditions,
  onChange,
  disabled,
}: {
  conditions: any;
  onChange: (field: string, value: any) => void;
  disabled: boolean;
}) {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-white flex items-center gap-2">
        📉 매도 조건
        <Switch
          checked={conditions.enabled}
          onCheckedChange={(enabled) => onChange('enabled', enabled)}
          disabled={disabled}
          size="sm"
        />
      </h4>

      <div className="grid gap-4">
        {/* MACD 조건 */}
        <div>
          <Label className="text-xs text-gray-300">MACD Signal Line</Label>
          <Select
            value={conditions.macd_type}
            onValueChange={(value) => onChange('macd_type', value)}
            disabled={disabled}
          >
            <SelectTrigger className="h-8 text-xs bg-gray-800 border-gray-600 text-white hover:bg-gray-700 focus:border-blue-400">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-800 border-gray-600">
              {Object.entries(CONDITION_TYPES.MACD).map(([key, value]) => (
                <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* RSI 조건 */}
        <div>
          <Label className="text-xs text-gray-300">RSI 조건</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              value={conditions.rsi_value}
              onChange={(e) => onChange('rsi_value', Number(e.target.value))}
              disabled={disabled}
              className="h-8 text-xs flex-1 bg-gray-800 border-gray-600 text-white placeholder-gray-400 focus:border-blue-400 focus:ring-blue-400"
              min="0"
              max="100"
            />
            <Select
              value={conditions.rsi_type}
              onValueChange={(value) => onChange('rsi_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="h-8 text-xs w-24 bg-gray-800 border-gray-600 text-white hover:bg-gray-700 focus:border-blue-400">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-600">
                {Object.entries(CONDITION_TYPES.RSI).map(([key, value]) => (
                  <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* 손익 관리 */}
        <div className="space-y-3">
          <div>
            <Label className="text-xs text-gray-300">손절매 (%)</Label>
            <Input
              type="number"
              value={conditions.stop_loss_rate || 5}
              onChange={(e) => onChange('stop_loss_rate', Number(e.target.value))}
              disabled={disabled}
              className="h-8 text-xs bg-gray-800 border-gray-600 text-white placeholder-gray-400 focus:border-blue-400 focus:ring-blue-400"
              min="1"
              max="50"
            />
          </div>

          <div>
            <Label className="text-xs text-gray-300">익절매 (%)</Label>
            <Input
              type="number"
              value={conditions.take_profit_rate || 10}
              onChange={(e) => onChange('take_profit_rate', Number(e.target.value))}
              disabled={disabled}
              className="h-8 text-xs bg-gray-800 border-gray-600 text-white placeholder-gray-400 focus:border-blue-400 focus:ring-blue-400"
              min="1"
              max="100"
            />
          </div>

          <div className="flex items-center gap-2">
            <Switch
              checked={conditions.trailing_stop_enabled || false}
              onCheckedChange={(enabled) => onChange('trailing_stop_enabled', enabled)}
              disabled={disabled}
              size="sm"
            />
            <Label className="text-xs text-gray-300">트레일링 스톱</Label>
          </div>
        </div>
      </div>
    </div>
  );
}