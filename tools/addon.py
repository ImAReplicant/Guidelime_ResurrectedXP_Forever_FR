"""Nom et chemins de l'addon FR construit par la chaine.

Aujourd'hui un seul addon (Alliance). La version Horde se construira avec
`ADDON_NAME=Guidelime_ResurrectedXP_Forever_Horde_FR` sans editer les outils.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.environ.get("ADDON_NAME", "Guidelime_ResurrectedXP_Forever_Alliance_FR")
OUT = os.path.join(ROOT, ADDON)
TOC = ADDON + ".toc"
