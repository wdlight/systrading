import { test, expect } from '@playwright/test';

test('차트 내 좌클릭 드래그 스크롤 테스트', async ({ page }) => {
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
  await page.waitForTimeout(3000); // 차트 렌더링 대기

  // 차트 컨테이너 찾기
  const chartContainer = page.locator('.bg-\\[\\#0a0a0b\\].border.border-gray-700.rounded-lg.p-2').first();
  await expect(chartContainer).toBeVisible();

  console.log('📊 차트 컨테이너 확인됨');

  // 초기 스크린샷
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/chart-before-drag.png',
    fullPage: true
  });

  // 차트 컨테이너의 위치와 크기 확인
  const chartBox = await chartContainer.boundingBox();
  console.log('📐 차트 컨테이너 위치:', chartBox);

  if (chartBox) {
    // 차트 중앙에서 좌클릭 드래그 시뮬레이션
    const startX = chartBox.x + chartBox.width * 0.7;  // 70% 지점에서 시작
    const startY = chartBox.y + chartBox.height * 0.5; // 중앙 높이
    const endX = chartBox.x + chartBox.width * 0.3;    // 30% 지점으로 드래그
    const endY = startY; // 같은 높이 유지

    console.log(`🖱️ 드래그 시작: (${startX}, ${startY}) → (${endX}, ${endY})`);

    // 좌클릭 드래그 실행
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    await page.mouse.move(endX, endY, { steps: 10 }); // 10단계로 나누어 부드럽게 드래그
    await page.mouse.up();

    // 드래그 후 잠시 대기
    await page.waitForTimeout(1000);

    console.log('🎯 드래그 완료');

    // 드래그 후 스크린샷
    await page.screenshot({
      path: '/home/wide/projects/systrading/stock-trading-ui/chart-after-drag.png',
      fullPage: true
    });
  }

  // 마우스 커서가 grab/grabbing으로 변경되는지 확인
  const cursorStyle = await chartContainer.evaluate(el =>
    window.getComputedStyle(el).cursor
  );
  console.log('🖱️ 차트 컨테이너 커서:', cursorStyle);

  // grab 또는 grabbing 커서인지 확인
  expect(['grab', 'grabbing']).toContain(cursorStyle);

  // SVG 엘리먼트와 캔들스틱 렌더링 확인
  const candlestickElements = await page.evaluate(() => {
    const svgElement = document.querySelector('svg');
    if (!svgElement) return null;

    const rects = svgElement.querySelectorAll('rect');
    const lines = svgElement.querySelectorAll('line');
    const candlestickLayer = svgElement.querySelector('.candlestick-layer');
    const viewportIndicator = svgElement.querySelector('.viewport-indicator');

    return {
      hasChart: !!svgElement,
      rectCount: rects.length,
      lineCount: lines.length,
      hasCandlestickLayer: !!candlestickLayer,
      hasViewportIndicator: !!viewportIndicator,
      candlestickChildrenCount: candlestickLayer?.children.length || 0
    };
  });

  console.log('🕯️ 차트 렌더링 상태:', JSON.stringify(candlestickElements, null, 2));

  // 차트가 정상적으로 렌더링되었는지 확인
  expect(candlestickElements?.hasChart).toBe(true);
  expect(candlestickElements?.hasCandlestickLayer).toBe(true);
  expect(candlestickElements?.candlestickChildrenCount).toBeGreaterThan(0);

  // 뷰포트 인디케이터가 렌더링되었는지 확인
  expect(candlestickElements?.hasViewportIndicator).toBe(true);

  console.log('✅ 차트 드래그 스크롤 테스트 완료');

  // 에러 검증
  expect(errors).toHaveLength(0);
});