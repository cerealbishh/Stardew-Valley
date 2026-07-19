#!/usr/bin/env python3
"""
stardew-bridge.py — Hoe Down Farms Live Sync
Watches your Stardew save file and serves parsed data to the tracker on your iPhone.
"""

import base64
import http.server
import json
import os
import platform
import threading
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime


def find_save_path():
    """Auto-detect the Stardew Valley save file for this OS.

    Picks the most-recently-modified save if more than one exists, since
    that's almost always the one actively being played. Set SDV_SAVE_PATH
    to override (useful if auto-detection picks the wrong save/location).
    """
    override = os.environ.get("SDV_SAVE_PATH")
    if override:
        return override

    home = os.path.expanduser("~")
    system = platform.system()
    candidates = []
    if system == "Windows":
        appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        candidates.append(os.path.join(appdata, "StardewValley", "Saves"))
    elif system == "Darwin":
        candidates.append(os.path.join(home, ".config", "StardewValley", "Saves"))
        candidates.append(os.path.join(home, "Library", "Application Support", "StardewValley", "Saves"))
    else:
        candidates.append(os.path.join(home, ".config", "StardewValley", "Saves"))

    best_path, best_mtime = None, -1
    for saves_dir in candidates:
        if not os.path.isdir(saves_dir):
            continue
        try:
            entries = os.listdir(saves_dir)
        except OSError:
            continue
        for entry in entries:
            save_file = os.path.join(saves_dir, entry, entry)
            if os.path.isfile(save_file):
                mtime = os.path.getmtime(save_file)
                if mtime > best_mtime:
                    best_mtime, best_path = mtime, save_file
    return best_path


SAVE_PATH = find_save_path()
PORT = 8742
POLL_INTERVAL = 5
_BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── GitHub Gist relay ──────────────────────────────────────────────────────────
# Option A (recommended): set env vars before running:
#   export SDV_GIST_TOKEN=ghp_...
#   export SDV_GIST_ID=<gist-id>
# Option B: create bridge-secrets.py next to this file with:
#   GIST_TOKEN = "ghp_..."
#   GIST_ID    = "..."
#   (bridge-secrets.py is gitignored)
try:
    from bridge_secrets import GIST_TOKEN, GIST_ID  # type: ignore
except ImportError:
    GIST_TOKEN = os.environ.get("SDV_GIST_TOKEN", "")
    GIST_ID    = os.environ.get("SDV_GIST_ID", "")

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
    "Large Goat Milk": "hard_goatmilk", "Cheese": "any_cheese",
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
    # Home Cook bundle (bundle 36, 1.6)
    "Tom Kha Soup": "hc_tomkha", "Blackberry Cobbler": "hc_blackberrycobbler",
    "Fish Taco": "hc_fishtaco", "Omelet": "hc_omelet",
    "Fried Eel": "hc_friedeel", "Cranberry Sauce": "hc_cranberrysauce",
    # Artisan extras
    "Cherry": "hc_cherry", "Apricot": "hc_apricot", "Orange": "hc_orange",
}

CC_BUNDLE_MAP = {
    # ── PANTRY ──────────────────────────────────────────────────────────────
    0:  ["sp_parsnip","sp_greenbean","sp_cauliflower","sp_potato"],     # Spring Crops
    1:  ["su_tomato","su_hotpepper","su_blueberry","su_melon"],         # Summer Crops
    2:  ["su_corn","fa_eggplant","fa_pumpkin","fa_yam"],                # Fall Crops
    3:  ["sp_parsnip","su_melon","fa_pumpkin","su_corn"],               # Quality Crops (⚠ gold quality not tracked)
    4:  ["hard_largeeggw","hard_largemilk","hard_largeeggb",            # Animal
         "hard_goatmilk","hard_wool","hard_duckegg"],
    5:  ["truffle_oil","any_cloth","any_goatcheese","any_cheese",       # Artisan (need 6 of listed)
         "any_honey","any_jelly","fa_apple","fa_pomegranate",
         "hc_cherry","hc_apricot","hc_orange","q_sweetgemberry"],
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
    36: ["hc_tomkha","hc_blackberrycobbler","hc_fishtaco",             # Home Cook (need 3 of 6)
         "hc_omelet","hc_friedeel","hc_cranberrysauce"],
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
    31:"Chef's", 32:"Field Research", 33:"Enchanter's", 34:"Dye", 35:"Fodder", 36:"Home Cook",
}
BUNDLE_ROOMS = {
    0:"Pantry",1:"Pantry",2:"Pantry",3:"Pantry",4:"Pantry",5:"Pantry",
    6:"Fish Tank",7:"Fish Tank",8:"Fish Tank",9:"Fish Tank",10:"Fish Tank",11:"Fish Tank",
    13:"Crafts Room",14:"Crafts Room",15:"Crafts Room",16:"Crafts Room",17:"Crafts Room",19:"Crafts Room",
    20:"Boiler Room",21:"Boiler Room",22:"Boiler Room",
    23:"Vault",24:"Vault",25:"Vault",26:"Vault",
    31:"Bulletin Board",32:"Bulletin Board",33:"Bulletin Board",34:"Bulletin Board",35:"Bulletin Board",36:"Bulletin Board",
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
    "fa_walleye":"Walleye","wi_squid":"Squid",
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
    # Artisan extras (1.6)
    "hc_cherry":"Cherry","hc_apricot":"Apricot","hc_orange":"Orange",
    # Home Cook bundle (bundle 36, 1.6)
    "hc_tomkha":"Tom Kha Soup","hc_blackberrycobbler":"Blackberry Cobbler",
    "hc_fishtaco":"Fish Taco","hc_omelet":"Omelet",
    "hc_friedeel":"Fried Eel","hc_cranberrysauce":"Cranberry Sauce",
}


def find_any(el, *tags):
    """el.find(a) or el.find(b) is broken: ElementTree elements with no child
    elements (any plain <tag>text</tag> leaf) are falsy regardless of being
    found, so `or` silently discards a real match and moves to the next tag.
    Confirmed live bug: quest <id> leaves were being discarded this way."""
    for t in tags:
        found = el.find(t)
        if found is not None:
            return found
    return None


def parse_bundle_string(raw):
    """Decode one bundleData value string into structured data.

    Real format (confirmed against a live save, both vanilla and remixed
    bundles use the same shape): Name/Reward/Items/ColorIndex/MinRequired//DisplayName
    e.g. "Spring Crops/O 465 20/24 1 0 188 1 0 190 1 0 192 1 0/0///Spring Crops"
    Item IDs are the game's numeric object IDs — resolving them to names
    happens client-side (a lookup table, since it's static reference data).
    """
    parts = raw.split("/")
    name = parts[0] if len(parts) > 0 else ""
    reward_tokens = parts[1].split() if len(parts) > 1 else []
    item_tokens = parts[2].split() if len(parts) > 2 else []
    color_index = int(parts[3]) if len(parts) > 3 and parts[3].lstrip('-').isdigit() else 0
    min_required_raw = parts[4] if len(parts) > 4 else ""
    display_name = parts[6] if len(parts) > 6 and parts[6] else name

    reward = None
    if len(reward_tokens) >= 3:
        reward = {"type": reward_tokens[0], "itemId": reward_tokens[1], "amount": int(reward_tokens[2])}

    items = []
    for i in range(0, len(item_tokens) - 2, 3):
        items.append({
            "itemId": item_tokens[i],
            "qty": int(item_tokens[i + 1]),
            "quality": int(item_tokens[i + 2]),
        })

    min_required = int(min_required_raw) if min_required_raw.isdigit() else len(items)

    return {
        "name": name,
        "displayName": display_name,
        "reward": reward,
        "items": items,
        "colorIndex": color_index,
        "minRequired": min_required,
    }


def parse_bundle_data(root):
    result = {}
    for item in root.findall(".//bundleData/item"):
        key_el = item.find("key/string")
        val_el = item.find("value/string")
        if key_el is not None and val_el is not None and key_el.text and val_el.text:
            result[key_el.text] = parse_bundle_string(val_el.text)
    return result


def push_to_gist(data):
    global GIST_ID
    if not GIST_TOKEN:
        return
    payload = json.dumps({
        "description": "Stardew Valley Live Save",
        "public": False,
        "files": {"sdv-save.json": {"content": json.dumps(data, separators=(',', ':'))}}
    }).encode('utf-8')
    url    = f"https://api.github.com/gists/{GIST_ID}" if GIST_ID else "https://api.github.com/gists"
    method = 'PATCH' if GIST_ID else 'POST'
    req = urllib.request.Request(url, data=payload, method=method)
    req.add_header("Authorization", f"Bearer {GIST_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "stardew-bridge/1.0")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if not GIST_ID:
                GIST_ID = result["id"]
                print(f"[bridge] Gist created!")
                print(f"[bridge]   Token:   {GIST_TOKEN}")
                print(f"[bridge]   Gist ID: {GIST_ID}")
                print(f"[bridge] Paste both into the app on your phone.")
    except urllib.error.HTTPError as e:
        print(f"[bridge] Gist push error {e.code}: {e.read().decode('utf-8','ignore')[:80]}")
    except Exception as e:
        print(f"[bridge] Gist push failed: {e}")


def create_gist(token):
    """One-shot gist creation for the setup wizard — separate from
    push_to_gist() because that function is designed for the silent
    background watch loop (swallows errors), whereas setup needs to show
    the user exactly what went wrong if their token doesn't work."""
    payload = json.dumps({
        "description": "Stardew Valley Live Save (The Grindset)",
        "public": False,
        "files": {"sdv-save.json": {"content": json.dumps({"schema_version": 1, "status": "waiting for first sync"})}},
    }).encode("utf-8")
    req = urllib.request.Request("https://api.github.com/gists", data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "stardew-bridge/1.0")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return True, result["id"]
    except urllib.error.HTTPError as e:
        return False, f"GitHub said: {e.code} — {e.read().decode('utf-8', 'ignore')[:200]}"
    except Exception as e:
        return False, str(e)


def generate_sync_code(token, gist_id):
    """Bundle the token+gist-id into one paste-able code. Note: this is
    necessarily longer than a short PIN — it's the actual credential pair,
    reversibly encoded, not a lookup key — because there's deliberately no
    server anywhere to look a short code up against.

    Grouped with SPACES every 4 characters for readability — NOT dashes:
    URL-safe base64's alphabet legitimately includes '-' (in place of '+'),
    so stripping dashes on decode would silently corrupt any code whose
    encoding happens to contain one. Confirmed real with a quick fuzz test.
    Space never appears in base64 output, so it's always safe to strip."""
    raw = f"{token}|{gist_id}".encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return " ".join(encoded[i:i + 4] for i in range(0, len(encoded), 4))


def decode_sync_code(code):
    raw = code.replace(" ", "")
    padded = raw + ("=" * (-len(raw) % 4))
    decoded = base64.urlsafe_b64decode(padded).decode("utf-8")
    token, gist_id = decoded.split("|", 1)
    return token, gist_id


def run_setup_wizard():
    """First-run interactive setup: get a GitHub token, create the user's
    private gist, save both for next time, and hand them a sync code to
    paste into the website. No account system, no shared server — every
    user's data lives in their own gist from here on."""
    global GIST_TOKEN, GIST_ID
    print()
    print("=" * 60)
    print("  Let's get your farm synced!")
    print("=" * 60)
    print()
    print("First, a free GitHub token — this keeps your farm data private,")
    print("just for you. No password or account needed beyond this.")
    print()
    print("1. Open this link:")
    print("   https://github.com/settings/tokens/new?scopes=gist&description=Stardew+Bridge")
    print("2. Click the green 'Generate token' button at the bottom.")
    print("3. Copy the token it shows you (starts with 'ghp_').")
    print()
    token = input("Paste your token here, then press Enter: ").strip()
    if not token:
        print("\n[bridge] No token entered — run this again whenever you're ready.")
        return False

    print("\nCreating your private farm storage...")
    ok, result = create_gist(token)
    if not ok:
        print(f"\n[bridge] Something went wrong: {result}")
        print("[bridge] Double-check you copied the whole token, then run this again.")
        return False

    gist_id = result
    GIST_TOKEN, GIST_ID = token, gist_id

    try:
        secrets_path = os.path.join(_BRIDGE_DIR, "bridge_secrets.py")
        with open(secrets_path, "w") as f:
            f.write(f'GIST_TOKEN = "{token}"\nGIST_ID    = "{gist_id}"\n')
    except OSError as e:
        print(f"[bridge] Couldn't save your setup for next time: {e}")
        print("[bridge] You'll need to paste your token again next time you run this.")

    print_sync_code(token, gist_id, first_time=True)
    return True


def print_sync_code(token, gist_id, first_time=False):
    code = generate_sync_code(token, gist_id)
    print()
    print("=" * 60)
    print("  You're all set!" if first_time else "  Your sync code")
    print("=" * 60)
    print()
    print("Your sync code:")
    print()
    print(f"  {code}")
    print()
    print("Copy that, then open The Grindset on your phone, tap Log In,")
    print("and paste it in. That's the whole setup" + (" — you won't need to do this again." if first_time else "."))
    print()


def parse_save():
    try:
        tree = ET.parse(SAVE_PATH)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse save: {e}"}

    out = {
        "schema_version": 1,
        "farm": "My Farm",
        "seed": None,
        "updated": datetime.now().strftime("%H:%M:%S"),
        "generated_at": int(time.time()),
        "gold": 0, "season": "spring", "day": 1, "year": 1,
        "isRaining": False, "isSnowing": False, "isLightning": False,
        "isDebrisWeather": False, "dailyLuck": 0.0, "weatherTomorrow": "Sun",
        "skills": {}, "friendship": {}, "inventory": {}, "chest_ore": {},
        "hoard_have": [], "hoard_done": [],
    }

    money = root.find(".//player/money")
    if money is not None: out["gold"] = int(money.text or 0)

    farm_name_el = root.find(".//farmName")
    if farm_name_el is not None and farm_name_el.text:
        out["farm"] = farm_name_el.text

    seed_el = root.find(".//uniqueIDForThisGame")
    if seed_el is not None and seed_el.text:
        out["seed"] = int(seed_el.text)

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

    def parse_date_node(el):
        """Friendship dates are {Year, Season, DayOfMonth} structs, not a single int."""
        if el is None:
            return None
        y, s, d = el.find("Year"), el.find("Season"), el.find("DayOfMonth")
        if y is None or s is None or d is None:
            return None
        return {"year": int(y.text or 1), "season": (s.text or "spring").lower(), "day": int(d.text or 1)}

    # SV 1.6: friendship data moved from .//friendships to player/friendshipData
    _frnd_paths = [".//player/friendshipData/item", ".//friendships/item"]
    for path in _frnd_paths:
        for entry in root.findall(path):
            key_el = entry.find("key/string")
            pts_el = entry.find("value/Friendship/Points")
            gifts_el = entry.find("value/Friendship/GiftsThisWeek")
            last_gift_el = entry.find("value/Friendship/LastGiftDate")
            talked_el = entry.find("value/Friendship/TalkedToToday")
            wedding_el = entry.find("value/Friendship/WeddingDate")
            status_el = entry.find("value/Friendship/Status")
            if key_el is not None and pts_el is not None:
                name = key_el.text
                if name in FRIENDSHIP_NPCS:
                    nk = name.lower()
                    out["friendship"][nk] = int(pts_el.text or 0)
                    if gifts_el is not None:
                        out.setdefault("giftsThisWeek", {})[nk] = int(gifts_el.text or 0)
                    last_gift = parse_date_node(last_gift_el)
                    if last_gift:
                        out.setdefault("lastGiftDate", {})[nk] = last_gift
                    if talked_el is not None:
                        out.setdefault("talkedToToday", {})[nk] = (talked_el.text == "true")
                    wedding = parse_date_node(wedding_el)
                    if wedding:
                        out.setdefault("weddingDate", {})[nk] = wedding
                    if status_el is not None and status_el.text:
                        out.setdefault("relationshipStatus", {})[nk] = status_el.text

    gifted_items = {}
    for entry in root.findall(".//player/giftedItems/item"):
        npc_key_el = entry.find("key/string")
        if npc_key_el is None or not npc_key_el.text or npc_key_el.text not in FRIENDSHIP_NPCS:
            continue
        nk = npc_key_el.text.lower()
        per_item = {}
        for gift_entry in entry.findall("value/dictionary/item"):
            item_id_el = gift_entry.find("key/string")
            times_el = gift_entry.find("value/int")
            if item_id_el is not None and times_el is not None and item_id_el.text:
                per_item[item_id_el.text] = int(times_el.text or 0)
        if per_item:
            gifted_items[nk] = per_item
    out["giftedItems"] = gifted_items

    # Real, per-save resolved CC bundle contents — works for vanilla AND
    # remixed bundles alike, so this replaces CC_BUNDLE_MAP as the source of
    # truth for "what does this bundle actually want" (CC_BUNDLE_MAP is kept
    # only as a fallback/reference, since it's confirmed wrong for at least
    # one bundle on this exact save: bundleData says bundle 36 is "Abandoned
    # Joja Mart: The Missing," not the hardcoded "Home Cook").
    out["bundleData"] = parse_bundle_data(root)

    inv_counts = {}
    for item in root.findall(".//player/items/Item"):
        name_el  = item.find("name")
        stack_el = find_any(item, "Stack", "stack")
        if name_el is not None and name_el.text and stack_el is not None:
            n = name_el.text.replace(" ", "")
            count = int(stack_el.text or 0)
            if n in TRACKED_ITEMS and count > 0:
                key = TRACKED_ITEMS[n]
                inv_counts[key] = inv_counts.get(key, 0) + count

    chest_ore = {"copper": 0, "iron": 0, "gold": 0, "coal": 0}
    for item in root.findall(".//objects/item/value/Object/items/Item"):
        name_el  = item.find("name")
        stack_el = find_any(item, "Stack", "stack")
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

    # ── CHESTS (full contents, grouped by location, no item allowlist) ─────────
    # The above inv_counts/chest_ore logic (an allowlisted subset, location
    # discarded) stays untouched for backward compat — this is a separate,
    # additive, complete view for Davy Jones' Locker's per-location browser.
    chests_by_location = {}
    for loc in root.findall(".//locations/GameLocation"):
        loc_name_el = loc.find("name")
        loc_name = loc_name_el.text if loc_name_el is not None and loc_name_el.text else "Unknown"
        for obj_item in loc.findall("objects/item"):
            chest_items = obj_item.findall("value/Object/items/Item")
            if not chest_items:
                continue
            chest_name_el = obj_item.find("value/Object/name")
            chest_name = chest_name_el.text if chest_name_el is not None and chest_name_el.text else "Chest"
            x_el, y_el = obj_item.find("key/Vector2/X"), obj_item.find("key/Vector2/Y")
            tile = [int(x_el.text), int(y_el.text)] if x_el is not None and y_el is not None else None
            items_list = []
            for it in chest_items:
                n = it.find("name")
                s = find_any(it, "Stack", "stack")
                q = it.find("quality")
                if n is not None and n.text:
                    items_list.append({
                        "name": n.text,
                        "count": int(s.text or 1) if s is not None else 1,
                        "quality": int(q.text or 0) if q is not None else 0,
                    })
            if items_list:
                chests_by_location.setdefault(loc_name, []).append({
                    "chestName": chest_name, "tile": tile, "items": items_list,
                })
    out["chests"] = chests_by_location

    hoard_have = set()
    storage = {}
    all_item_els = (
        list(root.findall(".//player/items/Item")) +
        list(root.findall(".//objects/item/value/Object/items/Item"))
    )
    for item in all_item_els:
        name_el  = item.find("name")
        stack_el = find_any(item, "Stack", "stack")
        if name_el is not None and name_el.text:
            name  = name_el.text
            count = int(stack_el.text or 0) if stack_el is not None else 1
            if count > 0 and name in HOARD_ITEM_MAP:
                code = HOARD_ITEM_MAP[name]
                hoard_have.add(code)
                storage[code] = storage.get(code, 0) + count
    out["hoard_have"] = list(hoard_have)
    out["storage"] = storage

    vault_map = {23:"vault_2500", 24:"vault_5000", 25:"vault_10000", 26:"vault_25000"}
    # Pre-parse bundleRewards for hoard_done (accurate for partial-donation bundles)
    bundle_rewards_done = {}
    for item in root.findall(".//bundleRewards/item"):
        k = item.find("key/int")
        v = item.find("value/boolean")
        if k is not None and v is not None:
            bundle_rewards_done[int(k.text or -1)] = (v.text == 'true')
    hoard_done = set()
    for bundle_id, hids in CC_BUNDLE_MAP.items():
        if bundle_rewards_done.get(bundle_id, False):
            for hid in hids:
                hoard_done.add(hid)
    for bid, vk in vault_map.items():
        if bundle_rewards_done.get(bid, False):
            hoard_done.add(vk)
    out["hoard_done"] = list(hoard_done)

    mail = set()
    for m in root.findall(".//player/mailReceived/string"):
        if m.text: mail.add(m.text)
    out["mail"] = list(mail)

    events = set()
    event_flags = set()  # non-numeric entries (e.g. "festival_summer11") — proves real attendance, not just date-passed
    for e in root.findall(".//player/eventsSeen/int"):
        if not e.text:
            continue
        try:
            events.add(int(e.text))
        except ValueError:
            event_flags.add(e.text)
    out["events"] = list(events)
    out["eventFlags"] = list(event_flags)

    total_money_el = root.find(".//player/totalMoneyEarned")
    out["totalMoneyEarned"] = int(total_money_el.text or 0) if total_money_el is not None else 0

    # SV 1.6 stores the real numeric stats in a nested Values dict — the direct
    # children of <stats> (daysPlayed, monstersKilled, etc.) are empty placeholders.
    stats = {}
    stats_el = root.find(".//player/stats")
    if stats_el is not None:
        values_el = stats_el.find("Values")
        if values_el is not None:
            for item in values_el.findall("item"):
                k = item.find("key/string")
                v = item.find("value")
                if k is not None and k.text and v is not None and len(v):
                    try: stats[k.text] = int(v[0].text or 0)
                    except (TypeError, ValueError): pass

    specific_monsters = {}
    sm_el = stats_el.find("specificMonstersKilled") if stats_el is not None else None
    if sm_el is not None:
        for item in sm_el.findall("item"):
            k = item.find("key/string")
            v = item.find("value/int")
            if k is not None and k.text and v is not None:
                try: specific_monsters[k.text] = int(v.text or 0)
                except (TypeError, ValueError): pass

    out["stats"] = stats
    out["specificMonstersKilled"] = specific_monsters

    # ── COLLECTIONS (fish/artifacts/minerals actually found — for the Holocron) ──
    fish_caught = {}
    for item in root.findall(".//player/fishCaught/item"):
        k = item.find("key/string")
        vals = item.findall("value/ArrayOfInt/int")
        if k is not None and k.text and len(vals) >= 2:
            fish_caught[k.text] = {"count": int(vals[0].text or 0), "maxSize": int(vals[1].text or 0)}
    out["fishCaught"] = fish_caught

    artifacts_found = {}
    for item in root.findall(".//player/archaeologyFound/item"):
        k = item.find("key/string")
        vals = item.findall("value/ArrayOfInt/int")
        if k is not None and k.text and vals:
            artifacts_found[k.text] = int(vals[0].text or 0)
    out["archaeologyFound"] = artifacts_found

    minerals_found = {}
    for item in root.findall(".//player/mineralsFound/item"):
        k = item.find("key/string")
        v = item.find("value/int")
        if k is not None and k.text and v is not None:
            minerals_found[k.text] = int(v.text or 0)
    out["mineralsFound"] = minerals_found

    # ── MISC FIELDS (achievements, secret notes, locations, songs, recipes cooked) ──
    out["achievements"] = [int(e.text) for e in root.findall(".//player/achievements/int") if e.text]
    out["secretNotesSeen"] = [int(e.text) for e in root.findall(".//player/secretNotesSeen/int") if e.text]
    out["locationsVisited"] = [e.text for e in root.findall(".//player/locationsVisited/string") if e.text]
    out["songsHeard"] = [e.text for e in root.findall(".//player/songsHeard/string") if e.text]

    recipes_cooked = {}
    for item in root.findall(".//player/recipesCooked/item"):
        k = item.find("key/string")
        v = item.find("value/int")
        if k is not None and k.text and v is not None:
            recipes_cooked[k.text] = int(v.text or 0)
    out["recipesCooked"] = recipes_cooked

    completed_quests = set()
    for q in root.findall(".//player/questLog/Quest"):
        completed_el = q.find("completed")
        id_el = q.find("id") if q.find("id") is not None else q.find("questID")
        if completed_el is not None and completed_el.text == 'true' and id_el is not None:
            completed_quests.add(int(id_el.text or 0))
    out["completedQuests"] = list(completed_quests)

    # museumPieces is keyed by tile position -> donated item ID; count() alone
    # discards *which* items were donated, which the Museum tab needs to break
    # artifacts vs minerals apart (item-ID->name resolution happens client-side).
    museum_item_ids = []
    for item in root.findall(".//locations/GameLocation/museumPieces/item"):
        val_el = item.find("value/string")
        if val_el is not None and val_el.text:
            museum_item_ids.append(val_el.text)
    out["museumDonations"] = len(museum_item_ids)
    out["museumItemIds"] = museum_item_ids

    # Active quests currently in questLog (journal + Help Wanted board)
    active_quests = []
    for q in root.findall(".//player/questLog/Quest"):
        id_el      = find_any(q, "id", "questID")
        # Help Wanted quests store title in _questTitle; story quests use questTitle/title
        title_el   = find_any(q, "questTitle", "title", "_questTitle")
        obj_el     = q.find("_currentObjective")
        completed_el = q.find("completed")
        daily_el   = q.find("dailyQuest")
        days_el    = q.find("daysLeft")
        reward_el  = q.find("moneyReward")
        item_el    = q.find("itemIndex")
        req_el     = find_any(q, "requester", "target")
        number_el  = q.find("number")

        if title_el is None or not title_el.text:
            continue

        active_quests.append({
            "id":        int(id_el.text or 0) if id_el is not None else 0,
            "title":     title_el.text,
            "objective": obj_el.text if obj_el is not None else None,
            "done":      completed_el is not None and completed_el.text == "true",
            "daily":     daily_el is not None and daily_el.text == "true",
            "daysLeft":  int(days_el.text or 0) if days_el is not None else None,
            "reward":    int(reward_el.text or 0) if reward_el is not None else 0,
            "item":      item_el.text if item_el is not None else None,
            "requester": req_el.text if req_el is not None else None,
            "number":    int(number_el.text or 1) if number_el is not None else 1,
        })
    out["activeQuests"] = active_quests

    # Special Orders (Pierre's board + Qi's board) — stored separately from questLog
    special_orders = []
    for so in root.findall(".//specialOrders/SpecialOrder"):
        key_el = so.find("questKey")
        name_el = find_any(so, "questName", "questTitle")
        due_el = so.find("dueDate")
        done_el = so.find("readyForRemoval")
        obj_descs = []
        for obj in so.findall(".//objectives/SpecialOrderObjective"):
            desc_el = obj.find("description")
            cur_el = obj.find("currentCount")
            max_el = find_any(obj, "maxCount", "requiredCount")
            if desc_el is not None and desc_el.text:
                cur = int(cur_el.text or 0) if cur_el is not None else 0
                req = int(max_el.text or 0) if max_el is not None else 0
                obj_descs.append({"desc": desc_el.text, "current": cur, "required": req})
        special_orders.append({
            "key": key_el.text if key_el is not None else "",
            "title": name_el.text if name_el is not None else (key_el.text if key_el is not None else "Special Order"),
            "dueDate": int(due_el.text or -1) if due_el is not None else -1,
            "done": done_el is not None and done_el.text == "true",
            "objectives": obj_descs,
        })
    # Completed special order keys
    completed_so = [s.text for s in root.findall(".//specialOrdersCompleted/string") if s.text]
    out["specialOrders"] = special_orders
    out["completedSpecialOrders"] = completed_so

    # Tool upgrade levels: 0=Basic 1=Copper 2=Iron 3=Gold 4=Iridium
    # Scan both player inventory and chests (players often store tools in a chest)
    tool_levels = {}
    _tool_paths = [".//player/items/Item", ".//objects/item/value/Object/items/Item"]
    for path in _tool_paths:
        for item in root.findall(path):
            name_el = item.find("name")
            upgrade_el = item.find("upgradeLevel")
            if name_el is not None and name_el.text and upgrade_el is not None:
                n = name_el.text
                if n in ("Pickaxe", "Axe", "Hoe", "Watering Can"):
                    lvl = int(upgrade_el.text or 0)
                    tool_levels[n] = max(tool_levels.get(n, 0), lvl)
    out["toolLevels"] = tool_levels

    house_el = root.find(".//player/houseUpgradeLevel")
    out["houseUpgradeLevel"] = int(house_el.text or 0) if house_el is not None else 0

    max_items_el = root.find(".//player/maxItems")
    out["maxItems"] = int(max_items_el.text or 12) if max_items_el is not None else 12

    spouse_el = root.find(".//player/spouse")
    out["spouse"] = spouse_el.text.strip() if spouse_el is not None and spouse_el.text else None

    buildings = []
    under_construction = []
    for b in root.findall(".//locations/GameLocation/buildings/Building"):
        t = b.find("buildingType") if b.find("buildingType") is not None else b.find("name")
        if t is None or not t.text:
            continue
        days_el = b.find("daysOfConstructionLeft")
        days_left = int(days_el.text or 0) if days_el is not None else 0
        if days_left > 0:
            under_construction.append({"name": t.text, "daysLeft": days_left})
        else:
            buildings.append(t.text)
    out["buildings"] = buildings
    out["under_construction"] = under_construction

    hearts8plus = 0
    seen_8h = set()
    for path in _frnd_paths:
        for entry in root.findall(path):
            key_el = entry.find("key/string")
            pts_el = entry.find("value/Friendship/Points")
            if key_el is None or pts_el is None: continue
            npc_key = key_el.text or ""
            if npc_key in seen_8h: continue
            if int(pts_el.text or 0) >= 2000:
                hearts8plus += 1
                seen_8h.add(npc_key)
    out["npcsAt8Hearts"] = hearts8plus

    # ── CC BUNDLES (structured for Junimo Feed) ──────────────────────────────
    # bundleRewards tracks true completion (handles "pick X of Y" bundles correctly)
    bundle_done = {}
    for item in root.findall(".//bundleRewards/item"):
        k = item.find("key/int")
        v = item.find("value/boolean")
        if k is not None and v is not None:
            bundle_done[int(k.text or -1)] = (v.text == 'true')

    # SV 1.6 stores 3 booleans per item slot in the ArrayOfBoolean.
    # Slot for item i is at index i*3 (triples represent item+quantity+quality).
    slot_donated = {}  # {(bundle_id, item_idx): bool}
    for bundle_el in root.findall(".//bundles/item"):
        key_el  = bundle_el.find("key/int")
        val_els = bundle_el.findall("value/ArrayOfBoolean/boolean")
        if key_el is None or not val_els: continue
        bid = int(key_el.text or -1)
        for i, v in enumerate(val_els):
            slot_donated[(bid, i)] = (v.text == 'true')

    # Vault: if ccVault mail received, mark all vault bundle slots as done
    # Must run BEFORE room_map is built so the data propagates into cc_bundles output
    if "ccVault" in mail:
        for bid in [23, 24, 25, 26]:
            bundle_done[bid] = True
            slot_donated[(bid, 0)] = True

    # Raw per-slot completion, independent of CC_BUNDLE_MAP identity — lets
    # the frontend pair real bundleData item names with real completion
    # status for ANY save (vanilla or remixed) without trusting whether
    # CC_BUNDLE_MAP guessed the right item count/order for a given bundle.
    # Re-keyed from the raw i*3 XML triple-index to a plain item index (0,1,2...)
    # matching bundleData["Room/bid"].items[i] directly — the *3 encoding is
    # an XML-format quirk callers shouldn't need to know about.
    out["bundleSlotDonated"] = {f"{bid}_{i // 3}": v for (bid, i), v in slot_donated.items() if i % 3 == 0}

    hoard_have_set = set(out["hoard_have"])
    room_map = {r: {"name": r, "emoji": ROOM_EMOJI[r], "bundles": [], "done": 0} for r in ROOM_ORDER}

    for bid in sorted(BUNDLE_ROOMS.keys()):
        room = BUNDLE_ROOMS[bid]
        items = CC_BUNDLE_MAP.get(bid, [])
        # Vault bundles: show gold amount as a single slot
        if not items and bid in vault_map:
            items = [vault_map[bid]]
        slots = [{"code": c, "name": HOARD_CODE_NAMES.get(c, c),
                  "have": slot_donated.get((bid, i * 3), False) or c in hoard_have_set}
                 for i, c in enumerate(items)]
        # A bundle is complete if bundleRewards says so OR all required slots are donated.
        # bundleRewards can lag (e.g. CC cutscene not yet triggered) even when items are in.
        all_slots_in = len(items) > 0 and all(slot_donated.get((bid, i * 3), False) for i in range(len(items)))
        completed = bundle_done.get(bid, False) or all_slots_in
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

    # Weapons have no dedicated "equipped" slot in the save the way hats/rings
    # do — pick the best melee weapon actually carried (highest max damage) as
    # the one worth showing on Fit Check.
    best_weapon = None
    _ns_xsi = "http://www.w3.org/2001/XMLSchema-instance"
    for it in root.findall(".//player/items/Item"):
        if it.get(f"{{{_ns_xsi}}}type") != "MeleeWeapon":
            continue
        name_el, min_el, max_el = it.find("name"), it.find("minDamage"), it.find("maxDamage")
        if name_el is None or not name_el.text:
            continue
        max_dmg = int(max_el.text or 0) if max_el is not None else 0
        if best_weapon is None or max_dmg > best_weapon["maxDamage"]:
            best_weapon = {
                "name": name_el.text,
                "minDamage": int(min_el.text or 0) if min_el is not None else 0,
                "maxDamage": max_dmg,
            }

    out["equipment"] = {
        "hat":       _item_name(".//player/hat/Hat"),
        "boots":     _item_name(".//player/boots/Boots"),
        "leftRing":  _item_name(".//player/leftRing/Ring"),
        "rightRing": _item_name(".//player/rightRing/Ring"),
        "shirt":     _item_name(".//player/shirtItem/Clothing"),
        "pants":     _item_name(".//player/pantsItem/Clothing"),
        "weapon":    best_weapon,
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
    # Stardew 1.6 stores many boolean flags as empty XML elements (<flag />)
    # rather than <flag>true</flag>, so also cross-check mail flags as fallback.
    MAIL_FLAG_MAP = {
        "hasSkullKey":         "HasSkullKey",
        "hasRustyKey":         "HasRustyKey",
        "hasClubCard":         "HasClubCard",
        "canUnderstandDwarves":"learnedDwarfLanguage",
        "hasMagnifyingGlass":  "HasMagnifyingGlass",
    }
    for flag in ("hasSkullKey", "hasClubCard", "hasDarkTalisman", "hasMagicInk",
                 "hasMagnifyingGlass", "hasRustyKey", "canUnderstandDwarves",
                 "hasGaloshes", "hasSpecialCharm", "catPerson"):
        el = root.find(f".//player/{flag}")
        xml_true = el is not None and (el.text or "").lower() == "true"
        mail_key = MAIL_FLAG_MAP.get(flag)
        mail_true = mail_key is not None and mail_key in mail
        out[flag] = xml_true or mail_true

    cave_el = root.find(".//player/caveChoice")
    out["caveChoice"] = int(cave_el.text or 0) if cave_el is not None else 0

    # ── ANIMALS ───────────────────────────────────────────────────────────────
    # FarmAnimal lives at indoors/animals/item/value/FarmAnimal (a serialized
    # key->value dict), NOT indoors/characters/FarmAnimal — that slot is for
    # NPCs, and is always empty for an animal house. Confirmed against a real
    # save: the old path found 0 animals, this one finds all of them.
    animals = []
    for b in root.findall(".//locations/GameLocation/buildings/Building"):
        bt = find_any(b, "buildingType", "name")
        bname = bt.text if bt is not None else "Building"
        for a in b.findall(".//indoors/animals/item/value/FarmAnimal"):
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
    if not SAVE_PATH:
        latest_data = {"error": "Couldn't find a Stardew save automatically. Set SDV_SAVE_PATH to your save file's full path."}
        print("[bridge] No save found automatically — set SDV_SAVE_PATH and restart.")
        return
    print(f"[bridge] Watching: {SAVE_PATH}")
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
                threading.Thread(target=push_to_gist, args=(latest_data,), daemon=True).start()
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
        else:
            # Serve static files from the project directory
            import mimetypes, hashlib, gzip as gzip_mod
            req = self.path.split('?')[0]
            if req == '/':
                req = '/index.html'
            file_path = os.path.join(_BRIDGE_DIR, req.lstrip('/'))
            if os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                mime = mime or "application/octet-stream"
                with open(file_path, 'rb') as f:
                    raw = f.read()

                # ETag from content hash for cache validation
                etag = '"' + hashlib.md5(raw).hexdigest()[:16] + '"'
                if self.headers.get('If-None-Match') == etag:
                    self.send_response(304)
                    self.end_headers()
                    return

                # Gzip for text assets
                accept_enc = self.headers.get('Accept-Encoding', '')
                use_gzip = 'gzip' in accept_enc and mime.startswith(('text/', 'application/javascript', 'application/json'))
                body = gzip_mod.compress(raw, compresslevel=6) if use_gzip else raw

                # Cache policy: assets (images/fonts) → 7 days; HTML/JS → revalidate
                is_asset = mime.startswith('image/') or 'font' in mime
                cache = 'public, max-age=604800, immutable' if is_asset else 'no-cache'

                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", cache)
                self.send_header("ETag", etag)
                self.send_header("Access-Control-Allow-Origin", "*")
                if use_gzip:
                    self.send_header("Content-Encoding", "gzip")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    if not GIST_TOKEN:
        run_setup_wizard()
    elif GIST_ID:
        print_sync_code(GIST_TOKEN, GIST_ID)

    if SAVE_PATH and os.path.exists(SAVE_PATH):
        latest_data = parse_save()
        # Push immediately on startup so phone gets current data right away
        threading.Thread(target=push_to_gist, args=(latest_data,), daemon=True).start()
    elif SAVE_PATH:
        latest_data = {"error": "Save file not found yet."}
    else:
        latest_data = {"error": "Couldn't find a Stardew save automatically. Set SDV_SAVE_PATH to your save file's full path."}
        print("[bridge] No Stardew save found automatically.")
        print("[bridge] If you've played before, set SDV_SAVE_PATH to your save file's full path and run this again.")

    t = threading.Thread(target=watch_loop, daemon=True)
    t.start()

    import re, subprocess
    ips = []
    try:
        out = subprocess.check_output(['ifconfig'], text=True, stderr=subprocess.DEVNULL)
        for m in re.finditer(r'inet (\d+\.\d+\.\d+\.\d+)', out):
            ip = m.group(1)
            if not ip.startswith('127') and not ip.startswith('169'):
                ips.append(ip)
    except Exception:
        pass

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[bridge] Running — open on iPhone (same WiFi):")
    for ip in ips:
        print(f"           http://{ip}:{PORT}")
    if not ips:
        print(f"           http://[your-mac-ip]:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[bridge] Stopped.")
