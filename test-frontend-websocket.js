/**
 * Frontend WebSocket 분봉 업데이트 테스트 스크립트
 * Playwright를 사용하여 브라우저를 자동화하고 Console 로그를 수집합니다.
 */

const { chromium } = require('playwright');

async function testMinuteCandleUpdate() {
  console.log('🚀 브라우저 테스트 시작...\n');

  const browser = await chromium.launch({
    headless: false, // 브라우저 UI 표시
    slowMo: 500 // 천천히 실행
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Console 로그 수집
  const logs = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push({ type: msg.type(), text, timestamp: new Date().toISOString() });

    // 중요한 로그만 즉시 출력
    if (
      text.includes('[FINALIZE]') ||
      text.includes('[UPDATE]') ||
      text.includes('[WS]') ||
      text.includes('WebSocket') ||
      text.includes('minute_candle')
    ) {
      console.log(`[${msg.type()}] ${text}`);
    }
  });

  // 에러 수집
  page.on('pageerror', error => {
    console.error('❌ 페이지 에러:', error.message);
    logs.push({ type: 'error', text: error.message, timestamp: new Date().toISOString() });
  });

  try {
    console.log('📡 Frontend 접속 중: http://localhost:9000/trading\n');
    await page.goto('http://localhost:9000/trading', { waitUntil: 'networkidle' });

    console.log('✅ 페이지 로드 완료\n');
    console.log('⏳ 5초 대기 (UI 초기화)...\n');
    await page.waitForTimeout(5000);

    // 종목 선택 (삼성전자 005930)
    console.log('🔍 삼성전자 선택 시도...\n');

    // 종목 검색 또는 선택 (페이지 구조에 따라 다를 수 있음)
    // 여러 방법 시도
    const selectors = [
      'input[placeholder*="종목"]',
      'input[placeholder*="검색"]',
      'button:has-text("삼성전자")',
      'div:has-text("005930")'
    ];

    for (const selector of selectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          console.log(`✅ 요소 발견: ${selector}`);
          await element.click();
          await page.waitForTimeout(1000);
          break;
        }
      } catch (e) {
        // 다음 selector 시도
      }
    }

    // 분봉 차트 선택
    console.log('📊 분봉 차트 선택 시도...\n');
    const timeframeSelectors = [
      'button:has-text("1분")',
      'button:has-text("분봉")',
      '[data-timeframe="minute"]'
    ];

    for (const selector of timeframeSelectors) {
      try {
        const element = await page.$(selector);
        if (element) {
          console.log(`✅ 타임프레임 버튼 발견: ${selector}`);
          await element.click();
          await page.waitForTimeout(1000);
          break;
        }
      } catch (e) {
        // 다음 selector 시도
      }
    }

    console.log('\n📋 === WebSocket 리스너 등록 확인 ===\n');
    await page.waitForTimeout(2000);

    // WebSocket 상태 확인
    const wsStatus = await page.evaluate(() => {
      if (typeof wsManager === 'undefined') {
        return { available: false, message: 'wsManager not found' };
      }

      return {
        available: true,
        connected: wsManager.isConnected(),
        listeners: {
          update: wsManager.listeners.get('minute_candle_update')?.size || 0,
          finalize: wsManager.listeners.get('minute_candle_finalize')?.size || 0
        }
      };
    });

    console.log('WebSocket 상태:', JSON.stringify(wsStatus, null, 2));

    if (!wsStatus.available) {
      console.error('❌ wsManager를 찾을 수 없습니다!');
    } else if (!wsStatus.connected) {
      console.error('❌ WebSocket이 연결되지 않았습니다!');
    } else {
      console.log('✅ WebSocket 연결됨');
      console.log(`📝 UPDATE 리스너: ${wsStatus.listeners.update}개`);
      console.log(`📝 FINALIZE 리스너: ${wsStatus.listeners.finalize}개`);
    }

    // 테스트용 메시지 전송 (시뮬레이션)
    console.log('\n🧪 === 테스트 메시지 시뮬레이션 ===\n');

    const simulateResult = await page.evaluate(() => {
      if (typeof wsManager === 'undefined') {
        return { success: false, error: 'wsManager not available' };
      }

      try {
        // FINALIZE 메시지 시뮬레이션
        const testMessage = {
          type: 'minute_candle_finalize',
          stock_code: '005930',
          data: {
            timestamp: new Date().toISOString().substring(0, 16) + ':00+09:00',
            open: 62000,
            high: 62200,
            low: 61900,
            close: 62100,
            volume: 1500
          }
        };

        // handleMessage 호출 (내부 메서드이므로 직접 접근)
        if (wsManager.handleMessage) {
          wsManager.handleMessage(testMessage);
          return { success: true, message: testMessage };
        } else {
          return { success: false, error: 'handleMessage not available' };
        }
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    console.log('시뮬레이션 결과:', JSON.stringify(simulateResult, null, 2));

    // 로그 수집 대기
    console.log('\n⏳ 10초 대기 (로그 수집 중)...\n');
    await page.waitForTimeout(10000);

    // 실제 WebSocket 메시지 대기 (1분)
    console.log('⏳ 실제 WebSocket 메시지 대기 중 (60초)...');
    console.log('   Backend에서 분봉 완성 메시지를 기다립니다.\n');
    await page.waitForTimeout(60000);

  } catch (error) {
    console.error('❌ 테스트 실패:', error.message);
    logs.push({ type: 'error', text: error.message, timestamp: new Date().toISOString() });
  }

  // 결과 분석
  console.log('\n📊 === 로그 분석 결과 ===\n');

  const importantLogs = logs.filter(log =>
    log.text.includes('useRealtimeMinuteCandles') ||
    log.text.includes('[FINALIZE]') ||
    log.text.includes('[UPDATE]') ||
    log.text.includes('[WS]') ||
    log.text.includes('[Chart]') ||
    log.text.includes('WebSocket')
  );

  console.log(`총 로그: ${logs.length}개`);
  console.log(`중요 로그: ${importantLogs.length}개\n`);

  // 주요 체크포인트
  const checkpoints = {
    hookInitialized: importantLogs.some(l => l.text.includes('훅 초기화')),
    listenersRegistered: importantLogs.some(l => l.text.includes('리스너 등록')),
    updateReceived: importantLogs.some(l => l.text.includes('UPDATE') && l.text.includes('메시지 수신')),
    finalizeReceived: importantLogs.some(l => l.text.includes('FINALIZE') && l.text.includes('메시지 수신')),
    candleAdded: importantLogs.some(l => l.text.includes('finalizedCandles 배열에 추가')),
    chartUpdated: importantLogs.some(l => l.text.includes('차트 데이터 병합'))
  };

  console.log('체크포인트:');
  console.log('  ✓ 훅 초기화:', checkpoints.hookInitialized ? '✅' : '❌');
  console.log('  ✓ 리스너 등록:', checkpoints.listenersRegistered ? '✅' : '❌');
  console.log('  ✓ UPDATE 수신:', checkpoints.updateReceived ? '✅' : '❌');
  console.log('  ✓ FINALIZE 수신:', checkpoints.finalizeReceived ? '✅' : '❌');
  console.log('  ✓ 분봉 배열 추가:', checkpoints.candleAdded ? '✅' : '❌');
  console.log('  ✓ 차트 업데이트:', checkpoints.chartUpdated ? '✅' : '❌');

  console.log('\n중요 로그 (최근 20개):\n');
  importantLogs.slice(-20).forEach(log => {
    console.log(`[${log.type}] ${log.text}`);
  });

  // 로그 파일 저장
  const fs = require('fs');
  const logFilePath = '/home/wide/projects/systrading/frontend-test-logs.json';
  fs.writeFileSync(logFilePath, JSON.stringify({ checkpoints, logs: importantLogs }, null, 2));
  console.log(`\n💾 상세 로그 저장: ${logFilePath}`);

  console.log('\n⏸️  브라우저를 10초간 유지합니다. 수동으로 확인하세요.\n');
  await page.waitForTimeout(10000);

  await browser.close();
  console.log('\n✅ 테스트 완료\n');
}

// 실행
testMinuteCandleUpdate().catch(console.error);
