/**
 * Brush 이벤트 디버그 페이지
 * 왼쪽 드래그가 정상적으로 감지되는지 테스트
 */

'use client';

import React, { useEffect, useState } from 'react';
import BrushDebugChart from '@/components/trading/BrushDebugChart';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { chartAPI } from '@/lib/chart-api';

export default function DebugBrushPage() {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await chartAPI.getMinuteCandles('005930', {
          date: '2025-09-30'
        });
        setChartData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터 로드 실패');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center text-red-400">
          <p className="text-xl mb-2">❌ 에러 발생</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 헤더 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h1 className="text-2xl font-bold text-white mb-2">
            🔍 Brush 이벤트 디버그
          </h1>
          <p className="text-gray-400 text-sm">
            Recharts Brush 컴포넌트의 onChange 이벤트가 정상적으로 발생하는지 확인
          </p>
        </div>

        {/* 현재 상태 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">📊 현재 상태</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">종목</div>
              <div className="text-xl font-bold text-white">005930 (삼성전자)</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">날짜</div>
              <div className="text-xl font-bold text-white">2025-09-30</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">캔들 수</div>
              <div className="text-xl font-bold text-white">{chartData.length}개</div>
            </div>
          </div>
        </div>

        {/* 테스트 체크리스트 */}
        <div className="bg-orange-900/20 border border-orange-700/50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-orange-300 mb-4">
            ✓ 테스트 체크리스트
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check1" />
              <label htmlFor="check1" className="text-orange-200 cursor-pointer">
                <strong>1. Brush 컴포넌트 확인:</strong> 차트 하단에 슬라이더(Brush)가 보이는가?
              </label>
            </div>
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check2" />
              <label htmlFor="check2" className="text-orange-200 cursor-pointer">
                <strong>2. 드래그 테스트:</strong> Brush를 왼쪽으로 드래그할 수 있는가?
              </label>
            </div>
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check3" />
              <label htmlFor="check3" className="text-orange-200 cursor-pointer">
                <strong>3. 이벤트 로그:</strong> 드래그 시 위의 "Brush 이벤트 로그"에 항목이 추가되는가?
              </label>
            </div>
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check4" />
              <label htmlFor="check4" className="text-orange-200 cursor-pointer">
                <strong>4. 콘솔 로그:</strong> 브라우저 개발자 도구 콘솔에 <code className="bg-gray-800 px-1 rounded">🔥 Brush Event</code> 로그가 출력되는가?
              </label>
            </div>
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check5" />
              <label htmlFor="check5" className="text-orange-200 cursor-pointer">
                <strong>5. 트리거 조건:</strong> startIndex가 20 미만일 때 녹색 배경으로 표시되는가?
              </label>
            </div>
          </div>
        </div>

        {/* Brush 디버그 차트 */}
        <BrushDebugChart chartData={chartData} height={500} />

        {/* 문제 해결 가이드 */}
        <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-300 mb-4">
            🚨 문제가 발생했다면?
          </h2>
          <div className="space-y-3 text-sm text-red-200">
            <div>
              <strong className="text-red-300">1. Brush가 보이지 않는 경우:</strong>
              <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                <li>RechartsAdapter.tsx에 Brush 컴포넌트가 추가되었는지 확인</li>
                <li>Brush import 문이 있는지 확인: <code className="bg-gray-800 px-1 rounded">import {'{'} Brush {'}'} from 'recharts'</code></li>
              </ul>
            </div>
            <div>
              <strong className="text-red-300">2. 이벤트가 발생하지 않는 경우:</strong>
              <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                <li>Brush의 onChange prop이 연결되었는지 확인</li>
                <li>onBrushChange가 ChartAdapterProps에 정의되었는지 확인</li>
                <li>브라우저 콘솔에서 JavaScript 오류가 있는지 확인</li>
              </ul>
            </div>
            <div>
              <strong className="text-red-300">3. 드래그가 안 되는 경우:</strong>
              <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
                <li>차트 데이터가 충분한지 확인 (최소 50개 이상 권장)</li>
                <li>CSS z-index 문제로 다른 요소가 Brush를 가리고 있는지 확인</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 개발자 도구 안내 */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            🛠️ 개발자 도구 사용법
          </h2>
          <div className="space-y-2 text-sm text-gray-300">
            <p><strong>Chrome/Edge:</strong> F12 또는 Ctrl+Shift+I (Mac: Cmd+Option+I)</p>
            <p><strong>Firefox:</strong> F12 또는 Ctrl+Shift+K (Mac: Cmd+Option+K)</p>
            <p><strong>Safari:</strong> Cmd+Option+I (먼저 개발자 메뉴 활성화 필요)</p>
            <p className="mt-3 text-blue-400">
              📌 콘솔 탭에서 <code className="bg-gray-800 px-1 rounded">🔥 Brush Event</code> 로그를 확인하세요
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}