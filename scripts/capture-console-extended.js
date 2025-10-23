const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Collect console logs with detailed tracking
  const consoleLogs = [];
  let minuteCandleCount = 0;

  page.on('console', msg => {
    const timestamp = new Date().toISOString();
    const text = msg.text();
    const logEntry = {
      timestamp,
      type: msg.type(),
      text: text
    };
    consoleLogs.push(logEntry);

    // Highlight important messages
    if (text.includes('minute_candle')) {
      minuteCandleCount++;
      console.log(`\n🔥 [${timestamp}] MINUTE CANDLE MESSAGE #${minuteCandleCount}:`);
      console.log(`   ${text}`);
    } else if (text.includes('구독 요청') || text.includes('subscribe')) {
      console.log(`\n📤 [${timestamp}] SUBSCRIPTION REQUEST:`);
      console.log(`   ${text}`);
    } else if (text.includes('received')) {
      console.log(`\n📥 [${timestamp}] RECEIVED MESSAGE:`);
      console.log(`   ${text}`);
    } else {
      console.log(`[${timestamp}] [${msg.type()}] ${text}`);
    }
  });

  page.on('pageerror', error => {
    console.log(`\n❌ [PAGE ERROR] ${error.message}`);
  });

  // Navigate to the page
  console.log('\nNavigating to http://localhost:9000/trview...\n');
  await page.goto('http://localhost:9000/trview', {
    waitUntil: 'networkidle2',
    timeout: 30000
  });

  console.log('\n⏰ Waiting 60 seconds to capture real-time updates...\n');

  // Wait longer to capture actual real-time updates
  for (let i = 0; i < 12; i++) {
    await new Promise(resolve => setTimeout(resolve, 5000));
    console.log(`\n⏱️  Elapsed: ${(i + 1) * 5} seconds | Minute candle messages: ${minuteCandleCount}`);
  }

  // Take screenshot
  console.log('\nTaking screenshot...');
  await page.screenshot({
    path: '/tmp/trview_console_extended.png',
    fullPage: true
  });

  // Save logs
  const logsPath = '/tmp/console_logs_extended.json';
  fs.writeFileSync(logsPath, JSON.stringify(consoleLogs, null, 2));
  console.log(`\nConsole logs saved to ${logsPath}`);

  // Create detailed summary
  const summary = {
    totalLogs: consoleLogs.length,
    errors: consoleLogs.filter(l => l.type === 'error').length,
    warnings: consoleLogs.filter(l => l.type === 'warning').length,
    websocketConnections: consoleLogs.filter(l => l.text.includes('WebSocket 연결')).length,
    subscriptionRequests: consoleLogs.filter(l => l.text.includes('구독 요청')).length,
    receivedMessages: consoleLogs.filter(l => l.text.includes('received')).length,
    minuteCandleUpdates: consoleLogs.filter(l => l.text.includes('minute_candle_update')).length,
    minuteCandleFinalized: consoleLogs.filter(l => l.text.includes('minute_candle_finalized')).length,
    minuteCandleListeners: consoleLogs.filter(l => l.text.includes('minute_candle') && l.text.includes('리스너')).length
  };

  console.log('\n=== DETAILED SUMMARY ===');
  console.log(JSON.stringify(summary, null, 2));

  // Show minute candle related logs
  const minuteCandelLogs = consoleLogs.filter(l => l.text.includes('minute_candle'));
  console.log('\n=== ALL MINUTE_CANDLE LOGS ===');
  minuteCandelLogs.forEach(log => {
    console.log(`[${log.timestamp}] ${log.text}`);
  });

  await browser.close();
  console.log('\nDone!');
})();
