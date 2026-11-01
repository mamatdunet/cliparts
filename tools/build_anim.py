"""Copie les GIF animés du CD 2 d'IMSI « ClipArt & More 2.5 Million » (Web Spice) dans cliparts/anim.
Usage : python3 tools/build_anim.py <racine extraite de ClipaArt&More_2.5M_CD2_WIN.iso (button/, object/, word/)>
Chaque animation existe sur 3 fonds (dernière lettre du fichier : B noir, T transparent, W blanc) ;
les boutons existent en 4 animations (dossiers A, C, G, H) et 25 couleurs."""
import sys, os, json, shutil
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
dst = os.path.join(root, 'cliparts/anim')
SHAPES = {
 'biohazard': 'Risque biologique', 'blisterpack': 'Plaquette de gélules', 'block_1': 'Bloc 1', 'block_2': 'Bloc 2', 'block_3': 'Bloc 3',
 'blocks': 'Blocs', 'bolt': 'Éclair', 'bottle': 'Bouteille', 'bowling_pin': 'Quille', 'brick': 'Brique', 'cable': 'Câble',
 'candy': 'Bonbon', 'capsule': 'Gélule', 'castle': 'Château', 'check': 'Coche', 'cherry': 'Cerises', 'cinderblock': 'Parpaing',
 'circle_1': 'Cercle 1', 'circle_2': 'Cercle 2', 'cog': 'Engrenage', 'cone_1': 'Cône 1', 'cone_2': 'Cône 2', 'cone_3': 'Cône 3',
 'crescent': 'Croissant de lune', 'cube': 'Cube', 'cube_3': 'Cube 3', 'cup': 'Tasse', 'cylinder': 'Cylindre', 'diamond': 'Diamant',
 'die': 'Dé', 'dodecahedron': 'Dodécaèdre', 'donut': 'Beignet', 'envelope': 'Enveloppe', 'fleur_de_lis': 'Fleur de lys',
 'frame': 'Cadre', 'girder_1': 'Poutrelle 1', 'girder_2': 'Poutrelle 2', 'girder_3': 'Poutrelle 3', 'hazmat': 'Matière dangereuse',
 'heart': 'Cœur', 'hexagram_1': 'Étoile à six branches 1', 'hexagram_2': 'Étoile à six branches 2', 'house': 'Maison',
 'icosahedron': 'Icosaèdre', 'jack': 'Osselet', 'jar': 'Bocal', 'lightbulb': 'Ampoule', 'lozenge': 'Losange', 'mace': 'Masse d\'armes',
 'moai': 'Moaï', 'molecule_1': 'Molécule 1', 'molecule_2': 'Molécule 2', 'molecule_3': 'Molécule 3', 'mug': 'Mug',
 'note': 'Note de musique', 'nut': 'Écrou', 'object_1': 'Forme 1', 'object_2': 'Forme 2', 'object_3': 'Forme 3', 'object_4': 'Forme 4',
 'octagon': 'Octogone', 'octahedron': 'Octaèdre', 'pill': 'Pilule', 'propeller': 'Hélice', 'puzzle': 'Puzzle',
 'pyramid_1': 'Pyramide 1', 'pyramid_2': 'Pyramide 2', 'religion_1': 'Croix 1', 'religion_2': 'Croix 2', 'ribbon': 'Ruban',
 'ring_1': 'Anneau 1', 'ring_2': 'Anneau 2', 'ring_3': 'Anneau 3', 'ring_4': 'Anneau 4', 'rings': 'Anneaux', 'roller': 'Rouleau',
 'saturn': 'Saturne', 'shapes': 'Formes', 'shim': 'Rondelle', 'slats': 'Lattes', 'slot_grommet': 'Œillet', 'snowflake_1': 'Flocon 1',
 'snowflake_2': 'Flocon 2', 'snowflake_3': 'Flocon 3', 'spheres_1': 'Sphères 1', 'spheres_2': 'Sphères 2', 'spheres_3': 'Sphères 3',
 'spool': 'Bobine', 'spring_1': 'Ressort 1', 'spring_2': 'Ressort 2', 'square_1': 'Carré 1', 'square_2': 'Carré 2',
 'square_3': 'Carré 3', 'stamp': 'Timbre', 'star_1': 'Étoile 1', 'star_2': 'Étoile 2', 'star_3': 'Étoile 3', 'swirl': 'Spirale',
 'talk': 'Bulle', 'temple': 'Temple', 'tile': 'Carreau', 'top': 'Toupie', 'triangle': 'Triangle', 'triangles': 'Triangles',
 'triangles_3': 'Triangles 3', 'ufo': 'Soucoupe volante', 'vase': 'Vase', 'vines': 'Lianes', 'x_1': 'Croix en X 1', 'x_2': 'Croix en X 2',
 'yingyang': 'Yin et yang'}
SHAPES.update({'sphere_%02d' % i: 'Sphère %d' % i for i in range(1, 11)})
OBJECTS = {
 'abacus': 'Boulier', 'backhoe': 'Pelleteuse', 'barber': 'Enseigne de barbier', 'bell_1': 'Cloche', 'bell_2': 'Clochette',
 'bells': 'Cloches de Noël', 'block': 'Cube de jeu', 'book_1': 'Livre', 'book_2': 'Livre fermé', 'cart': 'Caddie',
 'cash_register': 'Caisse enregistreuse', 'cellphone': 'Téléphone portable', 'cheese': 'Fromage', 'chess': 'Échecs',
 'chili': 'Piment', 'clip_binder': 'Pince à dessin', 'clip_paper': 'Trombone', 'clock': 'Pendule', 'daisy': 'Marguerite',
 'dna': 'ADN', 'fountain_pen': 'Stylo plume', 'gavel': 'Marteau de juge', 'glasses': 'Lunettes', 'jet': 'Avion de ligne',
 'key_1': 'Clé', 'key_2': 'Clé ancienne', 'lavalamp': 'Lampe à lave', 'mailbox_1': 'Boîte aux lettres', 'mailbox_2': 'Boîte aux lettres 2',
 'martini': 'Martini', 'note': 'Note de musique', 'padlock': 'Cadenas', 'piano': 'Piano', 'quill_pen': 'Plume d\'oie', 'rose': 'Rose',
 'screwdriver': 'Tournevis', 'scroll': 'Parchemin', 'ship': 'Bateau', 'sign_sale': 'Panneau Soldes', 'sparkplug': 'Bougie d\'allumage',
 'sundial': 'Cadran solaire', 'sunglasses': 'Lunettes de soleil', 'tack': 'Punaise', 'toilet': 'Toilettes', 'trombones': 'Trombones',
 'trumpet': 'Trompette', 'violin': 'Violon'}
ANIM = {'A': 'rotation', 'C': 'culbute', 'G': 'rebond', 'H': 'pulsation'}
WORD_ANIM = {'encircling': 'en cercle', 'falling': 'chute', 'growing': 'zoom', 'rotating': 'rotation', 'spinning': 'tourbillon'}
WORDS = ['Back', 'Buy Now', 'Click Here', 'Download', 'E-Mail', 'Free', 'Home', 'HOT!', 'Links', 'New', 'Next']
FONDS = {'b': 'fond noir', 't': 'fond transparent', 'w': 'fond blanc'}
themes, items, used = [], [], set()

def theme(k, nom):
    themes.append([k, nom]); os.makedirs(os.path.join(dst, k), exist_ok=True)
    return len(themes) - 1

def add(t, p, nom, kw):
    n = os.path.basename(p)[:-4].lower()
    assert (t, n) not in used, p
    used.add((t, n))
    shutil.copyfile(p, os.path.join(dst, themes[t][0], n + '.gif'))
    items.append([t, n, nom, kw + ' ' + FONDS[n[-1]]])

def gifs(d):
    return sorted(f for f in os.listdir(d) if f.upper().endswith('.GIF'))

for s in sorted(os.listdir(os.path.join(src, 'button')), key=lambda s: SHAPES[s]):
    t = theme('bouton-' + s.replace('_', '-'), 'Bouton ' + SHAPES[s][0].lower() + SHAPES[s][1:])
    for a in sorted(os.listdir(os.path.join(src, 'button', s))):
        for f in gifs(os.path.join(src, 'button', s, a)):
            add(t, os.path.join(src, 'button', s, a, f), SHAPES[s], f'bouton {ANIM[a]} {s.replace("_", " ")}')
t = theme('objets', 'Objets animés')
for o in sorted(os.listdir(os.path.join(src, 'object')), key=lambda o: OBJECTS[o]):
    for f in gifs(os.path.join(src, 'object', o)):
        add(t, os.path.join(src, 'object', o, f), OBJECTS[o], f'objet {o.replace("_", " ")}')
for font, nom in (('serif', 'Mots animés (serif)'), ('sans', 'Mots animés (sans serif)')):
    t = theme('mots-' + font, nom)
    for d in sorted(os.listdir(os.path.join(src, 'word', font))):
        fs = gifs(os.path.join(src, 'word', font, d))
        codes = sorted({f[4:6] for f in fs})
        assert len(codes) == len(WORDS), d
        for f in fs:
            add(t, os.path.join(src, 'word', font, d, f), WORDS[codes.index(f[4:6])], f'mot {WORD_ANIM[d.split("_")[0]]} {d.split("_")[0]}')
json.dump({'source': 'ClipArt & More 2.5 Million (IMSI, 2003), CD 2, animations Web Spice',
           'chemin': 'cliparts/anim/{dossier}/{n}.gif', 'themes': themes, 'items': items},
          open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('anim', len(items), 'themes', len(themes))
