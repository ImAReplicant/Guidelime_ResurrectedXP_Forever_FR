#!/usr/bin/env python3
"""Genere l'addon de dump des noms localises (a installer une fois dans WoW).

L'addon liste tous les identifiants references par les guides (objets, creatures, quetes) et ecrit
leurs noms francais lus depuis le client dans SavedVariables. On couvre ainsi le contenu custom
(WoW Forever) absent des bases frFR de Guidelime et de Wowhead.

Usage : python3 tools/gen_dump.py
Sortie : Guidelime_FR_Dump/ (dossier addon) — puis `python3 tools/import_dump.py <fichier.lua>`
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = os.path.join(ROOT, "upstream", "Guidelime_ResurrectedXP_Forever_Alliance")
OUT = os.path.join(ROOT, "Guidelime_FR_Dump")
DIRS = ["Speedrun", "Dungeon Route", "Riverglades"]

TOC = """## Interface: %s
## Title: Guidelime FR Dump
## Notes: Exporte les noms FR des objets/PNJ/quetes utilises par les guides (a lancer une fois).
## SavedVariables: GuidelimeFRDumpDB

data.lua
core.lua
"""

CORE = '''-- Exporte les noms localises des objets/PNJ/quetes references par les guides.
-- Client WoW: Forever = base client moderne : les globals Classic ont disparu, on utilise
-- donc les API C_* avec repli sur les globals.
-- Deux messages seulement : debut de collecte, puis fin.
local PREFIX = "|cff2a9df4Guidelime FR Dump|r : "

local f = CreateFrame("Frame")
local elapsed, attempts = 0, 0
local MAX_ATTEMPTS = 150 -- ~5 minutes a 2s d'intervalle
local requested = {}
local done = false

local getItemInfo = GetItemInfo or (C_Item and C_Item.GetItemInfo)
local requestItem = C_Item and C_Item.RequestLoadItemDataByID
local getCreatureInfo = C_CreatureInfo and C_CreatureInfo.GetCreatureInfo
local getTooltip = C_TooltipInfo and C_TooltipInfo.GetHyperlink
local getQuestTitle = C_QuestLog and (C_QuestLog.GetQuestInfo or C_QuestLog.GetTitleForQuestID)
local getObjectives = C_QuestLog and C_QuestLog.GetQuestObjectives

local pendingItems, pendingCreatures, pendingQuests = {}, {}, {}
local questCursor = 1

local function initPending()
    if #pendingItems > 0 or #pendingCreatures > 0 or #pendingQuests > 0 then return end
    for _, id in ipairs(GuidelimeFRDumpItems or {}) do pendingItems[#pendingItems + 1] = id end
    for _, id in ipairs(GuidelimeFRDumpCreatures or {}) do pendingCreatures[#pendingCreatures + 1] = id end
    for _, id in ipairs(GuidelimeFRDumpQuests or {}) do pendingQuests[#pendingQuests + 1] = id end
end

local function creatureName(id)
    if getCreatureInfo then
        local ok, info = pcall(getCreatureInfo, id)
        if ok and info and info.name then return info.name end
    end
    return nil
end

local function questName(id)
    if getTooltip then
        local ok, data = pcall(getTooltip, "quest:" .. id)
        if ok and data and data.lines and data.lines[1] then
            local line = data.lines[1]
            local text = line.leftText or line.left
            if type(text) == "string" and text ~= "" and text ~= RETRIEVING_DATA then return text end
        end
    end
    if getQuestTitle then
        local ok, title = pcall(getQuestTitle, id)
        if ok and type(title) == "string" and title ~= "" then return title end
    end
    if GetQuestLink then
        local ok, link = pcall(GetQuestLink, id)
        if ok and type(link) == "string" then
            local name = link:match("%[(.-)%]")
            if name and name ~= "" then return name end
        end
    end
    return nil
end

-- objectifs de quete : "Gyrostabiliseur de moissonneur: 3/5" -> "Gyrostabiliseur de moissonneur"
-- on ne garde que les textes qui sont de vrais noms (pas "Tuer X", pas de compteurs)
local function cleanObjective(text)
    text = text:gsub("|%d[^;]*;", "")                 -- marqueurs de pluriel |4singulier:pluriel;
    text = text:gsub("[:：]%s*%d+%s*/%s*%d+%s*$", "") -- ": 3/5"
    text = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
    text = text:gsub("^%s+", ""):gsub("%s+$", "")
    if text == "" or text:find("%d") or text:find("[:：/|;]") then return nil end
    return text
end

local function dumpObjectives(id)
    if not getObjectives then return end
    local ok, objectives = pcall(getObjectives, id)
    if not ok or type(objectives) ~= "table" then return end
    for i, obj in ipairs(objectives) do
        local text = type(obj) == "string" and obj or (type(obj) == "table" and obj.text)
        if type(text) == "string" and text ~= "" then
            local name = cleanObjective(text)
            if name then
                GuidelimeFRDumpDB["questobj:" .. id .. "#" .. i] = name
            end
        end
    end
end

local function dump()
    GuidelimeFRDumpDB = GuidelimeFRDumpDB or {}
    initPending()
    local items, creatures, quests = 0, 0, 0
    for i = #pendingItems, 1, -1 do
        local id = pendingItems[i]
        local name
        if getItemInfo then
            local ok, n = pcall(getItemInfo, id)
            if ok then name = n end
        end
        if name then
            GuidelimeFRDumpDB["item:" .. id] = name
            items = items + 1
            table.remove(pendingItems, i)
        elseif not requested[id] and requestItem then
            requested[id] = true
            pcall(requestItem, id)
        end
    end
    for i = #pendingCreatures, 1, -1 do
        local id = pendingCreatures[i]
        local name = creatureName(id)
        if name then
            GuidelimeFRDumpDB["creature:" .. id] = name
            creatures = creatures + 1
            table.remove(pendingCreatures, i)
        end
    end
    -- les quetes sont interrogees par tranches pour ne pas faire ramer le client
    local budget = math.min(#pendingQuests, 200)
    while budget > 0 do
        if questCursor > #pendingQuests then questCursor = 1 end
        if #pendingQuests == 0 then break end
        local id = pendingQuests[questCursor]
        local name = questName(id)
        if name then
            GuidelimeFRDumpDB["quest:" .. id] = name
            quests = quests + 1
            dumpObjectives(id)
            table.remove(pendingQuests, questCursor)
        else
            questCursor = questCursor + 1
        end
        budget = budget - 1
    end
    return items, creatures, quests
end

local function finish()
    if done then return end
    done = true
    f:SetScript("OnUpdate", nil)
    print(PREFIX .. "terminé, vous pouvez vous déconnecter.")
    if #pendingItems + #pendingCreatures + #pendingQuests > 0 then
        print(string.format(PREFIX .. "INCOMPLET : %d objet(s), %d PNJ, %d quete(s) non resolus (delai de 5 min atteint).",
            #pendingItems, #pendingCreatures, #pendingQuests))
    end
end

f:RegisterEvent("PLAYER_LOGIN")
f:RegisterEvent("BAG_UPDATE")
f:SetScript("OnEvent", function(_, event)
    dump()
    if event == "PLAYER_LOGIN" then
        print(PREFIX .. "collecte des noms en cours, patientez quelques secondes (5 minutes maximum)...")
    end
end)

f:SetScript("OnUpdate", function(_, dt)
    elapsed = elapsed + dt
    if elapsed < 2 then return end
    elapsed = 0
    attempts = attempts + 1
    dump()
    if attempts >= MAX_ATTEMPTS or (#pendingItems == 0 and #pendingCreatures == 0 and #pendingQuests == 0) then
        finish()
    end
end)
'''


def interface_version():
    """Numero d'interface declare par l'addon EN (source unique)."""
    toc = os.path.join(EN, "Guidelime_ResurrectedXP_Forever_Alliance.toc")
    for line in open(toc, encoding="utf-8"):
        if line.startswith("## Interface:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit("## Interface introuvable dans %s" % toc)


def main():
    os.makedirs(OUT, exist_ok=True)
    items, creatures, quests = set(), set(), set()
    for d in DIRS:
        for path in glob.glob(os.path.join(EN, d, "*.lua")):
            for line in open(path, encoding="utf-8"):
                items.update(int(i) for i in re.findall(r"\[(?:CI|UI)(\d+)", line))
                creatures.update(int(i) for i in re.findall(r"\[TAR(\d+)", line))
                for ids in re.findall(r"\[Q[ATCS]([0-9/]+)", line):
                    quests.update(int(x) for x in ids.split("/") if x.isdigit())
    open(os.path.join(OUT, "Guidelime_FR_Dump.toc"), "w", encoding="utf-8").write(TOC % interface_version())
    open(os.path.join(OUT, "core.lua"), "w", encoding="utf-8").write(CORE)
    with open(os.path.join(OUT, "data.lua"), "w", encoding="utf-8") as f:
        f.write("GuidelimeFRDumpItems = {%s}\n" % ",".join(str(i) for i in sorted(items)))
        f.write("GuidelimeFRDumpCreatures = {%s}\n" % ",".join(str(i) for i in sorted(creatures)))
        f.write("GuidelimeFRDumpQuests = {%s}\n" % ",".join(str(i) for i in sorted(quests)))
    print("addon ecrit dans", OUT)
    print("objets :", len(items), "| creatures :", len(creatures), "| quetes :", len(quests))


if __name__ == "__main__":
    main()
