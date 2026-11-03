"""Extrait les images du CD « Print Artist Gold » (Sierra, 1998, réf. UK_PA4) en trois collections.
Usage : python3 tools/build_printartist.py <racine extraite de UK_PA4.ISO>   (numpy et Pillow requis)

- printartist : les dessins vectoriels des bibliothèques GFX/*.GFX, en SVG, un fichier par jeu de couleurs ;
- paphotos : les photos et images JPG/*.JPG, reprises telles quelles ;
- photoartist : les images détourées (TIF) de la démo de Photo Artist, en PNG.

Format GFX (retrouvé en lisant les fichiers, tout est vérifié à la lecture) : magic F00D, nombre d'entrées, puis pour
chaque entrée : position (u32), type (u16 : 2 = dessin, 512 = nom de la bibliothèque), 2 u16, 0, longueur du nom en
mots (u8), nom. Un dessin : taille en mots (u32), puis en big endian largeur, hauteur, nombre de formes, nombre de
jeux de couleurs (u8), jeu par défaut (u8), longueur des noms de jeux (u16), 0 (u16), noms. Une forme : code (bit 0 =
rempli, 1 = contour, 2 = fermé) ; si contour : épaisseur (u16) et une couleur par jeu ; si rempli : une couleur par
jeu ; longueur (u16), nombre de points (u16), points sur 3 octets (x, y, puis les 4 bits faibles de chacun : 12 bits,
de 0 à 4095 sur tout le dessin), segments sur 1 octet (5 bits : nombre ; 0x20 = droites, sinon courbes de Bézier ;
0x40 = nouveau tracé). Les couleurs sont les indices de la palette de 256 teintes rangée dans System/Data/Pixtype.dll.

Mots-clés (System/Data/C?[gka].pkw et CH?.PKW, compressés en SZDD) : les noms des images (Cdg), les mots-clés (Cdk) et
les paires mot-clé/image (Cda). Les numéros d'images ne suivent pas tout à fait l'ordre de la liste des noms ; aligner() retrouve le décalage."""
import sys, os, re, json, struct, shutil, collections, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_openclipart import rubrique as classer, FR, NOMS, SLUGS
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
iso = sys.argv[1]
DATA = os.path.join(iso, 'System/Data')


def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


# ---------- Format GFX ----------
def repertoire(b):
    assert b[:2] == b'\xf0\x0d'
    pos, out = 6, []
    for _ in range(struct.unpack('<H', b[4:6])[0]):
        off, typ, _a, _c, _z, w = struct.unpack('<IHHHBB', b[pos:pos + 12]); pos += 12
        out.append((off, typ, b[pos:pos + w * 2].split(b'\0')[0].decode('cp1252').strip())); pos += w * 2
    return out


def dessin(b, o):
    w, h, n = struct.unpack('>HHH', b[o + 4:o + 10])
    nj, defaut, nl = b[o + 10], b[o + 11], struct.unpack('>H', b[o + 12:o + 14])[0]
    jeux = [x.decode('cp1252').strip() for x in b[o + 16:o + 16 + nl].split(b'\0')[:nj]]
    p, formes = o + 16 + nl, []
    for _ in range(n):
        code = b[p]; p += 1; ep = 0; trait = fond = None
        if code & 2:
            ep = struct.unpack('>H', b[p:p + 2])[0]; p += 2
            trait = b[p:p + nj]; p += nj
        if code & 1:
            fond = b[p:p + nj]; p += nj
        ln, np_ = struct.unpack('>HH', b[p:p + 4])
        pts = [((b[q] << 4) | (b[q + 2] >> 4), (b[q + 1] << 4) | (b[q + 2] & 15)) for q in range(p + 4, p + 4 + np_ * 3, 3)]
        segs = b[p + 4 + np_ * 3:p + 2 + ln]
        p += 2 + ln
        formes.append((code, ep, trait, fond, pts, segs))
    return w, h, jeux, defaut, formes


def tracer(pts, segs, kx, ky):
    P = lambda p: f'{round(p[0] * kx)} {round(p[1] * ky)}'
    i, d = 0, []
    for s in segs:
        if s & 0x40 or i == 0:
            d.append('M' + P(pts[i])); i += 1
        if s & 0x20:
            for _ in range(s & 31):
                d.append('L' + P(pts[i])); i += 1
        else:
            for _ in range(s & 31):
                d.append('C' + P(pts[i]) + ' ' + P(pts[i + 1]) + ' ' + P(pts[i + 2])); i += 3
    assert i == len(pts)
    return ''.join(d)


def svg(w, h, formes, jeu, PAL):
    kx, ky = (1, h / w) if w >= h else (w / h, 1)
    marge = max([f[1] for f in formes if f[2] is not None] + [4]) // 2 + 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-marge} {-marge} {round(4095 * kx) + 2 * marge} {round(4095 * ky) + 2 * marge}" '
           'stroke-linejoin="round" stroke-linecap="round" fill-rule="evenodd">']
    for code, ep, trait, fond, pts, segs in formes:
        d = tracer(pts, segs, kx, ky) + ('Z' if code & 4 else '')
        a = f'fill="{PAL[fond[jeu]]}"' if fond is not None and fond[jeu] else 'fill="none"'
        if trait is not None and trait[jeu]:
            a += f' stroke="{PAL[trait[jeu]]}" stroke-width="{max(ep, 4)}"'
        out.append(f'<path {a} d="{d}"/>')
    return ''.join(out) + '</svg>'


# ---------- Mots-clés ----------
def lire(nom):
    b = open(os.path.join(DATA, nom), 'rb').read()
    if b[:4] != b'SZDD':
        return b
    # Compression SZDD (LZSS sur une fenêtre de 4 096 octets)
    n, p, fen, fp, o = struct.unpack('<I', b[10:14])[0], 14, bytearray(b' ' * 4096), 4080, bytearray()
    while p < len(b) and len(o) < n:
        f = b[p]; p += 1
        for i in range(8):
            if p >= len(b): break
            if f >> i & 1:
                c = b[p]; p += 1; o.append(c); fen[fp] = c; fp = (fp + 1) & 4095
            else:
                a, l = b[p], b[p + 1]; p += 2
                for j in range((l & 15) + 3):
                    c = fen[(a | (l & 0xf0) << 4) + j & 4095]; o.append(c); fen[fp] = c; fp = (fp + 1) & 4095
    return bytes(o)


def mots_cles():
    """Mots-clés de chaque image du catalogue : {numéro : [mots]} et la liste [(nom, numéro de bibliothèque)]."""
    g, k, a, ha, hk = (lire(f) for f in ('Cdg.pkw', 'Cdk.pkw', 'Cda.pkw', 'CHA.PKW', 'CHK.PKW'))
    p, G = 4, []
    while p < len(g):
        e = g.find(b'\0', p); G.append((g[p:e].decode('cp1252').strip(), struct.unpack('<H', g[e + 1:e + 3])[0])); p = e + 3
    K = [x.decode('cp1252') for x in k[4:].split(b'\0')]
    code = {h: o for o, h in (struct.unpack('<HH', hk[i:i + 4]) for i in range(4, len(hk) - 3, 4))}
    ligne = {r: K[code[h]] for h, r in (struct.unpack('<II', ha[i:i + 8]) for i in range(4, len(ha) - 7, 8))}
    par_num = collections.defaultdict(list)
    for i, r in enumerate(range(4, len(a) - 3, 4)):
        par_num[struct.unpack('<H', a[r + 2:r + 4])[0]].append(ligne[i])
    return G, dict(par_num)


def aligner(G, par_num, jpg, biblios):
    """Le numéro d'une image = sa place dans G + un décalage qui ne fait que croître. On cherche la suite de décalages
    qui fait le plus souvent coïncider le nom de l'image et ses mots-clés (programmation dynamique)."""
    import numpy as np
    D0, D1, SAUT = 700, 8100, 1.5
    tok, bib, en_jpg = {}, collections.defaultdict(set), set()
    for y, ks in par_num.items():
        for m in ks:
            for w in re.findall('[a-z]{3,}', m.lower()):
                tok.setdefault(w[:4], set()).add(y)
            if m.startswith('^'):
                bib[re.sub(r'\s+', ' ', m[1:]).lower()].add(y)
                if m == '^JPEG Bitmap Files': en_jpg.add(y)
    N = D1 - D0
    best, par = np.zeros(N), np.zeros((len(G), N), dtype=np.int16)
    idx = np.arange(N)
    for i, (n, _) in enumerate(G):
        cm = np.maximum.accumulate(best)
        am = np.maximum.accumulate(np.where(np.r_[True, best[1:] > cm[:-1]], idx, 0))
        alt, altp = np.r_[-1e9, cm[:-1]] - SAUT, np.r_[0, am[:-1]]
        reste = best >= alt
        best, par[i] = np.where(reste, best, alt), np.where(reste, idx, altp)
        ys = collections.Counter()
        for w in re.findall('[a-z]{3,}', n.lower()):
            ys.update(tok.get(w[:4], ()))
        if n in jpg:
            ys.update({y: 2 for y in en_jpg})
        for L in biblios.get(n, ()):
            ys.update({y: 2 for y in bib.get(re.sub(r'\s+', ' ', L).lower(), ())})
        for y, v in ys.items():
            if 0 <= y - i - D0 < N: best[y - i - D0] += v
    d, num = int(best.argmax()), [0] * len(G)
    for i in range(len(G) - 1, -1, -1):
        num[i] = i + d + D0; d = int(par[i][d])
    return num


# Mots-clés du CD commençant par « ^ » (bibliothèque ou sujet) → un mot de TAGS (tools/build_openclipart.py) qui oriente le classement
SUJETS = {'animals': 'animal', 'flora': 'flora', 'agriculture': 'farm', 'food': 'food', 'sports': 'sport', 'holidays': 'christmas', 'seasons': 'christmas',
          'special occasions': 'birthday', 'occasion': 'birthday', 'people, families': 'family', 'people, professional': 'job', 'people': 'people',
          'vehicles': 'vehicle', 'transportation': 'transport', 'home': 'furniture', 'music': 'music', 'education': 'school',
          'business, currency': 'money', 'business': 'office', 'office': 'office', 'tools': 'tools', 'construction': 'tools',
          'toys': 'toy', 'places': 'building', 'real estate': 'house', 'religion': 'religion', 'borders': 'border', 'backgrounds': 'background', 'fractal': 'background',
          'labels': 'label', 'icons': 'icon', 'shapes, arrows': 'arrow', 'shapes': 'shape', 'flags': 'flag', 'maps': 'map', 'medical': 'medical', 'health': 'medical',
          't18': 'medical', 'military': 'military', 'signs, zodiac': 'symbol', 'signs': 'sign', 'astrology': 'symbol', 'humor': 'humor', 'symbols': 'symbol',
          'entertainment': 'game', 'americana, landmark': 'landmark', 'technology': 'technology', 'textiles': 'pattern', 'victorian': 'vintage', 'audio video': 'television',
          'sports action': 'sport', 't12': 'sport', 't11': 'bird', 't8': 'fish', 't16': 'insect', 't5': 'border', 't4': 'animal', 't10': 'animal', 't1': 'christmas',
          't6': 'woman', 't9': 'food', 't15': 'tools', 't17': 'job', 't3': 'school', 't2': 'office', 't14': 'travel', 't13': 'bird', 't7': 'boat'}
SUJETS = sorted(SUJETS.items(), key=lambda kv: -len(kv[0]))
# Bibliothèques sans mots-clés : leur fichier donne le sujet (TANIMALS, GFLORA…)
FICHIERS = {'ANIMALS': 'animal', 'ART': 'painting', 'ASTRO': 'star', 'AUDIOVI': 'television', 'BACK': 'background', 'BORDERS': 'border', 'EDUCATI': 'school', 'FLORA': 'flora',
            'FOOD': 'food', 'HOME': 'furniture', 'ICONS': 'icon', 'MUSIC': 'music', 'OCCASIO': 'birthday', 'OFFICE': 'office', 'PEOPLE': 'people', 'PLACES': 'building',
            'SPORTS': 'sport', 'SYMBOLS': 'symbol', 'TOOLS': 'tools', 'TOYS': 'toy', 'VEHICLE': 'vehicle'}


def fiche(mots, nom, fichier=''):
    """(rubrique, mots-clés de recherche) d'une image, d'après les mots-clés du CD."""
    tags, sujets, extra = [], [], []
    for m in mots:
        if not m.startswith('^'):
            tags.append(m.lower()); continue
        s = re.sub(r'\s+', ' ', m[1:]).replace(' (P)', '').strip()
        for prefixe, w in SUJETS:
            if s.lower().startswith(prefixe):
                sujets.append(w); break
        if not re.match(r'(?i)t\d|psd |jpeg|bmp ', s):
            extra.extend(s.replace('/', ' ').split())
    fich = fichier.upper()[1:] if fichier[:1].upper() in 'TGK' else fichier.upper()
    if fich in FICHIERS: sujets.append(FICHIERS[fich])
    words = []
    for w in [FR.get(x, '') for x in tags] + tags + extra:
        for x in w.lower().split():
            if x not in words: words.append(x)
    return classer(tags + sujets + sujets, nom), ' '.join(words)


def ecrire(id_, source, ext, items):
    dst = os.path.join(root, 'cliparts', id_)
    themes = sorted({it[0] for it in items}, key=lambda t: SLUGS.index(t))
    tidx = {t: i for i, t in enumerate(themes)}
    json.dump({'source': source, 'chemin': f'cliparts/{id_}/{{dossier}}/{{n}}.{ext}', 'themes': [[t, NOMS[t]] for t in themes],
               'items': [[tidx[it[0]]] + it[1:] for it in items]},
              open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(id_, len(items), 'images', len(themes), 'thèmes')


def vider(id_):
    d = os.path.join(root, 'cliparts', id_)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    return d


# ---------- Dessins GFX ----------
pal = open(os.path.join(DATA, 'Pixtype.dll'), 'rb').read()[0x2e01d:0x2e01d + 768]
assert pal[3:6] == b'\xff\xff\xff' and pal[51:54] == b'\0\0\0'  # 1 = blanc, 17 = noir
PAL = ['#%02x%02x%02x' % tuple(pal[i * 3:i * 3 + 3]) for i in range(256)]
gfx_dir = os.path.join(iso, 'GFX'); jpg_dir = os.path.join(iso, 'JPG')
FICHS = {f: open(os.path.join(gfx_dir, f), 'rb').read() for f in sorted(os.listdir(gfx_dir)) if f.upper() not in ('_SYSTEM.GFX', 'BASICS.GFX')}
biblios = collections.defaultdict(set)
for f, b in FICHS.items():
    rep = repertoire(b)
    L = [n for _, t, n in rep if t == 512]
    for _, t, n in rep:
        if t == 2: biblios[n].update(L)
jpgs = {os.path.splitext(f)[0]: f for f in os.listdir(jpg_dir)}
G, par_num = mots_cles()
num = aligner(G, par_num, jpgs, biblios)
# Un même nom peut revenir d'une bibliothèque à l'autre : on prend alors la place du catalogue dont la bibliothèque correspond
places = collections.defaultdict(list)
for i, (n, _) in enumerate(G):
    places[n].append(i)
def mots_de(nom, biblio=None):
    pl = places.get(nom, [])
    if biblio and len(pl) > 1:
        cle = re.sub(r'\s+', ' ', biblio).lower()
        for i in pl:
            if any(m.startswith('^') and re.sub(r'\s+', ' ', m[1:]).lower() == cle for m in par_num.get(num[i], [])):
                return par_num[num[i]]
    return par_num.get(num[pl[0]], []) if pl else []

# ---------- Menu d'origine : la fenêtre « Graphics Grabber » du logiciel ----------
# Bibliothèques d'après le tableau « GFX File and JPEG Image Collections » de l'aide (Pawin.hlp) : fichier GFX → (catégorie, éditeur)
BIBLIOS = {}
for noms, fichiers, editeur in (
        ('Small Business', (314, 315), 'Instant Image'), ('Sports Action', (316, 317), 'Focus'), ('Focus', (320,), 'Focus'),
        ('ProArt', (321, 322, 323, 324, 325, 326, 333, 335, 351, 353), 'Multi Ad Services'),
        ('Contemporary', (327, 334, 342, 349, 352, 355, 361, 365), 'M&M Data Systems'),
        ('Modern Woodcuts', (328, 341, 354, 360, 362, 363, 364), 'M&M Data Systems'),
        ('Sierra', (329, 359, 366), 'Sierra'), ('Classic Woodcuts', (330, 331, 348, 358), 'Scan This Book')):
    for rang, f in enumerate(fichiers, 1):
        BIBLIOS[str(f)] = (f'{noms} {rang}' if len(fichiers) > 1 else noms, editeur)
BIBLIOS.update({'332': ('Country', 'Kay Craig'), '343': ('Doodlers (P)', 'DJ Inkers'), '367': ('TNT', 'TNT Designs')})
EDITEURS = {'Photos 1/Produktum': 'Produktum AB', 'Photos 1-4/Aztech New Media': 'Aztech New Media', 'Photos5 & 6/Tom Kelley Studios (P)': 'Tom Kelley Studios',
            'Photos 7/Digital Media Prod. (P)': 'Digital Media Productions', 'Textiles/Digital Design Collect. (P)': 'The Digital Design Collection (The Meller Archive)',
            'Victorian/The Gifted Line (P)': 'The Gifted Line (John Grossman Collection of Antique Images)', 'Sierra Art': 'Sierra', 'Sierra Art/Tracy Tattro (P)': 'Tracey Tatro',
            **dict(BIBLIOS.values())}
PHOTOS = {k for k in EDITEURS if re.match('Photos|Textiles|Victorian|Sierra Art', k)}
# Bibliothèques sans catégorie dans le catalogue : leur fichier la donne (les « file groups » de Cdf.pkw)
GROUPES = {'ANIMALS': 'Animals', 'ART': 'Art', 'ASTRO': 'Astrology', 'AUDIOVI': 'audio video', 'BACK': 'Backgrounds', 'BORDERS': 'Borders', 'EDUCATI': 'Education', 'FLORA': 'Flora',
           'FOOD': 'Food', 'HOME': 'Home', 'ICONS': 'Icons/Accents', 'MUSIC': 'Music', 'OCCASIO': 'Occasion', 'OFFICE': 'Office', 'PEOPLE': 'People', 'PLACES': 'Places',
           'SPORTS': 'Sports', 'SYMBOLS': 'Symbols', 'TOOLS': 'Tools', 'TOYS': 'Toys', 'VEHICLE': 'Vehicles'}
ECARTES = re.compile(r'(?i)t\d|jpeg |bmp |print artist bonus')


def categories(mots, fichier=None):
    """Catégories du Graphics Grabber d'une image. fichier = bibliothèque GFX, None pour une photo."""
    biblio = BIBLIOS.get(fichier)
    cats = {biblio[0]} if biblio else set()
    for m in mots:
        if not m.startswith('^'): continue
        s = re.sub(r'\s+', ' ', m[1:]).strip()
        # L'alignement du catalogue n'est pas parfait : une bibliothèque ou une série de photos ne vaut que pour ses propres fichiers
        if ECARTES.match(s) or (s in EDITEURS and not (s in PHOTOS if fichier is None else biblio and s == biblio[0])): continue
        cats.add(s)
    if not cats and fichier:
        g = GROUPES.get(fichier.upper()[1:] if fichier[:1].upper() in 'TGK' else fichier.upper())
        if g: cats.add(g)
    return cats


def ecrire_menu(images):
    """data/menus/printartist.json : les images par ordre alphabétique de nom, et pour chaque catégorie les rangs de ses images."""
    images.sort(key=lambda x: (x[2].casefold(), x[1]))
    par_cat = collections.defaultdict(list)
    for r, (_, _, _, cats) in enumerate(images):
        for c in cats: par_cat[c].append(r)
    colls = ['printartist', 'paphotos']
    d = os.path.join(root, 'data', 'menus'); os.makedirs(d, exist_ok=True)
    json.dump({'collections': colls, 'titre': 'Categories', 'note': 'Le classement de Print Artist 4.0 Plus, avec ses noms anglais et son ordre alphabétique.',
               'alpha': True, 'logiciel': 'Print Artist 4.0 Plus', 'fenetre': 'Graphics Grabber',
               'images': [[colls.index(c), n, nom] for c, n, nom, _ in images],
               'categories': [{'nom': c, 'editeur': EDITEURS.get(c, ''), 'images': par_cat[c]} for c in sorted(par_cat, key=str.casefold)]},
              open(os.path.join(d, 'printartist.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print('menu', len(images), 'images', len(par_cat), 'catégories')


menu = []
dst = vider('printartist')
items, vus, ecarts, poids = [], set(), 0, 0
for f, b in FICHS.items():
    court = os.path.splitext(f)[0]
    rep = repertoire(b)
    L = next((n for _, t, n in rep if t == 512), None)
    for off, t, nom in rep:
        if t != 2 or off + 16 > len(b) or nom.startswith('~'):
            continue
        w, h, jeux, defaut, formes = dessin(b, off)
        if not formes or not w or not h:
            ecarts += 1; continue
        r, kw = fiche(mots_de(nom, L), nom, court)
        base = f'{court.lower()}_{slug(nom)}'
        i = 2
        while base in vus:
            base = f'{court.lower()}_{slug(nom)}-{i}'; i += 1
        vus.add(base)
        defaut = defaut if defaut < len(jeux) else 0
        os.makedirs(os.path.join(dst, r), exist_ok=True)
        for j, jeu in enumerate(jeux):
            n = base if j == defaut else f'{base}_{slug(jeu)}'
            texte = svg(w, h, formes, j, PAL)
            poids += len(texte)
            open(os.path.join(dst, r, n + '.svg'), 'w').write(texte)
            if j == defaut: menu.append(['printartist', n, nom, categories(mots_de(nom, L), court)])
            nom_j = nom if j == defaut else f'{nom} ({jeu})'
            kw_j = kw if j == defaut else ' '.join(filter(None, [kw, FR.get(jeu.lower(), ''), jeu.lower()]))
            items.append([r, n, nom_j, kw_j])
print('écartés', ecarts, 'poids', poids // 1000000, 'Mo')
ecrire('printartist', 'Print Artist Gold (Sierra, 1998), dossier GFX, converti en SVG', 'svg', items)

# ---------- Photos JPG ----------
dst = vider('paphotos')
items = []
for base, f in sorted(jpgs.items()):
    nom = base.replace('_', ' ').title()
    r, kw = fiche(mots_de(base), nom)
    n = base.lower()
    os.makedirs(os.path.join(dst, r), exist_ok=True)
    shutil.copyfile(os.path.join(jpg_dir, f), os.path.join(dst, r, n + '.jpg'))
    items.append([r, n, nom, kw])
    menu.append(['paphotos', n, nom, categories(mots_de(base))])
ecrire('paphotos', 'Print Artist Gold (Sierra, 1998), dossier JPG', 'jpg', items)
ecrire_menu(menu)

# ---------- Images détourées de la démo de Photo Artist ----------
from PIL import Image
PA = {'Alphabet': 'Alphabet illustré', 'Animals': 'Animaux', 'Bubbles': 'Bulles de BD', 'CanFrame': 'Cadres', 'Food': 'Cuisine', 'Holidays': 'Fêtes',
      'Misc': 'Divers', 'Office': 'Bureau', 'Plates': 'Plaques', 'Space': 'Espace', 'Sports': 'Sports', 'Symbols': 'Symboles', 'Trans': 'Transports'}
src = os.path.join(iso, 'Demos/Photo Artist/DATA/Content/Clipart')
dst = vider('photoartist')
themes, items = {}, []
for top in sorted(PA):
    k = slug(PA[top]); themes[k] = PA[top]
    os.makedirs(os.path.join(dst, k), exist_ok=True)
    for d, _, fs in sorted(os.walk(os.path.join(src, top))):
        for f in sorted(fs):
            if f.lower().endswith('.tif'):
                n = f[:-4].lower()
                if os.path.exists(os.path.join(dst, k, n + '.png')):
                    n = f'{os.path.basename(d).lower()}-{n}'
                Image.open(os.path.join(d, f)).save(os.path.join(dst, k, n + '.png'), optimize=True)
                items.append([k, n])
order = sorted(themes)
idx = {k: i for i, k in enumerate(order)}
json.dump({'source': 'Photo Artist (démo sur le CD de Print Artist Gold, Sierra, 1998), TIF convertis en PNG', 'chemin': 'cliparts/photoartist/{dossier}/{n}.png',
           'themes': [[k, themes[k]] for k in order], 'items': [[idx[k], n] for k, n in items]},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('photoartist', len(items), 'images', len(order), 'thèmes')
