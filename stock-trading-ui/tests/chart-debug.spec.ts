import { test, expect } from '@playwright/test';

test('차트 페이지 디버깅', async ({ page }) => {
  // 콘솔 로그 캐치
  const logs: string[] = [];
  const errors: string[] = [];

  page.on('console', msg => {
    const text = msg.text();
    logs.push(`${msg.type()}: ${text}`);
    console.log(`Console ${msg.type()}: ${text}`);
  });

  page.on('pageerror', error => {
    const errorMsg = error.message;
    errors.push(errorMsg);
    console.log(`Page Error: ${errorMsg}`);
  });

  // 페이지 접속
  console.log('🚀 차트 페이지 접속 중...');
  await page.goto('http://localhost:9000/test-chart');

  // 페이지 로드 대기
  await page.waitForLoadState('networkidle');

  // 차트 컨테이너 확인
  console.log('📊 차트 컨테이너 확인 중...');
  const chartContainer = page.locator('[data-testid="chart-container"], .bg-\\[\\#0a0a0b\\]').first();
  await expect(chartContainer).toBeVisible({ timeout: 10000 });

  // 스크린샷 촬영
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/chart-debug-screenshot.png',
    fullPage: true
  });

  // 차트 영역 텍스트 확인
  const chartText = await chartContainer.textContent();
  console.log('📝 차트 영역 텍스트:', chartText);

  // 에러 메시지 확인
  const errorElements = page.locator('text=차트 로딩 실패');
  if (await errorElements.count() > 0) {
    console.log('❌ 차트 로딩 실패 메시지 발견');
    const errorText = await errorElements.textContent();
    console.log('에러 내용:', errorText);
  }

  // 로딩 메시지 확인
  const loadingElements = page.locator('text=차트 로딩 중');
  if (await loadingElements.count() > 0) {
    console.log('⏳ 로딩 중 메시지 발견');

    // 로딩이 완료될 때까지 대기 (최대 15초)
    await page.waitForFunction(
      () => !document.querySelector('text=차트 로딩 중'),
      { timeout: 15000 }
    ).catch(() => {
      console.log('⚠️ 로딩 타임아웃');
    });
  }

  // lightweight-charts 라이브러리 로드 확인
  const isChartLibLoaded = await page.evaluate(() => {
    try {
      // window 객체에서 라이브러리 확인
      return typeof window !== 'undefined' && 'LightweightCharts' in window;
    } catch (e) {
      return false;
    }
  });

  console.log('📦 Lightweight Charts 라이브러리 로드됨:', isChartLibLoaded);

  // 네트워크 요청 확인
  console.log('🌐 네트워크 로그:');
  logs.forEach(log => console.log(log));

  console.log('🚨 에러 로그:');
  errors.forEach(error => console.log(error));

  // DOM 구조 확인
  const chartDomInfo = await page.evaluate(() => {
    const containers = document.querySelectorAll('.bg-\\[\\#0a0a0b\\]');
    return Array.from(containers).map(el => ({
      tag: el.tagName,
      classes: el.className,
      textContent: el.textContent?.substring(0, 100),
      children: el.children.length
    }));
  });

  console.log('🏗️ 차트 DOM 구조:', JSON.stringify(chartDomInfo, null, 2));

  // 최종 스크린샷
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/chart-final-screenshot.png',
    fullPage: true
  });

  console.log('✅ 디버깅 완료');
});