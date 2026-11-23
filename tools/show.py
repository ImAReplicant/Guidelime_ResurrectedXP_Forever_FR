#!/usr/bin/env python3
"""Affiche des tranches des unites a traduire (aide a la traduction)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GL = os.path.join(ROOT, "glossaire")


def load(name):
    return json.load(open(os.path.join(GL, name), encoding="utf-8"))


def done(section):
    """Cles deja traduites dans glossaire/trad/*.json"""
    out = set()
    d = os.path.join(GL, "trad")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                out |= set(json.load(open(os.path.join(d, f), encoding="utf-8")).get(section, {}))
    return out


def ordered(counter):
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))


def main():
    what = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end = int(sys.argv[3]) if len(sys.argv) > 3 else start + 250
    d = load("cles.json")
    if what == "clauses":
        items = ordered(d["clauses"])
    elif what == "noms":
        auto = load("auto_noms.json")

        def variants(n):
            v = [n]
            if n.endswith("es"):
                v.append(n[:-2])
            if n.endswith("s"):
                v.append(n[:-1])
            return v

        items = ordered({k: v for k, v in d["noms"].items()
                         if not any(x.lower() in auto for x in variants(k))})
    elif what == "quetes":
        auto = load("auto_quetes.json")
        items = ordered({k: v for k, v in d["quetes"].items() if k not in auto})
    elif what == "guides":
        items = ordered(d["guides"])
    else:
        raise SystemExit("clauses|noms|quetes|guides")
    if len(sys.argv) > 4 and sys.argv[4] == "--reste":
        out = done(what)
        items = [(k, v) for k, v in items if k not in out]
    print("total", len(items), "| tranche", start, end)
    for i, (k, v) in enumerate(items[start:end], start):
        print("%d\t%d\t%s" % (i, v, k))


if __name__ == "__main__":
    main()
