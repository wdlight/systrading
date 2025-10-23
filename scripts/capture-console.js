const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Set viewport size
  await page.setViewport({ width: 1920, height: 1080 });

  // Collect console logs
  const consoleLogs = [];
  page.on('console', msg => {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      type: msg.type(),
      text: msg.text(),
      args: msg.args()
    };
    consoleLogs.push(logEntry);
    console.log(`[${timestamp}] [${msg.type()}] ${msg.text()}`);
  });

  // Collect network errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR] ${error.message}`);
    consoleLogs.push({
      timestamp: new Date().toISOString(),
      type: 'error',
      text: `PAGE ERROR: ${error.message}`
    });
  });

  // Navigate to the page
  console.log('Navigating to http://localhost:9000/trview...');
  await page.goto('http://localhost:9000/trview', {
    waitUntil: 'networkidle2',
    timeout: 30000
  });

  console.log('Page loaded, waiting 15 seconds to capture console logs...');
  await new Promise(resolve => setTimeout(resolve, 15000));

  // Take screenshot
  console.log('Taking screenshot...');
  await page.screenshot({
    path: '/tmp/trview_console.png',
    fullPage: true
  });

  // Save console logs to file
  const logsPath = '/tmp/console_logs.json';
  fs.writeFileSync(logsPath, JSON.stringify(consoleLogs, null, 2));
  console.log(`Console logs saved to ${logsPath}`);

  // Create a summary
  const summary = {
    totalLogs: consoleLogs.length,
    errors: consoleLogs.filter(l => l.type === 'error').length,
    warnings: consoleLogs.filter(l => l.type === 'warning').length,
    websocketMessages: consoleLogs.filter(l => l.text.includes('WebSocket') || l.text.includes('구독')).length,
    minuteCandleUpdates: consoleLogs.filter(l => l.text.includes('minute_candle_update')).length
  };

  console.log('\n=== Summary ===');
  console.log(JSON.stringify(summary, null, 2));

  // Keep browser open for manual inspection
  console.log('\nBrowser will remain open for 30 seconds for manual inspection...');
  await new Promise(resolve => setTimeout(resolve, 30000));

  await browser.close();
  console.log('Done!');
})();
