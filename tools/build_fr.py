#!/usr/bin/env python3
"""Genere l'addon FR a partir des guides EN + du glossaire.

Usage : python3 tools/build_fr.py
Sortie : Guidelime_ResurrectedXP_Forever_Alliance_FR/ + RAPPORT-traduction.md
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from addon import ADDON, OUT, TOC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GL = os.path.join(ROOT, "glossaire")
DUMP = "30-client.json"
WOWHEAD = "29-wowhead.json"
EN = os.path.join(ROOT, "upstream", "Guidelime_ResurrectedXP_Forever_Alliance")
DIRS = ["Speedrun", "Dungeon Route", "Riverglades"]
SEP = "\\" * 2
TAG = re.compile(r"\[([^\]]*)\]")
NAME = re.compile(r"\*([^*]+)\*")
QUEST_TAG = re.compile(r"^(Q[AATCS])([0-9/?]+)((?:,[0-9]*)?)(\s*)(.*)$")
XP_TAG = re.compile(r"^(XP)\s*(\d+)([+\-.]?)(\d*)\s*(.*)$")
GUIDE_TAG = re.compile(r"^(NX|LI|N)(\s*)(.*)$")
FR_SUFFIX = "-fr.1"  # suffixe de la version FR, a bumper avec le guide
# projets : CurseForge https://www.curseforge.com/wow/addons/guidelime-resurrectedxp-forever-alliance-fr
#            Wago      https://addons.wago.io/addons/guidelime-resurrectedxp-forever-alliance-fr
WEBSITE = "https://github.com/ImAReplicant/Guidelime_ResurrectedXP_Forever_FR"
CURSE_ID = "1829310"
WAGO_ID = "mKOalZNx"
FOOTER = re.compile(r'^\]==\], "([^"]*)"\)(\.title = "([^"]*)")?$')
HEADER = "Guidelime.registerGuide([==["
FR_STOP = {"de", "du", "des", "d'", "la", "le", "les", "l'", "en", "et", "à", "au", "aux", "the"}
RANK = re.compile(r"^(.*) \(Rank (\d+)\)$")
ABANDON = re.compile(r"^Abandon (.+)$")
GROUPS = {
    "RestedXP Forever Dungeon Route (A)": "RestedXP Forever Donjons (A)",
}

# Le guide utilise l'infinitif ("Parler à", "Tuer") : on ramene les rares formes
# en imperatif-vouvoiement a l'infinitif pour garder un registre unique.
VOUS_TO_INF = {
    "achetez": "acheter", "abandonnez": "abandonner", "acceptez": "accepter", "allez": "aller",
    "apprenez": "apprendre", "assurez-vous": "s'assurer", "attendez": "attendre", "cherchez": "chercher",
    "cliquez": "cliquer", "cochez": "cocher", "continuez": "continuer", "courez": "courir",
    "déposez": "déposer", "descendez": "descendre", "déplacez-vous": "se déplacer", "détruisez": "détruire",
    "éloignez-vous": "s'éloigner", "entrez": "entrer", "équipez": "équiper", "escortez": "escorter",
    "essayez": "essayer", "évitez": "éviter", "faites": "faire", "farmez": "farmer", "fouillez": "fouiller",
    "gardez": "garder", "guettez": "guetter", "ignorez": "ignorer", "jetez": "jeter", "lancez": "lancer",
    "mettez": "mettre", "montez": "monter", "mourez": "mourir", "nagez": "nager", "notez": "noter",
    "accumulez": "accumuler", "appuyez": "appuyer", "choisissez": "choisir", "comptez": "compter",
    "déséquipez": "déséquiper", "kitez": "kiter", "priorisez": "prioriser", "regardez": "regarder",
    "reprenez": "reprendre", "sélectionnez": "sélectionner", "validez": "valider",
    "approchez": "approcher", "apportez": "apporter", "arrêtez": "arrêter", "attaquez": "attaquer",
    "canalisez": "canaliser", "ciblez": "cibler", "commencez": "commencer", "contournez": "contourner",
    "créez": "créer", "défendez": "défendre", "donnez": "donner", "envoyez": "envoyer",
    "escaladez": "escalader", "finissez": "finir", "glissez": "glisser", "maniez": "manier",
    "mangez": "manger", "minez": "miner", "obtenez": "obtenir", "partez": "partir",
    "plongez": "plonger", "posez": "poser", "rapportez": "rapporter", "remontez": "remonter",
    "renvoyez": "renvoyer", "rééquipez": "rééquiper", "ressortez": "ressortir", "tapez": "taper",
    "trouvez": "trouver", "vainquez": "vaincre", "surveillez": "surveiller",
    "oubliez": "oublier", "ouvrez": "ouvrir", "ouvrez-vous": "s'ouvrir", "parlez": "parler",
    "passez": "passer", "pensez": "penser", "placez": "placer", "prenez": "prendre",
    "préparez-vous": "se préparer", "ramassez": "ramasser", "récoltez": "récolter", "rendez": "rendre",
    "rendez-vous": "se rendre", "réparez": "réparer", "restez": "rester", "retirez": "retirer",
    "retournez": "retourner", "rejoignez": "rejoindre", "sautez": "sauter", "sortez": "sortir",
    "suivez": "suivre", "supprimez": "supprimer", "terminez": "terminer", "traversez": "traverser",
    "tuez": "tuer", "utilisez": "utiliser", "vendez": "vendre", "vérifiez": "vérifier",
}


def _inf(word):
    inf = VOUS_TO_INF.get(word.lower())
    if inf is None:
        return None
    return inf[0].upper() + inf[1:] if word[:1].isupper() else inf


def normalize_register(text):
    # le guide utilise l'infinitif partout : chaque verbe vouvoye d'un segment est ramene
    parts = re.split(r"(\. |; |! |\? |: | et | puis )", text)
    for i in range(0, len(parts), 2):
        parts[i] = _normalize_segment(parts[i])
    return "".join(parts)


def _normalize_segment(text):
    prefix = ""
    body = text
    if body.startswith("("):
        prefix, body = "(", body[1:]
    m = re.match(r"^(?:Ne|N')\s*(?:vous\s+)?(\S+?)(?:\s+pas\b|')", body)
    if m:
        inf = _inf(m.group(1))
        if inf:
            rest = body[m.end():].strip()
            return prefix + "Ne pas " + inf + (" " + rest if rest else "")
    m = re.match(r"^(\S+?)(?=[\s,.)]|$)", body)
    if m:
        inf = _inf(m.group(1))
        if inf:
            return prefix + inf + body[m.end():]
    return text
PATTERNS = [
    # conditions monetaires et de niveau : traduction mecanique, sans nom propre
    (re.compile(r"^\(Only if you have at least (\d+)s (\d+)c\)$"),
     r"(uniquement si vous avez au moins \1 pièces d'argent et \2 de cuivre)"),
    (re.compile(r"^\(Only if you have at least (\d+)s\)$"),
     r"(uniquement si vous avez au moins \1 pièces d'argent)"),
    (re.compile(r"^\(Only if you have at least (\d+)c\)$"),
     r"(uniquement si vous avez au moins \1 pièces de cuivre)"),
    (re.compile(r"^\(Only if you have less than (\d+)s (\d+)c\)$"),
     r"(uniquement si vous avez moins de \1 pièces d'argent et \2 de cuivre)"),
    (re.compile(r"^\(Only if you have less than (\d+)s\)$"),
     r"(uniquement si vous avez moins de \1 pièces d'argent)"),
    (re.compile(r"^\(From level ([\d.]+)\)$"), r"(à partir du niveau \1)"),
    (re.compile(r"^\(Skip if you are already level (\d+) or higher\)$"),
     r"(ignorez si vous êtes déjà niveau \1 ou plus)"),
    (re.compile(r"^\(Skip if you are above level (\d+)\)$"),
     r"(ignorez si vous êtes au-dessus du niveau \1)"),
    (re.compile(r"^\(Skip if you are above level (\d+): tick it off\)$"),
     r"(ignorez si vous êtes au-dessus du niveau \1 : cochez l'étape)"),
    (re.compile(r"^\(choose reward (\d+)\)$"), r"(choisir la récompense \1)"),
    (re.compile(r"^\(Tick this off if you do not learn (.+)\)$"),
     r"(cochez si vous n'apprenez pas \1)"),
    (re.compile(r"^\(Skip this if you already know (.+?) \(Rank (\d+)\): tick it off\)$"),
     r"(ignorez si vous connaissez déjà \1 (rang \2) : cochez l'étape)"),
    (re.compile(r"^\(Skip this if you already know (.+?) \(Rank (\d+)\)\)$"),
     r"(ignorez si vous connaissez déjà \1 (rang \2))"),
    (re.compile(r"^\(Skip this if you already know this rank of (.+?)\)$"),
     r"(ignorez si vous connaissez déjà ce rang de \1)"),
    (re.compile(r"^\(Skip this if you already know (.+?): tick it off\)$"),
     r"(ignorez si vous connaissez déjà \1 : cochez l'étape)"),
    (re.compile(r"^\(Skip this if you already know (.+?)\)$"),
     r"(ignorez si vous connaissez déjà \1)"),
    (re.compile(r"^Abandon (.+)$"), r"Abandonner \1"),
    # textes des balises [XP ...]
    (re.compile(r"^Grind to level (\d+)$"), r"Farmer jusqu'au niveau \1"),
    (re.compile(r"^Grind to (\d+)$"), r"Farmer jusqu'au niveau \1"),
    (re.compile(r"^Grind until you are level (\d+)$"), r"Farmer jusqu'au niveau \1"),
    (re.compile(r"^Grind until you are (\d+) ?xp (?:away from|off) level (\d+)( \(.*\))?$"),
     r"Farmer jusqu'à être à \1 xp du niveau \2\3"),
    (re.compile(r"^Grind until you are (\d+)xp into level (\d+)$"),
     r"Farmer jusqu'à \1 xp dans le niveau \2"),
    (re.compile(r"^Grind until you are (\d+)/(\d+) xp into level (\d+)$"),
     r"Farmer jusqu'à \1/\2 xp dans le niveau \3"),
    (re.compile(r"^Grind until (\d+)/(\d+) xp into level (\d+)$"),
     r"Farmer jusqu'à \1/\2 xp dans le niveau \3"),
    (re.compile(r"^Grind until you are (\d+) XP away from (\d+)$"),
     r"Farmer jusqu'à être à \1 xp du niveau \2"),
    (re.compile(r"^Grind to (\d+)\+/(\d+)xp$"), r"Farmer jusqu'à \1+/\2 xp"),
    (re.compile(r"^Grind en route to (\d+)\+/(\d+)xp$"), r"Farmer en chemin jusqu'à \1+/\2 xp"),
]


def load(name):
    return json.load(open(os.path.join(GL, name), encoding="utf-8"))


def merge_trad():
    merged = {"clauses": {}, "noms": {}, "quetes": {}, "guides": {}, "details": {}}
    auto = load("auto_noms.json")
    d = os.path.join(GL, "trad")
    shadowed = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".json"):
            continue
        data = json.load(open(os.path.join(d, f), encoding="utf-8"))
        for key in merged:
            items = data.get(key, {})
            if key == "noms" and f in (DUMP, WOWHEAD):
                # sources appariees par identifiant : les bases Guidelime font foi
                items = {k: v for k, v in items.items() if k.lower() not in auto}
            for k, v in items.items():
                if k in merged[key] and merged[key][k] != v:
                    shadowed.append((key, k, f))
                merged[key][k] = v
    for key, k, f in shadowed:
        print("glossaire : %s de %s ecrase une entree precedente : %r" % (key, f, k))
    return merged


def pluralize_fr(name):
    out = []
    prev = None
    for w in name.split(" "):
        low = w.lower()
        if low in FR_STOP or "'" in w or (prev is not None and prev.lower() in ("de", "du", "des", "d'")) \
                or low.endswith(("s", "x")):
            out.append(w)
        elif "-" in w:
            head, rest = w.split("-", 1)
            out.append(head + ("-" if head.lower().endswith(("s", "x")) else "s-") + rest)
        elif low.endswith(("eau", "au")):
            out.append(w + "x")
        else:
            out.append(w + "s")
        prev = w
    return " ".join(out)


def singular_candidates(name):
    """Formes singulieres plausibles d'un nom anglais pluriel (tete ou queue de groupe)."""
    words = name.split(" ")
    out = []
    for i, w in enumerate(words):
        for cut in ("es", "s"):
            if w.lower().endswith(cut) and len(w) > len(cut) + 1:
                out.append(" ".join(words[:i] + [w[:-len(cut)]] + words[i + 1:]))
                break
    return out


class Translator:
    def __init__(self):
        cles = load("cles.json")
        trad = merge_trad()
        self.clauses = trad["clauses"]
        self.auto_noms = load("auto_noms.json")
        self.noms = trad["noms"]
        self.noms_lower = {k.lower(): v for k, v in self.noms.items()}
        self.auto_quetes = load("auto_quetes.json")
        ids_path = os.path.join(GL, "auto_noms_ids.json")
        self.auto_ids = json.load(open(ids_path, encoding="utf-8")) if os.path.exists(ids_path) else {}
        self.quetes = trad["quetes"]
        self.guides = trad["guides"]
        self.details = trad.get("details", {})
        self.cles = cles
        self.missing = {"clauses": {}, "noms": {}, "quetes": {}, "guides": {}}
        self.prose_quetes = {}  # titres de quetes cites dans la prose (Abandonner …)
        # titres de quetes laisses en anglais dans une clause traduite (glossaire manuel) :
        # bases Guidelime + dictionnaires importes du client (meme ordre que resolve_quest)
        self.quest_all = dict(self.auto_quetes)
        self.quest_all.update(self.quetes)
        titles = [t for t in self.quest_all if len(t) > 3]
        self.quest_rx = re.compile(r"(?<![\w*])(%s)(?![\w*])" % "|".join(
            re.escape(t) for t in sorted(titles, key=len, reverse=True))) if titles else None
        self.bad = []

    def resolve_name(self, n):
        fr = self._resolve_name(n)
        # "Fireball (Rank 2)" absent des bases : on resout le sort de base, le client ajoute le rang
        m = RANK.match(n)
        if fr is None and m:
            base = self._resolve_name(m.group(1))
            if base is not None:
                return "%s (rang %s)" % (base, m.group(2))
        return fr

    def _resolve_name(self, n):
        if n in self.noms:
            return self.noms[n]
        low = n.lower()
        if low in self.auto_noms:
            return self.auto_noms[low]
        # pluriel : les bases Guidelime sont plus fiables que l'appariement heuristique
        for cand in singular_candidates(n):
            fr = self.auto_noms.get(cand.lower())
            if fr is not None:
                return pluralize_fr(fr)
        if low in self.noms_lower:
            return self.noms_lower[low]
        if low in self.auto_ids:
            return self.auto_ids[low]
        for cand in singular_candidates(n):
            fr = self.noms_lower.get(cand.lower()) or self.auto_ids.get(cand.lower())
            if fr is not None:
                return pluralize_fr(fr)
        # noms de quetes cites dans le texte libre (memes bases frFR)
        fr = self.auto_quetes.get(n) or self.quetes.get(n)
        if fr is not None:
            return fr
        return None

    def name(self, n):
        fr = self.resolve_name(n)
        if fr is None:
            self.missing["noms"][n] = self.cles["noms"].get(n, 1)
            return n
        return fr

    def resolve_quest(self, title):
        if title in self.quetes:
            return self.quetes[title]
        return self.auto_quetes.get(title)

    def quest(self, title):
        fr = self.resolve_quest(title)
        if fr is None:
            self.missing["quetes"][title] = self.cles["quetes"].get(title, 1)
            return title
        return fr

    def guide(self, title):
        if title in self.guides:
            return self.guides[title]
        self.missing["guides"][title] = self.cles["guides"].get(title, 1)
        return title

    def clause(self, core):
        tpl = NAME.sub("{N}", re.sub(r"\s+", " ", core))
        fr = self.clauses.get(tpl)
        if fr is None:
            key = tpl.rstrip(".").strip()
            fr = self.clauses.get(key)
            if fr is not None and tpl.endswith("."):
                fr = fr + "."
        # "Abandon <titre de quete>" : le titre est une quete, on le resout dans la base
        # (le glossaire le recopiait tel quel, le joueur lisait un titre absent de son journal)
        m = ABANDON.match(tpl)
        if m and "{N}" not in tpl and (fr is None or fr == "Abandonner " + m.group(1)):
            self.prose_quetes[m.group(1)] = self.prose_quetes.get(m.group(1), 0) + 1
            fr = "Abandonner " + self.quest(m.group(1))
        if fr is None:
            for rx, rep in PATTERNS:
                m = rx.match(tpl)
                if m:
                    fr = m.expand(rep)
                    break
        if fr is None:
            self.missing["clauses"][tpl] = self.cles["clauses"].get(tpl, 1)
            return core
        # un titre de quete reste en anglais dans une clause traduite -> version FR de la base
        if self.quest_rx is not None:
            def to_fr(m):
                self.prose_quetes[m.group(1)] = self.prose_quetes.get(m.group(1), 0) + 1
                return self.quest_all.get(m.group(1), m.group(1))
            fr = self.quest_rx.sub(to_fr, fr)
        names = NAME.findall(core)
        if fr.count("{N}") != len(names):
            self.bad.append(tpl)
            return core
        it = iter(names)
        possessive = re.compile(r"\b(?:leurs?|vos|votre|les|des|ces|ses|son|sa|du|de la|la|le|l')$", re.I)

        def repl(m):
            value = self.name(next(it))
            # "leurs *Les masques en cuir rouge*" -> "leurs *masques en cuir rouge*"
            if possessive.search(fr[:m.start()].rstrip()):
                value = re.sub(r"^(?:Les|Le|La|L')\s*", "", value)
            return "*" + value + "*"

        out = normalize_register(re.sub(r"\{N\}", repl, fr))
        # accord du possessif : « son *Tête* » -> « sa *Tête* » (les noms FR sont un ensemble clos,
        # la liste ci-dessous suffit ; tout le reste reste au masculin comme avant)
        return re.sub(r"\bson \*([^*]+)\*", _possessive, out)

    def text(self, s):
        parts = []
        for raw in s.split(SEP):
            if not raw.strip():
                parts.append(raw)
                continue
            core = raw.strip()
            lead = raw[:len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            parts.append(lead + self.clause(core) + trail)
        return SEP.join(parts)

    def tag(self, content):
        m = QUEST_TAG.match(content)
        if m and m.group(5) and m.group(5) != "-":
            return m.group(1) + m.group(2) + m.group(3) + m.group(4) + self.quest(m.group(5).strip())
        if content.startswith("D ") and len(content) > 2:
            return "D " + self.details.get(content[2:].strip(), content[2:].strip())
        m = XP_TAG.match(content)
        if m and m.group(5).strip():
            return "XP" + m.group(2) + m.group(3) + m.group(4) + " " + self.clause(m.group(5))
        m = GUIDE_TAG.match(content)
        if m:
            code, sp, rest = m.group(1), m.group(2), m.group(3)
            tm = re.match(r"\s*(\d*\.?\d*)\s*-?\s*(\d*\.?\d*)\s*(.*)$", rest)
            if tm and (tm.group(1) or tm.group(2)):
                prefix = tm.group(1) + "-" + tm.group(2) + " "
                title = tm.group(3).strip()
                return code + sp + prefix + self.guide(title)
        return content

    def line(self, line):
        out, pos = [], 0
        for m in TAG.finditer(line):
            if m.start() > pos:
                out.append(self.text(line[pos:m.start()]))
            out.append("[" + self.tag(m.group(1)) + "]")
            pos = m.end()
        if pos < len(line):
            out.append(self.text(line[pos:]))
        return "".join(out)


def toc_field(name):
    """Champ du toc de l'addon EN (source unique, evite toute derive)."""
    toc = os.path.join(EN, "Guidelime_ResurrectedXP_Forever_Alliance.toc")
    for line in open(toc, encoding="utf-8"):
        if line.startswith("## %s:" % name):
            return line.split(":", 1)[1].strip()
    raise SystemExit("## %s introuvable dans %s" % (name, toc))


FEMININE = {"tête", "patte", "serre", "griffe", "amulette", "clé", "peau", "main", "dent", "épaule"}


def _possessive(m):
    """« son *Tête* » -> « sa *Tête* » : le possessif s'accorde avec le nom mis en avant."""
    head = m.group(1).split(" ")[0].strip("*«»\"'").lower()
    return "sa *%s*" % m.group(1) if head in FEMININE else m.group(0)


def strip_wow_codes(text):
    """Retire les codes de mise en forme WoW d'un texte : couleur, lien, texture et gabarit de
    pluriel non evalue (|4personnage tué:personnages tués;), qui s'afficherait tel quel en jeu."""
    if "|" not in text:
        return text
    text = re.sub(r"\|c[0-9a-fA-F]{8}", "", text)
    text = re.sub(r"\|H([^|]*)\|h([^|]*)\|h", r"\2", text)
    text = re.sub(r"\|T[^|]*\|t", "", text)
    text = re.sub(r"\|A[^|]*\|a", "", text)
    text = text.replace("|n", " ").replace("|r", "").replace("|h", "")
    # |<chiffre>singulier:pluriel; -> singulier
    text = re.sub(r"\|[0-9]([^:;|]*)(?::[^;|]*)?;", r"\1", text)
    return text.replace("|", "")


def selftest():
    """Auto-controle des heuristiques : python3 tools/build_fr.py --selftest"""
    t = Translator()
    assert pluralize_fr("Peau de vieux kodo") == "Peaux de vieux kodos"
    assert pluralize_fr("Bottes") == "Bottes"
    assert "Kobold" in singular_candidates("Kobolds")
    assert "Sack of Oats" in singular_candidates("Sacks of Oats")
    assert normalize_register("Parlez à X et attendez une minute") == "Parler à X et attendre une minute"
    assert normalize_register("Ignorez cette étape") == "Ignorer cette étape"
    # un objet achete chez un PNJ ne doit pas heriter du nom du PNJ
    assert t.resolve_name("Agile Boots") != "Kat"
    assert t.resolve_name("Corruption") != "Drusilla La Salle"
    # le rang d'un sort ne bloque pas la resolution du nom de base
    fr = t.resolve_name("Fireball (Rank 2)")
    assert fr is None or fr.endswith("(rang 2)")
    # aucun code de mise en forme WoW ne doit atteindre le guide
    assert strip_wow_codes("|4personnage tué:personnages tués;") == "personnage tué"
    assert strip_wow_codes("|cffff0000rouge|r") == "rouge"
    assert "|" not in strip_wow_codes("|Hitem:1|h[x]|h")
    assert strip_wow_codes("Tuer les ours") == "Tuer les ours"
    # accord du possessif : « son *Tête* » -> « sa *Tête* », le masculin reste inchange
    class _M:
        def __init__(self, word):
            self.word = word

        def group(self, i):
            return self.word if i == 1 else "son *%s*" % self.word
    assert _possessive(_M("Tête")) == "sa *Tête*"
    assert _possessive(_M("Collier")) == "son *Collier*"
    print("selftest : OK")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    t = Translator()
    files_written = []
    for d in DIRS:
        outdir = os.path.join(OUT, d)
        os.makedirs(outdir, exist_ok=True)
        written = set()
        for path in sorted(glob.glob(os.path.join(EN, d, "*.lua"))):
            lines = open(path, encoding="utf-8").read().split("\n")
            res = []
            for line in lines:
                if line.startswith(HEADER):
                    res.append(line)
                    continue
                fm = FOOTER.match(line)
                if fm:
                    group = GROUPS.get(fm.group(1), fm.group(1)) + " FR"
                    tail = (').title = "%s"' % t.guide(fm.group(3))) if fm.group(2) else ""
                    res.append(']==], "%s")%s' % (group, tail[1:]))
                    continue
                res.append(t.line(line))
            name = os.path.basename(path)
            # apostrophe typographique des bases frFR -> apostrophe ASCII, comme le reste du guide ;
            # pas d'espace de bord dans un nom (« *Nom * » s'affichait avec un blanc parasite)
            text = re.sub(r"\*\s*([^*]*?)\s*\*", r"*\1*", "\n".join(res).replace("\u2019", "'"))
            open(os.path.join(outdir, name), "w", encoding="utf-8").write(strip_wow_codes(text))
            written.add(name)
            files_written.append(d + "\\" + name)
        for stale in glob.glob(os.path.join(outdir, "*.lua")):
            if os.path.basename(stale) not in written:
                os.remove(stale)

    toc = [
        "## Interface: " + toc_field("Interface"),
        "## Title: Guidelime |cff2a9df4ResurrectedXP Forever FR|r (Alliance)",
        "## Author: RestedXP (route), converted for Guidelime, traduction FR non officielle",
        "## Version: " + toc_field("Version") + FR_SUFFIX,
        "## RequiredDeps: Guidelime, Questie",
        "## Notes: Traduction francaise du guide RestedXP Forever (Alliance) pour Guidelime.",
        "## IconTexture: Interface\\AddOns\\" + ADDON + "\\Media\\Icon.tga",
        "## X-Website: " + WEBSITE,
        "## X-Curse-Project-ID: " + CURSE_ID,
        "## X-Wago-ID: " + WAGO_ID,
        "",
    ] + files_written
    open(os.path.join(OUT, TOC), "w",
         encoding="utf-8").write("\n".join(toc) + "\n")

    total_occ = sum(t.cles["clauses"].values())
    miss_occ = sum(t.missing["clauses"].values())
    name_occ = sum(t.cles["noms"].values())
    miss_names = {n: c for n, c in t.cles["noms"].items() if t.resolve_name(n) is None}
    miss_name = sum(miss_names.values())
    quest_occ = sum(t.cles["quetes"].values())
    miss_quests = {q: c for q, c in t.cles["quetes"].items() if t.resolve_quest(q) is None}
    miss_quest = sum(miss_quests.values())
    prose_occ = sum(t.prose_quetes.values())
    miss_prose = {q: c for q, c in t.prose_quetes.items() if t.resolve_quest(q) is None}
    miss_prose_occ = sum(miss_prose.values())

    rep = ["# Rapport de traduction FR", "",
           "Genere par `tools/build_fr.py`. Voir `README-FR.md` pour la politique de traduction.", "",
           "Les elements restants sont volontairement laisses en anglais : contenu ajoute par WoW Forever",
           "ou textes absents des bases frFR de Guidelime. Pour les traduire, ajouter une entree dans",
           "`glossaire/trad/*.json` puis relancer `tools/build_fr.py`.", "",
           "| Element | Distincts | Traduits | Reste | Occurrences restantes |",
           "|---|---|---|---|---|",
           "| Clauses | %d | %d | %d | %d / %d (%.1f%%) |" % (
               len(t.cles["clauses"]), len(t.cles["clauses"]) - len(t.missing["clauses"]),
               len(t.missing["clauses"]), miss_occ, total_occ, 100.0 * miss_occ / total_occ),
           "| Noms | %d | %d | %d | %d / %d (%.1f%%) |" % (
               len(t.cles["noms"]), len(t.cles["noms"]) - len(miss_names),
               len(miss_names), miss_name, name_occ, 100.0 * miss_name / name_occ),
           "| Titres de quetes | %d | %d | %d | %d / %d (%.1f%%) |" % (
               len(t.cles["quetes"]), len(t.cles["quetes"]) - len(miss_quests),
               len(miss_quests), miss_quest, quest_occ, 100.0 * miss_quest / quest_occ),
           "| Titres de quetes cites dans la prose | %d | %d | %d | %d / %d (%.1f%%) |" % (
               len(t.prose_quetes), len(t.prose_quetes) - len(miss_prose),
               len(miss_prose), miss_prose_occ, prose_occ,
               100.0 * miss_prose_occ / prose_occ if prose_occ else 0.0),
           ""]
    t.missing["noms"] = miss_names
    t.missing["quetes"] = dict(miss_quests, **miss_prose)
    for key, label in (("guides", "Titres de guides"), ("clauses", "Clauses restees en anglais"),
                       ("noms", "Noms restes en anglais"), ("quetes", "Titres de quetes restes en anglais")):
        items = sorted(t.missing[key].items(), key=lambda kv: (-kv[1], kv[0]))
        rep.append("## %s (%d)" % (label, len(items)))
        rep.append("")
        for k, v in items:
            rep.append("- `%s` (%d)" % (k, v))
        rep.append("")
    open(os.path.join(ROOT, "RAPPORT-traduction.md"), "w", encoding="utf-8").write("\n".join(rep))

    print("fichiers ecrits :", len(files_written))
    print("clauses : %d/%d distinctes traduites, reste %.1f%% des occurrences" % (
        len(t.clauses), len(t.cles["clauses"]), 100.0 * miss_occ / total_occ))
    print("noms restants : %d distincts (%.1f%% des occurrences)" % (
        len(t.missing["noms"]), 100.0 * miss_name / name_occ))
    print("quetes restantes : %d distinctes (%.1f%% des occurrences)" % (
        len(t.missing["quetes"]), 100.0 * miss_quest / quest_occ))
    print("guides non traduits :", len(t.missing["guides"]))
    if t.bad:
        print("traductions au nombre de {N} incorrect (ignorees) :", len(t.bad))
        for b in t.bad[:20]:
            print("   ", b)
        # une clause non traduite pour cette raison doit faire echouer le build
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
