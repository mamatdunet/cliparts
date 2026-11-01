"""Convertit les cliparts WMF et les photos BMP des 2 CD IMSI « Masterclips 35 000 Clip Arts » (1996).
Usage : python3 tools/build_masterclips.py <CLIPART extrait du CD 1> <PHOTOS extrait du CD 2>   (Pillow pour les photos)
Les fichiers du CD n'ont pas de nom : chaque dessin prend le nom de son dossier, traduit ici."""
import sys, os, json, re, hashlib, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wmf
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
clip, photos = sys.argv[1], sys.argv[2]
TOP = {'ANIMALS': 'Animaux', 'BORDERS': 'Bordures et fonds', 'MISC': 'Divers', 'OBJECTS': 'Objets', 'PEOPLE': 'Personnages',
       'RECREATN': 'Loisirs', 'REGIONAL': 'Pays et régions', 'SEASONAL': 'Fêtes et saisons', 'SYMBOLS': 'Symboles', 'TRANSPRT': 'Transports'}
FR = {
 'ANIMBIRD': 'Oiseaux', 'ANIMDOME': 'Animaux domestiques', 'ANIMWILD': 'Animaux sauvages', 'CARTANIM': 'Animaux humoristiques',
 'INSECTS': 'Insectes', 'POP_CRET': 'Créatures pop art', 'BACKLAND': 'Fonds à l\'italienne', 'BACKMISC': 'Fonds et bannières',
 'BACKPORT': 'Fonds à la française', 'BRDRLAND': 'Bordures à l\'italienne', 'BRDRMISC': 'Bordures diverses',
 'BRDRPORT': 'Bordures à la française', 'BRDRTOP': 'Frises', 'CORNERS': 'Coins', 'CARTMISC': 'Dessins humoristiques divers',
 'CONSTRU': 'Construction', 'FICTION': 'Fiction et fantastique', 'FINANCE': 'Finance', 'INDUSTRY': 'Industrie et environnement',
 'MILIINSG': 'Insignes militaires', 'MILIMISC': 'Militaires', 'MISC': 'Divers', 'POP_ART': 'Pop art', 'SAFETY': 'Sécurité',
 'SCIENCE': 'Sciences', 'ART_PRES': 'Arts et présentation', 'CARTOBJE': 'Objets humoristiques', 'CLOTHES': 'Vêtements',
 'COMMU': 'Communication', 'COMPUTER': 'Informatique', 'FOOD': 'Cuisine et boissons', 'HOUSFURN': 'Meubles',
 'HOUSITEM': 'Objets de la maison', 'HOUSUTNL': 'Ustensiles de cuisine', 'OBJECTS': 'Objets', 'OFFICE': 'Bureau',
 'PLANTS': 'Plantes et fleurs', 'TOOLS': 'Outils', 'ANATOMY': 'Anatomie', 'CARTDUNC': 'Personnages de Dunc',
 'CARTMEN': 'Hommes humoristiques', 'CARTMENP': 'Métiers humoristiques', 'CARTPEPL': 'Gens humoristiques',
 'CARTWOMN': 'Femmes humoristiques', 'EDUCATE': 'Éducation', 'ENTERTIN': 'Spectacle', 'HANDS': 'Mains', 'HEALTH': 'Santé',
 'MEN': 'Hommes', 'MENPROF': 'Métiers', 'PEOPLE': 'Gens', 'RELICHRS': 'Religion chrétienne', 'RELIMISC': 'Religions',
 'WOMEN': 'Femmes', 'CARTSPRT': 'Sports humoristiques', 'LEISGAME': 'Jeux', 'LEISMISC': 'Loisirs', 'SPRTINDV': 'Sports individuels',
 'SPRTMISC': 'Sports divers', 'SPRTTEAM': 'Sports d\'équipe', 'AGRICULT': 'Agriculture', 'AMERICA': 'Amérique',
 'FLAGMISC': 'Drapeaux divers', 'FLAGNATI': 'Drapeaux nationaux', 'FLAGUS': 'Drapeaux des États américains',
 'FLAGWRLD': 'Drapeaux du monde', 'GOVT': 'Gouvernement', 'MAPSUS': 'Cartes des États-Unis', 'MAPSWRLD': 'Cartes du monde',
 'ORIENT': 'Motifs orientaux', 'ORNTIMGE': 'Images orientales', 'PLACMISC': 'Lieux divers', 'PLACUS': 'Lieux des États-Unis',
 'PLACWRLD': 'Lieux du monde', 'REALESTE': 'Immobilier', 'WORLD': 'Le monde', 'CALENDAR': 'Calendrier', 'DAYDATE': 'Jours et dates',
 'HISTORY': 'Histoire', 'HOLICHRS': 'Noël', 'HOLIFALL': 'Fêtes d\'automne', 'HOLISPRI': 'Fêtes de printemps',
 'HOLISUMM': 'Fêtes d\'été', 'HOLIWNTR': 'Fêtes d\'hiver', 'SEASONS': 'Saisons', 'SPECOCCA': 'Grandes occasions', 'TIME': 'Le temps',
 'ALPHABET': 'Alphabets', 'ARCHSYMB': 'Symboles d\'architecture', 'ARROWS': 'Flèches', 'BUTTONS': 'Boutons et touches',
 'CARTELEM': 'Éléments de BD', 'CHARTS': 'Graphiques', 'CRESTS': 'Blasons', 'DESIGNS': 'Ornements', 'DINGBATS': 'Dingbats',
 'ICONS': 'Icônes', 'RUBRSTMP': 'Tampons', 'SHAPES': 'Formes', 'SIGNEURO': 'Panneaux européens', 'SIGNINFO': 'Panneaux d\'information',
 'SIGNLANG': 'Langue des signes et braille', 'SIGNMISC': 'Panneaux divers', 'SIGNTRFC': 'Signalisation routière',
 'SIGNWARN': 'Panneaux d\'avertissement', 'STARS': 'Étoiles et éclats', 'SYMBOLS': 'Symboles', 'TECH': 'Technologie',
 'TECHSYMB': 'Symboles techniques', 'TEXT': 'Textes', 'WORDSYMB': 'Mots et symboles', 'ZODIAC': 'Zodiaque',
 'CARTTRAN': 'Transports humoristiques', 'MILIEQUP': 'Matériel militaire', 'TRANAIR': 'Aviation', 'TRANGRND': 'Transports terrestres',
 'TRANWATR': 'Bateaux'}
PHOTOS = {'AUTO': 'Voitures', 'BIRDS': 'Oiseaux', 'BKGRNDS': 'Fonds', 'BOATS': 'Bateaux', 'BUILDNGS': 'Bâtiments', 'CHILDREN': 'Enfants',
          'CITYTWN': 'Villes', 'COASTS': 'Côtes', 'DOM_AN': 'Animaux domestiques', 'DSRTCYN': 'Déserts et canyons', 'FIELDS': 'Champs',
          'FOOD': 'Cuisine', 'LAKERIVR': 'Lacs et rivières', 'LIFESTYL': 'Art de vivre', 'MOUNTAIN': 'Montagnes', 'OBJECTS': 'Objets',
          'PEOPLE': 'Gens', 'PLANES': 'Avions', 'PLANTS': 'Plantes', 'SKYCLOUD': 'Ciel et nuages', 'SPACE': 'Espace',
          'SPCLOCSN': 'Grandes occasions', 'SUNSET': 'Couchers de soleil', 'TEXTURE': 'Textures', 'TREELEAV': 'Arbres et feuilles',
          'UNDERWTR': 'Sous la mer', 'WATRFALL': 'Cascades', 'WILDANIM': 'Animaux sauvages'}

def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def write(dst, source, ext, themes, items):
    order = sorted(themes, key=lambda k: slug(themes[k]))
    idx = {k: i for i, k in enumerate(order)}
    json.dump({'source': source, 'chemin': f'cliparts/{os.path.basename(dst)}/{{dossier}}/{{n}}.{ext}',
               'themes': [[k, themes[k]] for k in order], 'items': [[idx[k], n, kw] for k, n, kw in items]},
              open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(os.path.basename(dst), len(items), 'themes', len(order))

# Cliparts (CD 1) : un thème par sous-dossier ; « C » / « N » en 5e lettre = couleur / noir et blanc
dst = os.path.join(root, 'cliparts/masterclips')
themes, items, seen, fails, dups = {}, [], set(), [], 0
for top in sorted(os.listdir(clip)):
    for sub in sorted(os.listdir(os.path.join(clip, top))):
        d = os.path.join(clip, top, sub); k = slug(FR[sub])
        if k in themes and themes[k] != FR[sub]:
            k = slug(TOP[top] + ' ' + FR[sub])
        for f in sorted(os.listdir(d)):
            if not f.upper().endswith('.WMF'):
                continue
            p = os.path.join(d, f)
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
            themes.setdefault(k, FR[sub])
            items.append([k, n, TOP[top].lower()])
write(dst, 'Masterclips 35 000 Clip Arts (IMSI, 1996), CD 1, converti depuis WMF', 'svg', themes, items)
print('dups', dups, 'fails', len(fails), fails[:5])

# Photos (CD 2) : BMP 256 couleurs → JPG
from PIL import Image
dst = os.path.join(root, 'cliparts/mphotos')
themes, items = {}, []
for sub in sorted(os.listdir(photos)):
    k = slug(PHOTOS[sub]); themes[k] = PHOTOS[sub]
    os.makedirs(os.path.join(dst, k), exist_ok=True)
    for f in sorted(os.listdir(os.path.join(photos, sub))):
        if f.upper().endswith('.BMP'):
            n = f[:-4].lower()
            Image.open(os.path.join(photos, sub, f)).convert('RGB').save(os.path.join(dst, k, n + '.jpg'), quality=88, optimize=True)
            items.append([k, n, ''])
write(dst, 'Masterclips 35 000 Clip Arts (IMSI, 1996), CD 2, dossier PHOTOS converti depuis BMP', 'jpg', themes, items)
