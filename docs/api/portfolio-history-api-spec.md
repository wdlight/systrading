# Portfolio History API 명세서

**API 버전**: 2.0.0
**최종 수정**: 2025-10-11
**Base URL**: `http://localhost:8000`

---

## 📋 목차

1. [개요](#개요)
2. [인증](#인증)
3. [엔드포인트](#엔드포인트)
4. [데이터 타입](#데이터-타입)
5. [에러 코드](#에러-코드)
6. [사용 예제](#사용-예제)
7. [성능 및 캐싱](#성능-및-캐싱)

---

## 개요

Portfolio History API는 사용자의 포트폴리오 평가 금액과 KOSPI 벤치마크를 시계열 데이터로 제공합니다.

### 주요 기능

- 📊 기간별 포트폴리오 성과 조회 (1일 ~ 전체 기간)
- 📈 KOSPI 벤치마크 비교 데이터 제공
- ⚡ Redis 캐시를 통한 빠른 응답 (5분 TTL)
- 🔄 실시간 계좌 데이터 기반 계산

### 지원 기간

| 기간 코드 | 설명 | 데이터 포인트 수 (예상) |
|-----------|------|------------------------|
| `1D` | 1일 | 30~78 (분봉 기준) |
| `1W` | 1주 | 5~7 (일봉 기준) |
| `1M` | 1개월 | 20~22 (일봉 기준) |
| `3M` | 3개월 | 60~66 (일봉 기준) |
| `6M` | 6개월 | 120~132 (일봉 기준) |
| `1Y` | 1년 | 240~252 (일봉 기준) |
| `ALL` | 전체 | 가변 (계좌 개설일부터) |

---

## 인증

현재 버전은 인증이 필요하지 않습니다. (향후 추가 예정)

---

## 엔드포인트

### GET /api/portfolio/history

포트폴리오 성과 이력을 조회합니다.

#### Request

**HTTP Method**: `GET`

**URL**: `/api/portfolio/history`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 | 예시 |
|----------|------|------|--------|------|------|
| `period` | string | ❌ | `1W` | 조회 기간 | `1D`, `1W`, `1M`, `3M`, `6M`, `1Y`, `ALL` |

**허용되는 period 값**:
- `1D`: 1일 (당일 분봉 데이터)
- `1W`: 1주일
- `1M`: 1개월
- `3M`: 3개월
- `6M`: 6개월
- `1Y`: 1년
- `ALL`: 전체 기간

#### Response

**Status Code**: `200 OK`

**Content-Type**: `application/json`

**Response Body**: `PortfolioHistoryPoint[]`

```typescript
interface PortfolioHistoryPoint {
  date: string;        // ISO 8601 format (KST)
  portfolio: number;   // 포트폴리오 평가 금액 (원)
  benchmark: number;   // KOSPI 벤치마크 (정규화된 값)
}
```

**예시 응답**:
```json
[
  {
    "date": "2025-10-01T15:30:00+09:00",
    "portfolio": 10000000,
    "benchmark": 9800000
  },
  {
    "date": "2025-10-02T15:30:00+09:00",
    "portfolio": 10150000,
    "benchmark": 9850000
  },
  {
    "date": "2025-10-03T15:30:00+09:00",
    "portfolio": 10200000,
    "benchmark": 9900000
  }
]
```

#### Error Responses

##### 204 No Content

데이터가 없을 때 반환됩니다.

```json
{
  "detail": "데이터 없음"
}
```

**발생 조건**:
- 조회 기간에 거래 데이터가 없음
- 계좌 잔고가 0원
- 보유 종목이 없음

##### 400 Bad Request

잘못된 파라미터를 전달했을 때 반환됩니다.

```json
{
  "detail": "Invalid period. Must be one of: 1D, 1W, 1M, 3M, 6M, 1Y, ALL"
}
```

**발생 조건**:
- `period` 값이 허용 목록에 없음
- 쿼리 파라미터 형식 오류

##### 500 Internal Server Error

서버 내부 오류 발생 시 반환됩니다.

```json
{
  "detail": "Portfolio history 실패: [상세 에러 메시지]"
}
```

**발생 조건**:
- 한국투자증권 API 연동 실패
- 데이터 계산 로직 오류
- Redis 연결 오류 (캐시는 실패해도 동작함)

---

## 데이터 타입

### PortfolioHistoryPoint

포트폴리오 히스토리 데이터 포인트

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `date` | string | ISO 8601 날짜/시간 (KST, UTC+09:00) | `"2025-10-11T15:30:00+09:00"` |
| `portfolio` | number | 포트폴리오 총 평가 금액 (원) | `10000000` |
| `benchmark` | number | KOSPI 벤치마크 (정규화, 원) | `9800000` |

### 날짜 형식

- **포맷**: ISO 8601
- **타임존**: KST (Korea Standard Time, UTC+09:00)
- **예시**: `2025-10-11T15:30:00+09:00`

### 정규화 로직

**벤치마크 정규화**:
```python
# 시작점을 포트폴리오와 동일하게 맞춤
benchmark_normalized = (kospi_current / kospi_start) * portfolio_start
```

**목적**: 포트폴리오와 벤치마크의 절대 금액 차이를 없애고 수익률만 비교

---

## 에러 코드

### HTTP Status Codes

| 코드 | 의미 | 설명 |
|------|------|------|
| `200` | OK | 정상 응답 |
| `204` | No Content | 데이터 없음 |
| `400` | Bad Request | 잘못된 요청 |
| `500` | Internal Server Error | 서버 오류 |

### 에러 응답 형식

```typescript
interface ErrorResponse {
  detail: string;  // 에러 상세 메시지
}
```

---

## 사용 예제

### cURL

#### 기본 요청
```bash
curl http://localhost:8000/api/portfolio/history
```

#### 기간 지정
```bash
curl http://localhost:8000/api/portfolio/history?period=1M
```

#### JSON 포맷팅
```bash
curl http://localhost:8000/api/portfolio/history?period=1M | jq
```

#### 응답 저장
```bash
curl http://localhost:8000/api/portfolio/history?period=1M > portfolio.json
```

### JavaScript (fetch)

```javascript
// 기본 요청
const response = await fetch('http://localhost:8000/api/portfolio/history');
const data = await response.json();
console.log(data);

// 기간 지정
const response = await fetch('http://localhost:8000/api/portfolio/history?period=1M');
const data = await response.json();

// 에러 핸들링
try {
  const response = await fetch('http://localhost:8000/api/portfolio/history?period=1M');

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  console.log('Portfolio history:', data);
} catch (error) {
  console.error('API 호출 실패:', error);
}
```

### TypeScript (API Client)

```typescript
import { apiClient } from '@/lib/api-client';
import { PortfolioHistoryPoint, PortfolioTimeRange } from '@/lib/types';

// 타입 안전한 호출
async function getPortfolioHistory(period: PortfolioTimeRange): Promise<PortfolioHistoryPoint[]> {
  try {
    const data = await apiClient.getPortfolioHistory(period);
    return data;
  } catch (error) {
    console.error('Failed to fetch portfolio history:', error);
    return [];
  }
}

// 사용
const data = await getPortfolioHistory('1M');
```

### Python (requests)

```python
import requests
from typing import List, Dict

def get_portfolio_history(period: str = '1W') -> List[Dict]:
    """포트폴리오 이력 조회"""
    url = f'http://localhost:8000/api/portfolio/history'
    params = {'period': period}

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()

# 사용
data = get_portfolio_history('1M')
print(f"총 {len(data)}개의 데이터 포인트")
```

### React Hook

```typescript
import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { PortfolioHistoryPoint, PortfolioTimeRange } from '@/lib/types';

function usePortfolioHistory(period: PortfolioTimeRange) {
  const [data, setData] = useState<PortfolioHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const result = await apiClient.getPortfolioHistory(period);
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [period]);

  return { data, loading, error };
}

// 사용
function PortfolioChart() {
  const { data, loading, error } = usePortfolioHistory('1M');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return <Chart data={data} />;
}
```

---

## 성능 및 캐싱

### Redis 캐싱

**캐시 키 형식**:
```
portfolio_history:{period}
```

**예시**:
- `portfolio_history:1D`
- `portfolio_history:1W`
- `portfolio_history:1M`

**TTL (Time To Live)**:
- 300초 (5분)

**캐싱 플로우**:
1. 요청 수신
2. Redis에서 캐시 확인
3. 캐시 히트: 즉시 반환
4. 캐시 미스: 계산 후 저장
5. 응답 반환

### 성능 특징

| 상황 | 응답 시간 (예상) |
|------|------------------|
| 캐시 히트 | < 50ms |
| 캐시 미스 (1D) | 500ms ~ 2s |
| 캐시 미스 (1M) | 1s ~ 3s |
| 캐시 미스 (1Y) | 3s ~ 10s |

**최적화 팁**:
1. 동일 기간 반복 조회 시 캐시 활용
2. 여러 기간 동시 조회 시 병렬 요청
3. 프론트엔드에서 추가 캐싱 고려

### 데이터 신선도

- **실시간 데이터**: 최대 5분 지연 (캐시 TTL)
- **스냅샷 업데이트**: 5분마다 백그라운드 수집
- **장중/장후**: 장중에는 실시간, 장후에는 마지막 데이터 유지

---

## 제한사항 및 주의사항

### 현재 제한사항

1. **인증 없음**: 현재 버전은 인증 불필요 (향후 추가 예정)
2. **단일 계좌**: 하나의 계좌만 조회 가능
3. **현금 흐름 미반영**: 입출금, 배당 등 미반영 (Phase 2에서 개선 예정)
4. **추정 데이터**: 과거 데이터는 현재 보유량 기반 추정

### 주의사항

- 장 시작 전/후에는 데이터가 업데이트되지 않을 수 있음
- 휴장일에는 이전 거래일 데이터 반환
- `ALL` 기간은 데이터 양이 많아 응답 시간이 길 수 있음

---

## 버전 히스토리

### v2.0.0 (2025-10-11)
- ✨ Redis 캐싱 추가
- ✨ 벤치마크 정규화 개선
- ✨ 스냅샷 기반 계산 로직
- 🐛 타임존 처리 버그 수정

### v1.0.0 (2025-10-10)
- 🎉 최초 릴리스
- ✨ 기본 포트폴리오 이력 조회
- ✨ KOSPI 벤치마크 비교

---

## 관련 문서

- 📚 [통합 가이드](../guide/portfolio-frontend-integration-guide.md)
- 🚀 [빠른 시작](../guide/portfolio-quick-start.md)
- 🔧 [트러블슈팅](../troubleshooting/portfolio-integration-faq.md)
- 🏗️ [아키텍처](../architecture/redis-portfolio-history-cache.md)

---

**유지보수**: Backend Team
**문의**: GitHub Issues
