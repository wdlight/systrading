const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Listen to console messages
  page.on('console', msg => {
    console.log(`[CONSOLE ${msg.type()}]:`, msg.text());
  });

  // Listen to network requests
  page.on('request', request => {
    console.log(`[REQUEST]: ${request.method()} ${request.url()}`);
  });

  // Listen to network responses
  page.on('response', response => {
    const status = response.status();
    const url = response.url();
    if (status >= 400) {
      console.log(`[ERROR RESPONSE]: ${status} ${url}`);
    }
  });

  // Listen to page errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR]:`, error.message);
  });

  console.log('\n=== Opening http://localhost:9000/test-chart ===\n');

  try {
    const response = await page.goto('http://localhost:9000/test-chart', {
      waitUntil: 'networkidle',
      timeout: 10000
    });

    console.log(`\n[RESPONSE STATUS]: ${response.status()}`);
    console.log(`[RESPONSE URL]: ${response.url()}`);

    // Take screenshot
    await page.screenshot({ path: 'test-chart-debug.png' });
    console.log('\nScreenshot saved: test-chart-debug.png');

    // Get page title
    const title = await page.title();
    console.log(`[PAGE TITLE]: ${title}`);

    // Wait a bit to see the page
    await page.waitForTimeout(3000);

  } catch (error) {
    console.error('\n[NAVIGATION ERROR]:', error.message);
  }

  await browser.close();
  console.log('\n=== Debug complete ===\n');
})();
