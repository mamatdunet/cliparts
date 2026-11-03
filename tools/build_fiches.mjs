// Fiches légères pour les aperçus de liens (api/fiche.js, api/apercu.js) : public/fiches/<tranche>.json,
// { clé: [nom, thème, rubrique, auteur?, adulte?] }, et collections.json. Lancé par fetch_content.sh.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { trancheDe } from '../api/_lib/fiches.js';

const racine = new URL('..', import.meta.url);
const db = JSON.parse(readFileSync(new URL('data/index.json', racine)));
const sortie = new URL('public/fiches/', racine);
rmSync(sortie, { recursive: true, force: true });
mkdirSync(sortie, { recursive: true });

const adultes = new Set(db.adult || []);
const tranches = new Map();
db.items.forEach(([t, f, nom, v, , a], i) => {
  const [c, slug, theme, r, dir] = db.themes[t];
  const coll = db.collections[c].id;
  // Mêmes règles que assets/app.js pour la clé et le libellé
  const cle = f.includes('/') ? `${coll}/${f}` : `${coll}/${dir || slug}/${f}`;
  const perso = v ? db.persos[v.toUpperCase()] || '' : '';
  const nomSeul = nom ? nom.replace(/\.$/, '') : '';
  const fiche = [nomSeul ? nomSeul + (perso ? ' · ' + perso : '') : '', theme, db.rubriques[r][1], a != null ? db.auteurs[a] : ''];
  if (adultes.has(i)) fiche.push(1);
  const k = trancheDe(cle);
  if (!tranches.has(k)) tranches.set(k, {});
  tranches.get(k)[cle] = fiche;
});
for (const [k, t] of tranches) writeFileSync(new URL(k + '.json', sortie), JSON.stringify(t));
writeFileSync(new URL('collections.json', sortie), JSON.stringify(Object.fromEntries(db.collections.map(({ id, nom, annee, ext, base }) => [id, { id, nom, annee, ext, base }]))));
console.log(`fiches : ${db.items.length} images en ${tranches.size} tranches`);
