import { test, expect } from '@playwright/test';

test('차트 캔들스틱 렌더링 디버깅', async ({ page }) => {
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
  await page.waitForTimeout(5000); // 차트 렌더링 대기

  // 스크린샷 촬영
  await page.screenshot({
    path: '/home/wide/projects/systrading/stock-trading-ui/chart-candle-debug.png',
    fullPage: true
  });

  // SVG 엘리먼트 확인
  console.log('🔍 SVG 엘리먼트 분석 중...');
  const svgElements = await page.evaluate(() => {
    const svgs = Array.from(document.querySelectorAll('svg'));
    return svgs.map(svg => ({
      width: svg.getAttribute('width'),
      height: svg.getAttribute('height'),
      childrenCount: svg.children.length,
      innerHTML: svg.innerHTML.substring(0, 500) // 처음 500자만
    }));
  });

  console.log('📊 SVG 엘리먼트:', JSON.stringify(svgElements, null, 2));

  // 캔들스틱 바 (rect, line) 확인
  const candlestickElements = await page.evaluate(() => {
    const rects = Array.from(document.querySelectorAll('svg rect'));
    const lines = Array.from(document.querySelectorAll('svg line'));
    const groups = Array.from(document.querySelectorAll('svg g'));

    return {
      rectangles: rects.length,
      lines: lines.length,
      groups: groups.length,
      rectDetails: rects.slice(0, 5).map(rect => ({
        x: rect.getAttribute('x'),
        y: rect.getAttribute('y'),
        width: rect.getAttribute('width'),
        height: rect.getAttribute('height'),
        fill: rect.getAttribute('fill'),
        stroke: rect.getAttribute('stroke')
      })),
      lineDetails: lines.slice(0, 5).map(line => ({
        x1: line.getAttribute('x1'),
        y1: line.getAttribute('y1'),
        x2: line.getAttribute('x2'),
        y2: line.getAttribute('y2'),
        stroke: line.getAttribute('stroke')
      }))
    };
  });

  console.log('🕯️ 캔들스틱 엘리먼트:', JSON.stringify(candlestickElements, null, 2));

  // Y축 범위 확인
  const axisInfo = await page.evaluate(() => {
    const yAxisTexts = Array.from(document.querySelectorAll('svg text')).map(text => text.textContent);
    const chartContainer = document.querySelector('.bg-\\[\\#0a0a0b\\].border.border-gray-700.rounded-lg.p-2');

    return {
      yAxisValues: yAxisTexts.filter(text => text && !isNaN(parseFloat(text.replace(/,/g, '')))),
      containerDimensions: chartContainer ? {
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight
      } : null
    };
  });

  console.log('📏 축 정보:', JSON.stringify(axisInfo, null, 2));

  // 차트 데이터 확인
  const chartDataInfo = await page.evaluate(() => {
    // window 객체에서 차트 데이터 확인 시도
    return {
      windowKeys: Object.keys(window).filter(key => key.includes('chart') || key.includes('data')),
      recharts: typeof window !== 'undefined' && 'Recharts' in window
    };
  });

  console.log('📊 차트 데이터 정보:', JSON.stringify(chartDataInfo, null, 2));

  console.log('✅ 캔들스틱 디버깅 완료');
});