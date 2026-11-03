// Image Open Graph de la page d'accueil (assets/og.png, 1200×630) : le nom du site et quelques cliparts des CD.
// Usage : node tools/build_og.mjs <chemin de Kalam-Bold.ttf>   (police du site, Google Fonts) ; il faut les images dans cliparts/.
import { readFileSync, writeFileSync } from 'node:fs';
import { Resvg } from '@resvg/resvg-js';

const racine = new URL('..', import.meta.url);
const POSE = [
  ['office97/musique-spectacle/dancing', 60, 60, 230, -6],
  ['office97/gens/measrisk', 930, 50, 220, 5],
  ['pro/sports/s_p_0230', 70, 345, 235, 4],
  ['imsi/mammiferes/1995744', 345, 370, 210, -3],
  ['printartist/musique-spectacle/364_play', 640, 375, 205, 3],
  ['masterclips/graphiques/chart007', 925, 345, 225, -5],
];
const data = (cle) => 'data:image/svg+xml;base64,' + readFileSync(new URL(`cliparts/${cle}.svg`, racine)).toString('base64');
const images = POSE.map(([cle, x, y, t, r]) => `<image transform="rotate(${r} ${x + t / 2} ${y + t / 2})" x="${x}" y="${y}" width="${t}" height="${t}" xlink:href="${data(cle)}"/>`).join('');
const pastille = (x, y, c) => `<circle cx="${x}" cy="${y}" r="17" fill="${c}" stroke="#221c18" stroke-width="5"/>`;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="630">
<rect width="1200" height="630" fill="#fffdf7"/>
<g transform="rotate(-8 600 80)">${pastille(582, 58, '#0082f4')}${pastille(622, 58, '#fbaf00')}${pastille(582, 98, '#609b00')}${pastille(622, 98, '#ff1425')}</g>
<text x="600" y="228" text-anchor="middle" font-family="Kalam" font-weight="700" font-size="104" fill="#221c18">Cliparthèque</text>
<text x="600" y="296" text-anchor="middle" font-family="Kalam" font-weight="700" font-size="36" fill="#221c18">les cliparts des CD-ROM d'autrefois</text>
${images}</svg>`;
const png = new Resvg(svg, { font: { loadSystemFonts: false, fontFiles: [process.argv[2]], defaultFontFamily: 'Kalam' } }).render().asPng();
writeFileSync(new URL('assets/og.png', racine), png);
console.log(`assets/og.png : ${png.length} octets`);
