import { test } from '@playwright/test';

test('check time data format', async ({ page }) => {
  const consoleData: string[] = [];

  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('Chart Debug') || text.includes('Data Validation')) {
      consoleData.push(text);
    }
  });

  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  const minuteButton = page.locator('button:has-text("1분")').first();
  await minuteButton.click();
  await page.waitForTimeout(2000);

  console.log('\n=== TIME DATA ===');
  consoleData.forEach(log => console.log(log));
});
