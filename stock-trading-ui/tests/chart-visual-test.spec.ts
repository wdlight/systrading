import { test, expect } from '@playwright/test';

test('차트 시각적 렌더링 확인', async ({ page }) => {
  // 페이지 접속
  await page.goto('http://localhost:9000/test-chart');

  // 페이지 로드 대기
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // 스크린샷 촬영
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/chart-current-state.png',
    fullPage: true
  });

  // 차트 컨테이너 확인
  const chartContainer = page.locator('.bg-\\[\\#0a0a0b\\].border.border-gray-700.rounded-lg.p-2').first();
  await expect(chartContainer).toBeVisible();

  // 뷰포트 인디케이터 확인
  const viewportIndicator = page.locator('.relative.mt-2.h-5.bg-gray-800');
  await expect(viewportIndicator).toBeVisible();

  // Bar 컴포넌트 확인 (캔들스틱)
  const svgElement = await page.locator('svg').first();
  await expect(svgElement).toBeVisible();

  console.log('✅ 차트 시각적 테스트 완료');
});