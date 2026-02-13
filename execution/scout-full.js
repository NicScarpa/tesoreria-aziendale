/**
 * Scout Full Reconnaissance - Sibill (app.sibill.com)
 * Login + Tech Stack + JS Sources + Full Navigation + Network Capture
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
const cLines = envContent.trim().split('\n');
let email = '', password = '';
for (const line of cLines) {
  if (line.startsWith('user:')) email = line.split(':').slice(1).join(':').trim();
  if (line.startsWith('password:')) password = line.split(':').slice(1).join(':').trim();
}

// Collected data
const scoutData = {
  timestamp: new Date().toISOString(),
  tech_stack: { framework: '', ui_library: '', auth_type: '', other_libs: [] },
  pages: [],
  js_files: [],
  auth_info: { type: '', token_location: '', endpoints: {} },
  network_summary: {}
};

const allNetworkRequests = [];

function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith('https') ? https : http;
    const req = proto.get(url, { timeout: 15000 }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return downloadFile(res.headers.location, destPath).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => { fs.writeFileSync(destPath, Buffer.concat(chunks)); resolve(destPath); });
      res.on('error', reject);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

(async () => {
  console.log('=== SCOUT FULL RECON START ===');

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
  });

  const page = await context.newPage();

  // Network monitoring
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
    const entry = allNetworkRequests.find(r => r.url === url && !r.status);
    if (entry) {
      entry.status = response.status();
      entry.statusText = response.statusText();
      entry.responseHeaders = response.headers();
      if (response.headers()['content-type']?.includes('application/json') ||
          response.headers()['content-type']?.includes('application/vnd.api+json')) {
        try {
          const body = await response.text();
          entry.responseBody = body.substring(0, 100000);
        } catch (e) {}
      }
    }
  });

  try {
    // ============================================================
    // FASE 1: LOGIN
    // ============================================================
    console.log('\n========== FASE 1: LOGIN ==========');
    await page.goto('https://app.sibill.com/login', { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(3000);
    console.log(`URL: ${page.url()}, Title: ${await page.title()}`);

    // Wait for login form to appear
    await page.waitForSelector('input[name="username"]', { timeout: 15000 });
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '00-login-page.png'), fullPage: true });

    // Fill login form
    await page.fill('input[name="username"]', email);
    await page.waitForTimeout(300);
    await page.fill('input[type="password"]', password);
    await page.waitForTimeout(300);

    // Submit
    console.log('Submitting login...');
    await Promise.all([
      page.waitForNavigation({ timeout: 30000 }).catch(() => null),
      page.click('button[type="submit"]')
    ]);
    await page.waitForTimeout(5000);

    const postLoginUrl = page.url();
    console.log(`Post-login URL: ${postLoginUrl}`);

    // Check if login was successful
    if (postLoginUrl.includes('login') || postLoginUrl.includes('logout')) {
      console.log('Login might have failed. Checking for error messages...');
      const errorMsg = await page.evaluate(() => {
        const errorEl = document.querySelector('[class*="error"], [class*="alert"], [role="alert"]');
        return errorEl?.textContent?.trim();
      });
      if (errorMsg) console.log(`Error message: ${errorMsg}`);

      // Try again with a longer wait
      await page.waitForTimeout(5000);
      console.log(`URL after extra wait: ${page.url()}`);
    }

    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '01-dashboard.png'), fullPage: true });
    console.log('Dashboard screenshot saved');

    // ============================================================
    // FASE 2: TECH STACK & AUTH
    // ============================================================
    console.log('\n========== FASE 2: TECH STACK & AUTH ==========');

    const techStack = await page.evaluate(() => {
      const stack = {
        framework: 'unknown',
        hasNextData: !!window.__NEXT_DATA__,
        hasNuxt: !!window.__NUXT__,
        hasAngular: !!document.querySelector('[ng-version]'),
        hasReactRoot: !!document.getElementById('root'),
        nextData: window.__NEXT_DATA__ ? JSON.stringify(window.__NEXT_DATA__).substring(0, 2000) : null,
        scripts: Array.from(document.querySelectorAll('script[src]')).map(s => s.src),
        stylesheets: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href),
        metaTags: Array.from(document.querySelectorAll('meta')).map(m => ({
          name: m.name, content: m.content?.substring(0, 200), property: m.getAttribute('property')
        })).filter(m => m.name || m.property),
        bodyClasses: document.body?.className
      };

      if (stack.hasNextData) stack.framework = 'Next.js';
      else if (stack.hasNuxt) stack.framework = 'Nuxt.js';
      else if (stack.hasAngular) stack.framework = 'Angular';
      else if (stack.hasReactRoot) stack.framework = 'React (Vite)';

      return stack;
    });

    console.log(`Framework: ${techStack.framework}`);
    scoutData.tech_stack.framework = techStack.framework;

    // Storage & Cookies
    const storageData = await page.evaluate(() => {
      const ls = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        ls[key] = localStorage.getItem(key)?.substring(0, 500);
      }
      const ss = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        ss[key] = sessionStorage.getItem(key)?.substring(0, 500);
      }
      return { localStorage: ls, sessionStorage: ss, cookies: document.cookie };
    });

    const cookies = await context.cookies();
    console.log('localStorage keys:', Object.keys(storageData.localStorage));
    console.log('sessionStorage keys:', Object.keys(storageData.sessionStorage));
    console.log('Cookies:', cookies.map(c => c.name).join(', '));

    // Determine auth type
    let authType = 'unknown';
    let tokenLocation = 'unknown';

    for (const key of Object.keys(storageData.localStorage)) {
      const val = storageData.localStorage[key];
      if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth')) {
        authType = 'Token in localStorage';
        tokenLocation = `localStorage["${key}"]`;
      }
    }

    for (const c of cookies) {
      if (c.name.toLowerCase().includes('session') || c.name.toLowerCase().includes('token') || c.name.toLowerCase().includes('auth') || c.name === '_sibill_session') {
        authType = 'Cookie-based session';
        tokenLocation = `cookie: ${c.name}`;
      }
    }

    // Check for Authorization header in recent API requests
    for (const req of allNetworkRequests) {
      if (req.headers?.['authorization']) {
        const authHeader = req.headers['authorization'];
        if (authHeader.startsWith('Bearer ')) {
          authType = 'Bearer Token (JWT)';
          tokenLocation = 'Authorization header';
        }
      }
    }

    console.log(`Auth type: ${authType}`);
    console.log(`Token location: ${tokenLocation}`);

    scoutData.auth_info.type = authType;
    scoutData.auth_info.token_location = tokenLocation;
    scoutData.tech_stack.auth_type = authType;

    // Save storage data for reference
    fs.writeFileSync(path.join(TMP_DIR, 'storage-data.json'), JSON.stringify({
      localStorage: storageData.localStorage,
      sessionStorage: storageData.sessionStorage,
      cookies: cookies.map(c => ({ name: c.name, domain: c.domain, path: c.path, httpOnly: c.httpOnly, secure: c.secure, sameSite: c.sameSite }))
    }, null, 2));

    // ============================================================
    // FASE 3: JS SOURCES
    // ============================================================
    console.log('\n========== FASE 3: JS SOURCES ==========');

    const scriptUrls = await page.evaluate(() =>
      Array.from(document.querySelectorAll('script[src]')).map(s => s.src)
    );

    // Also get all loaded JS modules from the page
    const allJsModules = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('link[rel="modulepreload"]')).map(l => l.href);
    });

    const allJsUrls = [...new Set([...scriptUrls, ...allJsModules])];
    console.log(`Found ${allJsUrls.length} JS URLs (${scriptUrls.length} scripts + ${allJsModules.length} modules)`);

    for (const url of allJsUrls) {
      try {
        const urlObj = new URL(url);
        let filename = urlObj.pathname.split('/').pop() || 'unknown.js';
        filename = filename.replace(/[^a-zA-Z0-9._-]/g, '_');
        if (!filename.endsWith('.js')) filename += '.js';

        const destPath = path.join(JS_DIR, filename);
        if (!fs.existsSync(destPath)) {
          await downloadFile(url, destPath);
          scoutData.js_files.push(`assets/js-sources/${filename}`);
          console.log(`  Downloaded: ${filename}`);
        } else {
          scoutData.js_files.push(`assets/js-sources/${filename}`);
          console.log(`  Already exists: ${filename}`);
        }
      } catch (e) {
        console.log(`  Failed: ${url.substring(0, 80)}: ${e.message}`);
      }
    }

    // ============================================================
    // FASE 4: NAVIGAZIONE SISTEMATICA
    // ============================================================
    console.log('\n========== FASE 4: NAVIGAZIONE SISTEMATICA ==========');

    // First, analyze the navigation structure from the current page (dashboard)
    const navStructure = await page.evaluate(() => {
      const result = {
        sidebarLinks: [],
        topNavLinks: [],
        allInternalLinks: [],
        menuItems: []
      };

      // Sidebar navigation
      const sidebar = document.querySelector('[class*="sidebar"], [class*="Sidebar"], aside, nav');
      if (sidebar) {
        sidebar.querySelectorAll('a[href]').forEach(a => {
          result.sidebarLinks.push({
            text: a.textContent?.trim(),
            href: a.getAttribute('href'),
            fullHref: a.href,
            ariaLabel: a.getAttribute('aria-label'),
            className: a.className?.substring(0, 100)
          });
        });
      }

      // All internal links
      document.querySelectorAll('a[href]').forEach(a => {
        const href = a.getAttribute('href');
        if (href && (href.startsWith('/') || href.includes('app.sibill.com')) && !href.includes('logout') && !href.includes('login')) {
          result.allInternalLinks.push({
            text: a.textContent?.trim(),
            href: href,
            fullHref: a.href,
            inSidebar: !!a.closest('[class*="sidebar"], [class*="Sidebar"], aside, nav'),
            className: a.className?.substring(0, 100)
          });
        }
      });

      // Clickable items that might be navigation
      document.querySelectorAll('[role="menuitem"], [role="tab"], [class*="nav-item"], [class*="NavItem"], [class*="menu-item"], [class*="MenuItem"]').forEach(el => {
        result.menuItems.push({
          text: el.textContent?.trim(),
          tag: el.tagName,
          href: el.getAttribute('href'),
          className: el.className?.toString()?.substring(0, 100),
          ariaLabel: el.getAttribute('aria-label'),
          dataTestId: el.getAttribute('data-testid')
        });
      });

      return result;
    });

    console.log(`Sidebar links: ${navStructure.sidebarLinks.length}`);
    console.log(`Internal links: ${navStructure.allInternalLinks.length}`);
    console.log(`Menu items: ${navStructure.menuItems.length}`);

    // Print all found navigation items
    console.log('\nSidebar links:');
    navStructure.sidebarLinks.forEach(l => console.log(`  [${l.text}] -> ${l.href}`));
    console.log('\nInternal links:');
    navStructure.allInternalLinks.forEach(l => console.log(`  [${l.text}] -> ${l.href}${l.inSidebar ? ' (sidebar)' : ''}`));
    console.log('\nMenu items:');
    navStructure.menuItems.forEach(l => console.log(`  [${l.text}] -> ${l.href || '(click)'}`));

    fs.writeFileSync(path.join(TMP_DIR, 'nav-structure.json'), JSON.stringify(navStructure, null, 2));

    // Collect unique URLs to visit
    const urlsToVisit = new Map(); // href -> text
    for (const link of [...navStructure.sidebarLinks, ...navStructure.allInternalLinks]) {
      let href = link.href;
      if (!href) continue;
      // Normalize
      if (href.startsWith('https://app.sibill.com')) href = new URL(href).pathname;
      if (href === '/' || href.includes('login') || href.includes('logout') || href.includes('reset-password')) continue;
      if (!urlsToVisit.has(href)) {
        urlsToVisit.set(href, link.text || href);
      }
    }

    // Add common sections that might be dynamic
    const commonSections = [
      '/dashboard', '/tesoreria', '/cash-flow', '/cashflow', '/previsioni',
      '/conti', '/conti-bancari', '/bank-accounts', '/accounts',
      '/movimenti', '/transactions', '/movements',
      '/fatture', '/invoices', '/fatturazione',
      '/scadenzario', '/scadenze', '/deadlines',
      '/riconciliazione', '/reconciliation',
      '/pagamenti', '/payments',
      '/carte', '/cards',
      '/report', '/reports', '/analytics',
      '/impostazioni', '/settings', '/configurazione',
      '/connessioni', '/connections', '/connessioni-bancarie',
      '/clienti', '/fornitori', '/contatti',
      '/categorie', '/tags'
    ];

    for (const sec of commonSections) {
      if (!urlsToVisit.has(sec)) urlsToVisit.set(sec, sec);
    }

    console.log(`\nURLs to visit: ${urlsToVisit.size}`);

    let screenshotCounter = 2;
    const visitedPages = [];
    const failedUrls = [];

    // Visit dashboard first
    {
      const dashInfo = await page.evaluate(() => {
        const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent?.trim()).filter(Boolean);
        const tables = document.querySelectorAll('table, [class*="table"], [role="grid"], [class*="Table"]').length;
        const forms = document.querySelectorAll('form').length;
        const charts = document.querySelectorAll('canvas, svg[class*="chart"], [class*="Chart"], [class*="recharts"]').length;
        const buttons = Array.from(document.querySelectorAll('button:not([class*="intercom"])')).map(b => b.textContent?.trim()).filter(Boolean);
        return { headings, tables, forms, charts, buttons: buttons.slice(0, 20) };
      });

      visitedPages.push({
        id: 'dashboard',
        url: new URL(page.url()).pathname,
        title: await page.title(),
        description: dashInfo.headings.join(' > ') || 'Dashboard principale',
        screenshot: 'assets/screenshots/01-dashboard.png',
        components: [
          dashInfo.tables > 0 ? `tabelle(${dashInfo.tables})` : null,
          dashInfo.forms > 0 ? `form(${dashInfo.forms})` : null,
          dashInfo.charts > 0 ? `grafici(${dashInfo.charts})` : null
        ].filter(Boolean),
        actions: dashInfo.buttons.slice(0, 10),
        headings: dashInfo.headings
      });
    }

    // Navigate each section
    for (const [href, label] of urlsToVisit) {
      const fullUrl = href.startsWith('http') ? href : `https://app.sibill.com${href}`;
      try {
        console.log(`\nNavigating: [${label}] -> ${href}`);
        await page.goto(fullUrl, { waitUntil: 'load', timeout: 30000 });
        await page.waitForTimeout(3000);

        const currentUrl = page.url();
        const currentPath = new URL(currentUrl).pathname;

        // Skip if redirected to login/logout
        if (currentPath.includes('login') || currentPath.includes('logout')) {
          console.log(`  REDIRECT to ${currentPath} - skipping`);

          // Re-login if needed
          if (currentPath.includes('login')) {
            console.log('  Re-authenticating...');
            await page.fill('input[name="username"]', email);
            await page.fill('input[type="password"]', password);
            await Promise.all([
              page.waitForNavigation({ timeout: 15000 }).catch(() => null),
              page.click('button[type="submit"]')
            ]);
            await page.waitForTimeout(3000);
          }
          failedUrls.push({ href, label, reason: `redirected to ${currentPath}` });
          continue;
        }

        const pageTitle = await page.title();

        // Analyze page content
        const pageInfo = await page.evaluate(() => {
          const headings = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.textContent?.trim()).filter(Boolean);
          const tables = document.querySelectorAll('table, [class*="table"], [role="grid"], [class*="Table"]').length;
          const forms = document.querySelectorAll('form').length;
          const charts = document.querySelectorAll('canvas, svg[class*="chart"], [class*="Chart"], [class*="recharts"]').length;
          const buttons = Array.from(document.querySelectorAll('button:not([class*="intercom"])')).map(b => b.textContent?.trim()).filter(t => t && t.length < 50);
          const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea')).map(i => ({
            type: i.type || i.tagName.toLowerCase(),
            name: i.name,
            placeholder: i.placeholder,
            id: i.id
          }));

          // Check for subnavigation / tabs
          const tabs = Array.from(document.querySelectorAll('[role="tab"], [class*="tab"], [class*="Tab"]')).map(t => t.textContent?.trim()).filter(Boolean);

          // Detect main visible content area text
          const mainContent = document.querySelector('main, [class*="content"], [class*="Content"]');
          const visibleText = mainContent?.textContent?.substring(0, 500)?.trim() || '';

          return { headings, tables, forms, charts, buttons: buttons.slice(0, 20), inputs: inputs.slice(0, 30), tabs, visibleText };
        });

        // Screenshot
        const pathSlug = currentPath.replace(/\//g, '-').replace(/^-/, '').replace(/-$/, '') || 'root';
        const screenshotName = `${String(screenshotCounter).padStart(2, '0')}-${pathSlug.substring(0, 50)}.png`;
        await page.screenshot({ path: path.join(SCREENSHOTS_DIR, screenshotName), fullPage: true });

        const pageData = {
          id: pathSlug,
          url: currentPath,
          title: pageTitle,
          description: pageInfo.headings.join(' > ') || label,
          screenshot: `assets/screenshots/${screenshotName}`,
          components: [
            pageInfo.tables > 0 ? `tabelle(${pageInfo.tables})` : null,
            pageInfo.forms > 0 ? `form(${pageInfo.forms})` : null,
            pageInfo.charts > 0 ? `grafici(${pageInfo.charts})` : null,
            pageInfo.inputs.length > 0 ? `input(${pageInfo.inputs.length})` : null,
            pageInfo.tabs.length > 0 ? `tabs(${pageInfo.tabs.join(', ')})` : null
          ].filter(Boolean),
          actions: pageInfo.buttons.slice(0, 10),
          headings: pageInfo.headings,
          tabs: pageInfo.tabs,
          inputs: pageInfo.inputs
        };

        visitedPages.push(pageData);
        console.log(`  Title: "${pageTitle}", Path: ${currentPath}`);
        console.log(`  Headings: ${pageInfo.headings.join(', ')}`);
        console.log(`  Components: tables=${pageInfo.tables}, forms=${pageInfo.forms}, charts=${pageInfo.charts}, inputs=${pageInfo.inputs.length}`);
        if (pageInfo.tabs.length) console.log(`  Tabs: ${pageInfo.tabs.join(', ')}`);

        // Also discover new links from this page
        const newLinks = await page.evaluate(() => {
          return Array.from(document.querySelectorAll('a[href]'))
            .filter(a => {
              const h = a.getAttribute('href');
              return h && h.startsWith('/') && !h.includes('login') && !h.includes('logout');
            })
            .map(a => ({ text: a.textContent?.trim(), href: a.getAttribute('href') }));
        });

        for (const nl of newLinks) {
          if (nl.href && !urlsToVisit.has(nl.href) && !visitedPages.find(p => p.url === nl.href)) {
            urlsToVisit.set(nl.href, nl.text || nl.href);
            console.log(`  New link discovered: [${nl.text}] -> ${nl.href}`);
          }
        }

        screenshotCounter++;
      } catch (e) {
        console.log(`  ERROR: ${e.message}`);
        failedUrls.push({ href, label, reason: e.message });
      }
    }

    console.log(`\nVisited ${visitedPages.length} pages, ${failedUrls.length} failures`);

    // ============================================================
    // FASE 5: NETWORK CAPTURE
    // ============================================================
    console.log('\n========== FASE 5: NETWORK CAPTURE ==========');

    const apiRequests = allNetworkRequests.filter(r =>
      (r.resourceType === 'xhr' || r.resourceType === 'fetch') &&
      (r.url.includes('api.sibill.com') || r.url.includes('/api/'))
    );

    console.log(`Total network requests: ${allNetworkRequests.length}`);
    console.log(`Sibill API requests: ${apiRequests.length}`);

    // Save network data
    fs.writeFileSync(path.join(HAR_DIR, 'session-complete.txt'), JSON.stringify(allNetworkRequests, null, 2));
    fs.writeFileSync(path.join(HAR_DIR, 'api-requests.json'), JSON.stringify(apiRequests, null, 2));

    // Extract unique API endpoints
    const apiEndpoints = new Map();
    for (const req of apiRequests) {
      try {
        const url = new URL(req.url);
        // Remove query params for endpoint grouping
        const endpoint = `${req.method} ${url.pathname}`;
        if (!apiEndpoints.has(endpoint)) {
          apiEndpoints.set(endpoint, {
            method: req.method,
            path: url.pathname,
            queryParams: url.search ? url.search : undefined,
            status: req.status,
            responseContentType: req.responseHeaders?.['content-type'],
            count: 1
          });
        } else {
          apiEndpoints.get(endpoint).count++;
        }
      } catch (e) {}
    }

    console.log(`\nUnique API endpoints: ${apiEndpoints.size}`);
    const sortedEndpoints = Array.from(apiEndpoints.entries()).sort();
    for (const [ep, info] of sortedEndpoints) {
      console.log(`  ${ep} [${info.status || '?'}] x${info.count}`);
    }

    scoutData.auth_info.endpoints = Object.fromEntries(apiEndpoints);

    // Identify libraries from network requests
    const libs = new Set();
    for (const req of allNetworkRequests) {
      if (req.url.includes('intercom')) libs.add('Intercom');
      if (req.url.includes('segment') || req.url.includes('tracking.sibill.com')) libs.add('Segment Analytics');
      if (req.url.includes('hubspot') || req.url.includes('hs-')) libs.add('HubSpot');
      if (req.url.includes('hotjar')) libs.add('Hotjar');
      if (req.url.includes('sentry') || req.url.includes('exceptions.sibill.com')) libs.add('Sentry');
      if (req.url.includes('customer.io')) libs.add('Customer.io');
      if (req.url.includes('gist.build')) libs.add('Gist');
      if (req.url.includes('satismeter')) libs.add('SatisMeter');
    }
    scoutData.tech_stack.other_libs = Array.from(libs);
    scoutData.tech_stack.ui_library = 'Material UI (MUI)';

    // ============================================================
    // COMPILE & SAVE OUTPUT
    // ============================================================
    console.log('\n========== SAVING OUTPUT ==========');

    scoutData.pages = visitedPages;
    scoutData.network_summary = {
      total_requests: allNetworkRequests.length,
      api_requests: apiRequests.length,
      unique_endpoints: apiEndpoints.size,
      endpoints: Object.fromEntries(apiEndpoints)
    };

    // Save scout-complete.json
    fs.writeFileSync(path.join(TMP_DIR, 'scout-complete.json'), JSON.stringify(scoutData, null, 2));
    console.log('Saved .tmp/scout-complete.json');

    // Save failed URLs
    if (failedUrls.length > 0) {
      fs.writeFileSync(path.join(TMP_DIR, 'failed-urls.json'), JSON.stringify(failedUrls, null, 2));
      console.log('Saved .tmp/failed-urls.json');
    }

    // Final summary
    console.log('\n========== SUMMARY ==========');
    console.log(`Framework: ${scoutData.tech_stack.framework}`);
    console.log(`UI Library: ${scoutData.tech_stack.ui_library}`);
    console.log(`Auth: ${scoutData.auth_info.type} (${scoutData.auth_info.token_location})`);
    console.log(`Pages visited: ${visitedPages.length}`);
    console.log(`JS files: ${scoutData.js_files.length}`);
    console.log(`API endpoints: ${apiEndpoints.size}`);
    console.log(`External services: ${Array.from(libs).join(', ')}`);
    console.log(`Failed URLs: ${failedUrls.length}`);

    console.log('\nPages found:');
    for (const p of visitedPages) {
      console.log(`  ${p.url} - "${p.title}" - ${p.components.join(', ')}`);
    }

  } catch (error) {
    console.error('FATAL ERROR:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
    console.log('\n=== SCOUT FULL RECON COMPLETE ===');
  }
})();
