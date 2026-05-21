#!/usr/bin/env python3
"""
stardew-bridge.py — Hoe Down Farms Live Sync
Watches your Stardew save file and serves parsed data to the tracker on your iPhone.
"""

import http.server
import json
import os
import ssl
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

SAVE_PATH = "/Users/roohi/.config/StardewValley/Saves/Hoedown_203853699/Hoedown_203853699"
PORT = 8742
POLL_INTERVAL = 5
_BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(_BRIDGE_DIR, "roohis-macbook-air.tailcce197.ts.net.crt")
KEY_FILE  = os.path.join(_BRIDGE_DIR, "roohis-macbook-air.tailcce197.ts.net.key")

latest_data = {}
last_modified = 0

SKILL_NAMES = ["Farming", "Fishing", "Foraging", "Mining", "Combat"]
SKILL_IDS   = ["farm",    "fish",    "forage",   "mine",   "combat"]

FRIENDSHIP_NPCS = [
    "Abigail","Alex","Caroline","Clint","Demetrius","Elliott","Emily",
    "Evelyn","George","Gus","Harvey","Haley","Jas","Jodi","Kent","Krobus","Leah",
    "Lewis","Linus","Marnie","Maru","Pam","Penny","Pierre","Robin",
    "Sam","Sandy","Sebastian","Shane","Vincent","Willy","Wizard"
]

TRACKED_ITEMS = {
    "CopperOre": "copper", "IronOre": "iron", "GoldOre": "gold",
    "IridiumOre": "iridium", "Quartz": "quartz", "FireQuartz": "fire_quartz",
    "PrismaticShard": "prismatic", "OmniGeode": "omni_geode",
    "Geode": "regular_geode", "FrozenGeode": "frozen_geode",
    "CopperBar": "copper_bar", "IronBar": "iron_bar",
    "GoldBar": "gold_bar", "IridiumBar": "iridium_bar",
    "Amethyst": "amethyst", "Topaz": "topaz", "Aquamarine": "aquamarine",
    "Jade": "jade", "Emerald": "emerald", "Ruby": "ruby", "Diamond": "diamond",
    "Wood": "wood", "Hardwood": "hardwood", "Hay": "hay",
    "Fiber": "fiber", "Stone": "stone", "Coal": "coal",
    "Strawberry": "strawberry", "Blueberry": "blueberry",
    "Cranberries": "cranberry", "CommonMushroom": "common_mushroom",
    "PurpleMushroom": "purple_mushroom", "Truffle": "truffle",
    "Pale Ale": "pale_ale", "Wine": "wine", "Jelly": "jelly",
    "Honey": "honey", "Cheese": "cheese", "Mayonnaise": "mayonnaise",
    "Truffle Oil": "truffle_oil", "Aged Roe": "aged_roe",
    "Duck Mayonnaise": "mayonnaise", "Void Mayonnaise": "mayonnaise",
}

HOARD_ITEM_MAP = {
    "Wild Horseradish": "sp_horseradish", "Daffodil": "sp_daffodil",
    "Leek": "sp_leek", "Dandelion": "sp_dandelion", "Parsnip": "sp_parsnip",
    "Green Bean": "sp_greenbean", "Cauliflower": "sp_cauliflower",
    "Potato": "sp_potato", "Catfish": "sp_catfish", "Eel": "sp_eel",
    "Spice Berry": "su_spiceberry", "Grape": "su_grape",
    "Sweet Pea": "su_sweetpea", "Fiddlehead Fern": "su_fiddlehead",
    "Tomato": "su_tomato", "Hot Pepper": "su_hotpepper",
    "Blueberry": "su_blueberry", "Melon": "su_melon",
    "Wheat": "su_wheat10", "Poppy": "su_poppy", "Sunflower": "su_sunflower",
    "Corn": "su_corn", "Pufferfish": "su_pufferfish", "Tuna": "su_tuna",
    "Tilapia": "su_tilapia", "Red Snapper": "su_redsnapper",
    "Common Mushroom": "fa_mushroom", "Wild Plum": "fa_plum",
    "Hazelnut": "fa_hazelnut", "Blackberry": "fa_blackberry",
    "Eggplant": "fa_eggplant", "Pumpkin": "fa_pumpkin", "Yam": "fa_yam",
    "Apple": "fa_apple", "Pomegranate": "fa_pomegranate",
    "Walleye": "fa_walleye", "Tiger Trout": "fa_tigertrout",
    "Winter Root": "wi_winterroot", "Crystal Fruit": "wi_crystalfruit",
    "Snow Yam": "wi_snowyam", "Crocus": "wi_crocus",
    "Nautilus Shell": "wi_nautilus", "Squid": "wi_squid",
    "Wood": "any_wood", "Hardwood": "any_hardwood", "Stone": "any_stone",
    "Maple Syrup": "any_maplesyrup", "Oak Resin": "any_oakresin",
    "Pine Tar": "any_pinetar", "Cave Carrot": "any_cavecarrot",
    "Red Mushroom": "any_redmush", "Purple Mushroom": "any_purpmush",
    "Coconut": "any_coconut", "Cactus Fruit": "any_cactus",
    "Frozen Geode": "any_frozengeode", "Chub": "any_chub", "Hay": "any_hay",
    "Aquamarine": "any_aquamarine", "Sea Urchin": "any_seaurchin",
    "Sunfish": "any_sunfish", "Shad": "any_shad", "Bream": "any_bream",
    "Ghostfish": "any_ghostfish", "Woodskip": "any_woodskip",
    "Sandfish": "any_sandfish", "Duck Feather": "hard_duckfeather",
    "Truffle": "hard_truffle", "Rabbit's Foot": "hard_rabbit",
    "Large Milk": "hard_largemilk", "Large Egg": "hard_largeeggw",
    "Large Egg (White)": "hard_largeeggw", "Large Egg (Brown)": "hard_largeeggb",
    "Duck Egg": "hard_duckegg", "Wool": "hard_wool",
    "Red Cabbage": "hard_redcabbage", "Goat Milk": "hard_goatmilk",
    "Large Goat Milk": "hard_largemilk", "Cheese": "any_cheese",
    "Honey": "any_honey", "Fried Egg": "any_friedegg", "Maki Roll": "any_makiroll",
    "Largemouth Bass": "any_bass", "Carp": "any_carp", "Bullhead": "any_bullhead",
    "Sturgeon": "any_sturgeon", "Sardine": "any_sardine",
    "Quartz": "any_quartz", "Earth Crystal": "any_earthcrystal",
    "Frozen Tear": "any_frozentear", "Fire Quartz": "any_firequartz",
    "Copper Bar": "any_copperbar", "Iron Bar": "any_ironbar",
    "Gold Bar": "any_goldbar", "Slime": "any_slime", "Bat Wing": "any_batwing",
    "Solar Essence": "any_solar", "Void Essence": "any_void",
    "Wine": "any_wine", "Jelly": "any_jelly", "Juice": "any_wine",
    "Pale Ale": "pale_ale", "Aged Roe": "aged_roe",
    "Mayonnaise": "mayonnaise", "Truffle Oil": "truffle_oil",
    "Void Mayonnaise": "q_voidmayo",
    "Dwarvish Translation Guide": "q_dvd_scroll",
    "Ancient Seed": "q_ancientseeds", "Prismatic Shard": "q_prismatic1",
    "Rabbit's Foot": "q_rabbitsfoot", "Mermaid's Pendant": "q_mermaidpendant",
    "Bouquet": "q_bouquet", "Ancient Fruit": "ds_ancientfruit",
    "Battery Pack": "ds_battery", "Iridium Bar": "ds_iridiumbar",
    "Jade": "ds_jade", "Diamond": "ds_diamond", "Iridium Ore": "ds_iridiumore",
    "Gold Bar": "ds_goldbar", "Refined Quartz": "ds_refinedquartz",
    "Coal": "ds_coal", "Fiber": "ds_fiber",
    # Crab Pot bundle items
    "Crab": "any_crab", "Lobster": "any_lobster", "Crayfish": "any_crayfish",
    "Snail": "any_snail", "Periwinkle": "any_periwinkle", "Shrimp": "any_shrimp",
    "Mussel": "any_mussel", "Clam": "any_clam", "Oyster": "any_oyster",
    # Artisan / Enchanter's bundle items
    "Cloth": "any_cloth", "Goat Cheese": "any_goatcheese",
    "Sweet Gem Berry": "q_sweetgemberry",
}

CC_BUNDLE_MAP = {
    # ── PANTRY ──────────────────────────────────────────────────────────────
    0:  ["sp_parsnip","sp_greenbean","sp_cauliflower","sp_potato"],     # Spring Crops
    1:  ["su_tomato","su_hotpepper","su_blueberry","su_melon"],         # Summer Crops
    2:  ["su_corn","fa_eggplant","fa_pumpkin","fa_yam"],                # Fall Crops
    3:  ["sp_parsnip","su_melon","fa_pumpkin","su_corn"],               # Quality Crops (⚠ gold quality not tracked)
    4:  ["hard_largeeggw","hard_largemilk","hard_largeeggb",            # Animal
         "hard_goatmilk","hard_wool","hard_duckegg"],
    5:  ["truffle_oil","any_cloth","any_goatcheese","any_cheese",       # Artisan (need 4 of listed)
         "any_honey","any_jelly","fa_apple","fa_pomegranate","q_sweetgemberry"],
    # ── FISH TANK ────────────────────────────────────────────────────────────
    6:  ["any_sunfish","sp_catfish","any_shad"],                        # River Fish
    7:  ["any_bass","any_carp","any_bullhead","any_woodskip"],          # Lake Fish
    8:  ["any_sardine","su_tuna","su_redsnapper","su_tilapia"],         # Ocean Fish
    9:  ["sp_catfish","any_bream","sp_eel"],                            # Night Fishing
    10: ["su_pufferfish","any_woodskip","any_ghostfish","fa_tigertrout"], # Specialty Fish
    11: ["any_crab","any_lobster","any_crayfish","any_snail",           # Crab Pot
         "any_periwinkle","any_shrimp","any_mussel","any_clam","any_oyster"],
    # ── CRAFTS ROOM ──────────────────────────────────────────────────────────
    13: ["sp_horseradish","sp_daffodil","sp_leek","sp_dandelion"],      # Spring Foraging
    14: ["su_spiceberry","su_grape","su_sweetpea"],                     # Summer Foraging
    15: ["fa_mushroom","fa_plum","fa_hazelnut","fa_blackberry"],        # Fall Foraging
    16: ["wi_winterroot","wi_crystalfruit","wi_snowyam","wi_crocus"],   # Winter Foraging
    17: ["any_wood","any_stone","any_hardwood"],                        # Construction
    19: ["any_coconut","any_cactus","any_cavecarrot","any_redmush",    # Exotic Foraging (need 5 of listed)
         "any_purpmush","any_maplesyrup","any_oakresin","any_pinetar"],
    # ── BOILER ROOM ──────────────────────────────────────────────────────────
    20: ["any_copperbar","any_ironbar","any_goldbar"],                  # Blacksmith's
    21: ["any_quartz","any_earthcrystal","any_aquamarine","any_firequartz"],  # Geologist's
    22: ["any_slime","any_batwing","any_solar","any_void"],             # Adventurer's
    # ── BULLETIN BOARD ───────────────────────────────────────────────────────
    31: ["any_maplesyrup","su_fiddlehead","hard_truffle","su_poppy",   # Chef's
         "any_makiroll","any_friedegg"],
    32: ["any_purpmush","wi_nautilus","any_chub","any_frozengeode"],   # Field Research
    33: ["any_oakresin","any_wine","q_rabbitsfoot","q_sweetgemberry"],  # Enchanter's
    34: ["any_redmush","any_seaurchin","su_sunflower","hard_duckfeather",  # Dye
         "any_aquamarine","hard_redcabbage"],
    35: ["su_wheat10","any_hay","fa_apple"],                           # Fodder
}

SEASONS = ["spring", "summer", "fall", "winter"]

BUNDLE_NAMES = {
    0:"Spring Crops", 1:"Summer Crops", 2:"Fall Crops", 3:"Quality Crops",
    4:"Animal", 5:"Artisan",
    6:"River Fish", 7:"Lake Fish", 8:"Ocean Fish", 9:"Night Fishing",
    10:"Specialty Fish", 11:"Crab Pot",
    13:"Spring Foraging", 14:"Summer Foraging", 15:"Fall Foraging",
    16:"Winter Foraging", 17:"Construction", 19:"Exotic Foraging",
    20:"Blacksmith's", 21:"Geologist's", 22:"Adventurer's",
    23:"2,500g", 24:"5,000g", 25:"10,000g", 26:"25,000g",
    31:"Chef's", 32:"Field Research", 33:"Enchanter's", 34:"Dye", 35:"Fodder",
}
BUNDLE_ROOMS = {
    0:"Pantry",1:"Pantry",2:"Pantry",3:"Pantry",4:"Pantry",5:"Pantry",
    6:"Fish Tank",7:"Fish Tank",8:"Fish Tank",9:"Fish Tank",10:"Fish Tank",11:"Fish Tank",
    13:"Crafts Room",14:"Crafts Room",15:"Crafts Room",16:"Crafts Room",17:"Crafts Room",19:"Crafts Room",
    20:"Boiler Room",21:"Boiler Room",22:"Boiler Room",
    23:"Vault",24:"Vault",25:"Vault",26:"Vault",
    31:"Bulletin Board",32:"Bulletin Board",33:"Bulletin Board",34:"Bulletin Board",35:"Bulletin Board",
}
ROOM_ORDER = ["Pantry","Crafts Room","Fish Tank","Boiler Room","Bulletin Board","Vault"]
ROOM_EMOJI = {"Pantry":"🌽","Crafts Room":"🌲","Fish Tank":"🐟",
              "Boiler Room":"⚒️","Bulletin Board":"📋","Vault":"💰"}

HOARD_CODE_NAMES = {
    "sp_parsnip":"Parsnip","sp_greenbean":"Green Bean","sp_cauliflower":"Cauliflower",
    "sp_potato":"Potato","sp_catfish":"Catfish","sp_eel":"Eel",
    "sp_horseradish":"Wild Horseradish","sp_daffodil":"Daffodil","sp_leek":"Leek","sp_dandelion":"Dandelion",
    "su_tomato":"Tomato","su_hotpepper":"Hot Pepper","su_blueberry":"Blueberry","su_melon":"Melon",
    "su_corn":"Corn","su_spiceberry":"Spice Berry","su_grape":"Grape","su_sweetpea":"Sweet Pea",
    "su_fiddlehead":"Fiddlehead Fern","su_tuna":"Tuna","su_tilapia":"Tilapia",
    "su_redsnapper":"Red Snapper","su_pufferfish":"Pufferfish","su_sunflower":"Sunflower",
    "su_poppy":"Poppy","su_wheat10":"Wheat",
    "fa_eggplant":"Eggplant","fa_pumpkin":"Pumpkin","fa_yam":"Yam","fa_apple":"Apple",
    "fa_pomegranate":"Pomegranate","fa_mushroom":"Common Mushroom","fa_plum":"Wild Plum",
    "fa_hazelnut":"Hazelnut","fa_blackberry":"Blackberry","fa_tigertrout":"Tiger Trout",
    "wi_winterroot":"Winter Root","wi_crystalfruit":"Crystal Fruit",
    "wi_snowyam":"Snow Yam","wi_crocus":"Crocus","wi_nautilus":"Nautilus Shell",
    "any_wood":"Wood (99)","any_stone":"Stone (99)","any_hardwood":"Hardwood (10)",
    "any_hay":"Hay (10)","any_maplesyrup":"Maple Syrup","any_oakresin":"Oak Resin",
    "any_pinetar":"Pine Tar","any_cavecarrot":"Cave Carrot","any_redmush":"Red Mushroom",
    "any_purpmush":"Purple Mushroom","any_coconut":"Coconut","any_cactus":"Cactus Fruit",
    "any_frozengeode":"Frozen Geode","any_chub":"Chub","any_aquamarine":"Aquamarine",
    "any_seaurchin":"Sea Urchin","any_sunfish":"Sunfish","any_shad":"Shad",
    "any_bream":"Bream","any_ghostfish":"Ghostfish","any_woodskip":"Woodskip",
    "any_bass":"Largemouth Bass","any_carp":"Carp","any_bullhead":"Bullhead",
    "any_sardine":"Sardine","any_quartz":"Quartz","any_earthcrystal":"Earth Crystal",
    "any_firequartz":"Fire Quartz","any_ironbar":"Iron Bar","any_copperbar":"Copper Bar",
    "any_goldbar":"Gold Bar","any_slime":"Slime (99)","any_batwing":"Bat Wing (10)",
    "any_solar":"Solar Essence","any_void":"Void Essence","any_wine":"Wine",
    "any_jelly":"Jelly","any_cheese":"Cheese","any_honey":"Honey",
    "any_friedegg":"Fried Egg","any_makiroll":"Maki Roll","any_cloth":"Cloth",
    "any_goatcheese":"Goat Cheese","any_crab":"Crab","any_lobster":"Lobster",
    "any_crayfish":"Crayfish","any_snail":"Snail","any_periwinkle":"Periwinkle",
    "any_shrimp":"Shrimp","any_mussel":"Mussel","any_clam":"Clam","any_oyster":"Oyster",
    "hard_largemilk":"Large Milk","hard_largeeggw":"Large Egg (W)","hard_largeeggb":"Large Egg (B)",
    "hard_duckegg":"Duck Egg","hard_wool":"Wool","hard_goatmilk":"Goat Milk",
    "hard_redcabbage":"Red Cabbage","hard_duckfeather":"Duck Feather","hard_truffle":"Truffle",
    "truffle_oil":"Truffle Oil","q_rabbitsfoot":"Rabbit's Foot","q_sweetgemberry":"Sweet Gem Berry",
    "vault_2500":"2,500g","vault_5000":"5,000g","vault_10000":"10,000g","vault_25000":"25,000g",
}


def parse_save():
    try:
        tree = ET.parse(SAVE_PATH)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse save: {e}"}

    out = {
        "schema_version": 1,
        "farm": "Hoe Down Farms",
        "updated": datetime.now().strftime("%H:%M:%S"),
        "gold": 0, "season": "spring", "day": 1, "year": 1,
        "isRaining": False, "isSnowing": False, "isLightning": False,
        "isDebrisWeather": False, "dailyLuck": 0.0, "weatherTomorrow": "Sun",
        "skills": {}, "friendship": {}, "inventory": {}, "chest_ore": {},
        "hoard_have": [], "hoard_done": [],
    }

    money = root.find(".//player/money")
    if money is not None: out["gold"] = int(money.text or 0)

    season_el = root.find(".//currentSeason")
    day_el    = root.find(".//dayOfMonth")
    year_el   = root.find(".//year")
    if season_el is not None: out["season"] = season_el.text.lower()
    if day_el    is not None: out["day"]    = int(day_el.text or 1)
    if year_el   is not None: out["year"]   = int(year_el.text or 1)

    for key in ("isRaining", "isSnowing", "isLightning", "isDebrisWeather"):
        el = root.find(f".//{key}")
        if el is not None: out[key] = (el.text == "true")
    luck_el = root.find(".//dailyLuck")
    if luck_el is not None: out["dailyLuck"] = float(luck_el.text or 0)
    wtmr = root.find(".//weatherForTomorrow")
    if wtmr is not None: out["weatherTomorrow"] = wtmr.text or "Sun"

    exp_list = root.findall(".//player/experiencePoints/int")
    if exp_list:
        for idx, skill_id in enumerate(SKILL_IDS):
            if idx < len(exp_list):
                out["skills"][skill_id] = xp_to_level(int(exp_list[idx].text or 0))

    for entry in root.findall(".//friendships/item"):
        key_el = entry.find("key/string")
        pts_el = entry.find("value/Friendship/Points")
        if key_el is not None and pts_el is not None:
            name = key_el.text
            if name in FRIENDSHIP_NPCS:
                out["friendship"][name.lower()] = int(pts_el.text or 0)

    inv_counts = {}
    for item in root.findall(".//player/items/Item"):
        name_el  = item.find("name")
        stack_el = item.find("Stack") or item.find("stack")
        if name_el is not None and name_el.text and stack_el is not None:
            n = name_el.text.replace(" ", "")
            count = int(stack_el.text or 0)
            if n in TRACKED_ITEMS and count > 0:
                key = TRACKED_ITEMS[n]
                inv_counts[key] = inv_counts.get(key, 0) + count

    chest_ore = {"copper": 0, "iron": 0, "gold": 0, "coal": 0}
    for item in root.findall(".//objects/item/value/Object/items/Item"):
        name_el  = item.find("name")
        stack_el = item.find("Stack") or item.find("stack")
        if name_el is not None and name_el.text and stack_el is not None:
            n = name_el.text.replace(" ", "")
            count = int(stack_el.text or 0)
            if n in TRACKED_ITEMS and count > 0:
                key = TRACKED_ITEMS[n]
                inv_counts[key] = inv_counts.get(key, 0) + count
            if n == "CopperOre": chest_ore["copper"] += count
            elif n == "IronOre":  chest_ore["iron"]   += count
            elif n == "GoldOre":  chest_ore["gold"]   += count
            elif n == "Coal":     chest_ore["coal"]   += count

    out["inventory"] = inv_counts
    out["chest_ore"] = chest_ore
    out["copperOre"] = inv_counts.get("copper", 0) + chest_ore["copper"]
    out["ironOre"]   = inv_counts.get("iron",   0) + chest_ore["iron"]
    out["goldOre"]   = inv_counts.get("gold",   0) + chest_ore["gold"]
    out["coal"]      = inv_counts.get("coal",   0) + chest_ore["coal"]

    hoard_have = set()
    all_item_els = (
        list(root.findall(".//player/items/Item")) +
        list(root.findall(".//objects/item/value/Object/items/Item"))
    )
    for item in all_item_els:
        name_el  = item.find("name")
        stack_el = item.find("Stack") or item.find("stack")
        if name_el is not None and name_el.text:
            name  = name_el.text
            count = int(stack_el.text or 0) if stack_el is not None else 1
            if count > 0 and name in HOARD_ITEM_MAP:
                hoard_have.add(HOARD_ITEM_MAP[name])
    out["hoard_have"] = list(hoard_have)

    vault_map = {23:"vault_2500", 24:"vault_5000", 25:"vault_10000", 26:"vault_25000"}
    hoard_done = set()
    for bundle_el in root.findall(".//bundles/item"):
        key_el  = bundle_el.find("key/int")
        val_els = bundle_el.findall("value/ArrayOfBoolean/boolean")
        if key_el is None: continue
        bundle_id = int(key_el.text or -1)
        if not val_els: continue
        all_done = all(v.text == 'true' for v in val_els)
        if all_done and bundle_id in CC_BUNDLE_MAP:
            for hid in CC_BUNDLE_MAP[bundle_id]:
                hoard_done.add(hid)
        if bundle_id in vault_map and all_done:
            hoard_done.add(vault_map[bundle_id])
    out["hoard_done"] = list(hoard_done)

    mail = set()
    for m in root.findall(".//player/mailReceived/string"):
        if m.text: mail.add(m.text)
    out["mail"] = list(mail)

    events = set()
    for e in root.findall(".//player/eventsSeen/int"):
        try:
            if e.text: events.add(int(e.text))
        except ValueError:
            pass
    out["events"] = list(events)

    total_money_el = root.find(".//player/totalMoneyEarned")
    out["totalMoneyEarned"] = int(total_money_el.text or 0) if total_money_el is not None else 0

    stats = {}
    stats_el = root.find(".//player/stats")
    if stats_el is not None:
        for child in stats_el:
            try: stats[child.tag] = int(child.text or 0)
            except: pass
    out["stats"] = stats

    completed_quests = set()
    for q in root.findall(".//player/questLog/Quest"):
        completed_el = q.find("completed")
        id_el = q.find("id") if q.find("id") is not None else q.find("questID")
        if completed_el is not None and completed_el.text == 'true' and id_el is not None:
            completed_quests.add(int(id_el.text or 0))
    out["completedQuests"] = list(completed_quests)

    donated = 0
    for item in root.findall(".//locations/GameLocation/museumPieces/item"):
        donated += 1
    out["museumDonations"] = donated

    # Active quests currently in questLog
    active_quests = []
    for q in root.findall(".//player/questLog/Quest"):
        id_el = q.find("id") if q.find("id") is not None else q.find("questID")
        title_el = q.find("questTitle") or q.find("title")
        completed_el = q.find("completed")
        if title_el is not None and title_el.text:
            active_quests.append({
                "id": int(id_el.text or 0) if id_el is not None else 0,
                "title": title_el.text,
                "done": completed_el is not None and completed_el.text == "true"
            })
    out["activeQuests"] = active_quests

    # Tool upgrade levels: 0=Basic 1=Copper 2=Iron 3=Gold 4=Iridium
    tool_levels = {}
    for item in root.findall(".//player/items/Item"):
        name_el = item.find("name")
        upgrade_el = item.find("upgradeLevel")
        if name_el is not None and name_el.text and upgrade_el is not None:
            n = name_el.text
            if n in ("Pickaxe", "Axe", "Hoe", "Watering Can"):
                tool_levels[n] = int(upgrade_el.text or 0)
    out["toolLevels"] = tool_levels

    house_el = root.find(".//player/houseUpgradeLevel")
    out["houseUpgradeLevel"] = int(house_el.text or 0) if house_el is not None else 0

    spouse_el = root.find(".//player/spouse")
    out["spouse"] = spouse_el.text.strip() if spouse_el is not None and spouse_el.text else None

    buildings = []
    for b in root.findall(".//locations/GameLocation/buildings/Building"):
        t = b.find("buildingType") if b.find("buildingType") is not None else b.find("name")
        if t is not None and t.text:
            buildings.append(t.text)
    out["buildings"] = buildings

    hearts8plus = 0
    for entry in root.findall(".//friendships/item"):
        pts_el = entry.find("value/Friendship/Points")
        if pts_el is not None:
            if int(pts_el.text or 0) >= 2000:
                hearts8plus += 1
    out["npcsAt8Hearts"] = hearts8plus

    # ── CC BUNDLES (structured for Junimo Feed) ──────────────────────────────
    bundle_done = {}
    for bundle_el in root.findall(".//bundles/item"):
        key_el  = bundle_el.find("key/int")
        val_els = bundle_el.findall("value/ArrayOfBoolean/boolean")
        if key_el is None or not val_els: continue
        bid = int(key_el.text or -1)
        bundle_done[bid] = all(v.text == 'true' for v in val_els)

    hoard_have_set = set(out["hoard_have"])
    room_map = {r: {"name": r, "emoji": ROOM_EMOJI[r], "bundles": [], "done": 0} for r in ROOM_ORDER}

    for bid in sorted(BUNDLE_ROOMS.keys()):
        room = BUNDLE_ROOMS[bid]
        completed = bundle_done.get(bid, False)
        items = CC_BUNDLE_MAP.get(bid, [])
        # Vault bundles: show gold amount as a single slot
        if not items and bid in vault_map:
            amt = {23:2500, 24:5000, 25:10000, 26:25000}[bid]
            items = [vault_map[bid]]
        slots = [{"code": c, "name": HOARD_CODE_NAMES.get(c, c), "have": c in hoard_have_set}
                 for c in items]
        room_map[room]["bundles"].append({
            "id": bid, "name": BUNDLE_NAMES.get(bid, f"Bundle {bid}"),
            "completed": completed, "slots": slots,
        })
        if completed:
            room_map[room]["done"] += 1

    out["cc_bundles"] = [room_map[r] for r in ROOM_ORDER]

    # ── FULL BACKPACK ─────────────────────────────────────────────────────────
    backpack = []
    for item in root.findall(".//player/items/Item"):
        n_el = item.find("name")
        s_el = item.find("Stack") or item.find("stack")
        q_el = item.find("quality")
        if n_el is None or not n_el.text or n_el.text in ("null", "Empty", "(Empty)"):
            continue
        count = int(s_el.text or 1) if s_el is not None else 1
        if count <= 0:
            continue
        backpack.append({
            "name": n_el.text,
            "count": count,
            "quality": int(q_el.text or 0) if q_el is not None else 0,
        })
    out["backpack"] = backpack

    # ── SKILLS XP (raw values for progress bars) ──────────────────────────────
    xp_list = root.findall(".//player/experiencePoints/int")
    out["skillsXP"] = {SKILL_IDS[i]: int(xp_list[i].text or 0)
                       for i in range(min(5, len(xp_list)))}

    # ── PROFESSIONS ───────────────────────────────────────────────────────────
    profs = []
    for p in root.findall(".//player/professions/int"):
        try: profs.append(int(p.text))
        except: pass
    out["professions"] = profs

    # ── EQUIPMENT ─────────────────────────────────────────────────────────────
    def _item_name(path):
        el = root.find(path)
        n = el.find("name") if el is not None else None
        return n.text if n is not None else None

    out["equipment"] = {
        "hat":       _item_name(".//player/hat/Hat"),
        "boots":     _item_name(".//player/boots/Boots"),
        "leftRing":  _item_name(".//player/leftRing/Ring"),
        "rightRing": _item_name(".//player/rightRing/Ring"),
        "shirt":     _item_name(".//player/shirtItem/Clothing"),
        "pants":     _item_name(".//player/pantsItem/Clothing"),
    }

    # ── APPEARANCE ────────────────────────────────────────────────────────────
    appear = {}
    for field in ("hair", "skin", "shoeColor"):
        el = root.find(f".//player/{field}")
        if el is not None and el.text:
            appear[field] = el.text
    out["appearance"] = appear

    # ── RECIPES ───────────────────────────────────────────────────────────────
    cooking = []
    for item in root.findall(".//player/cookingRecipes/item"):
        k = item.find("key/string")
        if k is not None and k.text: cooking.append(k.text)
    out["cookingRecipes"] = cooking

    crafting = []
    for item in root.findall(".//player/craftingRecipes/item"):
        k = item.find("key/string")
        if k is not None and k.text: crafting.append(k.text)
    out["craftingRecipes"] = crafting

    # ── SPECIAL FLAGS ─────────────────────────────────────────────────────────
    for flag in ("hasSkullKey", "hasClubCard", "hasDarkTalisman", "hasMagicInk",
                 "hasMagnifyingGlass", "hasRustyKey", "canUnderstandDwarves",
                 "hasGaloshes", "hasSpecialCharm", "catPerson"):
        el = root.find(f".//player/{flag}")
        out[flag] = (el is not None and el.text == "true")
    cave_el = root.find(".//player/caveChoice")
    out["caveChoice"] = int(cave_el.text or 0) if cave_el is not None else 0

    # ── ANIMALS ───────────────────────────────────────────────────────────────
    animals = []
    for b in root.findall(".//locations/GameLocation/buildings/Building"):
        bt = b.find("buildingType") or b.find("name")
        bname = bt.text if bt is not None else "Building"
        for a in b.findall(".//indoors/characters/FarmAnimal"):
            a_name = a.find("name")
            a_type = a.find("type")
            a_friend = a.find("friendshipTowardFarmer")
            animals.append({
                "name": a_name.text if a_name is not None else "?",
                "type": a_type.text if a_type is not None else "Animal",
                "building": bname,
                "friendship": int(a_friend.text or 0) if a_friend is not None else 0,
            })
    out["animals"] = animals

    # ── PETS ──────────────────────────────────────────────────────────────────
    pets = []
    _ns = "http://www.w3.org/2001/XMLSchema-instance"
    for char in root.findall(".//locations/GameLocation/characters/NPC"):
        char_type = char.get(f"{{{_ns}}}type", "")
        if char_type in ("Dog", "Cat"):
            cn = char.find("name")
            cf = char.find("friendshipTowardFarmer")
            pets.append({
                "name": cn.text if cn is not None else "Pet",
                "type": char_type,
                "friendship": int(cf.text or 0) if cf is not None else 0,
            })
    out["pets"] = pets

    return out


def xp_to_level(xp):
    thresholds = [0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]
    level = 0
    for i, t in enumerate(thresholds):
        if xp >= t: level = i
    return level


def watch_loop():
    global latest_data, last_modified
    print(f"[bridge] Watching: {SAVE_PATH}")
    print(f"[bridge] Serving on https://localhost:{PORT}/save")
    while True:
        try:
            mtime = os.path.getmtime(SAVE_PATH)
            if mtime != last_modified:
                last_modified = mtime
                latest_data = parse_save()
                ts = datetime.now().strftime("%H:%M:%S")
                gold = latest_data.get("gold", 0)
                day  = latest_data.get("day", "?")
                season = latest_data.get("season", "?")
                print(f"[bridge] {ts} — {season} {day} | {gold:,}g")
        except FileNotFoundError:
            latest_data = {"error": "Save file not found. Is Stardew running?"}
        except Exception as e:
            latest_data = {"error": str(e)}
        time.sleep(POLL_INTERVAL)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_GET(self):
        if self.path == "/save":
            body = json.dumps(latest_data, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/cert":
            import base64, uuid
            with open(CERT_FILE, 'rb') as f:
                cert_pem = f.read()
            cert_b64_lines = [l for l in cert_pem.decode().splitlines()
                              if not l.startswith('-----')]
            cert_b64 = ''.join(cert_b64_lines)
            profile_uuid = str(uuid.uuid4()).upper()
            payload_uuid = str(uuid.uuid4()).upper()
            mobileconfig = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadCertificateFileName</key>
            <string>stardew-bridge.cer</string>
            <key>PayloadContent</key>
            <data>{cert_b64}</data>
            <key>PayloadDescription</key>
            <string>Trusts the Stardew Bridge local server certificate</string>
            <key>PayloadDisplayName</key>
            <string>Stardew Bridge CA</string>
            <key>PayloadIdentifier</key>
            <string>com.hoedownfarms.stardew.bridge.cert</string>
            <key>PayloadType</key>
            <string>com.apple.security.root</string>
            <key>PayloadUUID</key>
            <string>{payload_uuid}</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>Allows your iPhone to connect to the Stardew Bridge on your Mac</string>
    <key>PayloadDisplayName</key>
    <string>Stardew Bridge</string>
    <key>PayloadIdentifier</key>
    <string>com.hoedownfarms.stardew.bridge</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>{profile_uuid}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>"""
            body = mobileconfig.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/x-apple-aspen-config")
            self.send_header("Content-Disposition", "attachment; filename=stardew-bridge.mobileconfig")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            # Serve static files from the project directory
            import mimetypes
            req = self.path.split('?')[0]
            if req == '/':
                req = '/index.html'
            file_path = os.path.join(_BRIDGE_DIR, req.lstrip('/'))
            if os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                with open(file_path, 'rb') as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("[bridge] Generating self-signed certificate...")
        try:
            import socket, subprocess
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import ipaddress

            # Collect every IP and hostname this Mac answers to
            san_ips, san_dns = set(), {'localhost'}
            san_ips.add(ipaddress.IPv4Address('127.0.0.1'))
            try:
                # All network interface IPs
                import subprocess, re
                out = subprocess.check_output(['ifconfig'], text=True)
                for m in re.finditer(r'inet (\d+\.\d+\.\d+\.\d+)', out):
                    ip = m.group(1)
                    if ip != '127.0.0.1':
                        san_ips.add(ipaddress.IPv4Address(ip))
            except Exception:
                pass
            try:
                ts_out = subprocess.check_output(['tailscale', 'status', '--json'], text=True)
                import json as _j
                ts = _j.loads(ts_out)
                self_node = ts.get('Self', {})
                for addr in self_node.get('TailscaleIPs', []):
                    try: san_ips.add(ipaddress.IPv4Address(addr))
                    except Exception: pass
                dns = self_node.get('DNSName', '').rstrip('.')
                if dns:
                    san_dns.add(dns)
                    # also add short hostname
                    san_dns.add(dns.split('.')[0])
            except Exception:
                pass
            # Always include the Tailscale FQDN from CERT_FILE name as fallback
            ts_host = os.path.basename(CERT_FILE).replace('.crt', '')
            if ts_host:
                san_dns.add(ts_host)

            san_entries = [x509.IPAddress(ip) for ip in san_ips]
            san_entries += [x509.DNSName(d) for d in san_dns]

            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Stardew Bridge")])
            cert = (
                x509.CertificateBuilder()
                .subject_name(name)
                .issuer_name(name)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.now(timezone.utc))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
                .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
                .sign(key, hashes.SHA256())
            )
            with open(KEY_FILE, 'wb') as f:
                f.write(key.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()))
            with open(CERT_FILE, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            print(f"[bridge] Certificate SANs: IPs={[str(i) for i in san_ips]} DNS={san_dns}")
            print(f"[bridge] Certificate saved to {CERT_FILE}")
            # Announce cert download URL for every IP
            for ip in san_ips:
                s = str(ip)
                if not s.startswith('127'):
                    print(f"[bridge] Install cert on iPhone: http://{s}:8743/cert")
        except ImportError:
            print("[bridge] cryptography not installed. Run: pip3 install cryptography")
            exit(1)

    if os.path.exists(SAVE_PATH):
        latest_data = parse_save()
    else:
        latest_data = {"error": "Save file not found yet."}

    t = threading.Thread(target=watch_loop, daemon=True)
    t.start()

    try:
        http_server = http.server.HTTPServer(("0.0.0.0", 8743), Handler)
        http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
        http_thread.start()
        print(f"[bridge] Cert download (HTTP): http://10.0.0.70:8743/cert")
    except OSError:
        print("[bridge] Port 8743 in use — cert download server skipped")

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"[bridge] HTTPS server running on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[bridge] Stopped.")
