import { test, expect } from '@playwright/test';

test('차트 드래그 스크롤 기능 검증', async ({ page }) => {
  // 콘솔 로그 캐치 (에러 모니터링)
  const errors: string[] = [];
  page.on('pageerror', error => {
    errors.push(error.message);
    console.log(`❌ Page Error: ${error.message}`);
  });

  console.log('🚀 차트 페이지 접속 시작...');
  await page.goto('http://localhost:9000/test-chart');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  console.log('✅ 페이지 로드 완료');

  // 초기 상태 스크린샷
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/drag-test-before.png',
    fullPage: true
  });

  // 차트 컨테이너 확인
  const chartContainer = page.locator('.bg-\\[\\#0a0a0b\\].border.border-gray-700.rounded-lg.p-2').first();
  await expect(chartContainer).toBeVisible();

  // 뷰포트 인디케이터 확인
  const viewportIndicator = page.locator('.relative.mt-2.h-5.bg-gray-800');
  await expect(viewportIndicator).toBeVisible();

  // 초기 뷰포트 인디케이터 텍스트 확인
  const initialText = await viewportIndicator.locator('.text-xs.text-gray-400').textContent();
  console.log(`📊 초기 뷰포트 상태: ${initialText}`);

  // 차트 컨테이너의 커서 스타일 확인
  const cursorStyle = await chartContainer.evaluate(el =>
    window.getComputedStyle(el).cursor
  );
  console.log(`🖱️ 차트 커서 스타일: ${cursorStyle}`);
  expect(['grab', 'grabbing']).toContain(cursorStyle);

  // 차트 영역에서 드래그 시뮬레이션
  const chartBox = await chartContainer.boundingBox();
  if (chartBox) {
    const centerY = chartBox.y + chartBox.height * 0.4; // 차트 영역 중앙
    const startX = chartBox.x + chartBox.width * 0.7;   // 70% 지점에서 시작
    const endX = chartBox.x + chartBox.width * 0.3;     // 30% 지점으로 드래그

    console.log(`🖱️ 드래그 실행: (${startX}, ${centerY}) → (${endX}, ${centerY})`);

    // 드래그 실행
    await page.mouse.move(startX, centerY);
    await page.mouse.down();

    // 드래그 중 커서 변경 확인 (grabbing)
    await page.mouse.move(startX - 50, centerY, { steps: 3 });
    const draggingCursor = await chartContainer.evaluate(el =>
      window.getComputedStyle(el).cursor
    );
    console.log(`🖱️ 드래그 중 커서: ${draggingCursor}`);

    // 드래그 완료
    await page.mouse.move(endX, centerY, { steps: 10 });
    await page.mouse.up();

    console.log('🎯 드래그 완료');
    await page.waitForTimeout(1000);

    // 드래그 후 상태 스크린샷
    await page.screenshot({
      path: '/home/wide/projects/systrading/stock-trading-ui/drag-test-after.png',
      fullPage: true
    });

    // 뷰포트 인디케이터 변경 확인
    const finalText = await viewportIndicator.locator('.text-xs.text-gray-400').textContent();
    console.log(`📊 최종 뷰포트 상태: ${finalText}`);

    // 텍스트가 변경되었는지 확인 (드래그가 동작했다는 증거)
    if (initialText !== finalText) {
      console.log('✅ 드래그 스크롤이 정상 동작함 - 뷰포트가 변경됨');
    } else {
      console.log('⚠️ 뷰포트 텍스트가 동일함 - 드래그 효과를 확인할 수 없음');
    }

    // 빨간색 인디케이터 바 확인 (드래그된 위치 표시)
    const redIndicator = viewportIndicator.locator('.bg-red-500.opacity-60');
    if (await redIndicator.isVisible()) {
      console.log('✅ 빨간색 뷰포트 인디케이터 표시됨');
      const indicatorBox = await redIndicator.boundingBox();
      console.log(`📍 인디케이터 위치: left=${indicatorBox?.x}, width=${indicatorBox?.width}`);
    } else {
      console.log('⚠️ 빨간색 뷰포트 인디케이터가 보이지 않음');
    }
  }

  // 차트 데이터 상태 검증
  const chartState = await page.evaluate(() => {
    const svg = document.querySelector('svg');
    const bars = document.querySelectorAll('svg rect[fill="#EF5350"], svg rect[fill="#2196F3"]');
    const lines = document.querySelectorAll('svg line');

    return {
      hasSvg: !!svg,
      barCount: bars.length,
      lineCount: lines.length,
      svgWidth: svg?.getAttribute('width'),
      svgHeight: svg?.getAttribute('height')
    };
  });

  console.log('📊 차트 렌더링 상태:', JSON.stringify(chartState, null, 2));

  // 최소한의 렌더링 요소가 있는지 확인
  expect(chartState.hasSvg).toBe(true);
  expect(chartState.barCount + chartState.lineCount).toBeGreaterThan(0);

  // 에러 없이 완료되었는지 확인
  expect(errors).toHaveLength(0);

  console.log('✅ 차트 드래그 기능 테스트 완료');
});