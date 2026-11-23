#!/usr/bin/env python3
"""Verifie l'integrite de l'addon FR genere (tools/build_fr.py).

Controles :
 1. meme nombre de lignes que la source
 2. meme sequence de balises ; identifiants, objectifs, coordonnees et noms de zones inchanges
 3. nombre de separateurs \\\\ et de marqueurs * identiques
 4. aucun placeholder {N} residuel, aucun nom de balise inconnu
 5. balises [N]/[NX]/[LI] coherentes entre elles (chaque NX/LI pointe vers un guide existant)
 6. structure Lua des fichiers (une seule chaine longue par fichier)
 7. reste d'anglais sur une liste de tournures frequentes
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from addon import OUT, TOC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "upstream", "Guidelime_ResurrectedXP_Forever_Alliance")
DIRS = ["Speedrun", "Dungeon Route", "Riverglades"]
EN_DIRS = ["Speedrun", "Dungeon Route", "Dungeon Quests", "Mage AoE", "Riverglades"]
SEP = "\\" * 2
TAG = re.compile(r"\[([^\]]*)\]")
QUEST_TAG = re.compile(r"^(Q[AATCS])([0-9/?]+)((?:,[0-9]*)?)")
GUIDE_TAG = re.compile(r"^(NX|LI|N)\s*(\d*\.?\d*)\s*-?\s*(\d*\.?\d*)\s*(.*)$")
XP_TAG = re.compile(r"^(XP)\s*(\d+)([+\-.]?)(\d*)\s*(.*)$")
ENGLISH = ["Talk to ", "Turn in", "Accept ", "Loot them", "Vendor trash", "Kill ", "Train ",
           "Fly to", "Hearth to", "Buy ", "Grind ", "Equip the", "Click the", "Skip this",
           "Only if you", "Travel to", "Take the", "Cast ", "Use the", "Go to the", "Collect "]
STOP_EN = re.compile(r"(?<![A-Za-z])(the|you|your|this|that|any|if|it|not|of|and|with|from|into|"
                     r"his|her|they|when|which|have|has|does|was|were)(?![A-Za-z])")

errors = []
warnings = []


def norm_tag(content):
    """Cle de comparaison d'une balise : ignore les titres traduisibles."""
    if content.startswith("D "):
        return "DETAILS"
    m = XP_TAG.match(content)
    if m:
        return "XP:%s%s%s" % (m.group(2), m.group(3), m.group(4))
    m = QUEST_TAG.match(content)
    if m:
        return "QUEST:" + m.group(1) + m.group(2) + m.group(3)
    m = GUIDE_TAG.match(content)
    if m and m.group(1) in ("N", "NX", "LI"):
        return "%s:%s-%s" % (m.group(1), m.group(2), m.group(3))
    return content


def check_file(src_path, out_path):
    src = open(src_path, encoding="utf-8").read().split("\n")
    out = open(out_path, encoding="utf-8").read().split("\n")
    rel = os.path.relpath(out_path, OUT)
    if len(src) != len(out):
        errors.append("%s : %d lignes au lieu de %d" % (rel, len(out), len(src)))
        return []
    if not out[0].startswith("Guidelime.registerGuide([==["):
        errors.append("%s : entete Lua manquant" % rel)
    last = [ln for ln in out if ln.strip()][-1]
    if not re.match(r'^\]==\], "[^"]*"\)(\.title = "[^"]*")?$', last):
        errors.append("%s : ligne finale Lua invalide %r" % (rel, last[:80]))
    body = "\n".join(out[1:])
    if body.count("]==]") != 1:
        errors.append("%s : delimiteur de fin ]==] en nombre inattendu" % rel)
    guides = []
    for i, (a, b) in enumerate(zip(src, out), 1):
        if i == 1:
            continue
        ta, tb = TAG.findall(a), TAG.findall(b)
        na, nb = [norm_tag(t) for t in ta], [norm_tag(t) for t in tb]
        if na != nb:
            errors.append("%s:%d : balises differentes\n  EN %s\n  FR %s" % (rel, i, na, nb))
            continue
        for t in tb:
            m = GUIDE_TAG.match(t)
            if m and m.group(1) == "N":
                guides.append((m.group(2), m.group(3), m.group(4).strip()))
        if a.count(SEP) != b.count(SEP):
            errors.append("%s:%d : nombre de separateurs \\\\ different" % (rel, i))
        if a.count("*") != b.count("*"):
            errors.append("%s:%d : marqueurs * differents (%d vs %d)" % (rel, i, a.count("*"), b.count("*")))
        if "{N}" in b:
            errors.append("%s:%d : placeholder {N} non substitue" % (rel, i))
    return guides


def load_guidelime():
    """Codes de balises et noms de zones connus de Guidelime (pour prouver l'absence d'erreur de parsing)."""
    base = os.environ.get("GUIDELIME_DIR", "/tmp/gl/Guidelime")
    codes, zones = set(), set()
    gp = os.path.join(base, "GuideParser.lua")
    if os.path.exists(gp):
        src = open(gp, encoding="utf-8").read()
        block = src[src.find("GP.codes = {"):]
        block = block[:block.find("\n}")]
        codes = set(re.findall(r'= "([A-Z]+)"', block))
    md = os.path.join(base, "Data", "MapDB.lua")
    if os.path.exists(md):
        src = open(md, encoding="utf-8").read()
        zones = set(re.findall(r'^\s*(?:\[\d+\]\s*=\s*)?"([^"]+)",', src, re.M))
    return codes, zones


def zone_ok(name, zones):
    def norm(s):
        s = s.lower().replace(" ", "").replace("'", "")
        return s[3:] if s.startswith("the") else s
    n = norm(name)
    return any(norm(z) == n for z in zones)


def check_toc(root, toc_name, dirs):
    """Chaque fichier .lua d'un dossier de guides doit etre declare dans le .toc, et inversement."""
    toc = os.path.join(root, toc_name)
    if not os.path.exists(toc):
        errors.append("%s : .toc introuvable" % toc_name)
        return
    listed = {l.strip().replace("\\", "/") for l in open(toc, encoding="utf-8")
              if l.strip() and not l.strip().startswith("##")}
    on_disk = {os.path.join(d, os.path.basename(p)).replace("\\", "/") for d in dirs
               for p in glob.glob(os.path.join(root, d, "*.lua"))}
    for entry in sorted(listed - on_disk):
        errors.append("%s : %s declare mais absent du disque" % (toc_name, entry))
    for entry in sorted(on_disk - listed):
        errors.append("%s : %s absent du .toc (ne sera jamais charge)" % (toc_name, entry))


def main():
    groups = {}
    group_files = {}
    for d in DIRS:
        for path in sorted(glob.glob(os.path.join(SRC, d, "*.lua"))):
            out_path = os.path.join(OUT, d, os.path.basename(path))
            if not os.path.exists(out_path):
                errors.append("%s : fichier FR manquant" % out_path)
                continue
            g = check_file(path, out_path)
            txt = open(out_path, encoding="utf-8").read()
            m = re.search(r'^\]==\], "([^"]*)"', txt, re.M)
            group = m.group(1) if m else "?"
            groups.setdefault(group, set()).update(g)
            group_files.setdefault(group, []).append(out_path)

    check_toc(SRC, "Guidelime_ResurrectedXP_Forever_Alliance.toc", EN_DIRS)
    check_toc(OUT, TOC, DIRS)

    # coherence des liens de guides
    for group, names in groups.items():
        for path in group_files.get(group, []):
            txt = open(path, encoding="utf-8").read()
            for line in txt.split("\n")[1:]:
                for t in TAG.findall(line):
                    m = GUIDE_TAG.match(t)
                    if m and m.group(1) in ("NX", "LI"):
                        key = (m.group(2), m.group(3), m.group(4).strip())
                        if key not in names:
                            errors.append("%s : %s pointe vers un guide inexistant %s" % (
                                os.path.basename(path), m.group(1), key))

    # syntaxe Lua (si luac est disponible)
    luac = shutil.which("luac")
    lua_files = sorted(glob.glob(os.path.join(OUT, "*", "*.lua")))
    if luac:
        bad = [p for p in lua_files if subprocess.run([luac, "-p", p], capture_output=True).returncode]
        for p in bad:
            errors.append("%s : syntaxe Lua invalide (luac -p)" % os.path.relpath(p, OUT))
        print("syntaxe Lua (luac -p) :", "%d/%d fichiers valides" % (len(lua_files) - len(bad), len(lua_files)))
    else:
        print("syntaxe Lua : luac absent, controle ignore")

    # reste d'anglais
    english = 0
    for path in glob.glob(os.path.join(OUT, "*", "*.lua")):
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            text = TAG.sub("", line)
            text = re.sub(r"\*[^*]*\*", "", text)
            for w in ENGLISH:
                if w in text:
                    english += 1
                    warnings.append("%s:%d : tournure anglaise « %s »" % (
                        os.path.relpath(path, OUT), i, w.strip()))
                    break
            # phrase non traduite : deux mots outils anglais minuscules (les noms propres
            # et titres laisses en anglais sont capitalises, ils ne declenchent pas)
            words = {m.group(1) for m in STOP_EN.finditer(text)}
            if len(words) >= 2:
                english += 1
                warnings.append("%s:%d : mots anglais dans la prose (%s)" % (
                    os.path.relpath(path, OUT), i, ", ".join(sorted(words))))

    # codes de mise en forme WoW non evalues (|4singulier:pluriel;, |c...|r, |H...|h) : ils
    # s'affichent tels quels dans le guide, ils n'ont rien a y faire
    for path in glob.glob(os.path.join(OUT, "*", "*.lua")):
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if "|" in line:
                errors.append("%s:%d : code WoW non evalue (%s)" % (
                    os.path.relpath(path, OUT), i, line.strip()[:70]))

    # parsing Guidelime : codes de balises et noms de zones connus
    codes, zones = load_guidelime()
    if not codes:
        print("AVERTISSEMENT : Guidelime introuvable (GUIDELIME_DIR ou /tmp/gl/Guidelime).")
        print("                Controles de codes de balises et de zones ignores.")
    if codes:
        for path in glob.glob(os.path.join(OUT, "*", "*.lua")):
            for i, line in enumerate(open(path, encoding="utf-8"), 1):
                if i == 1:
                    continue
                for t in TAG.findall(line):
                    code = t[:3] if t[:3] in codes else t[:2] if t[:2] in codes else t[:1]
                    if code not in codes:
                        errors.append("%s:%d : code de balise inconnu de Guidelime [%s]" % (
                            os.path.relpath(path, OUT), i, t[:20]))
                        continue
                    if code in ("G", "L"):
                        m = re.match(r"^[GL]\s*[\d.]+\s*,\s*[\d.]+\s*,?\s*([\d.]*)\s*(.*)$", t)
                        if m and m.group(2) and zones and not zone_ok(m.group(2), zones):
                            errors.append("%s:%d : zone inconnue de Guidelime [%s]" % (
                                os.path.relpath(path, OUT), i, t[:40]))

    print("fichiers verifies :", len(glob.glob(os.path.join(OUT, "*", "*.lua"))))
    print("codes de balises Guidelime :", len(codes), "| zones connues :", len(zones))
    print("groupes de guides :", len(groups))
    print("lignes avec reste d'anglais :", english)
    if errors:
        print("\nERREURS (%d) :" % len(errors))
        for e in errors[:40]:
            print(" -", e)
    if warnings:
        print("\nAVERTISSEMENTS : %d (echantillon)" % len(warnings))
        for w in warnings[:10]:
            print(" -", w)
    print("\nRESULTAT :", "ECHEC" if errors else "OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
