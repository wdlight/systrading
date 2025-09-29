import { test, expect } from '@playwright/test';

test('test-chart 페이지 스크린샷 및 차트 확인', async ({ page }) => {
  // 콘솔 로그 수집 (페이지 로드 전에 설정)
  const logs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    // 중요한 로그만 출력
    if (text.includes('📊') || text.includes('✅') || text.includes('🔍') ||
        text.includes('🎨') || text.includes('🕯️') || text.includes('⚠️')) {
      console.log(`[Browser Console] ${text}`);
    }
  });

  // 페이지 크기 설정
  await page.setViewportSize({ width: 1920, height: 1080 });

  // test-chart 페이지 접속
  console.log('📍 http://localhost:9000/test-chart 접속 중...');
  await page.goto('http://localhost:9000/test-chart', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  // 페이지 로드 대기
  await page.waitForTimeout(5000);

  // 전체 페이지 스크린샷
  await page.screenshot({
    path: 'stock-trading-ui/test-chart-full.png',
    fullPage: true
  });
  console.log('✅ 전체 페이지 스크린샷 저장: test-chart-full.png');

  // 차트 영역이 있는지 확인
  const chartExists = await page.locator('text=Live Chart - Samsung Electronics').isVisible();
  console.log(`📊 차트 카드 존재 여부: ${chartExists}`);

  // RechartsAdapter가 렌더링되었는지 확인
  const rechartsContainer = page.locator('.recharts-responsive-container').first();
  const isRechartsVisible = await rechartsContainer.isVisible().catch(() => false);
  console.log(`📊 Recharts 컨테이너 존재 여부: ${isRechartsVisible}`);

  // 차트 영역만 스크린샷 (있다면)
  if (isRechartsVisible) {
    await rechartsContainer.screenshot({
      path: 'stock-trading-ui/test-chart-recharts.png'
    });
    console.log('✅ Recharts 영역 스크린샷 저장: test-chart-recharts.png');
  }

  // 차트 데이터 상태 확인
  const chartDataCount = await page.locator('text=/\\d+ candles/').first().textContent().catch(() => null);
  console.log(`📊 차트 데이터 개수 표시: ${chartDataCount}`);

  // 에러 메시지 확인
  const errorMessage = await page.locator('.text-red-400').first().textContent().catch(() => null);
  if (errorMessage) {
    console.log(`❌ 에러 메시지: ${errorMessage}`);
  }

  // 연결 상태 확인
  const connectionStatus = await page.locator('text=/Connected|Disconnected/').first().textContent().catch(() => 'Unknown');
  console.log(`🔌 연결 상태: ${connectionStatus}`);

  // 실시간 가격 정보 확인
  const priceExists = await page.locator('text=/삼성전자.*005930.*실시간 시세/').isVisible().catch(() => false);
  console.log(`💰 실시간 가격 정보 존재 여부: ${priceExists}`);

  // 수집된 브라우저 콘솔 로그 출력
  console.log('\n📋 수집된 브라우저 콘솔 로그:');
  logs.forEach(log => console.log(`  ${log}`));

  // 페이지 HTML 구조 일부 확인 (디버깅용)
  const chartCard = await page.locator('[class*="bg-"][class*="border"]').filter({ hasText: 'Live Chart' }).first();
  const chartCardHTML = await chartCard.innerHTML().catch(() => '');

  if (chartCardHTML) {
    console.log('\n📄 차트 카드 HTML 구조 (첫 500자):');
    console.log(chartCardHTML.substring(0, 500));
  }

  // 최종 대기 (차트 렌더링 완료 확인)
  await page.waitForTimeout(2000);

  // 최종 스크린샷
  await page.screenshot({
    path: 'stock-trading-ui/test-chart-final.png',
    fullPage: true
  });
  console.log('✅ 최종 스크린샷 저장: test-chart-final.png');
});