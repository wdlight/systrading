'use client';

import { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  title = '데이터가 없습니다',
  description = '새로운 데이터를 추가하면 이곳에서 확인할 수 있습니다.',
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-gray-600/80',
        'bg-[#1a1a1a] px-6 py-12 text-center text-sm text-gray-400',
        className,
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gray-700/40">
        {icon ?? <Inbox className="h-7 w-7 text-gray-500" />}
      </div>
      <div>
        <p className="text-base font-semibold text-gray-200">{title}</p>
        {description && (
          <p className="mt-1 text-sm text-gray-400/90">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
