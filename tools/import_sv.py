#!/usr/bin/env python3
"""Recupere les noms de quetes francais deja memorises par d'autres addons.

Certains addons mettent en cache les titres de quetes lus dans le client, par identifiant
(ex. Darnassus47 : D47DB.observed[id].title). On les réutilise comme source de traduction
hors ligne, en complement du dump Guidelime_FR_Dump.

Usage : python3 tools/import_sv.py <dossier SavedVariables>
Sortie : glossaire/trad/32-sv.json (section "quetes")
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GL = os.path.join(ROOT, "glossaire")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage : python3 tools/import_sv.py <dossier WTF/Account/<COMPTE>/SavedVariables>")
    base = sys.argv[1]
    if not os.path.isdir(base):
        raise SystemExit("dossier introuvable : %s" % base)
    quest_ids = json.load(open(os.path.join(GL, "quest_ids.json"), encoding="utf-8"))
    by_id = {}
    items = {}
    for f in sorted(glob.glob(os.path.join(base, "*.lua"))):
        if f.endswith(".bak"):
            continue
        src = open(f, encoding="utf-8", errors="replace").read()
        for ident, title in re.findall(
                r'\[(\d+)\] = \{[^{}]*?\["title"\] = "((?:[^"\\]|\\.)*)"', src, re.S):
            by_id.setdefault(int(ident), title)
        # tables plates du type ["localizedTitles"]["frFR"][id] = "titre"
        i = src.find('["localizedTitles"]')
        if i >= 0:
            for ident, title in re.findall(r'\[(\d+)\] = "((?:[^"\\]|\\.)*)"', src[i:]):
                by_id.setdefault(int(ident), title)
        # liens d'objets mis en cache par les addons de sacs : |Hitem:<id>:...|h[Nom localise]|h
        for ident, name in re.findall(r"\|Hitem:(\d+):[^|]*\|h\[([^]]+)\]\|h", src):
            items.setdefault(int(ident), name)
    quetes = {}
    for title_en, qid in quest_ids.items():
        fr = by_id.get(qid)
        if fr:
            quetes[title_en] = fr

    # noms d'objets : identifiant -> nom localise (cache des addons de sacs) joint au nom anglais
    noms = {}
    en_ids_path = os.path.join(GL, "en_ids.json")
    if os.path.exists(en_ids_path):
        for key, en in json.load(open(en_ids_path, encoding="utf-8")).items():
            if not key.startswith("item:"):
                continue
            fr = items.get(int(key.split(":")[1]))
            if fr and en not in noms:
                noms[en] = fr

    path = os.path.join(GL, "trad", "32-sv.json")
    json.dump({"quetes": quetes, "noms": noms}, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)
    print("recupere dans les SavedVariables : %d titres de quetes, %d noms d'objets -> %s"
          % (len(quetes), len(noms), path))


if __name__ == "__main__":
    main()
