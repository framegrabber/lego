# Spec: Kids' LEGO Designer

Source of intent: [docs/intent/kids-lego-instructions.md](docs/intent/kids-lego-instructions.md).
Background research: [ai-lego-design-summary.md](ai-lego-design-summary.md).

## Objective

A kid (10+) describes a model in their own words. Claude designs it as a program, deterministic
checkers prove it is buildable, and the kid gets a 3D web preview plus step-by-step building
instructions they can follow with real bricks — without an adult fixing anything.

**Users.** Kids 10+ describe and build; an adult or facilitator runs the tool (home or workshop).

**User stories**

1. As a kid, I describe "a red racing car with a spoiler" and receive instructions I can build to
   the end without getting stuck.
2. As a kid, I see my model in 3D in a browser and can spin it before building.
3. As a kid, I ask for a change ("make the spoiler bigger") and get updated instructions.
4. As a facilitator, I run one command or Claude Code prompt per kid and hand over a link/PDF.

**Priority order:** buildability > likeness to description > everything else. Generation time is
not a constraint.

### Definition of "buildable" (hard gate)

A model is delivered only if **all** checks pass. Each check returns machine-readable JSON naming
offending part indices and stud coordinates so Claude can fix them.

| # | Check | Rule |
|---|---|---|
| B1 | Valid parts | Every part number exists in the LDraw library and in the supported vocabulary; every color is a valid LDraw color code. |
| B2 | No collisions | No two parts occupy the same volume (occupancy grid at 1 stud × 1 plate height). |
| B3 | Connected | The stud/anti-stud connection graph of the finished model is a single component. |
| B4 | Step-wise connected | After every step, all placed parts form one connected component (or attach to the baseplate). No step introduces a part that only connects to parts from later steps. |
| B5 | Step-wise insertable | Every part in a step can be pressed onto its connections vertically (from above, or from below for underside attachment) without passing through already-placed parts. |
| B6 | Step size | Each step adds at most 6 parts (configurable); sub-builds are allowed and are checked the same way. |
| B7 | Stable (heuristic, v1) | No part or sub-structure is held only by a single 1×1 stud connection while supporting other parts; cantilevers beyond a configurable overhang are flagged. Full force-based analysis (StableLego-style) is a later upgrade. |

B1–B6 are exact for the v1 vocabulary. B7 is a heuristic and may produce warnings rather than
failures; the threshold is an open question.

### Likeness (soft gate)

Claude inspects renders (front / side / top / iso) against the description and either accepts or
revises. Not machine-checked; evaluated by humans on the eval set.

## Capability map

| Module id | Responsibility | Depends on |
|---|---|---|
| `parts` | Supported part vocabulary: LDraw id, footprint in studs, height in plates, stud/anti-stud positions; LDraw color table. | LDraw library |
| `dsl` | Python API in stud coordinates (`brick`, `plate`, `step`, `submodel`) that Claude writes; produces an in-memory model. | `parts` |
| `ldraw` | Serialize model → `.ldr` / `.mpd` with `0 STEP` and submodels; parse back for round-trips. | `dsl` |
| `check` | B1–B7 checks over the in-memory model; JSON report. | `parts`, `dsl` |
| `render` | Headless PNG renders of a model or a single step. | `ldraw` |
| `preview` | Static web page (three.js `LDrawLoader`) showing the model with a step slider (`buildingStep` / `numBuildingSteps`). | `ldraw` |
| `skill` | Claude Code skill: prompt → DSL program → build → check → render → fix loop → deliver. | all above |
| `manual` (later) | Printable PDF via LPub3D batch mode. | `ldraw` |

Build order: `parts` → `dsl` → `ldraw` → `check` (B1–B3) → `render` → `skill` (first loop) →
`check` (B4–B7) → `preview` → `manual`.

### v1 part vocabulary

Basic bricks and plates, axis-aligned, rotations in 90° steps:

- Bricks: 1×1 (3005), 1×2 (3004), 1×4 (3010), 2×2 (3003), 2×4 (3001)
- Plates: 1×1 (3024), 1×2 (3023), 1×4 (3710), 2×2 (3022), 2×4 (3020)
- Baseplate (optional): 32×32 (3811)

Extension (after v1 passes the eval set): slopes, tiles, round bricks, wheels. Each new part must
declare its connection geometry before the checker accepts it.

## Tech Stack

- Python 3.14, managed with `uv` (0.9.x); package `lego` in `src/lego/`
- Dev tooling: `basedpyright` (types), `ruff` (lint/format), `pytest`, `debugpy`
- LDraw parts library (`complete.zip`, ~80 MB) downloaded to `ldraw/` (gitignored)
- Renderer: LDView or LeoCAD CLI — to be decided in the first spike (macOS headless behaviour
  unverified)
- Preview: static HTML + three.js `LDrawLoader`, served locally
- Later: LPub3D for PDF manuals

## Commands

Existing:

```sh
uv sync                     # install deps
uv run pytest               # tests
uv run ruff check .         # lint
uv run ruff format .        # format
uv run basedpyright         # type check
```

Planned CLI (names fixed here, implemented per plan):

```sh
uv run lego build models/car.py -o out/car.mpd    # DSL program → LDraw
uv run lego check out/car.mpd --json              # B1–B7 report, exit 1 on failure
uv run lego render out/car.mpd -o out/car/        # front/side/top/iso PNGs
uv run lego render out/car.mpd --step 5 -o out/   # single step
uv run lego preview out/car.mpd                   # serve web preview, print URL
uv run lego setup                                 # download LDraw library, locate renderer
```

## Project Structure

```
src/lego/           → package
  parts.py          → vocabulary + colors
  dsl.py            → model-building API
  ldraw.py          → .ldr/.mpd writer/reader
  check/            → one module per check family (collision, connectivity, steps, stability)
  render.py         → renderer wrapper
  cli.py            → `lego` command
web/                → static preview page
models/             → example DSL programs (incl. deliberately broken ones for tests)
evals/prompts.md    → fixed eval prompts
tests/              → pytest
.claude/skills/lego-designer/ → the Claude Code skill
docs/intent/        → confirmed intents
ldraw/, out/        → gitignored: parts library, generated output
```

## Code Style

The DSL is what Claude writes, so it must be short and unambiguous. Coordinates are in studs
(x, z) and plates (y, upward); the compiler converts to LDraw units (20 LDU per stud, 8 LDU per
plate, LDraw −Y is up).

```python
from lego.dsl import Model

m = Model("racing car")

with m.step():
    m.plate("2x4", x=0, z=0, y=0, color="black")
    m.plate("2x4", x=0, z=4, y=0, color="black")

with m.step():
    m.brick("2x4", x=0, z=2, y=1, color="red")   # spans z 2..6: bridges both plates

m.save("out/car.mpd")
```

Conventions: ruff defaults with line length 100; full type hints, basedpyright `standard` clean;
dataclasses for model data; checks are pure functions `model → Report`.

## Testing Strategy

- `pytest`, tests in `tests/`, deterministic, no network (LDraw library required for B1 tests;
  skip with a clear message if absent).
- **Checker tests are the core**: each check gets a passing model and a minimal failing model
  (floating brick, overlapping bricks, step that attaches to a future part, step blocked from
  above, single-1×1-stud cantilever). These encode the buildability contract.
- Round-trip tests: DSL → `.mpd` → parse → same parts/positions/steps.
- Render and preview are verified by running them (smoke), not by image-diff tests.
- **Eval set**: ~10 fixed prompts in `evals/prompts.md`; per run record pass/fail of B1–B7,
  part count, and a human likeness score (1–3).

## Boundaries

- **Always:** run `pytest`, `ruff check`, `basedpyright` before committing; keep checks
  deterministic; every check failure names parts and coordinates; never deliver a model that
  fails B1–B6.
- **Ask first:** adding runtime dependencies (e.g. pyldraw3, StableLego, Gurobi); expanding the
  part vocabulary; changing the B1–B7 definitions; anything that installs system software.
- **Never:** commit the LDraw library or generated output; weaken a check to make a model pass;
  require a commercial license (e.g. Gurobi) for the default path.

## Success Criteria

1. `lego check` correctly classifies every model in the test suite (all good models pass, every
   deliberately broken model fails with the right check and part index).
2. On the eval set, the skill delivers a model that passes B1–B6 for ≥ 8 of 10 prompts, within any
   number of fix iterations; failures are reported, never silently delivered.
3. Delivered models are 50–400 parts.
4. The web preview shows the model and steps through it with a slider.
5. **Physical test:** at least 3 delivered models are built from real bricks by someone following
   only the instructions, without getting stuck.

## Open Questions

1. **Instruction format for kids:** is the web step player enough, or is a printable PDF (LPub3D)
   needed for workshops? Spec assumes web first, PDF later.
2. **B7 threshold:** should stability issues block delivery or only warn in v1?
3. **Renderer:** LDView vs. LeoCAD on macOS — decided by spike.
4. **Vocabulary:** is bricks + plates enough for likeness kids accept, or should slopes be in v1?
5. **Baseplate:** always build on a baseplate (simplifies B4) or allow free-standing models?
