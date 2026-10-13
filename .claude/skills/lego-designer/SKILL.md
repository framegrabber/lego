---
name: lego-designer
description: Designs a buildable LEGO model from a kid's description and delivers step-by-step web instructions. Writes a Python program against lego.dsl, then loops build → check → render → inspect → fix until every check passes and the renders look like the description. Use when asked to design, build or create a LEGO model, or to change an existing design ("make the wings bigger").
---

# LEGO Designer

You design LEGO models that a 10+ year old will build **from real bricks** by following the
generated steps. Priority order: **buildable first, looks like the description second.** A model
that fails a check is never delivered.

Run all commands from the repository root. If `ldraw/` is missing, run `uv run lego setup` once.

## Workflow

1. **Plan before coding.** Restate the description in one line. Decide the size (aim for
   50–200 parts), the footprint in studs, the colors, and the layers from the bottom up. Note
   which features carry the likeness (e.g. a lighthouse: tall, round-ish, red/white stripes, a
   lamp room on top).
2. **Write the program** at `models/designs/<slug>.py` (slug: lowercase, underscores). One
   module-level `Model`. Use loops and named constants; keep coordinates readable.
3. **Build:** `uv run lego build models/designs/<slug>.py` → writes `out/<slug>.mpd`.
   A `DesignError` names the file, line and call; fix it and rebuild.
4. **Check:** `uv run lego check out/<slug>.mpd --json`. Fix **every** issue. Each issue lists
   the parts by `index` (order of DSL calls), `step`, and the exact `call`, plus the grid cell
   `at` = `[x, y, z]`.
5. **Render:** `uv run lego render out/<slug>.mpd -o out/<slug>` writes
   `out/<slug>/<slug>-{front,side,top,iso}.png`; `--step N` writes `<slug>-<view>-stepN.png`.
   **Read all four images** and compare them to the plan. Also render a middle step
   (`--step N`) to see that the build grows sensibly. Fix anything that looks wrong or unlike
   the description, then go back to 3.
6. **Repeat 3–5** until the check passes and the renders match. There is no iteration limit, but
   if the same issue survives three attempts, step back and redesign that section.
7. **Deliver:** report the program path, the preview command `uv run lego preview
   out/<slug>.mpd` (don't run it yourself: it starts a server and blocks), part count, step
   count, the largest step, how many build/check/render iterations it took, and anything you are
   unsure about.

## The DSL

```python
from lego.dsl import Model

m = Model("lighthouse")

with m.step():                                   # every part belongs to a step
    m.plate("2x4", x=0, z=0, y=0, color="black")
    m.plate("2x4", x=0, z=2, y=0, color="black")

with m.step():
    m.brick("2x4", x=0, z=1, y=1, color="red")   # sits on top of both plates
```

### Coordinates (all integers)

- `x`, `z`: studs. `(x, z)` is the **min corner** of the part's footprint.
- `y`: plates, upward. `y` is the **bottom level** of the part. A plate is 1 level tall, a brick
  is **3** levels tall. Something sitting on a brick at `y=1` goes at `y=4`.
- An unrotated `AxB` part covers **B studs along x and A studs along z**: `2x4` → 4 wide (x),
  2 deep (z). `rot=90` or `rot=270` swaps that to A along x, B along z. Rotation never moves the
  min corner. `rot` must be 0, 90, 180 or 270.
- Negative coordinates are fine.
- Views: **front** looks at the low-z side (x increases to the right), **side** looks at the
  high-x side (low z on the left), **top** looks down, **iso** is front-right-above. For a
  vehicle or animal, put its length along x so the front view shows its profile.

### Parts (only these exist)

| Call | Sizes |
|---|---|
| `m.brick(size, x=, y=, z=, color=, rot=0)` | `1x1`, `1x2`, `1x4`, `2x2`, `2x4` |
| `m.plate(size, x=, y=, z=, color=, rot=0)` | `1x1`, `1x2`, `1x4`, `2x2`, `2x4` |

Colors: LDraw names, lowercase with underscores. Good kid palette: `red`, `blue`, `yellow`,
`green`, `black`, `white`, `orange`, `lime`, `tan`, `brown`, `light_bluish_grey`,
`dark_bluish_grey`, `dark_blue`, `dark_red`, `bright_pink`, `medium_azure`. See-through:
`trans_clear`, `trans_yellow`, `trans_red`, `trans_light_blue`. The full list is the
`!COLOUR` lines in `ldraw/LDConfig.ldr`.

### Steps

- `with m.step():` opens the next step; steps cannot be nested or empty.
- Build bottom-up: a part must sit on, or hang under, something placed in the **same or an
  earlier** step. **After every step, everything built so far must be one connected piece** —
  a kid can't hold two loose halves waiting for a later part to join them. The only exception
  is step 1: it may lay out several loose parts **on the model's bottom layer** (plates on the
  table), as long as step 2 joins them.
- Plan the order with that in mind: a base made of plates whose seams line up stays several
  loose pieces until something is stacked across the seams. Lay the bottom plates in step 1 and
  make sure step 2 locks all of them together. A base needing more than 6 bottom plates: put
  the rest in a later step and press them up from below under the top layer already built.
- Each part must be pressable straight down from above (nothing from an **earlier step** above
  its footprint) or straight up from below (nothing from an earlier step below it). Within a
  step the kid chooses the order, so parts of the same step never block each other.
- Keep steps small: **at most 6 parts** per step, ideally 2–4. Kids follow one step at a time.

## How parts connect (what the checker tests)

- **B1 valid parts**: part exists in the library, color is valid.
- **B2 no collisions**: no two parts share a grid cell (1 stud × 1 stud × 1 plate).
- **B3 connected**: every part is joined to the rest of the model by studs. Part B connects to A
  when B's bottom level equals A's top level (`A.y + height`) **and** their footprints overlap by
  at least one stud. **Parts side by side are NOT connected**, even when touching. To join two
  neighbors, put a part across them on the layer above or below.
- **B4 step-wise connected**: after every step, everything built so far is one piece (step 1
  may leave loose parts on the bottom layer only). Each loose piece is reported once, with the
  step and part that finally join it: move that joining part (or another bridge) into the step
  where the piece appears. **Fix the earliest B4 issue first**; later ones often follow from it.
- **B5 insertable**: no part is wedged between parts from earlier steps above and below it. The
  usual fix: put the wedged part in the **same step** as the part above it (a part hanging
  under something goes in the same step as that thing).
- **B6 step size**: at most 6 parts per step.
- **Stability is not checked yet**: overlap joints like a brick wall, avoid parts held by a
  single stud that carry weight, overhang at most 2 studs past the support, and hold every
  overhanging part by at least 2 studs.
- **No sub-assemblies yet**: everything is built as one growing piece. Build legs, arms or
  wings outward from the body instead of as separate pieces joined later.

## Design tips

- Two plate layers only lock together if **every top plate overlaps at least two bottom
  plates**. A plate sitting exactly on a same-sized plate is always a separate island. If the
  plates can't tie a base together on their own, put the first body bricks in the same steps.
- Two legs (or towers) can't be built side by side and joined later. Build one leg up, add a
  part that spans both leg positions, then hang the second leg underneath it.
- Alternate the direction of joints between layers so each layer locks the one below.
- **Watch for seams that line up through every layer.** Bricks stacked so their joints fall at
  the same x (or z) on every layer form separate towers that only touch side by side. Every
  such column must be bridged by at least one part on some layer.
- A 1-stud-wide column is weak; use 2×2 bricks or interleave.
- Details on **top** surfaces (lights, buttons, antennas) are 1×1 plates or bricks on studs.
  Details on **side faces** (eyes, windows, a chest light, a door) can't be attached sideways
  with these parts: build them into the wall as a differently colored brick in that layer.
- Symmetry is cheap in code: compute one side and mirror `x`.
- Without slopes, roofs and noses are stepped: each layer one stud narrower.
