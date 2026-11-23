# AGENTS.md — repère pour les agents et les mainteneurs

Dépôt de la **traduction française** de *Guidelime — ResurrectedXP Forever (Alliance)* (WoW Forever,
client `Interface: 16001`). L'addon anglais n'est pas publié ici : c'est l'entrée de build.

## Carte du dépôt

```
Guidelime_ResurrectedXP_Forever_Alliance_FR/   l'addon publié (généré, voir plus bas)
  Speedrun/ Dungeon Route/ Riverglades/        121 guides traduits
  Media/Icon.tga, Media/icon-256.png           icônes (tools/make_icon.sh)
upstream/Guidelime_ResurrectedXP_Forever_Alliance/   guides EN d'origine — entrée de build, jamais publiée
tools/                                         chaîne de production (Python 3, sans dépendance)
glossaire/                                     mémoire de traduction (trad/) + instantanés générés
RAPPORT-traduction.md                          ce qui reste en anglais (généré)
```

Projet anglais d'origine : <https://www.curseforge.com/wow/addons/guidelime-resurrectedxp-alliance-forever>.
L'icône est dérivée de celle de [Guidelime](https://github.com/max-ri/Guidelime) (© max-ri) ; elle sera
retirée sur demande de l'auteur.

## Commandes

```bash
python3 tools/extract.py          # unités à traduire + noms FR des bases Guidelime
python3 tools/wowhead_names.py    # complète les noms restants via Wowhead /forever/ (réseau)
python3 tools/build_fr.py         # génère l'addon FR + RAPPORT-traduction.md
python3 tools/build_fr.py --selftest   # auto-contrôle des heuristiques
python3 tools/validate.py         # porte de sortie (code 1 si erreur)
python3 tools/package.py          # dist/Guidelime_ResurrectedXP_Forever_Alliance_FR.zip
python3 tools/release.py --dry-run     # uploads CurseForge + Wago (sans réseau)
bash tools/make_icon.sh           # régénère Media/icon-256.png et Media/Icon.tga
```

`extract.py`, `validate.py` et `gen_dump.py` lisent une installation de Guidelime :
`GUIDELIME_DIR=/chemin/vers/Guidelime` (défaut `/tmp/gl/Guidelime`).

## Règles dures

- **Ne jamais éditer un fichier généré** : `Guidelime_ResurrectedXP_Forever_Alliance_FR/`,
  `RAPPORT-traduction.md`, `glossaire/{cles,name_ids,quest_ids,en_ids,auto_*}.json`,
  `glossaire/trad/{29,30,32}-*.json`, `Guidelime_FR_Dump/`. On édite la source, puis on relance la chaîne.
- **Toute modification d'un guide sous `upstream/` exige `build_fr.py` + `validate.py` dans le même
  commit** : la CI échoue sinon (« fichiers générés non à jour »).
- Le français du guide est à l'**infinitif** en début d'instruction (« Parler à », « Cocher ») ; les
  possessifs suivent le genre du nom (`sa *Tête*`, `son *Collier*`, liste `FEMININE` dans `build_fr.py`).
- Dans le glossaire, une clé et sa valeur doivent avoir **le même nombre de `{N}`** (sinon la traduction
  est ignorée et le build échoue).
- **Ne jamais traduire** les noms de zones dans `[G …]`/`[L …]`, les classes/races de `[A …]`/`[GA …]`,
  ni `[F …]`/`[P …]` (clés de recherche de Guidelime). `[S …]`/`[H …]` restent en anglais par choix.
- Pas de commentaire dans le code Python/Lua produit ; les commentaires existants expliquent un « pourquoi ».
- `glossaire/trad/` est fusionné par ordre alphabétique (le dernier fichier gagne) : `merge_trad()`
  affiche un avertissement à chaque clé écrasée, à garder à zéro.

## Version et publication

1. Bumper `## Version` dans `upstream/Guidelime_ResurrectedXP_Forever_Alliance/Guidelime_ResurrectedXP_Forever_Alliance.toc`
   (version amont) et `FR_SUFFIX` (`-fr.1` → `-fr.2`) dans `tools/build_fr.py` si seule la traduction change.
2. Ajouter la section correspondante dans `CHANGELOG.md`.
3. `extract` → `build_fr` → `validate` → `package`, puis commit.
4. Tag `v<version>` (ex. `v1.7.6-fr.2`) et push : la CI reconstruit, vérifie, publie la release GitHub
   et envoie l'archive sur CurseForge et Wago.

### Checklist de première publication (à faire une fois)

- [ ] Créer le dépôt distant et remplacer `WEBSITE` dans `tools/build_fr.py` (et le README).
- [ ] Créer le projet CurseForge (jeu *WoW*, version **Forever**, catégorie *Quests & Leveling*) ;
      renseigner `CURSE_ID` dans `tools/build_fr.py` et le secret `CF_PROJECT_ID`.
- [ ] Créer le projet Wago Addons ; renseigner `WAGO_ID` dans `tools/build_fr.py` et le secret
      `WAGO_PROJECT_ID`.
- [ ] Secrets GitHub : `CF_API_TOKEN`, `WAGO_API_TOKEN`, `CF_PROJECT_ID`, `WAGO_PROJECT_ID`.
- [ ] Uploader `Media/icon-256.png` comme avatar des deux pages.

## Pièges connus

- Le texte d'objectif sous un `[QC…]` vient de Questie et du client : un `|4personnage tué:personnages
  tués;` affiché en jeu est un défaut des données de la quête, pas du guide (identique en anglais).
- `glossaire/trad/30-client.json` ne peut être régénéré qu'avec un dump client (`gen_dump.py` +
  `import_dump.py`) ; sinon on le corrige à la main et `validate.py` signale les entrées douteuses.
- `wowhead_names.py` est limité par le débit de Wowhead : lancer par lots (`--limit`, `--delay`), il
  reprend là où il s'est arrêté et patiente sur un 403.
- Les icônes ne sont pas vérifiées par la CI (elle ne lance pas ImageMagick) : après un changement de
  `Media/icon-source.png`, relancer `bash tools/make_icon.sh` et committer les deux sorties. Le script
  échoue si le format n'est plus celui attendu par WoW (TGA 64×64, 32 bits, alpha).
- Le dossier racine du dépôt porte le nom de l'addon : ne pas le renommer sans mettre à jour les READMEs.
