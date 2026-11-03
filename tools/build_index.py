"""Construit data/index.json, l'index unique des neuf collections, à partir des catalogues.
Usage : python3 tools/build_index.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pro = json.load(open(os.path.join(root, 'cliparts/pro/catalog.json')))
mc = json.load(open(os.path.join(root, 'cliparts/mc/catalog.json')))
photos = json.load(open(os.path.join(root, 'cliparts/photos/catalog.json')))
web = json.load(open(os.path.join(root, 'cliparts/web/catalog.json')))
szene = json.load(open(os.path.join(root, 'cliparts/szene/catalog.json')))
imsi = json.load(open(os.path.join(root, 'cliparts/imsi/catalog.json')))
anim = json.load(open(os.path.join(root, 'cliparts/anim/catalog.json')))
mclips = json.load(open(os.path.join(root, 'cliparts/masterclips/catalog.json')))
mphotos = json.load(open(os.path.join(root, 'cliparts/mphotos/catalog.json')))
# Openclipart n'entre dans l'index qu'une fois importé (tools/build_openclipart.py)
ocp = os.path.join(root, 'cliparts/openclipart/catalog.json')
oclip = json.load(open(ocp)) if os.path.exists(ocp) else None

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
    {'id': 'anim', 'nom': 'Animations web', 'annee': 2003, 'editeur': 'IMSI, CD 2 de ClipArt & More',
     'source': 'https://archive.org/details/imsi-clipart-more-2.5-million-3-cd-rom', 'ext': 'gif'},
    {'id': 'masterclips', 'nom': 'Masterclips', 'annee': 1996, 'editeur': 'IMSI',
     'source': 'https://archive.org/details/IMSI_Masterclips_35000_ClipArts_1996Win31Eng', 'ext': 'svg'},
    {'id': 'mphotos', 'nom': 'Photos Masterclips', 'annee': 1996, 'editeur': 'IMSI, CD 2 de Masterclips',
     'source': 'https://archive.org/details/IMSI_Masterclips_35000_ClipArts_1996Win31Eng', 'ext': 'jpg'},
]
if oclip:
    collections.append({'id': 'openclipart', 'nom': 'Openclipart', 'editeur': 'Openclipart, domaine public (CC0)',  # sans année : alimenté depuis 2004
                        'source': 'https://openclipart.org/', 'ext': 'svg'})
    # Les dessins sont servis depuis Vercel Blob (tools/upload_openclipart.mjs), trop nombreux pour un déploiement
    bp = os.path.join(root, 'cliparts/openclipart/blob.json')
    if os.path.exists(bp):
        collections[-1]['base'] = json.load(open(bp))['base']
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
# Animations web (IMSI, CD 2) : même format, mots-clés = type d'animation et fond
base = len(themes)
for k, nom in anim['themes']:
    themes.append([6, k, nom])
for t, n, nom, kw in anim['items']:
    items.append([base + t, n, nom, 0, kw])
# Masterclips (IMSI, 1996) : pas de nom par dessin, le thème sert de nom ; mots-clés = grande catégorie du CD,
# plus l'occasion que code le début du fichier dans les thèmes de fêtes et de saisons (hallw001 = Halloween…)
MCLIPS_KW = {
    'hallw': 'halloween citrouille', 'thkgv': 'thanksgiving', 'colum': 'christophe colomb', 'labor': 'fete du travail labor day',
    'vetdy': 'armistice anciens combattants', 'oktbr': 'oktoberfest biere', 'valen': 'saint-valentin amour coeur',
    'newyr': 'nouvel an reveillon bonne annee', 'presd': 'presidents', 'hanak': 'hanoucca', 'mking': 'martin luther king',
    'ghog': 'jour de la marmotte', 'boxdy': 'boxing day', 'eastr': 'paques oeuf lapin', 'stpat': 'saint-patrick trefle',
    'aprl': "poisson d'avril", 'carn': 'carnaval', 'mardi': 'mardi gras carnaval', 'secdy': 'journee des secretaires',
    'july': '4 juillet fete nationale', 'memor': 'memorial day', 'mothr': 'fete des meres maman', 'fathr': 'fete des peres papa',
    'flgdy': 'jour du drapeau', 'maydy': '1er mai', 'arbor': "jour de l'arbre", 'bastl': '14 juillet fete nationale',
    'cinco': 'cinco de mayo', 'wintr': 'hiver neige', 'summr': 'ete vacances', 'sprng': 'printemps', 'fall': 'automne',
    'bday': 'anniversaire', 'wedng': 'mariage', 'grad': 'diplome', 'anniv': 'anniversaire de mariage',
    'baby': 'naissance bebe', 'funrl': 'obseques deuil', 'spcoc': 'occasion speciale',
}
base = len(themes)
for k, nom in mclips['themes']:
    themes.append([7, k, nom])
for t, n, kw in mclips['items']:
    extra = MCLIPS_KW.get(n.rstrip('0123456789'), '')
    items.append([base + t, n, 0, 0, (kw + ' ' + extra).strip()])
base = len(themes)
for k, nom in mphotos['themes']:
    themes.append([8, k, nom])
for t, n, kw in mphotos['items']:
    items.append([base + t, n])
# Openclipart : titre anglais de l'auteur ; mots-clés = tags (et leur traduction) et auteur ; « +18 » si la page
# du dessin le dit « Safe for Work? No »
if oclip:
    base = len(themes)
    for k, nom in oclip['themes']:
        themes.append([9, k, nom])
    auteurs = {}  # items[5] : numéro de l'auteur dans « auteurs »
    for it in oclip['items']:
        if len(it) > 5:
            adult.append(len(items))
        items.append([base + it[0], it[1], it[2], 0, it[3], auteurs.setdefault(it[4], len(auteurs))])

# Doublons : une image dont le fichier est identique à une autre n'apparaît qu'une fois. On garde de préférence
# la version ClipArt & More (nommée, avec mots-clés) plutôt que sa reprise par Micro Application ; le nom du dossier
# de chaque copie retirée devient un mot-clé de l'image gardée.
import hashlib
PRIO = {'imsi': 0}
adult_set = set(adult)
# Empreintes gardées d'une fois sur l'autre (cliparts/_md5.json) : Openclipart pèse près de 90 Go
cache_p = os.path.join(root, 'cliparts/_md5.json')
cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
def digest(it):
    c = collections[themes[it[0]][0]]
    rel = f"{c['id']}/{themes[it[0]][1].split('.')[0]}/{it[1]}.{c['ext']}"
    st = os.stat(os.path.join(root, 'cliparts', rel))
    sig = f'{st.st_size}:{int(st.st_mtime)}'
    if rel not in cache or cache[rel][0] != sig:
        cache[rel] = [sig, hashlib.md5(open(os.path.join(root, 'cliparts', rel), 'rb').read()).hexdigest()]
    return cache[rel][1]
groups = {}
for i, it in enumerate(items):
    groups.setdefault(digest(it), []).append(i)
json.dump(cache, open(cache_p, 'w'), separators=(',', ':'))
drop = set()
for g in groups.values():
    if len(g) < 2: continue
    g.sort(key=lambda i: (PRIO.get(collections[themes[items[i][0]][0]]['id'], 1), i))
    keep = items[g[0]]
    keep += [0] * (5 - len(keep))
    names = {themes[items[j][0]][2] for j in g[1:]} - {themes[keep[0]][2]}
    keep[4] = ' '.join(filter(None, [keep[4] or '', *sorted(names)]))
    if any(j in adult_set for j in g): adult_set.add(g[0])
    drop.update(g[1:])
old = items
items = [it for i, it in enumerate(old) if i not in drop]
adult = [k for k, i in enumerate(i for i in range(len(old)) if i not in drop) if i in adult_set]
print(len(drop), 'doublons retirés')

# Rubriques : les 964 dossiers des CD regroupés en une cinquantaine de thèmes généraux (tools/rubriques.py) ;
# themes[i] = [collection, dossier, nom du dossier, rubrique]
from rubriques import RUBRIQUES, rubrique
for th in themes:
    r = rubrique(collections[th[0]]['id'], th[1], th[2])
    assert r is not None, th
    th.append(r)
# Cliparts Pro : chaque sujet va dans sa rubrique (rubriques.PRO). Un dossier réparti entre plusieurs rubriques donne
# un thème par rubrique, « dossier.rubrique », dont le 5e champ garde le dossier des fichiers.
from rubriques import PRO, SLUGS, norm as rnorm
part = {}
for it in items:
    th = themes[it[0]]
    if collections[th[0]]['id'] != 'pro' or rnorm(it[2]) not in PRO: continue
    r = SLUGS.index(PRO[rnorm(it[2])])
    if r == th[3]: continue
    if (it[0], r) not in part:
        part[it[0], r] = len(themes)
        themes.append([th[0], f'{th[1]}.{SLUGS[r]}', th[2], r, th[1]])
    it[0] = part[it[0], r]
# Openclipart : un dessin reclassé depuis son téléchargement (thème « dossier.rubrique ») garde son fichier ; il rejoint
# le thème de sa rubrique et son dossier passe dans le nom de fichier (« dossier/numéro »)
oc = next((i for i, c in enumerate(collections) if c['id'] == 'openclipart'), None)
if oc is not None:
    pure = {th[1]: i for i, th in enumerate(themes) if th[0] == oc and '.' not in th[1]}
    for it in items:
        th = themes[it[0]]
        if th[0] != oc or '.' not in th[1]: continue
        d, r = th[1].split('.')
        if r not in pure:
            pure[r] = len(themes); themes.append([oc, r, th[2], th[3]])
        it[0], it[1] = pure[r], f'{d}/{it[1]}'
    used = sorted({it[0] for it in items})
    renum = {old: new for new, old in enumerate(used)}
    themes = [themes[i] for i in used]
    for it in items: it[0] = renum[it[0]]
from rubriques import SOUS
out = {'v': 2, 'collections': collections, 'persos': pro['persos'],
       'rubriques': [[r, nom] + ([SOUS[r]] if r in SOUS else []) for r, nom in RUBRIQUES],
       'themes': themes, 'items': items, 'adult': adult}
if oclip:
    out['auteurs'] = list(auteurs)
os.makedirs(os.path.join(root, 'data'), exist_ok=True)
json.dump(out, open(os.path.join(root, 'data/index.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(items), 'items', len(themes), 'themes')
