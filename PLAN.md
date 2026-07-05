# Stardew Valley Tracker — Build Plan v2 (durable memory)

> Saved so we can resume after the chat is deleted. Everything the assistant needs
> to pick up from where we left off is in this file. **This is the source of truth.**

## Resume-from status (2026-07-05)

- **Plan status:** approved by user (v2, includes Phase 6 Y2K kawaii theme overhaul).
- **Branch:** `claude/stardew-valley-tracker-plan-Didks` (already checked out).
- **Implementation status:** **not started.** No code changes yet. Working tree clean at time of save.
- **What to do next:** begin **Phase 1 — Foundation** (see checklist below). Suggested first commit boundary: bridge changes (`schema_version` + `CC_BUNDLE_MAP` stubs) as one commit; index.html foundation (namespace + visibility polling + tri-state indicator) as a second commit; service-worker cache bump as a third. Then start Phase 2 slice.
- **Blocker to flag to user before Phase 2:** we do not have access to a real save XML in this sandbox (the bridge's save path is `/Users/roohi/.config/StardewValley/Saves/Hoedown_203853699/...`, a Mac path). `fixtures/save.xml` will need to be produced by the user (redacted export of their real save) before offline dev tests can run. A hand-fabricated minimal fixture will not exercise real bundle IDs and will mislead the Phase 2 acceptance criteria.

## Context

The "Stardew or Dew Not" tracker is a single-page iPhone web app (`index.html`, ~308KB — note: NOT ~60KB as the plan initially said; already close to the 250KB budget) hosted on GitHub Pages, paired with a Python bridge (`stardew-bridge.py`) that watches a local save file and serves parsed JSON over HTTPS. Only one of four tools (**Route 66**) is fully built; the other three (**The Hoard**, **Story Time**, **Big Daddy Nightlock**) are "Coming Soon" placeholders at `index.html:289–338`.

The original plan proposed building all three tools layer-by-layer (all bridge fields → all HTML → all sync). Review surfaced several blockers: writable save-file sync risks corruption, a "6th skill" that doesn't exist in vanilla Stardew, a "time of day" field that isn't in the save, gaps in `CC_BUNDLE_MAP` (9 missing bundle IDs), and iOS Safari background-polling that silently fails. This plan replaces it with a vertical-slice approach grounded in the patterns Route 66 already established.

**Goal:** ship a production-ready iPhone web app that auto-syncs from the save file via the bridge, reusing every existing pattern (rendering, state, theming, PWA caching) instead of inventing parallel ones.

## Size budget correction

Plan text said `<250KB ungzipped`. `index.html` is already **~308KB** (`wc -c index.html` = 308893). Options when resuming:
1. Raise the budget to `<450KB` and accept the current state as baseline.
2. Split CSS/JS into separate files before adding any Hoard/Story/Nightlock code (and update `service-worker.js` cache list).

**Recommend option 2** — the current file will keep growing across Phases 2–5 and gzip won't save the parse-time cost on iPhone Safari. Do the split in Phase 1.

## Locked Decisions

| Decision | Choice |
|---|---|
| Save-file sync direction | **Read-only bridge** + localStorage mirror keyed by save hash |
| Build order | **Vertical slice** (Junimo Feed first, end-to-end) |
| Scope | **Build everything** (no Y1-only gate) |
| "Never Tell Me the Odds" tab | Lives under **Story Time** (Tab 6); Nightlock drops to 8 tabs |

## Spec Corrections (from code audit — must land in code)

1. **Skills = 5**, not 6. `stardew-bridge.py:25` confirms (`Farming/Fishing/Foraging/Mining/Combat`). Luck has no vanilla UI; show daily luck modifier as a Route 66 readout only.
2. **The Tardis stays separate** from Davy Jones' Locker. CLAUDE.md spec lists both; merging produces a giant scroll.
3. **No "time of day."** Stardew stores time in memory only, never in the save. Drop from Route 66 and Nightlock.
4. **`CC_BUNDLE_MAP` is missing IDs:** 12, 16, 18, 22, 25, 27, 28, 29, 30 (`stardew-bridge.py:113–140`). Fix in Phase 1 — but note: this codebase uses internal renumbering, not canonical Stardew CC IDs, so we cannot fabricate mappings without a real save to inspect. Add TODO stubs in Phase 1, verify against a real save during Phase 2.
5. **Covenant of the Rock** appears in two tools by design — implement as one shared component with two mount points, single source of truth.

## Architecture Rules

- **Bridge response gains `schema_version`** (int). Tracker checks on fetch; mismatch → soft yellow banner.
- **localStorage namespace:** `sdv:<save_hash>:<key>` where `save_hash = farmName + seed + Y1 start day`. Migration scaffold on version bump. Reuse the existing `lsSet/lsGet/lsTgl` helpers (`index.html:1011–1013`). **Backward-compat note:** existing Route 66 keys (`sdv_t_*`, `sdv_par_*`, `sdv_c_*`, `sdv_tab`, `sdv_rsub`, `sdv_dark`, `sdv_ip`) stay as-is for this save; only new tabs use the namespace. Or migrate all — pick one before Phase 1 lands.
- **Polling = visibility-based, not interval-based.** Replace the chained `setTimeout(fetchBridge, 30000)` at `index.html:1157` with: fetch on `visibilitychange → visible`, on focus, and on manual refresh. iOS Safari throttles/pauses background tabs; the current pattern silently lies when the app is backgrounded.
- **Sync indicator (existing `#bridge-dot` at `index.html:269` — actually rendered at `index.html:237`):** extend to 🟢 fresh (<30s) / 🟡 stale (30s–2min) / 🔴 dead (>2min or error). Show `last sync HH:MM:SS`. Add a lightweight `setInterval` (5s) that only recomputes the dot color from `S.lastFetchMs` — it does NOT fetch.
- **File size budget:** `index.html` target **<250KB ungzipped** — see "Size budget correction" above. Split before Phase 2 lands.
- **Lazy mount:** each tool's DOM built on first tab activation, not at page load. Mirror Route 66's `renderRoute()` fragment-based pattern (`index.html:1053–1085`).
- **Fixtures:** commit a redacted save XML to `fixtures/save.xml` — **user action required**, see resume-from status.
- **Service worker contract:** app shell + Route 66 cached for offline. Bridge JSON is online-only; offline shows "last known" with stale badge. Bump cache version on every release.

## Tab Inventory (final)

### 🔵 Route 66 (existing — additive only)
- Add weather glyph (☔/☀️/⚡/❄️) and daily luck modifier next to each day card.

### 🔴 The Hoard (5 tabs)
1. 🌽 **Junimo Feed** — CC bundles by room **← SLICE #1**
2. 📋 Take This Job And Shove It — quests
3. ✨ Omg Look Something Shiny — museum (X/95)
4. 🔨 I Made It Myself — buildings + location unlocks
5. 💌 Covenant of the Rock — NPC hearts/birthdays (shared component)

### ✨ Story Time (6 tabs)
1. 🎬 Previously On — cutscenes
2. 📜 The Lore — world flags + secret notes
3. 💌 Covenant of the Rock — shared component, romance focus
4. 📋 Main Quest — journal
5. 🏆 Milestones — Grandpa criteria (badge: "Y3 evaluation")
6. 🎲 Never Tell Me the Odds — stats, sleep records, professions readout, distance

### 💜 Big Daddy Nightlock (8 tabs)
1. 🌀 The Tardis — backpack (36 slots)
2. 🏴‍☠️ Davy Jones' Locker — chests across 87 locations + cash
3. 👗 Fit Check — appearance + equipment
4. 📈 Skillmaxxing — **5 skills** + XP bars + profession choices
5. 🌿 Touching Grass — friendship + romance + marriage state
6. 📺 I Watched One (1) Youtube Video — cooking + crafting recipes
7. 🐄 The Supporting Cast — animals + pets + farm layout
8. 🛡️ Plot Armor — special flags + Holocron collections

## Build Phases

### Phase 1 — Foundation (one-time, before any tab work)
- [ ] Ask user to export a redacted `fixtures/save.xml` OR commit a minimal hand-crafted stub with a comment flagging that real bundle IDs are unverified.
- [ ] Add `schema_version: 1` to bridge `/save` response (`stardew-bridge.py:152`).
- [ ] Add stubs for `CC_BUNDLE_MAP` IDs 12, 16, 18, 22, 25, 27, 28, 29, 30 with `# TODO: verify against real save` comments (don't fabricate items).
- [ ] Decide: split `index.html` into `index.html + app.css + app.js` OR raise size budget.
- [ ] Wire save-hash + localStorage namespace + migration scaffold in `index.html`.
- [ ] Replace `setTimeout(fetchBridge, 30000)` polling with visibility/focus-based triggers.
- [ ] Extend `#bridge-dot` to tri-state (fresh/stale/dead) with `last sync` readout. Add CSS classes `.stale` (yellow #e0a020) and `.dead` (red #e06868).
- [ ] Bump service worker cache to `hoedown-v6`. Add any new file names to `ASSETS` list.

### Phase 2 — Vertical Slice: Junimo Feed
- Bridge: emit `cc_bundles[]` with `{id, room, name, slots: [{item, have, need}], completed}`.
- HTML: replace `#p-hoard` "Coming Soon" with tab nav + Junimo Feed panel; mirror Route 66 sub-panel pattern.
- JS: `renderJunimo()` using fragment builder; event-delegation reads (no toggles — CC state is game-owned).
- CSS: reuse `.card / .panel / .nav-btn` plus existing season palette tokens.
- **Acceptance:** all 6 rooms render from `fixtures/save.xml` offline; bundles auto-check on bridge update; stale badge appears when bridge is down; total assets under budget.

### Phase 3 — Remaining Hoard tabs (apply slice lessons)
Quests → Museum → Unlocks → Covenant (build shared component here).

### Phase 4 — Story Time tabs
Previously On → Lore → Covenant (reuse) → Main Quest → Milestones → Never Tell Me the Odds.

### Phase 5 — Nightlock tabs
Tardis → Davy Jones' → Fit Check → Skillmaxxing → Touching Grass → Recipes → Supporting Cast → Plot Armor.

### Phase 6 — Y2K Kawaii Cottagecore Theme Overhaul

Target aesthetic from CLAUDE.md: **Y2K kawaii cottagecore pastel retro** — soft pinks, mints, lavenders, bubbly UI, pixel headers. The existing palette has the right starting point (`--hdr-a`/`--hdr-b` gradients, `#fdf0f5` background — actually `#fde8f4`, and season tokens) but reads as "soft pastel" rather than "Y2K bubbly retro." This phase pushes it the rest of the way.

**Token expansion** (`:root` in `index.html`):
- Add core kawaii palette: `--pink-100/300/500`, `--mint-100/300/500`, `--lavender-100/300/500`, `--cream`, `--cherry`.
- Add Y2K glow tokens: `--glow-pink`, `--glow-mint`, `--shadow-bubble` (soft drop shadow), `--shadow-inset-glow`.
- Add gradient presets: `--grad-bubble` (pink→lavender→mint), `--grad-holo` (subtle holographic shimmer for accent strips), `--grad-cherry` (action buttons).
- Re-map existing `--acc/--acc2/--hdr-a/--hdr-b` to draw from the new palette so all four tools inherit it consistently.

**Typography**:
- Add a pixel display font (e.g., `"Press Start 2P"` from Google Fonts, or inline a base64 of a small pixel font to keep offline-PWA-friendly) for `.panel-title` and section headers — matches the "pixel headers" spec.
- Body text stays in the current sans stack for legibility on iPhone.
- Add a fallback chain so PWA works offline if Google Fonts is blocked.

**Component restyling** (apply to `.card / .panel / .nav-btn / .route-day / .task-row / .bridge-status / .cs-tab`):
- Bubble radii: bump `--r` from 16px to 20px; add 24px variant for top-level cards.
- Soft inset highlights (`box-shadow: inset 0 1px 0 rgba(255,255,255,.6)`) to give buttons a glassy bubble look.
- Pastel borders with subtle 1px gradient (use `border-image` for the holographic shimmer on active tabs).
- Replace flat checkbox squares with rounded heart/star toggles (CSS-only, no asset files).

**Pixel art accents**:
- Mirror the inline `junimoSVG` pattern (`index.html:1182`) to add small pixel SVGs as section decorations: heart, star, sparkle, mushroom, leaf, bow. Inline string literals — no asset files — keeps PWA offline-friendly.
- Sparkle particles on checkbox completion (extend existing `spawnParticles` at `index.html:1201`).

**Dark mode parity**:
- Re-derive `html[data-dark="true"]` overrides (`index.html:34–37`) from new tokens. Dark mode = "midnight kawaii": deep plum background, neon mint/pink accents preserved.
- Verify contrast ratios ≥4.5:1 for body text in both modes.

**Mobile polish**:
- `env(safe-area-inset-*)` padding on `<main>` and `<nav>` for iPhone 15 notch + home bar (partially present: `#ticker` has `padding-top: env(safe-area-inset-top)`, `#nav` has `padding-bottom: env(safe-area-inset-bottom)`; verify others).
- Tap targets audited at ≥44×44px.
- `-webkit-tap-highlight-color: transparent` + custom tap feedback (scale 0.97 on `:active`).
- Viewport meta confirmed: `viewport-fit=cover` (already present at `index.html:5`).

**Acceptance**:
- All four tools render in the new theme with consistent palette inheritance — no tool feels "off-brand."
- Pixel header font loads online; falls back gracefully offline without layout shift.
- Dark mode passes contrast checks.
- Total asset size under the budget agreed in Phase 1.
- Smoke test on iPhone 15 Safari + PWA standalone mode: no horizontal scroll, no notch overlap, no tap-target failures.

## Per-Tab Acceptance Criteria (template)

Each tab is "done" when:
- [ ] Renders from `fixtures/save.xml` without live bridge.
- [ ] Renders correctly when bridge is offline (last-known + stale badge).
- [ ] Auto-derived fields update on visibility/refresh.
- [ ] User-toggled fields (where applicable) persist in localStorage and survive save reload.
- [ ] iPhone 15 Safari smoke test: scrolls smoothly, no horizontal overflow, tap targets ≥44px.
- [ ] Dark mode (`html[data-dark="true"]`) renders correctly.

## Critical Files

- `/home/user/Stardew-Valley/index.html` — all UI work. Reuse patterns from `index.html:1053–1085` (rendering), `1011–1013` (state helpers), `1138–1158` (bridge fetch), `1211–1269` (event delegation).
- `/home/user/Stardew-Valley/stardew-bridge.py` — expand `parse_save()` (`stardew-bridge.py:145`) field-by-field per slice. Add `schema_version`.
- `/home/user/Stardew-Valley/service-worker.js` — bump `hoedown-v5` cache name on each release; update asset list (`service-worker.js:2–7`) if files are added.
- `/home/user/Stardew-Valley/update-checker.js` — no changes expected; existing focus/visibility polling will pick up new HTML automatically.
- `/home/user/Stardew-Valley/fixtures/save.xml` — **NEW**, redacted save XML for offline dev/tests. See resume-from status.

## Patterns to Reuse (do NOT re-invent)

| Need | Existing pattern | Location |
|---|---|---|
| Render a list of cards | `renderRoute()` — `documentFragment` + `createElement` loop | `index.html:1053–1085` |
| Persist a boolean | `lsSet / lsGet / lsTgl` helpers | `index.html:1011–1013` |
| Click handlers | Single document-level event-delegation listener; `data-*` attrs carry IDs | `index.html:1211–1269` |
| Tab navigation | `.nav-btn[data-tab]` switching `.panel.active` | `index.html:343–347, 61–63, 71–79` |
| Theming | `:root` CSS custom properties + `html[data-season]` overrides + `html[data-dark]` | `index.html:34–37` |
| Bridge fetch + status UI | `fetchBridge()` with `AbortSignal.timeout(8000)`, `#bridge-dot` indicator | `index.html:1138–1158, 237, 55–57` |
| Inline pixel art | SVG string literal injected as `innerHTML` | `index.html:1182` (junimoSVG) |
| Particle burst | `spawnParticles(el)` | `index.html:1201` |

## Verification

**Per phase:**
1. Open `index.html` locally with `fixtures/save.xml` mocked into the bridge fetch path — confirm tab renders offline.
2. Run `python3 stardew-bridge.py` with the real save; load app on iPhone 15 Safari over Tailscale HTTPS. Confirm `#bridge-dot` goes green and the tab populates within 5s.
3. Lock iPhone for 3+ minutes, unlock — confirm dot goes yellow then refreshes to green within 2s of becoming visible.
4. Kill bridge process — confirm dot goes red within 2 min, app remains usable with last-known state.
5. Toggle dark mode — confirm new tab honors `html[data-dark="true"]` with the kawaii dark palette (deep plum + neon pastel accents).
6. Check `wc -c index.html` (+ CSS/JS if split) — confirm under the agreed budget. If exceeded, split before merging.
7. **Theme verification (post-Phase 6):** all four tools share the Y2K kawaii palette (pinks/mints/lavenders); pixel header font renders on `.panel-title`; sparkle particles fire on checkbox completion; iPhone 15 PWA standalone mode shows no notch overlap and no horizontal scroll.

**Slice #1 (Junimo Feed) success criterion:** open the Hoard tab on the phone, see all 6 CC rooms with each bundle's per-slot have/need state matching what's actually in the save's `bundles` node — including the 9 bundles that were previously missing from `CC_BUNDLE_MAP`.

## Known Risks (acknowledged, not blocking)

- `previousActiveDialogueEvents` semantics need verification against a real save before Covenant of the Rock can correctly show historical events.
- Animal names are stored deep in `Building/indoors/animals`; XPath confirmation needed during Supporting Cast slice.
- Mail IDs are opaque strings — need a curated `MAIL_LABELS` map similar to `HOARD_ITEM_MAP` or the Story Time mail view will be unreadable.
- Self-signed cert (`stardew-bridge.py:19–20`) only works after `.mobileconfig` install on iPhone — pre-existing setup, not in scope.
- `CC_BUNDLE_MAP` uses internal renumbering, not canonical Stardew IDs. Cannot fabricate missing bundles without a real save to inspect.

## When resuming in a fresh chat

Paste this to bootstrap the new session:
> "Read `PLAN.md` in the repo, then continue Phase 1 of the build plan. The branch `claude/stardew-valley-tracker-plan-Didks` is already checked out."
