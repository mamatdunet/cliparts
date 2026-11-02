"""Importe les dessins d'Openclipart (openclipart.org, domaine public CC0) dans cliparts/openclipart.
Usage : python3 tools/build_openclipart.py [--max N] [--parallele 8] [--pause 0] [--relister] [--catalogue]

1. La liste des dessins vient du sitemap public (identifiant, titre, adresse du SVG).
2. Pour chaque dessin : la page du dessin (tags, auteur, « Safe for Work ? »), puis le SVG, nettoyé
   (scripts, liens externes et données d'éditeur retirés) et rangé dans le dossier de sa rubrique :
   cliparts/openclipart/<rubrique>/<id>.svg. La rubrique se déduit des tags anglais (TAGS ci-dessous).
3. catalog.json est réécrit ; un dessin dont la rubrique a changé (TAGS modifié) est déplacé.

Deux requêtes par dessin, sur --parallele connexions à la fois (8 par défaut, pour ne pas surcharger ce petit site
bénévole) ; --pause N espace en plus les requêtes de N secondes. Si le site répond « trop de requêtes » (429) ou se
met en erreur, le script ralentit, puis s'arrête proprement si ça dure : il vaut mieux abandonner qu'insister.
Le script reprend où il s'est arrêté : les pages lues sont gardées dans cliparts/_openclipart/fiches.jsonl.
--max N s'arrête après N nouveaux dessins ; --catalogue refait seulement le catalogue, sans réseau ;
--relister relit le sitemap pour prendre les dessins publiés depuis."""
import sys, os, re, json, time, math, html, argparse, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rubriques import RUBRIQUES
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dst = os.path.join(root, 'cliparts/openclipart')
cache = os.path.join(root, 'cliparts/_openclipart')
SITE = 'https://openclipart.org'
UA = 'Cliparthèque, import des dessins du domaine public (matthieuchatry@gmail.com)'
FR = json.load(open(os.path.join(root, 'tools/imsi_fr.json')))['keywords']

# Tags anglais → rubrique. Chaque tag qui figure dans une liste donne deux points à la rubrique, chaque mot du titre
# un point ; la mieux notée l'emporte, la première de la liste en cas d'égalité ; sans point : « divers ».
# Un mot présent dans deux listes compte pour la première.
TAGS = {
    'humour': 'comic comics caricature funny humor humour joke meme smiley emoji emoticon mascot',
    'prehistoire': 'dinosaur dinosaurs dino prehistoric fossil mammoth caveman trex t-rex',
    'oiseaux': 'bird birds owl eagle parrot duck chicken hen rooster penguin swan crow raven pigeon dove sparrow robin flamingo',
    'vie-marine': 'fish fishes shark whale dolphin octopus crab jellyfish seahorse marine sea-life underwater coral shell seashell lobster',
    'insectes-reptiles': 'insect insects bug bugs butterfly bee ant spider ladybug ladybird dragonfly snake reptile lizard turtle frog crocodile beetle amphibian salamander',
    'animaux': 'animal animals cat cats kitten dog dogs puppy horse cow pig sheep goat rabbit bunny mouse rat bear lion tiger elephant '
               'giraffe monkey fox wolf deer zebra squirrel pet pets mammal wildlife hedgehog panda',
    'plantes-fleurs': 'flower flowers plant plants tree trees leaf leaves rose tulip garden botanical floral flora grass mushroom cactus '
                      'vegetation forest bush daisy sunflower',
    'ciel-espace': 'space planet planets star moon sun sky cloud clouds weather rain snow snowflake rocket astronaut galaxy comet storm rainbow',
    'paysages': 'landscape nature mountain mountains river lake beach island desert scenery sunset waterfall volcano hill',
    'cartes-drapeaux': 'map maps flag flags country globe world continent geography atlas',
    'architecture': 'building buildings house home architecture castle church tower bridge city skyline city skyscraper temple ruins',
    'voyages': 'travel tourism vacation holiday luggage suitcase hotel landmark',
    'fetes': 'christmas xmas santa halloween pumpkin easter valentine valentines thanksgiving hanukkah party celebration '
             'fireworks new-year carnival autumn spring winter summer',
    'occasions': 'love heart hearts wedding birthday anniversary gift present cake baby-shower',
    'visages': 'face faces portrait head avatar profile',
    'famille': 'family child children kid kids baby boy girl mother father parents',
    'gens': 'people person man woman men women silhouette human character',
    'metiers': 'job jobs work worker profession police firefighter doctor nurse chef farmer builder occupation',
    'bureau': 'office business businessman meeting desk shop store commerce marketing',
    'finance': 'money finance dollar euro coin coins bank cash currency bitcoin',
    'informatique': 'computer computers technology tech internet network electronics phone smartphone robot laptop keyboard mouse-pointer software hardware disk hard-drive server',
    'communication': 'communication media television tv radio newspaper camera film movie mail envelope book books',
    'sciences': 'science chemistry physics biology laboratory lab atom molecule microscope math mathematics geometry fraction',
    'sante': 'medical medicine health hospital pill pills virus covid doctor-bag first-aid dental tooth',
    'corps': 'body anatomy hand hands eye eyes skeleton skull brain foot',
    'cuisine': 'food fruit fruits vegetable vegetables drink drinks kitchen cooking meal coffee tea beer wine bread cheese apple '
               'pizza dessert candy breakfast cup',
    'maison': 'furniture chair table lamp bed sofa household object objects appliance key bottle doll seal certificate',
    'vetements': 'clothing clothes fashion dress shirt hat shoe shoes costume jewelry',
    'outils': 'tool tools hammer wrench screwdriver saw axe ax hatchet construction diy hardware-tool',
    'industrie': 'industry factory agriculture farm tractor energy recycling ecology environment oil',
    'sports': 'sport sports football soccer basketball baseball tennis golf ball bike bicycle cycling running swimming ski fitness olympic',
    'loisirs': 'game games toy toys play card cards chess puzzle dice hobby circus playing-card',
    'musique-spectacle': 'music musical instrument guitar piano drum violin note notes theater theatre dance singer concert',
    'arts': 'art painting artist paint drawing sketch sculpture museum design',
    'gravures': 'vintage engraving antique victorian woodcut etching old-book retro-illustration',
    'education': 'school education student teacher classroom university pencil learning',
    'histoire': 'history historical medieval knight ancient egypt roman greek viking pirate',
    'religion': 'religion religious christian cross angel bible church-symbol jesus islam jewish buddha',
    'armee': 'military army war weapon gun soldier tank sword',
    'societe': 'politics government law justice protest election',
    'transports': 'car cars vehicle vehicles truck bus train airplane plane aircraft aeroplane boat ship transport transportation '
                  'motorcycle helicopter traffic-vehicle',
    'panneaux': 'sign signs road-sign traffic warning safety hazard signage',
    'fleches': 'arrow arrows',
    'symboles': 'icon icons symbol symbols pictogram button buttons shape shapes logo emblem badge',
    'bordures': 'border borders frame frames ornament ornaments decoration decorative divider corner flourish',
    'fonds': 'background backgrounds pattern patterns texture seamless abstract wallpaper tile',
    'lettres': 'letter letters alphabet font text typography number numbers word',
    'calendrier': 'calendar time clock clock-face date month',
    'fantasy': 'fantasy dragon unicorn fairy monster magic wizard witch mythology alien zombie ghost',
}
SLUGS = [s for s, _ in RUBRIQUES]
NOMS = dict(RUBRIQUES)
ORDRE = list(TAGS)
WORD = {}
for r, ws in TAGS.items():
    assert r in NOMS, r
    for w in ws.split():
        WORD.setdefault(w, r)


def rubrique(tags, titre):
    score = {}
    def add(w, n):
        r = WORD.get(w) or (w.endswith('s') and WORD.get(w[:-1]))  # pluriel : « clocks » → « clock »
        if r: score[r] = score.get(r, 0) + n
    for tag in tags:
        if tag.replace(' ', '-') in WORD: add(tag.replace(' ', '-'), 2)
        else:  # tag de plusieurs mots : chaque mot connu compte moitié
            for x in tag.split(): add(x, 2 if ' ' not in tag else 1)
    for w in re.findall(r'[a-z]+', titre.lower()):
        add(w, 1)
    return max(score, key=lambda r: (score[r], -ORDRE.index(r))) if score else 'divers'


# ---------- Réseau ----------
last, verrou = 0.0, threading.Lock()
class Limite(Exception):
    """Le site refuse ou n'arrive plus à suivre : on arrête tout."""

def get(url, pause):
    """Le contenu de url (None s'il n'existe plus). Après un refus (429, avec son Retry-After) ou une erreur du serveur,
    attend 2, 4, 8, 16 puis 32 s avant de réessayer ; au-delà, lève Limite."""
    global last
    for essai in range(6):
        if pause:
            with verrou:
                time.sleep(max(0, last + pause - time.time())); last = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410): return None
            if e.code in (401, 403): raise Limite(f'{url} : accès refusé ({e.code}), le site nous bloque sans doute')
            if e.code not in (429, 500, 502, 503, 504): raise
            attente = int(e.headers.get('Retry-After') or 0) if (e.headers.get('Retry-After') or '').isdigit() else 0
            if attente > 300: raise Limite(f'{url} : le site demande d\'attendre {attente} s')
            time.sleep(max(attente, 2 ** (essai + 1)))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 ** (essai + 1))
    raise Limite(f'{url} : le site ne répond plus ou refuse les requêtes')


def lister(pause):
    """Le sitemap : [id, titre, adresse du SVG] de chaque dessin, du plus récent au plus ancien."""
    idx = get(SITE + '/sitemap.xml', pause).decode()
    out = []
    for sm in re.findall(r'<loc>([^<]+)</loc>', idx):
        t = get(sm, pause).decode()
        for u in re.findall(r'(?s)<url>(.*?)</url>', t):
            m = re.search(r'<loc>' + re.escape(SITE) + r'/detail/(\d+)/', u)
            svg = re.search(r'<image:loc>([^<]+\.svg)</image:loc>', u)
            if m and svg:
                ti = re.search(r'<image:title>([^<]*)</image:title>', u)
                out.append([int(m[1]), html.unescape(ti[1]).strip() if ti else '', html.unescape(svg[1])])
        print(f'\r{len(out)} dessins listés', end='', flush=True)
    print()
    return out


def fiche(id, pause):
    """Tags, auteur et « Safe for Work ? » de la page du dessin (None si elle n'existe plus)."""
    page = get(f'{SITE}/detail/{id}', pause)
    if page is None: return None
    t = page.decode('utf-8', 'replace')
    tags = [html.unescape(x).strip().lower() for x in re.findall(r'href="/tag/[^"]*"[^>]*>([^<]*)</a>', t)]
    auteur = re.search(r'"artist":\s*\{[^}]*"name":\s*"([^"]*)"', t)
    sfw = re.search(r'Safe for Work\?</dt>\s*<dd[^>]*>\s*(\w+)', t)
    return {'tags': [x for x in tags if x and not x.startswith('remix') and '<' not in x],
            'auteur': json.loads(f'"{auteur[1]}"') if auteur else '',
            'nsfw': bool(sfw and sfw[1].lower() == 'no')}


# ---------- Nettoyage des SVG ----------
# Les SVG sont déposés par n'importe qui : on retire ce qui pourrait s'exécuter ou charger autre chose
# quand le fichier est ouvert directement (scripts, on*, liens externes), et les données d'éditeur
# (Inkscape, Illustrator, métadonnées) qui alourdissent les fichiers sans rien changer au dessin.
SVG, XLINK = 'http://www.w3.org/2000/svg', 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG); ET.register_namespace('xlink', XLINK)
EDITEURS = ('sodipodi', 'inkscape', 'ns.adobe.com', 'purl.org/dc', 'creativecommons.org/ns', 'www.w3.org/1999/02/22-rdf')
INTERDITS = {'script', 'foreignObject', 'iframe', 'embed', 'object', 'metadata', 'handler', 'listener'}


def ns_local(tag):
    return tuple(tag[1:].split('}', 1)) if tag.startswith('{') else ('', tag)


def nettoyer(data):
    t = data.decode('utf-8', 'replace')
    # Entités du DOCTYPE (fichiers Illustrator : xmlns="&ns_svg;") remplacées à la main, puis DOCTYPE retiré
    ents = dict(re.findall(r'<!ENTITY\s+(\w+)\s+"([^"&<]*)"\s*>', t))
    t = re.sub(r'(?s)<!DOCTYPE[^\[>]*(\[.*?\])?\s*>', '', t, count=1)
    t = re.sub(r'&(\w+);', lambda m: ents.get(m[1], m[0]), t)
    if '<!ENTITY' in t: return None
    try:
        rt = ET.fromstring(t.encode())
    except ET.ParseError:
        return None
    if ns_local(rt.tag) != (SVG, 'svg'): return None

    def walk(el):
        for ch in list(el):
            ns, tag = ns_local(ch.tag) if isinstance(ch.tag, str) else ('', '')
            if not isinstance(ch.tag, str) or tag in INTERDITS or any(e in ns for e in EDITEURS) \
                    or (tag in ('set', 'animate') and 'href' in ch.get('attributeName', '')):
                el.remove(ch); continue
            walk(ch)
        for k in list(el.attrib):
            ns, a = ns_local(k)
            v = el.attrib[k].strip()
            if a.lower().startswith('on') or any(e in ns for e in EDITEURS) \
                    or (a == 'href' and not (v.startswith('#') or v.startswith('data:image/'))):
                del el.attrib[k]
        if ns_local(el.tag)[1] == 'style' and el.text:
            el.text = re.sub(r'@import[^;]*;?', '', el.text)
    walk(rt)
    alleger(rt)
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rt, encoding='utf-8', xml_declaration=False)


NUM = re.compile(r'-?\d*\.\d+(?:e-?\d+)?')
def alleger(rt):
    """Arrondit les nombres (Inkscape en écrit 6 à 8 décimales) à un cent-millième de la taille du dessin,
    et retire les blancs entre les balises : les fichiers perdent souvent un tiers de leur poids."""
    vb = [float(x) for x in re.findall(r'-?[\d.]+(?:e-?\d+)?', rt.get('viewBox', ''))[2:4] if float(x) > 0]
    size = max(vb) if vb else 1000
    dec = min(6, max(1, math.ceil(5 - math.log10(size))))
    fmt = lambda m: (f'{float(m[0]):.{dec}f}'.rstrip('0').rstrip('.') or '0') if len(m[0].split('.')[-1]) > dec else m[0]
    for el in rt.iter():
        for k, v in el.attrib.items():
            if not v.startswith('data:'): el.set(k, NUM.sub(fmt, v))
        if ns_local(el.tag)[1] not in ('text', 'tspan', 'textPath', 'title', 'desc', 'style'):
            if el.text and not el.text.strip(): el.text = None
        if el.tail and not el.tail.strip(): el.tail = None


# ---------- Catalogue ----------
def catalogue(liste, fiches):
    """Range chaque SVG dans le dossier de sa rubrique (le déplace si elle a changé) et écrit catalog.json."""
    ici = {}
    for d in os.listdir(dst) if os.path.isdir(dst) else []:
        if os.path.isdir(os.path.join(dst, d)):
            for f in os.listdir(os.path.join(dst, d)):
                if f.endswith('.svg'): ici[int(f[:-4])] = d
    themes, items, moved = {}, [], 0
    for id, titre, _ in liste:
        fi = fiches.get(id)
        if not fi or id not in ici: continue
        r = rubrique(fi['tags'], titre)
        if ici[id] != r:
            os.makedirs(os.path.join(dst, r), exist_ok=True)
            os.replace(os.path.join(dst, ici[id], f'{id}.svg'), os.path.join(dst, r, f'{id}.svg'))
            moved += 1
        themes.setdefault(r, NOMS[r])
        # Mots-clés : tags anglais, leur traduction quand tools/imsi_fr.json la connaît, et l'auteur
        words = []
        for w in [FR.get(x, '') for x in fi['tags']] + fi['tags'] + [fi['auteur']]:
            for x in w.lower().split():
                if x not in words: words.append(x)
        items.append([r, str(id), titre, ' '.join(words), fi['auteur']] + ([1] if fi['nsfw'] else []))
    order = sorted(themes, key=SLUGS.index)
    tidx = {k: i for i, k in enumerate(order)}
    json.dump({'source': 'Openclipart (openclipart.org), dessins versés dans le domaine public (CC0 1.0)',
               'chemin': 'cliparts/openclipart/{dossier}/{n}.svg', 'themes': [[k, themes[k]] for k in order],
               'items': [[tidx[it[0]]] + it[1:] for it in items]},
              open(os.path.join(dst, 'catalog.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print('openclipart', len(items), 'dessins', len(order), 'rubriques', moved, 'déplacés',
          sum(len(it) > 5 for it in items), 'réservés +18')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max', type=int, default=0)
    ap.add_argument('--parallele', type=int, default=8)
    ap.add_argument('--pause', type=float, default=0)
    ap.add_argument('--relister', action='store_true')
    ap.add_argument('--catalogue', action='store_true')
    o = ap.parse_args()
    os.makedirs(cache, exist_ok=True); os.makedirs(dst, exist_ok=True)
    lp, fp = os.path.join(cache, 'liste.json'), os.path.join(cache, 'fiches.jsonl')
    if o.relister or not os.path.exists(lp):
        if o.catalogue: sys.exit('Pas encore de liste : lancer le script sans --catalogue')
        json.dump(lister(o.pause), open(lp, 'w'), ensure_ascii=False)
    seen = set()  # le sitemap cite quelques centaines de dessins deux fois
    liste = [x for x in json.load(open(lp)) if not (x[0] in seen or seen.add(x[0]))]
    fiches = {}
    if os.path.exists(fp):
        for line in open(fp):
            d = json.loads(line); fiches[d['id']] = d.get('fiche')
    if not o.catalogue:
        log = open(fp, 'a')
        todo = [x for x in liste if x[0] not in fiches][:o.max or None]
        new = fails = 0
        t0 = time.time()

        def lire(id, titre, svg):
            fi = fiche(id, o.pause)
            if fi is None: return id, titre, None, None
            data = get(svg, o.pause)
            return id, titre, fi, nettoyer(data) if data else None

        pool = ThreadPoolExecutor(o.parallele)
        en_cours, it = set(), iter(todo)
        try:
            while True:
                while len(en_cours) < o.parallele * 2 and (x := next(it, None)):
                    en_cours.add(pool.submit(lire, *x))
                if not en_cours: break
                faits, en_cours = wait(en_cours, return_when=FIRST_COMPLETED)
                for f in faits:
                    id, titre, fi, clean = f.result()
                    if fi is not None and clean is None:
                        fi = None; fails += 1
                    elif fi is not None:
                        r = rubrique(fi['tags'], titre)
                        os.makedirs(os.path.join(dst, r), exist_ok=True)
                        open(os.path.join(dst, r, f'{id}.svg'), 'wb').write(clean)
                    # La ligne n'est écrite qu'une fois le SVG enregistré : un arrêt en cours de route refait ce dessin
                    log.write(json.dumps({'id': id, 'fiche': fi}, ensure_ascii=False) + '\n'); log.flush()
                    fiches[id] = fi; new += 1
                vitesse = new / max(1, time.time() - t0)
                reste = (len(todo) - new) / max(vitesse, 1e-9) / 3600
                print(f'\r{len(fiches)}/{len(liste)} dessins lus, {fails} illisibles, {vitesse:.1f}/s, encore {reste:.1f} h',
                      end='', flush=True)
        except Limite as e:
            print(f'\nArrêt : {e}')
        except KeyboardInterrupt:
            print('\nInterrompu : relancer la même commande pour reprendre.')
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        print()
    catalogue(liste, fiches)


if __name__ == '__main__':
    main()
