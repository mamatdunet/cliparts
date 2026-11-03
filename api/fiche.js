// /i/<collection>/<dossier>/<fichier> : la page du site, avec le titre, le texte et l'image de ce clipart
// pour les aperçus de liens (iMessage, réseaux sociaux). Une fois chargée, assets/app.js ouvre la fiche d'après l'adresse.
import { cheminImage, cleDe, lireFiche, origine } from './_lib/fiches.js';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const SITE = 'Cliparthèque';

// Ce que c'est, selon la collection : [un dessin, ce dessin, accord]
const NATURE = {
  svg: ['un dessin', 'ce dessin', ''], jpg: ['une photo', 'cette photo', 'e'],
  web: ['une image web', 'cette image web', 'e'], anim: ['une animation', 'cette animation', 'e'],
  szene: ['un graphisme de la scène démo', 'ce graphisme', ''], photoartist: ['une image détourée', 'cette image', 'e'],
};
// Les collections dont le nom seul se lirait mal dans une phrase (« une photo de Photos »)
const PROVENANCE = {
  photos: 'du CD Micro Application', web: 'du CD Micro Application', anim: 'du coffret ClipArt & More',
  mphotos: 'de Masterclips', paphotos: 'de Print Artist Gold', photodisc: "d'Office 97",
};
const de = (nom) => (/^[aeiouh]/i.test(nom) ? "d'" : 'de ') + nom;

function textes(f) {
  const { coll } = f;
  const nature = NATURE[coll.id] || NATURE[coll.ext] || NATURE.svg;
  const [un, ce, e] = nature;
  const source = PROVENANCE[coll.id] || de(coll.nom);
  const nom = f.nom || f.theme;
  const date = coll.annee ? ` (${coll.annee})` : '';
  const prendre = coll.ext === 'svg' ? 'À télécharger en SVG ou en PNG' : 'À télécharger';
  if (coll.id === 'openclipart') {
    return [`${nom}, ${un} d'Openclipart`, `${un[0].toUpperCase() + un.slice(1)} du domaine public${f.auteur ? ` signé ${f.auteur}` : ''}, rangé dans « ${f.rubrique} ». Libre de droits, à télécharger en SVG ou en PNG.`];
  }
  const phrases = [
    `Tout droit sorti${e} ${source}${date}, ${ce} vous attend dans la Cliparthèque. ${prendre}.`,
    `Le charme des CD-ROM d'autrefois : ${un} ${source}${date}, rangé${e} dans « ${f.rubrique} ». ${prendre}.`,
    `Une petite trouvaille ${source}${date} : ${un} à retrouver dans « ${f.rubrique} », sur la Cliparthèque.`,
  ];
  // Toujours la même phrase pour une même image
  const n = [...f.cle].reduce((s, c) => (s * 31 + c.charCodeAt(0)) >>> 0, 7);
  return [`${nom}, ${un} ${source}${date}`, phrases[n % phrases.length]];
}

function balises({ titre, texte, url, image, alt, generee }) {
  const m = (p, v) => `<meta property="${p}" content="${esc(v)}">`;
  return [
    m('og:site_name', SITE), m('og:type', 'website'), m('og:title', titre), m('og:description', texte), m('og:url', url), m('og:image', image),
    ...(generee ? [m('og:image:width', 1200), m('og:image:height', 630), m('og:image:type', 'image/png')] : []),
    m('og:image:alt', alt),
    `<meta name="twitter:card" content="summary_large_image">`,
    `<meta name="twitter:title" content="${esc(titre)}">`,
    `<meta name="twitter:description" content="${esc(texte)}">`,
    `<meta name="twitter:image" content="${esc(image)}">`,
    `<link rel="canonical" href="${esc(url)}">`,
  ].join('\n');
}

// Le JPG d'origine va tel quel ; le reste passe par /apercu : SVG refusés comme og:image, GIF et PNG minuscules ou transparents
function page(html, base, f) {
  const accueil = `${base}/assets/og.png`;
  let b;
  if (f && !f.adulte) {
    const [titre, texte] = textes(f);
    const direct = f.coll.ext === 'jpg';
    b = { titre, texte, url: `${base}/i/${cheminImage(f.cle)}`, image: direct ? f.url : `${base}/apercu/${cheminImage(f.cle)}.png`, alt: f.nom || f.theme, generee: !direct };
  } else if (f) {
    // +18 ans : ni l'image ni son nom
    b = { titre: `Image réservée aux adultes · ${SITE}`, texte: `Cette image de la ${SITE} ne s'affiche qu'avec l'option +18 ans.`, url: `${base}/`, image: accueil, alt: SITE, generee: true };
  } else {
    b = { titre: `Image introuvable · ${SITE}`, texte: `Cette image n'existe pas ou plus dans la ${SITE}.`, url: `${base}/`, image: accueil, alt: SITE, generee: true };
  }
  let sortie = html
    .replace(/<title>.*?<\/title>/, `<title>${esc(b.titre)}</title>`)
    .replace(/<meta name="description"[^>]*>/, `<meta name="description" content="${esc(b.texte)}">`)
    .replace(/<!-- og -->[\s\S]*?<!-- \/og -->/, () => balises(b));
  if (!f || f.adulte) sortie = sortie.replace('<head>', '<head>\n<meta name="robots" content="noindex">');
  return sortie;
}

export default async function handler(req, res) {
  const cle = cleDe(req).replace(/\/+$/, '');
  const base = origine(req);
  try {
    const [f, r] = await Promise.all([lireFiche(base, cle), fetch(`${base}/`)]);
    if (!r.ok) throw new Error(`accueil : ${r.status}`);
    const html = page(await r.text(), base, f);
    res.statusCode = f ? 200 : 404;
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.setHeader('Cache-Control', `public, max-age=0, must-revalidate, s-maxage=${f ? 604800 : 3600}, stale-while-revalidate=86400`);
    res.end(html);
  } catch (e) {
    // Le site reste utilisable sans aperçu : l'ancienne adresse ouvre la même fiche
    console.error(cle, e);
    res.statusCode = 302;
    res.setHeader('Location', `/#i=${encodeURIComponent(cle)}`);
    res.setHeader('Cache-Control', 'no-store');
    res.end();
  }
}
