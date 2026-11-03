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


# Cliparts Pro n'a que 8 dossiers très larges (« Nature & animaux » mêle fruits, météo et animaux) : ses 1 000 sujets
# nommés vont un à un dans leur rubrique. Seuls les sujets qui ne vont pas dans la rubrique de leur dossier sont listés.
PRO_SUJETS = {
    'cuisine': "Ananas|Banane|Cerises|Citron|Maïs|Orange|Poire|Pommes|Raisins|Salade|Bière|Brochette de viande|Cafe|Chocolat|"
               "Condiments|Cuisine chinoise|De la confiture|Des caramels|Des pâtes|Donuts|Fromage|Hamburguer|Hot dog|Ketchup|"
               "Marshmellow|Pizza|Poulet rôti|Viande rotie|Dégustation|Boîte du goûter|Produit diététique|Glace|Chewing gum|"
               "Tasse de thé|Restaurant|Barbecue|Plat|Couteau|Presse-fruits|Mixer|Cocktail|Champagne|Glacons",
    'insectes-reptiles': "Araignee|Mouche|Papillon|Chasseur de papillons|Lézard|Serpent|Tortue|Insecticide|Chasse mouches",
    'plantes-fleurs': "Arbre|Fleur|Graine|Plante carnivore|Planter un arbre|Rose|Semis|En arrosant des fleurs|Jardinnier",
    'ciel-espace': "Arc en ciel|Arc-en-ciel|Coucher du soleil|De la pluie|Etoiles|Lune|Nuage|Orage electrique|Ouragan|Soleil|"
                   "Systeme solaire|Terre|Vent|Neige|Comète|Soucoupe volante|Navette spatiale|Satellite|Vêtement pour la lune|"
                   "Fusee spatiale|Vaisseau spatial|Astronaute|Extra terrestre|Temperature",
    'fetes': "Automne|Ete|Hiver|Printemps|Feux d'artifice|Arbre de noël|Lapin de pâques|Nouvelle année|Fete|Saint nicolas|"
             "Jour de la saint valentine",
    'oiseaux': "Coq|Oiseau|Paon|Pigeon|Cigogne",
    'paysages': "Desert|Jungle|Lagune|Montagne|Riviere|Tombée d'eau|Vague|Volcan|Inondation|Seisme|Place",
    'prehistoire': "Dinosaure|Homme des cavernes",
    'industrie': "Ecologie|Recyclage|Triage d'ordures|Recolte|Récolte|Usine|Moulin à vent|Usine d'energie|Haute tension|"
                 "Moteur a essence|Chargeur frontal|Grue pour construire|Mélangeur de ciment|Machine|Electricite|Energie|Gaz|"
                 "Structure metallique|Travailler la terre|Fermier",
    'vie-marine': "Moule|Pieuvre|Poisson|Requin",
    'animaux': "Chameau|Vache laitiere",
    'loisirs': "Camping|Balancoire|Balançoire|Boomerang|Des dards|Jeu d'echecs|Jeu de cartes|Mots croisés|Patinette|Toupie|"
               "Yo-yo|Glissoir|Trapéziste|Jeu vidéo|Joystick|Passe-temps|Ballon|Tresor|Bal|Tenue de plage|Binoculaires",
    'panneaux': "Feux rouge|Feux vert|Arretez|Defendu|Interdit de fumer|Interdit de manger|Infraction de circulation|Sortie|Limite",
    'symboles': "Fragile|Croix rouge",
    'armee': "Tank de guerre|Canon|Dynamite|Missile|Masque à gas|Soldat|Bataille",
    'fantasy': "Tapis volant|Démon|Fée|Lutin|Sorcier|Vampire|Nain|Super héros|Tarot|Clairvoyant",
    'communication': "Timbre poste|Timbre-poste|Courrier|Boîte aux lettres|Adresse|Radio|Radio personnelle|Telephone|Téléphone|"
                     "Telephone sans fil|Telecommunications|Televiseur|Télévision par cable|Machine de fax|"
                     "Répondeur téléphonique|Haut parleurs|Syntoniser|Enregistreur video|Projecteur d'images|Journaliste|"
                     "Speaker de radio|Caméraman|Publicite|Nouvelles|Publication",
    'sciences': "Aimant|Atomique|Chimie|Science|Recherche|Telescope|Geologue",
    'sante': "Radiographie|Rayons x|Médicaments|Dépistage médical|Croix rouge|Operation|Hôpital|Avoir de la fièvre|Mal au dos|"
             "Mal aux dents|Mal à la tête|Tousser|Anesthésié|Hôpitalisé|Platré|Nettoyage dentaire|Orthodontie|"
             "Rinçage pour la bouche|Sante|Aveugle|Surdité|Myope|Handicapé|Boiteux|Anti drogues|Déboucher le nez|Acupunture|"
             "Chirurgien|Dentiste|Docteur|Médecin|Masseur",
    'outils': "Boîte à outils|Perceuse|Scie électrique|Tournevis|Engrenages|Levier|Ciseaux|Hache|Pelle|Scie|Mètre à ruban|"
              "Outils menagers|Corde|Canif|Brique|Boulons",
    'calendrier': "Calendrier|Horloge|Horloge de sable|Réveil|Chronomètre à|Agenda|Etre en retard|Temps",
    'maison': "Four microondes|Refrigerateur|Ventilateur|Casse noix|Ouvre boîtes|Machine à coudre|Linterne électrique|Banc",
    'occasions': "Anniversaire|Marriage|Amour|Baiser|Fiançailles|Désillusion amoureuse",
    'famille': "Bebe|Berceuse|Biberon|Famille|Etre enceinte|Naissance|Bonne d'enfants",
    'architecture': "Capitole|Bâtiment|Pont|Rue|Cimetière|Escalier",
    'religion': "Eglise|Ange|Prêtre|Priére|Confession|Meditation",
    'voyages': "Paris|Touriste|Voyageur|Esquimau|Indien d'amérique|Mexicain",
    'education': "Ecole|1 2 3.|A b c.|Alphabet|Crayon|Gomme a effacer|Regle|Papier|Livre|Des livres|Diplôme|"
                 "Table de matières|Questionnaire|Connaissance|Professeur|Diplômé|Bibliothecaire|Formation",
    'musique-spectacle': "Theatre|Cinema|Cassette musique|Disque musique|Musique|Microphone|Piano|Chanteur|Flûtiste|"
                         "Joueur de guitarre|Joueur de harmonique|Joueur de jazz|Joueur de tambour|Joueur de trompette|"
                         "Violiniste|Tambourineur|Directeur d'orchestre|Disc jockey|Acteur|Danseur|Ballet|Directeur de cinéma|"
                         "Clown|Jongleur|Dompteur|Montreur de marionnettes|Magicien",
    'societe': "Censure|Des lois|Justice|Emprisonne|Votation|Discours|Reglements|Explosion demographique|Pouvoir|Rotary club|"
               "Greve|Chômage|Chômeur|Gouvernement|Avocat|Juge|Notaire|Policier|Politicien|President|Convict|"
               "Evadé de la justice|Bandit|Enchainé|Puni|Coupable|Innocent",
    'histoire': "Guillotine|Momie|Cowboy|Pirate|Roi|Aristocrate|Gondolier|Cocher|Calèche|Caravelle",
    'cartes-drapeaux': "Carte géographique|Drapeau",
    'vetements': "Chapeau|Cravatte|Des bas|Gant|Manteau|Pyjama|Souliers|Nouer des lacets des ch.|Lunettes|Bijoux|"
                 "Vetements de sport|Deguisement|Encapuchonné",
    'corps': "Les mains|Les pieds|Bouche|Derriere|Empreintes digitales",
    'visages': "Visage|Portrait|Gros nez|Edenté",
    'arts': "Photographie|Appareil photo|Développement photograph.|Artiste|Artiste célèbre|Peintre|Sculpteur|Potier|Designer",
    'finance': "Argent|Actions|Bourse de valeurs|Carte de credit|Cheque|Monnaie|Emission de monnaie|Des pièces|Epargnes|Budget|"
               "Dividende|Taux d'interet|Inflation|Blanchissage d'argent|Depenses|Endettement|Debiteur|Financement|"
               "Liquidite monetaire|Index des actions|Faillite|Taxe|Caissier automatique|Portefeuille|Encaissement|"
               "Excedents de caisse|Flux de caisse|Caisse|Prix|Prix de vente|Hausse de prix|Pouvoir d'achat|"
               "Rentabilite de l'investissement|Reinvestissement|Capital de travail|Des coupons|Facture|Addition|Lotterie|Or|"
               "Millionaire|Vendeur d'assurances",
    'transports': "Péage|Parcmétre|Chauffeur de taxi|Mécanicien de voitures|Laver des voitures|Vente de voitures|"
                  "Batterie automobile|Congestion|Pilote de course|Motocycliste",
    'sports': "Arbitre|Lutteur|Cavalier|Toréro",
}
PRO = {}
for _r, _noms in PRO_SUJETS.items():
    for _n in _noms.split('|'):
        PRO.setdefault(norm(_n), _r)

# Sous-thèmes des grandes rubriques : une image y figure si l'un des mots (ou son pluriel en s ou x) est un mot de son
# nom, de son dossier ou de ses mots-clés. Mots sans accents ; français et anglais, Openclipart étant en anglais.
SOUS = {
    'animaux': [
        ('Chats', 'chat chaton cat kitten kitty felin feline'),
        ('Chiens', 'chien chiot dog puppy caniche'),
        ('Chevaux', 'cheval chevaux poney horse pony'),
        ('Ferme', 'vache cochon porc mouton chevre ane cow pig sheep goat donkey lamb ferme farm bull taureau'),
        ('Savane et jungle', 'lion tigre elephant girafe zebre singe gorille leopard rhinoceros hippopotame tiger giraffe zebra '
                             'monkey gorilla rhino hippo cheetah'),
        ('Forêt', 'ours renard loup cerf biche ecureuil herisson bear fox wolf deer squirrel hedgehog raccoon moose'),
        ('Lapins et rongeurs', 'lapin souris rat hamster rabbit bunny mouse castor beaver'),
    ],
    'plantes-fleurs': [
        ('Arbres', 'arbre tree palmier palm sapin pin oak chene'),
        ('Fleurs', 'fleur flower rose tulipe tulip marguerite daisy tournesol sunflower bouquet lys lily'),
        ('Feuilles', 'feuille leaf leaves'),
        ('Champignons', 'champignon mushroom'),
        ('Cactus et plantes grasses', 'cactus succulent'),
    ],
    'gens': [
        ('Hommes', 'homme man men monsieur gentleman businessman'),
        ('Femmes', 'femme woman women madame lady girl fille'),
        ('Enfants', 'enfant child children kid kids boy garcon bebe baby gamin'),
        ('Personnes âgées', 'vieux vieille elderly grandmother grandfather grand-mere grand-pere'),
        ('Silhouettes', 'silhouette'),
        ('Avatars', 'avatar'),
    ],
    'cuisine': [
        ('Fruits', 'fruit pomme banane orange poire cerise raisin ananas fraise citron apple banana pear cherry grape pineapple '
                   'strawberry lemon'),
        ('Légumes', 'legume vegetable carotte tomate carrot tomato salade lettuce chou cabbage oignon onion'),
        ('Boissons', 'boisson drink cafe coffee the tea biere beer vin wine cocktail jus juice'),
        ('Desserts et sucreries', 'gateau dessert bonbon chocolat glace cake candy cookie biscuit tarte pie'),
        ('Pain et fromage', 'pain fromage bread cheese croissant baguette'),
        ('Plats', 'pizza hamburger sandwich pates spaghetti soupe soup plat meal'),
        ('Ustensiles', 'couteau fourchette cuillere casserole poele knife fork spoon pan pot ustensile'),
    ],
    'symboles': [
        ('Icônes', 'icone icon'),
        ('Boutons', 'bouton button'),
        ('Logos et emblèmes', 'logo emblem embleme badge'),
        ('Formes', 'forme shape cercle circle carre square triangle hexagone hexagon etoile star'),
    ],
    'bordures': [
        ('Cadres', 'cadre frame'),
        ('Coins', 'coin corner'),
        ('Frises et séparateurs', 'frise bordure border divider separateur'),
        ('Ornements', 'ornement ornament flourish arabesque'),
    ],
    'transports': [
        ('Voitures', 'voiture car auto automobile'),
        ('Avions', 'avion plane airplane aircraft biplane jet'),
        ('Bateaux', 'bateau boat ship navire voilier sailboat'),
        ('Trains', 'train locomotive tram metro'),
        ('Vélos et motos', 'velo bicyclette bicycle bike moto motocyclette motorcycle scooter'),
        ('Camions et bus', 'camion truck bus autobus'),
    ],
    'fetes': [
        ('Noël', 'noel christmas xmas santa sapin'),
        ('Halloween', 'halloween citrouille pumpkin sorciere witch'),
        ('Pâques', 'paques easter'),
        ('Saint-Valentin', 'valentin valentine'),
        ('Saisons', 'printemps ete automne hiver spring summer autumn winter saisons'),
    ],
    'fonds': [
        ('Motifs', 'motif pattern seamless'),
        ('Textures', 'texture'),
        ('Dégradés', 'degrade gradient'),
        ('Abstraits', 'abstrait abstract'),
    ],
    'cartes-drapeaux': [
        ('Drapeaux', 'drapeau flag'),
        ('Cartes', 'carte map'),
        ('Globes', 'globe'),
    ],
    'sports': [
        ('Football', 'football soccer'),
        ('Basket', 'basket basketball'),
        ('Tennis', 'tennis'),
        ('Vélo', 'velo bicyclette bicycle bike cycling cyclist'),
        ('Sports d\'hiver', 'ski skieur patin skating snowboard luge'),
        ('Natation et plongée', 'natation nageur swimming swimmer plongee diving'),
        ('Golf', 'golf'),
    ],
    'oiseaux': [
        ('Basse-cour', 'poule coq poussin canard oie dindon chicken hen rooster chick duck goose turkey'),
        ('Rapaces', 'aigle hibou chouette faucon eagle owl hawk falcon vulture'),
        ('Oiseaux exotiques', 'perroquet toucan flamant paon parrot toucan flamingo peacock tropicaux'),
        ('Oiseaux marins', 'mouette pelican pingouin manchot seagull pelican penguin'),
    ],
}

SLUGS = [s for s, _ in RUBRIQUES]
_rx = [(re.compile(p), SLUGS.index(r)) for p, r in REGLES]


def rubrique(coll, dossier, nom):
    """Indice de la rubrique d'un dossier, ou None s'il n'est pas classé."""
    if coll == 'openclipart':  # dessins déjà rangés par rubrique, « dossier.rubrique » s'ils ont changé (build_openclipart.py)
        return SLUGS.index(dossier.split('.')[-1])
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
