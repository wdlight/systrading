import { UserNotification } from '@/lib/types';

export const mockUserNotifications: UserNotification[] = [
  {
    id: 'notif-1',
    type: 'order',
    title: '주문 체결 완료',
    message: '삼성전자(005930) 30주 매수가 체결되었습니다.',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    read: false,
    metadata: {
      stockCode: '005930',
      orderType: 'buy',
      amount: 2190000,
    },
  },
  {
    id: 'notif-2',
    type: 'alert',
    title: '기술적 신호 발생',
    message: 'NAVER(035420)의 RSI가 70을 초과했습니다.',
    timestamp: new Date(Date.now() - 35 * 60 * 1000),
    read: false,
    metadata: {
      stockCode: '035420',
    },
  },
  {
    id: 'notif-3',
    type: 'system',
    title: '포트폴리오 리밸런싱 제안',
    message: '현금 비중이 35% 이상입니다. 새로운 포지션을 고려해 보세요.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
  },
];
