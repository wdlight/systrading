
token 수 줄이기.


 현재 토큰 사용량을 보면 79k/200k (40%)로 아직 여유가 있지만, 빠르게 소모되는 이유와 효율적 사용법을 알려드리겠습니다.

  🔍 토큰 소모가 큰 이유

  1. MCP Tools 과다 로딩 (24k tokens - 12%)

  - 48개의 MCP 도구가 모두 메모리에 로드됨
  - Playwright, Figma, Context7 등 사용하지 않는 도구들도 포함
  - 해결책: 필요한 MCP만 활성화

  2. 긴 파일 읽기 (대화 기록 35.8k tokens - 17.9%)

  - 큰 React 컴포넌트 파일들을 전체 읽기
  - 이전 대화 컨텍스트 누적
  - 해결책: 파일의 특정 부분만 읽기, 컨텍스트 정리

  3. System Tools 오버헤드 (13.6k tokens - 6.8%)

  - 모든 시스템 도구 설명이 항상 로드됨

  ⚡ 효율적 사용법

  1. 작업 세션 분리

  # 현재 작업 완료 후 새 세션 시작
  # 대신 연속 작업 시 컨텍스트 누적 방지

  2. 파일 읽기 최적화

  # ❌ 비효율적
  Read entire-large-component.tsx

  # ✅ 효율적  
  Read component.tsx --offset=100 --limit=50  # 특정 라인만
  Grep "function.*Buy" --output_mode=content  # 필요한 부분만 검색

  3. 불필요한 MCP 비활성화

  현재 프로젝트에서 실제 필요한 것들만:
  - mcp__ide__* (코드 실행/진단)
  - mcp__shadcn__* (UI 컴포넌트)
  - mcp__playwright__* (브라우저 자동화 - 불필요)
  - mcp__figma__* (Figma 연동 - 불필요)
  - mcp__context7__* (문서 검색 - 불필요)

  4. 작업 패턴 개선

  현재 패턴 (비효율적):
  5. 전체 파일 읽기 → 2k tokens
  6. 수정 → 1k tokens
  7. 다시 전체 파일 읽기 → 2k tokens
  8. 재수정 → 1k tokens
  = 총 6k tokens

  효율적 패턴:
  9. Grep으로 필요 부분 찾기 → 0.1k tokens
  10. 해당 부분만 읽기 → 0.5k tokens
  11. 수정 → 1k tokens
  = 총 1.6k tokens (75% 절약)

  12. Agent 활용

  복잡한 작업은 전문 Agent에게 위임:
  # ❌ 직접 처리 (많은 토큰 소모)
  여러 파일 읽고 → 분석하고 → 수정하고...

  # ✅ Agent 활용 (효율적)
  Task tool → frontend-developer agent
  → "다크 테마 적용" 한 번에 처리

  📊 권장 사용 패턴

  작은 단위 작업

  - 한 번에 1-2개 컴포넌트만 수정
  - 완료 후 새 세션 시작

  검색 우선 접근

  1. Glob "**/*.tsx" | grep "Trading"  # 파일 찾기
  2. Grep "useState.*condition" --files_with_matches  # 관련 코드 찾기  
  3. Read 특정 라인만
  4. Edit 수정

  Agent 적극 활용

  - UI 작업 → frontend-developer
  - 타입 문제 → typescript-pro
  - 복합 작업 → context-manager

  🎯 즉시 적용 가능한 팁

  1. MCP 정리: 사용하지 않는 MCP 비활성화
  2. 파일 읽기: 전체 대신 필요한 부분만
  3. 작업 완료: 큰 작업 완료 시 새 세션
  4. Agent 활용: 복잡한 작업은 전문 Agent에게

  이렇게 하면 토큰 사용량을 50-75% 절약할 수 있습니다.
