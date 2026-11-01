#!/usr/bin/env bash
# Range les images de cliparts/ en une archive par collection et les publie dans une nouvelle Release GitHub.
# Usage : bash tools/pack_content.sh contenu-v2   puis mettre ce nom par défaut dans tools/fetch_content.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=$1; OUT=$(mktemp -d)
for c in pro mc photos web szene imsi anim masterclips mphotos; do
  COPYFILE_DISABLE=1 tar --no-xattrs --exclude .DS_Store -C cliparts -czf "$OUT/$c.tar.gz" "$c"
done
gh release create "$TAG" --repo mamatdunet/cliparts --title "Contenu : images des collections" \
  --notes "Archives des images de la Cliparthèque, une par collection, téléchargées par Vercel à chaque déploiement." "$OUT"/*.tar.gz
rm -rf "$OUT"
