import { test, expect } from '@playwright/test';

test('차트 드래그 상세 디버깅', async ({ page }) => {
  // 모든 콘솔 로그 캐치
  const logs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    console.log(`Console: ${text}`);
  });

  await page.goto('http://localhost:9000/test-chart');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // 초기 상태 확인
  const chartContainer = page.locator('.bg-\\[\\#0a0a0b\\].border.border-gray-700.rounded-lg.p-2').first();
  await expect(chartContainer).toBeVisible();

  const initialViewport = await page.locator('.relative.mt-2.h-5.bg-gray-800 .text-xs.text-gray-400').textContent();
  console.log(`📊 초기 뷰포트: ${initialViewport}`);

  // 차트 영역에서 간단한 클릭 테스트
  const chartBox = await chartContainer.boundingBox();
  if (chartBox) {
    const clickX = chartBox.x + chartBox.width * 0.5;
    const clickY = chartBox.y + chartBox.height * 0.3;

    console.log(`🖱️ 클릭 테스트: (${clickX}, ${clickY})`);
    await page.mouse.click(clickX, clickY);
    await page.waitForTimeout(500);

    // 마우스 다운 이벤트 확인
    console.log(`🖱️ 마우스 다운 시작: (${clickX}, ${clickY})`);
    await page.mouse.move(clickX, clickY);
    await page.mouse.down();
    await page.waitForTimeout(100);

    // 조금 이동
    await page.mouse.move(clickX - 100, clickY);
    await page.waitForTimeout(100);

    await page.mouse.up();
    await page.waitForTimeout(1000);

    // 최종 뷰포트 상태 확인
    const finalViewport = await page.locator('.relative.mt-2.h-5.bg-gray-800 .text-xs.text-gray-400').textContent();
    console.log(`📊 최종 뷰포트: ${finalViewport}`);

    // 변경되었는지 확인
    if (initialViewport !== finalViewport) {
      console.log('✅ 뷰포트가 변경됨 - 드래그 성공');
    } else {
      console.log('❌ 뷰포트가 동일함 - 드래그 실패');
    }
  }

  console.log('=== 수집된 모든 콘솔 로그 ===');
  logs.forEach(log => console.log(log));

  console.log('✅ 디버깅 테스트 완료');
});