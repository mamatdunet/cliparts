"""Construit data/index.json, l'index unique des six collections, à partir des catalogues.
Usage : python3 tools/build_index.py"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pro = json.load(open(os.path.join(root, 'cliparts/pro/catalog.json')))
mc = json.load(open(os.path.join(root, 'cliparts/mc/catalog.json')))
photos = json.load(open(os.path.join(root, 'cliparts/photos/catalog.json')))
web = json.load(open(os.path.join(root, 'cliparts/web/catalog.json')))
szene = json.load(open(os.path.join(root, 'cliparts/szene/catalog.json')))
imsi = json.load(open(os.path.join(root, 'cliparts/imsi/catalog.json')))

collections = [
    {'id': 'pro', 'nom': 'Cliparts Pro', 'annee': 1998, 'editeur': 'TLC Domus / Solver S.A.',
     'source': 'https://archive.org/details/cliparts-pro', 'ext': 'svg'},
    {'id': 'mc', 'nom': 'Micro Application', 'annee': 2002, 'editeur': 'Micro Application (réf. 4366MC)',
     'source': 'https://archive.org/details/4366-mc', 'ext': 'svg'},
    {'id': 'photos', 'nom': 'Photos', 'annee': 2002, 'editeur': 'CD Micro Application (réf. 4366MC)',
     'source': 'https://archive.org/details/4366-mc', 'ext': 'jpg'},
    {'id': 'web', 'nom': 'Images web', 'annee': 2001, 'editeur': 'Hemera, CD Micro Application',
     'source': 'https://archive.org/details/4366-mc', 'ext': 'gif'},
    {'id': 'szene', 'nom': 'Szene-Cliparts', 'annee': 2001, 'editeur': 'E.D.V. CD-ROM GmbH',
     'source': 'https://archive.org/details/szene-cliparts-2001', 'ext': 'png'},
    {'id': 'imsi', 'nom': 'ClipArt & More', 'annee': 2003, 'editeur': 'IMSI',
     'source': 'https://archive.org/details/imsi-clipart-more-2.5-million-3-cd-rom', 'ext': 'svg'},
]
themes, items = [], []
tidx = {}
for t, th in sorted(pro['themes'].items(), key=lambda kv: kv[1]['nom']):
    tidx[t] = len(themes); themes.append([0, th['dossier'], th['nom']])
for it in pro['items']:
    for v in it['v']:
        items.append([tidx[it['t']], f"{it['t']}_{v}_{it['n']}".lower(), it['nom'], v])
base = len(themes)
for k, nom in mc['themes']:
    themes.append([1, k, nom])
for t, n in mc['items']:
    items.append([base + t, n])
base = len(themes)
for k, nom in photos['themes']:
    themes.append([2, k, nom])
for t, n in photos['items']:
    items.append([base + t, n])
# Images web : le nom est celui du type (Bouton, Puce…), la forme et la couleur sont dans le fichier
base = len(themes)
for k, nom, un in web['themes']:
    themes.append([3, k, nom])
for t, n in web['items']:
    items.append([base + t, n, web['themes'][t][2]])
# Szene-Cliparts : images de la scène démo ; « adult » liste les images masquées sans l'option +18 ans
adult = []
base = len(themes)
for k, nom in szene['themes']:
    themes.append([4, k, nom])
for it in szene['items']:
    if len(it) > 3:
        adult.append(len(items))
    items.append([base + it[0], it[1]] + ([it[2]] if it[2] else []))
# ClipArt & More (IMSI) : 5e champ = mots-clés (français et anglais du CD) pour la recherche
base = len(themes)
for k, nom, top in imsi['themes']:
    themes.append([5, k, nom])
for t, n, nom, kw in imsi['items']:
    items.append([base + t, n, nom, 0, kw])

out = {'v': 1, 'collections': collections, 'persos': pro['persos'], 'themes': themes, 'items': items, 'adult': adult}
os.makedirs(os.path.join(root, 'data'), exist_ok=True)
json.dump(out, open(os.path.join(root, 'data/index.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(items), 'items', len(themes), 'themes')
