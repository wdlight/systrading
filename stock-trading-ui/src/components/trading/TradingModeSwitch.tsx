'use client';

import { Button } from '@/components/ui/button';
import { Hand, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TradingModeSwitchProps {
  mode: 'manual' | 'auto';
  onChange: (mode: 'manual' | 'auto') => void;
  className?: string;
}

export function TradingModeSwitch({ mode, onChange, className }: TradingModeSwitchProps) {
  return (
    <div className={cn('flex gap-2', className)}>
      <Button
        variant={mode === 'manual' ? 'default' : 'outline'}
        onClick={() => onChange('manual')}
        className={cn(
          'flex items-center gap-2 transition-all duration-200',
          mode === 'manual'
            ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/20'
            : 'border-gray-600 text-gray-300 hover:bg-blue-600/10 hover:text-blue-400 hover:border-blue-400'
        )}
      >
        <Hand className="w-4 h-4" />
        수동 매매
      </Button>

      <Button
        variant={mode === 'auto' ? 'default' : 'outline'}
        onClick={() => onChange('auto')}
        className={cn(
          'flex items-center gap-2 transition-all duration-200',
          mode === 'auto'
            ? 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg shadow-purple-600/20'
            : 'border-gray-600 text-gray-300 hover:bg-purple-600/10 hover:text-purple-400 hover:border-purple-400'
        )}
      >
        <Bot className="w-4 h-4" />
        자동 매매
      </Button>
    </div>
  );
}