import { test } from '@playwright/test';

test('capture console logs to check candle width', async ({ page }) => {
  const consoleLogs: string[] = [];

  // Listen to console messages
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('CandlestickDot rendering') || text.includes('providedWidth') || text.includes('처음 10개')) {
      consoleLogs.push(text);
    }
  });

  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  // Click "1분" button
  const minuteButton = page.locator('button:has-text("1분")').first();
  await minuteButton.click();

  await page.waitForTimeout(2000);

  console.log('\n=== CONSOLE LOGS ===');
  consoleLogs.forEach(log => console.log(log));
  console.log('===================\n');

  if (consoleLogs.length === 0) {
    console.log('⚠️  No console logs captured. The chart might not be rendering.');
  }
});