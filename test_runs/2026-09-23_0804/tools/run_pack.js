// Black-box runner: drives the public site in a real browser, one fresh context per list.
// Usage: node run_pack.js <pack.md> <outdir> <siteVersion> [ids comma list] [width] [height] [suffix]
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const [packPath, outDir, siteVersion, idsArg, wArg, hArg, suffixArg] = process.argv.slice(2);
const URL = process.env.PUBLIC_URL || 'https://rx-label-search-aidancolvins-projects.vercel.app/';
const W = +(wArg || 1440), H = +(hArg || 900), SUFFIX = suffixArg || '';

function parseLists(md) {
  const s5 = md.split('## Section 5')[1].split('## Section 6')[0];
  const lines = s5.split('\n'); const out = [];
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].trim().match(/^(L\d\d|G\d\d)$/);
    if (m) { let j = i + 1; while (!lines[j].trim()) j++; out.push({ id: m[1], line: lines[j].trim() }); }
  }
  return out;
}

async function extract(page) {
  return page.evaluate(() => {
    const t = (el) => (el ? el.innerText.trim() : null);
    const main = document.querySelector('main') || document.body;
    const alerts = [...main.querySelectorAll('li.alert')].map((a) => ({
      grade: t(a.querySelector('.grade')), grade_text: t(a.querySelector('.alert__grade-text')),
      drugs: t(a.querySelector('.alert__drugs')), category: t(a.querySelector('.alert__tier')),
      basis: t(a.querySelector('.alert__basis')), quote: t(a.querySelector('.alert__quote')),
      source: t(a.querySelector('.alert__source')), why_title: t(a.querySelector('.alert__why-title')),
      why_text: t(a.querySelector('.alert__why-text')),
      action: t(a.querySelector('.alert__action-text')), includes: t(a.querySelector('.alert__includes')),
      sources: t(a.querySelector('.alert__sources')),
      links: [...a.querySelectorAll('a[href]')].map((l) => ({ text: l.innerText.trim(), href: l.href })),
      classes: a.className,
    }));
    const severity = [...main.querySelectorAll('.severity__cell')].map((c) => ({
      letter: t(c.querySelector('.severity__letter')), name: t(c.querySelector('.severity__name')), count: t(c.querySelector('.severity__count')) }));
    const meds = [...main.querySelectorAll('.med-card')].map((c) => ({
      brand: t(c.querySelector('.med-card__brand')), generic: t(c.querySelector('.med-card__generic')),
      dose: t(c.querySelector('.med-card__dose')), facts: t(c.querySelector('.med-card__facts')), text: t(c) }));
    const totals = [...main.querySelectorAll('.totals li')].map((li) => li.innerText.trim());
    const totalMme = t(main.querySelector('.totals__mme'));
    const links = [...main.querySelectorAll('a[href]')].map((l) => ({ text: l.innerText.trim(), href: l.href, in_alert: !!l.closest('li.alert') }));
    const statusText = t(main.querySelector('.results__checked-count'));
    return { alerts, severity, meds, totals, totalMme, links, statusText, caption: t(main.querySelector('.severity__caption')), text: main.innerText, html: main.outerHTML };
  });
}

async function runOne(browser, item) {
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, permissions: ['clipboard-read', 'clipboard-write'] });
  await ctx.clearCookies();
  const page = await ctx.newPage();
  const consoleErrors = []; const badResponses = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message));
  page.on('response', (r) => { if (r.status() >= 400) badResponses.push(`${r.status()} ${r.url()}`); });
  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'networkidle', timeout: 45000 });
  const tInteractive = (Date.now() - t0) / 1000;
  await page.evaluate(() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} });
  const focus = await page.evaluate(() => { const a = document.activeElement; return { tag: a.tagName, id: a.id, placeholder: a.getAttribute('placeholder'), label: a.labels && a.labels[0] ? a.labels[0].innerText : null }; });
  const focusedOnLoad = focus.tag === 'INPUT' || focus.tag === 'TEXTAREA';
  const defects = [];
  if (!focusedOnLoad) {
    defects.push('Input did not have focus on load; clicked the first text input.');
    await page.locator('input[type=text], input:not([type]), input[type=search], textarea').first().click();
  }
  await page.evaluate((txt) => navigator.clipboard.writeText(txt), item.line);
  const before = await page.evaluate(() => (document.querySelector('main') || document.body).innerText);
  await page.keyboard.press('ControlOrMeta+V');
  await page.waitForTimeout(150);
  const tEnter = Date.now();
  await page.keyboard.press('Enter');
  // wait until the results region stops changing (stable 3 s), max 30 s
  let last = null, lastChange = Date.now(), changed = false;
  while (Date.now() - tEnter < 30000) {
    await page.waitForTimeout(400);
    const cur = await page.evaluate(() => (document.querySelector('main') || document.body).innerText);
    if (cur !== last) { if (last !== null || cur !== before) changed = true; last = cur; lastChange = Date.now(); }
    else if (Date.now() - lastChange > 3000 && changed) break;
  }
  const hung = Date.now() - tEnter >= 30000;
  if (!changed) defects.push('Paste + Enter did not change the page.');
  const secondsToResults = (lastChange - tEnter) / 1000;
  const data = await extract(page);
  const shot = path.join(outDir, 'screenshots', `${item.id}${SUFFIX}.png`);
  await page.screenshot({ path: shot, fullPage: true });
  await ctx.close();
  return { id: item.id, input: item.line, viewport: `${W}x${H}`, focus, focusedOnLoad, secondsToInteractive: tInteractive,
    secondsToResults, hung, defects, consoleErrors, badResponses, ...data };
}

(async () => {
  const lists = parseLists(fs.readFileSync(packPath, 'utf8'));
  const wanted = idsArg && idsArg !== 'all' ? new Set(idsArg.split(',')) : null;
  for (const d of ['screenshots', 'dom', 'raw']) fs.mkdirSync(path.join(outDir, d), { recursive: true });
  const browser = await chromium.launch();
  for (const item of lists) {
    if (wanted && !wanted.has(item.id)) continue;
    let r, attempts = [];
    for (let a = 1; a <= 2; a++) {
      try { r = await runOne(browser, item); attempts.push({ attempt: a, ok: !r.hung }); if (!r.hung) break; }
      catch (e) { attempts.push({ attempt: a, error: String(e) }); }
    }
    if (!r) r = { id: item.id, input: item.line, error: 'both attempts failed' };
    r.attempts = attempts; r.siteVersion = siteVersion; r.runAt = new Date().toISOString();
    if (r.html) { fs.writeFileSync(path.join(outDir, 'dom', `${item.id}${SUFFIX}.html`), r.html); delete r.html; }
    fs.writeFileSync(path.join(outDir, 'raw', `${item.id}${SUFFIX}.json`), JSON.stringify(r, null, 1));
    console.log(item.id, SUFFIX, 'alerts', (r.alerts || []).length, 'secs', r.secondsToResults, r.error || '');
  }
  await browser.close();
})();
