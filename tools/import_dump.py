#!/usr/bin/env python3
"""Importe le dump de noms localises produit par l'addon Guidelime_FR_Dump.

Usage : python3 tools/import_dump.py <SavedVariables/Guidelime_FR_Dump.lua>
Sortie : glossaire/trad/30-client.json (fusionne comme les autres glossaires)
         sections "noms" (objets/PNJ) et "quetes" (titres de quetes)
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GL = os.path.join(ROOT, "glossaire")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage : python3 tools/import_dump.py <SavedVariables/Guidelime_FR_Dump.lua>")
    src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    dump = {"%s:%s" % (kind, ident): name for kind, ident, name in
            re.findall(r'\["(item|creature|quest):(\d+)"\] = "((?:[^"\\]|\\.)*)"', src)}
    for ident, name in re.findall(r'\["(questobj:\d+#\d+)"\] = "((?:[^"\\]|\\.)*)"', src):
        dump[ident] = name

    noms = {}
    name_ids = json.load(open(os.path.join(GL, "name_ids.json"), encoding="utf-8"))
    # les noms deja couverts par les bases Guidelime ne passent pas par l'appariement heuristique
    auto_noms = json.load(open(os.path.join(GL, "auto_noms.json"), encoding="utf-8"))
    auto_ids_path = os.path.join(GL, "auto_noms_ids.json")
    auto_ids = json.load(open(auto_ids_path, encoding="utf-8")) if os.path.exists(auto_ids_path) else {}
    en_ids_path = os.path.join(GL, "en_ids.json")
    en_ids = json.load(open(en_ids_path, encoding="utf-8")) if os.path.exists(en_ids_path) else {}
    dirty = re.compile(r"[0-9:/|;]")
    for name, key in name_ids.items():
        if name.lower() in auto_noms:
            continue
        # l'identifiant courant donne deja le nom FR par les bases Guidelime : le dump n'apporte
        # qu'une valeur d'un appariement plus ancien (« Khardan » -> « Bâton court »)
        if name in auto_ids:
            continue
        fr = dump.get(key)
        if not fr:
            continue
        # un objectif de quete ne doit fournir qu'un nom propre, pas "Tuer X: 20/20" ni
        # une phrase entiere ("Aider le Puant a recolter les Feuilles de Haricots des marais")
        if key.startswith("questobj:"):
            if dirty.search(fr) or abs(len(fr.split()) - len(name.split())) > 2:
                continue
        # l'identifiant porte un autre nom anglais dans les bases : la paire est fausse
        known = en_ids.get(key)
        if known and known.lower().rstrip("s") != name.lower().rstrip("s"):
            continue
        noms[name] = fr

    # tout identifiant dumpe dont on connait le nom anglais (base Guidelime) devient une paire EN->FR
    if en_ids:
        for key, en in en_ids.items():
            fr = dump.get(key)
            if fr and en not in noms:
                noms[en] = fr

    quetes = {}
    quest_ids = json.load(open(os.path.join(GL, "quest_ids.json"), encoding="utf-8"))
    for title, qid in quest_ids.items():
        fr = dump.get("quest:%d" % qid)
        if fr:
            quetes[title] = fr

    path = os.path.join(GL, "trad", "30-client.json")
    json.dump({"noms": noms, "quetes": quetes}, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)
    print("importes depuis le client : %d noms, %d titres de quetes -> %s" % (len(noms), len(quetes), path))


if __name__ == "__main__":
    main()
