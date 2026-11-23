#!/usr/bin/env python3
"""Empaquette l'addon FR dans dist/ avec le nom de dossier attendu par WoW.

Le dossier racine du zip doit s'appeler exactement comme le .toc : un zip GitHub nomme
"-main", ou un dossier renomme, n'est jamais charge par le client.

Usage : python3 tools/package.py
Sortie : dist/Guidelime_ResurrectedXP_Forever_Alliance_FR.zip
"""
import glob
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = "Guidelime_ResurrectedXP_Forever_Alliance_FR"
DIRS = ["Speedrun", "Dungeon Route", "Riverglades"]


def main():
    src = os.path.join(ROOT, FR)
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    path = os.path.join(dist, FR + ".zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(src, FR + ".toc"), FR + "/" + FR + ".toc")
        for d in DIRS:
            for guide in sorted(glob.glob(os.path.join(src, d, "*.lua"))):
                zf.write(guide, "%s/%s/%s" % (FR, d, os.path.basename(guide)))
        for media in sorted(glob.glob(os.path.join(src, "Media", "*"))):
            # icon-source.png est la source de tools/make_icon.sh, inutile dans le zip
            if os.path.basename(media) != "icon-source.png":
                zf.write(media, FR + "/Media/" + os.path.basename(media))
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    assert names[0] == FR + "/" + FR + ".toc", names[0]
    assert FR + "/Media/Icon.tga" in names, "icone manquante dans le zip"
    print("%s : %d fichiers" % (os.path.relpath(path, ROOT), len(names)))


if __name__ == "__main__":
    main()
