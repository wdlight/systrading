'use client';

import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { ChartCandle } from '@/types/korean-stocks';

interface EChartsCandlestickChartProps {
  chartData: ChartCandle[];
  height?: number;
}

const EChartsCandlestickChart: React.FC<EChartsCandlestickChartProps> = ({ chartData, height = 400 }) => {

    const echartOptions = useMemo(() => {
      const data = chartData.map(candle => [
        candle.open,
        candle.close,
        candle.low,
        candle.high,
      ]);

      return {
        backgroundColor: '#1a1a1b',
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: '#2a2a2a',
          borderColor: '#555',
          textStyle: { color: '#D1D4DC' },
        },
        xAxis: {
          type: 'category',
          data: chartData.map(candle => candle.timestamp), // Pass raw timestamps
          axisLine: { lineStyle: { color: '#555' } },
          axisLabel: {
            color: '#D1D4DC',
            formatter: function (value: string, index: number) {
              const date = new Date(value);
              // Check if it's minute data (e.g., by checking if diffMinutes < 1440)
              if (chartData.length > 1) {
                  const firstTimestamp = new Date(chartData[0].timestamp);
                  const secondTimestamp = new Date(chartData[1].timestamp);
                  const diffMinutes = (secondTimestamp.getTime() - firstTimestamp.getTime()) / (1000 * 60);
                  if (diffMinutes < 1440) { // If it's minute data
                      if (date.getMinutes() % 15 === 0) { // Display label every 15 minutes
                          return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
                      }
                      return ''; // Hide other labels
                  }
              }
                          // Default to MM-DD for daily data
                          return `${(date.getMonth()+1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;            }
          }
        },
        yAxis: {
          scale: true,
          axisLine: { show: false },
          axisLabel: { color: '#D1D4DC' },
          splitLine: { lineStyle: { color: '#2B2B43' } },
        },
        grid: {
          left: '50px',
          right: '20px',
          top: '20px',
          bottom: '50px',
        },
        dataZoom: [
          {
            type: 'inside',
            start: 50,
            end: 100,
          },
          {
            show: true,
            type: 'slider',
            bottom: 10,
            start: 50,
            end: 100,
            backgroundColor: '#2a2a2a',
            borderColor: '#555',
            dataBackground: {
                lineStyle: {color: '#D1D4DC'},
                areaStyle: {color: '#555'}
            },
            selectedDataBackground: {
                lineStyle: {color: '#26A69A'},
                areaStyle: {color: '#26A69A'}
            },
            textStyle: { color: '#D1D4DC' },
          },
        ],
        series: [
          {
            type: 'candlestick',
            data: data,
            barWidth: '80%', // Make candles denser
            itemStyle: {
              color: '#EF5350', // 상승 (Red)
              color0: '#26A69A', // 하락 (Green/Blue)
              borderColor: '#EF5350',
              borderColor0: '#26A69A',
            },
          },
        ],
      };
    }, [chartData]);

  return (
    <ReactECharts
      option={echartOptions}
      style={{ height: height, width: '100%' }}
      notMerge={true}
      lazyUpdate={true}
      theme={"dark"}
    />
  );
};

export default EChartsCandlestickChart;
