// Рисует прозрачные PNG-слои 1080x1920: head.png и s000.png… по project.json.
// Использование: node overlays.js <project.json> <fonts_dir> <out_dir>
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path');
const [proj, fontsDir, outDir] = process.argv.slice(2);
const P = JSON.parse(fs.readFileSync(proj));
const tpl = fs.readFileSync(path.join(__dirname, '../templates/overlay.html'), 'utf8')
  .replace(/FONTS_DIR/g, 'file://' + path.resolve(fontsDir))
  .replace(/SKILL_FONTS/g, 'file://' + path.resolve(__dirname, '../fonts'));
fs.mkdirSync(outDir, {recursive: true});
const tmp = path.join(outDir, '_overlay.html'); fs.writeFileSync(tmp, tpl);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1080, height: 1920}});
  await p.goto('file://' + path.resolve(tmp));
  await p.evaluate(() => document.fonts.ready);
  await p.evaluate(h => {
    const el = document.getElementById('head');
    el.className = h.color || 'bordeaux';                 // 'bordeaux' | 'green'
    el.querySelector('.main').innerHTML = h.main;          // строки через <br>
    el.querySelector('.acc').innerHTML = h.accent || '';   // одно слово рукописью, без заглавных/аббревиатур
    el.querySelector('.tail').innerHTML = h.tail || '';    // мелкая строка (аббревиатуры, «в Reels» и т.п.)
    el.style.display = 'block';
  }, P.headline);
  await p.waitForTimeout(300);
  await p.screenshot({path: path.join(outDir, 'head.png'), omitBackground: true});
  await p.evaluate(() => document.getElementById('head').style.display = 'none');
  let maxw = 0;
  for (let i = 0; i < P.chunks.length; i++) {
    const w = await p.evaluate(t => {
      const s = document.getElementById('sub'); s.innerHTML = '<span>' + t + '</span>';
      const sp = s.firstChild; let fs = 66;
      while (sp.getBoundingClientRect().width > 1000 && fs > 40) { fs -= 2; sp.style.fontSize = fs + 'px'; }
      return sp.getBoundingClientRect().width;
    }, P.chunks[i][1]);
    maxw = Math.max(maxw, w);
    await p.screenshot({path: path.join(outDir, `s${String(i).padStart(3, '0')}.png`), omitBackground: true});
  }
  fs.unlinkSync(tmp);
  console.log(`слоёв: ${P.chunks.length + 1}, самая широкая плашка ${Math.round(maxw)}px`);
  await b.close();
})();
