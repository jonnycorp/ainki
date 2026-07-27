#!/usr/bin/env bash
# Build ainki-<version>.ankiaddon for AnkiWeb upload or manual install.
# Usage: ./build.sh [version]   e.g. ./build.sh 1.0.0
set -euo pipefail
cd "$(dirname "$0")"

VERSION="${1:-dev}"
OUT="$PWD/dist/ainki-${VERSION}.ankiaddon"
mkdir -p dist
rm -f "$OUT"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# meta.json holds runtime user state (including the API key) and must never ship.
rsync -a addon/ "$STAGE"/ \
  --exclude meta.json \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude '._*'

# AGPL requires the license text to travel with the distribution.
cp LICENSE "$STAGE"/

# manifest.json is required for manual .ankiaddon installs; AnkiWeb ignores it.
cat > "$STAGE/manifest.json" <<EOF
{"package": "ainki", "name": "ainki", "human_version": "${VERSION}"}
EOF

# AnkiWeb expects the files at the zip root, not inside a folder.
(cd "$STAGE" && zip -qr "$OUT" .)

echo "Built $OUT"
unzip -l "$OUT"
