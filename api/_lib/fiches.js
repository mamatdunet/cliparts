// Fiches légères des images, lues par les fonctions : data/index.json (33 Mo) est trop lourd pour être chargé
// à chaque requête. tools/build_fiches.mjs les range au build dans /fiches/<tranche>.json, servies comme le reste du site.
import { createHash } from 'node:crypto';

export const trancheDe = (cle) => createHash('md5').update(cle).digest('hex').slice(0, 3);

export const origine = (req) => `${req.headers['x-forwarded-proto'] || 'https'}://${req.headers['x-forwarded-host'] || req.headers.host}`;

export const cleDe = (req) => new URL(req.url, 'http://x').searchParams.get('cle') || '';

export const cheminImage = (cle) => cle.split('/').map(encodeURIComponent).join('/');

async function json(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} : ${r.status}`);
  return r.json();
}

let collections;
// Renvoie null si l'image n'existe pas ; lève une erreur si les fiches sont injoignables
export async function lireFiche(base, cle) {
  collections ||= await json(`${base}/fiches/collections.json`);
  const coll = collections[cle.split('/')[0]];
  if (!coll) return null;
  const f = (await json(`${base}/fiches/${trancheDe(cle)}.json`))[cle];
  if (!f) return null;
  const [nom, theme, rubrique, auteur, adulte] = f;
  return { cle, nom, theme, rubrique, auteur, adulte: !!adulte, coll, url: `${(coll.base || base + '/cliparts/')}${cheminImage(cle)}.${coll.ext}` };
}
