/**
 * Playwright 스크립트: 차트 상태 디버깅
 * 브라우저 콘솔 로그를 캡처하여 차트 데이터 및 viewWindow 상태 확인
 */

const { chromium } = require('playwright');

async function debugChartState() {
  console.log('🚀 Playwright 브라우저 시작...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // 네트워크 요청 캡처
  const networkRequests = [];
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/api/') || url.includes('/chart/')) {
      console.log(`🌐 [Request] ${request.method()} ${url}`);
      networkRequests.push({ method: request.method(), url });
    }
  });

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/') || url.includes('/chart/')) {
      console.log(`📥 [Response] ${response.status()} ${url}`);
      if (response.status() >= 400) {
        console.error(`  ❌ Error response: ${response.status()} ${response.statusText()}`);
      }
    }
  });

  // 콘솔 로그 캡처
  const logs = [];
  page.on('console', msg => {
    const text = msg.text();
    console.log(`📝 [Console ${msg.type()}]:`, text);
    logs.push({ type: msg.type(), text });
  });

  // 에러 캡처
  page.on('pageerror', error => {
    console.error('❌ [Page Error]:', error.message);
  });

  try {
    console.log('🌐 http://localhost:9000/test-chart 접속 중...\n');
    await page.goto('http://localhost:9000/test-chart', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('⏳ 차트 렌더링 대기 중...\n');
    await page.waitForTimeout(5000);

    // 차트 데이터 상태 확인
    const chartState = await page.evaluate(() => {
      // 콘솔 로그에서 차트 상태 정보 추출
      return {
        url: window.location.href,
        timestamp: new Date().toISOString()
      };
    });

    console.log('\n📊 차트 상태:', JSON.stringify(chartState, null, 2));

    // 스크린샷 저장
    const screenshotPath = '/home/wide/projects/systrading/docs/issues/chart-debug-' + Date.now() + '.png';
    await page.screenshot({
      path: screenshotPath,
      fullPage: true
    });
    console.log(`\n📸 스크린샷 저장: ${screenshotPath}`);

    // 캡처된 로그 분석
    console.log('\n📋 캡처된 콘솔 로그 분석:');
    console.log('=' .repeat(80));

    const dataValidationLogs = logs.filter(log =>
      log.text.includes('FRONTEND DATA VALIDATION') ||
      log.text.includes('First 10 candles') ||
      log.text.includes('Last 10 candles') ||
      log.text.includes('Initial viewWindow')
    );

    if (dataValidationLogs.length > 0) {
      console.log('\n✅ 데이터 관련 로그 발견:');
      dataValidationLogs.forEach(log => {
        console.log(log.text);
      });
    } else {
      console.log('\n⚠️ 데이터 검증 로그가 발견되지 않았습니다.');
    }

    // 10초 대기 (사용자가 브라우저 확인 가능)
    console.log('\n⏸️  10초 대기 중 (브라우저 확인 가능)...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('\n❌ 오류 발생:', error.message);
  } finally {
    await browser.close();
    console.log('\n✅ 브라우저 종료');
  }
}

debugChartState().catch(console.error);
