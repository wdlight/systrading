import { test } from '@playwright/test';

test('inspect chart structure', async ({ page }) => {
  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  // Log the entire chart HTML structure
  const chartHTML = await page.locator('.recharts-wrapper').innerHTML();
  console.log('=== CHART HTML STRUCTURE ===');
  console.log(chartHTML.substring(0, 2000)); // First 2000 chars

  // Try different selectors to find candles
  const selectors = [
    'g.recharts-layer.recharts-bar-rectangle > g',
    '.recharts-bar-rectangle',
    'g[class*="recharts-bar"]',
    'rect[fill="#ef5350"]',  // Red candles
    'rect[fill="#26a69a"]',  // Green candles
    'g > rect',
    '.recharts-layer g'
  ];

  for (const selector of selectors) {
    const count = await page.locator(selector).count();
    console.log(`Selector "${selector}": ${count} elements`);
  }

  // Take a screenshot
  await page.screenshot({
    path: 'tests/screenshots/chart-structure.png',
    fullPage: true
  });
});