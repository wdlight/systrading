const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Starting Playwright debugging...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 콘솔 로그 모니터링
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('Real-time') || text.includes('polling') || text.includes('candle')) {
      console.log(`📝 Console: ${text}`);
    }
  });

  // 네트워크 요청 모니터링
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/minute/current') || url.includes('/minute?')) {
      console.log(`🌐 Request: ${request.method()} ${url}`);
    }
  });

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/minute/current')) {
      console.log(`✅ Response: ${response.status()} ${url}`);
      try {
        const data = await response.json();
        console.log(`   Latest candle: ${data.timestamp} - Volume: ${data.volume}`);
      } catch (e) {
        // Ignore parse errors
      }
    }
  });

  console.log('🌐 Opening http://localhost:9000...\n');
  await page.goto('http://localhost:9000');

  console.log('⏳ Waiting for chart to load...\n');
  await page.waitForTimeout(5000);

  console.log('👀 Monitoring for 2 minutes...');
  console.log('   - Watch for console logs');
  console.log('   - Watch for /minute/current API calls');
  console.log('   - Check if chart updates every 60 seconds\n');

  // 2분 동안 모니터링
  await page.waitForTimeout(120000);

  console.log('\n✅ Monitoring complete!');
  await browser.close();
})();
