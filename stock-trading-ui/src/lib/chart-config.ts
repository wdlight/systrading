// Helper to check if a timeframe is intraday
export const isIntraday = (timeframe: string): boolean => {
  return timeframe.includes('m') || timeframe.includes('h');
};

// Formatter functions for different time units
const formatters = {
  time: (date: Date) => `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`, // "HH:MM"
  day: (date: Date) => `${date.getMonth() + 1}/${date.getDate()}`, // "MM/DD"
  month: (date: Date) => `${date.getFullYear()}.${(date.getMonth() + 1).toString().padStart(2, '0')}`, // "YYYY.MM"
  year: (date: Date) => `${date.getFullYear()}`, // "YYYY"
};

// Configuration for each timeframe
export const TIMEFRAME_CONFIG: { [key: string]: { mainUnit: string; formatter: (date: Date) => string } } = {
  '1m':   { mainUnit: 'thirty_minute', formatter: formatters.time },
  '5m':   { mainUnit: 'hour',           formatter: formatters.time },
  '10m':  { mainUnit: 'hour',           formatter: formatters.time },
  '30m':  { mainUnit: 'hour',           formatter: formatters.time },
  '1h':   { mainUnit: 'day',            formatter: formatters.day },
  '1D':   { mainUnit: 'month',          formatter: formatters.day },
  '1W':   { mainUnit: 'year',           formatter: formatters.month },
  '1M':   { mainUnit: 'year',           formatter: formatters.month },
};

/**
 * Generates an array of timestamps for X-axis ticks based on a given time range and timeframe.
 * @param startTime - The start of the time range (in ms).
 * @param endTime - The end of the time range (in ms).
 * @param timeframe - The current chart timeframe (e.g., '1m', '1D').
 * @returns An array of timestamps (in ms) for the ticks.
 */
export const generateTimeTicks = (startTime: number, endTime: number, timeframe: string): number[] => {
  if (!startTime || !endTime) {
    return [];
  }

  const config = TIMEFRAME_CONFIG[timeframe];
  if (!config) {
    return [];
  }

  const ticks: number[] = [];
  const startDate = new Date(startTime);
  const endDate = new Date(endTime);

  let cursor = new Date(startDate);
  cursor.setSeconds(0, 0);

  switch (config.mainUnit) {
    case 'fifteen_minute':
      const remainder = cursor.getMinutes() % 15;
      if (remainder !== 0) {
        cursor.setMinutes(cursor.getMinutes() + (15 - remainder));
      }
      while (cursor < endDate) {
        ticks.push(cursor.getTime());
        cursor.setMinutes(cursor.getMinutes() + 15);
      }
      break;

    case 'thirty_minute':
      // Round down to the nearest 30-minute mark
      cursor.setMinutes(Math.floor(cursor.getMinutes() / 30) * 30, 0, 0);
      
      while (cursor <= endDate) {
        if (cursor >= startDate) {
          ticks.push(cursor.getTime());
        }
        cursor.setMinutes(cursor.getMinutes() + 30);
      }
      break;

    case 'hour':
      if (cursor.getMinutes() !== 0) {
        cursor.setHours(cursor.getHours() + 1);
        cursor.setMinutes(0);
      }
      while (cursor < endDate) {
        ticks.push(cursor.getTime());
        cursor.setHours(cursor.getHours() + 1);
      }
      break;
    
    case 'day':
      cursor.setHours(0, 0, 0, 0);
      if (cursor.getTime() <= startDate.getTime()) {
          cursor.setDate(cursor.getDate() + 1);
      }
      while (cursor < endDate) {
        ticks.push(cursor.getTime());
        cursor.setDate(cursor.getDate() + 1);
      }
      break;

    case 'month':
      cursor.setHours(0, 0, 0, 0);
      cursor.setDate(1);
      if (cursor.getTime() <= startDate.getTime()) {
          cursor.setMonth(cursor.getMonth() + 1);
      }
      while (cursor < endDate) {
        ticks.push(cursor.getTime());
        cursor.setMonth(cursor.getMonth() + 1);
      }
      break;
    
    case 'year':
      cursor.setHours(0, 0, 0, 0);
      cursor.setDate(1);
      cursor.setMonth(0);
      if (cursor.getTime() <= startDate.getTime()) {
          cursor.setFullYear(cursor.getFullYear() + 1);
      }
      while (cursor < endDate) {
        ticks.push(cursor.getTime());
        cursor.setFullYear(cursor.getFullYear() + 1);
      }
      break;
  }

  return ticks;
};
