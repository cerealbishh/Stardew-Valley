# Stardew or Dew Not — Development Brief

## Project
Interactive Year 1 Stardew Valley min-max tracker suite.

- **Goal:** Perfect, production-ready iPhone web app (Safari)
- **Hosting:** GitHub Pages (`cerealbishh.github.io/Stardew-Valley`)
- **Storage:** localStorage + Python bridge (`stardew-bridge.py`) for live game sync
- **Aesthetic:** Y2K kawaii cottagecore pastel retro (soft pinks, mints, lavenders, bubbly UI, pixel headers)

## Device Setup
- MacBook Air M1 + iPhone 15 (Safari + web app mode)
- Playstyle: Min-max Year 1 (fishing + Skull Cavern → Iridium Bars → Starfruit)
- Target: ~5 million gold by Summer 28, CC complete Year 1, marry Abigail post-Year 1
- Seed: random (no fixed seed)

## Git / Deploy Situation
- **Repo:** `cerealbishh/Stardew-Valley` on GitHub
- **Live site deploys from:** `main` branch
- **Working branch:** `claude/stardew-valley-tracker-onS2e` (exists on remote)
- **BLOCKER:** The Claude Code environment's git proxy returns 403 on all pushes. Claude **cannot push** from this environment. Roohi must push from her Mac terminal.
- **To deploy:** Copy `index.html` from this environment to Mac → `git push origin main` from Mac
- **Stop hook:** `~/.claude/stop-hook-git-check.sh` fires every turn because of unpushed commits. Disable with `chmod -x ~/.claude/stop-hook-git-check.sh` if it's annoying.

## Bridge (stardew-bridge.py)
- Runs on Mac, parses Stardew save file
- Save file: `/Users/roohi/.config/StardewValley/Saves/Hoedown_203853699/Hoedown_203853699`
- Tailscale cert: `/Users/roohi/roohis-macbook-air.tailcce197.ts.net.crt` + `.key`
- HTTPS on port 8742 → `/save` endpoint
- HTTP on port 8743 → `/cert` endpoint (cert install)
- Returns: gold, season, day, year, skills, friendship, inventory, chest_ore, hoard_have, hoard_done, mail, events, totalMoneyEarned, stats, completedQuests, museumDonations, houseUpgradeLevel, buildings, npcsAt8Hearts
- XP thresholds: `[0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]`

## localStorage Keys
- `sdv_dark` — dark mode boolean
- `sdv_icons` — icon style (pixel/kawaii/line)
- `sdv_ip` — bridge IP
- `sdv_last_season` — last known season from bridge
- `sdv_last_day` — last known day from bridge
- `sdv_t_{id}` — task checkbox state ('1'/'0')
- `sdv_par_{id}` — par check state ('1'/'0')
- `sdv_c_{id}` — carry item state ('1'/'0')

## CSS Token System
HTML element has `data-season` and `data-dark` attributes.
```
:root tokens: --r66, --hoard, --story, --night (section colors)
              --bg, --card-bg, --text, --text-muted, --border
              --ticker-bg (#281515), --ticker-text (#ffd0a0)
              --nav-bg, --nav-border, --nav-h (60px), --ticker-h (34px)
[data-dark=true] — dark overrides
[data-season=spring/summer/fall/winter] — gradient tokens --sa, --sb
Each panel sets --panel-accent via CSS: #route{--panel-accent:var(--r66)} etc.
```

---

## Build Status

### ✅ Session 2 — DONE (not yet live)
New visual shell:
- Dark ticker at top (`#281515` bg, `#ffd0a0` text, monospace, scrolling)
- Bottom nav: Home / Route 66 / The Hoard / Story Time / Nightlock
- Seasonal gradient background (spring pink/purple → summer orange → fall brown → winter blue)
- Junimo SVG animations on Home screen
- Floating seasonal particles (emoji floaters)
- Bridge UI on Home: dot indicator, IP input, quick stats (gold/day/mine)
- Entry cards on Home linking to each section
- Dark mode toggle + icon style toggle
- All nav/tab switching via event delegation (iOS tap fix)
- Desktop sidebar layout at 768px+

### ✅ Session 3 — DONE (not yet live)
Route 66 fully implemented:
- **All 112 day cards** (Spring 1–28, Summer 1–28, Fall 1–28, Winter 1–28)
- Each day has 3–6 tasks with type badges: fire/prep/gather/plate/purchase/par/tomorrow
- Today's card auto-opens + scrolls into view; past days dimmed/grey; future days faded
- Task checkboxes persist in localStorage (`sdv_t_{id}`)
- Birthday days labeled 🎂 with gift suggestions in task text
- Festival days labeled with emoji (🥚🌊🎡🎃🎄 etc)
- Rain-conditional tasks labeled ☔/☀️
- **Calendar tab** — 7×4 grid, event dots, event list below
- **Par Check tab** — 16 milestone checkboxes with target dates (Sp5–Wi28)
- **Never Forget tab** — 4 carry sections: Tools & Upgrades, Mine Supplies, Community Center, NPC Gifts
- Bridge connect → re-renders route/cal for correct season+day
- Season+day persisted to localStorage (`sdv_last_season`, `sdv_last_day`)

### 🔲 Session 4 — TODO: The Hoard + Story Time
**The Hoard:**
- Junimo Feed 🌽 — CC bundles by room, checkable, auto-check from bridge `hoard_have`/`hoard_done`
- Take This Job 📋 — Journal quests + special orders, status badges
- Look Shiny ✨ — Museum donations, count from bridge `museumDonations`
- Made It Myself 🔨 — Tool/building/recipe/skill unlock milestones
- Covenant 💌 — NPC cards: portrait emoji, birthday, hearts (live from bridge `friendship`), gifts given

**Story Time:**
- Previously On 🎬 — Cutscenes in season/day order, auto-check from bridge `events`
- The Lore 📜 — World flags: Wizard met, CC complete, desert unlocked, skull cavern, goblin, witch, Krobus, cave choice — auto-check from bridge `mail`/`events`
- Covenant 💌 — Same NPC cards as Hoard (deduplicate if possible)
- Main Quest 📋 — Journal quests, auto-detect from bridge `completedQuests`
- Milestones 🏆 — Grandpa criteria with progress bars: earnings tiers, skills maxed, CC done, 8-heart friends, museum complete

### 🔲 Session 5 — TODO: Big Daddy Nightlock + Polish
- Tardis 🌀 — Backpack inventory (items + counts from bridge `inventory`)
- Davy Jones 🏴‍☠️ — Chests by location (from bridge `chest_ore`/chest data)
- Fit Check 👗 — Equipped weapon/rings/boots/hat (from bridge `stats`)
- Skillmaxxing 📈 — 5 skill XP bars with level + next unlock text
- Touching Grass 🌿 — Friendship points per NPC (from bridge `friendship`)
- One Video 📺 — Crafting + cooking recipe checklist
- The Cast 🐄 — Animals grouped by building (from bridge `buildings`)
- Plot Armor 🛡️ — Special flags: skull key, rusty key, dark talisman, magic ink, magnifying glass, club card, dwarf translation book, all from bridge `mail`/`events`
- Holocron 🔮 — Collections: fish caught, artifacts found, minerals found, cooking done
- Wire up global search on Home
- Final CLAUDE.md update

---

## The Four Tools (Design Spec)

### 🔵 Route 66 — Daily Efficiency Checklist
**Tabs:**
- **Prep/Fire/Plate** — Today's tasks sorted by urgency (fire=urgent, prep=setup, plate=gather)
- **It Is Wednesday My Dudes 🐸** — Calendar (festivals, birthdays)
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
