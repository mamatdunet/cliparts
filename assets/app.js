/* Cliparthèque — recherche et grille virtualisée sur data/index.json.
   Index : themes = [collection, dossier, nom] ; items = [thème, fichier, nom?, personnage?]. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[’']/g, ' ');
  const fmt = (n) => n.toLocaleString('fr-FR');
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* stockage indisponible */ } },
  };
  const COLL_COLOR = { '': 'var(--green)', pro: 'var(--blue)', mc: 'var(--red)', photos: 'var(--yellow)', web: 'var(--neutral-500)', szene: 'var(--ink)', imsi: 'var(--green-700)', anim: 'var(--red-700)', masterclips: 'var(--blue-700)', mphotos: 'var(--neutral-600)' };
  // Mots-clés en plus pour les types d'images web (noms anglais du CD compris)
  const KW = { boutons: 'button', icones: 'icon', puces: 'bullet', fleches: 'arrow', traits: 'ligne separateur line' };
  // Animations web : un bouton existe en 25 couleurs (même animation, même fond), un objet ou un mot en 3 fonds
  const animKey = (t, f) => THEMES[t].slug.startsWith('bouton') ? t + f[1] + f.slice(-1) : t + f.slice(0, -1);
  const LAST = new Set(['web', 'anim']);
  const COLL_IDS = ['pro', 'mc', 'photos', 'web', 'szene', 'imsi', 'anim', 'masterclips', 'mphotos'];

  let DB, ITEMS = [], THEMES = [], VARIANTS = new Map(), BY_THEME = [], EXT = {}, ADULT = new Set();
  let results = [];
  const state = { q: '', c: '', t: -1, fav: false, seed: 0, bg: store.get('bg', 'white'), size: store.get('size', 148), adult: store.get('adult', false) === true };
  const favs = new Set(store.get('favs', []));

  const grid = $('#grid');
  const rendered = new Map();
  let geo = { cols: 1, tw: 0, rowH: 1, lbl: 0 };

  // ---------- Données ----------
  fetch('data/index.json').then((r) => r.json()).then(init).catch(() => { $('#count').textContent = "Impossible de charger l'index."; });

  function init(db) {
    DB = db;
    for (const c of db.collections) EXT[c.id] = c.ext;
    ADULT = new Set(db.adult || []);
    THEMES = db.themes.map(([c, slug, nom], i) => ({ i, c: db.collections[c].id, slug, nom, key: db.collections[c].id + ':' + slug, norm: norm(nom), total: 0 }));
    ITEMS = db.items.map(([t, f, nom, v, kw], i) => {
      const th = THEMES[t];
      th.total++;
      const perso = v ? db.persos[v.toUpperCase()] || '' : '';
      const name = nom ? nom.replace(/\.$/, '') : '';
      const label = name ? name + (perso ? ' · ' + perso : '') : th.nom;
      const key = `${th.c}/${th.slug}/${f}`;
      const it = { i, t, f, name, perso, label, key, path: `cliparts/${key}.${EXT[th.c]}` };
      it.nname = norm(name);
      it.hay = norm([name, perso, th.nom, db.collections[db.themes[t][0]].nom, KW[th.slug] || '', kw || '', f].join(' '));
      // Variantes : personnages (Cliparts Pro) ou couleurs d'une même forme (images web)
      const k = th.c === 'pro' ? f.slice(0, 1) + f.slice(3) : th.c === 'web' ? t + f.slice(0, 4) : th.c === 'anim' ? animKey(t, f) : '';
      if (k) {
        if (!VARIANTS.has(k)) VARIANTS.set(k, []);
        VARIANTS.get(k).push(i);
      }
      (BY_THEME[t] ||= []).push(i);
      return it;
    });
    const open = hashItem();
    readHash();
    applyPrefs();
    renderColls();
    update();
    openFromHash(open);
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
    const th = THEMES.find((x) => x.key === p.get('t'));
    state.t = th ? th.i : -1;
    state.fav = p.get('fav') === '1';
    state.seed = +p.get('mix') || 0;
    $('#q').value = state.q;
  }
  function writeHash() {
    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.c) p.set('c', state.c);
    if (state.t >= 0) p.set('t', THEMES[state.t].key);
    if (state.fav) p.set('fav', '1');
    if (state.seed) p.set('mix', state.seed);
    if (current >= 0) p.set('i', ITEMS[current].key);
    const h = p.toString();
    history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
  }
  addEventListener('hashchange', () => {
    if (!DB) return;
    const open = hashItem();
    current = -1;
    readHash(); update(); openFromHash(open);
  });

  // ---------- Filtrage ----------
  // Les images marquées +18 ans n'apparaissent nulle part tant que l'option n'est pas activée
  const visible = (i) => state.adult || !ADULT.has(i);
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
    const byColl = { '': 0, pro: 0, mc: 0, photos: 0, web: 0, szene: 0, imsi: 0, anim: 0, masterclips: 0, mphotos: 0 };
    const byTheme = new Uint32Array(THEMES.length);
    const out = [];
    const scores = new Float32Array(ITEMS.length);
    for (const it of ITEMS) {
      if (state.fav && !favs.has(it.path)) continue;
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
      byTheme[it.t]++;
      if (state.t >= 0 && it.t !== state.t) continue;
      scores[it.i] = sc;
      out.push(it.i);
    }
    const home = !toks.length && state.t < 0 && !state.fav;
    const seed = state.seed || (home ? dailySeed() : 0);
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
    $('#fav-only').setAttribute('aria-pressed', state.fav);
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
    const list = [{ id: '', nom: 'Toutes les collections', sub: '7 CD-ROM, 1996-2003' }, ...DB.collections.map((c) => ({ id: c.id, nom: c.nom, sub: `${c.editeur.split(' (')[0]}, ${c.annee}` }))];
    box.innerHTML = list.map((c) => `<button class="coll" role="radio" type="button" data-c="${c.id}" aria-checked="${state.c === c.id}">
      <span class="dot" style="background:${COLL_COLOR[c.id]}"></span><span>${c.nom}<small>${c.sub}</small></span><span class="n">${counts ? fmt(counts[c.id]) : ''}</span></button>`).join('');
  }
  $('#colls').addEventListener('click', (e) => {
    const b = e.target.closest('.coll'); if (!b) return;
    state.c = b.dataset.c;
    if (state.t >= 0 && state.c && THEMES[state.t].c !== state.c) state.t = -1;
    update(); scrollTop();
  });

  let themeCounts = null, themeFiltered = false;
  function renderThemes(counts, filtered) {
    themeCounts = counts; themeFiltered = filtered;
    const f = norm($('#theme-filter').value.trim());
    let html = '', last = '';
    for (const th of THEMES) {
      if (state.c && th.c !== state.c) continue;
      const n = counts[th.i];
      if (!n && th.i !== state.t) continue;
      if (f && !th.norm.includes(f)) continue;
      if (!state.c && th.c !== last) {
        last = th.c;
        html += `<li class="grp">${DB.collections.find((c) => c.id === th.c).nom}</li>`;
      }
      html += `<li><button type="button" data-t="${th.i}" aria-pressed="${state.t === th.i}"><span>${th.nom}</span><span class="n">${fmt(n)}</span></button></li>`;
    }
    $('#themes').innerHTML = html || '<li class="grp">Aucun thème</li>';
  }
  $('#themes').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-t]'); if (!b) return;
    const t = +b.dataset.t;
    state.t = state.t === t ? -1 : t;
    update(); scrollTop();
    $('#side').classList.remove('open');
  });
  $('#theme-filter').addEventListener('input', () => themeCounts && renderThemes(themeCounts, themeFiltered));

  function renderChips() {
    const chips = [];
    if (state.t >= 0) chips.push(['t', THEMES[state.t].nom]);
    if (state.fav) chips.push(['fav', 'Favoris']);
    if (state.seed) chips.push(['mix', 'Mélangé']);
    $('#active').innerHTML = chips.map(([k, l]) => `<button class="chip" type="button" data-k="${k}" aria-label="Retirer le filtre ${l}">${l}<svg class="ic" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg></button>`).join('');
  }
  $('#active').addEventListener('click', (e) => {
    const b = e.target.closest('.chip'); if (!b) return;
    ({ t: () => (state.t = -1), fav: () => (state.fav = false), mix: () => (state.seed = 0) })[b.dataset.k]();
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
      const lbl = !it.name && state.t === it.t ? 'n° ' + it.f.replace(/^\D+/, '') : it.label;
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
    deb = setTimeout(() => { state.q = e.target.value.trim(); state.seed = 0; update(); scrollTop(); }, 90);
  });
  $('#fav-only').addEventListener('click', () => { state.fav = !state.fav; update(); scrollTop(); });
  $('#shuffle').addEventListener('click', () => { state.seed = 1 + Math.floor(Math.random() * 1e6); update(); scrollTop(); });
  $('#reset').addEventListener('click', () => { Object.assign(state, { q: '', c: '', t: -1, fav: false, seed: 0 }); $('#q').value = ''; $('#theme-filter').value = ''; update(); });
  $('#size').addEventListener('input', (e) => { state.size = +e.target.value; store.set('size', state.size); layout(); });
  $('#bg').addEventListener('click', (e) => { const b = e.target.closest('[data-bg]'); if (b) { state.bg = b.dataset.bg; store.set('bg', state.bg); applyPrefs(); } });
  $('#show-side').addEventListener('click', () => $('#side').classList.add('open'));
  $('#close-side').addEventListener('click', () => $('#side').classList.remove('open'));
  $('#about-btn').addEventListener('click', () => $('#about').showModal());
  $('#adult').addEventListener('change', (e) => {
    state.adult = e.target.checked;
    store.set('adult', state.adult);
    if (state.t >= 0 && !BY_THEME[state.t].some(visible)) state.t = -1;
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
  });

  // ---------- Fiche détaillée ----------
  const dlg = $('#detail');
  let current = -1;
  function openDetail(i) {
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
      `<button class="tag" type="button" data-act="theme">${esc(th.nom)}</button>`,
      it.perso ? `<button class="tag" type="button" data-act="perso">avec ${esc(it.perso)}</button>` : '',
      th.c === 'web' ? `<span class="tag file">forme ${it.f.slice(0, 4)} · couleur ${+it.f.slice(5)}</span>` : '',
      `<span class="tag file" id="d-file">${it.f}.${EXT[th.c]}</span>`,
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
    setFav(it);
    // Variantes (Cliparts Pro) ou voisins dans le thème (Micro Application)
    let rel, title;
    if (th.c === 'pro') { rel = VARIANTS.get(it.f.slice(0, 1) + it.f.slice(3)) || []; title = 'Toutes les variantes'; }
    else if (th.c === 'web') { rel = VARIANTS.get(it.t + it.f.slice(0, 4)) || []; title = 'Toutes les couleurs'; }
    else if (th.c === 'anim') { rel = VARIANTS.get(animKey(it.t, it.f)) || []; title = THEMES[it.t].slug.startsWith('bouton') ? 'Toutes les couleurs' : 'Tous les fonds'; }
    else {
      const list = BY_THEME[it.t], k = list.indexOf(i), s = Math.max(0, Math.min(list.length - 14, k - 7));
      rel = list.slice(s, s + 14); title = 'Dans le même thème';
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
    if (b.dataset.act === 'coll') { state.c = th.c; state.t = -1; }
    if (b.dataset.act === 'theme') { state.c = th.c; state.t = th.i; state.q = ''; }
    if (b.dataset.act === 'perso') { state.q = it.perso; state.c = 'pro'; state.t = -1; }
    state.seed = 0;
    $('#q').value = state.q;
    dlg.close(); update(); scrollTop();
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
      const txt = await (await fetch(ITEMS[current].path)).text();
      await navigator.clipboard.writeText(txt);
      toast('SVG copié dans le presse-papiers');
    } catch { toast('Copie impossible dans ce navigateur'); }
  });
  $('#d-png').addEventListener('click', async () => {
    const it = ITEMS[current], size = +$('#d-png-size').value;
    try {
      const txt = await (await fetch(it.path)).text();
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
      cv.toBlob((blob) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${fileBase(it)}-${size}px.png`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      }, 'image/png');
    } catch { toast("L'export PNG a échoué"); }
  });

  let tt = 0;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg; t.classList.add('on');
    clearTimeout(tt); tt = setTimeout(() => t.classList.remove('on'), 1800);
  }
})();
