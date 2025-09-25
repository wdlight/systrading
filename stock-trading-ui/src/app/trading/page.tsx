'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { TradingModeSwitch } from '@/components/trading/TradingModeSwitch';
import { ManualTradingInterface } from '@/components/trading/ManualTradingInterface';
import { AutoTradingInterface } from '@/components/trading/AutoTradingInterface';
import { StockInfoCard } from '@/components/common/StockInfoCard';
import { OrderHistoryCard } from '@/components/common/OrderHistoryCard';
import { RiskAssessmentCard } from '@/components/common/RiskAssessmentCard';
import { Stock } from '@/lib/types/trading';

export default function TradingPage() {
  const [tradingMode, setTradingMode] = useState<'manual' | 'auto'>('manual');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);

  return (
    <div className="min-h-screen bg-[#0a0a0b]">
      <Header />

      <div className="container mx-auto p-4 md:p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">매매 인터페이스</h1>
          <p className="text-gray-400">
            주식 매수/매도 및 자동매매 설정을 관리합니다.
          </p>
        </div>

        {/* 모드 스위치 */}
        <div className="mb-6">
          <TradingModeSwitch
            mode={tradingMode}
            onChange={setTradingMode}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 좌측: 매매 인터페이스 */}
          <div className="lg:col-span-2">
            {tradingMode === 'manual' ? (
              <ManualTradingInterface
                selectedStock={selectedStock}
                onStockChange={setSelectedStock}
              />
            ) : (
              <AutoTradingInterface />
            )}
          </div>

          {/* 우측: 보조 정보 */}
          <div className="space-y-6">
            <StockInfoCard stock={selectedStock} />
            <OrderHistoryCard />
            <RiskAssessmentCard />
          </div>
        </div>
      </div>
    </div>
  );
}