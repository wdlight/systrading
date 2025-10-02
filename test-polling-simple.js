const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // 모든 콘솔 로그 캡처
  const logs = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    console.log(`[Console] ${text}`);
  });

  console.log('Opening page...');
  await page.goto('http://localhost:9000');
  
  console.log('Waiting 10 seconds...');
  await page.waitForTimeout(10000);

  console.log('\n=== Console Logs Summary ===');
  const relevantLogs = logs.filter(log => 
    log.includes('InfiniteChart') || 
    log.includes('polling') || 
    log.includes('Real-time') ||
    log.includes('useInfiniteChartData')
  );
  
  if (relevantLogs.length === 0) {
    console.log('❌ No polling-related logs found!');
    console.log('Total console logs:', logs.length);
  } else {
    relevantLogs.forEach(log => console.log(`  - ${log}`));
  }

  await browser.close();
})();
