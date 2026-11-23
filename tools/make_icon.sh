#!/usr/bin/env bash
# Genere l'icone de l'addon FR a partir de l'avatar de Guidelime (Media/icon-source.png)
# plus un bandeau tricolore, puis verifie le format attendu par WoW.
#
#   Media/icon-256.png : avatar de la page CurseForge / Wago
#   Media/Icon.tga     : icone in-game (## IconTexture), 64x64, 32 bits, alpha
#
# Usage : tools/make_icon.sh
set -euo pipefail
cd "$(dirname "$0")/.."

MEDIA="Guidelime_ResurrectedXP_Forever_Alliance_FR/Media"
SRC="$MEDIA/icon-source.png"
BLEU="#002395"
BLANC="#FFFFFF"
ROUGE="#ED2939"

magick "$SRC" -resize 256x256 \
  \( -size 256x56 xc:none \
     -fill "$BLEU"  -draw "rectangle 0,0 84,55" \
     -fill "$BLANC" -draw "rectangle 85,0 170,55" \
     -fill "$ROUGE" -draw "rectangle 171,0 255,55" \) \
  -gravity south -composite "$MEDIA/icon-256.png"

magick "$MEDIA/icon-256.png" -resize 64x64\! -alpha on -type TrueColorAlpha \
  -define tga:compression=none "$MEDIA/Icon.tga"

python3 - "$MEDIA/Icon.tga" <<'PY'
import sys
path = sys.argv[1]
d = open(path, "rb").read()
w, h = d[12] | d[13] << 8, d[14] | d[15] << 8
kind, bpp, alpha = d[2], d[16], d[17] & 0x0F
assert (w, h) == (64, 64), "Icon.tga doit faire 64x64, pas %dx%d" % (w, h)
assert kind == 2, "Icon.tga doit etre non compresse (type 2), pas %d" % kind
assert bpp == 32 and alpha == 8, "Icon.tga doit etre 32 bits avec 8 bits alpha (%d/%d)" % (bpp, alpha)
print("Icon.tga : %dx%d, type %d, %d bits, alpha %d" % (w, h, kind, bpp, alpha))
PY

echo "icones ecrites dans $MEDIA"
