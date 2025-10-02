/**
 * 무한 스크롤 차트 테스트 페이지
 * Phase 3 검증용
 */

'use client';

import React, { useState } from 'react';
import InfiniteScrollCandlestickChart from '@/components/trading/InfiniteScrollCandlestickChart';

export default function TestInfiniteScrollPage() {
  const [stockCode, setStockCode] = useState('005930');  // 삼성전자
  const [selectedDate, setSelectedDate] = useState('2025-09-30');
  const [maxDays, setMaxDays] = useState(5);

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 헤더 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h1 className="text-2xl font-bold text-white mb-2">
            무한 스크롤 차트 테스트
          </h1>
          <p className="text-gray-400 text-sm">
            Phase 3: 좌측 드래그 시 자동으로 이전 날짜 데이터 로드
          </p>
        </div>

        {/* 설정 패널 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">차트 설정</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 종목코드 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                종목코드
              </label>
              <select
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="005930">005930 (삼성전자)</option>
                <option value="000660">000660 (SK하이닉스)</option>
                <option value="035420">035420 (NAVER)</option>
                <option value="035720">035720 (카카오)</option>
              </select>
            </div>

            {/* 시작 날짜 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                시작 날짜
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* 최대 날짜 수 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                최대 로드 날짜 수: {maxDays}일
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={maxDays}
                onChange={(e) => setMaxDays(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1일</span>
                <span>10일</span>
              </div>
            </div>
          </div>
        </div>

        {/* 사용 방법 */}
        <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-300 mb-3">
            💡 사용 방법
          </h3>
          <ul className="space-y-2 text-sm text-blue-200">
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-0.5">1.</span>
              <span>차트 하단의 Brush를 <strong>좌측으로 드래그</strong>하여 이전 데이터 영역으로 이동</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-0.5">2.</span>
              <span>시작 인덱스가 20 미만이 되면 <strong>자동으로 이전 거래일 데이터 로드</strong></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-0.5">3.</span>
              <span>좌측 상단에서 <strong>현재 로드된 날짜 범위</strong>와 캔들 개수 확인 가능</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-0.5">4.</span>
              <span>캐시된 데이터는 즉시 로드 (~10ms), 새 데이터는 API 호출 (~500ms)</span>
            </li>
          </ul>
        </div>

        {/* 기술 정보 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-3">
            🔧 기술 스택
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-gray-300 mb-2">백엔드</h4>
              <ul className="space-y-1 text-gray-400">
                <li>• ChartCacheService (로컬 파일 캐싱)</li>
                <li>• TradingCalendar (거래일 계산)</li>
                <li>• FastAPI 비동기 API</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-300 mb-2">프론트엔드</h4>
              <ul className="space-y-1 text-gray-400">
                <li>• useInfiniteChartData 훅</li>
                <li>• ChartAPI 클라이언트</li>
                <li>• Recharts + 커스텀 캔들스틱</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 차트 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <InfiniteScrollCandlestickChart
            stockCode={stockCode}
            height={500}
            timeframe="1m"
            initialDate={selectedDate}
            maxDays={maxDays}
            loadThreshold={20}
            chartLibrary="recharts"
          />
        </div>

        {/* 성능 정보 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-3">
            ⚡ 성능 특징
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-green-400 font-semibold mb-1">캐시 히트</div>
              <div className="text-2xl font-bold text-white mb-1">~10ms</div>
              <div className="text-gray-400">로컬 파일 읽기</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-yellow-400 font-semibold mb-1">캐시 미스</div>
              <div className="text-2xl font-bold text-white mb-1">~500ms</div>
              <div className="text-gray-400">API 호출 + 캐시 저장</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-blue-400 font-semibold mb-1">메모리</div>
              <div className="text-2xl font-bold text-white mb-1">~44KB</div>
              <div className="text-gray-400">하루치 (120 캔들)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}