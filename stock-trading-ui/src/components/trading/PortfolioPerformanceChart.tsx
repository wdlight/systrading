'use client';

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { PortfolioHistoryPoint, PortfolioTimeRange } from '@/lib/types';
import { formatCurrency } from '@/lib/utils';

interface PortfolioPerformanceChartProps {
  data: PortfolioHistoryPoint[];
  timeRange: PortfolioTimeRange;
}

function formatDateLabel(value: string, range: PortfolioTimeRange) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const options: Intl.DateTimeFormatOptions =
    range === '1D'
      ? { hour: '2-digit', minute: '2-digit' }
      : range === '1W'
        ? { month: '2-digit', day: '2-digit' }
        : { year: '2-digit', month: '2-digit', day: '2-digit' };

  return date.toLocaleString('ko-KR', options);
}

const tooltipFormatter = (value: number, name: string) => {
  // name은 Line 컴포넌트의 name prop 값 ("Portfolio" 또는 "KOSPI")
  return [formatCurrency(value), name];
};

const PortfolioPerformanceChart = ({ data, timeRange }: PortfolioPerformanceChartProps) => (
  <ResponsiveContainer width="100%" height={320}>
    <LineChart data={data} margin={{ top: 20, right: 20, left: 10, bottom: 10 }}>
      <defs>
        <linearGradient id="portfolioGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
        </linearGradient>
        <linearGradient id="benchmarkGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="5%" stopColor="#9ca3af" stopOpacity={0.3} />
          <stop offset="95%" stopColor="#9ca3af" stopOpacity={0} />
        </linearGradient>
      </defs>
      <CartesianGrid strokeDasharray="4 4" stroke="#374151" />
      <XAxis
        dataKey="date"
        tickFormatter={(value) => formatDateLabel(value, timeRange)}
        stroke="#6b7280"
        minTickGap={24}
        tick={{ fontSize: 11, fill: '#d1d5db', fontFamily: 'Inter, ui-sans-serif, system-ui' }}
      />
      <YAxis
        tickFormatter={(value) => formatCurrency(value)}
        stroke="#6b7280"
        width={72}
        tick={{ fontSize: 11, fill: '#d1d5db', fontFamily: 'Inter, ui-sans-serif, system-ui' }}
      />
      <Tooltip
        contentStyle={{
          backgroundColor: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          color: '#d1d5db',
          fontSize: 11,
          fontFamily: 'Inter, ui-sans-serif, system-ui',
        }}
        labelFormatter={(value) => formatDateLabel(String(value), timeRange)}
        formatter={tooltipFormatter}
      />
      <Legend
        verticalAlign="top"
        wrapperStyle={{ paddingBottom: 8, color: '#e5e7eb', fontSize: 11, fontFamily: 'Inter, ui-sans-serif, system-ui' }}
        iconType="circle"
      />
      <Line
        type="monotone"
        dataKey="portfolio"
        name="Portfolio"
        stroke="#3b82f6"
        strokeWidth={2}
        dot={false}
        activeDot={{ r: 5 }}
        fill="url(#portfolioGradient)"
      />
      <Line
        type="monotone"
        dataKey="benchmark"
        name="KOSPI"
        stroke="#9ca3af"
        strokeDasharray="6 4"
        strokeWidth={2}
        dot={false}
        activeDot={{ r: 4 }}
        fill="url(#benchmarkGradient)"
      />
    </LineChart>
  </ResponsiveContainer>
);

export default PortfolioPerformanceChart;
