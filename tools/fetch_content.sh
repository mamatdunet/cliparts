#!/usr/bin/env bash
# Assemble le site dans public/ : le code du dépôt plus les images, téléchargées depuis les archives
# de la Release GitHub (les images ne sont pas versionnées). Lancé par Vercel à chaque déploiement.
# Usage : bash tools/fetch_content.sh   (CONTENT_RELEASE=contenu-v2 pour une autre Release)
set -euo pipefail
cd "$(dirname "$0")/.."
BASE="https://github.com/mamatdunet/cliparts/releases/download/${CONTENT_RELEASE:-contenu-v1}"
rm -rf public && mkdir -p public/cliparts
cp -R index.html assets data public/
pids=()
for c in pro mc photos web szene imsi anim masterclips mphotos office97 printartist paphotos photoartist photodisc; do
  curl -fsSL --retry 3 "$BASE/$c.tar.gz" | tar -xzf - -C public/cliparts & pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done
echo "public/ : $(find public -type f | wc -l) fichiers"
