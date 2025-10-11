# 포트폴리오 통합 FAQ & 트러블슈팅

> **자주 묻는 질문과 문제 해결 방법 모음**

**최종 수정**: 2025-10-11
**난이도**: ⭐⭐⭐☆☆ (중급)

---

## 📋 목차

1. [일반 질문](#일반-질문)
2. [설치 및 설정 문제](#설치-및-설정-문제)
3. [백엔드 문제](#백엔드-문제)
4. [프론트엔드 문제](#프론트엔드-문제)
5. [통합 문제](#통합-문제)
6. [성능 문제](#성능-문제)
7. [데이터 문제](#데이터-문제)
8. [디버깅 팁](#디버깅-팁)

---

## 일반 질문

### Q1: 포트폴리오 통합이 무엇인가요?

**A**: 백엔드에서 구현한 포트폴리오 이력 조회 API를 프론트엔드 차트와 연결하여, Mock 데이터 대신 **실제 계좌 데이터**를 표시하는 작업입니다.

**통합 전**:
- ⚠️ Mock 데이터로 차트 표시
- 실제 성과 확인 불가

**통합 후**:
- ✅ 실시간 계좌 데이터로 차트 표시
- ✅ KOSPI 벤치마크와 비교
- ✅ 다양한 기간 조회 가능

### Q2: 얼마나 걸리나요?

**A**: 환경에 따라 다릅니다.

| 상황 | 예상 시간 |
|------|----------|
| 모든 준비 완료 | 5분 |
| 처음 설정 | 30분 ~ 1시간 |
| 문제 발생 시 | 1~2시간 |

### Q3: 어떤 기술을 알아야 하나요?

**A**: 기본적인 지식만 있으면 됩니다.

**필수**:
- ✅ 터미널 기본 명령어 (cd, ls 등)
- ✅ 텍스트 에디터 사용법
- ✅ 웹 브라우저 개발자 도구 (F12)

**선택** (있으면 좋음):
- Python 기초
- JavaScript/TypeScript 기초
- REST API 개념
- Git 사용법

### Q4: Redis가 반드시 필요한가요?

**A**: 아니요, 선택사항입니다.

**Redis 없이**:
- ✅ 정상 동작함
- ❌ 응답이 느릴 수 있음 (캐시 없음)

**Redis 사용 시**:
- ✅ 빠른 응답 (5분 캐시)
- ✅ API 호출 감소

**설치 방법** (Ubuntu/WSL):
```bash
sudo apt-get install redis-server
sudo service redis-server start
```

### Q5: 어떤 브라우저를 사용해야 하나요?

**A**: Chrome을 권장합니다.

| 브라우저 | 지원 | 개발자 도구 |
|----------|------|-------------|
| Chrome | ✅ 완전 지원 | 최고 |
| Firefox | ✅ 지원 | 우수 |
| Safari | ✅ 지원 | 보통 |
| Edge | ✅ 지원 | 우수 |

---

## 설치 및 설정 문제

### Q6: "python: command not found" 에러가 나요

**A**: Python이 설치되지 않았거나 PATH 설정이 안 되어 있습니다.

**해결 방법**:

1. **Python 설치 확인**:
   ```bash
   python --version
   python3 --version
   ```

2. **설치되지 않았다면**:
   ```bash
   # Ubuntu/WSL
   sudo apt-get update
   sudo apt-get install python3.12

   # Mac (Homebrew)
   brew install python@3.12
   ```

3. **python 명령어 연결**:
   ```bash
   # python3를 python으로 사용
   alias python=python3
   ```

### Q7: "npm: command not found" 에러가 나요

**A**: Node.js가 설치되지 않았습니다.

**해결 방법**:

1. **Node.js 설치**:
   - https://nodejs.org/ 방문
   - LTS 버전 다운로드 및 설치

2. **설치 확인**:
   ```bash
   node --version  # v18.x.x 이상
   npm --version   # 9.x.x 이상
   ```

### Q8: 가상환경 활성화가 안 돼요

**문제**:
```bash
source vkis/bin/activate
# bash: vkis/bin/activate: No such file or directory
```

**원인**: 가상환경이 생성되지 않음

**해결 방법**:

1. **가상환경 생성**:
   ```bash
   cd backend
   python -m venv vkis
   ```

2. **활성화**:
   ```bash
   source vkis/bin/activate  # Linux/Mac
   vkis\Scripts\activate     # Windows
   ```

3. **확인**:
   ```bash
   which python
   # /home/wide/projects/systrading/backend/vkis/bin/python
   ```

### Q9: requirements.txt 설치가 실패해요

**문제**:
```bash
pip install -r requirements.txt
# ERROR: Could not find a version that satisfies...
```

**해결 방법**:

1. **pip 업그레이드**:
   ```bash
   pip install --upgrade pip
   ```

2. **Python 버전 확인**:
   ```bash
   python --version
   # Python 3.12.x 이어야 함
   ```

3. **개별 설치 시도**:
   ```bash
   pip install fastapi uvicorn redis pydantic
   ```

### Q10: .env 파일이 없어요

**A**: 직접 생성해야 합니다.

**해결 방법**:

1. **예제 복사**:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **직접 생성**:
   ```bash
   cat > backend/.env << 'EOF'
   KOREA_INVEST_APP_KEY=your_key_here
   KOREA_INVEST_APP_SECRET=your_secret_here
   KOREA_INVEST_ACCOUNT_NO=your_account
   REDIS_URL=redis://localhost:6379/0
   EOF
   ```

3. **편집**:
   ```bash
   nano backend/.env
   # 또는
   code backend/.env
   ```

---

## 백엔드 문제

### Q11: "ModuleNotFoundError: No module named 'fastapi'"

**원인**: 가상환경이 활성화되지 않았거나 패키지 미설치

**해결 방법**:

1. **가상환경 확인**:
   ```bash
   which python
   # vkis/bin/python 경로 확인
   ```

2. **활성화 안 되어 있다면**:
   ```bash
   source vkis/bin/activate
   ```

3. **패키지 설치**:
   ```bash
   pip install -r requirements.txt
   ```

### Q12: "Address already in use" 포트 8000 충돌

**원인**: 다른 프로세스가 8000 포트 사용 중

**해결 방법**:

1. **포트 사용 프로세스 찾기**:
   ```bash
   lsof -i :8000
   # 또는
   netstat -tuln | grep 8000
   ```

2. **프로세스 종료**:
   ```bash
   kill -9 <PID>
   ```

3. **다른 포트 사용**:
   ```bash
   # main.py 수정
   uvicorn app.main:app --port 8001
   ```

### Q13: 한국투자증권 API 키 오류

**문제**:
```
ERROR: 인증 실패
```

**해결 방법**:

1. **.env 파일 확인**:
   ```bash
   cat backend/.env | grep KOREA_INVEST
   ```

2. **API 키 재발급**:
   - 한국투자증권 홈페이지 접속
   - API 키 재발급
   - .env 파일 업데이트

3. **환경 변수 재로드**:
   ```bash
   # 서버 재시작
   Ctrl+C
   python app/main.py
   ```

### Q14: "Circular Import" 에러

**원인**: 모듈 간 순환 참조

**해결 방법**:

1. **임포트 순서 확인**:
   ```python
   # 잘못된 예
   from app.core import config
   from app.core.config import settings  # 중복
   ```

2. **지연 임포트 사용**:
   ```python
   def some_function():
       from app.services import SomeService  # 함수 내부에서 임포트
       ...
   ```

3. **백엔드 재시작**:
   ```bash
   Ctrl+C
   python app/main.py
   ```

---

## 프론트엔드 문제

### Q15: "npm install" 실패

**문제**:
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE could not resolve
```

**해결 방법**:

1. **node_modules 삭제**:
   ```bash
   rm -rf node_modules package-lock.json
   ```

2. **재설치**:
   ```bash
   npm install
   ```

3. **강제 설치** (최후의 수단):
   ```bash
   npm install --legacy-peer-deps
   ```

### Q16: "Port 9000 already in use"

**원인**: 다른 Next.js 서버가 실행 중

**해결 방법**:

1. **프로세스 찾기**:
   ```bash
   lsof -i :9000
   ```

2. **종료**:
   ```bash
   kill -9 <PID>
   ```

3. **다른 포트 사용**:
   ```bash
   PORT=3000 npm run dev
   ```

### Q17: "Hydration mismatch" 에러

**원인**: 서버/클라이언트 렌더링 불일치

**해결 방법**:

1. **useEffect로 클라이언트 전용 처리**:
   ```typescript
   const [mounted, setMounted] = useState(false);

   useEffect(() => {
     setMounted(true);
   }, []);

   if (!mounted) return null;
   ```

2. **dynamic import 사용**:
   ```typescript
   const Chart = dynamic(() => import('./Chart'), {
     ssr: false
   });
   ```

### Q18: 차트가 렌더링 안 돼요

**원인**: 데이터 형식 오류 또는 Recharts 문제

**해결 방법**:

1. **Console 확인**:
   ```
   F12 > Console 탭
   ```

2. **데이터 구조 확인**:
   ```javascript
   console.log('Chart data:', chartData);
   ```

3. **필수 필드 확인**:
   ```typescript
   // 필요: date, portfolio, benchmark
   chartData.forEach(point => {
     console.log(point.date, point.portfolio, point.benchmark);
   });
   ```

---

## 통합 문제

### Q19: Mock 데이터 경고가 계속 떠요

**증상**:
```
⚠️ API 데이터가 준비되지 않아 샘플 데이터를 표시하고 있습니다.
```

**진단 체크리스트**:

- [ ] 백엔드 서버 실행 중? (`curl http://localhost:8000/health`)
- [ ] 프론트엔드 환경 변수 확인? (`cat .env.local`)
- [ ] Network 탭에서 요청 확인? (F12 > Network)
- [ ] API 응답 200 OK? (Network 탭)
- [ ] 응답 데이터가 배열? (Network > Preview)

**해결 방법**:

1. **백엔드 API 테스트**:
   ```bash
   curl http://localhost:8000/api/portfolio/history?period=1M
   ```

2. **CORS 확인**:
   ```python
   # backend/app/main.py
   allow_origins=["http://localhost:9000"]
   ```

3. **프론트엔드 API URL 확인**:
   ```bash
   # stock-trading-ui/.env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### Q20: "CORS policy" 에러

**증상** (Console):
```
Access to fetch at 'http://localhost:8000/...'
from origin 'http://localhost:9000' has been blocked by CORS policy
```

**해결 방법**:

1. **백엔드 CORS 설정 확인**:
   ```python
   # backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:9000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **서버 재시작**:
   ```bash
   # 백엔드 터미널
   Ctrl+C
   python app/main.py
   ```

3. **프론트엔드 재시작**:
   ```bash
   # 프론트엔드 터미널
   Ctrl+C
   npm run dev
   ```

### Q21: API 요청이 404 Not Found

**원인**: 엔드포인트 경로 오류

**해결 방법**:

1. **URL 확인**:
   ```
   올바름: http://localhost:8000/api/portfolio/history
   틀림: http://localhost:8000/portfolio/history
   ```

2. **FastAPI 문서 확인**:
   ```
   http://localhost:8000/docs
   ```

3. **라우터 확인**:
   ```python
   # backend/app/main.py
   app.include_router(portfolio_router, prefix="/api/portfolio")
   ```

### Q22: API 응답이 500 에러

**원인**: 백엔드 로직 오류

**해결 방법**:

1. **백엔드 로그 확인**:
   - 백엔드 터미널에서 Traceback 확인

2. **일반적인 원인**:
   - API 키 오류
   - 계좌 잔고 없음
   - 거래 데이터 없음

3. **디버그 모드 실행**:
   ```bash
   python app/main.py --reload --log-level debug
   ```

---

## 성능 문제

### Q23: API 응답이 너무 느려요

**원인**: 캐시 미사용 또는 긴 계산 시간

**해결 방법**:

1. **Redis 캐시 활성화**:
   ```bash
   # Redis 설치 및 시작
   sudo apt-get install redis-server
   sudo service redis-server start
   ```

2. **캐시 확인**:
   ```bash
   # 백엔드 로그에서
   ✅ 캐시 사용: portfolio_history:1M  # 빠름
   🔄 캐시 없음, 새로 계산: portfolio_history:1M  # 느림
   ```

3. **기간 조정**:
   - `1Y`, `ALL`은 느릴 수 있음
   - 짧은 기간(`1D`, `1W`)으로 테스트

### Q24: 차트가 끊기거나 느려요

**원인**: 데이터 포인트 과다 또는 렌더링 최적화 필요

**해결 방법**:

1. **데이터 포인트 수 확인**:
   ```javascript
   console.log('Data points:', chartData.length);
   // 1000개 이상이면 과다
   ```

2. **샘플링 적용**:
   ```typescript
   const sampledData = chartData.filter((_, i) => i % 5 === 0);
   ```

3. **메모이제이션 사용**:
   ```typescript
   const chartData = useMemo(() => history, [history]);
   ```

---

## 데이터 문제

### Q25: 차트 데이터가 이상해요

**증상**: 포트폴리오 값이 0원 또는 음수

**원인**: 계좌 데이터 오류 또는 계산 로직 문제

**해결 방법**:

1. **원본 API 응답 확인**:
   ```bash
   curl http://localhost:8000/api/portfolio/history?period=1M | jq
   ```

2. **계좌 잔고 확인**:
   ```bash
   curl http://localhost:8000/api/account/balance
   ```

3. **로그 확인**:
   - 백엔드 터미널에서 에러 메시지 찾기

### Q26: 벤치마크가 0으로 나와요

**원인**: KOSPI 데이터 조회 실패

**해결 방법**:

1. **벤치마크 서비스 로그 확인**:
   ```
   WARNING: 벤치마크 데이터 조회 실패, flat-line 반환
   ```

2. **pykrx 설치 확인**:
   ```bash
   pip list | grep pykrx
   ```

3. **수동 테스트**:
   ```python
   from pykrx import stock
   stock.get_index_ohlcv("20250101", "20251011", "1001")
   ```

### Q27: 특정 기간만 데이터가 없어요

**원인**: 해당 기간 거래 없음 또는 휴장일

**해결 방법**:

1. **거래 이력 확인**:
   - 해당 기간에 실제 거래가 있었는지 확인

2. **달력 확인**:
   - 주말, 공휴일은 데이터 없음

3. **로그 확인**:
   ```
   INFO: 조회 기간: 2025-10-01 ~ 2025-10-11
   INFO: 거래일 수: 7일
   ```

---

## 디버깅 팁

### 디버깅 워크플로우

```
1. 문제 확인
   ↓
2. 에러 메시지 읽기
   ↓
3. 로그 확인
   - 백엔드: 터미널
   - 프론트엔드: Console (F12)
   ↓
4. 네트워크 확인
   - Network 탭 (F12)
   ↓
5. 단계별 테스트
   - 백엔드만
   - 프론트엔드만
   - 통합
   ↓
6. FAQ 검색
   ↓
7. 문서 확인
```

### 필수 디버깅 도구

1. **브라우저 개발자 도구** (F12)
   - Console: 에러 메시지
   - Network: API 요청/응답
   - Elements: DOM 확인

2. **터미널 명령어**
   ```bash
   # 서버 실행 확인
   ps aux | grep python
   ps aux | grep node

   # 포트 확인
   lsof -i :8000
   lsof -i :9000

   # API 테스트
   curl http://localhost:8000/health
   ```

3. **로그 파일**
   - 백엔드: 터미널 출력
   - 프론트엔드: 브라우저 Console

### 디버깅 체크리스트

문제 발생 시 순서대로 확인:

- [ ] 1. 에러 메시지 전체 읽기
- [ ] 2. 백엔드 서버 실행 중?
- [ ] 3. 프론트엔드 서버 실행 중?
- [ ] 4. 환경 변수 설정?
- [ ] 5. 가상환경 활성화?
- [ ] 6. CORS 설정?
- [ ] 7. Network 탭 확인?
- [ ] 8. Console 에러?
- [ ] 9. API 응답 형식?
- [ ] 10. 데이터 타입?

---

## 추가 지원

### 문서

- 📚 [메인 통합 가이드](../guide/portfolio-frontend-integration-guide.md)
- 🚀 [빠른 시작](../guide/portfolio-quick-start.md)
- 📖 [API 명세서](../api/portfolio-history-api-spec.md)

### 커뮤니티

- GitHub Issues
- 팀 채팅방
- Stack Overflow

### 로그 수집 방법

문제 보고 시 다음 정보를 포함:

```bash
# 시스템 정보
uname -a
python --version
node --version

# 백엔드 로그
# (백엔드 터미널 출력 전체 복사)

# 프론트엔드 로그
# (브라우저 Console 탭 복사)

# API 테스트
curl -v http://localhost:8000/api/portfolio/history?period=1M
```

---

**최종 수정**: 2025-10-11
**버전**: 1.0.0
**유지보수**: Backend Team
