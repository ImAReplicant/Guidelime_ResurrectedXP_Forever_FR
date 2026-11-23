#!/usr/bin/env bash
# Genere l'icone de l'addon FR a partir de l'avatar de Guidelime (Media/icon-source.png)
# plus un bandeau tricolore, puis verifie le format attendu par WoW.
#
#   Media/icon-256.png : avatar de la page CurseForge / Wago
#   Media/Icon.tga     : icone in-game (## IconTexture), 64x64, 32 bits, alpha
#
# `-strip` sur le PNG : sans lui ImageMagick ecrit les chunks tIME/tEXt (horodatage) et chaque
# execution produirait un binaire different. La source doit etre carree (256x256).
#
# Usage : tools/make_icon.sh
set -euo pipefail
cd "$(dirname "$0")/.."

MEDIA="Guidelime_ResurrectedXP_Forever_Alliance_FR/Media"
SRC="$MEDIA/icon-source.png"
BLEU="#002395"
BLANC="#FFFFFF"
ROUGE="#ED2939"

magick "$SRC" -resize 256x256\! \
  \( -size 256x56 xc:none \
     -fill "$BLEU"  -draw "rectangle 0,0 84,55" \
     -fill "$BLANC" -draw "rectangle 85,0 170,55" \
     -fill "$ROUGE" -draw "rectangle 171,0 255,55" \) \
  -gravity south -composite -strip "$MEDIA/icon-256.png"

magick "$MEDIA/icon-256.png" -resize 64x64\! -alpha on -type TrueColorAlpha \
  -define tga:compression=none "$MEDIA/Icon.tga"

python3 - "$MEDIA/Icon.tga" "$MEDIA/icon-256.png" <<'PY'
import struct
import sys

tga, png = sys.argv[1], sys.argv[2]
d = open(tga, "rb").read()
w, h = d[12] | d[13] << 8, d[14] | d[15] << 8
kind, bpp, alpha = d[2], d[16], d[17] & 0x0F
assert (w, h) == (64, 64), "Icon.tga doit faire 64x64, pas %dx%d" % (w, h)
assert kind == 2, "Icon.tga doit etre non compresse (type 2), pas %d" % kind
assert bpp == 32 and alpha == 8, "Icon.tga doit etre 32 bits avec 8 bits alpha (%d/%d)" % (bpp, alpha)

d = open(png, "rb").read()
i, chunks = 8, []
while i < len(d):
    n = struct.unpack(">I", d[i:i + 4])[0]
    chunks.append(d[i + 4:i + 8].decode("latin1"))
    i += 12 + n
w, h = struct.unpack(">II", d[16:24])
assert (w, h) == (256, 256), "icon-256.png doit faire 256x256, pas %dx%d (source non carree ?)" % (w, h)
assert "tIME" not in chunks, "icon-256.png contient un horodatage (tIME) : sortie non deterministe"
assert "tEXt" not in chunks, "icon-256.png contient des metadonnees texte : sortie non deterministe"

print("Icon.tga : 64x64, type %d, %d bits, alpha %d" % (kind, bpp, alpha))
print("icon-256.png : 256x256, chunks %s" % " ".join(chunks))
PY

echo "icones ecrites dans $MEDIA"
