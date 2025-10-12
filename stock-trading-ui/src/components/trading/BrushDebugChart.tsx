/**
 * Brush 이벤트 디버그용 차트
 * 왼쪽 드래그 이벤트가 정상적으로 발생하는지 확인
 */

'use client';

import React, { useState, useCallback } from 'react';
import { UniversalChart } from './chart-adapters';
import { ChartCandle } from '@/lib/types/korean-stocks';

interface BrushDebugChartProps {
  chartData: ChartCandle[];
  height?: number;
}

export default function BrushDebugChart({
  chartData,
  height = 400
}: BrushDebugChartProps) {
  const [brushEvents, setBrushEvents] = useState<Array<{
    time: string;
    startIndex: number;
    endIndex: number;
  }>>([]);

  const handleBrushChange = useCallback((indices: { startIndex: number; endIndex: number }) => {
    const event = {
      time: new Date().toLocaleTimeString(),
      startIndex: indices.startIndex,
      endIndex: indices.endIndex
    };

    console.log('🔥 Brush Event:', event);

    setBrushEvents(prev => [event, ...prev].slice(0, 10)); // 최근 10개만 유지
  }, []);

  return (
    <div className="space-y-4">
      {/* Brush 이벤트 로그 */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">
          🔍 Brush 이벤트 로그
        </h3>

        {brushEvents.length === 0 ? (
          <div className="text-gray-400 text-sm py-4 text-center">
            <p>아직 Brush 이벤트가 발생하지 않았습니다.</p>
            <p className="mt-2">차트 하단의 슬라이더를 드래그해보세요.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {brushEvents.map((event, idx) => (
              <div
                key={idx}
                className={`
                  p-3 rounded-lg border
                  ${event.startIndex < 20
                    ? 'bg-green-900/20 border-green-700/50'
                    : 'bg-gray-800 border-gray-700'
                  }
                `}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{event.time}</span>
                  {event.startIndex < 20 && (
                    <span className="text-xs text-green-400 font-semibold">
                      ⚡ 이전 데이터 로드 트리거!
                    </span>
                  )}
                </div>
                <div className="mt-1 flex gap-4 text-sm">
                  <span className="text-white">
                    startIndex: <span className="font-mono text-blue-400">{event.startIndex}</span>
                  </span>
                  <span className="text-white">
                    endIndex: <span className="font-mono text-blue-400">{event.endIndex}</span>
                  </span>
                  <span className="text-white">
                    range: <span className="font-mono text-purple-400">{event.endIndex - event.startIndex + 1}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 안내 메시지 */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
        <h4 className="text-blue-300 font-semibold mb-2">💡 테스트 방법</h4>
        <ul className="space-y-1 text-sm text-blue-200">
          <li>1. 차트 하단의 <strong>Brush(슬라이더)</strong>를 찾으세요</li>
          <li>2. Brush를 <strong>왼쪽으로 드래그</strong>하세요</li>
          <li>3. startIndex가 <strong>20 미만</strong>이 되면 <span className="text-green-400">녹색 배경</span>으로 표시됩니다</li>
          <li>4. 콘솔에도 <code className="bg-gray-800 px-1 rounded">🔥 Brush Event</code> 로그가 출력됩니다</li>
        </ul>
      </div>

      {/* 차트 */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">
          📊 차트 ({chartData.length}개 캔들)
        </h3>
        <UniversalChart
          library="recharts"
          chartData={chartData}
          height={height}
          timeframe="1m"
          events={{ onRangeChange: handleBrushChange }}
        />
      </div>

      {/* 디버그 정보 */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3">
          🔧 디버그 정보
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-400">총 캔들 수</div>
            <div className="text-2xl font-bold text-white">{chartData.length}</div>
          </div>
          <div>
            <div className="text-gray-400">이벤트 발생 횟수</div>
            <div className="text-2xl font-bold text-white">{brushEvents.length}</div>
          </div>
          <div>
            <div className="text-gray-400">최근 startIndex</div>
            <div className="text-2xl font-bold text-white">
              {brushEvents[0]?.startIndex ?? '-'}
            </div>
          </div>
          <div>
            <div className="text-gray-400">트리거 임계값</div>
            <div className="text-2xl font-bold text-green-400">
              {'< 20'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}