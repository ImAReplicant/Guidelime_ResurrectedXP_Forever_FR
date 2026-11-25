#!/usr/bin/env python3
"""Envoie l'archive de l'addon sur CurseForge et Wago Addons.

Usage :
    python3 tools/release.py --dry-run     # affiche ce qui serait envoye, sans reseau
    python3 tools/release.py               # envoie vraiment

Variables d'environnement (requises hors --dry-run) :
    CF_PROJECT_ID, CF_API_TOKEN       CurseForge (jeton : projet > API Tokens)
    WAGO_PROJECT_ID, WAGO_API_TOKEN   Wago Addons (jeton : developer dashboard)

L'archive doit exister (python3 tools/package.py). Le texte du changelog vient de CHANGELOG.md.
"""
import json
import os
import re
import sys
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from addon import ADDON, OUT, TOC as ADDON_TOC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(ROOT, "dist", ADDON + ".zip")
TOC = os.path.join(OUT, ADDON_TOC)
CURSE_URL = "https://wow.curseforge.com/api/projects/%s/upload-file"
WAGO_URL = "https://addons.wago.io/api/projects/%s/version"
CURSE_PUBLIC = "https://www.curseforge.com/api/v1/mods/%s/files"


def publication_status():
    """Etat de publication du fichier courant sur la page du projet (API publique, sans jeton).

    Un fichier depose sur un projet neuf reste invisible tant que la moderation ne l'a pas approuve.
    Code de sortie : 0 publie, 2 en attente de moderation, 1 erreur.
    """
    pid = os.environ.get("CF_PROJECT_ID", "1829310")
    want = version()
    try:
        req = urllib.request.Request(CURSE_PUBLIC % pid, headers={"User-Agent": "Mozilla/5.0",
                                                                  "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            files = json.loads(resp.read().decode("utf-8")).get("data") or []
    except Exception as exc:  # noqa: BLE001 - message brut de l'API
        print("ERREUR : etat de publication illisible (%s)" % exc, file=sys.stderr)
        return 1
    for f in files:
        name = f.get("displayName") or f.get("fileName") or ""
        if want in name:
            print("publie : %s | type %s | versions %s" % (
                name, f.get("releaseType"), ", ".join(str(v) for v in f.get("gameVersions") or [])))
            return 0
    print("en attente de moderation : %s n'apparait pas encore sur la page du projet (%d fichier(s) public(s))"
          % (want, len(files)))
    return 2


def version():
    for line in open(TOC, encoding="utf-8"):
        if line.startswith("## Version:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("## Version introuvable dans %s" % TOC)


def changelog():
    """Section de CHANGELOG.md pour la version courante, sinon les 30 premieres lignes utiles."""
    text = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
    m = re.search(r"^## \[?%s\]?.*?$(.*?)(?=^## |\Z)" % re.escape(version()), text, re.M | re.S)
    if m:
        return m.group(1).strip()
    return "\n".join(text.split("\n")[6:36]).strip()


def multipart(fields, path):
    """Corps multipart/form-data minimal (une seule piece : le fichier)."""
    boundary = uuid.uuid4().hex
    body = b""
    for name, value in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                 % (boundary, name, value)).encode("utf-8")
    body += ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
             "Content-Type: application/zip\r\n\r\n" % (boundary, os.path.basename(path))).encode("utf-8")
    body += open(path, "rb").read() + ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    return body, "multipart/form-data; boundary=%s" % boundary


def post(url, headers, body, content_type):
    req = urllib.request.Request(url, data=body, headers=dict(headers, **{"Content-Type": content_type}))
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def notes_file():
    """--notes <fichier> : ecrit la section du CHANGELOG de la version courante (notes de release)."""
    if "--notes" not in sys.argv:
        return None
    path = sys.argv[sys.argv.index("--notes") + 1]
    open(path, "w", encoding="utf-8").write(changelog() + "\n")
    print("notes de version ecrites dans %s" % path)
    return 0


def selected_targets(targets):
    """--only curse|wago : restreint l'envoi a une plateforme (defaut : les deux)."""
    if "--only" not in sys.argv:
        return targets
    want = sys.argv[sys.argv.index("--only") + 1].strip().lower()
    alias = {"curse": "CurseForge", "curseforge": "CurseForge", "wago": "Wago Addons"}
    if want not in alias:
        raise SystemExit("cible inconnue : %s (attendu : curse ou wago)" % want)
    return [t for t in targets if t[0] == alias[want]]


def main():
    dry = "--dry-run" in sys.argv
    if "--status" in sys.argv:
        return publication_status()
    if "--notes" in sys.argv:
        return notes_file()
    if not os.path.exists(ZIP):
        raise SystemExit("archive absente : lancer python3 tools/package.py")
    ver, notes = version(), changelog()
    # version de jeu CurseForge : 17053 = Forever 1.60.1. Sans elle, le fichier s'affiche
    # « no game version » et n'est pas propose par l'application.
    game_version = int(os.environ.get("CF_GAME_VERSION_ID", "17053"))
    # envoi manuel = beta par defaut (un fichier release sur un projet neuf part en moderation) ;
    # le workflow de tag force release via CF_RELEASE_TYPE=release
    release_type = os.environ.get("CF_RELEASE_TYPE", "beta")
    # Wago exige un patch de jeu : Forever n'y connait que 1.60.1. La stabilite suit le type d'envoi.
    wago_patch = os.environ.get("WAGO_PATCH", "1.60.1")
    wago_stability = os.environ.get("WAGO_STABILITY",
                                    "stable" if release_type == "release" else "beta")
    targets = [
        ("CurseForge", "CF_PROJECT_ID", "CF_API_TOKEN", CURSE_URL,
         {"metadata": json.dumps({"changelog": notes, "changelogType": "markdown",
                                  "displayName": ver, "releaseType": release_type,
                                  "gameVersions": [game_version]})},
         "version de jeu %d, type %s" % (game_version, release_type)),
        ("Wago Addons", "WAGO_PROJECT_ID", "WAGO_API_TOKEN", WAGO_URL,
         {"metadata": json.dumps({"label": ver, "stability": wago_stability, "changelog": notes,
                                  "supported_forever_patch": wago_patch})},
         "canal %s, patch Forever %s" % (wago_stability, wago_patch)),
    ]
    missing = []
    for name, id_var, token_var, url, fields, detail in selected_targets(targets):
        pid = os.environ.get(id_var)
        token = os.environ.get(token_var)
        where = url % (pid or "<%s>" % id_var)
        print("%-12s %s  version %s  fichier %s  (%s)"
              % (name, where, ver, os.path.basename(ZIP), detail))
        if dry:
            continue
        if not pid or not token:
            missing.append("%s : %s et %s requis" % (name, id_var, token_var))
            continue
        body, ctype = multipart(fields, ZIP)
        header = ({"X-Api-Token": token} if name == "CurseForge" else {"authorization": "Bearer " + token})
        try:
            status, text = post(url % pid, header, body, ctype)
            print("  -> HTTP %s %s" % (status, text[:120]))
        except Exception as exc:  # noqa: BLE001 - on remonte le message brut de l'API
            missing.append("%s : %s" % (name, exc))
    if missing:
        for msg in missing:
            print("ERREUR :", msg, file=sys.stderr)
        return 1
    print("ok" if not dry else "dry-run : rien n'a ete envoye")
    return 0


if __name__ == "__main__":
    sys.exit(main())
