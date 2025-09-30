import { test } from '@playwright/test';

test('check backend data structure', async ({ page }) => {
  const apiData: any[] = [];
  const consoleData: string[] = [];

  // API 요청 캡처
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/api/') || url.includes('candle') || url.includes('chart')) {
      try {
        const data = await response.json();
        apiData.push({ url, data });
      } catch (e) {
        // JSON이 아닌 경우 무시
      }
    }
  });

  // 콘솔 로그 캡처
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('📊') || text.includes('formattedData') || text.includes('displayData')) {
      consoleData.push(text);
    }
  });

  await page.goto('http://localhost:9000/test-chart');
  await page.waitForTimeout(3000);

  // 1분 버튼 클릭
  const minuteButton = page.locator('button:has-text("1분")').first();
  await minuteButton.click();
  await page.waitForTimeout(3000);

  console.log('\n=== API DATA ===');
  apiData.forEach(({ url, data }) => {
    console.log(`URL: ${url}`);
    console.log(`Data length: ${Array.isArray(data) ? data.length : 'not array'}`);
    if (Array.isArray(data) && data.length > 0) {
      console.log('First item:', JSON.stringify(data[0], null, 2));
      console.log('Last item:', JSON.stringify(data[data.length - 1], null, 2));
    }
  });

  console.log('\n=== CONSOLE LOGS ===');
  consoleData.forEach(log => console.log(log));
});
