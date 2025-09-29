import { test, expect } from '@playwright/test';

test('캔들 렌더링 상태 상세 분석', async ({ page }) => {
  // 콘솔 로그 수집
  const logs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    console.log(`Console: ${text}`);
  });

  await page.goto('http://localhost:9000/test-chart');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  console.log('=== 차트 데이터 상태 분석 ===');

  // SVG 및 캔들스틱 요소 분석
  const chartAnalysis = await page.evaluate(() => {
    const svg = document.querySelector('svg');
    if (!svg) return { error: 'SVG not found' };

    const rects = svg.querySelectorAll('rect');
    const lines = svg.querySelectorAll('line');
    const paths = svg.querySelectorAll('path');
    const bars = svg.querySelectorAll('.recharts-bar');
    const barShapes = svg.querySelectorAll('.recharts-bar rect');

    // Bar 컴포넌트 확인
    const barComponents = svg.querySelectorAll('[data-key="candlestick"]');
    const barCells = svg.querySelectorAll('.recharts-bar-rectangle');

    return {
      svgDimensions: {
        width: svg.getAttribute('width'),
        height: svg.getAttribute('height'),
        viewBox: svg.getAttribute('viewBox')
      },
      elementCounts: {
        rects: rects.length,
        lines: lines.length,
        paths: paths.length,
        bars: bars.length,
        barShapes: barShapes.length,
        barComponents: barComponents.length,
        barCells: barCells.length
      },
      barDetails: Array.from(bars).slice(0, 3).map(bar => ({
        className: bar.className.baseVal,
        innerHTML: bar.innerHTML.substring(0, 200)
      })),
      rectDetails: Array.from(rects).slice(0, 5).map(rect => ({
        x: rect.getAttribute('x'),
        y: rect.getAttribute('y'),
        width: rect.getAttribute('width'),
        height: rect.getAttribute('height'),
        fill: rect.getAttribute('fill'),
        stroke: rect.getAttribute('stroke'),
        className: rect.className?.baseVal
      }))
    };
  });

  console.log('📊 차트 분석 결과:', JSON.stringify(chartAnalysis, null, 2));

  // Y축 데이터 확인
  const yAxisData = await page.evaluate(() => {
    const yAxisTexts = Array.from(document.querySelectorAll('svg text'))
      .map(text => text.textContent)
      .filter(text => text && !isNaN(parseFloat(text.replace(/,/g, ''))));

    return {
      yAxisValues: yAxisTexts,
      allTexts: Array.from(document.querySelectorAll('svg text'))
        .map(text => text.textContent)
        .filter(Boolean)
    };
  });

  console.log('📏 Y축 데이터:', JSON.stringify(yAxisData, null, 2));

  // 뷰포트 상태 확인
  const viewportInfo = await page.locator('.relative.mt-2.h-5.bg-gray-800 .text-xs.text-gray-400').textContent();
  console.log('📊 뷰포트 정보:', viewportInfo);

  // 차트 데이터 관련 로그만 필터링
  const chartLogs = logs.filter(log =>
    log.includes('Chart data loaded') ||
    log.includes('Y축 범위') ||
    log.includes('차트') ||
    log.includes('candlestick')
  );

  console.log('=== 차트 데이터 로그 ===');
  chartLogs.forEach(log => console.log(log));

  // 스크린샷 촬영
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/candle-analysis.png',
    fullPage: true
  });

  console.log('✅ 캔들 분석 완료');
});