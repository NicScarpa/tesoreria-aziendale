/**
 * Scout Login Script - Focus on auth flow
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_DIR = '/Users/nicolascarpa/Desktop/Progetti/sibill-re';
const SCREENSHOTS_DIR = path.join(BASE_DIR, 'assets/screenshots');
const TMP_DIR = path.join(BASE_DIR, '.tmp');

// Read credentials
const envContent = fs.readFileSync(path.join(BASE_DIR, 'credenziali.env'), 'utf8');
const lines = envContent.trim().split('\n');
let email = '', password = '';
for (const line of lines) {
  if (line.startsWith('user:')) email = line.split(':').slice(1).join(':').trim();
  if (line.startsWith('password:')) password = line.split(':').slice(1).join(':').trim();
}

(async () => {
  console.log('=== LOGIN FLOW ANALYSIS ===');

  const browser = await chromium.launch({
    headless: false, // Use headed mode to avoid detection
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
  });

  // Inject script to hide automation detection
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
    // Remove headless chrome signatures
    if (navigator.userAgent.includes('HeadlessChrome')) {
      Object.defineProperty(navigator, 'userAgent', {
        get: () => navigator.userAgent.replace('HeadlessChrome', 'Chrome')
      });
    }
  });

  const page = await context.newPage();

  // Track all navigation
  const navigationHistory = [];
  page.on('framenavigated', (frame) => {
    if (frame === page.mainFrame()) {
      navigationHistory.push({ url: frame.url(), timestamp: new Date().toISOString() });
      console.log(`NAVIGATED TO: ${frame.url()}`);
    }
  });

  // Track redirects
  page.on('response', (response) => {
    if (response.status() >= 300 && response.status() < 400) {
      console.log(`REDIRECT ${response.status()}: ${response.url()} -> ${response.headers()['location']}`);
    }
  });

  try {
    // Step 1: Navigate to app
    console.log('\n--- Step 1: Navigate to app.sibill.com ---');
    const response = await page.goto('https://app.sibill.com/', {
      waitUntil: 'load',
      timeout: 60000
    });
    console.log(`Initial response status: ${response?.status()}`);
    console.log(`Final URL: ${page.url()}`);

    // Wait for JS to fully load and any redirects to complete
    await page.waitForTimeout(5000);
    console.log(`URL after 5s: ${page.url()}`);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-01-initial.png'), fullPage: true });

    // Step 2: Check what's on the page
    console.log('\n--- Step 2: Analyze current page ---');
    const pageAnalysis = await page.evaluate(() => {
      const result = {
        url: window.location.href,
        title: document.title,
        allInputs: [],
        allButtons: [],
        allLinks: [],
        allForms: [],
        allText: []
      };

      // Find all inputs
      document.querySelectorAll('input').forEach(inp => {
        result.allInputs.push({
          type: inp.type,
          name: inp.name,
          id: inp.id,
          placeholder: inp.placeholder,
          className: inp.className?.substring(0, 100),
          visible: inp.offsetParent !== null,
          ariaLabel: inp.getAttribute('aria-label')
        });
      });

      // Find all buttons
      document.querySelectorAll('button, [role="button"], a.btn, a[class*="button"]').forEach(btn => {
        result.allButtons.push({
          text: btn.textContent?.trim()?.substring(0, 100),
          type: btn.type,
          className: btn.className?.substring(0, 100),
          href: btn.getAttribute('href'),
          visible: btn.offsetParent !== null
        });
      });

      // Find all links
      document.querySelectorAll('a[href]').forEach(a => {
        result.allLinks.push({
          text: a.textContent?.trim()?.substring(0, 100),
          href: a.href,
          visible: a.offsetParent !== null
        });
      });

      // Find forms
      document.querySelectorAll('form').forEach(f => {
        result.allForms.push({
          action: f.action,
          method: f.method,
          id: f.id,
          className: f.className?.substring(0, 100)
        });
      });

      // Get visible text content
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const text = walker.currentNode.textContent?.trim();
        if (text && text.length > 3 && text.length < 200) {
          result.allText.push(text);
        }
      }

      // Check for iframes (some auth providers use iframes)
      result.iframes = Array.from(document.querySelectorAll('iframe')).map(f => ({
        src: f.src,
        id: f.id,
        title: f.title
      }));

      return result;
    });

    console.log('Inputs:', JSON.stringify(pageAnalysis.allInputs, null, 2));
    console.log('Buttons:', JSON.stringify(pageAnalysis.allButtons, null, 2));
    console.log('Links:', JSON.stringify(pageAnalysis.allLinks, null, 2));
    console.log('Forms:', JSON.stringify(pageAnalysis.allForms, null, 2));
    console.log('Visible text:', pageAnalysis.allText);
    console.log('Iframes:', JSON.stringify(pageAnalysis.iframes, null, 2));

    // Step 3: Try common login URLs
    console.log('\n--- Step 3: Try common login URLs ---');
    const loginUrls = [
      'https://app.sibill.com/login',
      'https://app.sibill.com/signin',
      'https://app.sibill.com/sign-in',
      'https://app.sibill.com/accedi',
      'https://app.sibill.com/auth/login',
      'https://app.sibill.com/auth',
    ];

    for (const url of loginUrls) {
      try {
        await page.goto(url, { waitUntil: 'load', timeout: 15000 });
        await page.waitForTimeout(3000);
        const finalUrl = page.url();
        const title = await page.title();
        const inputCount = await page.$$eval('input', inputs => inputs.length);
        console.log(`${url} -> ${finalUrl} (title: ${title}, inputs: ${inputCount})`);

        if (inputCount > 0) {
          console.log('FOUND LOGIN PAGE!');
          await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-02-login-page.png'), fullPage: true });

          // Analyze the login page
          const loginPageInfo = await page.evaluate(() => {
            return {
              inputs: Array.from(document.querySelectorAll('input')).map(i => ({
                type: i.type,
                name: i.name,
                id: i.id,
                placeholder: i.placeholder,
                ariaLabel: i.getAttribute('aria-label'),
                visible: i.offsetParent !== null
              })),
              buttons: Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.textContent?.trim(),
                type: b.type
              })),
              title: document.title,
              url: window.location.href
            };
          });
          console.log('Login page analysis:', JSON.stringify(loginPageInfo, null, 2));
          break;
        }
      } catch (e) {
        console.log(`${url} -> ERROR: ${e.message}`);
      }
    }

    // Step 4: Check if there's an OAuth/external login
    console.log('\n--- Step 4: Check for OAuth/external auth ---');
    // Navigate back to main app to see the full redirect chain
    const navPromise = page.waitForNavigation({ timeout: 15000 }).catch(() => null);
    await page.goto('https://app.sibill.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(8000);

    console.log(`After full wait, URL: ${page.url()}`);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-03-after-wait.png'), fullPage: true });

    // Check all URLs we've been redirected to
    console.log('\nNavigation history:');
    for (const nav of navigationHistory) {
      console.log(`  ${nav.timestamp}: ${nav.url}`);
    }

    // Step 5: If we're on logout page, look for a login link/button
    console.log('\n--- Step 5: Look for login action ---');
    const currentUrl = page.url();
    if (currentUrl.includes('logout') || currentUrl.includes('login') || currentUrl.includes('auth')) {
      // Wait more time for JS to render
      await page.waitForTimeout(5000);
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-04-current.png'), fullPage: true });

      const loginActions = await page.evaluate(() => {
        const actions = [];
        // Check all clickable elements
        document.querySelectorAll('a, button, [role="button"], [onclick]').forEach(el => {
          const text = el.textContent?.trim();
          const href = el.getAttribute('href');
          const onclick = el.getAttribute('onclick');
          if (text || href || onclick) {
            actions.push({
              tag: el.tagName,
              text: text?.substring(0, 100),
              href,
              onclick: onclick?.substring(0, 200),
              visible: el.offsetParent !== null,
              className: el.className?.toString()?.substring(0, 100)
            });
          }
        });
        return actions;
      });
      console.log('Clickable elements:', JSON.stringify(loginActions, null, 2));

      // Try to find and click login button/link
      for (const action of loginActions) {
        if (action.text && (
          action.text.toLowerCase().includes('login') ||
          action.text.toLowerCase().includes('accedi') ||
          action.text.toLowerCase().includes('entra') ||
          action.text.toLowerCase().includes('sign in')
        )) {
          console.log(`Found login action: "${action.text}" (${action.tag})`);
          try {
            await page.click(`text="${action.text}"`);
            await page.waitForTimeout(5000);
            console.log(`After clicking, URL: ${page.url()}`);
            await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-05-after-click.png'), fullPage: true });
          } catch (e) {
            console.log(`Click failed: ${e.message}`);
          }
          break;
        }
      }
    }

    // Step 6: Try to fill login form if found
    console.log('\n--- Step 6: Attempt login ---');
    const finalPageUrl = page.url();
    console.log(`Current URL: ${finalPageUrl}`);

    // Look for login form
    const hasEmailInput = await page.$('input[type="email"], input[name="email"], input[placeholder*="email" i], input[placeholder*="mail" i]');
    const hasPasswordInput = await page.$('input[type="password"]');

    if (hasEmailInput && hasPasswordInput) {
      console.log('Login form found! Filling credentials...');
      await hasEmailInput.fill(email);
      await page.waitForTimeout(500);
      await hasPasswordInput.fill(password);
      await page.waitForTimeout(500);

      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-06-filled.png'), fullPage: true });

      // Submit
      const submitBtn = await page.$('button[type="submit"]') ||
                         await page.$('button:has-text("Login")') ||
                         await page.$('button:has-text("Accedi")') ||
                         await page.$('button:has-text("Sign in")') ||
                         await page.$('button:has-text("Entra")');

      if (submitBtn) {
        console.log('Clicking submit button...');
        await submitBtn.click();
        await page.waitForTimeout(10000);
        console.log(`After login, URL: ${page.url()}`);
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, 'login-flow-07-after-login.png'), fullPage: true });
      }
    } else {
      console.log('No email/password inputs found on current page');

      // Full DOM dump for debugging
      const html = await page.content();
      fs.writeFileSync(path.join(TMP_DIR, 'current-page-html.txt'), html);
      console.log('Current page HTML saved to .tmp/current-page-html.txt');

      // Check if it's a custom auth provider page
      console.log(`Current page URL domain: ${new URL(page.url()).hostname}`);
    }

    // Save all navigation history
    fs.writeFileSync(path.join(TMP_DIR, 'navigation-history.json'), JSON.stringify(navigationHistory, null, 2));

  } catch (error) {
    console.error('ERROR:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
    console.log('\n=== LOGIN FLOW ANALYSIS COMPLETE ===');
  }
})();
