# Guidelime — ResurrectedXP Forever (Alliance) — **FR**

Traduction française des guides de leveling **RestedXP Forever (Alliance)** pour
[Guidelime](https://www.curseforge.com/wow/addons/guidelime) sur **WoW: Forever** (client `Interface: 16001`).

L'addon anglais d'origine n'est pas distribué ici : c'est l'entrée de build de cette traduction.
Projet anglais : <https://www.curseforge.com/wow/addons/guidelime-resurrectedxp-alliance-forever>.

## Installation

Copier le dossier `Guidelime_ResurrectedXP_Forever_Alliance_FR/` dans
`World of Warcraft/_classic_era_/Interface/AddOns/`, puis `/lime` en jeu : les guides apparaissent dans
les groupes « RestedXP Forever … FR ».

Aucun renommage n'est nécessaire — WoW charge `<dossier>/<dossier>.toc`, et ce dossier porte déjà le bon
nom. Un « Download ZIP » de GitHub donne un dossier `<dépôt>-main` qui **contient** l'addon : ouvrez-le et
copiez le dossier `Guidelime_ResurrectedXP_Forever_Alliance_FR/`, pas `<dépôt>-main` lui-même.

Dépendances : **Guidelime** et **Questie**. L'addon français peut être installé seul ; il peut aussi
cohabiter avec l'addon anglais (groupes de guides distincts, suffixés « FR »).

## Contenu

| Dossier | Guides |
|---|---|
| `Speedrun/` | 60 |
| `Dungeon Route/` | 57 |
| `Riverglades/` | 4 |

Soit **121 guides** traduits. `Dungeon Quests/` (24) et `Mage AoE/` (20) ne sont pas traduits et restent
disponibles dans l'addon anglais.

La couverture exacte (clauses, noms, titres de quêtes) est régénérée à chaque build dans
**[RAPPORT-traduction.md](RAPPORT-traduction.md)** ; la politique de traduction et la procédure de mise à
jour sont dans **[README-FR.md](README-FR.md)**.

**Ne sont jamais modifiés** : codes de balises, identifiants de quêtes/objectifs, coordonnées, noms de zones
dans `[G …]`/`[L …]`, classes/races dans `[A …]`/`[GA …]`. La progression automatique est strictement
identique à la version anglaise.

## Développement

```
tools/                 chaîne de production (Python 3, sans dépendance)
upstream/              guides anglais d'origine (entrée de build, jamais publiés)
glossaire/             mémoire de traduction + instantanés des bases Guidelime
AGENTS.md              repère pour les contributeurs et les agents : commandes, règles, release
CHANGELOG.md           journal des versions
```

```bash
python3 tools/extract.py && python3 tools/build_fr.py && python3 tools/validate.py
python3 tools/package.py        # dist/Guidelime_ResurrectedXP_Forever_Alliance_FR.zip
python3 tools/release.py --dry-run
```

`extract.py` et `validate.py` lisent une installation de Guidelime (`GUIDELIME_DIR`, défaut
`/tmp/gl/Guidelime`) ; sans elle, `validate.py` saute les contrôles de balises/zones avec un avertissement.

## Crédits et licence

Routes : RestedXP (<https://restedxp.com>), converties pour Guidelime par le projet anglais cité plus haut.
Bases de quêtes/objets/PNJ françaises : [max-ri/Guidelime](https://github.com/max-ri/Guidelime).
Icône : dérivée de celle de Guidelime (© max-ri), avec un bandeau tricolore — elle sera retirée sur demande
de l'auteur.

L'**outillage et la traduction** sont couverts par le fichier `LICENSE` (MIT). Le **texte des routes reste
© RestedXP** et n'est pas couvert par cette licence ; cette traduction est une conversion non officielle et
non commerciale, retirée sur demande des ayants droit.
