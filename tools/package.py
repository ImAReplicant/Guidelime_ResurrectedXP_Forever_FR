#!/usr/bin/env python3
"""Empaquette l'addon FR dans dist/ avec le nom de dossier attendu par WoW.

Le dossier racine du zip doit s'appeler exactement comme le .toc : un zip GitHub nomme
"-main", ou un dossier renomme, n'est jamais charge par le client.

Usage : python3 tools/package.py
Sortie : dist/Guidelime_ResurrectedXP_Forever_Alliance_FR.zip
"""
import glob
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from addon import ADDON as FR, OUT as SRC_DIR, TOC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["Speedrun", "Dungeon Route", "Riverglades"]


def main():
    src = SRC_DIR
    if not os.path.exists(os.path.join(src, TOC)):
        raise SystemExit("addon introuvable : %s (lancer tools/build_fr.py ou verifier ADDON_NAME)" % src)
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    path = os.path.join(dist, FR + ".zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(src, TOC), FR + "/" + TOC)
        for d in DIRS:
            for guide in sorted(glob.glob(os.path.join(src, d, "*.lua"))):
                zf.write(guide, "%s/%s/%s" % (FR, d, os.path.basename(guide)))
        for media in sorted(glob.glob(os.path.join(src, "Media", "*"))):
            # sources et visuels de page (CurseForge/Wago) : hors du zip d'addon
            if os.path.basename(media) not in ("icon-source.png", "avatar-400.png"):
                zf.write(media, FR + "/Media/" + os.path.basename(media))
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    assert names[0] == FR + "/" + TOC, names[0]
    assert FR + "/Media/Icon.tga" in names, "icone manquante dans le zip"
    print("%s : %d fichiers" % (os.path.relpath(path, ROOT), len(names)))


if __name__ == "__main__":
    main()
