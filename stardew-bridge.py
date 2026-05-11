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
CERT_FILE = "/Users/roohi/Documents/Stardew Valley/bridge-cert.pem"
KEY_FILE  = "/Users/roohi/Documents/Stardew Valley/bridge-key.pem"

latest_data = {}
last_modified = 0

SKILL_NAMES = ["Farming", "Fishing", "Foraging", "Mining", "Combat"]
SKILL_IDS   = ["farm",    "fish",    "forage",   "mine",   "combat"]

FRIENDSHIP_NPCS = [
    "Abigail","Alex","Caroline","Clint","Demetrius","Elliott","Emily",
    "Evelyn","George","Gus","Harvey","Haley","Jas","Jodi","Kent","Leah",
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
}

CC_BUNDLE_MAP = {
    0:  ["sp_parsnip","sp_greenbean","sp_cauliflower","sp_potato"],
    1:  ["su_tomato","su_hotpepper","su_blueberry","su_melon"],
    2:  ["fa_eggplant","fa_pumpkin","fa_yam","su_corn"],
    3:  ["wi_winterroot","wi_crystalfruit","wi_snowyam","wi_crocus"],
    4:  ["sp_horseradish","sp_daffodil","sp_leek","sp_dandelion"],
    5:  ["su_spiceberry","su_grape","su_sweetpea","su_fiddlehead"],
    6:  ["fa_mushroom","fa_plum","fa_hazelnut","fa_blackberry"],
    7:  ["wi_winterroot","wi_crystalfruit","wi_snowyam","wi_crocus"],
    8:  ["any_catfish","sp_eel","any_shad","any_sunfish"],
    9:  ["su_pufferfish","su_tuna","su_redsnapper","su_tilapia"],
    10: ["any_woodskip","any_cavecarrot","any_ghostfish","any_sandfish"],
    11: ["any_bream","any_chub","wi_squid"],
    13: ["sp_catfish","fa_walleye","fa_tigertrout","sp_eel"],
    14: ["any_maplesyrup","any_oakresin","any_pinetar"],
    15: ["any_hardwood"],
    17: ["any_wood","any_stone","any_hay"],
    19: ["any_redmush","any_seaurchin","any_cavecarrot"],
    20: ["any_coconut","any_cactus"],
    21: ["any_frozengeode","any_aquamarine"],
    23: ["any_wine","any_jelly","any_cheese","any_honey"],
    24: ["any_makiroll","any_friedegg"],
    26: ["hard_largemilk","hard_largeeggw","hard_goatmilk","hard_wool","hard_duckegg","hard_largeeggb"],
    31: ["su_poppy","su_sunflower","hard_redcabbage","hard_duckfeather"],
    32: ["any_woodskip"],
    33: ["fa_pomegranate","fa_apple"],
    34: ["any_maplesyrup","any_oakresin","any_pinetar","su_wheat10"],
}

SEASONS = ["spring", "summer", "fall", "winter"]


def parse_save():
    try:
        tree = ET.parse(SAVE_PATH)
        root = tree.getroot()
    except Exception as e:
        return {"error": f"Failed to parse save: {e}"}

    out = {
        "farm": "Hoe Down Farms",
        "updated": datetime.now().strftime("%H:%M:%S"),
        "gold": 0, "season": "spring", "day": 1, "year": 1,
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
        vault_map = {36:"vault_2500",37:"vault_5000",38:"vault_10000",39:"vault_25000"}
        if bundle_id in vault_map and all_done:
            hoard_done.add(vault_map[bundle_id])
    out["hoard_done"] = list(hoard_done)

    mail = set()
    for m in root.findall(".//player/mailReceived/string"):
        if m.text: mail.add(m.text)
    out["mail"] = list(mail)

    events = set()
    for e in root.findall(".//player/eventsSeen/int"):
        if e.text: events.add(int(e.text))
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
        id_el = q.find("id") or q.find("questID")
        if completed_el is not None and completed_el.text == 'true' and id_el is not None:
            completed_quests.add(int(id_el.text or 0))
    out["completedQuests"] = list(completed_quests)

    donated = 0
    for item in root.findall(".//locations/GameLocation/museumPieces/item"):
        donated += 1
    out["museumDonations"] = donated

    house_el = root.find(".//player/houseUpgradeLevel")
    out["houseUpgradeLevel"] = int(house_el.text or 0) if house_el is not None else 0

    buildings = []
    for b in root.findall(".//locations/GameLocation/buildings/Building"):
        t = b.find("buildingType") or b.find("name")
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
        elif self.path == "/":
            body = b"Stardew Bridge is running. GET /save for data."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
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
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import ipaddress

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
                .add_extension(x509.SubjectAlternativeName([
                    x509.IPAddress(ipaddress.IPv4Address('10.0.0.70')),
                    x509.DNSName('localhost'),
                ]), critical=False)
                .sign(key, hashes.SHA256())
            )
            with open(KEY_FILE, 'wb') as f:
                f.write(key.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()))
            with open(CERT_FILE, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            print(f"[bridge] Certificate saved to {CERT_FILE}")
            print(f"[bridge] Install cert on iPhone: http://10.0.0.70:8743/cert")
        except ImportError:
            print("[bridge] cryptography not installed. Run: pip3 install cryptography")
            exit(1)

    if os.path.exists(SAVE_PATH):
        latest_data = parse_save()
    else:
        latest_data = {"error": "Save file not found yet."}

    t = threading.Thread(target=watch_loop, daemon=True)
    t.start()

    http_server = http.server.HTTPServer(("0.0.0.0", 8743), Handler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    print(f"[bridge] Cert download (HTTP): http://10.0.0.70:8743/cert")

    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"[bridge] HTTPS server running on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[bridge] Stopped.")
