/**
 * 날짜/시간 유틸리티 함수
 * 한국 표준시(KST, UTC+9) 처리
 */

/**
 * 현재 한국 표준시(KST) 날짜를 YYYY-MM-DD 형식으로 반환
 *
 * 중요: new Date().toISOString()은 UTC 기준이므로,
 * 한국 시간 자정~오전 8:59분에는 전날 날짜가 반환됨
 *
 * @returns {string} YYYY-MM-DD 형식의 한국 시간 기준 오늘 날짜
 *
 * @example
 * // 한국 시간: 2025-10-04 02:00 (자정 넘음)
 * // UTC 시간: 2025-10-03 17:00 (아직 전날)
 * getKSTToday() // "2025-10-04" ✅ (한국 시간 기준)
 * new Date().toISOString().split('T')[0] // "2025-10-03" ❌ (UTC 기준, 틀림!)
 */
export function getKSTToday(): string {
  const now = new Date();

  // UTC 시간을 KST(UTC+9)로 변환
  const kstOffset = 9 * 60; // 9시간 = 540분
  const kstTime = new Date(now.getTime() + kstOffset * 60 * 1000);

  // ISO 문자열에서 날짜 부분만 추출 (YYYY-MM-DD)
  return kstTime.toISOString().split('T')[0];
}

/**
 * 주어진 날짜가 KST 기준 오늘인지 확인
 *
 * @param {string} dateStr - YYYY-MM-DD 형식의 날짜 문자열
 * @returns {boolean} 오늘이면 true
 *
 * @example
 * isKSTToday("2025-10-03") // 한국이 10월 3일이면 true
 */
export function isKSTToday(dateStr: string): boolean {
  return dateStr === getKSTToday();
}

/**
 * 현재 KST 시간을 Date 객체로 반환
 *
 * @returns {Date} KST 기준 현재 시간
 */
export function getKSTNow(): Date {
  const now = new Date();
  const kstOffset = 9 * 60;
  return new Date(now.getTime() + kstOffset * 60 * 1000);
}

/**
 * KST 날짜 문자열을 Date 객체로 변환
 *
 * @param {string} dateStr - YYYY-MM-DD 형식
 * @returns {Date} Date 객체 (KST 자정)
 */
export function parseKSTDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  // UTC 기준으로 만든 후 9시간 뺌 (KST 자정 = UTC 15:00 전날)
  return new Date(Date.UTC(year, month - 1, day, -9, 0, 0));
}

/**
 * Date 객체를 KST 기준 YYYY-MM-DD 문자열로 변환
 *
 * @param {Date} date - Date 객체
 * @returns {string} YYYY-MM-DD 형식의 KST 날짜
 */
export function formatKSTDate(date: Date): string {
  const kstOffset = 9 * 60;
  const kstTime = new Date(date.getTime() + kstOffset * 60 * 1000);
  return kstTime.toISOString().split('T')[0];
}
