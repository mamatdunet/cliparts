"""Copie les photos et les images Web du CD Micro Application (4366MC) dans cliparts/photos et cliparts/web.
Usage : python3 tools/build_extras.py <dossier extrait de l'ISO contenant Photos/ et WebGen/>"""
import sys, os, json, re, shutil, hashlib, unicodedata
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
# Quelques dossiers photo restés en anglais sur le CD
RENAME = {'Arthropods': 'Arthropodes', 'Artist Textures': "Textures d'artiste", 'Beautiful Roses': 'Belles roses',
          'Backgrounds I': 'Fonds I', 'Barbecue & Salads': 'Barbecue et salades', 'Red': 'Rouge',
          'Cuisiens Internationale': 'Cuisine internationale', 'Les décors  grecs': 'Les décors grecs'}
WEB = [('Buttons', 'boutons', 'Boutons', 'Bouton'), ('Icons', 'icones', 'Icônes', 'Icône'),
       ('Bullets', 'puces', 'Puces', 'Puce'), ('arrows', 'fleches', 'Flèches', 'Flèche'),
       ('Lines', 'traits', 'Traits de séparation', 'Trait')]

def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def nice(s):
    s = unicodedata.normalize('NFC', s).replace('’', "'")
    s = RENAME.get(s, s)
    for k, v in RENAME.items():
        s = s.replace(k, v)
    return s[:1].upper() + s[1:]

# Photos : un thème par dossier (le plus profond quand le CD en a imbriqué)
dst = os.path.join(root, 'cliparts/photos')
themes, items, seen = {}, [], set()
for r, _, files in sorted(os.walk(os.path.join(src, 'Photos'))):
    jpgs = sorted(f for f in files if f.lower().endswith('.jpg'))
    if not jpgs:
        continue
    nom = nice(os.path.basename(r)); k = slug(nom)
    for f in jpgs:
        p = os.path.join(r, f)
        h = hashlib.md5(open(p, 'rb').read()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        os.makedirs(os.path.join(dst, k), exist_ok=True)
        n = f[:-4].lower()
        shutil.copyfile(p, os.path.join(dst, k, n + '.jpg'))
        themes.setdefault(k, nom); items.append([k, n])
order = sorted(themes, key=lambda k: slug(themes[k]).removeprefix('les-').removeprefix('le-').removeprefix('la-').removeprefix('l-'))
idx = {k: i for i, k in enumerate(order)}
json.dump({'source': 'Plus de 50 000 Cliparts Volume 1 (Micro Application, réf. 4366MC, 2002), dossier Photos',
           'chemin': 'cliparts/photos/{dossier}/{n}.jpg', 'themes': [[k, themes[k]] for k in order],
           'items': [[idx[k], n] for k, n in items]},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('photos', len(items), 'themes', len(order))

# Images Web (Hemera) : <forme 4 car.><type><couleur 3 car.>.gif, 10 couleurs par forme
dst = os.path.join(root, 'cliparts/web')
cat = {'source': 'Plus de 50 000 Cliparts Volume 1 (Micro Application, réf. 4366MC, 2002), dossier WebGen (Hemera Technologies, 2001)',
       'chemin': 'cliparts/web/{dossier}/{n}.gif', 'themes': [], 'items': []}
for i, (d, k, nom, un) in enumerate(WEB):
    cat['themes'].append([k, nom, un])
    os.makedirs(os.path.join(dst, k), exist_ok=True)
    for r, _, files in sorted(os.walk(os.path.join(src, 'WebGen', d))):
        if os.path.relpath(r, os.path.join(src, 'WebGen', d)).count(os.sep) < 1:
            continue
        for f in sorted(files):
            if f.lower().endswith('.gif'):
                n = f[:-4].lower()
                shutil.copyfile(os.path.join(r, f), os.path.join(dst, k, n + '.gif'))
                cat['items'].append([i, n])
json.dump(cat, open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('web', len(cat['items']))
