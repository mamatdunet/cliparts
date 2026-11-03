// /apercu/<collection>/<dossier>/<fichier>.png : l'image d'aperçu de lien, 1200×630 sur fond blanc,
// générée à la demande puis gardée en cache par Vercel.
import { createRequire } from 'node:module';
import { Resvg } from '@resvg/resvg-js';
import { cleDe, lireFiche, origine } from './_lib/fiches.js';

const POLICE = createRequire(import.meta.url).resolve('dejavu-fonts-ttf/ttf/DejaVuSans.ttf');
const W = 1200, H = 630, MARGE = 40;
const MAX_OCTETS = 20e6;
const MIME = { svg: 'image/svg+xml', gif: 'image/gif', png: 'image/png', jpg: 'image/jpeg' };
// Dessinées pixel par pixel : agrandies d'un nombre entier de fois, sans lissage
const PIXELS = new Set(['web', 'anim', 'szene']);

function taille(ext, o) {
  if (ext === 'gif') return [o.readUInt16LE(6), o.readUInt16LE(8)];
  if (ext === 'png') return [o.readUInt32BE(16), o.readUInt32BE(20)];
  return null;
}

const FONT = { loadSystemFonts: false, fontFiles: [POLICE], defaultFontFamily: 'DejaVu Sans', sansSerifFamily: 'DejaVu Sans', serifFamily: 'DejaVu Sans', monospaceFamily: 'DejaVu Sans' };

export function composer(id, ext, octets) {
  let [x, y, w, h] = [MARGE, MARGE, W - 2 * MARGE, H - 2 * MARGE];
  let rendu = '';
  const dim = PIXELS.has(id) && taille(ext, octets);
  if (dim) {
    const k = Math.max(1, Math.floor(Math.min(w / dim[0], h / dim[1])));
    [w, h] = [dim[0] * k, dim[1] * k];
    [x, y] = [(W - w) / 2, (H - h) / 2];
    rendu = ' style="image-rendering:optimizeSpeed"';
  }
  let mime = MIME[ext];
  if (ext === 'svg') {
    // Un SVG imbriqué n'a pas accès aux polices : on le dessine d'abord à la bonne taille, avec son texte
    const d = new Resvg(octets, { font: FONT });
    const fit = d.width / d.height > w / h ? { mode: 'width', value: w } : { mode: 'height', value: h };
    octets = new Resvg(octets, { font: FONT, fitTo: fit }).render().asPng();
    mime = MIME.png;
  }
  const href = `data:${mime};base64,${octets.toString('base64')}`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="#fff"/><image x="${x}" y="${y}" width="${w}" height="${h}"${rendu} xlink:href="${href}"/></svg>`;
  return new Resvg(svg).render().asPng();
}

export default async function handler(req, res) {
  const cle = cleDe(req).replace(/\.png$/, '');
  const base = origine(req);
  try {
    const f = await lireFiche(base, cle);
    if (!f || f.adulte) {
      res.statusCode = 404;
      res.setHeader('Cache-Control', 'public, s-maxage=3600');
      return res.end('Pas d\'aperçu pour cette image');
    }
    const r = await fetch(f.url);
    if (!r.ok) throw new Error(`${f.url} : ${r.status}`);
    const octets = Buffer.from(await r.arrayBuffer());
    if (octets.length > MAX_OCTETS) throw new Error(`${f.url} : ${octets.length} octets`);
    const png = composer(f.coll.id, f.coll.ext, octets);
    res.statusCode = 200;
    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=31536000');
    res.end(png);
  } catch (e) {
    // Dessin illisible ou trop lourd : l'image du site plutôt qu'un aperçu cassé
    console.error(cle, e);
    res.statusCode = 302;
    res.setHeader('Location', '/assets/og.png');
    res.setHeader('Cache-Control', 'public, s-maxage=3600');
    res.end();
  }
}
