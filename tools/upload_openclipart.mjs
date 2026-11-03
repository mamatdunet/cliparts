// Envoie les dessins d'Openclipart (cliparts/openclipart, sur le disque externe) dans un store Vercel Blob :
// ils sont trop nombreux pour un déploiement Vercel (limite de 15 000 fichiers). Reprend là où il s'est
// arrêté (liste des envois dans cliparts/_openclipart/envoyes.txt) et note l'adresse du store dans
// cliparts/openclipart/blob.json, que lit build_index.py.
// Usage : cd tools && npm install && node --env-file=.env upload_openclipart.mjs [--parallele 16] [--max 20]
// tools/.env, hors dépôt, s'obtient avec : vercel env pull tools/.env --environment development
// (BLOB_STORE_ID et un jeton OIDC que le module renouvelle seul)
import { put, BlobServiceRateLimited } from '@vercel/blob';
import fs from 'node:fs';
import path from 'node:path';

const root = path.join(import.meta.dirname, '..');
const dst = path.join(root, 'cliparts/openclipart');
const journal = path.join(root, 'cliparts/_openclipart/envoyes.txt');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? +process.argv[i + 1] : d; };
const PARALLELE = arg('--parallele', 16);
const MAX = arg('--max', Infinity); // pour un essai
const PAR_SECONDE = 60; // le plan Pro autorise 75 envois par seconde
if (!process.env.BLOB_STORE_ID) { console.error('Il manque tools/.env : vercel env pull tools/.env --environment development'); process.exit(1); }

const cat = JSON.parse(fs.readFileSync(path.join(dst, 'catalog.json'), 'utf8'));
const faits = new Set(fs.existsSync(journal) ? fs.readFileSync(journal, 'utf8').split('\n') : []);
const todo = cat.items.map(([t, n]) => `openclipart/${cat.themes[t][0]}/${n}.svg`).filter((p) => !faits.has(p)).slice(0, MAX);
console.log(`${cat.items.length} dessins, ${faits.size ? faits.size - 1 : 0} déjà envoyés, ${todo.length} à envoyer`);
const log = fs.createWriteStream(journal, { flags: 'a' });

// Pas plus de PAR_SECONDE envois lancés par seconde, tous fils confondus
let prochain = Date.now();
const cadence = async () => {
  const t = Math.max(prochain, Date.now());
  prochain = t + 1000 / PAR_SECONDE;
  if (t > Date.now()) await new Promise((ok) => setTimeout(ok, t - Date.now()));
};

let fait = 0, octets = 0, base = null;
const debut = Date.now();
async function envoyer(p) {
  const corps = fs.readFileSync(path.join(root, 'cliparts', p));
  for (let essai = 1; ; essai++) {
    await cadence();
    try {
      const r = await put(p, corps, {
        access: 'public', addRandomSuffix: false, allowOverwrite: true,
        contentType: 'image/svg+xml', cacheControlMaxAge: 31536000, multipart: corps.length > 50e6,
      });
      if (!base) {
        base = r.url.slice(0, r.url.indexOf(p));
        fs.writeFileSync(path.join(dst, 'blob.json'), JSON.stringify({ base }) + '\n');
      }
      break;
    } catch (e) {
      if (essai >= 6) throw new Error(`${p} : ${e.message}`);
      const pause = e instanceof BlobServiceRateLimited ? (e.retryAfter || 10) * 1000 : 2000 * 2 ** essai;
      await new Promise((ok) => setTimeout(ok, pause));
    }
  }
  log.write(p + '\n');
  fait++; octets += corps.length;
  if (fait % 100 === 0 || fait === todo.length) {
    const v = fait / ((Date.now() - debut) / 1000);
    process.stdout.write(`\r${fait}/${todo.length} envoyés, ${(octets / 1e9).toFixed(1)} Go, ${v.toFixed(1)}/s, encore ${((todo.length - fait) / v / 60).toFixed(0)} min   `);
  }
}

let i = 0;
await Promise.all(Array.from({ length: PARALLELE }, async () => {
  while (i < todo.length) await envoyer(todo[i++]);
}));
log.end();
console.log(`\nTerminé. Adresse du store : ${base || JSON.parse(fs.readFileSync(path.join(dst, 'blob.json'), 'utf8')).base}`);
