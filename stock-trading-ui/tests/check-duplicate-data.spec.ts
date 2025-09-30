import { test } from '@playwright/test';

test('check for duplicate candle data', async ({ page }) => {
  const consoleData: string[] = [];

  page.on('console', msg => {
    consoleData.push(msg.text());
  });

  // displayData 내용을 출력하는 임시 코드 추가를 위해 페이지 평가
  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  const minuteButton = page.locator('button:has-text("1분")').first();
  await minuteButton.click();
  await page.waitForTimeout(2000);

  // 페이지에서 직접 데이터 추출
  const chartData = await page.evaluate(() => {
    // React 컴포넌트에서 데이터 추출 (전역 변수나 DOM에 접근)
    const chartElements = document.querySelectorAll('g > rect[fill]');
    const data: any[] = [];
    
    chartElements.forEach((rect, index) => {
      const x = rect.getAttribute('x');
      const y = rect.getAttribute('y');
      const width = rect.getAttribute('width');
      const height = rect.getAttribute('height');
      const fill = rect.getAttribute('fill');
      
      data.push({ index, x, y, width, height, fill });
    });
    
    return data;
  });

  console.log('\n=== 캔들 데이터 분석 ===');
  console.log(`총 캔들 개수: ${chartData.length}`);

  // 연속된 5개씩 그룹으로 묶어서 비교
  const groups: any[] = [];
  for (let i = 0; i < chartData.length; i += 5) {
    groups.push(chartData.slice(i, i + 5));
  }

  console.log(`\n5개씩 그룹 개수: ${groups.length}`);

  // 각 그룹 내에서 중복 확인
  groups.forEach((group, groupIndex) => {
    const xValues = group.map((d: any) => d.x);
    const yValues = group.map((d: any) => d.y);
    const heightValues = group.map((d: any) => d.height);
    
    const uniqueX = new Set(xValues).size;
    const uniqueY = new Set(yValues).size;
    const uniqueHeight = new Set(heightValues).size;
    
    if (uniqueX === 1 && uniqueY === 1 && uniqueHeight === 1) {
      console.log(`\n⚠️  그룹 ${groupIndex} - 동일한 데이터 5개 발견!`);
      console.log('X positions:', xValues);
      console.log('Y positions:', yValues);
      console.log('Heights:', heightValues);
    }
  });

  // 전체 x 위치 분포 확인
  const xPositions = chartData.map((d: any) => parseFloat(d.x));
  const uniqueXPositions = [...new Set(xPositions)];
  
  console.log(`\n전체 X 위치 개수: ${xPositions.length}`);
  console.log(`고유한 X 위치 개수: ${uniqueXPositions.length}`);
  
  if (xPositions.length !== uniqueXPositions.length) {
    console.log('\n⚠️  중복된 X 위치가 있습니다!');
    
    // 각 X 위치별 개수 세기
    const xCounts: Record<string, number> = {};
    xPositions.forEach(x => {
      xCounts[x] = (xCounts[x] || 0) + 1;
    });
    
    // 2개 이상인 것만 출력
    Object.entries(xCounts)
      .filter(([_, count]) => count > 1)
      .slice(0, 10)
      .forEach(([x, count]) => {
        console.log(`X=${x}: ${count}개`);
      });
  }

  // 콘솔 로그 중 Chart Debug 출력
  const chartDebugLogs = consoleData.filter(log => log.includes('Chart Debug') || log.includes('displayDataLength'));
  console.log('\n=== Chart Debug Logs ===');
  chartDebugLogs.forEach(log => console.log(log));
});
