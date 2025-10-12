'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  TrendingUp,
  TrendingDown,
  Star,
  MoreVertical,
  Filter,
  SortAsc,
  SortDesc,
  ArrowUpDown,
  Volume2,
  Target,
  BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  KoreanStock,
  POPULAR_KOREAN_STOCKS,
  formatStockPrice,
  formatPriceChange,
  getStockColorClass,
  getStockTrendIcon,
  formatKoreanWon,
  StockSector,
  STOCK_SECTORS
} from '@/lib/types/korean-stocks';

interface KoreanStockWatchlistProps {
  className?: string;
  onStockSelect?: (stock: KoreanStock) => void;
  selectedStock?: KoreanStock | null;
  compact?: boolean;
}

type SortField = 'name' | 'currentPrice' | 'changeRate' | 'volume' | 'marketCap';
type SortDirection = 'asc' | 'desc';

const getSectorColor = (sector: StockSector) => {
  const colorMap = {
    '반도체': 'bg-blue-500/20 text-blue-400',
    '인터넷': 'bg-purple-500/20 text-purple-400',
    '자동차': 'bg-green-500/20 text-green-400',
    '가전': 'bg-orange-500/20 text-orange-400',
    'ETF': 'bg-gray-500/20 text-gray-400',
    '화학': 'bg-red-500/20 text-red-400',
    '지주회사': 'bg-cyan-500/20 text-cyan-400'
  };
  return colorMap[sector] || 'bg-gray-500/20 text-gray-400';
};

export function KoreanStockWatchlist({
  className,
  onStockSelect,
  selectedStock,
  compact = false
}: KoreanStockWatchlistProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('marketCap');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [selectedSector, setSelectedSector] = useState<StockSector | 'all'>('all');
  const [watchlist, setWatchlist] = useState<string[]>(['005930', '000660', '035420']);

  // Filter and sort stocks
  const filteredAndSortedStocks = useMemo(() => {
    let filtered = POPULAR_KOREAN_STOCKS.filter(stock => {
      const matchesSearch = searchQuery === '' ||
        stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        stock.code.includes(searchQuery);

      const matchesSector = selectedSector === 'all' || stock.sector === selectedSector;

      return matchesSearch && matchesSector;
    });

    // Sort stocks
    filtered.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      if (sortField === 'name') {
        aValue = a.name;
        bValue = b.name;
      }

      if (typeof aValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue, 'ko-KR')
          : bValue.localeCompare(aValue, 'ko-KR');
      }

      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return filtered;
  }, [searchQuery, sortField, sortDirection, selectedSector]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const toggleWatchlist = (stockCode: string) => {
    setWatchlist(prev =>
      prev.includes(stockCode)
        ? prev.filter(code => code !== stockCode)
        : [...prev, stockCode]
    );
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return <ArrowUpDown className="w-3 h-3" />;
    return sortDirection === 'asc'
      ? <SortAsc className="w-3 h-3" />
      : <SortDesc className="w-3 h-3" />;
  };

  if (compact) {
    return (
      <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              관심종목
            </CardTitle>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              <MoreVertical className="w-3 h-3" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-1">
          {POPULAR_KOREAN_STOCKS.slice(0, 5).map((stock) => {
            const priceChange = formatPriceChange(stock.changeAmount, stock.changeRate);
            const isSelected = selectedStock?.code === stock.code;

            return (
              <div
                key={stock.code}
                onClick={() => onStockSelect?.(stock)}
                className={cn(
                  'p-2 rounded-lg cursor-pointer transition-all duration-200',
                  'hover:bg-gray-800/50',
                  isSelected && 'bg-blue-500/10 border border-blue-500/30'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1">
                      <span className="text-white text-xs font-medium truncate">
                        {stock.name}
                      </span>
                      <span className="text-gray-500 text-xs">
                        {stock.code}
                      </span>
                    </div>
                    <div className="text-xs text-white font-medium">
                      {formatStockPrice(stock.currentPrice)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={cn('text-xs font-medium', priceChange.color)}>
                      {getStockTrendIcon(stock.changeRate)} {stock.changeRate.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            한국 주식 시장
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-8">
              <Filter className="w-4 h-4 mr-1" />
              필터
            </Button>
          </div>
        </div>

        {/* Search and Sector Filter */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="종목명 또는 종목코드 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-[#2a2a2a] border-gray-600 text-white placeholder:text-gray-500"
            />
          </div>

          {/* Sector Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
            <Button
              variant={selectedSector === 'all' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setSelectedSector('all')}
              className="whitespace-nowrap text-xs"
            >
              전체
            </Button>
            {Object.entries(STOCK_SECTORS).map(([sector, config]) => (
              <Button
                key={sector}
                variant={selectedSector === sector ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setSelectedSector(sector as StockSector)}
                className="whitespace-nowrap text-xs"
              >
                {sector} ({config.count})
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-2 px-2 py-1 text-xs text-gray-400 font-medium border-b border-gray-700">
          <div className="col-span-1 flex items-center">
            <Star className="w-3 h-3" />
          </div>
          <div
            className="col-span-3 flex items-center gap-1 cursor-pointer hover:text-white transition-colors"
            onClick={() => handleSort('name')}
          >
            종목명 {getSortIcon('name')}
          </div>
          <div
            className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors text-right"
            onClick={() => handleSort('currentPrice')}
          >
            현재가 {getSortIcon('currentPrice')}
          </div>
          <div
            className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors text-right"
            onClick={() => handleSort('changeRate')}
          >
            등락률 {getSortIcon('changeRate')}
          </div>
          <div
            className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors text-right"
            onClick={() => handleSort('volume')}
          >
            거래량 {getSortIcon('volume')}
          </div>
          <div
            className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors text-right"
            onClick={() => handleSort('marketCap')}
          >
            시총 {getSortIcon('marketCap')}
          </div>
        </div>

        {/* Stock List */}
        <div className="space-y-1 max-h-[600px] overflow-y-auto scrollbar-thin">
          {filteredAndSortedStocks.map((stock) => {
            const priceChange = formatPriceChange(stock.changeAmount, stock.changeRate);
            const isSelected = selectedStock?.code === stock.code;
            const isInWatchlist = watchlist.includes(stock.code);

            return (
              <div
                key={stock.code}
                onClick={() => onStockSelect?.(stock)}
                className={cn(
                  'grid grid-cols-12 gap-2 p-2 rounded-lg cursor-pointer transition-all duration-200',
                  'hover:bg-gray-800/50 border border-transparent',
                  isSelected && 'bg-blue-500/10 border-blue-500/30',
                  getStockColorClass(stock.changeRate)
                )}
              >
                {/* Watchlist Star */}
                <div className="col-span-1 flex items-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleWatchlist(stock.code);
                    }}
                  >
                    <Star
                      className={cn(
                        'w-3 h-3',
                        isInWatchlist ? 'fill-yellow-400 text-yellow-400' : 'text-gray-500'
                      )}
                    />
                  </Button>
                </div>

                {/* Stock Name and Code */}
                <div className="col-span-3 min-w-0">
                  <div className="text-white text-xs font-medium truncate">
                    {stock.name}
                  </div>
                  <div className="text-gray-500 text-xs">{stock.code}</div>
                  <div className="mt-1">
                    <Badge className={cn('text-xs px-1', getSectorColor(stock.sector as StockSector))}>
                      {stock.sector}
                    </Badge>
                  </div>
                </div>

                {/* Current Price */}
                <div className="col-span-2 text-right">
                  <div className="text-white text-xs font-medium">
                    {formatStockPrice(stock.currentPrice, false)}
                  </div>
                  <div className="text-xs text-gray-400">
                    전일 {formatStockPrice(stock.previousClose, false)}
                  </div>
                </div>

                {/* Price Change */}
                <div className="col-span-2 text-right">
                  <div className={cn('text-xs font-medium flex items-center justify-end gap-1', priceChange.color)}>
                    {stock.changeRate > 0 ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : stock.changeRate < 0 ? (
                      <TrendingDown className="w-3 h-3" />
                    ) : null}
                    {stock.changeRate.toFixed(2)}%
                  </div>
                  <div className={cn('text-xs', priceChange.color)}>
                    {stock.changeAmount > 0 ? '+' : ''}{stock.changeAmount.toLocaleString()}
                  </div>
                </div>

                {/* Volume */}
                <div className="col-span-2 text-right">
                  <div className="text-white text-xs font-medium flex items-center justify-end gap-1">
                    <Volume2 className="w-3 h-3 text-gray-400" />
                    {(stock.volume / 1000000).toFixed(1)}M
                  </div>
                  <div className="text-xs text-gray-400">
                    {formatKoreanWon(stock.volume * stock.currentPrice, true, false)}
                  </div>
                </div>

                {/* Market Cap */}
                <div className="col-span-2 text-right">
                  <div className="text-white text-xs font-medium">
                    {formatKoreanWon(stock.marketCap, true, false)}
                  </div>
                  <div className="text-xs text-gray-400">
                    PER {stock.per}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Unit Footer */}
        <div className="pt-2 px-2 text-right text-xs text-gray-500">
          (단위: 원, 시총/거래대금: 억원)
        </div>

        {/* Summary */}
        <div className="pt-3 border-t border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>{filteredAndSortedStocks.length}개 종목</span>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                상승 {filteredAndSortedStocks.filter(s => s.changeRate > 0).length}
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                하락 {filteredAndSortedStocks.filter(s => s.changeRate < 0).length}
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                보합 {filteredAndSortedStocks.filter(s => s.changeRate === 0).length}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Compact mobile version
export function MobileKoreanStockWatchlist({
  className,
  onStockSelect,
  selectedStock
}: KoreanStockWatchlistProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredStocks = useMemo(() => {
    return POPULAR_KOREAN_STOCKS.filter(stock => {
      return searchQuery === '' ||
        stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        stock.code.includes(searchQuery);
    });
  }, [searchQuery]);

  return (
    <div className={cn('bg-[#1a1a1b] border-t border-gray-700', className)}>
      {/* Search Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder="종목 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-[#2a2a2a] border-gray-600 text-white"
          />
        </div>
      </div>

      {/* Stock List */}
      <div className="max-h-80 overflow-y-auto">
        {filteredStocks.map((stock) => {
          const priceChange = formatPriceChange(stock.changeAmount, stock.changeRate);
          const isSelected = selectedStock?.code === stock.code;

          return (
            <div
              key={stock.code}
              onClick={() => onStockSelect?.(stock)}
              className={cn(
                'p-4 border-b border-gray-800 cursor-pointer transition-colors',
                'hover:bg-gray-800/50',
                isSelected && 'bg-blue-500/10'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{stock.name}</span>
                    <Badge className={getSectorColor(stock.sector as StockSector)}>
                      {stock.sector}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-400">{stock.code}</div>
                </div>
                <div className="text-right">
                  <div className="text-white font-medium">
                    {formatStockPrice(stock.currentPrice)}
                  </div>
                  <div className={cn('text-sm font-medium', priceChange.color)}>
                    {getStockTrendIcon(stock.changeRate)} {stock.changeRate.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}