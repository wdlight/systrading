'use client';

import { AlertTriangle } from 'lucide-react';
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface ErrorStateProps {
  title?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function ErrorState({
  title = '문제가 발생했습니다',
  description,
  icon,
  action,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border border-red-500/30',
        'bg-red-500/5 px-6 py-10 text-center text-sm text-red-200',
        className,
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500/15">
        {icon ?? <AlertTriangle className="h-6 w-6 text-red-400" />}
      </div>
      <div>
        <p className="text-base font-semibold text-red-300">{title}</p>
        {description && (
          <p className="mt-1 text-sm text-red-200/80">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
