"""Convertit les cliparts WMF du CD 1 d'IMSI « ClipArt & More 2.5 Million » en SVG dans cliparts/imsi.
Usage : python3 tools/build_imsi.py <dossier CLIPART extrait de ClipaArt&More_2.5M_CD1_WIN.iso>
Les dossiers et les mots-clés les plus fréquents sont traduits par tools/imsi_fr.json ; les mots-clés
anglais du CD (KEYWORDS.TXT) restent dans le catalogue pour la recherche."""
import sys, os, json, re, hashlib, shlex, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wmf
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
dst = os.path.join(root, 'cliparts/imsi')
FR = json.load(open(os.path.join(root, 'tools/imsi_fr.json')))

def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def fr(folder):
    return FR['folders'].get(folder) or folder.replace('_NEW_', '').replace('_', ' ').strip().capitalize()

def keywords(s):
    """« a, "b c", d » ou « a b c » → liste de mots-clés en minuscules."""
    s = s.replace('\x00', ' ').strip()
    try:
        parts = [p.strip(' "') for p in s.split(',')] if ',' in s else shlex.split(s)
    except ValueError:
        parts = s.replace('"', ' ').split()
    return [p.lower() for p in parts if p.strip()]

themes, items, seen, fails, dups = {}, [], set(), [], 0
for r, dirs, files in sorted(os.walk(src)):
    dirs.sort()
    rel = os.path.relpath(r, src).split(os.sep)
    wmfs = sorted(f for f in files if f.lower().endswith('.wmf'))
    if len(rel) < 2 or not wmfs:
        continue
    kw = {}
    for name in ('KEYWORDS.TXT', 'keywords.txt'):
        p = os.path.join(r, name)
        if os.path.exists(p):
            for line in open(p, encoding='latin-1'):
                if '\t' in line:
                    f, k = line.split('\t', 1)
                    kw[f.strip().lower()] = keywords(k)
            break
    top, l2 = rel[0], rel[1]
    k = slug(fr(l2))
    themes.setdefault(k, (fr(l2), fr(top)))
    nom = fr(rel[-1])
    for f in wmfs:
        p = os.path.join(r, f)
        h = hashlib.md5(open(p, 'rb').read()).hexdigest()
        if h in seen:
            dups += 1; continue
        seen.add(h)
        try:
            svg = wmf.to_svg(p, True)
        except Exception as e:
            fails.append((p, repr(e))); continue
        n = f[:-4].lower()
        os.makedirs(os.path.join(dst, k), exist_ok=True)
        open(os.path.join(dst, k, n + '.svg'), 'w').write(svg)
        en = kw.get(f.lower(), [])
        words = []
        for w in [FR['keywords'].get(x, '') for x in en] + en:
            for t in w.split():
                if t not in words:
                    words.append(t)
        items.append([k, n, nom, ' '.join(words)])
order = sorted(themes, key=lambda k: slug(themes[k][0]))
idx = {k: i for i, k in enumerate(order)}
json.dump({'source': 'ClipArt & More 2.5 Million (IMSI, 2003), CD 1, converti depuis WMF',
           'chemin': 'cliparts/imsi/{dossier}/{n}.svg', 'themes': [[k, themes[k][0], themes[k][1]] for k in order],
           'items': [[idx[k], n, nom, w] for k, n, nom, w in items]},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('imsi', len(items), 'themes', len(order), 'dups', dups, 'fails', len(fails), fails[:5])
