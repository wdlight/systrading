import { test, expect } from '@playwright/test';

test('차트 긴 드래그 테스트', async ({ page }) => {
  // 콘솔 로그 캐치
  const logs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    if (text.includes('🖱️')) {
      console.log(`🎯 드래그 로그: ${text}`);
    }
  });

  await page.goto('http://localhost:9000/test-chart');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  const chartContainer = page.locator('.bg-\\[\\#0a0a0b\\].border.border-gray-700.rounded-lg.p-2').first();
  await expect(chartContainer).toBeVisible();

  const initialViewport = await page.locator('.relative.mt-2.h-5.bg-gray-800 .text-xs.text-gray-400').textContent();
  console.log(`📊 초기 뷰포트: ${initialViewport}`);

  const chartBox = await chartContainer.boundingBox();
  if (chartBox) {
    const startX = chartBox.x + chartBox.width * 0.8; // 80% 지점에서 시작
    const startY = chartBox.y + chartBox.height * 0.4; // 40% 높이
    const endX = chartBox.x + chartBox.width * 0.2;   // 20% 지점까지 드래그
    const endY = startY; // 같은 높이

    console.log(`🖱️ 긴 드래그 시작: (${startX}, ${startY}) → (${endX}, ${endY})`);

    // 느린 드래그 시뮬레이션
    await page.mouse.move(startX, startY);
    await page.waitForTimeout(100);

    // 마우스 다운
    await page.mouse.down();
    await page.waitForTimeout(200);

    // 여러 단계로 드래그
    const steps = 20;
    for (let i = 1; i <= steps; i++) {
      const progress = i / steps;
      const currentX = startX + (endX - startX) * progress;
      await page.mouse.move(currentX, endY);
      await page.waitForTimeout(50); // 각 단계마다 50ms 대기
    }

    // 마우스 업
    await page.mouse.up();
    await page.waitForTimeout(1000);

    console.log('🎯 긴 드래그 완료');

    // 최종 뷰포트 상태 확인
    const finalViewport = await page.locator('.relative.mt-2.h-5.bg-gray-800 .text-xs.text-gray-400').textContent();
    console.log(`📊 최종 뷰포트: ${finalViewport}`);

    if (initialViewport !== finalViewport) {
      console.log('✅ 드래그 성공: 뷰포트가 변경됨');
    } else {
      console.log('❌ 드래그 실패: 뷰포트가 동일함');
    }

    // 빨간색 인디케이터 확인
    const redIndicator = page.locator('.relative.mt-2.h-5.bg-gray-800 .bg-red-500.opacity-60');
    if (await redIndicator.isVisible()) {
      const indicatorBox = await redIndicator.boundingBox();
      console.log(`📍 빨간색 인디케이터 발견: left=${indicatorBox?.x}, width=${indicatorBox?.width}`);
    }

    // 스크린샷
    await page.screenshot({
      path: '/home/wide/projects/systrading/stock-trading-ui/long-drag-result.png',
      fullPage: true
    });
  }

  // 드래그 관련 로그만 필터링
  const dragLogs = logs.filter(log => log.includes('🖱️'));
  console.log('=== 드래그 관련 로그 ===');
  dragLogs.forEach(log => console.log(log));

  console.log('✅ 긴 드래그 테스트 완료');
});