# AGENTS.md — repère pour les agents et les mainteneurs

Dépôt des **traductions françaises** de *Guidelime — ResurrectedXP Forever* (WoW Forever,
client `Interface: 16001`). L'addon **Alliance** est publié aujourd'hui ; la version **Horde** viendra
plus tard (d'où le nom du dépôt sans « Alliance »). Les guides anglais ne sont pas publiés ici : ils sont
l'entrée de build.

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

Le nom de l'addon est centralisé dans `tools/addon.py` (`ADDON`, surchargeable par la variable
d'environnement `ADDON_NAME`) : c'est le point d'entrée pour une seconde édition.

### Ajouter la version Horde (plus tard)

1. Déposer les guides EN Horde dans `upstream/Guidelime_ResurrectedXP_Forever_Horde/`.
2. Ajouter un glossaire généré par corpus : `cles.json`, `name_ids.json`, `auto_*` décrivent **un** corpus
   de guides, ils ne peuvent pas être partagés entre Alliance et Horde. La mémoire de traduction
   `glossaire/trad/` (clauses, noms, quêtes) reste commune.
3. Construire avec `ADDON_NAME=Guidelime_ResurrectedXP_Forever_Horde_FR` et un dossier de sortie dédié
   (`tools/addon.py` accepte déjà la surcharge ; `build_fr.py` lit `upstream/…_Alliance` en dur, à
   paramétrer à ce moment-là).
4. Ajouter le job correspondant dans `.github/workflows/release.yml` et un second projet CurseForge/Wago
   (un projet par addon, chacun avec son `## X-Curse-Project-ID` / `## X-Wago-ID`).

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
python3 tools/update_upstream.py --check   # l'addon anglais a-t-il bougé ? (sans clé)
bash tools/make_icon.sh           # régénère Media/icon-256.png et Media/Icon.tga
```

`extract.py`, `validate.py` et `gen_dump.py` lisent une installation de Guidelime :
`GUIDELIME_DIR=/chemin/vers/Guidelime` (défaut `/tmp/gl/Guidelime`).

## Mettre à jour depuis l'amont

Les guides anglais viennent de [CurseForge](https://www.curseforge.com/wow/addons/guidelime-resurrectedxp-alliance-forever)
et sont recopiés dans `upstream/` par `tools/update_upstream.py` :

| Commande | Effet |
|---|---|
| `--check` | compare la version de `upstream/…/*.toc` à la dernière publiée ; code 0 = à jour, **2 = mise à jour disponible**, 1 = erreur |
| `--apply` | télécharge et remplace `upstream/Guidelime_ResurrectedXP_Forever_Alliance/` (rien d'autre ne bouge) |
| `--from-zip <archive>` | même chose depuis un zip téléchargé à la main — utile si le service tiers tombe |
| `--selftest` | vérifie le parsing d'une réponse factice, hors ligne |

**Aucune clé n'est nécessaire.** Les métadonnées viennent de [cfwidget](https://api.cfwidget.com/wow/addons/guidelime-resurrectedxp-alliance-forever)
(service tiers qui expose les données CurseForge : id du projet, fichiers, `uploaded_at`) et l'archive du
CDN `mediafilez.forgecdn.net`. L'API officielle `api.curseforge.com/v1` demanderait une clé de la console
*CurseForge for Studios*, qui est un programme B2B sur candidature — inutile ici.

`CF_API_KEY` reste **optionnelle** : si elle est fournie, elle sert de repli sur `edge.forgecdn.net`, qui
exige un `x-api-key` depuis juillet 2026. Si cfwidget est injoignable, `--check` échoue avec un message
explicite ; on passe alors par un téléchargement manuel + `--from-zip`.

Enchaînement après une mise à jour (ou laisser la CI le faire) :

```bash
python3 tools/update_upstream.py --apply
python3 tools/extract.py && python3 tools/build_fr.py && python3 tools/validate.py
```

La version FR suit l'amont automatiquement (`1.7.6` → `1.8.0-fr.1`) : `FR_SUFFIX` ne se bump que pour un
changement **de traduction** à version amont identique. Le workflow `upstream.yml` fait cette vérification
chaque lundi (sans aucun secret) et ouvre une pull request intitulée `Upstream <version>` avec les guides
modifiés et les restes à traduire ; si l'amont n'a pas bougé, il ne produit rien.

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

Premier envoi manuel (avant tout tag) : `release.py` envoie en **beta** par défaut, pour ne pas publier une
version `release` sur un projet tout neuf ; le workflow de tag force `release`.

```bash
python3 tools/package.py
CF_PROJECT_ID=1829310 CF_API_TOKEN=… python3 tools/release.py
```

`CF_GAME_VERSION_ID` (défaut `17053` = Forever 1.60.1) doit correspondre à la version de jeu du client :
sans elle, le fichier s'affiche « no game version » et n'est pas proposé par l'application CurseForge.

Un fichier envoyé sur un projet neuf reste **en attente de modération** avant d'être listé publiquement.
`python3 tools/release.py --status` interroge les pages publiques des deux plateformes et affiche l'état de
la version courante (`publie : 1.8.0-fr.1 | type 2 | versions 1.60.1` / `canal beta`) ; code **0** publié
partout, **2** en attente, **1** illisible. Le workflow `upstream` (hebdomadaire) lance cette vérification
et émet un avertissement tant qu'une plateforme manque.

Attention au contrôle manuel côté Wago : les releases ne sont **pas** dans la page du projet
(`/addons/<slug>` n'a pas de champ `releases`), mais dans
`https://addons.wago.io/addons/<slug>/versions?stability=beta` (puis `stable`, `alpha`).

Corriger le type, la version de jeu ou le changelog d'un fichier **déjà envoyé** (sans ré-uploader) :
`POST https://wow.curseforge.com/api/projects/1829310/update-file`, en-tête `X-Api-Token`, champ `metadata`
= `{"fileID": <id>, "displayName": …, "releaseType": "beta|release|alpha", "gameVersions": [17053],
"changelog": …, "changelogType": "markdown"}`. La réponse `{"id": <fileID>}` confirme que le fichier
appartient bien au projet.

### Checklist de première publication (à faire une fois)

- [x] Dépôt distant et `WEBSITE` renseignés.
- [x] Projet CurseForge créé (id **1829310**, version **Forever**) et `CURSE_ID` renseigné.
- [ ] Projet Wago Addons ; renseigner `WAGO_ID` dans `tools/build_fr.py` et le secret `WAGO_PROJECT_ID`.
- [ ] Secrets GitHub : `CF_API_TOKEN`, `WAGO_API_TOKEN`, `CF_PROJECT_ID`, `WAGO_PROJECT_ID`.
- [ ] Avatar de la page : **`Media/avatar-400.png`** (400×400, imposé par la charte CurseForge). La charte
      interdit l'imagerie sous copyright : l'actuel dérive de l'icône Guidelime, à remplacer par un visuel
      original si la modération le refuse.

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
