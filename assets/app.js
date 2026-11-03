/* Cliparthèque — recherche et grille virtualisée sur data/index.json, éditorial sur data/editorial.json.
   Index : themes = [collection, dossier, nom] ; items = [thème, fichier, nom?, personnage?, mots-clés?]. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[’']/g, ' ');
  const fmt = (n) => n.toLocaleString('fr-FR');
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* stockage indisponible */ } },
  };
  const COLL_COLOR = { '': 'var(--green)', pro: 'var(--blue)', mc: 'var(--red)', photos: 'var(--yellow)', web: 'var(--neutral-500)', szene: 'var(--ink)', imsi: 'var(--green-700)', anim: 'var(--red-700)', masterclips: 'var(--blue-700)', mphotos: 'var(--neutral-600)', openclipart: 'var(--neutral-300)' };
  // Mots-clés en plus pour les types d'images web (noms anglais du CD compris)
  const KW = { boutons: 'button', icones: 'icon', puces: 'bullet', fleches: 'arrow', traits: 'ligne separateur line' };
  // Animations web : un bouton existe en 25 couleurs (même animation, même fond), un objet ou un mot en 3 fonds
  const animKey = (t, f) => THEMES[t].slug.startsWith('bouton') ? t + f[1] + f.slice(-1) : t + f.slice(0, -1);
  const LAST = new Set(['web', 'anim']);
  const COLL_IDS = ['pro', 'mc', 'photos', 'web', 'szene', 'imsi', 'anim', 'masterclips', 'mphotos', 'openclipart'];

  // RUBS = thèmes généraux affichés ; THEMES = dossiers des CD (chaque dossier appartient à une rubrique)
  let DB, ITEMS = [], THEMES = [], RUBS = [], VARIANTS = new Map(), BY_THEME = [], BY_RUB = [], EXT = {}, BASE = {}, ADULT = new Set(), BY_KEY = new Map();
  let EDITO = { selections: [], articles: [] }, SEL = new Map(), ART = new Map();
  let results = [];
  const state = { q: '', c: '', t: -1, d: -1, fav: false, sel: '', a: '', seed: 0, photos: store.get('photos', true) !== false, bg: store.get('bg', 'white'), size: store.get('size', 148), adult: store.get('adult', false) === true };
  const favs = new Set(store.get('favs', []));

  const grid = $('#grid');
  const rendered = new Map();
  let geo = { cols: 1, tw: 0, rowH: 1, lbl: 0 };

  // ---------- Données ----------
  // L'éditorial (galerie du jour, sélections, articles) est facultatif : le site marche sans lui
  const edito = fetch('data/editorial.json').then((r) => r.json()).catch(() => null);
  fetch('data/index.json').then((r) => r.json()).then(async (db) => init(db, await edito))
    .catch(() => { $('#count').textContent = "Impossible de charger l'index."; });

  function init(db, ed) {
    DB = db;
    if (ed) EDITO = ed;
    for (const s of EDITO.selections) SEL.set(s.id, s);
    for (const a of EDITO.articles) ART.set(a.id, a);
    for (const c of db.collections) { EXT[c.id] = c.ext; BASE[c.id] = c.base || 'cliparts/'; }
    ADULT = new Set(db.adult || []);
    RUBS = db.rubriques.map(([slug, nom], i) => ({ i, slug, nom, norm: norm(nom) }));
    THEMES = db.themes.map(([c, slug, nom, r], i) => ({ i, c: db.collections[c].id, slug, nom, r, key: db.collections[c].id + ':' + slug, norm: norm(nom), total: 0 }));
    ITEMS = db.items.map(([t, f, nom, v, kw, a], i) => {
      const th = THEMES[t];
      th.total++;
      const perso = v ? db.persos[v.toUpperCase()] || '' : '';
      const name = nom ? nom.replace(/\.$/, '') : '';
      const label = name ? name + (perso ? ' · ' + perso : '') : th.nom;
      const key = `${th.c}/${th.slug}/${f}`;
      const it = { i, t, f, name, perso, label, key, path: `${BASE[th.c]}${key}.${EXT[th.c]}` };
      if (a != null) it.auteur = db.auteurs[a];
      it.nname = norm(name);
      it.hay = norm([name, perso, th.nom, RUBS[th.r].nom, db.collections[db.themes[t][0]].nom, KW[th.slug] || '', kw || '', f].join(' '));
      // Variantes : personnages (Cliparts Pro) ou couleurs d'une même forme (images web)
      const k = th.c === 'pro' ? f.slice(0, 1) + f.slice(3) : th.c === 'web' ? t + f.slice(0, 4) : th.c === 'anim' ? animKey(t, f) : '';
      if (k) {
        it.vk = k;
        if (!VARIANTS.has(k)) VARIANTS.set(k, []);
        VARIANTS.get(k).push(i);
      }
      (BY_THEME[t] ||= []).push(i);
      (BY_RUB[th.r] ||= []).push(i);
      BY_KEY.set(key, i);
      return it;
    });
    const open = hashItem();
    readHash();
    applyPrefs();
    renderColls();
    update();
    openFromHash(open);
    syncArticle();
  }
  const hashItem = () => new URLSearchParams(location.hash.slice(1)).get('i');
  function openFromHash(open) {
    const it = open && ITEMS.find((x) => x.key === open);
    if (it && visible(it.i)) openDetail(it.i); else if (dlg.open) dlg.close();
  }

  // ---------- État <-> URL ----------
  function readHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    state.q = p.get('q') || '';
    state.c = COLL_IDS.includes(p.get('c')) ? p.get('c') : '';
    // t = rubrique ; d = dossier d'un CD (les anciennes adresses t=collection:dossier deviennent d)
    const t = p.get('t') || '', d = p.get('d') || (t.includes(':') ? t : '');
    const rub = RUBS.find((x) => x.slug === t), th = THEMES.find((x) => x.key === d);
    state.t = rub ? rub.i : -1;
    state.d = th ? th.i : -1;
    state.fav = p.get('fav') === '1';
    state.sel = SEL.has(p.get('sel')) ? p.get('sel') : '';
    state.a = ART.has(p.get('a')) || p.get('a') === 'sommaire' ? p.get('a') : '';
    state.seed = +p.get('mix') || 0;
    $('#q').value = state.q;
  }
  function writeHash() {
    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.c) p.set('c', state.c);
    if (state.t >= 0) p.set('t', RUBS[state.t].slug);
    if (state.d >= 0) p.set('d', THEMES[state.d].key);
    if (state.fav) p.set('fav', '1');
    if (state.sel) p.set('sel', state.sel);
    if (state.a) p.set('a', state.a);
    if (state.seed) p.set('mix', state.seed);
    if (current >= 0) p.set('i', ITEMS[current].key);
    const h = p.toString();
    history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
  }
  addEventListener('hashchange', () => {
    if (!DB) return;
    const open = hashItem();
    current = -1;
    const sel = state.sel;
    readHash(); update(); openFromHash(open); syncArticle();
    if (state.sel !== sel) scrollTop();
  });

  // ---------- Filtrage ----------
  // Les images marquées +18 ans n'apparaissent nulle part tant que l'option n'est pas activée
  // Les photos peuvent être masquées (bouton Photos), sauf quand on parcourt une collection de photos
  const PHOTO = new Set(['photos', 'mphotos']);
  const visible = (i) => (state.adult || !ADULT.has(i)) && (state.photos || PHOTO.has(state.c) || !PHOTO.has(THEMES[ITEMS[i].t].c));
  function rng(seed) {
    return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  function shuffle(a, seed) {
    const r = rng(seed);
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  }

  function update() {
    const toks = norm(state.q).split(/[^a-z0-9]+/).filter(Boolean);
    const byColl = { '': 0, pro: 0, mc: 0, photos: 0, web: 0, szene: 0, imsi: 0, anim: 0, masterclips: 0, mphotos: 0, openclipart: 0 };
    const byTheme = new Uint32Array(RUBS.length);
    const out = [];
    const scores = new Float32Array(ITEMS.length);
    const sel = state.sel ? selSet(state.sel) : null;
    for (const it of ITEMS) {
      if (state.fav && !favs.has(it.path)) continue;
      if (sel && !sel.has(it.i)) continue;
      if (!visible(it.i)) continue;
      let ok = true, sc = 0;
      for (const tk of toks) {
        const at = it.hay.indexOf(tk);
        if (at < 0) { ok = false; break; }
        const n = it.nname.indexOf(tk);
        if (n === 0 || (n > 0 && it.nname[n - 1] === ' ')) sc += 3; else if (n > 0) sc += 2; else sc += 1;
      }
      if (!ok) continue;
      if (toks.length && it.nname === toks.join(' ')) sc += 5;
      const th = THEMES[it.t];
      byColl['']++; byColl[th.c]++;
      if (state.c && th.c !== state.c) continue;
      if (state.d >= 0 && it.t !== state.d) continue;
      byTheme[th.r]++;
      if (state.t >= 0 && th.r !== state.t) continue;
      scores[it.i] = sc;
      out.push(it.i);
    }
    const home = !toks.length && state.t < 0 && state.d < 0 && !state.fav && !state.sel;
    const seed = state.seed || (home || state.sel ? dailySeed() : 0);
    if (seed) shuffle(out, seed);
    // À l'accueil, les 28 000 boutons et puces passent après les dessins et les photos
    if (home && !state.seed && !state.c) out.sort((a, b) => LAST.has(THEMES[ITEMS[a].t].c) - LAST.has(THEMES[ITEMS[b].t].c));
    else if (toks.length) out.sort((a, b) => scores[b] - scores[a] || a - b);
    results = out;

    const n = out.length;
    $('#count').innerHTML = `${fmt(n)} <span>image${n > 1 ? 's' : ''}</span>`;
    $('#empty').hidden = n > 0;
    renderColls(byColl);
    renderThemes(byTheme, toks.length > 0 || state.fav);
    renderChips();
    renderEdito(home && !state.c);
    $('#fav-only').setAttribute('aria-pressed', state.fav);
    $('#photos-btn').setAttribute('aria-pressed', state.photos);
    $('#shuffle').classList.toggle('toggle', true);
    $('#shuffle').setAttribute('aria-pressed', !!state.seed);
    writeHash();
    for (const el of rendered.values()) el.remove();
    rendered.clear();
    layout();
  }
  function dailySeed() { const d = new Date(); return d.getFullYear() * 1000 + d.getMonth() * 40 + d.getDate(); }

  // ---------- Barre latérale ----------
  function renderColls(counts) {
    const box = $('#colls');
    const list = [{ id: '', nom: 'Toutes les collections', sub: '7 CD-ROM et Openclipart' }, ...DB.collections.map((c) => ({ id: c.id, nom: c.nom, sub: `${c.editeur.split(' (')[0]}, ${c.annee}` }))];
    box.innerHTML = list.map((c) => `<button class="coll" role="radio" type="button" data-c="${c.id}" aria-checked="${state.c === c.id}">
      <span class="dot" style="background:${COLL_COLOR[c.id]}"></span><span>${c.nom}<small>${c.sub}</small></span><span class="n">${counts ? fmt(counts[c.id]) : ''}</span></button>`).join('');
  }
  $('#colls').addEventListener('click', (e) => {
    const b = e.target.closest('.coll'); if (!b) return;
    state.c = b.dataset.c;
    if (state.d >= 0 && state.c && THEMES[state.d].c !== state.c) state.d = -1;
    update(); scrollTop();
  });

  let themeCounts = null, themeFiltered = false;
  function renderThemes(counts, filtered) {
    themeCounts = counts; themeFiltered = filtered;
    const f = norm($('#theme-filter').value.trim());
    let html = '';
    for (const r of RUBS) {
      const n = counts[r.i];
      if (!n && r.i !== state.t) continue;
      if (f && !r.norm.includes(f)) continue;
      html += `<li><button type="button" data-t="${r.i}" aria-pressed="${state.t === r.i}"><span>${r.nom}</span><span class="n">${fmt(n)}</span></button></li>`;
    }
    $('#themes').innerHTML = html || '<li class="grp">Aucun thème</li>';
  }
  $('#themes').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-t]'); if (!b) return;
    const t = +b.dataset.t;
    state.t = state.t === t ? -1 : t;
    state.d = -1;
    update(); scrollTop();
    $('#side').classList.remove('open');
  });
  $('#theme-filter').addEventListener('input', () => themeCounts && renderThemes(themeCounts, themeFiltered));

  // Collections repliables : repliées, seule la collection choisie reste visible
  function foldColls(open) {
    $('#colls').classList.toggle('folded', !open);
    $('#colls-toggle').setAttribute('aria-expanded', open);
    store.set('collsOpen', open);
  }
  foldColls(store.get('collsOpen', true) !== false);
  $('#colls-toggle').addEventListener('click', () => foldColls($('#colls-toggle').getAttribute('aria-expanded') !== 'true'));

  // ---------- Tous les thèmes en grand, avec l'aperçu d'un thème dans une colonne ----------
  const tv = $('#themes-dlg');
  let tvColl = '', tvTheme = -1, tvShown = 0;
  // Images d'une rubrique dans la collection choisie en haut de la fenêtre
  const rubItems = (r) => (BY_RUB[r] || []).filter((i) => visible(i) && (!tvColl || THEMES[ITEMS[i].t].c === tvColl));
  function renderTv() {
    const f = norm($('#tv-filter').value.trim());
    $('#tv-colls').innerHTML = [{ id: '', nom: 'Toutes les collections' }, ...DB.collections].map((c) =>
      `<button class="chip" role="radio" type="button" data-c="${c.id}" aria-checked="${tvColl === c.id}">${c.nom}</button>`).join('');
    const cards = RUBS.filter((r) => !f || r.norm.includes(f)).map((r) => [r, rubItems(r.i)]).filter(([, l]) => l.length);
    $('#tv-body').innerHTML = cards.length ? '<div class="tv-grid">' + cards.map(([r, l]) => {
      // Vignette : de préférence un dessin, pris au même endroit de la liste chaque jour
      const pool = l.filter((i) => EXT[THEMES[ITEMS[i].t].c] === 'svg'), src = pool.length ? pool : l;
      const it = ITEMS[src[(dailySeed() + r.i * 7919) % src.length]];
      return `<button type="button" class="tv-card" data-t="${r.i}" aria-pressed="${tvTheme === r.i}">
        <span class="th k-${THEMES[it.t].c}"><img src="${it.path}" alt="" loading="lazy"></span>
        <strong>${esc(r.nom)}</strong><small>${fmt(l.length)} image${l.length > 1 ? 's' : ''}</small></button>`;
    }).join('') + '</div>' : '<p class="muted">Aucun thème.</p>';
  }
  function openPanel(r) {
    tvTheme = r; tvShown = 0;
    for (const b of tv.querySelectorAll('.tv-card')) b.setAttribute('aria-pressed', +b.dataset.t === r);
    const l = rubItems(r);
    $('#tp-coll').textContent = tvColl ? DB.collections.find((c) => c.id === tvColl).nom : 'Toutes les collections';
    $('#tp-title').textContent = RUBS[r].nom;
    $('#tp-go').textContent = `Afficher ${l.length > 1 ? 'les ' + fmt(l.length) + ' images' : "l'image"} dans la grille`;
    // Les dossiers des CD qui composent la rubrique, pour aller plus finement
    const folders = new Map();
    for (const i of l) folders.set(ITEMS[i].t, (folders.get(ITEMS[i].t) || 0) + 1);
    $('#tp-folders').innerHTML = folders.size > 1 ? `<span class="eyebrow">Dossiers des CD</span>` + [...folders].sort((a, b) => b[1] - a[1]).map(([t, n]) =>
      `<button class="chip" type="button" data-d="${t}" title="${DB.collections.find((c) => c.id === THEMES[t].c).nom}">${esc(THEMES[t].nom)} <small>${fmt(n)}</small></button>`).join('') : '';
    $('#tp-grid').className = 'related-grid tp-grid';
    $('#tp-grid').innerHTML = '';
    morePanel();
    $('#tv-panel').hidden = false;
    $('#tv-panel').scrollTop = 0;
  }
  function morePanel() {
    const l = rubItems(tvTheme), next = l.slice(tvShown, tvShown + 60);
    tvShown += next.length;
    $('#tp-grid').insertAdjacentHTML('beforeend', next.map((i) =>
      `<button type="button" class="k-${THEMES[ITEMS[i].t].c}" data-i="${i}" title="${esc(ITEMS[i].label)}"><img src="${ITEMS[i].path}" alt="${esc(ITEMS[i].label)}" loading="lazy"></button>`).join(''));
    $('#tp-more').hidden = tvShown >= l.length;
  }
  function closePanel() {
    tvTheme = -1;
    $('#tv-panel').hidden = true;
    for (const b of tv.querySelectorAll('.tv-card[aria-pressed="true"]')) b.setAttribute('aria-pressed', false);
  }
  $('#themes-all').addEventListener('click', () => {
    tvColl = state.c; $('#tv-filter').value = $('#theme-filter').value;
    renderTv(); tv.showModal(); $('#tv-body').scrollTop = 0;
    $('#side').classList.remove('open');
  });
  $('#tv-filter').addEventListener('input', renderTv);
  $('#tv-colls').addEventListener('click', (e) => {
    const b = e.target.closest('[data-c]'); if (!b) return;
    tvColl = b.dataset.c; renderTv(); $('#tv-body').scrollTop = 0;
  });
  $('#tv-body').addEventListener('click', (e) => {
    const b = e.target.closest('.tv-card'); if (!b) return;
    +b.dataset.t === tvTheme ? closePanel() : openPanel(+b.dataset.t);
  });
  $('#tp-close').addEventListener('click', closePanel);
  $('#tp-more').addEventListener('click', morePanel);
  $('#tp-grid').addEventListener('click', (e) => { const b = e.target.closest('[data-i]'); if (b) openDetail(+b.dataset.i); });
  $('#tp-folders').addEventListener('click', (e) => {
    const b = e.target.closest('[data-d]'); if (!b) return;
    const t = +b.dataset.d;
    Object.assign(state, { c: THEMES[t].c, t: -1, d: t, q: '', fav: false, sel: '', seed: 0 });
    $('#q').value = ''; $('#theme-filter').value = '';
    tv.close(); update(); scrollTop();
  });
  $('#tp-go').addEventListener('click', () => {
    Object.assign(state, { c: tvColl, t: tvTheme, d: -1, q: '', fav: false, sel: '', seed: 0 });
    $('#q').value = ''; $('#theme-filter').value = '';
    tv.close(); update(); scrollTop();
  });
  // Échap ferme d'abord l'aperçu, puis la fenêtre
  tv.addEventListener('cancel', (e) => { if (!$('#tv-panel').hidden) { e.preventDefault(); closePanel(); } });
  tv.addEventListener('close', closePanel);

  function renderChips() {
    const chips = [];
    if (state.t >= 0) chips.push(['t', RUBS[state.t].nom]);
    if (state.d >= 0) chips.push(['d', 'Dossier : ' + THEMES[state.d].nom]);
    if (state.sel) chips.push(['sel', SEL.get(state.sel).titre]);
    if (state.fav) chips.push(['fav', 'Favoris']);
    if (state.seed) chips.push(['mix', 'Mélangé']);
    $('#active').innerHTML = chips.map(([k, l]) => `<button class="chip" type="button" data-k="${k}" aria-label="Retirer le filtre ${l}">${l}<svg class="ic" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg></button>`).join('');
  }
  $('#active').addEventListener('click', (e) => {
    const b = e.target.closest('.chip'); if (!b) return;
    ({ t: () => (state.t = -1), d: () => (state.d = -1), sel: () => (state.sel = ''), fav: () => (state.fav = false), mix: () => (state.seed = 0) })[b.dataset.k]();
    update();
  });

  // ---------- Grille virtualisée ----------
  function layout() {
    const W = grid.clientWidth;
    const gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--gap')) || 14;
    const cols = Math.max(2, Math.floor((W + gap) / (state.size + gap)));
    const tw = (W - gap * (cols - 1)) / cols;
    const lbl = tw >= 108 ? 38 : 0;
    geo = { cols, tw, lbl, gap, rowH: tw + lbl + gap };
    grid.classList.toggle('no-lbl', !lbl);
    const rows = Math.ceil(results.length / cols);
    grid.style.height = Math.max(0, rows * geo.rowH - gap) + 'px';
    for (const el of rendered.values()) place(el, +el.dataset.r);
    paint();
  }
  function place(el, r) {
    const { cols, tw, lbl, gap, rowH } = geo;
    el.style.transform = `translate(${(r % cols) * (tw + gap)}px,${Math.floor(r / cols) * rowH}px)`;
    el.style.width = tw + 'px';
    el.style.height = tw + lbl + 'px';
  }
  function paint() {
    const top = grid.getBoundingClientRect().top;
    const { cols, rowH } = geo;
    const first = Math.max(0, Math.floor(-top / rowH) - 2);
    const last = Math.floor((innerHeight - top) / rowH) + 2;
    const a = first * cols, b = Math.min(results.length, (last + 1) * cols);
    for (const [r, el] of rendered) if (r < a || r >= b) { el.remove(); rendered.delete(r); }
    const frag = document.createDocumentFragment();
    for (let r = a; r < b; r++) {
      if (rendered.has(r)) continue;
      const it = ITEMS[results[r]];
      const el = document.createElement('button');
      el.type = 'button';
      el.className = `tile k-${THEMES[it.t].c}` + (favs.has(it.path) ? ' fav' : '');
      el.dataset.r = r;
      const lbl = !it.name && state.d === it.t ? 'n° ' + it.f.replace(/^\D+/, '') : it.label;
      el.title = it.label;
      el.innerHTML = `<span class="pic"><img src="${it.path}" alt="" loading="lazy" decoding="async"></span><span class="lbl">${esc(lbl)}</span>`;
      el.setAttribute('aria-label', it.label);
      place(el, r);
      rendered.set(r, el);
      frag.appendChild(el);
    }
    grid.appendChild(frag);
  }
  let raf = 0;
  addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; paint(); }); }, { passive: true });
  new ResizeObserver(() => layout()).observe(grid);
  grid.addEventListener('click', (e) => { const t = e.target.closest('.tile'); if (t) openDetail(results[+t.dataset.r]); });
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const scrollTop = () => scrollTo({ top: 0 });

  // ---------- Barre d'outils ----------
  let deb = 0;
  $('#q').addEventListener('input', (e) => {
    clearTimeout(deb);
    deb = setTimeout(() => { state.q = e.target.value.trim(); state.seed = 0; state.sel = ''; update(); scrollTop(); }, 90);
  });
  $('#fav-only').addEventListener('click', () => { state.fav = !state.fav; update(); scrollTop(); });
  $('#photos-btn').addEventListener('click', () => {
    state.photos = !state.photos; store.set('photos', state.photos);
    editoKey = ''; update();
    if (tv.open) { renderTv(); if (tvTheme >= 0) openPanel(tvTheme); }
    toast(state.photos ? 'Photos affichées' : 'Photos masquées');
  });
  $('#shuffle').addEventListener('click', () => { state.seed = 1 + Math.floor(Math.random() * 1e6); update(); scrollTop(); });
  $('#reset').addEventListener('click', () => { Object.assign(state, { q: '', c: '', t: -1, d: -1, fav: false, sel: '', seed: 0 }); $('#q').value = ''; $('#theme-filter').value = ''; update(); });
  $('#size').addEventListener('input', (e) => { state.size = +e.target.value; store.set('size', state.size); layout(); });
  $('#bg').addEventListener('click', (e) => { const b = e.target.closest('[data-bg]'); if (b) { state.bg = b.dataset.bg; store.set('bg', state.bg); applyPrefs(); } });
  $('#show-side').addEventListener('click', () => $('#side').classList.add('open'));
  $('#close-side').addEventListener('click', () => $('#side').classList.remove('open'));
  $('#about-btn').addEventListener('click', () => $('#about').showModal());
  $('#adult').addEventListener('change', (e) => {
    state.adult = e.target.checked;
    store.set('adult', state.adult);
    if (state.d >= 0 && !BY_THEME[state.d].some(visible)) state.d = -1;
    update();
  });
  function applyPrefs() {
    document.body.dataset.bg = state.bg;
    for (const b of document.querySelectorAll('#bg [data-bg]')) { b.setAttribute('role', 'radio'); b.setAttribute('aria-checked', b.dataset.bg === state.bg); }
    $('#size').value = state.size;
    $('#adult').checked = state.adult;
  }
  addEventListener('keydown', (e) => {
    if (e.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName) && !document.querySelector('dialog[open]')) { e.preventDefault(); $('#q').focus(); }
    if (dlg.open && (e.key === 'ArrowLeft' || e.key === 'ArrowRight') && document.activeElement.tagName !== 'SELECT') { e.preventDefault(); step(e.key === 'ArrowLeft' ? -1 : 1); }
    if (dlg.open && (e.key === 'r' || e.key === 'R') && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) { rot = (rot + (e.key === 'R' ? 270 : 90)) % 360; $('#d-rot-box').open = true; applyRot(); }
  });

  // ---------- Fiche détaillée ----------
  const dlg = $('#detail');
  let current = -1;
  let rot = 0;
  function openDetail(i) {
    if (i !== current) rot = 0;
    current = i;
    const it = ITEMS[i], th = THEMES[it.t], coll = DB.collections.find((c) => c.id === th.c);
    const raster = EXT[th.c] !== 'svg';
    $('#d-img').src = it.path;
    $('#d-img').alt = it.label;
    $('#d-stage').className = `stage k-${th.c}`;
    $('#d-img').style.width = '';
    $('#d-coll').textContent = `${coll.nom} · ${coll.annee}`;
    $('#d-title').textContent = it.name || th.nom;
    $('#d-meta').innerHTML = [
      `<button class="tag" type="button" data-act="coll" style="box-shadow:inset 6px 0 0 ${COLL_COLOR[th.c]}">${coll.nom}</button>`,
      `<button class="tag" type="button" data-act="theme">${esc(RUBS[th.r].nom)}</button>`,
      th.nom !== RUBS[th.r].nom ? `<button class="tag sub" type="button" data-act="folder" title="Dossier du CD">${esc(th.nom)}</button>` : '',
      it.perso ? `<button class="tag" type="button" data-act="perso">avec ${esc(it.perso)}</button>` : '',
      th.c === 'web' ? `<span class="tag file">forme ${it.f.slice(0, 4)} · couleur ${+it.f.slice(5)}</span>` : '',
      `<span class="tag file" id="d-file">${it.f}.${EXT[th.c]}</span>`,
      it.auteur ? `<a class="tag" href="https://openclipart.org/artist/${encodeURIComponent(it.auteur)}" target="_blank" rel="noopener" title="Ses dessins sur Openclipart">par ${esc(it.auteur)}</a>` : '',
      th.c === 'openclipart' ? `<a class="tag" href="https://openclipart.org/detail/${it.f}" target="_blank" rel="noopener">Fiche Openclipart</a>` : '',
    ].join('');
    const dl = $('#d-svg');
    dl.href = it.path;
    dl.download = fileBase(it) + '.' + EXT[th.c];
    dl.lastChild.textContent = EXT[th.c].toUpperCase();
    $('.png').hidden = raster;
    $('#d-copy').hidden = raster;
    if (raster) {
      const img = $('#d-img');
      const dims = () => {
        const f = $('#d-file');
        if (f && img.naturalWidth) f.textContent = `${it.f}.${EXT[th.c]} · ${img.naturalWidth}×${img.naturalHeight} px`;
        // Les images web sont minuscules : on les agrandit en pixels nets, sans dépasser la scène
        img.style.width = th.c === 'web' || th.c === 'anim' ? Math.min(img.naturalWidth * 4, 440) + 'px' : '';
      };
      img.complete ? dims() : img.addEventListener('load', dims, { once: true });
    }
    applyRot();
    if (!rot) $('#d-rot-box').open = false;
    setFav(it);
    // Variantes (Cliparts Pro) ou voisins dans le thème (Micro Application)
    let rel, title;
    if (th.c === 'pro') { rel = VARIANTS.get(it.f.slice(0, 1) + it.f.slice(3)) || []; title = 'Toutes les variantes'; }
    else if (th.c === 'web') { rel = VARIANTS.get(it.t + it.f.slice(0, 4)) || []; title = 'Toutes les couleurs'; }
    else if (th.c === 'anim') { rel = VARIANTS.get(animKey(it.t, it.f)) || []; title = THEMES[it.t].slug.startsWith('bouton') ? 'Toutes les couleurs' : 'Tous les fonds'; }
    else {
      const list = BY_THEME[it.t], k = list.indexOf(i), s = Math.max(0, Math.min(list.length - 14, k - 7));
      rel = list.slice(s, s + 14); title = 'Dans le même dossier';
    }
    rel = rel.filter(visible);
    $('#d-related-wrap').hidden = rel.length < 2;
    $('#d-related-title').textContent = title;
    $('#d-related').className = `related-grid k-${th.c}`;
    $('#d-related').innerHTML = rel.map((j) => `<button type="button" data-i="${j}" aria-current="${j === i}" title="${esc(ITEMS[j].label)}"><img src="${ITEMS[j].path}" alt="${esc(ITEMS[j].label)}" loading="lazy"></button>`).join('');
    const r = results.indexOf(i);
    $('#d-prev').disabled = r <= 0;
    $('#d-next').disabled = r < 0 || r >= results.length - 1;
    if (!dlg.open) dlg.showModal();
    writeHash();
  }

  // ---------- Rotation : l'aperçu tourne, et les fichiers téléchargés ou copiés sont tournés eux aussi ----------
  function applyRot() {
    const it = ITEMS[current], ext = EXT[THEMES[it.t].c], img = $('#d-img');
    for (const b of document.querySelectorAll('#d-rot [data-rot]')) b.setAttribute('aria-pressed', +b.dataset.rot === rot);
    // Tourné d'un quart de tour, le dessin est réduit pour tenir dans la scène
    const k = rot % 180 && img.clientWidth && img.clientHeight ? Math.min(img.clientWidth / img.clientHeight, img.clientHeight / img.clientWidth) : 1;
    img.style.transform = rot ? `rotate(${rot}deg) scale(${k})` : '';
    // Une fois tourné, un GIF devient une image fixe en PNG
    $('#d-svg').lastChild.textContent = (rot && ext === 'gif' ? 'png' : ext).toUpperCase();
    $('#d-svg').title = rot && ext === 'gif' ? "Image tournée, en PNG (l'animation n'est pas conservée)" : '';
  }
  // Tourne un SVG autour de son centre : la boîte (viewBox) pivote, le dessin passe dans un groupe tourné
  function rotSvg(txt, r) {
    if (!r) return txt;
    const m = txt.match(/<svg[^>]*>/), vb = (m[0].match(/viewBox="([^"]+)"/) || [])[1]?.split(/[\s,]+/).map(Number);
    if (!vb) return txt;
    const cx = vb[0] + vb[2] / 2, cy = vb[1] + vb[3] / 2, [w, h] = r % 180 ? [vb[3], vb[2]] : [vb[2], vb[3]];
    const head = m[0].replace(/viewBox="[^"]+"/, `viewBox="${cx - w / 2} ${cy - h / 2} ${w} ${h}"`);
    return head + `<g transform="rotate(${r} ${cx} ${cy})">` + txt.slice(m.index + m[0].length).replace(/<\/svg>\s*$/, '</g></svg>');
  }
  function saveBlob(blob, name) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }
  async function rotatedFile(it) {
    const ext = EXT[THEMES[it.t].c], name = `${fileBase(it)}-${rot}deg`;
    if (ext === 'svg') return [new Blob([rotSvg(await (await fetch(it.path)).text(), rot)], { type: 'image/svg+xml' }), name + '.svg'];
    const img = new Image();
    await new Promise((ok, ko) => { img.onload = ok; img.onerror = ko; img.src = it.path; });
    const cv = document.createElement('canvas'), w = img.naturalWidth, h = img.naturalHeight;
    [cv.width, cv.height] = rot % 180 ? [h, w] : [w, h];
    const ctx = cv.getContext('2d');
    ctx.translate(cv.width / 2, cv.height / 2);
    ctx.rotate(rot * Math.PI / 180);
    ctx.drawImage(img, -w / 2, -h / 2);
    const type = ext === 'jpg' ? 'image/jpeg' : 'image/png';
    return [await new Promise((ok) => cv.toBlob(ok, type, 0.92)), name + (ext === 'jpg' ? '.jpg' : '.png')];
  }
  $('#d-img').addEventListener('load', () => { if (rot && current >= 0) applyRot(); });
  $('#d-rot').addEventListener('click', (e) => { const b = e.target.closest('[data-rot]'); if (b) { rot = +b.dataset.rot; applyRot(); } });
  $('#d-svg').addEventListener('click', async (e) => {
    const it = ITEMS[current], ext = EXT[THEMES[it.t].c];
    if (!rot && !/^https?:/.test(it.path)) return;
    e.preventDefault();
    // Sans rotation, un fichier venu d'un autre site (Vercel Blob) : l'attribut download y est ignoré
    try { saveBlob(...(rot ? await rotatedFile(it) : [await (await fetch(it.path)).blob(), fileBase(it) + '.' + ext])); } catch { toast('Le téléchargement a échoué'); }
  });
  function step(d) {
    const r = results.indexOf(current) + d;
    if (r >= 0 && r < results.length) openDetail(results[r]);
  }
  function fileBase(it) {
    const s = norm(it.label).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    return `${s || 'clipart'}-${it.f}`;
  }
  function setFav(it) {
    const on = favs.has(it.path);
    $('#d-fav').setAttribute('aria-pressed', on);
    $('#d-fav').setAttribute('aria-label', on ? 'Retirer des favoris' : 'Ajouter aux favoris');
  }
  $('#d-prev').addEventListener('click', () => step(-1));
  $('#d-next').addEventListener('click', () => step(1));
  $('#d-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('close', () => { current = -1; writeHash(); });
  for (const d of document.querySelectorAll('dialog')) {
    d.addEventListener('click', (e) => { if (e.target === d || e.target.closest('[data-close]')) d.close(); });
  }
  $('#d-related').addEventListener('click', (e) => { const b = e.target.closest('[data-i]'); if (b) openDetail(+b.dataset.i); });
  $('#d-meta').addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b) return;
    const it = ITEMS[current], th = THEMES[it.t];
    if (b.dataset.act === 'coll') { state.c = th.c; state.t = -1; state.d = -1; }
    if (b.dataset.act === 'theme') { state.t = th.r; state.d = -1; state.q = ''; }
    if (b.dataset.act === 'folder') { state.c = th.c; state.t = -1; state.d = th.i; state.q = ''; }
    if (b.dataset.act === 'perso') { state.q = it.perso; state.c = 'pro'; state.t = -1; state.d = -1; }
    state.seed = 0; state.sel = '';
    $('#q').value = state.q;
    dlg.close(); art.close(); update(); scrollTop();
  });
  $('#d-fav').addEventListener('click', () => {
    const it = ITEMS[current];
    favs.has(it.path) ? favs.delete(it.path) : favs.add(it.path);
    store.set('favs', [...favs]);
    setFav(it);
    for (const el of rendered.values()) if (results[+el.dataset.r] === current) el.classList.toggle('fav', favs.has(it.path));
    toast(favs.has(it.path) ? 'Ajouté aux favoris' : 'Retiré des favoris');
  });
  $('#d-copy').addEventListener('click', async () => {
    try {
      const txt = rotSvg(await (await fetch(ITEMS[current].path)).text(), rot);
      await navigator.clipboard.writeText(txt);
      toast('SVG copié dans le presse-papiers');
    } catch { toast('Copie impossible dans ce navigateur'); }
  });
  $('#d-png').addEventListener('click', async () => {
    const it = ITEMS[current], size = +$('#d-png-size').value;
    try {
      const txt = rotSvg(await (await fetch(it.path)).text(), rot);
      const vb = (txt.match(/viewBox="([^"]+)"/) || [])[1]?.split(/[\s,]+/).map(Number) || [0, 0, 1, 1];
      const k = size / Math.max(vb[2], vb[3]);
      const w = Math.round(vb[2] * k), h = Math.round(vb[3] * k);
      const sized = txt.replace('<svg ', `<svg width="${w}" height="${h}" `);
      const url = URL.createObjectURL(new Blob([sized], { type: 'image/svg+xml' }));
      const img = new Image();
      await new Promise((ok, ko) => { img.onload = ok; img.onerror = ko; img.src = url; });
      const cv = document.createElement('canvas');
      cv.width = w; cv.height = h;
      cv.getContext('2d').drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      cv.toBlob((blob) => saveBlob(blob, `${fileBase(it)}${rot ? '-' + rot + 'deg' : ''}-${size}px.png`), 'image/png');
    } catch { toast("L'export PNG a échoué"); }
  });

  // ---------- Éditorial : galerie du jour, sélections, articles « Autour des cliparts » (data/editorial.json) ----------
  // Une sélection réunit les images qui répondent à l'une de ses règles : q = recherche, t = thème (* final = préfixe)
  const selCache = new Map();
  function selSet(id) {
    if (selCache.has(id)) return selCache.get(id);
    const rules = SEL.get(id).regles.map((r) => ({
      toks: r.q ? norm(r.q).split(/[^a-z0-9]+/).filter(Boolean) : [],
      t: !r.t ? null : r.t.endsWith('*') ? (k) => k.startsWith(r.t.slice(0, -1)) : (k) => k === r.t,
    }));
    const set = new Set();
    for (const it of ITEMS) {
      if (rules.some((r) => (!r.t || r.t(THEMES[it.t].key)) && r.toks.every((tk) => it.hay.includes(tk)))) set.add(it.i);
    }
    selCache.set(id, set);
    return set;
  }
  const selCount = (id) => { let n = 0; for (const i of selSet(id)) if (visible(i)) n++; return n; };
  // n images d'une sélection, différentes chaque jour, une seule par groupe de variantes (couleurs, personnages, fonds)
  function pick(id, n) {
    const seen = new Set(), out = [];
    for (const i of shuffle([...selSet(id)].filter(visible), dailySeed() + id.length)) {
      const vk = ITEMS[i].vk;
      if (vk && seen.has(vk)) continue;
      if (vk) seen.add(vk);
      out.push(i);
      if (out.length === n) break;
    }
    return out;
  }
  const thumb = (i, href) => {
    const it = ITEMS[i];
    return `<a class="th k-${THEMES[it.t].c}" href="${href}&i=${encodeURIComponent(it.key)}" title="${esc(it.label)}"><img src="${it.path}" alt="${esc(it.label)}" loading="lazy"></a>`;
  };

  // Périodes des galeries du jour : « MM-JJ/MM-JJ », « AAAA-MM-JJ/… », ou paques, meres, peres avec un décalage en jours
  function easter(y) {
    const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451), x = h + l - 7 * m + 114;
    return new Date(y, Math.floor(x / 31) - 1, (x % 31) + 1);
  }
  // Fête des mères : dernier dimanche de mai, une semaine plus tard si c'est la Pentecôte ; fête des pères : 3e dimanche de juin
  function mothers(y) {
    const d = new Date(y, 5, 0), p = easter(y);
    d.setDate(d.getDate() - d.getDay()); p.setDate(p.getDate() + 49);
    if (+d === +p) d.setDate(d.getDate() + 7);
    return d;
  }
  function fathers(y) { const d = new Date(y, 5, 1); d.setDate(1 + ((7 - d.getDay()) % 7) + 14); return d; }
  function day(tok, y) {
    const m = tok.trim().match(/^(?:(paques|meres|peres)|(?:(\d{4})-)?(\d\d)-(\d\d))([+-]\d+)?$/);
    if (!m) return null;
    const d = m[1] ? { paques: easter, meres: mothers, peres: fathers }[m[1]](y) : new Date(m[2] ? +m[2] : y, +m[3] - 1, +m[4]);
    if (m[5]) d.setDate(d.getDate() + +m[5]);
    return d;
  }
  function inPeriod(p, now) {
    const y = now.getFullYear(), today = new Date(y, now.getMonth(), now.getDate());
    const [s, e] = p.split('/').map((x) => day(x, y));
    if (!s || !e) return false;
    return s <= e ? today >= s && today <= e : today >= s || today <= e; // à cheval sur deux années
  }
  const todaySel = () => EDITO.selections.find((s) => s.quand && s.quand.some((p) => inPeriod(p, new Date())));

  let editoKey = '';
  function renderEdito(show) {
    const sel = state.sel && SEL.get(state.sel);
    $('#sel-head').hidden = !sel;
    if (sel) {
      $('#sel-head').innerHTML = `<p class="eyebrow">${sel === todaySel() ? "Galerie du jour" : sel.quand ? 'Au fil de l’année' : 'Sélection'}</p>
        <h1>${esc(sel.titre)}</h1><p>${esc(sel.texte)}</p>`;
    }
    const box = $('#edito');
    box.hidden = !show || !EDITO.selections.length;
    const key = dailySeed() + ':' + state.adult + ':' + state.photos;
    if (box.hidden || editoKey === key) return;
    editoKey = key;
    const today = todaySel();
    const date = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    let html = '';
    if (today) {
      html += `<section class="today" aria-labelledby="today-h">
        <div class="today-txt"><p class="eyebrow">Aujourd'hui, ${date}</p><h2 id="today-h">${esc(today.titre)}</h2><p>${esc(today.texte)}</p>
        <a class="btn primary" href="#sel=${today.id}">Voir les ${fmt(selCount(today.id))} images</a></div>
        <div class="today-pics">${pick(today.id, 8).map((i) => thumb(i, '#sel=' + today.id)).join('')}</div></section>`;
    }
    // Les articles, à côté de la galerie du jour, pour donner le contexte dès l'arrivée
    if (EDITO.articles.length) {
      html += `<aside class="une-journal" aria-labelledby="journal-h"><h2 id="journal-h" class="eyebrow">Autour des cliparts</h2>
        ${EDITO.articles.map((a) => artRow(a)).join('')}<a class="more" href="#a=sommaire">Tous les articles →</a></aside>`;
    }
    if (html) html = `<div class="une${today ? '' : ' seul'}">${html}</div>`;
    const fetes = EDITO.selections.filter((s) => s.quand && s !== today);
    html += `<div class="fetes"><span class="eyebrow">Au fil de l'année</span>${fetes.map((s) => `<a class="chip" href="#sel=${s.id}">${esc(s.titre)}</a>`).join('')}</div>`;
    html += `<h2 class="edito-h">Sélections</h2><div class="cards">${EDITO.selections.filter((s) => !s.quand).map((s) =>
      `<a class="card" href="#sel=${s.id}"><span class="mosaic">${pick(s.id, 4).map((i) => `<img class="k-${THEMES[ITEMS[i].t].c}" src="${ITEMS[i].path}" alt="" loading="lazy">`).join('')}</span>
        <strong>${esc(s.titre)}</strong><small>${fmt(selCount(s.id))} images</small></a>`).join('')}</div>`;
    box.innerHTML = html + '<h2 class="edito-h">Toutes les images</h2>';
  }
  function artRow(a) {
    const it = ITEMS[BY_KEY.get(a.image)];
    return `<a class="art-row" href="#a=${a.id}"><span class="cover${it ? ' k-' + THEMES[it.t].c : ''}">${it ? `<img src="${it.path}" alt="" loading="lazy">` : ''}</span>
      <span><strong>${esc(a.titre)}</strong><small>${esc(a.chapo)}</small></span></a>`;
  }
  function artCard(a) {
    const it = ITEMS[BY_KEY.get(a.image)];
    return `<a class="card art" href="#a=${a.id}"><span class="cover${it ? ' k-' + THEMES[it.t].c : ''}">${it ? `<img src="${it.path}" alt="" loading="lazy">` : ''}</span>
      <strong>${esc(a.titre)}</strong><small>${esc(a.chapo)}</small></a>`;
  }

  // Articles : fragments HTML de data/journal/<id>.html, ouverts dans une fenêtre
  const art = $('#article');
  async function syncArticle() {
    if (!state.a) { if (art.open) art.close(); return; }
    if (art.dataset.id !== state.a) { art.dataset.id = state.a; await fillArticle(state.a); }
    if (!art.open) { art.showModal(); art.scrollTop = 0; }
  }
  async function fillArticle(id) {
    const body = $('#art-body');
    if (id === 'sommaire') {
      body.innerHTML = `<p class="eyebrow">Autour des cliparts</p><h2 id="art-title">Histoires de cliparts</h2>
        <p class="chapo">D'où viennent ces images, qui les a dessinées, et ce qu'elles sont devenues.</p>
        <div class="cards arts">${EDITO.articles.map(artCard).join('')}</div>`;
      return;
    }
    const a = ART.get(id);
    body.innerHTML = '<p class="muted">Chargement…</p>';
    try {
      const r = await fetch(`data/journal/${id}.html`);
      if (!r.ok) throw new Error(r.status);
      const when = new Date(a.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
      body.innerHTML = `<p class="eyebrow">Autour des cliparts · ${when}</p><h2 id="art-title">${esc(a.titre)}</h2><p class="chapo">${esc(a.chapo)}</p>${await r.text()}`;
    } catch { body.innerHTML = '<p>Article introuvable.</p>'; return; }
    for (const el of body.querySelectorAll('.planche')) {
      const ids = el.dataset.sel ? pick(el.dataset.sel, +el.dataset.n || 8) : el.dataset.items.split(/\s+/).map((k) => BY_KEY.get(k)).filter((i) => i != null && visible(i));
      el.innerHTML = ids.map((i) => thumb(i, '#a=' + id)).join('') + (el.dataset.sel ? `<a class="more" href="#sel=${el.dataset.sel}">Toute la sélection →</a>` : '');
    }
    // Vidéos : vignette d'abord, le lecteur YouTube (sans cookie) ne se charge qu'au clic
    for (const v of body.querySelectorAll('.video[data-yt]')) {
      v.innerHTML = `<button type="button" aria-label="Lire la vidéo ${esc(v.dataset.titre || '')}"><img src="https://i.ytimg.com/vi/${v.dataset.yt}/hqdefault.jpg" alt="" loading="lazy"><span class="play" aria-hidden="true"></span></button>`;
      v.querySelector('button').addEventListener('click', () => {
        v.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${v.dataset.yt}?autoplay=1" title="${esc(v.dataset.titre || 'Vidéo')}" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>`;
      });
    }
  }
  art.addEventListener('close', () => { if (state.a) { state.a = ''; writeHash(); } });
  // Les liens #sel=… d'un article ferment la fenêtre (le hashchange s'en charge) ; on remonte en haut de la grille
  art.addEventListener('click', (e) => { if (e.target.closest('a[href^="#sel="]')) art.close(); });

  let tt = 0;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg; t.classList.add('on');
    clearTimeout(tt); tt = setTimeout(() => t.classList.remove('on'), 1800);
  }
})();
