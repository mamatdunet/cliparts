// Serveur local, comme Vercel : les adresses /i/ et /apercu/ passent par les fonctions de api/, le reste vient de public/ puis du dépôt.
// Usage : npm install && node tools/build_fiches.mjs && node tools/dev_server.mjs   (http://localhost:8765)
import { createServer } from 'node:http';
import { createReadStream, statSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import fiche from '../api/fiche.js';
import apercu from '../api/apercu.js';

const racine = fileURLToPath(new URL('..', import.meta.url));
const PORT = +process.env.PORT || 8765;
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.gif': 'image/gif', '.jpg': 'image/jpeg' };
const estFichier = (p) => { try { return statSync(p).isFile(); } catch { return false; } };

createServer((req, res) => {
  req.headers['x-forwarded-proto'] = 'http';
  const { pathname } = new URL(req.url, 'http://x');
  const m = pathname.match(/^\/(i|apercu)\/(.+)$/);
  if (m) {
    req.url = `/api?cle=${encodeURIComponent(decodeURIComponent(m[2]))}`;
    return (m[1] === 'i' ? fiche : apercu)(req, res);
  }
  const rel = normalize(decodeURIComponent(pathname === '/' ? '/index.html' : pathname));
  const p = [join(racine, 'public', rel), join(racine, rel)].find(estFichier);
  if (!p) { res.statusCode = 404; return res.end('Introuvable'); }
  res.setHeader('Content-Type', TYPES[extname(p)] || 'application/octet-stream');
  createReadStream(p).pipe(res);
}).listen(PORT, () => console.log(`http://localhost:${PORT}`));
