# Stardew or Dew Not — Development Brief

## Project
Interactive Year 1 Stardew Valley min-max tracker suite.

- **Goal:** Perfect, production-ready iPhone web app (Safari)
- **Hosting:** GitHub Pages (`cerealbishh.github.io/Stardew-Valley`) — deploys from `main` branch
- **Also on Vercel:** `stardew-or-dew-not.vercel.app` (auto-deploys from PRs)
- **Storage:** localStorage + Python bridge (`stardew-bridge.py`) for live game sync
- **Aesthetic:** Y2K kawaii cottagecore pastel retro (pinks, mints, lavenders, bubbly UI, pixel headers)

## Device Setup
- MacBook Air M1 + iPhone 15 (Safari + web app mode)
- Playstyle: Min-max Year 1 (fishing + Skull Cavern → Iridium Bars → Starfruit)
- Target: ~5 million gold by Summer 28, CC complete Year 1, marry Abigail post-Year 1
- Save: `HoeDown_440710266` (seed 440710266)
- Weather seed: 382994277 (accurate per-day rain forecasts baked into route tasks)

## Git / Deploy
- **Repo:** `cerealbishh/Stardew-Valley`
- **Working branch:** `claude/stardew-valley-tracker-onS2e` (exists on remote — pushes work!)
- **Open PR:** #3 (`claude/stardew-valley-tracker-onS2e` → `main`) — CI green, Vercel preview live
- **To go live:** Merge PR #3 on GitHub → GitHub Pages auto-deploys from main
- **Stop hook:** `~/.claude/stop-hook-git-check.sh` — disable with `chmod -x` if annoying

## Bridge (stardew-bridge.py)
- Runs on Mac, parses Stardew save file
- Save file: `/Users/roohi/.config/StardewValley/Saves/HoeDown_440710266/HoeDown_440710266`
- Tailscale cert: `/Users/roohi/roohis-macbook-air.tailcce197.ts.net.crt` + `.key`
- HTTPS on port 8742 → `/save` endpoint
- HTTP on port 8743 → `/cert` endpoint (cert install)
- Also pushes to GitHub Gist on startup so phone gets data without direct bridge connection
- Returns: gold, season, day, year, skills, friendship, inventory, chest_ore, hoard_have, hoard_done,
  mail, events, totalMoneyEarned, stats, completedQuests, museumDonations, houseUpgradeLevel,
  buildings, npcsAt8Hearts, backpack, equipment, appearance, spouse, caveChoice, catPerson,
  copperOre, ironOre, goldOre, coal
- XP thresholds: `[0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]`

## App Architecture
- Single `index.html` (~4800 lines) with all CSS + JS inline
- CSS uses `data-tab` + `data-sub` attributes on `<html>` for per-section theming
- Each section has its own pastel palette (spring=pink, summer=teal, fall=butter, winter=lavender)
- Per-tab overrides: `html[data-tab=hoard][data-sub=junimo]{...}` etc.
- Assets in `assets/` (icons, fonts, logo)
- Font: Press Start 2P (pixel) for headers

## localStorage Keys
- `sdv_dark` — dark mode boolean
- `sdv_ip` — bridge IP
- `sdv_last_season` / `sdv_last_day` — persisted from bridge or day override
- `sdv_t_{id}` — task checkbox state
- `sdv_par_{id}` — par check state
- `sdv_c_{id}` — carry item state
- `sdv_b_{bundleId}_{slot}` — CC bundle item checks (manual override)

## Build Status — EVERYTHING IS BUILT ✅

### ✅ Route 66 (all 4 seasons implemented)
- 112 day cards with accurate weather from seed 382994277
- Tasks auto-check from bridge via `syncTasksFromSave()`
- Calendar tab, Par Check (16 milestones), Never Forget (4 carry sections)
- Day override modal for offline use
- Stale data banner if save hasn't updated

### ✅ The Hoard
- **Junimo Feed** — All 6 CC rooms with all bundle items, auto-checked from `hoard_done`
- **Take This Job** — Journal quests parsed from bridge `completedQuests`, Help Wanted support
- **Look Shiny** — Museum donations count + progress bar from `museumDonations`
- **I Made It Myself** — Tool/building/recipe/skill milestones
- **Covenant of the Rock** — All 32 NPCs, birthday, hearts (live from `friendship`), gift hints with availability info

### ✅ Story Time
- **Previously On** — Cutscenes grouped by season, auto-checked from bridge `events`
- **The Lore** — World flags from bridge `mail`/`events` (wizard, CC, desert, skull cavern, etc.)
- **Neighbors 2: Sorority Rising** — Same NPC cards as Hoard
- **Milestones** — Grandpa score with candle display, Year 1 gold progress bar
- **Main Quest** — Journal quests
- **Never Tell Me the Odds** — Special odds/luck tracking

### ✅ Big Daddy Nightlock
- **The Tardis** — Backpack inventory from `backpack`
- **Davy Jones** — Resources/ore counts, gold progress bar
- **Fit Check** — Equipment slots (hat/boots/rings/shirt/pants), appearance, spouse, cave choice
- **Skillmaxxing** — 5 skill XP bars from bridge `skills`
- **Touching Grass** — Friendship hearts per NPC from `friendship`
- **One Video** — Crafting + cooking recipe checklist
- **The Supporting Cast** — Animals from `buildings`
- **Plot Armor** — Special flags (skull key, rusty key, dark talisman, etc.)
- **The Holocron** — Collections (fish, artifacts, minerals, cooking)

## What Actually Needs Work
- Merge PR #3 to go live (user action on GitHub)
- Any bugs discovered during actual gameplay
- Polish pass after real-world usage on iPhone

---

## The Four Tools (Design Reference)

### 🔵 Route 66
Tasks by day, calendar, par checks, never forget carry list.
Weather-conditional tasks tagged ☔/☀️ based on seed-accurate forecasts.
Birthday tasks 🎂 with easiest gift + source.

### 🔴 The Hoard
CC bundles, quests, museum, unlocks, NPC cards.

### ✨ Story Time
Cutscenes, world flags, NPC covenant, milestones, main quest.

### 💜 Big Daddy Nightlock
Inventory, resources, equipment, skills, friendship, recipes, animals, flags, collections.
