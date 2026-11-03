"""Écrit data/menus/<collection>.json, le classement d'origine des collections qui en ont gardé un.
Usage : python3 tools/build_menus.py <dossier Clipart extrait de Clipart.zip (archive.org/details/mso97clipart)>
Les ISO de ClipArt & More sont lus à la racine du projet. Print Artist a son menu dans build_printartist.py ;
les collections rangées en simples dossiers n'ont pas de fichier : le site reconstruit leur menu depuis l'index."""
import sys, os, json, re, subprocess, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cag
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
clipart = sys.argv[1]
os.makedirs(os.path.join(root, 'data/menus'), exist_ok=True)


def sauver(id_, menu, noms):
    """noms : les fichiers que le menu devrait trouver. On signale ceux que la collection n'a pas (doublons écartés à l'import)."""
    cat = json.load(open(os.path.join(root, f'cliparts/{id_}/catalog.json')))
    connus = {it[1] for it in cat['items']}
    noms = [n.split('/')[-1] for n in noms]
    print(id_, len(menu['images']), 'images', len(menu['categories']), 'catégories,', len(set(noms) - connus), 'absentes,', len(connus - set(noms)), 'sans catégorie')
    json.dump(menu, open(os.path.join(root, f'data/menus/{id_}.json'), 'w'), ensure_ascii=False, separators=(',', ':'))


def arbre(id_, titre, note, entrees):
    """entrees : [(dossiers du CD, fichier)]. Seules les feuilles portent leurs images : le site en déduit celles des dossiers parents."""
    entrees = sorted(set(entrees), key=lambda e: ([d.casefold() for d in e[0]], e[1]))
    images, feuilles, chemins = [], collections.defaultdict(list), set()
    vus = {}
    for ch, n in entrees:
        if n in vus: continue
        vus[n] = len(images); images.append(n)
        feuilles[ch].append(vus[n])
        for k in range(1, len(ch) + 1):
            chemins.add(ch[:k])
    cats = [{'nom': ' > '.join(c), 'court': c[-1], 'niveau': len(c) - 1, 'images': feuilles.get(c, [])} for c in sorted(chemins, key=lambda c: [d.casefold() for d in c])]
    sauver(id_, {'collections': [id_], 'titre': titre, 'note': note, 'images': images, 'categories': cats}, images)


def lisible(s):
    s = re.sub(r'_+$', '', s).replace('_', ' ').strip().title()
    return re.sub(r'\b(And|Of|The|For)\b', lambda m: m.group().lower(), s)


def iso(nom):
    return subprocess.run(['bsdtar', '-tf', os.path.join(root, nom)], capture_output=True, text=True).stdout.splitlines()


# ---------- Office 97 : les catalogues de la Clip Gallery ----------
DOSSIERS = (('Office', 'office.cag'), ('Powerpnt', 'powerpnt.cag'), ('Popular', 'pop97.cag'), ('Scrbeans', 'scrbeans.cag'))
connus = {it[1] for it in json.load(open(os.path.join(root, 'cliparts/office97/catalog.json')))['items']}
images, rang, par_cat, attendus = [], {}, collections.defaultdict(set), []
for d, f in DOSSIERS:
    cats, fiches = cag.lire(os.path.join(clipart, d, f))
    # Un dessin de même nom mais différent d'un dossier à l'autre porte le nom du dossier en plus
    fich = {}
    for i, (nom, _) in sorted(fiches.items()):
        n = nom[:-4].lower()
        fich[i] = n2 if (n2 := f'{n}-{d.lower()}') in connus else n
        attendus.append(fich[i])
        if fich[i] not in rang:
            rang[fich[i]] = len(images); images.append(fich[i])
    for c, ids in cats.items():
        par_cat[c].update(rang[fich[i]] for i in ids)
sauver('office97', {'collections': ['office97'], 'titre': 'Categories', 'note': "Le classement de la Clip Gallery d'Office 97, avec ses noms anglais. Ses mots-clés servent à la recherche.",
                    'images': images, 'categories': [{'nom': c, 'images': sorted(par_cat[c])} for c in sorted(par_cat, key=str.casefold)]}, attendus)

# ---------- ClipArt & More : les dossiers des deux CD ----------
arbre('imsi', 'Dossiers du CD', "L'arborescence du CD, avec ses noms anglais.",
      [(tuple(lisible(x) for x in p[1:-1]), p[-1][:-4].lower()) for p in (l.split('/') for l in iso('ClipaArt&More_2.5M_CD1_WIN.iso')) if p[0] == 'CLIPART' and p[-1].upper().endswith('.WMF')])
arbre('anim', 'Dossiers du CD', "L'arborescence du CD Web Spice, avec ses noms anglais.",
      [(tuple(lisible(x) for x in p[:-1]), p[-1][:-4].lower()) for p in (l.split('/') for l in iso('ClipaArt&More_2.5M_CD2_WIN.iso')) if p[0] in ('button', 'object', 'word') and p[-1].upper().endswith('.GIF')])

# ---------- Masterclips : 10 grands dossiers et 117 bibliothèques du navigateur MediaPaq ----------
d = json.load(open(os.path.join(root, 'cliparts/masterclips/catalog.json')))
fois = collections.Counter(it[1] for it in d['items'])  # un même nom dans deux bibliothèques : on précise son dossier
arbre('masterclips', 'Dossiers du CD', "Les 10 grands dossiers du CD et ses 117 bibliothèques, aux noms traduits.",
      [((it[2].capitalize(), d['themes'][it[0]][1]), it[1] if fois[it[1]] == 1 else f"{d['themes'][it[0]][0]}/{it[1]}") for it in d['items']])
