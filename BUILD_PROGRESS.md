# Stardew Valley Tracker — Build Progress

**Last Updated:** 2026-07-05  
**Branch:** `claude/chat-memory-check-zny9Q`  
**Status:** Phase 3 (HTML structure) → Phase 4 (JavaScript rendering) next

---

## 🎯 Project Overview

**Goal:** Production-ready iPhone web app (Safari) for Year 1 Stardew Valley min-max tracking  
**Hosting:** GitHub Pages (`cerealbishh.github.io/Stardew-Valley`)  
**Sync:** Live game sync via Python bridge (`stardew-bridge.py`)  
**Theme:** Y2K kawaii cottagecore pastel (soft pinks, mints, lavenders, pixel headers)  
**Device:** MacBook Air M1 + iPhone 15  
**Seed:** 203853699

---

## ✅ COMPLETED

### Phase 1: Planning & Data Mapping
- ✅ Finalized complete data organization across 4 major tools
- ✅ Mapped ALL save file data to specific UI tabs
- ✅ Locked in user preferences:
  - NPC hearts shown as both ❤️ visual (0-8) + raw points (0-2880)
  - NPCs sorted by next birthday
  - Bridge auto-polls every 30s + manual refresh button
  - All 87 locations tracked
  - All chests with contents visible
  - Collections: Fish, Artifacts, Minerals, Crops Shipped, Monsters Killed
  - Web app mode writable (checkboxes sync back to save)
  - Additional: Pet info, daily weather, daily luck, farm name in ticker

### Phase 2: Python Bridge Expansion ✅
**File:** `/home/user/Stardew-Valley/stardew-bridge.py`

Bridge now exposes:
- ✅ Player personal data: name, farm name, appearance (hair/skin/shoes), pet (type/breed), cave choice, gender
- ✅ All NPC data: friendships (0-2880 points), names, relationships
- ✅ Recipes: 13 cooking + 50 crafting recipes with known/unknown status
- ✅ Special flags: hasSkullKey, hasClubCard, hasDarkTalisman, hasMagicInk, hasMagnifyingGlass, hasRustyKey, HasTownKey, hasSpecialCharm, hasUnlockedSkullDoor, canUnderstandDwarves, catPerson
- ✅ All chests: 9 chests across all locations with full item contents
- ✅ Farm animals: name, type, friendship per animal
- ✅ Quests: active + completed with full details (title, description, objective, completion status)
- ✅ Secret notes seen: count and locations
- ✅ Collections: fish caught, artifacts found, minerals found, crops shipped, monsters killed
- ✅ Skills: all 6 skills (Farming, Fishing, Foraging, Mining, Combat, Luck) with levels + XP
- ✅ World state: locations unlocked, wizard met, goblin bridge, etc.
- ✅ Daily data: season, day, year, weather (rain/snow/lightning), daily luck modifier
- ✅ Time tracking: farm animals, births, deaths

**Bridge Status:** Fully tested ✅
- Save file parses without errors
- 87 locations found
- 40 NPC instances across locations
- 13 cooking + 50 crafting recipes detected
- 9 chests detected and parseable

**Endpoint:** `GET /save` → Returns comprehensive JSON with all above data

### Phase 3: HTML Tab Structure ✅
**File:** `/home/user/Stardew-Valley/index.html`

Replaced 3 "Coming Soon" stubs with full sub-nav + sub-panel architecture:

#### 🔴 **The Hoard** (5 tabs)
- 🌽 **Junimo Feed** — Community Center bundles by room
- 📋 **Take This Job And Shove It** — Active quests + journal
- ✨ **Omg Look Something Shiny** — Museum donations (X/95 progress)
- 🔨 **I Made It Myself** — Farm buildings + all 87 locations access status
- 💌 **Covenant of the Rock** — NPC birthdays, friendship (hearts + points), gifts given, cutscenes seen, sorted by next birthday

#### ✨ **Story Time** (5 tabs)
- 🎬 **Previously On** — All cutscenes in chronological order (auto-checked from bridge)
- 📜 **The Lore** — World flags (skulls, locations unlocked, etc.) + secret notes seen
- 💌 **Covenant of the Rock** — NPC events/cutscenes per NPC
- 📋 **Main Quest** — Active quests + eventsSeen entries
- 🏆 **Milestones** — Grandpa criteria progress bars (earnings, skills maxed, CC done, 8-heart friends, museum complete)

#### 💜 **Big Daddy Nightlock** (9 tabs)
- 🏴‍☠️ **Inventory** (absorbs The Tardis) — Backpack (36 items, exact counts, qualities) + cash + all chests grouped by location
- 👗 **Fit Check** — Appearance (hair/skin/shoes colors) + equipment (hat, boots, shirt, pants, rings, accessories) + currently holding
- 📈 **Skillmaxxing** — All 6 skills (level + XP bar + next unlock)
- 🌿 **Touching Grass** — NPC friendships (hearts + points), last gift date & item, romance status, marriage status
- 📺 **I Watched One (1) Youtube Video** — Cooking + crafting recipes (known checkboxes)
- 🐄 **The Supporting Cast** — Farm animals by building + pets + all locations + buildings + terrain
- 🛡️ **Plot Armor** — Special flags (skull key, dark talisman, etc.) + world unlock flags
- 🔮 **The Holocron** — Collections (fish, artifacts, minerals, crops, monsters) with X/Y progress
- 🎲 **Never Tell Me the Odds** — Daily schedule, tool usage, professions, movement tracking

**Sub-nav buttons:** All 15 tabs have functional click handlers ready for content rendering

---

## 🔄 IN PROGRESS / NEXT STEPS

### Phase 4: JavaScript Rendering Functions (NEXT)

For each sub-panel, write render functions that:
1. Fetch bridge data from `S.bridge` (global cache)
2. Parse and format data for display
3. Render HTML cards/lists with proper styling
4. Hook up checkboxes to localStorage + bridge sync

**High-priority tabs to start with:**
1. **Nightlock → Inventory** (simplest: just list items + chests)
2. **Nightlock → Skills** (skill bars + XP visualization)
3. **Hoard → Quests** (quest list with status badges)
4. **Story Time → Milestones** (progress bars for Grandpa criteria)

### Phase 5: Live Bridge Integration

- Connect to bridge `/save` endpoint via `fetchBridge()`
- Auto-poll every 30s (already partially implemented)
- Add manual "Refresh" button in ticker
- Green/red sync indicator dot in top bar
- Error handling for offline/connection lost

### Phase 6: UI/Design Polish

- Add Stardew Valley pixel art icons for each tab
- Ensure Y2K kawaii cottagecore consistency across all new tabs
- Mobile optimization for iPhone 15 Safari:
  - Safe areas for notch/home bar
  - Touch-friendly checkbox sizes
  - Optimized spacing for small screens
- Dark mode support (already implemented in base theme)

---

## 📋 Data Model Reference

### Bridge Response Structure
```json
{
  "farm": "Hoe Down Farms",
  "updated": "HH:MM:SS",
  "season": "spring",
  "day": 1,
  "year": 1,
  "gold": 0,
  "totalMoneyEarned": 0,
  
  "player": {
    "name": "...",
    "farm_name": "...",
    "appearance": { "hair": 101, "skin": 7, "shoes": 4 },
    "pet": { "type": "Dog", "breed": 3 },
    "cave_choice": 1,
    "gender": "Male"
  },
  
  "npcs": {
    "abigail": { "name": "Abigail", "friendship": 0 },
    ...
  },
  
  "skills": {
    "farming": { "level": 0, "xp": 0 },
    "fishing": { "level": 0, "xp": 0 },
    ...
  },
  
  "recipes": {
    "cooking": [
      { "name": "Spaghetti", "known": true },
      ...
    ],
    "crafting": [
      { "name": "Chest", "known": true },
      ...
    ]
  },
  
  "special_flags": {
    "hasSkullKey": false,
    "hasClubCard": false,
    ...
  },
  
  "chests": [
    {
      "location": "Farm",
      "items": [
        { "name": "Wood", "count": 50 }
      ],
      "count": 1
    }
  ],
  
  "animals": [
    { "name": "...", "type": "Chicken" },
    ...
  ],
  
  "quests": [
    {
      "id": 1,
      "title": "...",
      "description": "...",
      "objective": "...",
      "completed": false
    }
  ],
  
  "secret_notes_seen": [1, 5, 12, ...],
  
  "collections": {
    "fish_caught": 0,
    "artifacts_found": 0,
    "minerals_found": 0,
    "crops_shipped": 0,
    "monsters_killed": 0
  },
  
  "stats": { ... },
  "events": [...],
  "mail": [...]
}
```

---

## 🛠️ Key Files

| File | Status | Purpose |
|------|--------|---------|
| `index.html` | In Progress | Main app (128KB monolithic) with all tools |
| `stardew-bridge.py` | ✅ Complete | Python bridge server, parses save → JSON |
| `manifest.json` | ✅ Complete | PWA manifest for web app mode |
| `CLAUDE.md` | ✅ Reference | Project brief + requirements |

---

## 📊 Git Commits

```
76381a5 Phase 3: Add tab structure for Hoard, Story Time, and Nightlock
d3b68c3 Fix special flags logic (syntax warning)
2e561ab Phase 2: Expand bridge to expose complete save file data
```

**Branch:** `claude/chat-memory-check-zny9Q`  
**Remote:** `cerealbishh/Stardew-Valley`

---

## 🎮 Testing Checklist

- [ ] Bridge runs and serves `/save` without errors
- [ ] iPhone can fetch bridge data via Safari
- [ ] All 15 tabs load placeholder content
- [ ] Checkbox clicks update localStorage
- [ ] Auto-refresh from bridge updates UI
- [ ] Dark mode toggle works on all new tabs
- [ ] Mobile layout looks good on iPhone 15
- [ ] Performance: No lag on scroll/tab switching

---

## 💾 How to Resume

1. Check out branch: `git checkout claude/chat-memory-check-zny9Q`
2. Bridge is ready at port 8742 (HTTPS)
3. HTML tabs are structured but empty — add render functions next
4. Start with Phase 4 (JavaScript rendering)
5. Reference `index.html` lines 290-350 for the new tab structure

---

## 🎨 Design System

- **Theme:** Y2K kawaii cottagecore pastel (see `:root` CSS vars)
- **Seasons:** Spring (pinks), Summer (greens/golds), Fall (oranges), Winter (blues)
- **Dark mode:** `html[data-dark="true"]`
- **Colors:** Pastels (pinks #e870b8, purples #b898e0, greens #58c080)
- **Typography:** System font stack, 13px base for content
- **Icons:** Emoji + pixel headers

---

## 📝 Notes

- Bridge polls save file every 5s, serves latest state
- localStorage stores checkbox state (keys: `sdv_t_*`, `sdv_par_*`, `sdv_c_*`)
- All 4 tools share same bridge data source
- Route 66 (daily checklist) already fully working
- No external dependencies — vanilla HTML/CSS/JS only
- Responsive for iPhone 15 Safari web app mode

