# Cliparthèque

Une bibliothèque web pour parcourir, rechercher et télécharger **122 845 images** issues de cinq
CD-ROM de 1998 à 2003 : 47 662 cliparts vectoriels (convertis de WMF en SVG),
3 010 photos, 28 250 images web, 41 579 animations GIF et 2 344 graphismes de la scène démo.

- **Cliparts Pro 12.000** (TLC Domus / Solver S.A., 1998) : 1 000 sujets nommés en français,
  en 12 000 dessins (chaque sujet seul ou avec l'un des 13 personnages récurrents).
- **Plus de 50 000 Cliparts, vol. 1** (Micro Application, réf. 4366MC, 2002) : 19 999 dessins
  rangés dans les 288 dossiers thématiques du CD.
- **Photos** (même CD) : 3 010 photos JPG en 640 px, dans les 264 dossiers du CD.
- **Images web** (même CD, Hemera Technologies 2001) : 25 000 boutons, 1 000 icônes, 1 000 puces,
  1 000 flèches et 250 traits de séparation en GIF, chaque forme en 10 couleurs.
- **Szene-Cliparts** (E.D.V. CD-ROM GmbH, 2001) : 2 344 images de la scène démo Amiga et PC
  (logos de groupes, fantasy, visages, science-fiction…), converties de PCX en PNG.
  Source : [archive.org/details/szene-cliparts-2001](https://archive.org/details/szene-cliparts-2001).
  196 images avec nudité ou contenu suggestif (liste : `tools/szene_adult.json`) ne s'affichent
  qu'une fois l'option « +18 ans » activée dans le panneau Crédits.
- **ClipArt & More 2.5 Million** (IMSI, 2003), CD 1 : 15 663 dessins en 115 thèmes, avec les mots-clés
  anglais du CD et une traduction française des dossiers et des mots-clés courants (`tools/imsi_fr.json`).
  Source : [archive.org/details/imsi-clipart-more-2.5-million-3-cd-rom](https://archive.org/details/imsi-clipart-more-2.5-million-3-cd-rom).
- **Animations web** (IMSI, 2003), CD 2 du même coffret : 41 579 GIF animés en 3D (boutons en 4 animations
  et 25 couleurs, objets, mots de pages web), chacun sur fond noir, transparent et blanc. Le CD 3 (sons) n'est pas repris.

Ce que fait le site :

- recherche instantanée sans accents ni majuscules (nom, thème, personnage, collection, mots-clés) ;
- filtres par collection et par thème, avec le nombre de résultats ;
- grille virtualisée : seules les vignettes visibles sont dans la page, même pour 122 000 images ;
- taille des vignettes réglable, fond blanc, damier ou sombre ;
- fiche de chaque image : variantes, couleurs ou images voisines, téléchargement au format d'origine, export PNG des SVG
  de 512 à 4 096 px, copie du SVG, favoris (gardés dans le navigateur) ;
- adresse partageable : la recherche, les filtres et le dessin ouvert sont dans l'URL.

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
data/index.json            l'index unique des sept collections
cliparts/pro/<thème>/      Cliparts Pro : <thème>_<personnage>_<numéro>.svg + catalog.json
cliparts/mc/<thème>/       Micro Application : <numéro>.svg + catalog.json
cliparts/photos/<thème>/   Photos : <numéro>.jpg + catalog.json
cliparts/web/<type>/       Images web : <forme><type><couleur>.gif + catalog.json
cliparts/szene/<thème>/    Szene-Cliparts : <nom>.png + catalog.json
cliparts/imsi/<thème>/     ClipArt & More : <numéro>.svg + catalog.json
cliparts/anim/<thème>/     Animations web : <code><fond B/T/W>.gif + catalog.json
tools/                     conversion WMF → SVG, construction de l'index, archives de contenu
licences/                  licences d'origine des CD Cliparts Pro et Micro Application
```

`data/index.json` : `themes` = `[collection, dossier, nom]`, `items` = `[thème, fichier, nom?, personnage?, mots-clés?]`,
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
python3 tools/build_index.py
bash tools/pack_content.sh contenu-v2   # publie les archives, puis mettre contenu-v2 dans fetch_content.sh
```

Les dossiers `cliparts/<collection>/` ci-dessus n'existent qu'en local (ou dans `public/` après
`fetch_content.sh`) : ils sont ignorés par git.

`tools/wmf.py` est un convertisseur WMF minimal (polygones, polylignes, stylos et brosses).

## Licences d'origine

Voir `licences/cliparts-pro.txt` et `licences/micro-application.txt`. En résumé : les dessins peuvent
être intégrés à vos propres créations et publiés, mais pas revendus ni redistribués en tant que
collection de clip arts. Sources : [archive.org/details/cliparts-pro](https://archive.org/details/cliparts-pro)
et [archive.org/details/4366-mc](https://archive.org/details/4366-mc).
