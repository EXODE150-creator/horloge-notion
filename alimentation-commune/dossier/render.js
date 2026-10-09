// Rend un fichier HTML en PDF A4 avec Chromium. Usage : node render.js entree.html sortie.pdf [--pied]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [inFile, outFile, flag] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(inFile), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const pied = flag === '--pied';
  await page.pdf({
    path: outFile,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: pied,
    headerTemplate: '<div></div>',
    footerTemplate: pied ? `<div style="width:100%;font-size:7pt;color:#5a695d;font-family:sans-serif;padding:0 18mm;display:flex;justify-content:space-between;-webkit-print-color-adjust:exact">
      <span>La Table Commune · Dossier de présentation · Saint-Jean-d'Heurs</span>
      <span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>` : '<div></div>',
  });
  await browser.close();
})();
