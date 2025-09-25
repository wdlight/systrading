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
      <CardHeader className="pb-3">
        <CardTitle className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <div className="icon-bg-blue">
              <Target className="h-4 w-4" />
            </div>
            <div className="space-y-0.5">
              <h3 className="text-base font-semibold text-white">Trading Conditions</h3>
              <p className="text-xs text-gray-400">Configure automated trading parameters</p>
            </div>
          </div>

          {/* Professional Auto-Trading Toggle */}
          <div className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <div className="flex items-center gap-3">
              <div className={cn(
                'w-2.5 h-2.5 rounded-full animate-pulse',
                localConditions.auto_trading_enabled
                  ? 'bg-profit'
                  : 'bg-gray-500'
              )} />
              <div className="space-y-0.5">
                <p className="text-sm font-semibold text-white">
                  Auto Trading
                </p>
                <p className="text-xs text-gray-400">
                  {localConditions.auto_trading_enabled ? 'System is active' : 'System is paused'}
                </p>
              </div>
            </div>
            <Switch
              checked={localConditions.auto_trading_enabled}
              onCheckedChange={handleAutoTradingToggle}
              disabled={isLoading}
              className="data-[state=checked]:bg-profit"
            />
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 pt-2">
        {/* Professional Error Display */}
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="icon-bg-red">
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div className="space-y-0.5">
                <p className="text-sm font-semibold text-red-400">System Error</p>
                <p className="text-xs text-red-300">{error}</p>
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
        <div className="space-y-2 pt-3 border-t border-gray-600">
          <Button
            onClick={() => handleAutoTradingToggle(!localConditions.auto_trading_enabled)}
            disabled={isLoading}
            className={cn(
              'button-professional w-full py-2.5',
              localConditions.auto_trading_enabled
                ? 'bg-loss hover:bg-loss/90 text-white shadow-professional hover:shadow-loss/25'
                : 'bg-gradient-to-r from-profit to-profit/90 hover:from-profit/90 hover:to-profit text-white shadow-professional hover:shadow-profit/25'
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
            className="button-professional w-full py-2.5 border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white hover:border-gray-500"
          >
            <Settings className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
        </div>

        {/* Professional Status Display */}
        {localConditions.auto_trading_enabled && (
          <div className="p-3 bg-profit/10 border border-profit/30 rounded-lg backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="icon-bg-profit">
                <div className="w-2.5 h-2.5 bg-profit rounded-full animate-pulse" />
              </div>
              <div className="space-y-0.5">
                <p className="text-sm font-semibold text-profit-foreground">System Active</p>
                <p className="text-xs text-profit-foreground/80">Automated trading is running based on your configured conditions</p>
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
    <div className="space-y-4">
      <div className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
        <div className="flex items-center gap-3">
          <div className="icon-bg-profit">
            <span className="text-profit-foreground font-bold text-xs">↗️</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-sm font-bold text-white">Buy Conditions</h4>
            <p className="text-xs text-gray-400">Configure when to enter positions</p>
          </div>
        </div>
        <Switch
          checked={conditions.enabled}
          onCheckedChange={(enabled) => onChange('enabled', enabled)}
          disabled={disabled}
          className="data-[state=checked]:bg-profit"
        />
      </div>

      <div className="space-y-3">
        {/* Buy Amount */}
        <div className="space-y-2">
          <Label className="text-xs font-medium text-gray-300">Buy Amount</Label>
          <Input
            type="number"
            value={conditions.amount}
            onChange={(e) => onChange('amount', Number(e.target.value))}
            disabled={disabled}
            className="input-professional focus:border-profit focus:ring-profit h-8 text-sm"
            placeholder={formatCurrency(DEFAULTS.BUY_AMOUNT)}
          />
        </div>

        {/* MACD Condition */}
        <div className="space-y-2">
          <Label className="text-xs font-medium text-gray-300">MACD Signal</Label>
          <Select
            value={conditions.macd_type}
            onValueChange={(value) => onChange('macd_type', value)}
            disabled={disabled}
          >
            <SelectTrigger className="select-professional focus:border-profit h-8 text-sm">
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
        <div className="space-y-2">
          <Label className="text-xs font-medium text-gray-300">RSI Condition</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              value={conditions.rsi_value}
              onChange={(e) => onChange('rsi_value', Number(e.target.value))}
              disabled={disabled}
              className="input-professional flex-1 focus:border-profit focus:ring-profit h-8 text-sm"
              min="0"
              max="100"
            />
            <Select
              value={conditions.rsi_type}
              onValueChange={(value) => onChange('rsi_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="select-professional w-20 focus:border-profit h-8 text-sm">
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
    <div className="space-y-4">
      <div className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
        <div className="flex items-center gap-3">
          <div className="icon-bg-loss">
            <span className="text-loss-foreground font-bold text-xs">↘️</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-sm font-bold text-white">Sell Conditions</h4>
            <p className="text-xs text-gray-400">Configure when to exit positions</p>
          </div>
        </div>
        <Switch
          checked={conditions.enabled}
          onCheckedChange={(enabled) => onChange('enabled', enabled)}
          disabled={disabled}
          className="data-[state=checked]:bg-loss"
        />
      </div>

      <div className="space-y-3">
        {/* MACD Condition */}
        <div className="space-y-2">
          <Label className="text-xs font-medium text-gray-300">MACD Signal</Label>
          <Select
            value={conditions.macd_type}
            onValueChange={(value) => onChange('macd_type', value)}
            disabled={disabled}
          >
            <SelectTrigger className="select-professional focus:border-loss h-8 text-sm">
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
        <div className="space-y-2">
          <Label className="text-xs font-medium text-gray-300">RSI Condition</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              value={conditions.rsi_value}
              onChange={(e) => onChange('rsi_value', Number(e.target.value))}
              disabled={disabled}
              className="input-professional flex-1 focus:border-loss focus:ring-loss h-8 text-sm"
              min="0"
              max="100"
            />
            <Select
              value={conditions.rsi_type}
              onValueChange={(value) => onChange('rsi_type', value)}
              disabled={disabled}
            >
              <SelectTrigger className="select-professional w-20 focus:border-loss h-8 text-sm">
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
        <div className="space-y-3">
          <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <h5 className="text-xs font-medium text-white mb-3">Risk Management</h5>
            <div className="space-y-3">
              <div className="space-y-2">
                <Label className="text-xs font-medium text-loss-foreground/80">Stop Loss (%)</Label>
                <Input
                  type="number"
                  value={conditions.stop_loss_rate || 5}
                  onChange={(e) => onChange('stop_loss_rate', Number(e.target.value))}
                  disabled={disabled}
                  className="input-professional bg-[#2a2a2a] focus:border-loss focus:ring-loss h-8 text-sm"
                  min="1"
                  max="50"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-medium text-profit-foreground/80">Take Profit (%)</Label>
                <Input
                  type="number"
                  value={conditions.take_profit_rate || 10}
                  onChange={(e) => onChange('take_profit_rate', Number(e.target.value))}
                  disabled={disabled}
                  className="input-professional bg-[#2a2a2a] focus:border-profit focus:ring-profit h-8 text-sm"
                  min="1"
                  max="100"
                />
              </div>

              <div className="flex items-center justify-between p-2.5 bg-[#2a2a2a] rounded-lg">
                <div className="space-y-0.5">
                  <p className="text-xs font-semibold text-white">Trailing Stop</p>
                  <p className="text-xs text-gray-400">Dynamic stop loss adjustment</p>
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