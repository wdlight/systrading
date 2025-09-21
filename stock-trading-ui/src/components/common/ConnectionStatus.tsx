'use client';

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { ConnectionState } from '@/lib/types';

interface ConnectionStatusProps {
  connectionState: ConnectionState;
  showDetails?: boolean;
  className?: string;
}

export function ConnectionStatus({ 
  connectionState, 
  showDetails = false,
  className 
}: ConnectionStatusProps) {
  const { status, reconnectAttempts, lastConnected, error } = connectionState;

  const statusConfig = useMemo(() => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500',
          textColor: 'text-green-700 dark:text-green-400',
          label: '연결됨',
          icon: '●',
          pulse: false,
        };
      case 'connecting':
        return {
          color: 'bg-yellow-500',
          textColor: 'text-yellow-700 dark:text-yellow-400',
          label: '연결 중...',
          icon: '●',
          pulse: true,
        };
      case 'reconnecting':
        return {
          color: 'bg-orange-500',
          textColor: 'text-orange-700 dark:text-orange-400',
          label: `재연결 중... (${reconnectAttempts}/5)`,
          icon: '●',
          pulse: true,
        };
      case 'disconnected':
      default:
        return {
          color: 'bg-red-500',
          textColor: 'text-red-700 dark:text-red-400',
          label: '연결 끊김',
          icon: '●',
          pulse: false,
        };
    }
  }, [status, reconnectAttempts]);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* 상태 인디케이터 */}
      <div className="flex items-center gap-1.5">
        <div
          className={cn(
            'w-2 h-2 rounded-full transition-all duration-300',
            statusConfig.color,
            statusConfig.pulse && 'animate-pulse'
          )}
        />
        <span className={cn(
          'text-xs font-medium transition-colors duration-300',
          statusConfig.textColor
        )}>
          {statusConfig.label}
        </span>
      </div>

      {/* 상세 정보 */}
      {showDetails && (
        <div className="flex flex-col gap-1 text-xs text-gray-600 dark:text-gray-400">
          {lastConnected && (
            <div>
              마지막 연결: {lastConnected.toLocaleTimeString('ko-KR')}
            </div>
          )}
          {error && (
            <div className="text-red-600 dark:text-red-400 max-w-xs truncate">
              오류: {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// 헤더용 간단한 연결 상태 표시
export function SimpleConnectionStatus({ 
  connectionState,
  className 
}: {
  connectionState: ConnectionState;
  className?: string;
}) {
  const { status } = connectionState;

  const statusConfig = useMemo(() => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500',
          title: '실시간 데이터 연결됨',
        };
      case 'connecting':
      case 'reconnecting':
        return {
          color: 'bg-yellow-500',
          title: '연결 중...',
        };
      case 'disconnected':
      default:
        return {
          color: 'bg-red-500',
          title: '실시간 데이터 연결 끊김',
        };
    }
  }, [status]);

  return (
    <div 
      className={cn('flex items-center gap-1', className)}
      title={statusConfig.title}
    >
      <div
        className={cn(
          'w-2 h-2 rounded-full transition-all duration-300',
          statusConfig.color,
          (status === 'connecting' || status === 'reconnecting') && 'animate-pulse'
        )}
      />
      <span className="text-xs text-gray-600 dark:text-gray-400">
        실시간
      </span>
    </div>
  );
}

// 대시보드용 상세 연결 상태 카드
export function DetailedConnectionStatus({ 
  connectionState,
  className 
}: {
  connectionState: ConnectionState;
  className?: string;
}) {
  const { status, reconnectAttempts, lastConnected, error } = connectionState;

  const statusConfig = useMemo(() => {
    switch (status) {
      case 'connected':
        return {
          bgColor: 'bg-green-50 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          iconColor: 'text-green-600 dark:text-green-400',
          title: '실시간 연결 활성',
          description: '모든 데이터가 실시간으로 업데이트됩니다.',
        };
      case 'connecting':
        return {
          bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
          borderColor: 'border-yellow-200 dark:border-yellow-800',
          iconColor: 'text-yellow-600 dark:text-yellow-400',
          title: '연결 시도 중',
          description: '서버에 연결을 시도하고 있습니다...',
        };
      case 'reconnecting':
        return {
          bgColor: 'bg-orange-50 dark:bg-orange-900/20',
          borderColor: 'border-orange-200 dark:border-orange-800',
          iconColor: 'text-orange-600 dark:text-orange-400',
          title: '재연결 시도 중',
          description: `연결이 끊어져 재시도 중입니다. (${reconnectAttempts}/5)`,
        };
      case 'disconnected':
      default:
        return {
          bgColor: 'bg-red-50 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          iconColor: 'text-red-600 dark:text-red-400',
          title: '연결 끊김',
          description: '실시간 데이터를 받을 수 없습니다.',
        };
    }
  }, [status, reconnectAttempts]);

  return (
    <div className={cn(
      'p-4 rounded-lg border-2 transition-all duration-300',
      statusConfig.bgColor,
      statusConfig.borderColor,
      className
    )}>
      <div className="flex items-start gap-3">
        {/* 상태 아이콘 */}
        <div className={cn(
          'w-3 h-3 rounded-full mt-1 transition-all duration-300',
          statusConfig.iconColor.replace('text-', 'bg-'),
          (status === 'connecting' || status === 'reconnecting') && 'animate-pulse'
        )} />

        <div className="flex-1 min-w-0">
          {/* 제목 */}
          <h3 className={cn(
            'font-medium text-sm',
            statusConfig.iconColor
          )}>
            {statusConfig.title}
          </h3>

          {/* 설명 */}
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {statusConfig.description}
          </p>

          {/* 추가 정보 */}
          <div className="mt-2 space-y-1 text-xs text-gray-500 dark:text-gray-500">
            {lastConnected && (
              <div>
                마지막 연결: {lastConnected.toLocaleString('ko-KR')}
              </div>
            )}
            {error && (
              <div className="text-red-600 dark:text-red-400">
                오류: {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}