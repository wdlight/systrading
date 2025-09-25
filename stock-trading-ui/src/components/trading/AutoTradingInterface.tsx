'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Bot, Settings, TrendingUp, TrendingDown, Activity, AlertTriangle } from 'lucide-react';
import { TradingCondition } from '@/lib/types/trading';
import { cn } from '@/lib/utils';

interface AutoTradingInterfaceProps {
  className?: string;
}

export function AutoTradingInterface({ className }: AutoTradingInterfaceProps) {
  const [newCondition, setNewCondition] = useState({
    name: '',
    stockCode: '',
    type: 'buy' as 'buy' | 'sell',
    rsiMin: '',
    rsiMax: '',
    macdSignal: 'positive' as 'positive' | 'negative' | 'crossover',
    quantity: '',
    priceType: 'market' as 'market' | 'limit'
  });

  // 모의 자동매매 조건 데이터
  const [conditions, setConditions] = useState<TradingCondition[]>([
    {
      id: '1',
      name: '삼성전자 RSI 과매도 매수',
      stockCode: '005930',
      type: 'buy',
      conditions: {
        rsi: { min: 20, max: 30 }
      },
      action: {
        quantity: 10,
        priceType: 'market'
      },
      isActive: true,
      createdAt: new Date('2024-09-20'),
      lastTriggered: new Date('2024-09-23')
    },
    {
      id: '2',
      name: 'SK하이닉스 MACD 골든크로스',
      stockCode: '000660',
      type: 'buy',
      conditions: {
        macd: { signal: 'crossover' }
      },
      action: {
        quantity: 5,
        priceType: 'market'
      },
      isActive: false,
      createdAt: new Date('2024-09-21')
    }
  ]);

  const toggleCondition = (id: string) => {
    setConditions(prev =>
      prev.map(condition =>
        condition.id === id
          ? { ...condition, isActive: !condition.isActive }
          : condition
      )
    );
  };

  const deleteCondition = (id: string) => {
    setConditions(prev => prev.filter(condition => condition.id !== id));
  };

  const addNewCondition = () => {
    if (!newCondition.name || !newCondition.stockCode || !newCondition.quantity) return;

    const condition: TradingCondition = {
      id: Date.now().toString(),
      name: newCondition.name,
      stockCode: newCondition.stockCode,
      type: newCondition.type,
      conditions: {
        rsi: newCondition.rsiMin && newCondition.rsiMax ? {
          min: parseInt(newCondition.rsiMin),
          max: parseInt(newCondition.rsiMax)
        } : undefined,
        macd: { signal: newCondition.macdSignal }
      },
      action: {
        quantity: parseInt(newCondition.quantity),
        priceType: newCondition.priceType
      },
      isActive: false,
      createdAt: new Date()
    };

    setConditions(prev => [...prev, condition]);

    // 폼 초기화
    setNewCondition({
      name: '',
      stockCode: '',
      type: 'buy',
      rsiMin: '',
      rsiMax: '',
      macdSignal: 'positive',
      quantity: '',
      priceType: 'market'
    });
  };

  const activeConditionsCount = conditions.filter(c => c.isActive).length;

  return (
    <div className={cn('space-y-6', className)}>
      {/* 자동매매 상태 개요 */}
      <Card className="bg-[#2a2a2a] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Bot className="w-5 h-5" />
            자동매매 상태
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-[#1a1a1a] rounded-lg">
              <div className="text-2xl font-bold text-blue-400">{conditions.length}</div>
              <div className="text-sm text-gray-400">총 조건 수</div>
            </div>
            <div className="text-center p-4 bg-[#1a1a1a] rounded-lg">
              <div className="text-2xl font-bold text-profit-foreground">{activeConditionsCount}</div>
              <div className="text-sm text-gray-400">활성 조건</div>
            </div>
            <div className="text-center p-4 bg-[#1a1a1a] rounded-lg">
              <div className="text-2xl font-bold text-amber-400">2</div>
              <div className="text-sm text-gray-400">오늘 실행됨</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 기존 자동매매 조건 목록 */}
      <Card className="bg-[#2a2a2a] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              자동매매 조건 목록
            </div>
            <Badge variant="outline" className="text-gray-300">
              {conditions.length}개 조건
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {conditions.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>설정된 자동매매 조건이 없습니다.</p>
              <p className="text-sm">아래에서 새로운 조건을 추가해보세요.</p>
            </div>
          ) : (
            conditions.map((condition) => (
              <div
                key={condition.id}
                className="p-4 bg-[#1a1a1a] rounded-lg border border-gray-600"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-white">{condition.name}</h4>
                    <p className="text-sm text-gray-400">
                      {condition.stockCode} • {condition.type === 'buy' ? '매수' : '매도'} •
                      {condition.action.quantity}주
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={condition.isActive}
                      onCheckedChange={() => toggleCondition(condition.id)}
                    />
                    <Badge
                      variant={condition.isActive ? "default" : "secondary"}
                      className={condition.isActive ? "bg-profit" : ""}
                    >
                      {condition.isActive ? '활성' : '비활성'}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  {condition.conditions.rsi && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">RSI 조건:</span>
                      <span className="text-white">
                        {condition.conditions.rsi.min} ~ {condition.conditions.rsi.max}
                      </span>
                    </div>
                  )}
                  {condition.conditions.macd && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">MACD 조건:</span>
                      <span className="text-white">
                        {condition.conditions.macd.signal === 'positive' && '양수'}
                        {condition.conditions.macd.signal === 'negative' && '음수'}
                        {condition.conditions.macd.signal === 'crossover' && '골든크로스'}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-400">생성일:</span>
                    <span className="text-white">
                      {condition.createdAt.toLocaleDateString('ko-KR')}
                    </span>
                  </div>
                  {condition.lastTriggered && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">마지막 실행:</span>
                      <span className="text-profit-foreground">
                        {condition.lastTriggered.toLocaleDateString('ko-KR')}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-gray-600 text-gray-300 hover:bg-blue-600/10 hover:text-blue-400"
                  >
                    <Settings className="w-3 h-3 mr-1" />
                    수정
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => deleteCondition(condition.id)}
                    className="border-gray-600 text-gray-300 hover:bg-red-600/10 hover:text-red-400"
                  >
                    삭제
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* 새 조건 추가 폼 */}
      <Card className="bg-[#2a2a2a] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Settings className="w-5 h-5" />
            새 자동매매 조건 추가
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 기본 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">조건명</label>
              <Input
                value={newCondition.name}
                onChange={(e) => setNewCondition(prev => ({ ...prev, name: e.target.value }))}
                placeholder="조건명을 입력하세요"
                className="bg-[#1a1a1a] border-gray-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">종목 코드</label>
              <Input
                value={newCondition.stockCode}
                onChange={(e) => setNewCondition(prev => ({ ...prev, stockCode: e.target.value }))}
                placeholder="005930"
                className="bg-[#1a1a1a] border-gray-600 text-white"
              />
            </div>
          </div>

          {/* 매수/매도 타입 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">주문 유형</label>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant={newCondition.type === 'buy' ? 'default' : 'outline'}
                onClick={() => setNewCondition(prev => ({ ...prev, type: 'buy' }))}
                className={cn(
                  newCondition.type === 'buy'
                    ? 'bg-profit hover:bg-profit/90 text-white'
                    : 'border-profit text-profit-foreground hover:bg-profit/10'
                )}
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                매수
              </Button>
              <Button
                variant={newCondition.type === 'sell' ? 'default' : 'outline'}
                onClick={() => setNewCondition(prev => ({ ...prev, type: 'sell' }))}
                className={cn(
                  newCondition.type === 'sell'
                    ? 'bg-loss hover:bg-loss/90 text-white'
                    : 'border-loss text-loss-foreground hover:bg-loss/10'
                )}
              >
                <TrendingDown className="w-4 h-4 mr-2" />
                매도
              </Button>
            </div>
          </div>

          {/* RSI 조건 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">RSI 조건 (선택사항)</label>
            <div className="grid grid-cols-2 gap-3">
              <Input
                type="number"
                value={newCondition.rsiMin}
                onChange={(e) => setNewCondition(prev => ({ ...prev, rsiMin: e.target.value }))}
                placeholder="최소값 (예: 20)"
                className="bg-[#1a1a1a] border-gray-600 text-white"
              />
              <Input
                type="number"
                value={newCondition.rsiMax}
                onChange={(e) => setNewCondition(prev => ({ ...prev, rsiMax: e.target.value }))}
                placeholder="최대값 (예: 30)"
                className="bg-[#1a1a1a] border-gray-600 text-white"
              />
            </div>
          </div>

          {/* MACD 조건 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">MACD 조건</label>
            <Select
              value={newCondition.macdSignal}
              onValueChange={(value: 'positive' | 'negative' | 'crossover') =>
                setNewCondition(prev => ({ ...prev, macdSignal: value }))
              }
            >
              <SelectTrigger className="bg-[#1a1a1a] border-gray-600 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#2a2a2a] border-gray-600">
                <SelectItem value="positive">MACD 양수</SelectItem>
                <SelectItem value="negative">MACD 음수</SelectItem>
                <SelectItem value="crossover">골든크로스</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 실행 조건 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">수량</label>
              <Input
                type="number"
                value={newCondition.quantity}
                onChange={(e) => setNewCondition(prev => ({ ...prev, quantity: e.target.value }))}
                placeholder="주문 수량"
                className="bg-[#1a1a1a] border-gray-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300">주문 방식</label>
              <Select
                value={newCondition.priceType}
                onValueChange={(value: 'market' | 'limit') =>
                  setNewCondition(prev => ({ ...prev, priceType: value }))
                }
              >
                <SelectTrigger className="bg-[#1a1a1a] border-gray-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#2a2a2a] border-gray-600">
                  <SelectItem value="market">시장가</SelectItem>
                  <SelectItem value="limit">지정가</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 추가 버튼 */}
          <Button
            onClick={addNewCondition}
            disabled={!newCondition.name || !newCondition.stockCode || !newCondition.quantity}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
          >
            조건 추가
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}