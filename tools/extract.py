#!/usr/bin/env python3
"""Extrait les unites traduisibles des guides EN + les noms FR des bases de Guidelime.

Sorties (dossier glossaire/) :
  cles.json        -> unites a traduire (clauses, noms, titres de quetes, titres de guides)
  auto_noms.json   -> noms EN -> FR issus des bases frFR de Guidelime
  auto_quetes.json -> titres de quetes EN -> FR issus de questsDB_frFR
"""
import collections
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GL = os.path.join(ROOT, "glossaire")
EN = os.path.join(ROOT, "upstream", "Guidelime_ResurrectedXP_Forever_Alliance")
GUIDELIME = os.environ.get("GUIDELIME_DIR", "/tmp/gl/Guidelime")
DIRS = ["Speedrun", "Dungeon Route", "Riverglades"]

TAG = re.compile(r"\[([^\]]*)\]")
NAME = re.compile(r"\*([^*]+)\*")
SEP = "\\" * 2  # separateur d'instructions dans les fichiers de guide
SKIP_PREFIX = ("N ", "NX ", "D ", "GA ", "LI ")
QUEST_TAG = re.compile(r"^(Q[AATCS])([0-9/?]+)(?:,([0-9]*))?\s*(.*)$")
XP_TAG = re.compile(r"^XP\s*(\d+)([+\-.]?)(\d*)\s*(.*)$")


def iter_lines(dirs=DIRS):
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(EN, d, "*.lua"))):
            for line in open(path, encoding="utf-8"):
                yield path, line.rstrip("\n")


def is_guide_header(line):
    return line.startswith("Guidelime.registerGuide(") or line.startswith("]==]")


def split_segments(line):
    """Retourne [('TAG'|'TEXT', contenu), ...] en conservant l'ordre."""
    out, pos = [], 0
    for m in TAG.finditer(line):
        if m.start() > pos:
            out.append(("TEXT", line[pos:m.start()]))
        out.append(("TAG", m.group(1)))
        pos = m.end()
    if pos < len(line):
        out.append(("TEXT", line[pos:]))
    return out


def clause_template(clause):
    return NAME.sub("{N}", re.sub(r"\s+", " ", clause.strip()))


def split_ws(raw):
    """Separe les espaces de bord du coeur de la clause (preserves a la reconstruction)."""
    core = raw.strip()
    if not core:
        return "", "", ""
    lead = raw[:len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()):]
    return lead, core, trail


def parse_guide_title(text):
    """[N 1-6 Shadowglen] -> ('1-6 ', 'Shadowglen')"""
    m = re.match(r"\s*(\d*\.?\d*)\s*-?\s*(\d*\.?\d*)\s*(.*)$", text)
    if not m:
        return "", text.strip()
    minl, maxl, title = m.group(1), m.group(2), m.group(3).strip()
    if not minl and not maxl:
        return "", title
    return (minl + "-" + maxl + " "), title


def load_db_names():
    """nom anglais et type de chaque identifiant des bases Guidelime."""
    internal = os.path.join(GUIDELIME, "Data", "Internal")
    db_name, db_kind = {}, {}
    for tbl, table, kind in (("ItemsDB.lua", "itemsDB", "item"), ("ObjectsDB.lua", "objectsDB", "item"),
                             ("CreaturesDB.lua", "creaturesDB", "creature")):
        for ident, name in read_lua_named(os.path.join(internal, tbl), table).items():
            db_name.setdefault("%s:%s" % (kind, ident), name.lower())
            db_kind.setdefault(name.lower(), kind)
    return db_name, db_kind


def extract():
    db_name, db_kind = load_db_names()
    clauses = collections.Counter()
    names = collections.Counter()
    quests = collections.Counter()
    guides = collections.Counter()
    quest_ids = {}
    # nom en prose -> identifiant present sur la meme ligne (pour resoudre via les bases frFR)
    pairs = collections.defaultdict(collections.Counter)
    qpairs = collections.defaultdict(collections.Counter)
    for path, line in iter_lines():
        if is_guide_header(line):
            continue
        line_names = []
        ids_in_order = []
        first_block = None
        qids_in_order = []
        qfirst_block = None
        for kind, content in split_segments(line):
            if kind == "TAG":
                m = re.match(r"^(TAR|CI|UI)(\d+)", content)
                if m:
                    key = ("creature" if m.group(1) == "TAR" else "item") + ":" + m.group(2)
                    if first_block is None:
                        first_block = list(line_names)
                    if key not in ids_in_order:
                        ids_in_order.append(key)
                    continue
                # objectif de quete : [QC<id>,<n> ...] -> questobj:<id>#<n> (resolution de repli)
                m = re.match(r"^QC(\d+),(\d+)", content)
                if m:
                    key = "questobj:%s#%s" % (m.group(1), m.group(2))
                    if qfirst_block is None:
                        qfirst_block = list(line_names)
                    if key not in qids_in_order:
                        qids_in_order.append(key)
                continue
            line_names.extend(NAME.findall(content))
        if first_block and ids_in_order:
            def coherent(n, key):
                """Un nom connu comme PNJ ne peut pas porter un id d'objet (et inversement)."""
                kind = db_kind.get(n.lower())
                return kind is None or key.startswith(kind + ":")

            def vote(n, key, weight):
                if not coherent(n, key):
                    return
                # l'id porte deja un autre nom anglais dans les bases : la paire est fausse
                # (Bonebiter n'est pas le PNJ 8671 = Auctioneer Buckler). Un id absent des
                # bases (contenu Forever) reste accepte, et un nom de PNJ abrege dans le guide
                # (« Khardan » pour « Khardan Proudblade ») reste valide.
                known = db_name.get(key)
                if known:
                    k, x = known.lower(), n.lower()
                    if not (k == x or k.rstrip("s") == x.rstrip("s") or k.startswith(x + " ")):
                        return
                pairs[n.lower()][key] += weight

            # un id de PNJ isole est celui de l'etape (Talk to *X*[TAR…]) : seul le premier nom
            # cite le porte, sinon l'objet ou le sort achete/appris chez lui en herite
            # (Buy *Agile Boots* from her[TAR954-], Train *Corruption*[TAR459-])
            single_creature = len(ids_in_order) == 1 and ids_in_order[0].startswith("creature:")

            # 1. identite : le nom anglais de l'id est le nom cite (le plus fiable). Un nom
            # abrege dans le guide (« Khardan » pour « Khardan Proudblade ») compte aussi.
            rest_names = list(first_block)
            rest_ids = list(ids_in_order)
            for n in list(rest_names):
                for key in list(rest_ids):
                    known = db_name.get(key) or ""
                    if known == n.lower() or known.startswith(n.lower() + " "):
                        pairs[n.lower()][key] += 3
                        rest_names.remove(n)
                        rest_ids.remove(key)
                        break
            # 2. positionnel sur les restes
            if single_creature:
                vote(first_block[0], ids_in_order[0], 3)
                rest_names, rest_ids = [], []
            if rest_names and rest_ids:
                if len(rest_names) == len(rest_ids):
                    for n, key in zip(rest_names, rest_ids):
                        vote(n, key, 3)
                elif len(rest_names) > len(rest_ids):
                    # liste d'objets fouilles : elle termine le bloc de texte avant les balises
                    for n, key in zip(rest_names[-len(rest_ids):], rest_ids):
                        vote(n, key, 2)
                elif len(rest_ids) == 1:
                    for n in rest_names:
                        vote(n, rest_ids[0], 1)
            # 3. filet : positionnel d'origine a poids faible, aucune paire perdue
            if not single_creature and len(first_block) == len(ids_in_order):
                for n, key in zip(first_block, ids_in_order):
                    vote(n, key, 1)
            elif len(first_block) > len(ids_in_order):
                for n, key in zip(first_block[-len(ids_in_order):], ids_in_order):
                    vote(n, key, 1)
            elif len(ids_in_order) == 1:
                for n in first_block:
                    vote(n, ids_in_order[0], 1)
        if qfirst_block and qids_in_order and len(qfirst_block) == len(qids_in_order):
            for n, key in zip(qfirst_block, qids_in_order):
                qpairs[n.lower()][key] += 1
        for kind, content in split_segments(line):
            if kind == "TAG":
                head = content[:3]
                if head.startswith(SKIP_PREFIX):
                    if head.startswith(("N ", "NX ", "LI ")):
                        _, title = parse_guide_title(content[head.index(" ") + 1:])
                        if title:
                            guides[title] += 1
                    continue
                m = QUEST_TAG.match(content)
                if m and m.group(4) and m.group(4) != "-":
                    title = m.group(4).strip()
                    quests[title] += 1
                    ids = [int(x) for x in m.group(2).split("/") if x.isdigit()]
                    if ids:
                        quest_ids.setdefault(title, ids[0])
                    continue
                m = XP_TAG.match(content)
                if m and m.group(4).strip():
                    clauses[clause_template(m.group(4))] += 1
                continue
            for raw in content.split(SEP):
                lead, core, trail = split_ws(raw)
                if not core:
                    continue
                for n in NAME.findall(core):
                    names[n] += 1
                clauses[clause_template(core)] += 1
    return clauses, names, quests, guides, pairs, qpairs, quest_ids


def table_bounds(s, key):
    """Bornes de la table DB.<key> (jusqu'a la fermeture de la table)."""
    i = s.find("DB.%s = {" % key)
    if i < 0:
        return None
    end = s.find("\n\t}\nend\n", i)
    if end < 0:
        end = s.find("\nend\n", i)
    return i, (end if end > 0 else len(s))


def read_lua_table(path, key):
    s = open(path, encoding="utf-8").read()
    b = table_bounds(s, key)
    if b is None:
        return {}
    seg = s[b[0]:b[1]]
    out = {}
    for m in re.finditer(r"\[(\d+)\] = \"((?:[^\"\\]|\\.)*)\"", seg):
        out[int(m.group(1))] = m.group(2)
    return out


def read_lua_named(path, key):
    """Lit une table lua [id] = { ["name"] = "..." ... } en tolerant l'ordre des champs."""
    s = open(path, encoding="utf-8").read()
    b = table_bounds(s, key)
    if b is None:
        return {}
    seg = s[b[0]:b[1]]
    starts = [(m.start(), int(m.group(1))) for m in re.finditer(r"\n\t\[(\d+)\] = \{", seg)]
    out = {}
    for k, (pos, qid) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(seg)
        m = re.search(r"\[\"name\"\] = \"((?:[^\"\\]|\\.)*)\"", seg[pos:end])
        if m:
            out[qid] = m.group(1)
    return out


def main():
    os.makedirs(GL, exist_ok=True)
    internal = os.path.join(GUIDELIME, "Data", "Internal")
    if not os.path.exists(os.path.join(internal, "CreaturesDB.lua")):
        raise SystemExit("ERREUR : Guidelime introuvable (GUIDELIME_DIR ou %s).\n"
                         "         Definir GUIDELIME_DIR=/chemin/vers/Guidelime" % GUIDELIME)
    clauses, names, quests, guides, pairs, qpairs, quest_ids = extract()
    json.dump({"clauses": dict(clauses), "noms": dict(names), "quetes": dict(quests),
               "guides": dict(guides)},
              open(os.path.join(GL, "cles.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)

    internal = os.path.join(GUIDELIME, "Data", "Internal")
    en_cr = read_lua_named(os.path.join(internal, "CreaturesDB.lua"), "creaturesDB")
    en_it = read_lua_named(os.path.join(internal, "ItemsDB.lua"), "itemsDB")
    en_ob = read_lua_named(os.path.join(internal, "ObjectsDB.lua"), "objectsDB")
    fr_cr = read_lua_table(os.path.join(internal, "CreaturesDB_Locales.lua"), "creaturesDB_frFR")
    fr_it = read_lua_table(os.path.join(internal, "ItemsDB_Locales.lua"), "itemsDB_frFR")
    fr_ob = read_lua_table(os.path.join(internal, "ObjectsDB_Locales.lua"), "objectsDB_frFR")

    auto_names = {}
    for en, fr in ((en_cr, fr_cr), (en_it, fr_it), (en_ob, fr_ob)):
        for qid, name in en.items():
            if qid in fr:
                auto_names.setdefault(name.lower(), fr[qid])
    json.dump(auto_names, open(os.path.join(GL, "auto_noms.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)

    en_quests = read_lua_named(os.path.join(internal, "QuestsDB.lua"), "questsDB")
    fr_quests = {}
    s = open(os.path.join(internal, "QuestsDB_Locales.lua"), encoding="utf-8").read()
    b = table_bounds(s, "questsDB_frFR")
    if b is not None:
        for m in re.finditer(r"\[(\d+)\] = \{\s*\[\"name\"\] = \"((?:[^\"\\]|\\.)*)\"", s[b[0]:b[1]]):
            fr_quests[int(m.group(1))] = m.group(2)
    auto_quests = {}
    for qid, name in en_quests.items():
        if qid in fr_quests:
            auto_quests.setdefault(name, fr_quests[qid])
    json.dump(auto_quests, open(os.path.join(GL, "auto_quetes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)

    # noms de la prose resolus via l'identifiant present sur la meme ligne du guide
    by_id = {"creature": fr_cr, "item": {}, "quest": fr_quests}
    by_id["item"].update(fr_it)
    by_id["item"].update(fr_ob)
    auto_ids = {}
    ambiguous = 0
    name_ids = {}
    for name, ids in pairs.items():
        ranked = ids.most_common()
        if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
            ambiguous += 1
            continue
        key = ranked[0][0]
        name_ids[name] = key
        kind, ident = key.split(":")
        fr = by_id[kind].get(int(ident))
        if fr:
            auto_ids[name] = fr
    # repli : objectifs de quete, uniquement pour les noms sans identifiant objet/PNJ
    for name, ids in qpairs.items():
        if name in name_ids:
            continue
        ranked = ids.most_common()
        if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
            continue
        name_ids[name] = ranked[0][0]
    json.dump(name_ids, open(os.path.join(GL, "name_ids.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)
    json.dump(quest_ids, open(os.path.join(GL, "quest_ids.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)

    # identifiants references par les guides -> nom anglais (base Guidelime) :
    # permet de relier le dump client (id -> nom FR) au nom anglais utilise dans la prose
    ref = collections.defaultdict(set)
    for d in DIRS:
        for path in glob.glob(os.path.join(EN, d, "*.lua")):
            for line in open(path, encoding="utf-8"):
                for kind, ident in re.findall(r"\[(TAR|CI|UI)(\d+)", line):
                    ref[("creature" if kind == "TAR" else "item")].add(int(ident))
                for ids in re.findall(r"\[Q[ATCS]([0-9/]+)", line):
                    for x in ids.split("/"):
                        if x.isdigit():
                            ref["quest"].add(int(x))
    en_ids = {}
    for kind, table in (("creature", en_cr), ("item", en_it), ("item", en_ob), ("quest", en_quests)):
        for ident in ref.get(kind, ()):
            name = table.get(ident)
            if name:
                en_ids["%s:%d" % (kind, ident)] = name
    json.dump(en_ids, open(os.path.join(GL, "en_ids.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)
    print("ids references avec nom anglais :", len(en_ids))
    json.dump(auto_ids, open(os.path.join(GL, "auto_noms_ids.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0, sort_keys=True)
    print("noms resolus par identifiant :", len(auto_ids), "| ambigus ignores :", ambiguous)

    print("clauses distinctes :", len(clauses), "| occurrences :", sum(clauses.values()))
    print("noms distincts     :", len(names), "| occurrences :", sum(names.values()))
    print("titres de quetes   :", len(quests), "| titres de guides :", len(guides))
    print("auto noms EN->FR   :", len(auto_names), "| auto quetes EN->FR :", len(auto_quests))


if __name__ == "__main__":
    main()
