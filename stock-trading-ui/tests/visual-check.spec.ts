import { test } from '@playwright/test';

test('visual check of candle spacing', async ({ page }) => {
  await page.goto('http://localhost:9000/test-chart');

  // Wait for chart to fully load
  await page.waitForTimeout(4000);

  // Wait for "1분" button to be visible and clickable (use first one)
  const minuteButton = page.locator('button:has-text("1분")').first();
  await minuteButton.waitFor({ state: 'visible' });
  await minuteButton.click();

  // Wait for chart to update
  await page.waitForTimeout(2000);

  // Take full page screenshot
  await page.screenshot({
    path: 'tests/screenshots/candle-spacing-visual-full.png',
    fullPage: true
  });

  // Zoom in on just the chart area
  const chartArea = page.locator('.recharts-wrapper').first();
  await chartArea.screenshot({
    path: 'tests/screenshots/candle-spacing-visual-chart.png'
  });

  console.log('\n✅ Screenshots saved:');
  console.log('   - tests/screenshots/candle-spacing-visual-full.png');
  console.log('   - tests/screenshots/candle-spacing-visual-chart.png');
  console.log('\nPlease manually inspect the screenshots to verify:');
  console.log('   1. Candles should have visible gaps between them');
  console.log('   2. Gap should be approximately 10% of candle width');
  console.log('   3. Candles should not overlap');
});