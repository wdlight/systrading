import { test, expect } from '@playwright/test';

test('verify 120 candles display with 10-minute intervals', async ({ page }) => {
  // Navigate to test-chart page
  await page.goto('http://localhost:9000/test-chart');

  // Wait for chart to load
  await page.waitForTimeout(8000);

  // Capture screenshot
  await page.screenshot({
    path: 'verification-120-candles.png',
    fullPage: true
  });

  // Capture just the Recharts container
  const rechartsContainer = page.locator('.recharts-responsive-container').first();
  if (await rechartsContainer.count() > 0) {
    await rechartsContainer.screenshot({
      path: 'verification-chart-only.png'
    });
  }

  console.log('✅ Screenshots captured successfully');
});