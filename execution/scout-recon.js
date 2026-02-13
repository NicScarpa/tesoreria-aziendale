/**
 * Scout Reconnaissance Script - Sibill (app.sibill.com)
 * Fase 1: Login, Tech Stack, JS Sources, Navigazione, Network capture
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const BASE_DIR = '/Users/nicolascarpa/Desktop/Progetti/sibill-re';
const SCREENSHOTS_DIR = path.join(BASE_DIR, 'assets/screenshots');
const JS_DIR = path.join(BASE_DIR, 'assets/js-sources');
const HAR_DIR = path.join(BASE_DIR, 'assets/har');
const TMP_DIR = path.join(BASE_DIR, '.tmp');

// Read credentials
const envContent = fs.readFileSync(path.join(BASE_DIR, 'credenziali.env'), 'utf8');
const lines = envContent.trim().split('\n');
let email = '', password = '';
for (const line of lines) {
  if (line.startsWith('user:')) email = line.split(':').slice(1).join(':').trim();
  if (line.startsWith('password:')) password = line.split(':').slice(1).join(':').trim();
}

// Collected data
const scoutData = {
  timestamp: new Date().toISOString(),
  tech_stack: {},
  pages: [],
  js_files: [],
  auth_info: {},
  network_requests: [],
  storage_data: {}
};

// Network requests collector
const allNetworkRequests = [];

function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith('https') ? https : http;
    proto.get(url, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return downloadFile(res.headers.location, destPath).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        fs.writeFileSync(destPath, Buffer.concat(chunks));
        resolve(destPath);
      });
      res.on('error', reject);
    }).on('error', reject);
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

(async () => {
  console.log('=== SCOUT RECON START ===');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  // Setup network monitoring
  const page = await context.newPage();

  page.on('request', (request) => {
    allNetworkRequests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers(),
      postData: request.postData(),
      resourceType: request.resourceType(),
      timestamp: new Date().toISOString()
    });
  });

  page.on('response', async (response) => {
    const url = response.url();
    const status = response.status();
    const entry = allNetworkRequests.find(r => r.url === url && !r.status);
    if (entry) {
      entry.status = status;
      entry.statusText = response.statusText();
      entry.responseHeaders = response.headers();
      // Try to capture JSON responses (API calls)
      if (response.headers()['content-type']?.includes('application/json')) {
        try {
          const body = await response.text();
          entry.responseBody = body.substring(0, 50000); // limit size
        } catch (e) {}
      }
    }
  });

  try {
    // === FASE 1: LOGIN ===
    console.log('\n--- FASE 1: LOGIN ---');
    await page.goto('https://app.sibill.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(2000);
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '00-login-page.png'), fullPage: true });
    console.log('Screenshot login page salvato');

    // Try to find and fill the login form
    // First let's see what's on the page
    const pageContent = await page.content();
    console.log('Page title:', await page.title());
    console.log('Page URL:', page.url());

    // Check for common login form selectors
    const emailSelectors = [
      'input[type="email"]',
      'input[name="email"]',
      'input[name="username"]',
      'input[placeholder*="email" i]',
      'input[placeholder*="mail" i]',
      'input[id*="email" i]',
      'input[id*="user" i]',
      '#email',
      '#username'
    ];

    const passwordSelectors = [
      'input[type="password"]',
      'input[name="password"]',
      '#password'
    ];

    let emailInput = null;
    for (const sel of emailSelectors) {
      emailInput = await page.$(sel);
      if (emailInput) {
        console.log(`Found email input: ${sel}`);
        break;
      }
    }

    let passwordInput = null;
    for (const sel of passwordSelectors) {
      passwordInput = await page.$(sel);
      if (passwordInput) {
        console.log(`Found password input: ${sel}`);
        break;
      }
    }

    if (emailInput && passwordInput) {
      await emailInput.fill(email);
      await sleep(500);
      await passwordInput.fill(password);
      await sleep(500);

      // Find submit button
      const submitSelectors = [
        'button[type="submit"]',
        'button:has-text("Login")',
        'button:has-text("Accedi")',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        'input[type="submit"]'
      ];

      for (const sel of submitSelectors) {
        const btn = await page.$(sel);
        if (btn) {
          console.log(`Found submit button: ${sel}`);
          await btn.click();
          break;
        }
      }

      // Wait for navigation after login
      await page.waitForLoadState('load', { timeout: 30000 }).catch(() => {});
      await sleep(5000);
      console.log('Post-login URL:', page.url());
    } else {
      console.log('Login form not found with standard selectors. Trying alternative approach...');
      // Dump page HTML to help debug
      const html = await page.content();
      fs.writeFileSync(path.join(TMP_DIR, 'login-page-html.txt'), html);
      console.log('Page HTML saved to .tmp/login-page-html.txt');

      // Try clicking any visible inputs
      const allInputs = await page.$$('input');
      console.log(`Found ${allInputs.length} input elements on page`);
      for (let i = 0; i < allInputs.length; i++) {
        const inp = allInputs[i];
        const type = await inp.getAttribute('type');
        const name = await inp.getAttribute('name');
        const id = await inp.getAttribute('id');
        const placeholder = await inp.getAttribute('placeholder');
        console.log(`  Input ${i}: type=${type}, name=${name}, id=${id}, placeholder=${placeholder}`);
      }
    }

    // Take dashboard screenshot
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '01-dashboard.png'), fullPage: true });
    console.log('Screenshot dashboard salvato');

    // === FASE 2: TECH STACK IDENTIFICATION ===
    console.log('\n--- FASE 2: TECH STACK ---');

    const techStack = await page.evaluate(() => {
      const stack = {
        framework: 'unknown',
        hasNextData: !!window.__NEXT_DATA__,
        hasNuxt: !!window.__NUXT__,
        hasAngular: !!document.querySelector('[ng-version]'),
        hasReactRoot: !!document.querySelector('[data-reactroot]') || !!document.querySelector('#__next'),
        hasReactContainer: !!document.getElementById('_reactRootContainer'),
        hasVue: !!document.querySelector('[data-v-]'),
        nextData: window.__NEXT_DATA__ ? JSON.stringify(window.__NEXT_DATA__).substring(0, 5000) : null,
        metaTags: Array.from(document.querySelectorAll('meta')).map(m => ({
          name: m.getAttribute('name'),
          content: m.getAttribute('content'),
          property: m.getAttribute('property')
        })),
        angularVersion: document.querySelector('[ng-version]')?.getAttribute('ng-version'),
        scripts: Array.from(document.querySelectorAll('script')).map(s => ({
          src: s.src,
          type: s.type,
          id: s.id,
          hasInnerContent: !!s.innerText?.trim()
        })),
        links: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href),
        bodyClasses: document.body?.className,
        rootElement: document.getElementById('root')?.tagName || document.getElementById('__next')?.tagName || document.getElementById('app')?.tagName || null,
        rootId: document.body?.firstElementChild?.id
      };

      // Identify framework
      if (stack.hasNextData) stack.framework = 'Next.js';
      else if (stack.hasNuxt) stack.framework = 'Nuxt.js';
      else if (stack.angularVersion) stack.framework = `Angular ${stack.angularVersion}`;
      else if (stack.hasReactRoot || stack.hasReactContainer || document.getElementById('root')) stack.framework = 'React';
      else if (stack.hasVue) stack.framework = 'Vue.js';

      return stack;
    });

    console.log('Framework:', techStack.framework);
    console.log('Next.js data:', techStack.hasNextData);
    console.log('React root:', techStack.hasReactRoot);
    console.log('Root element:', techStack.rootElement);
    console.log('Root ID:', techStack.rootId);
    scoutData.tech_stack.framework_detection = techStack;

    // === STORAGE & COOKIES ===
    console.log('\n--- STORAGE & COOKIES ---');

    const storageData = await page.evaluate(() => {
      const ls = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        const val = localStorage.getItem(key);
        ls[key] = val?.substring(0, 2000);
      }
      const ss = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        const val = sessionStorage.getItem(key);
        ss[key] = val?.substring(0, 2000);
      }
      return {
        localStorage: ls,
        sessionStorage: ss,
        cookies: document.cookie
      };
    });

    console.log('localStorage keys:', Object.keys(storageData.localStorage));
    console.log('sessionStorage keys:', Object.keys(storageData.sessionStorage));
    console.log('Cookies:', storageData.cookies?.substring(0, 200));
    scoutData.storage_data = storageData;

    // Auth info
    const cookies = await context.cookies();
    scoutData.auth_info = {
      cookies: cookies.map(c => ({ name: c.name, domain: c.domain, path: c.path, httpOnly: c.httpOnly, secure: c.secure, sameSite: c.sameSite, expires: c.expires })),
      localStorageKeys: Object.keys(storageData.localStorage),
      sessionStorageKeys: Object.keys(storageData.sessionStorage)
    };

    // Detect auth type from storage
    for (const key of Object.keys(storageData.localStorage)) {
      if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth') || key.toLowerCase().includes('session')) {
        console.log(`  Auth-related localStorage key: ${key}`);
        scoutData.auth_info.type = 'JWT/Token (localStorage)';
        scoutData.auth_info.token_location = `localStorage.${key}`;
      }
    }
    for (const c of cookies) {
      if (c.name.toLowerCase().includes('token') || c.name.toLowerCase().includes('session') || c.name.toLowerCase().includes('auth')) {
        console.log(`  Auth-related cookie: ${c.name}`);
        if (!scoutData.auth_info.type) {
          scoutData.auth_info.type = 'Cookie-based';
          scoutData.auth_info.token_location = `cookie.${c.name}`;
        }
      }
    }

    // === FASE 3: JS SOURCES ===
    console.log('\n--- FASE 3: JS SOURCES ---');

    const scriptUrls = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
    });

    console.log(`Found ${scriptUrls.length} script URLs`);
    for (const url of scriptUrls) {
      console.log(`  - ${url}`);
    }

    // Download JS files
    for (const url of scriptUrls) {
      try {
        const urlObj = new URL(url);
        let filename = urlObj.pathname.split('/').pop() || 'unknown.js';
        // Sanitize filename
        filename = filename.replace(/[^a-zA-Z0-9._-]/g, '_');
        if (!filename.endsWith('.js')) filename += '.js';

        const destPath = path.join(JS_DIR, filename);
        await downloadFile(url, destPath);
        scoutData.js_files.push(`assets/js-sources/${filename}`);
        console.log(`  Downloaded: ${filename}`);
      } catch (e) {
        console.log(`  Failed to download ${url}: ${e.message}`);
      }
    }

    // === FASE 4: NAVIGAZIONE SISTEMATICA ===
    console.log('\n--- FASE 4: NAVIGAZIONE SISTEMATICA ---');

    // First, get navigation structure
    const navInfo = await page.evaluate(() => {
      // Find navigation elements
      const navElements = document.querySelectorAll('nav, [role="navigation"], .sidebar, .nav, .menu, [class*="sidebar"], [class*="nav"], [class*="menu"]');
      const navData = [];

      for (const nav of navElements) {
        const links = nav.querySelectorAll('a[href]');
        for (const link of links) {
          navData.push({
            text: link.textContent?.trim(),
            href: link.href,
            title: link.title,
            ariaLabel: link.getAttribute('aria-label')
          });
        }
      }

      // Also get all links on page
      const allLinks = Array.from(document.querySelectorAll('a[href]'))
        .filter(a => {
          const href = a.href;
          return href &&
            href.startsWith('https://app.sibill.com') &&
            !href.includes('#') &&
            a.textContent?.trim();
        })
        .map(a => ({
          text: a.textContent?.trim(),
          href: a.href,
          inNav: !!a.closest('nav, [role="navigation"], .sidebar, .nav, .menu, [class*="sidebar"], [class*="nav"], [class*="menu"]')
        }));

      // Look for clickable menu items (not just links)
      const buttons = Array.from(document.querySelectorAll('button, [role="button"], [role="menuitem"], [class*="menu-item"], [class*="nav-item"]'))
        .filter(b => b.textContent?.trim())
        .map(b => ({
          text: b.textContent?.trim(),
          tag: b.tagName,
          className: b.className?.substring?.(0, 200),
          ariaLabel: b.getAttribute('aria-label'),
          dataTestId: b.getAttribute('data-testid')
        }));

      return { navElements: navData, allLinks, buttons };
    });

    console.log('Navigation links:', navInfo.navElements.length);
    console.log('All internal links:', navInfo.allLinks.length);
    console.log('Buttons/menu items:', navInfo.buttons.length);

    // Save nav info
    fs.writeFileSync(path.join(TMP_DIR, 'nav-info.json'), JSON.stringify(navInfo, null, 2));

    // Collect unique URLs to visit
    const urlsToVisit = new Set();
    for (const link of [...navInfo.navElements, ...navInfo.allLinks]) {
      if (link.href && link.href.startsWith('https://app.sibill.com')) {
        urlsToVisit.add(link.href);
      }
    }

    console.log(`\nURLs to visit: ${urlsToVisit.size}`);

    // Navigate each section
    let screenshotCounter = 2;
    const visitedPages = [];

    for (const url of urlsToVisit) {
      try {
        console.log(`\nNavigating to: ${url}`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
        await sleep(2000);

        const pageTitle = await page.title();
        const currentUrl = page.url();

        // Get page info
        const pageInfo = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent?.trim()).filter(Boolean);
          const tables = document.querySelectorAll('table, [class*="table"], [role="table"], [class*="grid"]').length;
          const forms = document.querySelectorAll('form').length;
          const buttons = Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(Boolean);
          const inputs = Array.from(document.querySelectorAll('input, select, textarea')).map(i => ({
            type: i.type || i.tagName.toLowerCase(),
            name: i.name,
            placeholder: i.placeholder,
            id: i.id
          }));
          const charts = document.querySelectorAll('canvas, svg, [class*="chart"], [class*="graph"]').length;

          return { headings, tables, forms, buttons: buttons.slice(0, 20), inputs: inputs.slice(0, 30), charts };
        });

        // Generate meaningful screenshot name
        const urlPath = new URL(currentUrl).pathname.replace(/\//g, '-').replace(/^-/, '').replace(/-$/, '') || 'root';
        const screenshotName = `${String(screenshotCounter).padStart(2, '0')}-${urlPath.substring(0, 50)}.png`;
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, screenshotName), fullPage: true });

        const pageData = {
          id: urlPath,
          url: new URL(currentUrl).pathname,
          title: pageTitle,
          description: pageInfo.headings.join(' > '),
          screenshot: `assets/screenshots/${screenshotName}`,
          components: [],
          actions: []
        };

        if (pageInfo.tables > 0) pageData.components.push(`tabelle(${pageInfo.tables})`);
        if (pageInfo.forms > 0) pageData.components.push(`form(${pageInfo.forms})`);
        if (pageInfo.charts > 0) pageData.components.push(`grafici(${pageInfo.charts})`);
        if (pageInfo.inputs.length > 0) pageData.components.push(`input(${pageInfo.inputs.length})`);
        pageData.actions = pageInfo.buttons.slice(0, 10);
        pageData.headings = pageInfo.headings;
        pageData.inputs = pageInfo.inputs;

        visitedPages.push(pageData);
        console.log(`  Title: ${pageTitle}, Headings: ${pageInfo.headings.join(', ')}, Tables: ${pageInfo.tables}, Charts: ${pageInfo.charts}`);

        screenshotCounter++;
      } catch (e) {
        console.log(`  Error visiting ${url}: ${e.message}`);
      }
    }

    // Also try to find and click sidebar/navigation items that might not be regular links
    console.log('\n--- Exploring clickable nav items ---');
    await page.goto('https://app.sibill.com/', { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    await sleep(3000);

    // Re-snapshot after going back to dashboard to find nav items
    const clickableNavItems = await page.evaluate(() => {
      const items = [];
      // Look for sidebar items, nav items, menu items
      const selectors = [
        '[class*="sidebar"] a',
        '[class*="sidebar"] [role="button"]',
        '[class*="sidebar"] [class*="item"]',
        'nav a',
        '[role="navigation"] a',
        '[class*="menu"] a',
        '[class*="nav-item"]',
        '[class*="MenuItem"]',
        '[data-testid*="nav"]',
        '[data-testid*="menu"]'
      ];

      for (const sel of selectors) {
        const elements = document.querySelectorAll(sel);
        for (const el of elements) {
          const text = el.textContent?.trim();
          const href = el.getAttribute('href');
          if (text && !items.find(i => i.text === text)) {
            items.push({
              text,
              href,
              tag: el.tagName,
              className: el.className?.toString()?.substring(0, 100)
            });
          }
        }
      }
      return items;
    });

    console.log('Clickable nav items found:');
    for (const item of clickableNavItems) {
      console.log(`  - ${item.text} -> ${item.href || '(no href)'}`);
    }

    // Visit any new URLs found
    for (const item of clickableNavItems) {
      if (item.href && item.href.startsWith('/') && !visitedPages.find(p => p.url === item.href)) {
        try {
          const fullUrl = `https://app.sibill.com${item.href}`;
          console.log(`\nNavigating to new section: ${item.text} (${fullUrl})`);
          await page.goto(fullUrl, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
          await sleep(2000);

          const pageTitle = await page.title();
          const currentUrl = page.url();
          const urlPath = new URL(currentUrl).pathname.replace(/\//g, '-').replace(/^-/, '').replace(/-$/, '') || 'root';
          const screenshotName = `${String(screenshotCounter).padStart(2, '0')}-${urlPath.substring(0, 50)}.png`;
          await page.screenshot({ path: path.join(SCREENSHOTS_DIR, screenshotName), fullPage: true });

          const pageInfo = await page.evaluate(() => {
            const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent?.trim()).filter(Boolean);
            const tables = document.querySelectorAll('table, [class*="table"], [role="table"]').length;
            const forms = document.querySelectorAll('form').length;
            const charts = document.querySelectorAll('canvas, svg, [class*="chart"]').length;
            const buttons = Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(Boolean);
            return { headings, tables, forms, charts, buttons: buttons.slice(0, 20) };
          });

          visitedPages.push({
            id: urlPath,
            url: item.href,
            title: pageTitle,
            description: pageInfo.headings.join(' > '),
            screenshot: `assets/screenshots/${screenshotName}`,
            components: [
              pageInfo.tables > 0 ? `tabelle(${pageInfo.tables})` : null,
              pageInfo.forms > 0 ? `form(${pageInfo.forms})` : null,
              pageInfo.charts > 0 ? `grafici(${pageInfo.charts})` : null
            ].filter(Boolean),
            actions: pageInfo.buttons.slice(0, 10),
            headings: pageInfo.headings
          });

          console.log(`  Title: ${pageTitle}, Headings: ${pageInfo.headings.join(', ')}`);
          screenshotCounter++;
        } catch (e) {
          console.log(`  Error: ${e.message}`);
        }
      }
    }

    // === FASE 5: NETWORK REQUESTS SAVE ===
    console.log('\n--- FASE 5: SAVE NETWORK REQUESTS ---');

    // Filter and save network requests
    const apiRequests = allNetworkRequests.filter(r =>
      r.resourceType === 'xhr' || r.resourceType === 'fetch' ||
      r.url.includes('/api/') || r.url.includes('/graphql')
    );

    console.log(`Total network requests: ${allNetworkRequests.length}`);
    console.log(`API requests (XHR/Fetch): ${apiRequests.length}`);

    // Save full network log
    fs.writeFileSync(
      path.join(HAR_DIR, 'session-complete.txt'),
      JSON.stringify(allNetworkRequests, null, 2)
    );
    console.log('Network requests saved to assets/har/session-complete.txt');

    // Save API-only requests
    fs.writeFileSync(
      path.join(HAR_DIR, 'api-requests.json'),
      JSON.stringify(apiRequests, null, 2)
    );
    console.log('API requests saved to assets/har/api-requests.json');

    // === COMPILE SCOUT DATA ===
    scoutData.pages = visitedPages;
    scoutData.tech_stack.framework = techStack.framework;
    scoutData.tech_stack.ui_library = techStack.links.filter(l => l.includes('material') || l.includes('antd') || l.includes('chakra') || l.includes('tailwind')).join(', ') || 'to be identified from JS';
    scoutData.tech_stack.other_libs = [];

    // Identify auth type
    if (!scoutData.auth_info.type) {
      scoutData.auth_info.type = 'unknown';
    }

    // Identify API endpoints from network
    const apiEndpoints = new Set();
    for (const req of apiRequests) {
      try {
        const url = new URL(req.url);
        apiEndpoints.add(`${req.method} ${url.pathname}`);
      } catch(e) {}
    }
    scoutData.auth_info.endpoints = Array.from(apiEndpoints);

    // Save scout complete JSON
    fs.writeFileSync(
      path.join(TMP_DIR, 'scout-complete.json'),
      JSON.stringify(scoutData, null, 2)
    );
    console.log('\nScout data saved to .tmp/scout-complete.json');

    // Print summary
    console.log('\n=== SCOUT RECON SUMMARY ===');
    console.log(`Framework: ${scoutData.tech_stack.framework}`);
    console.log(`Pages visited: ${visitedPages.length}`);
    console.log(`JS files downloaded: ${scoutData.js_files.length}`);
    console.log(`Total network requests: ${allNetworkRequests.length}`);
    console.log(`API requests captured: ${apiRequests.length}`);
    console.log(`API endpoints discovered: ${apiEndpoints.size}`);
    console.log(`Auth type: ${scoutData.auth_info.type}`);

    console.log('\nPages:');
    for (const p of visitedPages) {
      console.log(`  ${p.url} - ${p.title} - ${p.description}`);
    }

    console.log('\nAPI Endpoints:');
    for (const ep of Array.from(apiEndpoints).sort()) {
      console.log(`  ${ep}`);
    }

  } catch (error) {
    console.error('FATAL ERROR:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
    console.log('\n=== SCOUT RECON COMPLETE ===');
  }
})();
