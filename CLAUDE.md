# Stardew or Dew Not — Development Brief

## Project
Interactive Year 1 Stardew Valley min-max tracker suite.

- **Goal:** Perfect, production-ready iPhone web app (Safari)
- **Hosting:** GitHub Pages (`cerealbishh.github.io/Stardew-Valley`)
- **Also deployed on:** Vercel (`stardew-or-dew-not` project under `cerealbishhs-projects`)
- **Storage:** localStorage + Python bridge (`stardew-bridge.py`) for live game sync
- **Aesthetic:** Y2K kawaii cottagecore pastel retro (soft pinks, mints, lavenders, bubbly UI, pixel headers)

## Device Setup
- MacBook Air M1 + iPhone 15 (Safari + web app mode)
- Playstyle: Min-max Year 1 (fishing + Skull Cavern → Iridium Bars → Starfruit)
- Target: ~5 million gold by Summer 28
- Seed: `203853699`

## Repo
- GitHub: `cerealbishh/Stardew-Valley`
- Main branch: `main`
- Dev branch convention: `claude/<description>`

## Current State (as of Session 4)
Single `index.html` (~60KB, 1292 lines) + supporting files. Sessions so far:

| Session | What was built |
|---------|---------------|
| 1 | Initial single HTML file (~128KB), all features rough-drafted |
| 2 | New app shell — bottom nav, seasonal CSS tokens, bridge UI, Junimos panel |
| 3 | All 112 days of Route 66 data hardcoded; corrupted index.html fixed; `.gitignore *.crt` |
| 4 | Y2K kawaii theme (CSS vars, seasonal color switching, dark mode); 5-tab bottom nav; service-worker bridge fix |

## File Structure
```
index.html          # Main app (single file, all HTML/CSS/JS)
manifest.json       # PWA manifest — name: "Stardew or Dew Not, There is no Try", short_name: "Hoe Down 🌾"
service-worker.js   # SW for PWA + bridge polling fix
stardew-bridge.py   # Python bridge for live game state sync
update-checker.js   # Checks for app updates
.gitignore          # Ignores *.crt (Tailscale certs)
CLAUDE.md           # This file
```

## Theme / CSS Architecture
CSS custom properties on `:root` with seasonal overrides:
- `html[data-season=spring]` → pinks/lavenders (default)
- `html[data-season=summer]` → mint/teal/gold
- `html[data-season=fall]` → amber/burnt orange
- `html[data-season=winter]` → blues/purples
- `html[data-dark=true]` → dark mode override

Key vars: `--bg, --surf, --text, --muted, --border, --acc, --acc2, --hdr-a, --hdr-b, --nav-bg, --nav-act`

Task badge colors: `--t-fire` (red), `--t-prep` (orange), `--t-gather` (green), `--t-plate` (purple), `--t-purchase` (blue), `--t-par` (gold), `--t-tomorrow` (gray)

---

## The Four Tools

### 🔵 Route 66 — Daily Efficiency Checklist
**Tabs:**
- **Prep/Fire/Plate** — Today's tasks sorted by urgency (fire=urgent, prep=setup, plate=gather)
- **It Is Wednesday My Dudes 🐸** — Calendar (festivals, birthdays, weather flags hardcoded from seed 203853699)
- **Are We There Yet? 🗺️** — Par check (gold/skills/ore vs targets, green/yellow/red status)
- **🚨 Never Forget 🚨** — Carryover (unchecked tasks auto-roll to next day with "[X carryover]" badge)

**Behavior:**
- Today's card always open; past days collapsed + inverted colors; future days dimmed
- Real-time daily progress ("5/8 → 6/8" as you check boxes)
- ✓ for 100% complete, ◐ for 50-99%, ○ for 0-49%
- Color-coded left borders (green=done, red=in progress, gray=not started)
- Weather-conditional tasks tagged ☔/☀️ (blue tint for rain tasks)
- Birthday tasks pink-tagged 🎂 with easiest gift + how to get it
- Festival days get special card treatment
- All 112 days (Spring 1 → Winter 28) fully hardcoded with tasks

---

### 🔴 The Hoard — Items & Unlocks Tracker
**Tabs:**
- **Junimo Feed 🌽** — Community Center bundles by room (Pantry, Crafts Room, Fish Tank, Boiler Room, Bulletin Board, Vault). Auto-checked from bridge.
- **Take This Job And Shove It 📋** — Journal quests + special orders (Pierre/bulletin). Status: active/complete/missed/not yet.
- **Omg Look Something Shiny ✨** — Museum donations (Gunther). Artifacts + minerals. Auto-counted from bridge.
- **I Made It Myself 🔨** — Unlocks (Tools, Buildings, Recipes, Skills milestones).
- **Covenant of the Rock 💌** — NPCs collapsible by card. Birthday + easiest gift, friendship hearts (live), gifts given, cutscenes seen. Sorted by next birthday.

Source of truth: Quantities from bridge (live). Hoard only tracks yes/no checklists + world-state flags.

---

### ✨ Story Time — Events, Cutscenes, Lore, Progression
**Tabs:**
- **Previously On 🎬** — All cutscenes in chronological order by season/day. Auto-checked from bridge events.
- **The Lore 📜** — World flags (Wizard met, CC complete, desert unlocked, skull cavern unlocked, goblin solved, witch visited, Krobus met, cave choice, etc.). Auto-checked from bridge.
- **Covenant of the Rock 💌** — One collapsible card per NPC. Portrait emoji, birthday, hearts (live), gifts given, cutscenes seen, romance progress. Sorted by next birthday.
- **Main Quest 📋** — Journal quests + special orders. Auto-detected where possible.
- **Milestones 🏆** — Grandpa criteria (earnings tiers, skills maxed, CC done, 8-heart friends, museum complete). Progress bars. All auto-checked.

---

### 💜 Big Daddy Nightlock — Game Menu E-Screen + All Chests
**Tabs:**
- **The Tardis 🌀** — Backpack inventory (exact items + counts from bridge)
- **Davy Jones' Locker 🏴‍☠️** — All chests across town, grouped by location with item counts
- **Fit Check 👗** — Equipped (weapon + damage, rings, boots, hat, shirt). Live from bridge.
- **Skillmaxxing 📈** — All 5 skills (level + XP bar + what unlocks at next level)
- **Touching Grass 🌿** — Friendship points per NPC, last gift date, liked gifts list
- **I Watched One (1) Youtube Video 📺** — Crafting + cooking recipes (known = checkbox)
- **The Supporting Cast 🐄** — Animals grouped by building (Coop/Barn/other)
- **Plot Armor 🛡️** — Special flags (skull key, dark talisman, magic ink, magnifying glass, club card, dwarf language, etc.). All auto-checked from bridge.
- **The Holocron 🔮** — Collections (Fish Caught, Artifacts, Minerals, Cooking, etc.)

---

## Bridge Setup
- `stardew-bridge.py` runs on MacBook, serves game state over HTTP
- Supports Tailscale hostname (with `.crt` cert, ignored by gitignore) and Cloudflare tunnel URLs
- Service worker handles bridge polling; fix landed in Session 4
- Bridge status dot in header: red = disconnected, green = connected

## PWA Setup
- `manifest.json` configured for standalone display, portrait, iOS web app
- Icons are inline SVG data URIs (🌾 emoji on pink background)
- `apple-mobile-web-app-capable` and status bar meta tags set
- Safe area insets handled with `env(safe-area-inset-top/bottom)`
