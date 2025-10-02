const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const logs = [];
  page.on('console', msg => {
    const text = msg.text();
    const time = new Date().toLocaleTimeString();
    logs.push({ time, text });
    console.log('[' + time + '] ' + text);
  });

  page.on('request', req => {
    const url = req.url();
    if (url.includes('/current')) {
      const time = new Date().toLocaleTimeString();
      console.log('[' + time + '] [API] ' + url);
    }
  });

  console.log('Opening /test-infinite-scroll...');
  await page.goto('http://localhost:9000/test-infinite-scroll');

  console.log('Waiting 70 seconds...');
  await page.waitForTimeout(70000);

  console.log('\n=== Summary ===');
  const pollingLogs = logs.filter(l =>
    l.text.includes('polling') ||
    l.text.includes('Real-time') ||
    l.text.includes('useInfiniteChartData')
  );

  if (pollingLogs.length > 0) {
    console.log('Polling logs:');
    pollingLogs.forEach(l => console.log('  ' + l.time + ': ' + l.text));
  } else {
    console.log('No polling logs found');
  }

  await browser.close();
})();
