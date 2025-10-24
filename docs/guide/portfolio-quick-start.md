# 포트폴리오 통합 빠른 시작 가이드

> **⚡ 5분 안에 포트폴리오 차트를 실제 데이터로 연동하기**

**예상 소요 시간**: 5분
**난이도**: ⭐☆☆☆☆ (매우 쉬움)

---

## 📋 빠른 체크리스트

### ✅ 사전 준비

- [ ] Node.js 설치됨 (`node --version`)
- [ ] Python 3.12 설치됨 (`python --version`)
- [ ] 프로젝트 다운로드 완료
- [ ] 한국투자증권 API 키 보유

### ✅ 실행 단계

- [ ] 백엔드 서버 실행
- [ ] 프론트엔드 서버 실행
- [ ] 브라우저에서 확인
- [ ] Mock 경고 사라짐 확인

---

## 🚀 1단계: 백엔드 서버 실행 (2분)

### 터미널 1 열기

```bash
# 프로젝트 루트로 이동
cd /home/wide/projects/systrading/backend

# 가상환경 활성화
source vkis/bin/activate

# 서버 실행
python app/main.py
```

**성공 메시지**:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 빠른 테스트

```bash
# 새 터미널에서 (백엔드는 계속 실행)
curl http://localhost:8000/health

# 응답: {"status":"ok"}
```

---

## 🎨 2단계: 프론트엔드 서버 실행 (1분)

### 터미널 2 열기

```bash
# 프론트엔드 디렉토리로 이동
cd /home/wide/projects/systrading/stock-trading-ui

# 서버 실행
npm run dev
```

**성공 메시지**:

```
✓ Ready in 3.2s
- Local: http://localhost:9000
```

---

## 🌐 3단계: 브라우저에서 확인 (1분)

### 페이지 열기

```
http://localhost:9000
```

### 포트폴리오 카드 찾기

1. **메인 대시보드**에서 스크롤
2. **"Portfolio Performance"** 카드 찾기
3. 차트 영역 확인

### 성공 확인

**✅ 성공 (실제 데이터 사용 중)**:

- 차트가 정상 표시됨
- Mock 경고 메시지 **없음**

**❌ 실패 (여전히 Mock 데이터)**:

```
⚠️ API 데이터가 준비되지 않아 샘플 데이터를 표시하고 있습니다.
```

---

## 🔍 4단계: 데이터 검증 (1분)

### 네트워크 탭 확인

1. **F12** 키 누르기
2. **Network** 탭 선택
3. **페이지 새로고침** (F5)
4. `portfolio/history` 요청 찾기

### 정상 응답 확인

**Status**: `200 OK`

**Response**:

```json
[
  {
    "date": "2025-10-11T15:30:00+09:00",
    "portfolio": 10000000,
    "benchmark": 9800000
  }
]
```

---

## 🎉 완료!

축하합니다! 포트폴리오 통합이 완료되었습니다!

### 다음 작업

- [ ] 다른 기간 테스트 (1D, 1W, 3M 등)
- [ ] 차트 스타일 커스터마이징
- [ ] 추가 기능 구현

---

## 🆘 문제 발생 시

### 빠른 해결법

| 문제               | 해결           |
| ---------------- | ------------ |
| Mock 경고 계속 표시    | 백엔드 서버 실행 확인 |
| CORS 에러          | 백엔드 재시작      |
| 404 Not Found    | URL 경로 확인    |
| 500 Server Error | 백엔드 로그 확인    |

### 상세 가이드

더 자세한 문제 해결은 다음 문서를 참고하세요:

- 📚 [메인 통합 가이드](./portfolio-frontend-integration-guide.md)
- 🔧 [트러블슈팅 FAQ](../troubleshooting/portfolio-integration-faq.md)
- 📖 [API 명세서](../api/portfolio-history-api-spec.md)

---

## 📋 명령어 모음 (복사용)

### 전체 실행 명령어

```bash
# 터미널 1: 백엔드
cd /home/wide/projects/systrading/backend
source vkis/bin/activate
python app/main.py

# 터미널 2: 프론트엔드 (새 터미널)
cd /home/wide/projects/systrading/stock-trading-ui
npm run dev

# 터미널 3: 테스트 (새 터미널)
curl http://localhost:8000/health
curl http://localhost:8000/api/portfolio/history?period=1M
```

### 서버 종료

```bash
# 각 터미널에서
Ctrl + C
```

---

**작성**: 2025-10-11
**버전**: 1.0.0
