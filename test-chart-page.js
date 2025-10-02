const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('useInfinite') || text.includes('Real-time') || text.includes('polling') || text.includes('candle')) {
      console.log(`[LOG] ${text}`);
    }
  });

  console.log('Opening /trading page...');
  await page.goto('http://localhost:9000/trading');
  
  await page.waitForTimeout(5000);
  
  console.log('Opening /echart page...');
  await page.goto('http://localhost:9000/echart');
  
  await page.waitForTimeout(5000);

  await browser.close();
})();
