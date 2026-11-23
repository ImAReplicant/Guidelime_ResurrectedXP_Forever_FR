# Traduction française — Guidelime RestedXP Forever (Alliance)

Addon séparé : `Guidelime_ResurrectedXP_Forever_Alliance_FR/`. Les guides anglais d'origine (dossier
`upstream/Guidelime_ResurrectedXP_Forever_Alliance/`) servent d'entrée de build et ne sont pas distribués
ici ; les deux addons peuvent être installés en même temps (groupes de guides distincts, suffixés « FR »).

**Périmètre traduit : `Speedrun/` (60 guides), `Dungeon Route/` (57) et `Riverglades/` (4), soit 121 guides.
`Dungeon Quests/` (24) et `Mage AoE/` (20) ne sont pas traduits** — ils restent disponibles en anglais
dans l'addon d'origine. Pour les ajouter : ajouter les deux dossiers à `DIRS` dans les quatre scripts de
`tools/` (`extract.py`, `build_fr.py`, `gen_dump.py`, `validate.py`), relancer la chaîne, puis traduire les
nouvelles chaînes listées dans `RAPPORT-traduction.md`.

## Installation

L'addon est prêt à copier, à la racine du dépôt :

```
Guidelime_ResurrectedXP_Forever_Alliance_FR/   <- guides français (l'addon à installer)
upstream/                                      <- guides anglais d'origine (entrée de build)
```

Copier `Guidelime_ResurrectedXP_Forever_Alliance_FR/` dans
`World of Warcraft/_classic_era_/Interface/AddOns/` (ou le dossier AddOns de votre client), puis `/lime`
en jeu : les guides apparaissent dans le groupe « RestedXP Forever … FR ». Rien à renommer, aucun zip à
construire ; un « Download ZIP » de GitHub donne un dossier `<dépôt>-main` qui **contient** l'addon — copier
le dossier `Guidelime_ResurrectedXP_Forever_Alliance_FR/`, pas `<dépôt>-main` (WoW charge
`<dossier>/<dossier>.toc`).

## Ce qui est traduit

Les pourcentages exacts sont régénérés à chaque build dans **[RAPPORT-traduction.md](RAPPORT-traduction.md)** ;
le tableau ci-dessous indique seulement la source de chaque type de texte.

| Élément | Source de la traduction |
|---|---|
| Instructions hors balises | glossaire manuel (`glossaire/trad/`) — 100 % des occurrences |
| Titres de quêtes | base `questsDB_frFR` + `import_sv.py` + `import_dump.py` |
| Noms de PNJ / objets / objets interactifs | bases frFR de Guidelime + résolution par identifiant + Wowhead Forever + dump client + glossaire |
| Titres de guides, détails de guides | glossaire manuel — 100 % |

Ce qui reste en anglais est volontaire : ce sont les noms propres absents des bases frFR de Guidelime —
contenu ajouté par WoW Forever (que le client français affiche aussi en anglais) **et** quelques PNJ/objets
classiques que ces bases ne couvrent pas (ex. `Stitches`, « Balafreux » en français). Un nom traduit à la
main dans `glossaire/trad/33-noms-verifies.json` est prioritaire. La liste exacte est dans
`RAPPORT-traduction.md`.

**Ne sont jamais modifiés** : les codes de balises, les identifiants de quêtes/objectifs, les coordonnées,
les noms de zones dans `[G …]`/`[L …]` (comparés par Guidelime à sa table de noms anglais), les classes/races
dans `[A …]`/`[GA …]`. La progression automatique est donc strictement identique à la version anglaise.

## Chaîne de production

```
python3 tools/extract.py        # 1. extrait les unités à traduire + les noms FR des bases Guidelime
python3 tools/wowhead_names.py  # 1b. complète les noms restants via la base Wowhead Forever (réseau)
python3 tools/build_fr.py       # 2. génère l'addon FR + RAPPORT-traduction.md
python3 tools/build_fr.py --selftest   #    auto-contrôle des heuristiques (pluriel, registre, rangs)
python3 tools/validate.py       # 3. vérifie l'intégrité (code de sortie 1 si erreur)
python3 tools/show.py clauses 0 200 --reste   # aide : affiche les unités non traduites
```

### Résolution automatique des noms

`extract.py` résout les noms de la prose sans intervention manuelle, dans cet ordre :

1. **correspondance exacte** avec les bases frFR de Guidelime (créatures, objets, objets interactifs) ;
2. **singulier automatique** (`Sacks of Oats` → `Sack of Oats` → « Sac d'avoine », re-pluralisé) ;
3. **via l'identifiant de la balise** : le nom est apparié aux `[CI…]`/`[UI…]`/`[TAR…]` de la même ligne
   (`*Vulture Meat*` + `[CI729,3]` → item 729 → « Viande filandreuse de vautour »). Les appariements
   ambigus (votes contradictoires) sont ignorés ;
4. **titres de quêtes** cités dans la prose, via `questsDB_frFR` puis les dictionnaires de quêtes
   importés (`30-client.json`, `32-sv.json`, `31-quetes-manuelles.json`).

Le résultat est écrit dans `glossaire/auto_noms_ids.json` (nom → nom FR), `glossaire/name_ids.json`
(nom → identifiant), `glossaire/quest_ids.json` (titre de quête → id) et `glossaire/en_ids.json`
(identifiant → nom anglais), tous régénérés par `extract.py`.

Les noms importés du client (`30-client.json`) sont appariés par identifiant et ne remplacent jamais un nom
des bases Guidelime frFR : `build_fr.py` écarte les entrées en conflit, elles ne servent que pour le contenu
absent de ces bases. `29-wowhead.json` reçoit le même traitement.

### Compléter les noms restants via Wowhead (sans lancer WoW)

Le contenu ajouté par WoW Forever est absent des bases frFR de Guidelime, mais **Wowhead le référence sous
son espace `/forever/`, localisé en français**. Wowhead n'expose aucune API publique (pas de clé, pas
d'inscription, pas de programme partenaire accessible) : le tool s'appuie sur les deux endpoints JSON que
sert son propre site, qui ne demandent aucun jeton.

| Endpoint | Rôle |
|---|---|
| `https://www.wowhead.com/forever/search/suggestions-template?q=<nom>` | nom anglais → id, type (`NPC`, `Item`, `Quest`, `Spell`, `Object`) et nom anglais du résultat |
| `https://nether.wowhead.com/forever/tooltip/<type>/<id>?locale=frFR` | nom localisé |

`tools/wowhead_names.py` interroge les noms que la chaîne n'arrive pas à résoudre : correspondance exacte
sur le nom anglais, puis repli sur le singulier (`Al'Aketh Healers` → `Al'Aketh Healer` → « Soigneur
al'aketh », re-pluralisé). Le nom anglais renvoyé par la recherche est comparé au nom cherché avant
d'appeler le tooltip (la recherche renvoie aussi des homonymes) ; pour un identifiant déjà apparié
(`name_ids.json`), c'est `en_ids.json` qui sert de contrôle, sans requête. Sortie :
`glossaire/trad/29-wowhead.json`, numéroté **avant** les fichiers issus du client (`30-client.json`,
`32-sv.json`, `33-noms-verifies.json`) pour que ceux-ci restent prioritaires. Le tool est reprenable
(les noms déjà résolus ne sont pas réinterrogés) et limitable : `--limit N`, `--delay S` ; sur un 403 de
Wowhead il patiente puis reprend là où il s'était arrêté.

`python3 tools/wowhead_names.py --check` compare, lui, les noms Wowhead aux noms lus dans le client
(`30-client.json`) et liste les divergences : écarts de capitalisation (`Une Note chiffonnée` côté
Wowhead) et entrées client douteuses, où un objectif de quête a été pris pour un nom propre.

Le client reste la référence d'affichage ; il reste nécessaire pour les sorts et les quelques PNJ absents
de Wowhead (`Read Ley Line`, `Jenna`, `Glyx`). Deux imports complémentaires :

```
# 1. noms de quetes deja mis en cache par d'autres addons (hors ligne, ex. Darnassus47)
python3 tools/import_sv.py ~/.../WTF/Account/<COMPTE>/SavedVariables

# 2. dump complet depuis le client (objets, PNJ, quetes)
python3 tools/gen_dump.py                       # génère l'addon Guidelime_FR_Dump/
# copier Guidelime_FR_Dump/ dans Interface/AddOns/, lancer WoW, attendre le message de fin, se déconnecter
python3 tools/import_dump.py ~/.../WTF/Account/<COMPTE>/SavedVariables/Guidelime_FR_Dump.lua
python3 tools/build_fr.py && python3 tools/validate.py
```

`import_dump.py` écrit `glossaire/trad/30-client.json` (sections `noms` et `quetes`) et `import_sv.py`
`glossaire/trad/32-sv.json`, fusionnés comme les autres fichiers de glossaire. À relancer après chaque
ajout de guide.

`tools/extract.py` lit les bases de Guidelime ; par défaut dans `/tmp/gl/Guidelime`, sinon :
`GUIDELIME_DIR=/chemin/vers/Guidelime python3 tools/extract.py`.

`validate.py` lit Guidelime pour les contrôles de codes de balises et de noms de zones (`GuideParser.lua`,
`Data/MapDB.lua`) ; s'il ne le trouve pas, il **affiche un avertissement, saute ces deux contrôles et sort
en 0** — les autres vérifications (nombre de lignes, séquence de balises, identifiants, coordonnées,
séparateurs, `.toc` ↔ disque, liens entre guides) restent faites. Il vérifie aussi la ligne finale de
chaque fichier (`]==], "…")`, un `)` manquant rendant le fichier entier inchargeable par WoW), l'absence de
code WoW non évalué (`|4…;`), et, si `luac` est présent dans le `PATH`, compile chaque fichier avec `luac -p`.

`glossaire/cles.json`, `glossaire/auto_noms.json` et `glossaire/auto_quetes.json` sont **générés** par
`extract.py` (ne pas les éditer à la main) : ce sont des instantanés des bases de Guidelime, donc leur
diff est volumineux à chaque mise à jour de l'addon. Ils sont versionnés pour pouvoir régénérer la
traduction sans Guidelime installé.

### Mettre à jour après une nouvelle version du guide anglais

1. Remplacer les fichiers de `Speedrun/`, `Dungeon Route/`, `Riverglades/` par la nouvelle version.
2. Relancer les trois commandes ci-dessus.
3. Les chaînes déjà traduites sont conservées (mémoire de traduction) ; `RAPPORT-traduction.md` liste
   uniquement ce qui reste à traduire, à ajouter dans un nouveau fichier `glossaire/trad/NN.json`.

### Format du glossaire

`glossaire/trad/*.json`, fusionnés par ordre alphabétique :

```json
{
  "clauses": { "Talk to {N}": "Parler à {N}" },
  "noms":    { "Small Eggs": "Petits œufs" },
  "quetes":  { "The Balance of Nature": "L'équilibre de la nature" },
  "guides":  { "Westfall": "Marche de l'Ouest" },
  "details": { "<texte [D …] anglais>": "<texte français>" }
}
```

`{N}` = emplacement d'un nom mis en évidence dans le guide ; le nombre de `{N}` doit être identique
dans la clé et la valeur (sinon la traduction est ignorée et signalée par `build_fr.py`).

### Registre

Le guide parle au joueur en **vouvoiement** (« Cochez cette étape »), mais les instructions commencent par
un **infinitif** (« Cocher cette étape ») pour rester homogènes. `build_fr.py` ramène donc au début de
chaque phrase et après `et`/`puis` les verbes vouvoyés connus (`VOUS_TO_INF`, ~110 entrées) à l'infinitif —
y compris dans vos entrées de glossaire : écrire « Cochez… » y produit « Cocher… ». Pour garder un
impératif, commencez la phrase par autre chose (un nom, un adverbe) ou ajoutez la forme voulue au
glossaire avec un verbe absent de `VOUS_TO_INF`.

## Limites connues

- **Toutes les instructions** (texte hors balises, y compris les textes `[XP …]` et `[D …]`) sont traduites.
  Ce qui reste en anglais, ce sont uniquement des **noms propres** : PNJ, objets et quêtes absents des bases
  frFR de Guidelime — contenu ajouté par WoW Forever (que le client français affiche aussi en anglais) et
  quelques entrées classiques que ces bases ne couvrent pas (ex. `Stitches` = « Balafreux »). Dans ce second
  cas, le joueur voit un nom français en jeu et un nom anglais dans le guide.
- Les noms propres ne sont pas traduits « à la main » : ils viennent des bases frFR de Guidelime.
  Pour en corriger un, ajouter une entrée dans `noms` du glossaire.
- Les **noms de lieux dans les balises** `[S …]` (pierre de foyer) et `[H …]` (auberge) restent en anglais :
  Guidelime les affiche tels quels, ils ne sont pas utilisés comme clé de recherche. `[F …]`/`[P …]` en
  revanche **ne doivent pas** être traduits : Guidelime s'en sert pour retrouver le maître de vol
  (`FM.getFlightmasterByPlace`). `[SK Blacksmithing 1 -]` est correct
  tel quel : Guidelime affiche le nom localisé de la compétence (« Forge »).
- Les **titres de quêtes** cités dans la prose (`Abandonner …`) sont résolus dans les bases de quêtes ;
  ceux absents de ces bases restent en anglais et sont listés dans `RAPPORT-traduction.md`
  (ligne « Titres de quetes cites dans la prose »).
- La **ligne d'objectif** affichée sous un `[QC…]` vient de Questie et du client, pas du guide : un gabarit
  de pluriel non évalué comme `|4personnage tué:personnages tués;` est un défaut des données de la quête
  côté serveur (il apparaît aussi dans le guide anglais, avec « character/characters »), impossible à
  corriger ici. En revanche aucun code WoW (`|4…;`, `|c…|r`, `|H…|h`) ne peut sortir de nos fichiers :
  `build_fr.py` les retire de tout texte émis et `validate.py` échoue si un `|` apparaît dans la sortie.
- Aucun test en jeu automatisé : la validation est structurelle (voir `tools/validate.py`).
