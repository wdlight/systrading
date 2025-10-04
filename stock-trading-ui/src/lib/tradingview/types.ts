// lib/tradingview/types.ts
import { UTCTimestamp } from 'lightweight-charts';

export interface TRViewCandleData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface TRViewVolumeData {
  time: UTCTimestamp;
  value: number;
  color?: string;
}
