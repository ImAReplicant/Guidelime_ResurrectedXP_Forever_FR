#!/usr/bin/env python3
"""Complete les noms restants avec la base Wowhead Forever (locale frFR).

Wowhead n'expose pas d'API publique : on utilise les deux endpoints JSON que sert son site.
  https://www.wowhead.com/forever/search/suggestions-template?q=<nom>  -> id + type (JSON)
  https://nether.wowhead.com/forever/tooltip/<type>/<id>?locale=frFR   -> nom localise
Le nom anglais du tooltip sert de verification (search renvoie aussi des homonymes).

Usage : python3 tools/wowhead_names.py [--limit N] [--delay S] [--check [--limit N]]
Sortie : glossaire/trad/29-wowhead.json (section "noms"), fusionne par build_fr.py.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_fr import Translator, pluralize_fr  # noqa: E402

GL = os.path.join(ROOT, "glossaire")
OUT = os.path.join(GL, "trad", "29-wowhead.json")
SEARCH = "https://www.wowhead.com/forever/search/suggestions-template?q=%s"
TOOLTIP = "https://nether.wowhead.com/forever/tooltip/%s/%s?locale=%s"
AGENT = "Mozilla/5.0 (X11; Linux x86_64)"
KINDS = {"NPC": "npc", "Item": "item", "Quest": "quest", "Spell": "spell", "Object": "object"}
DELAY = 0.3
PAUSE = 90
RANK = re.compile(r"^(.*) \(Rank (\d+)\)$")


class Blocked(Exception):
    """Wowhead a renvoye 403 : on s'arrete et on reprend plus tard (les noms resolus sont gardes)."""


def fetch(url, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENT})
            return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                raise Blocked(url)
            if i + 1 == tries:
                return None
            time.sleep(1.5)
        except (urllib.error.URLError, OSError):
            if i + 1 == tries:
                return None
            time.sleep(1.5)
    return None


def suggest(name):
    """Candidats (type tooltip, id, nom anglais) renvoyes par la recherche Wowhead."""
    body = fetch(SEARCH % urllib.parse.quote(name))
    time.sleep(DELAY)
    if not body:
        return []
    try:
        results = (json.loads(body) or {}).get("results", [])
    except ValueError:
        return []
    return [(KINDS[r["typeName"]], str(r["id"]), r.get("name", ""))
            for r in results if r.get("typeName") in KINDS]


def tooltip(kind, ident, locale):
    body = fetch(TOOLTIP % (kind, ident, locale))
    time.sleep(DELAY)
    if not body:
        return None
    try:
        name = (json.loads(body) or {}).get("name") or None
    except ValueError:
        return None
    # Wowhead entoure de crochets les objets interactifs ([Brazier of Embersight]) : un crochet
    # dans la traduction casserait les balises du guide
    return name.strip("[]").strip() if name else None


def same_name(found, wanted):
    """Vrai si le nom anglais renvoye correspond (pluriel tolere)."""
    a, b = found.strip().lower(), wanted.strip().lower()
    return a == b or a == b.rstrip("s") or b == a.rstrip("s")


def variants(name):
    """Formes interrogeables d'un nom anglais pluriel (`-s` puis `-es`), 3 au plus."""
    out = [name]
    words = name.split(" ")
    for i, w in enumerate(words):
        for cut in ("s", "es"):
            if w.lower().endswith(cut) and len(w) > len(cut) + 1:
                out.append(" ".join(words[:i] + [w[:-len(cut)]] + words[i + 1:]))
    return out[:3]


def resolve(name, known, keys, en_ids):
    """Nom FR d'un nom anglais, ou None. `known` = identifiant deja apparie (name_ids.json)."""
    # "Fireball (Rank 2)" : Wowhead ne connait que le sort de base, le client ajoute le rang
    m = RANK.match(name)
    if m:
        fr = resolve(m.group(1), None, keys, en_ids)
        return None if fr is None else "%s (rang %s)" % (fr, m.group(2))
    if known:
        kind, ident = known.split(":")
        tkind = {"creature": "npc", "item": "item"}.get(kind)
        # le nom anglais de la base Guidelime (en_ids.json) suffit a verifier, sans requete
        if tkind and same_name(en_ids.get(known, ""), name):
            fr = tooltip(tkind, ident, "frFR")
            if fr:
                return fr
    for cand in variants(name):
        hits = [c for c in suggest(cand) if same_name(c[2], cand)]
        for kind, ident, _ in hits[:3]:
            fr = tooltip(kind, ident, "frFR")
            if fr:
                return pluralize_fr(fr) if cand != name else fr
    return None


def suspect(name, fr, keys):
    """Entree client douteuse : un objectif de quete n'est pas un nom propre."""
    if not keys.get(name.lower(), "").startswith("questobj:"):
        return False
    return abs(len(fr.split()) - len(name.split())) > 2 or any(c in fr for c in "0123456789:/|;")


def check(keys, en_ids, limit):
    """Divergences entre les noms Wowhead FR et le dump client (30-client.json)."""
    client = json.load(open(os.path.join(GL, "trad", "30-client.json"), encoding="utf-8"))["noms"]
    bad = [(n, fr) for n, fr in sorted(client.items()) if suspect(n, fr, keys)]
    print("entrees client suspectes (sans reseau) :", len(bad))
    for n, fr in bad:
        print("   %-32r %r" % (n, fr))
    names = sorted(client)[:limit]
    print("\ncomparaison Wowhead / client sur %d noms :" % len(names))
    same = diff = miss = 0
    for n in names:
        try:
            fr = resolve(n, keys.get(n.lower()), keys, en_ids)
        except Blocked:
            print("  403 de Wowhead : comparaison interrompue")
            break
        if not fr:
            miss += 1
        elif fr == client[n]:
            same += 1
        else:
            diff += 1
            print("   DIFF %-32r client=%r wowhead=%r" % (n, client[n], fr))
    print("identiques : %d | differents : %d | non resolus : %d" % (same, diff, miss))


def main():
    global DELAY
    args = sys.argv[1:]
    if "--delay" in args:
        DELAY = float(args[args.index("--delay") + 1])
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 0
    keys = json.load(open(os.path.join(GL, "name_ids.json"), encoding="utf-8"))
    en_ids = json.load(open(os.path.join(GL, "en_ids.json"), encoding="utf-8"))
    if "--check" in args:
        check(keys, en_ids, limit or 100)
        return
    t = Translator()
    done = {}
    if os.path.exists(OUT):
        done = json.load(open(OUT, encoding="utf-8")).get("noms", {})
        # une traduction contenant un crochet casserait les balises du guide
        done = {k: v for k, v in done.items() if "[" not in v and "]" not in v}
    todo = [n for n in sorted(t.cles["noms"]) if t.resolve_name(n) is None and n not in done]
    if limit:
        todo = todo[:limit]
    print("noms a interroger :", len(todo), "| deja resolus par Wowhead :", len(done))
    found = 0
    for i, name in enumerate(todo, 1):
        for attempt in range(4):
            try:
                fr = resolve(name, keys.get(name.lower()), keys, en_ids)
                break
            except Blocked:
                print("  403 de Wowhead : pause de %d s" % PAUSE)
                time.sleep(PAUSE)
        else:
            print("  403 persistant apres %d noms : arret, relancer plus tard" % i)
            break
        if fr:
            done[name] = fr
            found += 1
        if i % 25 == 0 or i == len(todo):
            print("  %d/%d | resolus %d | echecs %d" % (i, len(todo), found, i - found))
            json.dump({"noms": done}, open(OUT, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=0, sort_keys=True)
    json.dump({"noms": done}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print("noms resolus via Wowhead :", len(done), "->", OUT)


if __name__ == "__main__":
    main()
