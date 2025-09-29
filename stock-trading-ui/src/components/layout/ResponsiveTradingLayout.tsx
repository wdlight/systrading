'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  PanelLeft,
  PanelRight,
  Maximize2,
  Minimize2,
  BarChart3,
  Target,
  ShoppingCart,
  Smartphone,
  Monitor,
  Tablet
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ResponsiveTradingLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  leftPanelTitle?: string;
  rightPanelTitle?: string;
  className?: string;
}

type LayoutMode = 'desktop' | 'tablet' | 'mobile';
type PanelFocus = 'left' | 'center' | 'right';

export function ResponsiveTradingLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  leftPanelTitle = '관심종목',
  rightPanelTitle = '거래하기',
  className
}: ResponsiveTradingLayoutProps) {
  const [isClient, setIsClient] = useState(false);
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('desktop');
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);
  const [mobilePanelFocus, setMobilePanelFocus] = useState<PanelFocus>('center');

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Detect screen size and set layout mode
  useEffect(() => {
    if (!isClient) return;

    const handleResize = () => {
      const width = window.innerWidth;
      if (width >= 1024) {
        setLayoutMode('desktop');
      } else if (width >= 768) {
        setLayoutMode('tablet');
      } else {
        setLayoutMode('mobile');
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isClient]);

  // Auto-collapse panels based on screen size
  useEffect(() => {
    if (!isClient) return;
    
    if (layoutMode === 'mobile') {
      setLeftPanelCollapsed(mobilePanelFocus !== 'left');
      setRightPanelCollapsed(mobilePanelFocus !== 'right');
    } else if (layoutMode === 'tablet') {
      setLeftPanelCollapsed(false);
      setRightPanelCollapsed(true);
    } else {
      // Desktop - show all panels
      setLeftPanelCollapsed(false);
      setRightPanelCollapsed(false);
    }
  }, [layoutMode, mobilePanelFocus, isClient]);

  const getLayoutModeIcon = () => {
    switch (layoutMode) {
      case 'desktop': return <Monitor className="w-3 h-3" />;
      case 'tablet': return <Tablet className="w-3 h-3" />;
      case 'mobile': return <Smartphone className="w-3 h-3" />;
    }
  };

  const getOptimalPanelWidth = () => {
    if (layoutMode === 'desktop') {
      return 'w-96 xl:w-[420px]';
    } else if (layoutMode === 'tablet') {
      return 'w-72';
    } else {
      return 'w-full';
    }
  };

  // Mobile navigation
  const MobileTabBar = () => (
    <div className="md:hidden bg-[#1a1a1b] border-t border-gray-700 p-2">
      <div className="flex items-center justify-around">
        <Button
          variant={mobilePanelFocus === 'left' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setMobilePanelFocus('left')}
          className={cn(
            'flex-1 mx-1',
            mobilePanelFocus === 'left' && 'bg-blue-600 text-white'
          )}
        >
          <BarChart3 className="w-4 h-4 mr-1" />
          종목
        </Button>
        <Button
          variant={mobilePanelFocus === 'center' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setMobilePanelFocus('center')}
          className={cn(
            'flex-1 mx-1',
            mobilePanelFocus === 'center' && 'bg-blue-600 text-white'
          )}
        >
          <Maximize2 className="w-4 h-4 mr-1" />
          차트
        </Button>
        <Button
          variant={mobilePanelFocus === 'right' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setMobilePanelFocus('right')}
          className={cn(
            'flex-1 mx-1',
            mobilePanelFocus === 'right' && 'bg-blue-600 text-white'
          )}
        >
          <ShoppingCart className="w-4 h-4 mr-1" />
          거래
        </Button>
      </div>
    </div>
  );

  if (!isClient) {
    return null;
  }

  if (layoutMode === 'mobile') {
    return (
      <div className={cn('h-full flex flex-col', className)}>
        {/* Mobile Content */}
        <div className="flex-1 overflow-hidden">
          {mobilePanelFocus === 'left' && (
            <div className="h-full">{leftPanel}</div>
          )}
          {mobilePanelFocus === 'center' && (
            <div className="h-full">{centerPanel}</div>
          )}
          {mobilePanelFocus === 'right' && (
            <div className="h-full">{rightPanel}</div>
          )}
        </div>

        {/* Mobile Tab Bar */}
        <MobileTabBar />

        {/* Layout Mode Indicator */}
        <div className="fixed top-20 right-2 z-50">
          <Badge className="bg-orange-500 text-white text-xs">
            {getLayoutModeIcon()}
            Mobile
          </Badge>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('h-full flex', className)}>
      {/* Left Panel */}
      <div className={cn(
        'border-r border-gray-700 transition-all duration-300 flex-shrink-0',
        leftPanelCollapsed ? 'w-12' : getOptimalPanelWidth(),
        layoutMode === 'tablet' && leftPanelCollapsed && 'hidden'
      )}>
        <div className="h-full flex flex-col">
          {/* Panel Header */}
          <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-[#1a1a1b]">
            {!leftPanelCollapsed && (
              <h2 className="text-white font-medium flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                {leftPanelTitle}
              </h2>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
              className="text-gray-400 hover:text-white p-1 h-8 w-8"
            >
              {leftPanelCollapsed ?
                <PanelLeft className="w-4 h-4" /> :
                <Minimize2 className="w-4 h-4" />
              }
            </Button>
          </div>

          {/* Panel Content */}
          {!leftPanelCollapsed && (
            <div className="flex-1 overflow-hidden">
              {leftPanel}
            </div>
          )}
        </div>
      </div>

      {/* Center Panel */}
      <div className="flex-1 flex flex-col min-w-0">
        {centerPanel}
      </div>

      {/* Right Panel */}
      <div className={cn(
        'border-l border-gray-700 transition-all duration-300 flex-shrink-0',
        rightPanelCollapsed ? 'w-12' : getOptimalPanelWidth(),
        (layoutMode === 'tablet' || layoutMode === 'mobile') && rightPanelCollapsed && 'hidden'
      )}>
        <div className="h-full flex flex-col">
          {/* Panel Header */}
          <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-[#1a1a1b]">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setRightPanelCollapsed(!rightPanelCollapsed)}
              className="text-gray-400 hover:text-white p-1 h-8 w-8"
            >
              {rightPanelCollapsed ?
                <PanelRight className="w-4 h-4" /> :
                <Maximize2 className="w-4 h-4" />
              }
            </Button>
            {!rightPanelCollapsed && (
              <h2 className="text-white font-medium flex items-center gap-2">
                {rightPanelTitle}
                <Target className="w-4 h-4" />
              </h2>
            )}
          </div>

          {/* Panel Content */}
          {!rightPanelCollapsed && (
            <div className="flex-1 overflow-hidden">
              {rightPanel}
            </div>
          )}
        </div>
      </div>

      {/* Layout Mode Indicator */}
      <div className="fixed top-20 right-2 z-50">
        <Badge className={cn(
          'text-white text-xs',
          layoutMode === 'desktop' ? 'bg-green-500' :
          layoutMode === 'tablet' ? 'bg-yellow-500' :
          'bg-orange-500'
        )}>
          {getLayoutModeIcon()}
          {layoutMode.charAt(0).toUpperCase() + layoutMode.slice(1)}
        </Badge>
      </div>

      {/* Panel State Indicator */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 left-4 bg-[#2a2a2a] border border-gray-600 rounded-lg p-2 text-xs text-gray-300">
          <div className="font-medium text-blue-400 mb-1">Layout Debug</div>
          <div>Mode: {layoutMode}</div>
          <div>Left: {leftPanelCollapsed ? 'Collapsed' : 'Open'}</div>
          <div>Right: {rightPanelCollapsed ? 'Collapsed' : 'Open'}</div>
          {layoutMode === 'mobile' && <div>Focus: {mobilePanelFocus}</div>}
        </div>
      )}
    </div>
  );
}

// Information Density Optimization Component
export function DenseInfoCard({
  title,
  children,
  compact = false,
  className
}: {
  title: string;
  children: React.ReactNode;
  compact?: boolean;
  className?: string;
}) {
  return (
    <div className={cn(
      'bg-[#1a1a1b] border border-gray-700 rounded-lg',
      compact ? 'p-2' : 'p-3',
      className
    )}>
      <h3 className={cn(
        'text-white font-medium mb-2 flex items-center gap-2',
        compact ? 'text-xs' : 'text-sm'
      )}>
        <div className={cn(
          'w-2 h-2 bg-blue-500 rounded-full',
          compact && 'w-1.5 h-1.5'
        )} />
        {title}
      </h3>
      <div className={cn(
        'space-y-1',
        compact && 'text-xs'
      )}>
        {children}
      </div>
    </div>
  );
}

// Compact Data Row Component
export function CompactDataRow({
  label,
  value,
  change,
  className
}: {
  label: string;
  value: string | number;
  change?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}) {
  return (
    <div className={cn('flex items-center justify-between py-1', className)}>
      <span className="text-gray-400 text-xs">{label}</span>
      <div className="text-right">
        <span className="text-white text-xs font-medium">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {change && (
          <span className={cn(
            'ml-2 text-xs',
            change.isPositive ? 'text-red-400' : 'text-blue-400'
          )}>
            {change.isPositive ? '+' : ''}{change.value.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  );
}