const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Users/yann/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium'
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  await page.goto('http://localhost:5175/watchlist/1', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/tmp/watchlist-screenshot.png', fullPage: true });
  await browser.close();
  console.log('Screenshot saved to /tmp/watchlist-screenshot.png');
})();
