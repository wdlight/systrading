'use client';

import { TabButtonProps } from '@/lib/types/components';
import { cn } from '@/lib/utils';

export function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
  className
}: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex-1 flex items-center justify-center gap-2 p-3 text-sm font-medium transition-all duration-200',
        'border-b-2 border-transparent',
        active
          ? 'text-blue-400 bg-blue-500/10 border-blue-400 shadow-sm'
          : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/50',
        className
      )}
      type="button"
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  );
}