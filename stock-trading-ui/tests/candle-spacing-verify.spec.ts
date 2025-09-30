import { test, expect } from '@playwright/test';

test('verify candle spacing with correct selector', async ({ page }) => {
  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  // Take initial screenshot
  await page.screenshot({
    path: 'tests/screenshots/candle-spacing-initial.png',
    fullPage: true
  });

  // Find all candle rectangles
  const candleRects = page.locator('g > rect');
  const candleCount = await candleRects.count();

  console.log(`\n=== CANDLE SPACING ANALYSIS ===`);
  console.log(`Total candle elements found: ${candleCount}`);

  if (candleCount >= 4) {
    // Measure first 3 pairs of candles to get average
    const measurements = [];

    for (let i = 0; i < Math.min(3, candleCount - 1); i++) {
      const currentRect = candleRects.nth(i);
      const nextRect = candleRects.nth(i + 1);

      const currentBox = await currentRect.boundingBox();
      const nextBox = await nextRect.boundingBox();

      if (currentBox && nextBox) {
        const candleWidth = currentBox.width;
        const gap = nextBox.x - (currentBox.x + currentBox.width);
        const gapPercentage = (gap / candleWidth) * 100;

        measurements.push({
          pairIndex: i,
          candleWidth,
          gap,
          gapPercentage
        });

        console.log(`\nCandle pair ${i} → ${i+1}:`);
        console.log(`  - Candle width: ${candleWidth.toFixed(2)}px`);
        console.log(`  - Gap: ${gap.toFixed(2)}px`);
        console.log(`  - Gap percentage: ${gapPercentage.toFixed(2)}%`);
      }
    }

    if (measurements.length > 0) {
      const avgGapPercentage = measurements.reduce((sum, m) => sum + m.gapPercentage, 0) / measurements.length;
      console.log(`\n=== SUMMARY ===`);
      console.log(`Average gap percentage: ${avgGapPercentage.toFixed(2)}%`);
      console.log(`Expected: ~10%`);

      // Check if gap is close to 10% (allow 5% - 20% tolerance for now)
      if (avgGapPercentage < 5) {
        console.log(`❌ Gap is too small (${avgGapPercentage.toFixed(2)}% < 5%)`);
        console.log(`   barCategoryGap setting may not be applied correctly`);
      } else if (avgGapPercentage > 20) {
        console.log(`❌ Gap is too large (${avgGapPercentage.toFixed(2)}% > 20%)`);
      } else {
        console.log(`✅ Gap is within acceptable range`);
      }

      // Take final screenshot with measurements
      await page.screenshot({
        path: 'tests/screenshots/candle-spacing-measured.png',
        fullPage: true
      });
    }
  }
});