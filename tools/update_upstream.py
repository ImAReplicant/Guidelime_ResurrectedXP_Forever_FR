#!/usr/bin/env python3
"""Met a jour les guides anglais d'origine (upstream/) depuis CurseForge.

Modes :
    --check           compare la version locale a la derniere publiee (0 = a jour, 2 = a jour dispo)
    --apply           telecharge la derniere version et remplace upstream/<addon>/
    --from-zip ZIP    meme chose depuis une archive locale (ni reseau ni cle)
    --selftest        verifie le parsing d'une reponse factice, sans reseau

Aucune cle n'est necessaire : les metadonnees viennent de cfwidget (service tiers qui expose
l'API CurseForge) et l'archive du CDN mediafilez. La variable CF_API_KEY reste optionnelle :
elle sert de repli sur edge.forgecdn.net, qui exige un x-api-key depuis juillet 2026.
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
CFWIDGET = "https://api.cfwidget.com/wow/addons/%s"
CDN_MEDIA = "https://mediafilez.forgecdn.net/files/%d/%d/%s"
CDN_EDGE = "https://edge.forgecdn.net/files/%d/%d/%s"
AGENT = "GuidelimeFR-upstream/1.0"


def fetch_bytes(url, key=None):
    headers = {"User-Agent": AGENT}
    if key:
        headers["x-api-key"] = key
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def fetch_json(url):
    try:
        return json.loads(fetch_bytes(url).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit("cfwidget injoignable (%s) : %s\n"
                         "         reessayer plus tard, ou telecharger l'archive a la main puis"
                         " --from-zip" % (exc.code, url))
    except (urllib.error.URLError, ValueError) as exc:
        raise SystemExit("cfwidget injoignable (%s) : %s" % (exc, url))


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


def latest_release(payload):
    """Dernier fichier de type release, le plus recent par uploaded_at."""
    rel = [f for f in payload.get("files", []) if f.get("type") == "release"]
    if not rel:
        raise SystemExit("aucun fichier release pour %s" % SLUG)
    return max(rel, key=lambda f: f.get("uploaded_at", ""))


def file_version(f):
    """Version de l'addon : 'Guidelime … 1.8.0.zip' -> 1.8.0. Le champ `version` de cfwidget
    est la version du jeu (1.60.1), pas celle de l'addon."""
    for field in ("display", "name"):
        m = re.search(r"(\d+\.\d+(?:\.\d+)*)", f.get(field) or "")
        if m:
            return m.group(1)
    return ""


def cdn_urls(f):
    """URL mediafilez (sans cle) puis edge (repli, x-api-key requis depuis juillet 2026)."""
    ident, name = f["id"], f["name"]
    return (CDN_MEDIA % (ident // 1000, ident % 1000, name),
            CDN_EDGE % (ident // 1000, ident % 1000, name))


def download(f, key=None):
    media, edge = cdn_urls(f)
    try:
        return fetch_bytes(media)
    except urllib.error.HTTPError as exc:
        if not key or exc.code not in (401, 403, 404):
            raise SystemExit("telechargement refuse (%s) : %s" % (exc.code, media))
    except urllib.error.URLError as exc:
        raise SystemExit("CDN injoignable (%s) : %s" % (exc, media))
    try:
        return fetch_bytes(edge, key)
    except urllib.error.HTTPError as exc:
        raise SystemExit("telechargement refuse (%s) : %s (repli edge, x-api-key fourni)"
                         % (exc.code, edge))
    except urllib.error.URLError as exc:
        raise SystemExit("CDN injoignable (%s) : %s (repli edge)" % (exc, edge))


def install_zip(path):
    """Remplace upstream/<addon>/ par le contenu du zip (le seul dossier qui bouge)."""
    if not os.path.exists(path):
        raise SystemExit("archive introuvable : %s" % path)
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise SystemExit("ce n'est pas une archive zip : %s" % path)
    with zf:
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
    payload = {"id": 1802706, "files": [
        {"id": 9742557, "name": "Guidelime_ResurrectedXP_Forever_Alliance-1.8.0.zip",
         "display": "Guidelime_ResurrectedXP_Forever_Alliance 1.8.0.zip", "type": "release",
         "version": "1.60.1", "uploaded_at": "2026-11-22T00:00:47.207Z"},
        {"id": 9717407, "name": "Guidelime_ResurrectedXP_Forever_Alliance.zip",
         "display": "Guidelime_ResurrectedXP_Forever_Alliance.zip", "type": "release",
         "version": "1.60.1", "uploaded_at": "2026-11-20T15:19:48.210Z"},
        {"id": 9999999, "name": "beta-1.9.0.zip", "display": "1.9.0-beta", "type": "beta",
         "version": "1.60.1", "uploaded_at": "2026-11-23T00:00:00Z"},
    ]}
    latest = latest_release(payload)
    assert latest["id"] == 9742557, "un beta plus recent ne doit pas etre retenu"
    assert file_version(latest) == "1.8.0"
    assert file_version({"display": "Guidelime_ResurrectedXP_Forever_Alliance.zip",
                         "name": "Guidelime_ResurrectedXP_Forever_Alliance-1.7.5.zip"}) == "1.7.5"
    media, edge = cdn_urls(latest)
    assert media == ("https://mediafilez.forgecdn.net/files/9742/557/"
                     "Guidelime_ResurrectedXP_Forever_Alliance-1.8.0.zip"), media
    assert edge == ("https://edge.forgecdn.net/files/9742/557/"
                    "Guidelime_ResurrectedXP_Forever_Alliance-1.8.0.zip"), edge
    assert parse_version("1.8.0") > parse_version("1.7.6")
    assert parse_version("1.7.7-fr.2") == (1, 7, 7)

    with tempfile.NamedTemporaryFile("w", suffix=".toc", delete=False, encoding="utf-8") as tmp:
        tmp.write("## Interface: 16001\n## Version: 1.8.0\n")
    try:
        assert local_version(tmp.name) == "1.8.0"
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
    latest = latest_release(fetch_json(CFWIDGET % SLUG))
    remote, local = file_version(latest), local_version()
    if parse_version(remote) <= parse_version(local):
        print("a jour : %s (derniere publiee : %s)" % (local, remote))
        return 0
    print("mise a jour disponible : %s -> %s (%s)" % (local, remote, latest["name"]))
    if "--apply" not in args:
        return 2
    tmp = tempfile.mkdtemp(prefix="cf-")
    path = os.path.join(tmp, latest["name"])
    open(path, "wb").write(download(latest, key))
    install_zip(path)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
