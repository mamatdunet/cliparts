# Cliparthèque

Une bibliothèque web pour parcourir, rechercher et télécharger **31 999 cliparts vectoriels**
issus de deux CD-ROM de la fin des années 90, convertis de WMF en SVG.

- **Cliparts Pro 12.000** (TLC Domus / Solver S.A., 1998) : 1 000 sujets nommés en français,
  en 12 000 dessins (chaque sujet seul ou avec l'un des 13 personnages récurrents).
- **Plus de 50 000 Cliparts, vol. 1** (Micro Application, réf. 4366MC, 2002) : 19 999 dessins
  rangés dans les 288 dossiers thématiques du CD.

Ce que fait le site :

- recherche instantanée sans accents ni majuscules (nom, thème, personnage, collection) ;
- filtres par collection et par thème, avec le nombre de résultats ;
- grille virtualisée : seules les vignettes visibles sont dans la page, même pour 32 000 dessins ;
- taille des vignettes réglable, fond blanc, damier ou sombre ;
- fiche de chaque dessin : variantes ou dessins voisins, téléchargement SVG, export PNG
  de 512 à 4 096 px, copie du SVG, favoris (gardés dans le navigateur) ;
- adresse partageable : la recherche, les filtres et le dessin ouvert sont dans l'URL.

Interface aux couleurs du design system Amuseurs (Kalam et Karla, encre et papier, ombres « pop »).

## Lancer en local

Site statique, sans build :

```bash
python3 -m http.server 8765
```

puis http://localhost:8765. Déployable tel quel sur Vercel (voir `vercel.json`) ou tout hébergeur statique.

## Organisation

```
index.html, assets/        l'interface (HTML, CSS, JS sans dépendance)
data/index.json            l'index unique des deux collections
cliparts/pro/<thème>/      Cliparts Pro : <thème>_<personnage>_<numéro>.svg + catalog.json
cliparts/mc/<thème>/       Micro Application : <numéro>.svg + catalog.json
tools/                     conversion WMF → SVG et construction de l'index
```

`data/index.json` : `themes` = `[collection, dossier, nom]`, `items` = `[thème, fichier, nom?, personnage?]`.

## Refaire la conversion

Les SVG viennent de l'atelier [WordArt 97](https://wordart-iagora.vercel.app/), qui les a
convertis depuis les images ISO des CD (non versionnées ici) :

```bash
python3 tools/build.py <NEWCLIP2 extrait de ClipartsPro.iso> cliparts/pro
python3 tools/build_mc.py <Clipart extrait de 4366MC.iso> cliparts/mc
python3 tools/build_index.py
```

`tools/wmf.py` est un convertisseur WMF minimal (polygones, polylignes, stylos et brosses).

## Licences d'origine

Voir `cliparts/pro/LISEZMOI.txt` et `cliparts/mc/LISEZMOI.txt`. En résumé : les dessins peuvent
être intégrés à vos propres créations et publiés, mais pas revendus ni redistribués en tant que
collection de clip arts. Sources : [archive.org/details/cliparts-pro](https://archive.org/details/cliparts-pro)
et [archive.org/details/4366-mc](https://archive.org/details/4366-mc).
