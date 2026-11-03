# Cliparthèque

Une bibliothèque web pour parcourir, rechercher et télécharger **336 692 images** : celles de sept
CD-ROM de 1996 à 2003 (79 615 cliparts vectoriels convertis de WMF en SVG,
4 011 photos, 28 230 images web, 41 579 animations GIF et 2 335 graphismes de la scène démo)
et 180 922 dessins du domaine public d'Openclipart.

- **Cliparts Pro 12.000** (TLC Domus / Solver S.A., 1998) : 1 000 sujets nommés en français,
  en 12 000 dessins (chaque sujet seul ou avec l'un des 13 personnages récurrents).
- **Plus de 50 000 Cliparts, vol. 1** (Micro Application, réf. 4366MC, 2002) : 19 110 dessins
  rangés dans les 288 dossiers thématiques du CD (sans les 889 dessins repris du CD ClipArt & More d'IMSI).
- **Photos** (même CD) : 3 010 photos JPG en 640 px, dans les 264 dossiers du CD.
- **Images web** (même CD, Hemera Technologies 2001) : 25 000 boutons, 990 icônes, 990 puces,
  1 000 flèches et 250 traits de séparation en GIF, chaque forme en 10 couleurs.
- **Szene-Cliparts** (E.D.V. CD-ROM GmbH, 2001) : 2 335 images de la scène démo Amiga et PC
  (logos de groupes, fantasy, visages, science-fiction…), converties de PCX en PNG.
  Source : [archive.org/details/szene-cliparts-2001](https://archive.org/details/szene-cliparts-2001).
  195 images avec nudité ou contenu suggestif (liste : `tools/szene_adult.json`) ne s'affichent
  qu'une fois l'option « +18 ans » activée dans le panneau Crédits.
- **ClipArt & More 2.5 Million** (IMSI, 2003), CD 1 : 15 663 dessins en 115 thèmes, avec les mots-clés
  anglais du CD et une traduction française des dossiers et des mots-clés courants (`tools/imsi_fr.json`).
  Source : [archive.org/details/imsi-clipart-more-2.5-million-3-cd-rom](https://archive.org/details/imsi-clipart-more-2.5-million-3-cd-rom).
- **Animations web** (IMSI, 2003), CD 2 du même coffret : 41 579 GIF animés en 3D (boutons en 4 animations
  et 25 couleurs, objets, mots de pages web), chacun sur fond noir, transparent et blanc. Le CD 3 (sons) n'est pas repris.
- **Masterclips 35 000 Clip Arts** (IMSI, 1996), CD 1 : 32 842 dessins en 117 thèmes (sans nom sur le CD :
  le thème sert de nom). Le CD 2 fournit **Photos Masterclips** : 1 001 photos BMP converties en JPG.
  Source : [archive.org/details/IMSI_Masterclips_35000_ClipArts_1996Win31Eng](https://archive.org/details/IMSI_Masterclips_35000_ClipArts_1996Win31Eng).

Ce que fait le site :

- recherche instantanée sans accents ni majuscules (nom, thème, personnage, collection, mots-clés) ;
- filtres par collection (liste repliable) et par thème, avec le nombre de résultats. Les 964 dossiers des CD sont
  regroupés en 57 thèmes généraux (`tools/rubriques.py`), les sujets de Cliparts Pro un par un (`PRO_SUJETS`) ; le nom
  du dossier reste un mot-clé de recherche et un filtre depuis la fiche d'une image. Les grandes rubriques ont des
  sous-thèmes (Chats, Chiens, Fruits…, `SOUS`) ; un bouton masque ou affiche les photos, quand il y en a ; « Tout voir » ouvre tous les
  thèmes en grand, avec une vignette chacun et l'aperçu du thème choisi dans une colonne ;
- grille virtualisée : seules les vignettes visibles sont dans la page, même pour 337 000 images ;
- taille des vignettes réglable, fond blanc, damier ou sombre ;
- fiche de chaque image : variantes, couleurs ou images voisines, rotation de 90, 180 ou 270° (touche R), appliquée aussi aux fichiers, téléchargement au format d'origine, export PNG des SVG
  de 512 à 4 096 px, copie du SVG, favoris (gardés dans le navigateur) ;
- adresse partageable : la recherche, les filtres et le dessin ouvert sont dans l'URL.
- éditorial à l'accueil : une galerie du jour (fête ou saison du moment), des sélections thématiques
  et des articles sur l'histoire du clip art (« Autour des cliparts »).

## Éditorial

Tout est dans `data/editorial.json`, sans code à toucher :

- **sélections** : `{id, titre, texte, regles}`. Une image entre dans la sélection si elle répond à l'une des
  règles : `q` = recherche (tous les mots), `t` = thème `collection:dossier` (`*` final pour un préfixe), les deux
  ensemble pour chercher dans un thème. Exemple : `{"q": "fall", "t": "masterclips:saisons"}`.
- **galeries du jour** : une sélection avec `quand`, une liste de périodes `MM-JJ/MM-JJ`. La première dont une
  période contient la date du jour s'affiche à l'accueil : mettre les fêtes avant les saisons. Pour une actualité,
  ajouter en tête une période datée `2026-11-05/2026-11-08`. `paques`, `meres` et `peres` (fêtes des mères
  et des pères) acceptent un décalage : `paques-47` = mardi gras.
- **articles** : `{id, titre, date, chapo, image}` (image = `collection/dossier/fichier` d'une vignette), et le texte dans
  `data/journal/<id>.html`. Dans le texte, `<div class="planche" data-items="clé clé…"></div>` affiche des images,
  `<div class="planche" data-sel="id" data-n="8"></div>` un extrait de sélection, et
  `<div class="video" data-yt="identifiant YouTube" data-titre="…"></div>` une vidéo chargée au clic.

Adresses : `#sel=<id>` ouvre une sélection, `#a=<id>` un article, `#a=sommaire` la liste des articles.

Interface aux couleurs du design system Amuseurs (Kalam et Karla, encre et papier, ombres « pop »).

## Lancer en local

Site statique. Les images ne sont pas dans le dépôt : elles sont rangées en une archive par collection
dans la Release GitHub [`contenu-v1`](https://github.com/mamatdunet/cliparts/releases/tag/contenu-v1).
`tools/fetch_content.sh` assemble le site complet dans `public/` (code + images téléchargées) :

```bash
bash tools/fetch_content.sh
python3 -m http.server 8765 -d public
```

puis http://localhost:8765. Vercel lance ce même script à chaque déploiement (voir `vercel.json`).

## Organisation

```
index.html, assets/        l'interface (HTML, CSS, JS sans dépendance)
data/index.json            l'index unique des neuf collections
data/editorial.json        galeries du jour, sélections et liste des articles
data/journal/              le texte des articles
cliparts/pro/<thème>/      Cliparts Pro : <thème>_<personnage>_<numéro>.svg + catalog.json
cliparts/mc/<thème>/       Micro Application : <numéro>.svg + catalog.json
cliparts/photos/<thème>/   Photos : <numéro>.jpg + catalog.json
cliparts/web/<type>/       Images web : <forme><type><couleur>.gif + catalog.json
cliparts/szene/<thème>/    Szene-Cliparts : <nom>.png + catalog.json
cliparts/imsi/<thème>/     ClipArt & More : <numéro>.svg + catalog.json
cliparts/anim/<thème>/     Animations web : <code><fond B/T/W>.gif + catalog.json
cliparts/masterclips/<thème>/ Masterclips : <code>.svg + catalog.json
cliparts/mphotos/<thème>/  Photos Masterclips : <code>.jpg + catalog.json
tools/                     conversion WMF → SVG, construction de l'index, archives de contenu
licences/                  licences d'origine des CD Cliparts Pro et Micro Application
```

`data/index.json` : `rubriques` = `[slug, nom]`, `themes` = `[collection, dossier, nom, rubrique]`, `items` = `[thème, fichier, nom?, personnage?, mots-clés?]`,
`adult` = indices des images réservées à l'option +18 ans.

## Refaire la conversion

Les SVG viennent de l'atelier [WordArt 97](https://wordart-iagora.vercel.app/), qui les a
convertis depuis les images ISO des CD (non versionnées ici) :

```bash
python3 tools/build.py <NEWCLIP2 extrait de ClipartsPro.iso> cliparts/pro
python3 tools/build_mc.py <Clipart extrait de 4366MC.iso> cliparts/mc
python3 tools/build_extras.py <dossier où Photos/ et WebGen/ de 4366MC.iso sont extraits>
python3 tools/build_szene.py <GRAPHICS extrait de Szene-Cliparts (2001).iso>   # nécessite Pillow
python3 tools/build_imsi.py <CLIPART extrait de ClipaArt&More_2.5M_CD1_WIN.iso>
python3 tools/build_anim.py <racine extraite de ClipaArt&More_2.5M_CD2_WIN.iso>
python3 tools/build_masterclips.py <CLIPART du CD 1 Masterclips> <PHOTOS du CD 2 Masterclips>
python3 tools/build_index.py
bash tools/pack_content.sh contenu-v2   # publie les archives, puis mettre contenu-v2 dans fetch_content.sh
```

**Openclipart** : `python3 tools/build_openclipart.py` importe les ~185 000 dessins du domaine public
d'[openclipart.org](https://openclipart.org/) dans `cliparts/openclipart/<rubrique>/<id>.svg`. La liste vient du sitemap ;
la page de chaque dessin donne ses tags (qui choisissent la rubrique), son auteur et l'indication « Safe for Work? »
(sinon réservé à l'option +18 ans). Les SVG sont nettoyés : scripts, liens externes et données d'Inkscape ou
d'Illustrator retirés, nombres arrondis. Téléchargements en parallèle (`--parallele`, 4 conseillé : à 8 le site a fini par ne plus répondre) ; le script
ralentit puis s'arrête si le site refuse les requêtes, et reprend où il s'est arrêté (`--max N` pour un essai, `--catalogue` pour reclasser sans réseau). `build_index.py` ajoute la
collection dès que `cliparts/openclipart/catalog.json` existe.

Trop nombreux pour un déploiement Vercel (90 Go, 184 000 fichiers), ces dessins sont servis depuis un store
Vercel Blob (`cliparts-openclipart`, connecté au projet) : `cd tools && npm install && vercel env pull .env
--environment development && node --env-file=.env upload_openclipart.mjs` envoie les fichiers pas encore envoyés
et note l'adresse du store dans `cliparts/openclipart/blob.json`, que `build_index.py` reporte dans l'index.

`build_index.py` écarte les images dont le fichier est identique à une autre (4 399, surtout des dessins IMSI repris
par Micro Application et des dessins publiés deux fois sur Openclipart ; empreintes en cache dans `cliparts/_md5.json`) ; le dossier de chaque copie écartée devient un mot-clé de l'image gardée.

Les dossiers `cliparts/<collection>/` ci-dessus n'existent qu'en local (ou dans `public/` après
`fetch_content.sh`) : ils sont ignorés par git.

`tools/wmf.py` est un convertisseur WMF minimal (polygones, polylignes, rectangles, ellipses, arcs, textes,
stylos et brosses).

## Licences d'origine

Voir `licences/cliparts-pro.txt` et `licences/micro-application.txt`. En résumé : les dessins peuvent
être intégrés à vos propres créations et publiés, mais pas revendus ni redistribués en tant que
collection de clip arts. Sources : [archive.org/details/cliparts-pro](https://archive.org/details/cliparts-pro)
et [archive.org/details/4366-mc](https://archive.org/details/4366-mc).
