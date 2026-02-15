/**
 * Capture Cashflow Page - Sibill Offline Replay
 *
 * Cattura completa della pagina /cashflow con HAR recording nativo di Playwright.
 * Output: captured/har-complete.har + index.html + localStorage.json
 *
 * Uso: node capture/capture-cashflow.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_DIR = '/Users/nicolascarpa/Desktop/Progetti/sibill-re';
const SCREENS_DIR = path.join(BASE_DIR, 'screens/cashflow');
const CAPTURED_DIR = path.join(SCREENS_DIR, 'captured');

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

// Assicura che la directory captured/ esista
fs.mkdirSync(CAPTURED_DIR, { recursive: true });

const HAR_PATH = path.join(CAPTURED_DIR, 'har-complete.har');

(async () => {
  console.log('=== CASHFLOW CAPTURE START ===');
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log(`Output: ${CAPTURED_DIR}/`);

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
  });

  // Context con HAR recording nativo — cattura TUTTI i response body
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    recordHar: {
      path: HAR_PATH,
      content: 'embed',    // Embed base64 body in HAR (alternativa: 'attach' per file separati)
      urlFilter: /.*$/,     // Cattura TUTTO
      mode: 'full'
    }
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
  });

  const page = await context.newPage();

  // Contatore API intercettate (per logging)
  let apiCount = 0;
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('api.sibill.com') || url.includes('/api/')) {
      apiCount++;
      const urlObj = new URL(url);
      console.log(`  [API ${apiCount}] ${response.status()} ${urlObj.pathname}${urlObj.search ? ' (+ params)' : ''}`);
    }
  });

  try {
    // ================================================================
    // FASE A: LOGIN
    // ================================================================
    console.log('\n--- FASE A: LOGIN ---');
    await page.goto('https://app.sibill.com/login', { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(3000);

    await page.waitForSelector('input[name="username"]', { timeout: 15000 });
    console.log('Form login trovato');

    await page.fill('input[name="username"]', email);
    await page.waitForTimeout(300);
    await page.fill('input[type="password"]', password);
    await page.waitForTimeout(300);

    await Promise.all([
      page.waitForNavigation({ timeout: 30000 }).catch(() => null),
      page.click('button[type="submit"]')
    ]);
    await page.waitForTimeout(5000);

    const postLoginUrl = page.url();
    console.log(`Post-login URL: ${postLoginUrl}`);

    if (postLoginUrl.includes('login')) {
      throw new Error('Login fallito — controlla le credenziali');
    }
    console.log('Login riuscito!');

    // ================================================================
    // FASE B: NAVIGA A /CASHFLOW E INTERAZIONI
    // ================================================================
    console.log('\n--- FASE B: NAVIGAZIONE CASHFLOW ---');

    await page.goto('https://app.sibill.com/cashflow', { waitUntil: 'load', timeout: 60000 });
    // Attendi extra per il caricamento lazy (API, chunks JS)
    await page.waitForTimeout(8000);
    console.log(`Pagina cashflow caricata: ${page.url()}`);

    // Attendi che il grafico sia renderizzato
    try {
      await page.waitForSelector('[class*="recharts"], svg[class*="chart"], [class*="Chart"]', { timeout: 15000 });
      console.log('Grafico Recharts trovato');
    } catch (e) {
      console.log('WARN: Grafico non trovato, provo ad attendere...');
      await page.waitForTimeout(5000);
    }

    // Screenshot stato iniziale
    await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-initial.png'), fullPage: true });
    console.log('Screenshot iniziale salvato');

    // --- Interazione 1: Toggle filtri di visualizzazione ---
    console.log('\n  >> Interazione: Toggle filtri');

    // Cerca i toggle/checkbox per budget, overdue, pastdue
    const toggleLabels = ['Budget', 'Previsioni', 'Scadut', 'Fuori termine', 'Overdue', 'Past'];

    for (const label of toggleLabels) {
      try {
        // Cerca bottoni o checkbox con testo che contiene il label
        const toggle = await page.$(`button:has-text("${label}"), label:has-text("${label}"), [aria-label*="${label}" i]`);
        if (toggle) {
          console.log(`  Toggle trovato: "${label}" — click`);
          await toggle.click();
          await page.waitForTimeout(2000);
          // Aspetta che le API rispondano
          await page.waitForLoadState('networkidle').catch(() => {});
          await page.waitForTimeout(1000);
        }
      } catch (e) {
        console.log(`  Toggle "${label}" non trovato o errore: ${e.message}`);
      }
    }

    // --- Interazione 2: Prova a trovare e cliccare le checkbox di visualizzazione dal DOM ---
    console.log('\n  >> Interazione: Checkbox visualizzazione dal DOM');
    const checkboxInfo = await page.evaluate(() => {
      // Cerca checkbox, switch, toggle nell'area di navigazione cashflow
      const elements = document.querySelectorAll('input[type="checkbox"], [role="switch"], [role="checkbox"]');
      return Array.from(elements).map(el => ({
        id: el.id,
        name: el.name,
        ariaLabel: el.getAttribute('aria-label'),
        checked: el.checked || el.getAttribute('aria-checked') === 'true',
        parentText: el.parentElement?.textContent?.trim().substring(0, 50)
      }));
    });
    console.log(`  Checkbox trovati: ${checkboxInfo.length}`);
    for (const cb of checkboxInfo) {
      console.log(`    [${cb.checked ? 'X' : ' '}] id=${cb.id}, name=${cb.name}, label="${cb.ariaLabel || cb.parentText}"`);
    }

    // Click su ogni checkbox non ancora attivo per triggerare nuove combinazioni
    const checkboxes = await page.$$('input[type="checkbox"], [role="switch"], [role="checkbox"]');
    for (let i = 0; i < checkboxes.length; i++) {
      try {
        const isChecked = await checkboxes[i].evaluate(el =>
          el.checked || el.getAttribute('aria-checked') === 'true'
        );
        if (!isChecked) {
          await checkboxes[i].click();
          console.log(`  Checkbox ${i} attivato`);
          await page.waitForTimeout(2000);
          await page.waitForLoadState('networkidle').catch(() => {});
        }
      } catch (e) {
        // Ignora checkbox non cliccabili
      }
    }

    // Screenshot con tutti i filtri attivi
    await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-all-filters.png'), fullPage: true });

    // --- Interazione 3: Selettore periodo ---
    console.log('\n  >> Interazione: Selettore periodo');

    // Cerca il selettore periodo (dropdown, select, o bottoni con testo tipo "12 mesi", "2025")
    const periodSelectors = await page.$$('[class*="period"], [class*="Period"], [class*="time"], [class*="Time"], [class*="range"], [class*="Range"], select, [role="combobox"], [role="listbox"]');
    console.log(`  Selettori periodo candidati: ${periodSelectors.length}`);

    // Prova a trovare e cliccare il dropdown del periodo
    try {
      // Cerca bottoni con testo di periodo
      const periodButton = await page.$('button:has-text("mesi"), button:has-text("Mesi"), button:has-text("Anno"), button:has-text("Periodo"), [data-testid*="period"], [data-testid*="range"]');
      if (periodButton) {
        console.log('  Dropdown periodo trovato — click');
        await periodButton.click();
        await page.waitForTimeout(1000);

        // Screenshot del menu aperto
        await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-period-dropdown.png'), fullPage: true });

        // Cerca le opzioni nel dropdown
        const options = await page.$$('[role="option"], [role="menuitem"], li[class*="option"], li[class*="Option"], [class*="menu-item"], [class*="MenuItem"]');
        console.log(`  Opzioni periodo trovate: ${options.length}`);

        // Click sulla prima opzione diversa (es. "12 mesi" o anno diverso)
        if (options.length > 1) {
          const optionTexts = await Promise.all(options.map(o => o.textContent()));
          console.log(`  Opzioni: ${optionTexts.join(', ')}`);

          // Click su un'opzione diversa dalla corrente
          await options[1].click();
          console.log(`  Selezionata opzione: "${optionTexts[1]}"`);
          await page.waitForTimeout(3000);
          await page.waitForLoadState('networkidle').catch(() => {});

          await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-period-changed.png'), fullPage: true });

          // Riapri e seleziona un'altra opzione
          if (options.length > 2) {
            await periodButton.click();
            await page.waitForTimeout(1000);
            const options2 = await page.$$('[role="option"], [role="menuitem"], li[class*="option"], li[class*="Option"]');
            if (options2.length > 2) {
              await options2[2].click();
              console.log(`  Selezionata terza opzione`);
              await page.waitForTimeout(3000);
              await page.waitForLoadState('networkidle').catch(() => {});
            }
          }
        }
      } else {
        console.log('  Dropdown periodo non trovato con selettore diretto, provo ricerca generica...');
        // Fallback: cerca qualsiasi selettore/dropdown nell'area superiore della pagina
        const topButtons = await page.$$('header button, [class*="toolbar"] button, [class*="Toolbar"] button, [class*="navigation"] button, [class*="Navigation"] button');
        console.log(`  Bottoni toolbar trovati: ${topButtons.length}`);
        for (const btn of topButtons.slice(0, 5)) {
          const text = await btn.textContent();
          console.log(`    Button: "${text.trim()}"`);
        }
      }
    } catch (e) {
      console.log(`  Errore selettore periodo: ${e.message}`);
    }

    // --- Interazione 4: Espandi categorie nella tabella ---
    console.log('\n  >> Interazione: Espansione categorie tabella');

    // Cerca righe espandibili nella tabella
    const expandableRows = await page.$$('[class*="expand"], [aria-expanded], [class*="Expand"], tr[class*="parent"], [class*="row"][class*="click"], [class*="Row"][class*="click"]');
    console.log(`  Righe espandibili candidate: ${expandableRows.length}`);

    // Prova a espandere le prime righe
    const rowsToExpand = await page.$$('[aria-expanded="false"], [class*="expand"][class*="icon"], [class*="chevron"], [class*="Chevron"], [class*="arrow"][class*="right"]');
    console.log(`  Righe con expand icon: ${rowsToExpand.length}`);

    for (let i = 0; i < Math.min(rowsToExpand.length, 5); i++) {
      try {
        await rowsToExpand[i].click();
        console.log(`  Riga ${i} espansa`);
        await page.waitForTimeout(1000);
      } catch (e) {
        // Ignora errori su righe non cliccabili
      }
    }

    await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-expanded.png'), fullPage: true });

    // --- Interazione 5: Click su celle tabella per aprire aside panel ---
    console.log('\n  >> Interazione: Click celle tabella (aside panel)');

    // Cerca celle cliccabili nella tabella (tipicamente celle con importi)
    const tableCells = await page.$$('td[class*="click"], td[role="button"], [class*="cell"][class*="click"], [class*="Cell"][class*="click"], td[class*="amount"], td[class*="Amount"]');
    console.log(`  Celle cliccabili: ${tableCells.length}`);

    if (tableCells.length > 0) {
      try {
        await tableCells[0].click();
        console.log('  Click sulla prima cella — attendendo aside panel...');
        await page.waitForTimeout(2000);
        await page.waitForLoadState('networkidle').catch(() => {});
        await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-aside-panel.png'), fullPage: true });

        // Cerca tab nell'aside panel (Movimenti, Scadenze, Scaduti)
        const asideTabs = await page.$$('[class*="aside"] [role="tab"], [class*="drawer"] [role="tab"], [class*="panel"] [role="tab"], [class*="split"] [role="tab"]');
        console.log(`  Tab nell'aside: ${asideTabs.length}`);
        for (const tab of asideTabs) {
          try {
            await tab.click();
            await page.waitForTimeout(1500);
            await page.waitForLoadState('networkidle').catch(() => {});
          } catch (e) {}
        }
      } catch (e) {
        console.log(`  Errore click cella: ${e.message}`);
      }
    }

    // --- Interazione 6: Click su barre del grafico ---
    console.log('\n  >> Interazione: Click barre grafico');

    // Recharts renderizza rect elements dentro svg — click con force per elementi SVG
    const bars = await page.$$('.recharts-bar-rectangle rect');
    console.log(`  Barre grafico trovate: ${bars.length}`);

    // Prova a cliccare su una barra visibile
    for (let i = 0; i < Math.min(bars.length, 10); i++) {
      try {
        const isVisible = await bars[i].isVisible().catch(() => false);
        if (isVisible) {
          await bars[i].click({ force: true, timeout: 5000 });
          console.log(`  Click su barra ${i}`);
          await page.waitForTimeout(2000);
          break;
        }
      } catch (e) {
        // Prova la prossima
      }
    }

    // --- Interazione 7: Filtro per conto bancario ---
    console.log('\n  >> Interazione: Filtro conto bancario');

    try {
      const accountFilter = await page.$('button:has-text("Conto"), button:has-text("conto"), button:has-text("Account"), [data-testid*="account"], [aria-label*="account" i], [aria-label*="conto" i]');
      if (accountFilter) {
        console.log('  Filtro conto trovato — click');
        await accountFilter.click();
        await page.waitForTimeout(1000);

        const accountOptions = await page.$$('[role="option"], [role="menuitemcheckbox"], li[class*="option"]');
        console.log(`  Opzioni conto: ${accountOptions.length}`);

        if (accountOptions.length > 0) {
          await accountOptions[0].click();
          console.log('  Selezionato primo conto');
          await page.waitForTimeout(3000);
          await page.waitForLoadState('networkidle').catch(() => {});
          await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-single-account.png'), fullPage: true });
        }
      }
    } catch (e) {
      console.log(`  Errore filtro conto: ${e.message}`);
    }

    // --- Interazione 8: Export Excel (se disponibile) ---
    console.log('\n  >> Interazione: Export');

    try {
      const exportBtn = await page.$('button:has-text("Export"), button:has-text("export"), button:has-text("Scarica"), button:has-text("Download"), [aria-label*="export" i], [aria-label*="download" i]');
      if (exportBtn) {
        console.log('  Bottone export trovato — click');
        const [download] = await Promise.all([
          page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
          exportBtn.click()
        ]);
        if (download) {
          const downloadPath = path.join(CAPTURED_DIR, download.suggestedFilename());
          await download.saveAs(downloadPath);
          console.log(`  File scaricato: ${download.suggestedFilename()}`);
        }
        await page.waitForTimeout(2000);
      }
    } catch (e) {
      console.log(`  Errore export: ${e.message}`);
    }

    // ================================================================
    // FASE C: CATTURA HTML E LOCALSTORAGE
    // ================================================================
    // NOTA: catturiamo PRIMA di ricaricare per evitare timeout su networkidle
    console.log('\n--- FASE C: CATTURA HTML E STORAGE ---');

    // index.html
    const htmlContent = await page.content();
    fs.writeFileSync(path.join(CAPTURED_DIR, 'index.html'), htmlContent);
    console.log(`index.html salvato (${(htmlContent.length / 1024).toFixed(0)} KB)`);

    // localStorage completo (senza troncamento)
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

    // sessionStorage
    const sessionStorageData = await page.evaluate(() => {
      const data = {};
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        data[key] = sessionStorage.getItem(key);
      }
      return data;
    });
    fs.writeFileSync(path.join(CAPTURED_DIR, 'sessionStorage.json'), JSON.stringify(sessionStorageData, null, 2));
    console.log(`sessionStorage salvato (${Object.keys(sessionStorageData).length} chiavi)`);

    // Lista completa di tutti gli URL delle risorse caricate
    const loadedResources = await page.evaluate(() => {
      const resources = {
        scripts: Array.from(document.querySelectorAll('script[src]')).map(s => s.src),
        modules: Array.from(document.querySelectorAll('link[rel="modulepreload"]')).map(l => l.href),
        stylesheets: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href),
        images: Array.from(document.querySelectorAll('img[src]')).map(i => i.src),
        fonts: Array.from(document.querySelectorAll('link[rel="preload"][as="font"]')).map(l => l.href)
      };
      return resources;
    });
    fs.writeFileSync(path.join(CAPTURED_DIR, 'loaded-resources.json'), JSON.stringify(loadedResources, null, 2));
    console.log(`Risorse DOM: ${loadedResources.scripts.length} scripts, ${loadedResources.modules.length} modules, ${loadedResources.stylesheets.length} CSS`);

    // Screenshot finale
    await page.screenshot({ path: path.join(CAPTURED_DIR, 'cashflow-final.png'), fullPage: true });

    // ================================================================
    // FASE D: CHIUSURA E SALVATAGGIO HAR
    // ================================================================
    console.log('\n--- FASE D: SALVATAGGIO HAR ---');
    console.log(`API intercettate: ${apiCount}`);

    // IMPORTANTE: chiudere il context prima di leggere il HAR
    // Playwright scrive il HAR solo alla chiusura del context
    await context.close();
    console.log('Context chiuso — HAR scritto su disco');

    // Verifica che il HAR sia stato creato
    if (fs.existsSync(HAR_PATH)) {
      const harSize = fs.statSync(HAR_PATH).size;
      console.log(`HAR salvato: ${HAR_PATH} (${(harSize / 1024 / 1024).toFixed(1)} MB)`);

      // Conta le entry nel HAR
      try {
        const harContent = JSON.parse(fs.readFileSync(HAR_PATH, 'utf8'));
        const entries = harContent.log?.entries?.length || 0;
        const withBody = harContent.log?.entries?.filter(e =>
          e.response?.content?.text || e.response?.content?.size > 0
        ).length || 0;
        console.log(`HAR entries: ${entries} totali, ${withBody} con response body`);
      } catch (e) {
        console.log(`Impossibile analizzare il HAR: ${e.message}`);
      }
    } else {
      console.error('ERRORE: HAR non trovato!');
    }

    await browser.close();

    console.log('\n=== CASHFLOW CAPTURE COMPLETE ===');
    console.log(`\nFile generati in ${CAPTURED_DIR}/:`);
    const files = fs.readdirSync(CAPTURED_DIR);
    for (const f of files) {
      const stat = fs.statSync(path.join(CAPTURED_DIR, f));
      console.log(`  ${f} (${stat.isDirectory() ? 'dir' : (stat.size / 1024).toFixed(0) + ' KB'})`);
    }
    console.log(`\nProssimo step: python3 build/build-offline.py`);

  } catch (error) {
    console.error(`\nFATAL ERROR: ${error.message}`);
    console.error(error.stack);

    // Salva quello che c'è prima di uscire
    try {
      await context.close();
      await browser.close();
    } catch (e) {}

    process.exit(1);
  }
})();
