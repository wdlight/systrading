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
    <Card className={cn(className, "bg-[#2a2a2a] border-gray-700 shadow-xl")}>
      <CardHeader className="pb-5">
        <CardTitle className="flex flex-col gap-5">
          <div className="flex items-center gap-4">
            <div className="icon-bg-blue">
              <Target className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-heading-md text-white">Trading Conditions</h3>
              <p className="text-caption-md text-gray-400">Configure automated trading parameters</p>
            </div>
          </div>

          {/* Professional Auto-Trading Toggle */}
          <div className="flex items-center justify-between p-4 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <div className="flex items-center gap-4">
              <div className={cn(
                'w-3.5 h-3.5 rounded-full animate-pulse',
                localConditions.auto_trading_enabled
                  ? 'bg-green-500'
                  : 'bg-gray-500'
              )} />
              <div className="space-y-0.5">
                <p className="text-body-md font-semibold text-white">
                  Auto Trading
                </p>
                <p className="text-caption-md text-gray-400">
                  {localConditions.auto_trading_enabled ? 'System is active' : 'System is paused'}
                </p>
              </div>
            </div>
            <Switch
              checked={localConditions.auto_trading_enabled}
              onCheckedChange={handleAutoTradingToggle}
              disabled={isLoading}
              className="data-[state=checked]:bg-green-500"
            />
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-section pt-3">
        {/* Professional Error Display */}
        {error && (
          <div className="p-5 bg-red-500/10 border border-red-500/30 rounded-lg backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <div className="icon-bg-red">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <p className="text-body-md font-semibold text-red-400">System Error</p>
                <p className="text-caption-md text-red-300">{error}</p>
              </div>
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

        {/* Professional Control Buttons */}
        <div className="space-comfortable pt-5 border-t border-gray-600">
          <Button
            onClick={() => handleAutoTradingToggle(!localConditions.auto_trading_enabled)}
            disabled={isLoading}
            className={cn(
              'button-professional-lg w-full',
              localConditions.auto_trading_enabled
                ? 'bg-red-500 hover:bg-red-600 text-white shadow-professional hover:shadow-red-500/25'
                : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-professional hover:shadow-green-500/25'
            )}
          >
            {localConditions.auto_trading_enabled ? (
              <>
                <Square className="h-4 w-4 mr-2" />
                Stop Auto Trading
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Start Auto Trading
              </>
            )}
          </Button>

          <Button
            onClick={resetConditions}
            variant="outline"
            disabled={isLoading}
            className="button-professional w-full border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white hover:border-gray-500"
          >
            <Settings className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
        </div>

        {/* Professional Status Display */}
        {localConditions.auto_trading_enabled && (
          <div className="p-5 bg-green-500/10 border border-green-500/30 rounded-lg backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <div className="icon-bg-green">
                <div className="w-3.5 h-3.5 bg-green-500 rounded-full animate-pulse" />
              </div>
              <div className="space-y-1">
                <p className="text-body-md font-semibold text-green-400">System Active</p>
                <p className="text-caption-md text-green-300">Automated trading is running based on your configured conditions</p>
              </div>
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
    <div className="space-relaxed">
      <div className="flex items-center justify-between p-4 bg-[#1a1a1a] rounded-lg border border-gray-600">
        <div className="flex items-center gap-4">
          <div className="icon-bg-green">
            <span className="text-green-400 font-bold text-sm">↗️</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-body-md font-bold text-white">Buy Conditions</h4>
            <p className="text-caption-md text-gray-400">Configure when to enter positions</p>
          </div>
        </div>
        <Switch
          checked={conditions.enabled}
          onCheckedChange={(enabled) => onChange('enabled', enabled)}
          disabled={disabled}
          className="data-[state=checked]:bg-green-500"
        />
      </div>

      <div className="space-comfortable">
        {/* Buy Amount */}
        <div className="space-y-2.5">
          <Label className="text-label-md text-gray-300">Buy Amount</Label>
          <Input
            type="number"
            value={conditions.amount}
            onChange={(e) => onChange('amount', Number(e.target.value))}
            disabled={disabled}
            className="input-professional focus:border-green-400 focus:ring-green-400"
            placeholder={formatCurrency(DEFAULTS.BUY_AMOUNT)}
          />
        </div>

        {/* MACD Condition */}
        <div className="space-y-2.5">
          <Label className="text-label-md text-gray-300">MACD Signal</Label>
          <Select
            value={conditions.macd_type}
            onValueChange={(value) => onChange('macd_type', value)}
            disabled={disabled}
          >
            <SelectTrigger className="select-professional focus:border-green-400">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#2a2a2a] border-gray-600">
              {Object.entries(CONDITION_TYPES.MACD).map(([key, value]) => (
                <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* RSI Condition */}
        <div className="space-y-2.5">
          <Label className="text-label-md text-gray-300">RSI Condition</Label>
          <div className="flex gap-3">
            <Input
              type="number"
              value={conditions.rsi_value}
              onChange={(e) => onChange('rsi_value', Number(e.target.value))}
              disabled={disabled}
              className="input-professional flex-1 focus:border-green-400 focus:ring-green-400"
              min="0"
              max="100"
            />
            <Select
              value={conditions.rsi_type}
              onValueChange={(value) => onChange('rsi_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="select-professional w-28 focus:border-green-400">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#2a2a2a] border-gray-600">
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
    <div className="space-relaxed">
      <div className="flex items-center justify-between p-4 bg-[#1a1a1a] rounded-lg border border-gray-600">
        <div className="flex items-center gap-4">
          <div className="icon-bg-red">
            <span className="text-red-400 font-bold text-sm">↘️</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-body-md font-bold text-white">Sell Conditions</h4>
            <p className="text-caption-md text-gray-400">Configure when to exit positions</p>
          </div>
        </div>
        <Switch
          checked={conditions.enabled}
          onCheckedChange={(enabled) => onChange('enabled', enabled)}
          disabled={disabled}
          className="data-[state=checked]:bg-red-500"
        />
      </div>

      <div className="space-comfortable">
        {/* MACD Condition */}
        <div className="space-y-2.5">
          <Label className="text-label-md text-gray-300">MACD Signal</Label>
          <Select
            value={conditions.macd_type}
            onValueChange={(value) => onChange('macd_type', value)}
            disabled={disabled}
          >
            <SelectTrigger className="select-professional focus:border-red-400">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#2a2a2a] border-gray-600">
              {Object.entries(CONDITION_TYPES.MACD).map(([key, value]) => (
                <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* RSI Condition */}
        <div className="space-y-2.5">
          <Label className="text-label-md text-gray-300">RSI Condition</Label>
          <div className="flex gap-3">
            <Input
              type="number"
              value={conditions.rsi_value}
              onChange={(e) => onChange('rsi_value', Number(e.target.value))}
              disabled={disabled}
              className="input-professional flex-1 focus:border-red-400 focus:ring-red-400"
              min="0"
              max="100"
            />
            <Select
              value={conditions.rsi_type}
              onValueChange={(value) => onChange('rsi_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="select-professional w-28 focus:border-red-400">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#2a2a2a] border-gray-600">
                {Object.entries(CONDITION_TYPES.RSI).map(([key, value]) => (
                  <SelectItem key={key} value={value} className="text-white hover:bg-gray-700 focus:bg-gray-700">
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Risk Management */}
        <div className="space-comfortable">
          <div className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <h5 className="text-label-md text-white mb-4">Risk Management</h5>
            <div className="space-comfortable">
              <div className="space-y-2.5">
                <Label className="text-label-md text-red-300">Stop Loss (%)</Label>
                <Input
                  type="number"
                  value={conditions.stop_loss_rate || 5}
                  onChange={(e) => onChange('stop_loss_rate', Number(e.target.value))}
                  disabled={disabled}
                  className="input-professional bg-[#2a2a2a] focus:border-red-400 focus:ring-red-400"
                  min="1"
                  max="50"
                />
              </div>

              <div className="space-y-2.5">
                <Label className="text-label-md text-green-300">Take Profit (%)</Label>
                <Input
                  type="number"
                  value={conditions.take_profit_rate || 10}
                  onChange={(e) => onChange('take_profit_rate', Number(e.target.value))}
                  disabled={disabled}
                  className="input-professional bg-[#2a2a2a] focus:border-green-400 focus:ring-green-400"
                  min="1"
                  max="100"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-[#2a2a2a] rounded-lg">
                <div className="space-y-0.5">
                  <p className="text-body-sm font-semibold text-white">Trailing Stop</p>
                  <p className="text-caption-md text-gray-400">Dynamic stop loss adjustment</p>
                </div>
                <Switch
                  checked={conditions.trailing_stop_enabled || false}
                  onCheckedChange={(enabled) => onChange('trailing_stop_enabled', enabled)}
                  disabled={disabled}
                  className="data-[state=checked]:bg-blue-500"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}