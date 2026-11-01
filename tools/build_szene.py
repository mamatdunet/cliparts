"""Convertit les images PCX du CD Szene-Cliparts (2001) en PNG dans cliparts/szene.
Usage : python3 tools/build_szene.py <dossier GRAPHICS extrait de l'ISO>   (nécessite Pillow)
Les images listées dans tools/szene_adult.json (nudité, contenu suggestif) sont marquées « 18 » :
le site ne les montre qu'une fois l'option +18 ans activée."""
import sys, os, json, re, hashlib
from PIL import Image
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
dst = os.path.join(root, 'cliparts/szene')
adult = set(json.load(open(os.path.join(root, 'tools/szene_adult.json'))))
THEMES = {'ANIMALS': ('animaux', 'Animaux'), 'COMIC': ('bd', 'Bande dessinée'), 'FACES': ('visages', 'Visages'),
          'FANTASY': ('fantasy', 'Fantasy'), 'FONTS': ('polices', 'Polices bitmap'), 'GIRLS': ('pin-up', 'Pin-up'),
          'LANDSCAP': ('paysages', 'Paysages'), 'LOGOS': ('logos', 'Logos de groupes'), 'MIXED': ('divers', 'Divers'),
          'OBJECTS': ('objets', 'Objets'), 'PERSONS': ('personnages', 'Personnages'), 'SCENE': ('scenes', 'Scènes'),
          'SCENES': ('scenes', 'Scènes'), 'SCIFI': ('science-fiction', 'Science-fiction'),
          'SURREAL': ('surrealisme', 'Surréalisme'), 'TEXTURE': ('textures', 'Textures')}

def name_of(rel):
    """Nom lisible : le groupe pour les logos, sinon le nom de fichier débarrassé des numéros."""
    parts = rel.split('/')
    if parts[0] == 'LOGOS' and len(parts) > 2 and parts[1] != 'OTHERS':
        return {'_DSKMAGS': 'Diskmag'}.get(parts[1], parts[1].replace('_', ' ').strip().title())
    s = re.sub(r'[\d_\-]+', ' ', parts[-1][:-4]).strip()
    return s.title() if len(s) > 2 else ''

order = sorted({v for v in THEMES.values()}, key=lambda v: v[0])
tidx = {k: i for i, (k, _) in enumerate(order)}
items, seen, used = [], set(), set()
for r, _, files in sorted(os.walk(src)):
    for f in sorted(files):
        if not f.lower().endswith('.pcx'):
            continue
        p = os.path.join(r, f); rel = os.path.relpath(p, src).replace(os.sep, '/')
        h = hashlib.md5(open(p, 'rb').read()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        k = THEMES[rel.split('/')[0]][0]
        base = re.sub(r'[^a-z0-9]+', '-', rel.split('/', 1)[1][:-4].lower()).strip('-')
        n = base; i = 2
        while (k, n) in used:
            n = f'{base}-{i}'; i += 1
        used.add((k, n))
        os.makedirs(os.path.join(dst, k), exist_ok=True)
        im = Image.open(p)
        if im.mode not in ('P', 'L', 'RGB'):
            im = im.convert('RGB')
        im.save(os.path.join(dst, k, n + '.png'), optimize=True)
        items.append([tidx[k], n, name_of(rel)] + ([1] if rel in adult else []))
json.dump({'source': 'Szene-Cliparts (E.D.V. CD-ROM GmbH, 2001), dossier GRAPHICS, converti depuis PCX',
           'chemin': 'cliparts/szene/{dossier}/{n}.png', 'themes': [list(t) for t in order], 'items': items},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('szene', len(items), 'adult', sum(len(x) > 3 for x in items))
