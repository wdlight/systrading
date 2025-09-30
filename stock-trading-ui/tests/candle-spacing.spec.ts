import { test, expect } from '@playwright/test';

test('verify candle spacing on test-chart page', async ({ page }) => {
  // Navigate to test-chart page
  await page.goto('http://localhost:9000/test-chart');

  // Wait for chart to load
  await page.waitForTimeout(3000);

  // Take screenshot of the chart
  await page.screenshot({
    path: 'tests/screenshots/candle-spacing-before.png',
    fullPage: true
  });

  // Get the chart container
  const chartContainer = page.locator('.recharts-wrapper');
  await expect(chartContainer).toBeVisible();

  // Get all candlestick bars (looking for the actual bar elements)
  const candles = page.locator('g.recharts-layer.recharts-bar-rectangle > g');
  const candleCount = await candles.count();

  console.log(`Found ${candleCount} candles`);

  if (candleCount >= 2) {
    // Get positions of first two candles
    const firstCandle = candles.nth(0);
    const secondCandle = candles.nth(1);

    const firstBox = await firstCandle.boundingBox();
    const secondBox = await secondCandle.boundingBox();

    if (firstBox && secondBox) {
      const candleWidth = firstBox.width;
      const gap = secondBox.x - (firstBox.x + firstBox.width);
      const gapPercentage = (gap / candleWidth) * 100;

      console.log('Candle metrics:');
      console.log(`- Candle width: ${candleWidth}px`);
      console.log(`- Gap between candles: ${gap}px`);
      console.log(`- Gap as percentage of width: ${gapPercentage.toFixed(2)}%`);

      // Gap should be approximately 10% of candle width
      // Allow some tolerance (5% - 15%)
      expect(gapPercentage).toBeGreaterThan(5);
      expect(gapPercentage).toBeLessThan(15);
    }
  }

  // Take final screenshot
  await page.screenshot({
    path: 'tests/screenshots/candle-spacing-after.png',
    fullPage: true
  });
});