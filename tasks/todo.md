# Tasks

Plan: [plan.md](plan.md). Standard verification for every task: `uv run pytest`,
`uv run ruff check .`, `uv run basedpyright` all clean.

## Phase 0 — First picture

### Task 1: `lego setup` — parts library and headless browser
**Description:** CLI skeleton (`cli.py`, `argparse`) with a `setup` command that downloads the
LDraw `complete.zip` into `ldraw/` (skip if present) and runs Playwright's Chromium install. Add
`playwright` as a runtime dependency.
**Acceptance:**
- [x] `uv run lego setup` leaves `ldraw/parts/3001.dat` and `ldraw/LDConfig.ldr` on disk
- [x] Re-running is a no-op and says so
- [x] Failure (network, bad zip) exits non-zero with a clear message
**Verify:** run it twice on a clean checkout; check files exist.
**Depends on:** none · **Files:** `pyproject.toml`, `src/lego/cli.py`, `src/lego/setup.py`, `src/lego/__init__.py` · **Size:** S

### Task 2: Web preview of a hand-written model
**Description:** `web/index.html` + vendored three.js (`LDrawLoader`, `OrbitControls`). Loads a
model URL from the query string, orbit camera, step slider using `buildingStep` /
`numBuildingSteps`. `lego preview FILE` serves `web/`, `ldraw/` and the model's directory on
localhost and prints the URL. Add `models/hello.ldr` (hand-written, ~10 parts, 2 steps).
**Acceptance:**
- [x] `uv run lego preview models/hello.ldr` prints a URL; the page shows the model with real part geometry and colors
- [x] Slider steps through the 2 steps
- [x] Works with network disabled (no CDN) — 0 external requests; hello.ldr loads in 0.1 s
**Verify:** open in browser, screenshot; note load time.
**Depends on:** 1 · **Files:** `web/index.html`, `web/main.js`, `web/vendor/…`, `src/lego/preview.py`, `models/hello.ldr` · **Size:** M

### Task 3: `lego render` — headless screenshots
**Description:** Playwright loads the preview page with `?view=front|side|top|iso&step=N`, waits
for a "ready" flag set by the page, saves PNGs.
**Acceptance:**
- [x] `uv run lego render models/hello.ldr -o out/hello/` writes 4 PNGs showing the model
- [x] `--step 1` renders only step 1's parts
- [x] Clear error when the model fails to load (no blank PNG)
**Verify:** run it; view the PNGs.
**Depends on:** 2 · **Files:** `src/lego/render.py`, `src/lego/cli.py`, `web/main.js` · **Size:** S

### Checkpoint: First picture
- [x] Hand-written model visible in browser and as PNGs
- [ ] Review with human

## Phase 1 — Model core

### Task 4: Part vocabulary and DSL
**Description:** `parts.py`: bricks + plates from the spec (footprint, height in plates, stud and
anti-stud cells) and the LDraw color table parsed from `LDConfig.ldr` (names → codes).
`dsl.py`: `Model` with `brick`, `plate`, `step()` context manager, integer grid positions,
`rot` in {0, 90, 180, 270}; rejects unknown part names/colors/rotations immediately.
**Acceptance:**
- [x] The spec's code-style example runs unchanged (after fixing its floating brick — see SPEC.md)
- [x] Invalid input (unknown part, color, non-integer position, rot=45) raises with a message naming the call
- [x] Rotated footprints are correct (2×4 at rot=90 covers 4×2 cells)
**Verify:** unit tests for footprints/rotations and validation.
**Depends on:** 1 · **Files:** `src/lego/parts.py`, `src/lego/dsl.py`, `tests/test_dsl.py` · **Size:** M

### Task 5: LDraw writer/reader and `lego build`
**Description:** `ldraw.py` converts the model to `.mpd` (20 LDU/stud, 8 LDU/plate, −Y up,
rotation matrices, `0 STEP` between steps) and parses it back. `lego build PROGRAM -o FILE` runs a
DSL program. Add `models/wall.py` (multi-step example).
**Acceptance:**
- [x] Round-trip: DSL → `.mpd` → parse gives identical parts, positions, rotations, colors, steps
- [x] `lego build models/wall.py -o out/wall.mpd` then `lego preview out/wall.mpd` shows correctly placed parts and steps
**Verify:** round-trip test; visual check in preview and with `lego render`.
**Depends on:** 3, 4 · **Files:** `src/lego/ldraw.py`, `src/lego/cli.py`, `models/wall.py`, `tests/test_ldraw.py` · **Size:** M

### Checkpoint: Model core
- [x] DSL program → `.mpd` → preview with steps works end to end

## Phase 2 — Checker core + first Claude loop

### Task 6: Check framework, B1 valid parts, B2 collisions
**Description:** `check/` package with `Report`/`Issue` types and JSON output; B1 (part file exists
in `ldraw/parts`, color valid), B2 (occupancy grid; overlapping cells reported with both parts).
`lego check FILE [--json]`, exit 1 on failure. Fixture models in `models/broken/`.
**Acceptance:**
- [ ] Good models pass; `overlap.py` fails B2 naming both part indices and the cell
- [ ] JSON output is stable and documented in the module docstring
**Verify:** tests per fixture; run `lego check` on good and broken models.
**Depends on:** 5 · **Files:** `src/lego/check/__init__.py`, `check/report.py`, `check/basic.py`, `src/lego/cli.py`, `tests/test_check_basic.py` · **Size:** M

### Task 7: B3 connectivity
**Description:** Build the connection graph (stud cell of A under anti-stud cell of B, B directly on
top). Report every component not attached to the main one (baseplate or largest component).
**Acceptance:**
- [ ] `floating.py` (brick in the air) fails B3 naming the part
- [ ] Two parts touching only side-by-side are not connected
- [ ] A brick bridging two towers connects them
**Verify:** tests per case.
**Depends on:** 6 · **Files:** `src/lego/check/connectivity.py`, `tests/test_connectivity.py`, `models/broken/…` · **Size:** S

### Task 8: Claude Code skill v1 and eval baseline
**Description:** `.claude/skills/lego-designer/SKILL.md`: write DSL program → build → check →
render → inspect → fix, until B1–B3 pass and Claude accepts the renders; DSL reference inside the
skill. `evals/prompts.md` with 10 prompts and a results table.
**Acceptance:**
- [ ] 3 eval prompts run end to end; results (pass/fail, iterations, parts, likeness 1–3) recorded
- [ ] Notes on which report messages Claude misread, with fixes applied
**Verify:** run the skill on the 3 prompts; inspect outputs in the preview.
**Depends on:** 7 · **Files:** `.claude/skills/lego-designer/SKILL.md`, `evals/prompts.md` · **Size:** M

### Checkpoint: First loop
- [ ] Claude produces connected, collision-free models from prompts
- [ ] Review baseline with human before investing in step checks

## Phase 3 — Instruction checks

### Task 9: B4 step-wise connected and B6 step size
**Description:** Re-run connectivity after each step (anchor: baseplate if present, else step 1's
parts). B6: max parts per step (default 6, configurable).
**Acceptance:**
- [ ] `future_support.py` (part in step 2 only connected via a step-3 part) fails B4 naming part and step
- [ ] Free-standing model with connected step 1 passes
- [ ] Step with 7 parts fails B6
**Verify:** tests per case.
**Depends on:** 7 · **Files:** `src/lego/check/steps.py`, `tests/test_steps.py`, `models/broken/…` · **Size:** S

### Task 10: B5 step-wise insertable
**Description:** For each part, it must be pressable vertically onto its connections: the column of
cells above (if it connects downward) or below (if it connects upward) its footprint must be free
of already-placed parts.
**Acceptance:**
- [ ] `blocked.py` (brick inserted under an existing overhang from above) fails B5
- [ ] Underside attachment from below with free space passes
- [ ] Skill updated to run B4–B6
**Verify:** tests; re-run 3 eval prompts.
**Depends on:** 9 · **Files:** `src/lego/check/steps.py`, `tests/test_steps.py`, `.claude/skills/lego-designer/SKILL.md` · **Size:** S

### Checkpoint: Instructions
- [ ] Eval prompts pass B1–B6; human steps through one model in the preview

## Phase 4 — Stability

### Task 11: B7 heuristic score and thresholds
**Description:** Per-part score from minimum stud cut to ground vs. carried load and lever arm,
evaluated after every step; tipping term for free-standing models; `warn`/`fail` thresholds
(0.6 / 0.3) configurable; verdict ok/fragile/unstable in the report.
**Acceptance:**
- [ ] Single 1×1-stud cantilever carrying a tower scores < 0.3
- [ ] Solid wall scores ≥ 0.6
- [ ] Free-standing model with centre of mass outside its footprint is unstable
**Verify:** tests per case; scores of eval models look plausible.
**Depends on:** 9 · **Files:** `src/lego/check/stability.py`, `tests/test_stability.py`, `models/broken/…` · **Size:** M

### Task 12: Fragile parts in the preview
**Description:** `lego build` writes check results next to the `.mpd`; preview highlights fragile
parts with a "hold carefully" marker at their step. Skill blocks on unstable, tries to improve
fragile.
**Acceptance:**
- [ ] Fragile fixture shows highlighted parts at the right step
**Verify:** visual check in browser.
**Depends on:** 11 · **Files:** `src/lego/cli.py`, `web/main.js`, `.claude/skills/lego-designer/SKILL.md` · **Size:** S

## Phase 5 — Slopes

### Task 13: Slopes and inverted slopes
**Description:** Add 3040, 3039, 3037, 3665, 3660 to `parts` with partial stud/anti-stud cells and
bounding-box occupancy; `m.slope("2x2", facing="north", …)` in the DSL; all checks use the part
data, no slope special cases in check code.
**Acceptance:**
- [ ] Nothing connects on a slope's sloped face; a brick on the back row connects
- [ ] Inverted slope connects only via its back-row anti-studs
- [ ] `facing` maps to the correct LDraw rotation (visually verified for all 4 directions)
**Verify:** tests; render a slope test model.
**Depends on:** 10, 11 · **Files:** `src/lego/parts.py`, `src/lego/dsl.py`, `tests/test_slopes.py`, `models/slopes.py`, `.claude/skills/lego-designer/SKILL.md` · **Size:** M

## Phase 6 — Validation

### Task 14: Full eval and physical builds
**Description:** Run all 10 eval prompts; build ≥ 3 delivered models from real bricks following
only the preview; calibrate B7 thresholds and B5 rules from what happened.
**Acceptance:**
- [ ] ≥ 8/10 prompts deliver models passing B1–B6 with B7 ≥ fail, 50–400 parts
- [ ] ≥ 3 physical builds completed without getting stuck (notes recorded)
**Verify:** results table in `evals/prompts.md`.
**Depends on:** 12, 13 · **Files:** `evals/prompts.md`, thresholds in `src/lego/check/stability.py` · **Size:** S

### Checkpoint: Complete
- [ ] All spec success criteria met
