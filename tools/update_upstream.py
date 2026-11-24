#!/usr/bin/env python3
"""Met a jour les guides anglais d'origine (upstream/) depuis CurseForge.

Modes :
    --check           compare la version locale a la derniere publiee (0 = a jour, 2 = a jour dispo)
    --apply           telecharge la derniere version et remplace upstream/<addon>/
    --from-zip ZIP    meme chose depuis une archive locale (ni reseau ni cle)
    --selftest        verifie le parsing d'une reponse API factice, sans reseau

La cle API CurseForge est requise pour --check et --apply :
https://console.curseforge.com/ (compte gratuit), variable d'environnement CF_API_KEY.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_ADDON = "Guidelime_ResurrectedXP_Forever_Alliance"
UPSTREAM = os.path.join(ROOT, "upstream", EN_ADDON)
TOC = os.path.join(UPSTREAM, EN_ADDON + ".toc")
SLUG = "guidelime-resurrectedxp-alliance-forever"
GAME_ID = 1  # World of Warcraft
API = "https://api.curseforge.com/v1"
CDN = "https://mediafilez.forgecdn.net/files/%d/%d/%s"
AGENT = "GuidelimeFR-upstream/1.0"


def fetch_json(path, key):
    req = urllib.request.Request(API + path, headers={"x-api-key": key, "Accept": "application/json",
                                                      "User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def local_version(path=TOC):
    for line in open(path, encoding="utf-8"):
        if line.startswith("## Version:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("## Version introuvable dans %s" % path)


def parse_version(text):
    """'1.7.6' -> (1, 7, 6) ; tolere un suffixe ('1.7.7-fr.1' -> (1, 7, 7))."""
    m = re.match(r"(\d+(?:\.\d+)*)", text.strip())
    if not m:
        return ()
    return tuple(int(x) for x in m.group(1).split("."))


def pick_mod(data, slug):
    """Id du projet dont le slug correspond exactement (la recherche peut renvoyer des voisins)."""
    for mod in data.get("data", []):
        if mod.get("slug") == slug:
            return mod["id"]
    raise SystemExit("projet introuvable sur CurseForge : %s" % slug)


def project_id(key):
    return pick_mod(fetch_json("/mods/search?gameId=%d&slug=%s" % (GAME_ID, SLUG), key), SLUG)


def latest_release(files):
    """Dernier fichier de type release (releaseType 1), le plus recent par fileDate."""
    rel = [f for f in files.get("data", []) if f.get("releaseType") == 1]
    if not rel:
        raise SystemExit("aucun fichier release pour %s" % SLUG)
    return max(rel, key=lambda f: f.get("fileDate", ""))


def file_version(f):
    """'1.7.7' depuis displayName, sinon depuis le nom du fichier."""
    m = re.search(r"(\d+(?:\.\d+)+)", f.get("displayName") or "")
    if not m:
        m = re.search(r"(\d+(?:\.\d+)+)", f.get("fileName") or "")
    return m.group(1) if m else ""


def download_url(f):
    return f.get("downloadUrl") or CDN % (f["id"] // 1000, f["id"] % 1000, f["fileName"])


def install_zip(path):
    """Remplace upstream/<addon>/ par le contenu du zip (le seul dossier qui bouge)."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if not any(n == EN_ADDON + "/" + EN_ADDON + ".toc" for n in names):
            raise SystemExit("archive inattendue : %s/%s.toc absent de %s" % (EN_ADDON, EN_ADDON, path))
        tmp = tempfile.mkdtemp(prefix="upstream-")
        zf.extractall(tmp)
    src = os.path.join(tmp, EN_ADDON)
    shutil.rmtree(UPSTREAM, ignore_errors=True)
    shutil.move(src, UPSTREAM)
    shutil.rmtree(tmp, ignore_errors=True)
    print("upstream mis a jour : version %s" % local_version())


def selftest():
    files = {"data": [
        {"id": 4000001, "fileName": "a-1.7.5.zip", "displayName": "1.7.5",
         "fileDate": "2026-11-01T10:00:00Z", "releaseType": 1, "downloadUrl": None},
        {"id": 4000002, "fileName": "a-1.7.7.zip", "displayName": "1.7.7",
         "fileDate": "2026-11-20T10:00:00Z", "releaseType": 1, "downloadUrl": None},
        {"id": 4000003, "fileName": "beta.zip", "displayName": "1.8.0-beta",
         "fileDate": "2026-11-21T10:00:00Z", "releaseType": 3, "downloadUrl": "https://example/x.zip"},
    ]}
    latest = latest_release(files)
    assert latest["id"] == 4000002, "le fichier beta ne doit pas etre retenu"
    assert file_version(latest) == "1.7.7"
    assert download_url(latest) == "https://mediafilez.forgecdn.net/files/4000/2/a-1.7.7.zip"
    assert parse_version("1.7.7") > parse_version("1.7.6")
    assert parse_version("1.7.7-fr.2") == (1, 7, 7)
    assert file_version({"displayName": "", "fileName": "Guide-1.8.0.zip"}) == "1.8.0"

    # recherche par slug : le voisin homonyme ne doit pas etre retenu
    mods = {"data": [{"id": 7, "slug": "guidelime-resurrectedxp-horde-forever"},
                     {"id": 123456, "slug": SLUG}]}
    assert pick_mod(mods, SLUG) == 123456
    try:
        pick_mod({"data": [{"id": 7, "slug": "autre"}]}, SLUG)
    except SystemExit:
        pass
    else:
        raise AssertionError("un slug absent doit faire echouer la recherche")

    # lecture de la version dans un .toc, et comparaison avec ce que lit la chaine
    with tempfile.NamedTemporaryFile("w", suffix=".toc", delete=False, encoding="utf-8") as tmp:
        tmp.write("## Interface: 16001\n## Version: 1.7.7\n")
    try:
        assert local_version(tmp.name) == "1.7.7"
        assert parse_version(local_version(tmp.name)) > parse_version("1.7.6")
    finally:
        os.unlink(tmp.name)
    print("selftest : OK")


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
        return 0
    if "--from-zip" in args:
        install_zip(args[args.index("--from-zip") + 1])
        return 0
    key = os.environ.get("CF_API_KEY")
    if not key:
        print("ERREUR : cle API CurseForge requise (CF_API_KEY) pour --check/--apply.\n"
              "         Cle gratuite : https://console.curseforge.com/ — voir AGENTS.md.\n"
              "         Sans cle, utiliser --from-zip <archive telechargee a la main>.", file=sys.stderr)
        return 1
    mod = project_id(key)
    latest = latest_release(fetch_json("/mods/%d/files?pageSize=20" % mod, key))
    remote, local = file_version(latest), local_version()
    if parse_version(remote) <= parse_version(local):
        print("a jour : %s (derniere publiee : %s)" % (local, remote))
        return 0
    print("mise a jour disponible : %s -> %s (%s)" % (local, remote, latest["fileName"]))
    if "--apply" not in args:
        return 2
    tmp = tempfile.mkdtemp(prefix="cf-")
    path = os.path.join(tmp, latest["fileName"])
    open(path, "wb").write(fetch_bytes(download_url(latest)))
    install_zip(path)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
