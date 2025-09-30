import { test } from '@playwright/test';

test('check visual pattern of candles', async ({ page }) => {
  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  const minuteButton = page.locator('button:has-text("1분")').first();
  await minuteButton.click();
  await page.waitForTimeout(2000);

  // 실제 데이터 값 추출
  const candleDetails = await page.evaluate(() => {
    const rects = Array.from(document.querySelectorAll('g > rect[fill]'));
    
    return rects.slice(0, 30).map((rect, index) => {
      const x = parseFloat(rect.getAttribute('x') || '0');
      const y = parseFloat(rect.getAttribute('y') || '0');
      const width = parseFloat(rect.getAttribute('width') || '0');
      const height = parseFloat(rect.getAttribute('height') || '0');
      const fill = rect.getAttribute('fill');
      
      return { 
        index, 
        x: Math.round(x * 100) / 100, 
        y: Math.round(y * 100) / 100,
        width: Math.round(width * 100) / 100,
        height: Math.round(height * 100) / 100,
        fill 
      };
    });
  });

  console.log('\n=== 처음 30개 캔들 상세 정보 ===');
  console.log('Index | X위치 | Y위치 | 너비 | 높이 | 색상');
  console.log('------|-------|-------|------|------|------');
  candleDetails.forEach(c => {
    console.log(`${c.index.toString().padStart(5)} | ${c.x.toString().padStart(5)} | ${c.y.toString().padStart(5)} | ${c.width.toString().padStart(4)} | ${c.height.toString().padStart(4)} | ${c.fill}`);
  });

  // 연속된 5개씩 비교
  console.log('\n=== 5개씩 그룹 비교 ===');
  for (let i = 0; i < 25; i += 5) {
    const group = candleDetails.slice(i, i + 5);
    const xDiff = group[4].x - group[0].x;
    const allSameHeight = group.every((c, idx) => idx === 0 || Math.abs(c.height - group[0].height) < 0.1);
    const allSameY = group.every((c, idx) => idx === 0 || Math.abs(c.y - group[0].y) < 0.1);
    
    console.log(`\n그룹 ${i/5 + 1} (인덱스 ${i}-${i+4}):`);
    console.log(`  X 범위: ${group[0].x} ~ ${group[4].x} (차이: ${xDiff.toFixed(2)})`);
    console.log(`  높이 동일: ${allSameHeight}`);
    console.log(`  Y위치 동일: ${allSameY}`);
    if (allSameHeight && allSameY) {
      console.log('  ⚠️  이 그룹은 시각적으로 동일하게 보일 수 있습니다!');
    }
  }
});
