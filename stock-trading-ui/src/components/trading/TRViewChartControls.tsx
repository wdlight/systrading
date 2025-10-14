// components/trading/TRViewChartControls.tsx
'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, TrendingUp, Check, ChevronsUpDown } from 'lucide-react';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { useStockList } from '@/hooks/useStockList';

interface Stock {
  code: string;
  name: string;
}

interface TRViewChartControlsProps {
  selectedStockCode: string;
  onStockChange: (code: string) => void;
  stocks: Stock[];
  showVolume: boolean;
  onVolumeToggle: () => void;
  showGrid: boolean;
  onGridToggle: () => void;
  dataCount?: number;
}

export function TRViewChartControls({
  selectedStockCode,
  onStockChange,
  stocks,
  showVolume,
  onVolumeToggle,
  showGrid,
  onGridToggle,
  dataCount = 0
}: TRViewChartControlsProps) {
  const [open, setOpen] = React.useState(false);
  const { stockList, isLoading, error } = useStockList();

  const displayValue = React.useMemo(() => {
    if (isLoading) return "종목 리스트 로딩 중...";
    if (error) return `오류: ${error}`;
    if (selectedStockCode) {
      const selected = stockList.find((stock) => stock.value === selectedStockCode);
      return selected ? `${selected.label} (${selected.value})` : "종목명을 검색하세요...";
    }
    return "종목명을 검색하세요...";
  }, [selectedStockCode, stockList, isLoading, error]);

  return (
    <Card className="bg-[#1a1a1b] border-gray-700">
      <CardHeader className="pb-2 px-3 pt-3">
        <CardTitle className="text-white text-sm">차트 설정</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 px-3 pb-3">
        {/* 종목 선택 */}
        <div>
          <label className="text-xs text-gray-400 mb-1 block">
            종목 검색
          </label>
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={open}
                size="sm"
                className="w-full justify-between text-xs h-8"
                disabled={isLoading || !!error}
              >
                {displayValue}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-full p-0 shadow-professional-lg border-gray-600">
              <Command className="bg-[#1a1a1b]">
                <CommandInput
                  placeholder="종목 검색..."
                  className="text-white placeholder:text-gray-500"
                />
                <CommandList>
                  {isLoading && <CommandEmpty className="text-gray-400">종목 리스트 로딩 중...</CommandEmpty>}
                  {error && <CommandEmpty className="text-red-400">오류: {error}</CommandEmpty>}
                  {!isLoading && !error && stockList.length === 0 && <CommandEmpty className="text-gray-400">검색 결과가 없습니다.</CommandEmpty>}
                  <CommandGroup>
                    {stockList.map((stock) => (
                      <CommandItem
                        key={stock.value}
                        value={stock.label}
                        data-selected={selectedStockCode === stock.value}
                        onSelect={(currentValue) => {
                          const selected = stockList.find(s => s.label === currentValue);
                          if (selected) {
                            onStockChange(selected.value === selectedStockCode ? "" : selected.value);
                          }
                          setOpen(false);
                        }}
                        className="text-white"
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4 text-blue-400",
                            selectedStockCode === stock.value ? "opacity-100" : "opacity-0"
                          )}
                        />
                        <span className={cn(
                          selectedStockCode === stock.value && "text-blue-300"
                        )}>
                          {stock.label} ({stock.value})
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          <div className="mt-2 space-y-1">
            <label className="text-xs text-gray-400 mb-1 block">
              주요 종목
            </label>
            {stocks.map((stock) => (
              <Button
                key={stock.code}
                variant={selectedStockCode === stock.code ? 'default' : 'outline'}
                size="sm"
                className="w-full justify-start text-xs h-7 py-1"
                onClick={() => onStockChange(stock.code)}
              >
                {stock.name} ({stock.code})
              </Button>
            ))}
          </div>
        </div>

        {/* 표시 옵션 */}
        <div>
          <label className="text-xs text-gray-400 mb-1 block">
            표시 옵션
          </label>
          <div className="space-y-1">
            <Button
              variant={showVolume ? 'default' : 'outline'}
              size="sm"
              className="w-full justify-start text-xs h-7 py-1"
              onClick={onVolumeToggle}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              거래량 표시
            </Button>
            <Button
              variant={showGrid ? 'default' : 'outline'}
              size="sm"
              className="w-full justify-start text-xs h-7 py-1"
              onClick={onGridToggle}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              그리드 표시
            </Button>
          </div>
        </div>

        {/* 정보 */}
        <div className="pt-2 border-t border-gray-700">
          <p className="text-[10px] text-gray-500">
            Backend API: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </p>
          <p className="text-[10px] text-gray-500">
            데이터: {dataCount}개 캔들
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
