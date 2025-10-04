// 브라우저의 로컬 시간(KST로 간주)을 'YYYY-MM-DD' 형식으로 변환
function getLocalDateAsString(date: Date): string {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 현재 날짜를 KST 기준으로 반환
export function getKSTToday(): string {
  return getLocalDateAsString(new Date());
}

// 주어진 Date 객체를 KST 날짜 문자열로 변환
export function toKSTDateString(date: Date): string {
  return getLocalDateAsString(date);
}

// 주어진 날짜가 KST 기준으로 오늘인지 확인
export function isKSTToday(dateString: string): boolean {
    if (!dateString) return false;
    return dateString === getKSTToday();
}
