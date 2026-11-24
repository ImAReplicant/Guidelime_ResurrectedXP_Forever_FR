# Journal des modifications

Toutes les versions notables de la traduction française de *Guidelime — ResurrectedXP Forever (Alliance)*.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Versionnement : `<version amont>-fr.<n>`,
où la version amont est celle de l'addon anglais (`## Version` de son `.toc`).

## [1.8.0-fr.1] — 2026-11-24

Mise à jour vers les guides anglais **1.8.0** (73 fichiers amont modifiés).

### Modifié
- Guides `Speedrun/`, `Dungeon Route/` et `Riverglades/` régénérés depuis l'amont 1.8.0 ; les
  traductions existantes sont conservées (mémoire de traduction).
- `glossaire/` régénéré (`cles.json`, `name_ids.json`, `quest_ids.json`, `en_ids.json`, `auto_*`).

### À faire
- **21 clauses** (42 occurrences) apparaissent en anglais dans `RAPPORT-traduction.md` : à traduire dans
  `glossaire/trad/` lors de la prochaine passe.

## [1.7.6-fr.1] — 2026-11-23

Première version publiable.

### Ajouté
- Traduction française de 121 guides (Speedrun 60, Dungeon Route 57, Riverglades 4) : instructions,
  titres de quêtes, noms de PNJ/objets, détails et titres de guides.
- Chaîne d'outils sans dépendance : `extract.py` → `wowhead_names.py` → `build_fr.py` → `validate.py` →
  `package.py` → `release.py`, plus `gen_dump.py` / `import_dump.py` / `import_sv.py` pour les noms lus
  dans le client.
- Complétion des noms propres du contenu WoW Forever via la base Wowhead `/forever/` (699 noms).
- `validate.py` : contrôle des balises, identifiants, zones, liens entre guides, `.toc` ↔ disque, codes
  WoW non évalués, reste d'anglais.
- `build_fr.py --selftest` : auto-contrôle des heuristiques (pluriels, registre, rangs, possessifs,
  codes WoW).
- Icône de l'addon (dérivée de celle de Guidelime, bandeau tricolore) et `tools/make_icon.sh`.

### Corrigé
- Noms de PNJ héritant du nom d'un objet ou d'un objectif de quête (`Parler à *Kit de feu de camp
  basique*`), par appariement par identité et purge des entrées périmées du dump client.
- `(Rank N)` non résolu → `(rang N)`.
- Possessifs français toujours masculins (`son *Tête*` → `sa *Tête*`).
- Registre mélangé dans une même phrase (vouvoiement après `!`, `:`, `…`).
- Titres de quêtes laissés en anglais dans la prose (`Abandonner …`, conditions `si vous n'avez pas fait X`).
- Apostrophes typographiques et espaces de bord dans les noms.

### Connu
- Le texte d'objectif affiché sous un `[QC…]` vient de Questie et du client : un gabarit non évalué
  comme `|4personnage tué:personnages tués;` est un défaut des données de la quête côté serveur.
- 279 noms propres restent en anglais (contenu Forever absent de Wowhead et des bases Guidelime).
