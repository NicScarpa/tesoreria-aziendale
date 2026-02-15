/**
 * Capture Full Site - Sibill Offline Replay
 *
 * Cattura completa di TUTTE le pagine di Sibill con HAR recording nativo.
 * Naviga tutte le 23 sezioni, interagisce con elementi UI, cattura tutte le API.
 *
 * Uso: node capture/capture-site.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_DIR = '/Users/nicolascarpa/Desktop/Progetti/sibill-re';
const SCREENS_DIR = path.join(BASE_DIR, 'screens/offline');
const CAPTURED_DIR = path.join(SCREENS_DIR, 'captured');
const SCREENSHOTS_DIR = path.join(CAPTURED_DIR, 'screenshots');

// Leggi credenziali
const envContent = fs.readFileSync(path.join(BASE_DIR, 'credenziali.env'), 'utf8');
const cLines = envContent.trim().split('\n');
let email = '', password = '';
for (const line of cLines) {
  if (line.startsWith('user:')) email = line.split(':').slice(1).join(':').trim();
  if (line.startsWith('password:')) password = line.split(':').slice(1).join(':').trim();
}

if (!email || !password) {
  console.error('Credenziali non trovate in credenziali.env');
  process.exit(1);
}

// Tutte le pagine da catturare
const PAGES = [
  { path: '/cashflow', label: 'Cashflow', hasSpecificInteractions: true },
  { path: '/cashflow/categories', label: 'Categorie Cashflow' },
  { path: '/transactions/movements', label: 'Movimenti Bancari' },
  { path: '/transactions/payments', label: 'Pagamenti' },
  { path: '/transactions/rules', label: 'Regole Categorizzazione' },
  { path: '/reconciliations', label: 'Riconciliazioni' },
  { path: '/accounts', label: 'Conti Bancari' },
  { path: '/outstanding', label: 'Scadenzario' },
  { path: '/outstanding/recurrences/received', label: 'Ricorrenze Ricevute' },
  { path: '/outstanding/recurrences/issued', label: 'Ricorrenze Emesse' },
  { path: '/outstanding/rules', label: 'Regole Scadenzario' },
  { path: '/invoices/dashboard', label: 'Dashboard Fatture' },
  { path: '/invoices/issued', label: 'Fatture Emesse' },
  { path: '/invoices/received', label: 'Fatture Ricevute' },
  { path: '/invoices/bills', label: 'Corrispettivi' },
  { path: '/counterparts', label: 'Controparti' },
  { path: '/invoices/profile/company-data', label: 'Profilo Fatturazione' },
  { path: '/invoices/profile/defaults', label: 'Default Fatturazione' },
  { path: '/invoices/info', label: 'Crea Fattura' },
  { path: '/invoices/import', label: 'Import Fatture' },
  { path: '/f24', label: 'F24' },
  { path: '/settings/team', label: 'Team' },
  { path: '/referral', label: 'Referral' },
];

fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

const HAR_PATH = path.join(CAPTURED_DIR, 'har-complete.har');

// ======================================================================
// INTERAZIONI GENERICHE — funzionano su qualsiasi pagina
// ======================================================================

async function genericInteractions(page, pageLabel) {
  // 1. Espandi righe espandibili (tabelle con drill-down)
  try {
    const expandIcons = await page.$$('[aria-expanded="false"]');
    const toExpand = Math.min(expandIcons.length, 3);
    for (let i = 0; i < toExpand; i++) {
      try {
        await expandIcons[i].click();
        await page.waitForTimeout(800);
      } catch (e) {}
    }
    if (toExpand > 0) console.log(`    Espanse ${toExpand} righe`);
  } catch (e) {}

  // 2. Clicca la prima cella cliccabile (aside panel / dettaglio)
  try {
    const clickableCells = await page.$$('td[role="button"], [class*="cell"][class*="click"], [class*="Cell"][class*="click"]');
    if (clickableCells.length > 0) {
      await clickableCells[0].click();
      await page.waitForTimeout(1500);
      console.log('    Aperto dettaglio/aside');
      // Chiudi con Escape
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    }
  } catch (e) {}

  // 3. Cerca tab e clicca per triggerare API diverse
  try {
    const tabs = await page.$$('[role="tab"]');
    if (tabs.length > 1) {
      for (let i = 1; i < Math.min(tabs.length, 4); i++) {
        try {
          await tabs[i].click();
          await page.waitForTimeout(1500);
        } catch (e) {}
      }
      // Torna alla prima tab
      try { await tabs[0].click(); await page.waitForTimeout(1000); } catch (e) {}
      console.log(`    Navigati ${Math.min(tabs.length, 4)} tab`);
    }
  } catch (e) {}

  // 4. Scroll fino in fondo per triggerare lazy loading / infinite scroll
  try {
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    await page.waitForTimeout(1500);
    // Torna su
    await page.evaluate(() => { window.scrollTo(0, 0); });
    await page.waitForTimeout(500);
  } catch (e) {}
}

// ======================================================================
// INTERAZIONI SPECIFICHE CASHFLOW
// ======================================================================

async function cashflowInteractions(page) {
  console.log('    >> Interazioni specifiche cashflow');

  // Toggle checkbox/switch (budget, overdue, pastdue)
  const checkboxes = await page.$$('input[type="checkbox"], [role="switch"], [role="checkbox"]');
  for (let i = 0; i < checkboxes.length; i++) {
    try {
      const isChecked = await checkboxes[i].evaluate(el =>
        el.checked || el.getAttribute('aria-checked') === 'true'
      );
      if (!isChecked) {
        await checkboxes[i].click();
        await page.waitForTimeout(2000);
      }
    } catch (e) {}
  }
  if (checkboxes.length > 0) console.log(`    Toggle ${checkboxes.length} checkbox`);

  // Click barre grafico
  const bars = await page.$$('.recharts-bar-rectangle rect');
  for (let i = 0; i < Math.min(bars.length, 10); i++) {
    try {
      const isVisible = await bars[i].isVisible().catch(() => false);
      if (isVisible) {
        await bars[i].click({ force: true, timeout: 5000 });
        await page.waitForTimeout(1500);
        break;
      }
    } catch (e) {}
  }
}

// ======================================================================
// MAIN
// ======================================================================

(async () => {
  console.log('=== FULL SITE CAPTURE START ===');
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log(`Pagine da catturare: ${PAGES.length}`);
  console.log(`Output: ${CAPTURED_DIR}/\n`);

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    recordHar: {
      path: HAR_PATH,
      content: 'embed',
      urlFilter: /.*$/,
      mode: 'full'
    }
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
  });

  const page = await context.newPage();

  let apiCount = 0;
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('api.sibill.com') || url.includes('/api/')) {
      apiCount++;
    }
  });

  try {
    // ================================================================
    // FASE A: LOGIN
    // ================================================================
    console.log('--- FASE A: LOGIN ---');
    await page.goto('https://app.sibill.com/login', { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(3000);

    await page.waitForSelector('input[name="username"]', { timeout: 15000 });
    await page.fill('input[name="username"]', email);
    await page.waitForTimeout(300);
    await page.fill('input[type="password"]', password);
    await page.waitForTimeout(300);

    await Promise.all([
      page.waitForNavigation({ timeout: 30000 }).catch(() => null),
      page.click('button[type="submit"]')
    ]);
    await page.waitForTimeout(5000);

    if (page.url().includes('login')) {
      throw new Error('Login fallito — controlla le credenziali');
    }
    console.log(`Login riuscito! (${page.url()})\n`);

    // ================================================================
    // FASE B: NAVIGA TUTTE LE PAGINE
    // ================================================================
    console.log('--- FASE B: NAVIGAZIONE TUTTE LE PAGINE ---\n');

    const results = [];

    for (let i = 0; i < PAGES.length; i++) {
      const pg = PAGES[i];
      const num = String(i + 1).padStart(2, '0');
      const slug = pg.path.replace(/\//g, '-').replace(/^-/, '');

      console.log(`[${num}/${PAGES.length}] ${pg.label} (${pg.path})`);

      try {
        await page.goto(`https://app.sibill.com${pg.path}`, {
          waitUntil: 'load',
          timeout: 30000
        });
        // Attendi caricamento lazy (API, chunks JS)
        await page.waitForTimeout(5000);

        const currentUrl = page.url();
        const apisBefore = apiCount;

        // Screenshot
        const screenshotPath = path.join(SCREENSHOTS_DIR, `${num}-${slug}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });

        // Interazioni generiche
        await genericInteractions(page, pg.label);

        // Interazioni specifiche cashflow
        if (pg.hasSpecificInteractions) {
          await cashflowInteractions(page);
        }

        const apisTriggered = apiCount - apisBefore;
        console.log(`    OK — ${apisTriggered} API catturate\n`);

        results.push({
          path: pg.path,
          label: pg.label,
          actualUrl: currentUrl,
          screenshot: `${num}-${slug}.png`,
          apisTriggered
        });

      } catch (e) {
        console.log(`    ERRORE: ${e.message}\n`);
        results.push({
          path: pg.path,
          label: pg.label,
          error: e.message
        });
      }
    }

    // ================================================================
    // FASE C: CATTURA HTML E STORAGE
    // ================================================================
    console.log('--- FASE C: CATTURA HTML E STORAGE ---');

    // Torna alla pagina principale per catturare l'HTML completo
    await page.goto('https://app.sibill.com/cashflow', { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(5000);

    const htmlContent = await page.content();
    fs.writeFileSync(path.join(CAPTURED_DIR, 'index.html'), htmlContent);
    console.log(`index.html salvato (${(htmlContent.length / 1024).toFixed(0)} KB)`);

    const localStorageData = await page.evaluate(() => {
      const data = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        data[key] = localStorage.getItem(key);
      }
      return data;
    });
    fs.writeFileSync(path.join(CAPTURED_DIR, 'localStorage.json'), JSON.stringify(localStorageData, null, 2));
    console.log(`localStorage salvato (${Object.keys(localStorageData).length} chiavi)`);

    const sessionStorageData = await page.evaluate(() => {
      const data = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        data[key] = sessionStorage.getItem(key);
      }
      return data;
    });
    fs.writeFileSync(path.join(CAPTURED_DIR, 'sessionStorage.json'), JSON.stringify(sessionStorageData, null, 2));

    // Salva report navigazione
    fs.writeFileSync(path.join(CAPTURED_DIR, 'capture-report.json'), JSON.stringify({
      timestamp: new Date().toISOString(),
      totalPages: PAGES.length,
      successful: results.filter(r => !r.error).length,
      failed: results.filter(r => r.error).length,
      totalApis: apiCount,
      pages: results
    }, null, 2));

    // ================================================================
    // FASE D: CHIUSURA
    // ================================================================
    console.log('\n--- FASE D: SALVATAGGIO HAR ---');
    console.log(`API totali intercettate: ${apiCount}`);

    await context.close();
    console.log('Context chiuso — HAR scritto su disco');

    if (fs.existsSync(HAR_PATH)) {
      const harSize = fs.statSync(HAR_PATH).size;
      console.log(`HAR: ${(harSize / 1024 / 1024).toFixed(1)} MB`);

      try {
        const harContent = JSON.parse(fs.readFileSync(HAR_PATH, 'utf8'));
        const entries = harContent.log?.entries?.length || 0;
        const withBody = harContent.log?.entries?.filter(e =>
          e.response?.content?.text || e.response?.content?.size > 0
        ).length || 0;
        console.log(`HAR entries: ${entries} totali, ${withBody} con body`);
      } catch (e) {}
    }

    await browser.close();

    // Riepilogo
    console.log('\n=== RIEPILOGO ===');
    console.log(`Pagine navigate: ${results.filter(r => !r.error).length}/${PAGES.length}`);
    console.log(`API catturate: ${apiCount}`);
    const failedPages = results.filter(r => r.error);
    if (failedPages.length > 0) {
      console.log('Pagine fallite:');
      failedPages.forEach(p => console.log(`  - ${p.path}: ${p.error}`));
    }
    console.log(`\nProssimo step: python3 build/build-offline.py`);

  } catch (error) {
    console.error(`\nFATAL ERROR: ${error.message}`);
    console.error(error.stack);
    try { await context.close(); await browser.close(); } catch (e) {}
    process.exit(1);
  }
})();
