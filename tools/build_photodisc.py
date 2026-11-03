"""Copie les 144 photos PhotoDisc d'Office 97 (dossier Photos de Clipart.zip) dans cliparts/photodisc/<rubrique>/<nom>.jpg.
Usage : python3 tools/build_photodisc.py <Clipart extrait de Clipart.zip (archive.org/details/mso97clipart)>
Les catégories et les mots-clés viennent de l'onglet Pictures de la Clip Gallery (Photos/photos.cag) : le premier mot-clé
sert de nom. Les JPG sont repris tels quels."""
import sys, os, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cag
from rubriques import PHOTODISC, RUBRIQUES
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(sys.argv[1], 'Photos')
dst = os.path.join(root, 'cliparts/photodisc')
shutil.rmtree(dst, ignore_errors=True)
cats, fiches = cag.lire(os.path.join(src, 'photos.cag'), cag.PICTURES)
noms = dict(RUBRIQUES)
themes = sorted({PHOTODISC[c][1] for c in cats}, key=lambda r: noms[r])
items = []
for c, ids in sorted(cats.items()):
    dossier, r = PHOTODISC[c]
    fichiers = {f.lower(): f for f in os.listdir(os.path.join(src, dossier))}
    os.makedirs(os.path.join(dst, r), exist_ok=True)
    for i in ids:
        f, kw = fiches[i]
        mots = kw.split(',')
        n = f[:-4].lower()
        shutil.copyfile(os.path.join(src, dossier, fichiers[f.lower()]), os.path.join(dst, r, n + '.jpg'))
        items.append([themes.index(r), n, mots[0], ' '.join([c] + mots[1:])])
json.dump({'source': "Microsoft Office 97 (archive.org/details/mso97clipart), Clipart.zip, dossier Photos : photos PhotoDisc, 1996", 'chemin': 'cliparts/photodisc/{dossier}/{n}.jpg',
           'themes': [[r, noms[r]] for r in themes], 'items': items},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('photodisc', len(items), 'photos', len(themes), 'thèmes')
