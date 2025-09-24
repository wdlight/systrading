'use client';

import { useState, useMemo, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CompactPriceDisplay } from '@/components/common/PriceDisplay';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { cn, formatNumber, getRSIStatus, getMACDSignal, formatDateTime } from '@/lib/utils';
import { Eye, Plus, X, TrendingUp, AlertCircle, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { WatchlistItem } from '@/lib/types';

interface LogEntry {
  timestamp: string;
  data: WatchlistItem;
  type: 'update' | 'initial';
}

interface WatchlistPanelProps {
  className?: string;
}

export function WatchlistPanel({ className }: WatchlistPanelProps) {
  const { watchlist, isLoading, error } = useRealtimeData();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'code' | 'profit_rate' | 'rsi' | 'volume'>('code');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // 검색 및 정렬된 워치리스트
  const filteredAndSortedWatchlist = useMemo(() => {
    let filtered = watchlist.filter(item =>
      item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.stock_name && item.stock_name.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    filtered.sort((a, b) => {
      let aValue: number;
      let bValue: number;

      switch (sortBy) {
        case 'code':
          return sortOrder === 'asc' 
            ? a.stock_code.localeCompare(b.stock_code)
            : b.stock_code.localeCompare(a.stock_code);
        case 'profit_rate':
          aValue = a.profit_rate;
          bValue = b.profit_rate;
          break;
        case 'rsi':
          aValue = a.rsi;
          bValue = b.rsi;
          break;
        case 'volume':
          aValue = a.volume;
          bValue = b.volume;
          break;
        default:
          return 0;
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return filtered;
  }, [watchlist, searchTerm, sortBy, sortOrder]);

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            워치리스트
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(className, "bg-[#2a2a2a] border-gray-700 shadow-xl")}>
      <CardHeader className="pb-5">
        <div className="flex flex-col gap-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="icon-bg-blue">
                <Eye className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-heading-md text-white">Portfolio Holdings</h3>
                <p className="text-caption-md text-gray-400">
                  {filteredAndSortedWatchlist.length} position{filteredAndSortedWatchlist.length !== 1 ? 's' : ''} tracked
                </p>
              </div>
            </div>

            <Button
              className="button-professional bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-professional hover:shadow-professional-lg hover:scale-105"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Stock
            </Button>
          </div>

          {/* Professional Search Bar */}
          <div className="flex gap-3">
            <Input
              placeholder="Search by stock code or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-professional flex-1 focus:border-blue-400 focus:ring-blue-400"
            />
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="p-5 mb-5 bg-red-500/10 border border-red-500/30 rounded-lg backdrop-blur-sm">
            <div className="flex items-center gap-4">
              <div className="icon-bg-red">
                <AlertCircle className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <p className="text-body-md font-semibold text-red-400">Connection Error</p>
                <p className="text-caption-md text-red-300">{error}</p>
              </div>
            </div>
          </div>
        )}

        {filteredAndSortedWatchlist.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Eye className="h-8 w-8 text-gray-500" />
            </div>
            <h4 className="text-heading-sm font-semibold text-gray-400 mb-2">
              {searchTerm ? 'No Results Found' : 'No Holdings Yet'}
            </h4>
            <p className="text-body-md text-gray-500">
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Add your first stock to start tracking'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="text-xs border-gray-600">
                  <TableHead
                    className="h-11 cursor-pointer hover:bg-gray-700 text-gray-300 font-semibold uppercase tracking-wide transition-colors duration-200"
                    onClick={() => handleSort('code')}
                  >
                    Stock
                    {sortBy === 'code' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead className="h-11 text-center text-gray-300 font-semibold uppercase tracking-wide">현재가</TableHead>
                  <TableHead
                    className="h-11 cursor-pointer hover:bg-gray-700 text-gray-300 font-semibold uppercase tracking-wide transition-colors duration-200"
                    onClick={() => handleSort('profit_rate')}
                  >
                    수익률
                    {sortBy === 'profit_rate' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead className="h-11 text-gray-300 font-semibold uppercase tracking-wide">평균단가</TableHead>
                  <TableHead className="h-11 text-gray-300 font-semibold uppercase tracking-wide">수량</TableHead>
                  <TableHead className="h-11 text-gray-300 font-semibold uppercase tracking-wide">MACD</TableHead>
                  <TableHead
                    className="h-11 cursor-pointer hover:bg-gray-700 text-gray-300 font-semibold uppercase tracking-wide transition-colors duration-200"
                    onClick={() => handleSort('rsi')}
                  >
                    RSI
                    {sortBy === 'rsi' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead
                    className="h-8 cursor-pointer hover:bg-gray-700 text-gray-300"
                    onClick={() => handleSort('volume')}
                  >
                    거래량
                    {sortBy === 'volume' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead className="h-8 text-gray-300">액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedWatchlist.map((item) => (
                  <WatchlistRow key={item.stock_code} item={item} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function WatchlistRow({ item }: { item: WatchlistItem }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const prevItemRef = useRef<WatchlistItem | null>(null);
  const rsiStatus = getRSIStatus(item.rsi);
  const macdSignal = getMACDSignal(item.macd, item.macd_signal);

  // 데이터 변경 감지 및 로그 추가
  useEffect(() => {
    const now = new Date().toISOString();

    if (!prevItemRef.current) {
      // 초기 데이터
      setLogs([{
        timestamp: now,
        data: { ...item },
        type: 'initial'
      }]);
    } else {
      // 데이터 변경 감지
      const hasChanged = JSON.stringify(prevItemRef.current) !== JSON.stringify(item);

      if (hasChanged) {
        setLogs(prev => [{
          timestamp: now,
          data: { ...item },
          type: 'update'
        }, ...prev].slice(0, 50)); // 최대 50개 로그 유지
      }
    }

    prevItemRef.current = { ...item };
  }, [item]);

  const columnCount = 9; // 전체 컬럼 수

  return (
    <>
      <TableRow className="text-xs hover:bg-gray-700/50 border-gray-700">
        {/* 종목 정보 */}
        <TableCell className="font-medium">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              className="h-4 w-4 p-0 text-gray-400 hover:text-white"
              onClick={() => setIsExpanded(!isExpanded)}
              title={isExpanded ? "로그 접기" : "로그 펼치기"}
            >
              {isExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>
            <div>
              <div className="font-mono text-xs text-gray-100">{item.stock_code}</div>
              {item.stock_name && (
                <div className="text-xs text-gray-400 truncate max-w-20">
                  {item.stock_name}
                </div>
              )}
            </div>
          </div>
        </TableCell>

        {/* 현재가 */}
        <TableCell className="text-center">
          <CompactPriceDisplay
            current={item.current_price}
            changeRate={item.change_rate}
          />
        </TableCell>

        {/* 수익률 */}
        <TableCell>
          <div className={cn(
            'text-xs font-medium',
            item.profit_rate > 0 ? 'text-green-500 dark:text-green-400' :
            item.profit_rate < 0 ? 'text-red-500 dark:text-red-400' :
            'text-gray-600 dark:text-gray-400'
          )}>
            {item.profit_rate > 0 ? '+' : ''}{item.profit_rate}%
          </div>
        </TableCell>

        {/* 평균단가 */}
        <TableCell>
          <div className="text-xs font-mono text-gray-200">
            {item.avg_price ? formatNumber(item.avg_price) : '-'}
          </div>
        </TableCell>

        {/* 수량 */}
        <TableCell>
          <div className="text-xs font-mono text-gray-200">
            {formatNumber(item.quantity)}
          </div>
        </TableCell>

        {/* MACD */}
        <TableCell>
          <div className="flex flex-col gap-0.5">
            <div className="text-xs font-mono text-gray-200">
              {item.macd}
            </div>
            <div className={cn(
              'text-xs px-1 py-0.5 rounded text-center',
              macdSignal.trend === 'bullish' ? 'bg-green-900/30 text-green-400' :
              macdSignal.trend === 'bearish' ? 'bg-red-900/30 text-red-400' :
              'bg-gray-800 text-gray-400'
            )}>
              {macdSignal.trend === 'bullish' ? '▲' : macdSignal.trend === 'bearish' ? '▼' : '●'}
            </div>
          </div>
        </TableCell>

        {/* RSI */}
        <TableCell>
          <div className="flex flex-col gap-0.5">
            <div className="text-xs font-mono text-gray-200">
              {item.rsi}
            </div>
            <div className={cn(
              'text-xs px-1 py-0.5 rounded text-center',
              rsiStatus.status === 'oversold' ? 'bg-blue-900/30 text-blue-400' :
              rsiStatus.status === 'overbought' ? 'bg-orange-900/30 text-orange-400' :
              'bg-gray-800 text-gray-400'
            )}>
              {rsiStatus.description}
            </div>
          </div>
        </TableCell>

        {/* 거래량 */}
        <TableCell>
          <div className="text-xs font-mono text-gray-200">
            {formatNumber(item.volume, { compact: false })}
          </div>
        </TableCell>

        {/* 액션 버튼 */}
        <TableCell>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant="ghost"
              className="h-6 w-6 p-0 text-gray-400 hover:text-blue-400"
              title="차트 보기"
            >
              <TrendingUp className="h-3 w-3" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-6 w-6 p-0 text-gray-400 hover:text-red-400"
              title="워치리스트에서 제거"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        </TableCell>
      </TableRow>

      {/* 확장된 로그 영역 */}
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={columnCount} className="p-0">
            <div className="bg-gray-800 border-t border-gray-600">
              <div className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-300">
                    실시간 데이터 로그 ({logs.length}개)
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setLogs([])}
                    className="h-6 text-xs border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    로그 클리어
                  </Button>
                </div>

                <div className="max-h-60 overflow-y-auto space-y-2">
                  {logs.length === 0 ? (
                    <div className="text-center py-4 text-gray-400 text-sm">
                      로그 데이터가 없습니다.
                    </div>
                  ) : (
                    logs.map((log, index) => (
                      <LogEntryComponent key={index} entry={log} />
                    ))
                  )}
                </div>
              </div>
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function LogEntryComponent({ entry }: { entry: LogEntry }) {
  const isUpdate = entry.type === 'update';

  return (
    <div className={cn(
      "p-3 rounded-lg border text-xs font-mono",
      isUpdate
        ? "bg-blue-900/20 border-blue-800"
        : "bg-green-900/20 border-green-800"
    )}>
      <div className="flex items-center justify-between mb-2">
        <span className={cn(
          "text-xs font-medium px-2 py-1 rounded",
          isUpdate
            ? "bg-blue-800 text-blue-200"
            : "bg-green-800 text-green-200"
        )}>
          {isUpdate ? '업데이트' : '초기값'}
        </span>
        <span className="text-gray-400">
          {formatDateTime(entry.timestamp)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
        <div><span className="text-gray-400">현재가:</span> <span className="text-gray-100">₩{entry.data.current_price.toLocaleString()}</span></div>
        <div><span className="text-gray-400">수익률:</span> <span className="text-gray-300">{entry.data.profit_rate}%</span></div>
        <div><span className="text-gray-400">평균단가:</span> <span className="text-gray-200">₩{entry.data.avg_price?.toLocaleString() || '-'}</span></div>
        <div><span className="text-gray-400">수량:</span> <span className="text-gray-200">{entry.data.quantity}</span></div>
        <div><span className="text-gray-400">MACD:</span> <span className="text-gray-200">{entry.data.macd}</span></div>
        <div><span className="text-gray-400">RSI:</span> <span className="text-gray-200">{entry.data.rsi}</span></div>
        <div><span className="text-gray-400">거래량:</span> <span className="text-gray-200">{entry.data.volume.toLocaleString()}</span></div>
        <div><span className="text-gray-400">변동률:</span> <span className="text-gray-200">{entry.data.change_rate}%</span></div>
      </div>
    </div>
  );
}