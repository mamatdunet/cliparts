"""Regroupe les 964 dossiers des CD en une cinquantaine de thèmes généraux (« rubriques »).
Chaque dossier va dans la première rubrique dont un motif correspond à « collection:nom du dossier »
(nom sans accents, en minuscules). Le nom du dossier reste un mot-clé de recherche de ses images.
Usage : importé par build_index.py ; lancé seul, affiche la taille de chaque rubrique et les dossiers non classés."""
import re, unicodedata

RUBRIQUES = [
    ('animaux', 'Animaux'), ('oiseaux', 'Oiseaux'), ('vie-marine', 'Poissons et vie marine'),
    ('insectes-reptiles', 'Insectes et reptiles'), ('prehistoire', 'Dinosaures et préhistoire'),
    ('plantes-fleurs', 'Plantes et fleurs'), ('paysages', 'Paysages et nature'), ('ciel-espace', 'Ciel, météo et espace'),
    ('voyages', 'Voyages et pays du monde'), ('architecture', 'Architecture et bâtiments'),
    ('cartes-drapeaux', 'Cartes et drapeaux'), ('fetes', 'Fêtes et saisons'), ('occasions', 'Amour et grandes occasions'),
    ('gens', 'Gens'), ('visages', 'Visages et portraits'), ('famille', 'Famille et enfants'),
    ('dessins-enfants', "Dessins d'enfants"), ('metiers', 'Métiers et travail'), ('bureau', 'Bureau et affaires'),
    ('finance', 'Argent et finance'), ('informatique', 'Informatique et technologie'),
    ('communication', 'Communication et médias'), ('sciences', 'Sciences'), ('sante', 'Santé et médecine'),
    ('corps', 'Corps humain'), ('cuisine', 'Cuisine et alimentation'), ('maison', 'Maison et objets'),
    ('vetements', 'Vêtements et mode'), ('outils', 'Outils et bricolage'), ('industrie', 'Industrie, agriculture et environnement'),
    ('sports', 'Sports'), ('loisirs', 'Loisirs et jeux'), ('musique-spectacle', 'Musique et spectacle'),
    ('arts', 'Arts et culture'), ('gravures', 'Gravures anciennes'), ('education', 'École et éducation'),
    ('histoire', 'Histoire et civilisations'), ('religion', 'Religion'), ('armee', 'Armée'),
    ('societe', 'Société, politique et justice'), ('transports', 'Transports'),
    ('panneaux', 'Panneaux et signalisation'), ('symboles', 'Symboles et pictogrammes'), ('fleches', 'Flèches'),
    ('bordures', 'Bordures, coins et ornements'), ('fonds', 'Fonds et textures'), ('lettres', 'Lettres et textes'),
    ('calendrier', 'Calendrier et temps'), ('fantasy', 'Fantasy et merveilleux'), ('humour', 'Humour et BD'),
    ('pop-art', 'Pop art'), ('logos-demo', 'Logos de la scène démo'), ('pin-up', 'Pin-up'),
    ('boutons-web', 'Boutons web'), ('elements-web', 'Icônes et puces web'), ('animations', 'Objets et mots animés'),
    ('divers', 'Divers'),
]

# Motifs dans l'ordre : le premier qui correspond l'emporte. « coll: » restreint à une collection.
REGLES = [
    # Collections dont le classement est à part
    (r'^web:boutons', 'boutons-web'), (r'^web:', 'elements-web'),
    (r'^anim:bouton', 'boutons-web'), (r'^anim:', 'animations'),
    (r'^szene:logos', 'logos-demo'), (r'^szene:pin-up', 'pin-up'), (r'^szene:polices', 'lettres'),
    (r'^szene:(bd|surrealisme|science-fiction|fantasy)', 'fantasy'), (r'^szene:visages', 'visages'),
    (r'^szene:personnages', 'gens'), (r'^szene:(scenes|divers)', 'divers'),
    (r'^pro:bureau', 'bureau'), (r'^pro:maison', 'maison'), (r'^pro:metiers', 'metiers'), (r'^pro:nature', 'animaux'),
    (r'^pro:sports', 'sports'), (r'^pro:techniques', 'informatique'), (r'^pro:transports', 'transports'), (r'^pro:vie', 'gens'),
    (r'^photos:(bleu|jaune|orange|rouge|vert)$', 'fonds'),
    # Cas particuliers, avant les règles générales
    (r'gravure', 'gravures'), (r'gratte-ciel', 'architecture'), (r'cadres photographiques', 'bordures'), (r'voir le monde', 'voyages'),
    (r'periodes et styles|techniques artistiques|nature morte|images orientales|motifs orientaux|arlequin|images de studio|modeles de studio|decoratives|art de vivre$', 'arts'),
    (r'mythique', 'fantasy'), (r'cirque', 'loisirs'), (r'lutte contre', 'metiers'), (r'gendarmerie', 'armee'),
    (r'le masque', 'fetes'), (r'arriere-plans', 'fonds'), (r'blasons', 'histoire'), (r'boutons et touches', 'symboles'),
    (r'grande vitesse|transport', 'transports'), (r'education moderne', 'education'), (r'nourriture moderne', 'cuisine'),
    (r'accessoires des femmes|vetements des femmes|habits d enfants', 'vetements'), (r'femmes de sports', 'sports'),
    (r'cow-boys|humanite', 'gens'),
    (r'jouets d enfant|objets des enfants', 'loisirs'),
    # Humour, BD et pop art avant les sujets (« animaux humoristiques » va dans l'humour)
    (r'humoristi|caricature|dunc|comique|elements de bd|bande dessinee|animaux humanises|objets de caricature', 'humour'),
    (r'pop art', 'pop-art'),
    (r'gravure', 'gravures'),
    (r'art des enfants|vue par des enfants', 'dessins-enfants'),
    # Fêtes et occasions
    (r'noel|halloween|hanouk|paques|valentin|fete|nouvel an|nouvelle annee|jour de l an|feu d artifice|cartes de voeux|millenaire|saisons|printemps|citrouille', 'fetes'),
    (r'occasion|anniversaire|noces|mariage|amour|amoureuse|cadeaux|retraite', 'occasions'),
    # Nature
    (r'dinosaure|prehisto|especes disparues', 'prehistoire'),
    (r'oiseau|pingouin', 'oiseaux'),
    (r'poisson|vie marine|marine des|mer rouge|subaquat|sous l eau|sous la mer|sous-marines|aquatique|dauphin|caricatures de mer|fruits de mer', 'vie-marine'),
    (r'insecte|invertebr|arthropod|papillon|reptile', 'insectes-reptiles'),
    (r'animaux|animal|mammif|faune|\bchats|chiens|chevaux|serengeti|creatures', 'animaux'),
    (r'fleur|plante|roses|orchidee|tulipe|flore|jardin|arbres|feuillage|foret', 'plantes-fleurs'),
    (r'\bciel|cieux|nuage|espace|coucher|aube|orbite|spatial|temperature|le temps$|pluvieu|nocturne', 'ciel-espace'),
    (r'paysage|nature|cascade|chutes|lacs|montagn|cotes|cotier|desert|champs|plage|volcan|sable|vagues|cavernes|rock|campagne', 'paysages'),
    # Lieux et histoire
    (r'histoire|civilisation|azteque|egypte|pharaon|viking|medieval|chevalier|indigene|artefact|guerre|merveilles|ruines|decors grecs|americana|moments marquants', 'histoire'),
    (r'cartes du|cartes des|cartes et|drapeau|terre et globes|^masterclips:le monde$|etats americains|^masterclips:amerique', 'cartes-drapeaux'),
    (r'architect|batiment|habitation|maisons et les cottages|maisons juives|chateau|tours$|gratte|\bponts?\b|colonne|arches|eglise|immeubles|phares|monuments|symboles d architecture|developpement urbain|interieur', 'architecture'),
    (r'voyage|vacances|bagages|tourist|destination|lieux|villes|hotels|marinas|en route|traineau|canoe|nautique|bornes limites|parcs nationaux'
     r'|\b(afrique|allemagne|angleterre|arizona|berlin|bhoutan|canada|chicago|colombie|copenhague|costa rica|washington|france|extreme-orient'
     r'|floride|hawaii|hong kong|ile|japon|jamaique|kenya|miami|montreal|moyen orient|namibie|new york|nouvelle|ontario|ottawa|pays-bas|philadelphie'
     r'|colorado|italie|quebec|san diego|suisse|toronto|utah|mexic\w*|mexique|vallee du monument|zimbabwe|tropiques|pacifique|etats unis|usa|asie'
     r'|australie|zelande|rio de janeiro|la manche|sud-ouest)\b', 'voyages'),
    # Gens
    (r'visage|profils|portrait', 'visages'),
    (r'famille|enfant|bebe|adolescent|ecoliers|super-maman', 'famille'),
    (r'metier|occupation|ouvrier|travail|travaux|urgence|police|incendie|personnel|boulot', 'metiers'),
    (r'\bsport|golf|balles|soccer|gymnastique|exercice|lutte|cricket|baseball|alpiniste|corrida|camp d entrainement|surf', 'sports'),
    (r'vetement|mode$|coiffure|costume|couture|confection|beaute|maquillage', 'vetements'),
    (r'gens|personnages|hommes$|femmes|modes de vie|scenes$|silhouette|de l est|occidental', 'gens'),
    # Travail, technique, savoir
    (r'financ|argent|dollar', 'finance'),
    (r'ordinateur|informatique|technolog|electroniq|robot|courriel|toile mondiale|utilisateurs|renseignements', 'informatique'),
    (r'communication|television|radio|presse|cinema|tournage|courrier|messagerie|publicite|accroches|livres|bibliotheque|panneaux d information', 'communication'),
    (r'bureau|affaire|classement|entreprise|commerce|magasin|secretariat|immobilier|o glyphics', 'bureau'),
    (r'scienc|molecule|classification|mesure|symboles techniques', 'sciences'),
    (r'medic|sante|hopital|pharmac|medecin|dentai|dentiste|maladie|secours|hygiene|bequille|surdite|^imsi:vue|maux de|alcool|toxico|tabac|poison|spa et|veterinaire|mousse de savon', 'sante'),
    (r'anatomie|corps humain|mains|langue des signes', 'corps'),
    (r'nourriture|cuisin|fruits|legumes|boisson|repas|viande|cereales|sucrerie|laitier|condiment|conserve|herbes|noix|haricot|sandwich|the et cafe|cafe ou the|desserts|barbecue|comestible|martini|ustensiles|creme glacee|restauration', 'cuisine'),
    (r'outil|bricolage|construction|metallurgie|mines|amelioration du foyer|atelier', 'outils'),
    (r'agricult|industri|ferme|chasse|peche|environnement|recyclage|ecolog|ressources naturelles', 'industrie'),
    (r'loisir|jeux|jeu de|jouet|divertissement|magie|temps de repos|plein air|billard|recreation', 'loisirs'),
    (r'musi|spectacle|theatre|danse', 'musique-spectacle'),
    (r'\barts?\b|artistes?$|musee|esquisse|conception|inspiration', 'arts'),
    (r'educat|ecole|alphabetisation', 'education'),
    (r'religi|synagogue|chretienne', 'religion'),
    (r'\barme|militaire', 'armee'),
    (r'gouvern|justice|\bloi\b|problemes sociaux', 'societe'),
    (r'\bauto|aviation|avion|bateau|navigation|voiture|conduite|lave-auto', 'transports'),
    # Graphisme
    (r'panneaux|signalisation|securite', 'panneaux'),
    (r'fleche', 'fleches'),
    (r'symbole|signe|dingbat|icones|etoiles|formes$|tampons|graphiques|affiches|mots et', 'symboles'),
    (r'bordure|coins|frise|cadres|ornement|frontiere|bannieres', 'bordures'),
    (r'fond|texture|couleur|abstrait|agate|pierre|fractale|reflet|reflexion|motifs|dessins textiles|effets|detail', 'fonds'),
    (r'lettre|alphabet|textes|polices|nombres', 'lettres'),
    (r'calendrier|jours et dates|fuseaux|le temps vole|horloge', 'calendrier'),
    (r'fantais|fantas|fiction|contes|imagination|zodiaque|mystique|mirage|surreal', 'fantasy'),
    (r'maison|objet|decor|menage|entretien|meuble|appareil|accessoires|choses', 'maison'),
    (r'divers|cacher|elements de dessin|zones et jets|moderne$', 'divers'),
]


def norm(s):
    s = s.replace('œ', 'oe').replace('Œ', 'Oe').replace('æ', 'ae')
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r"[’'\s]+", ' ', s).strip()


SLUGS = [s for s, _ in RUBRIQUES]
_rx = [(re.compile(p), SLUGS.index(r)) for p, r in REGLES]


def rubrique(coll, dossier, nom):
    """Indice de la rubrique d'un dossier, ou None s'il n'est pas classé."""
    key = f'{coll}:{norm(nom)}'
    for rx, i in _rx:
        if rx.search(key) or rx.search(f'{coll}:{dossier}'):
            return i
    return None


if __name__ == '__main__':
    import json, os, collections
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = json.load(open(os.path.join(root, 'data/index.json')))
    cnt = collections.Counter(it[0] for it in d['items'])
    tot = collections.Counter(); folders = collections.defaultdict(list); miss = []
    for i, (c, k, nom) in enumerate(d['themes'][:]):
        cid = d['collections'][c]['id']
        r = rubrique(cid, k, nom)
        if r is None: miss.append(f'{cid}:{nom}({cnt[i]})'); continue
        tot[r] += cnt[i]; folders[r].append(f'{cid}:{nom}')
    for i, (s, n) in enumerate(RUBRIQUES):
        print(f'{tot[i]:6} {n}: ' + ' | '.join(folders[i][:400]))
    print('NON CLASSÉS', len(miss), miss)
