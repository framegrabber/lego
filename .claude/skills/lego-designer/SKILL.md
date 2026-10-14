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
   out/<slug>.mpd` (don't run `preview` or `live` yourself: they start a server and block), part
   count, the **instruction step** count (`lego build` prints main steps and instruction steps;
   the latter is what the kid clicks through), the largest step, the B7 score and any warnings,
   how many build/check/render iterations it took, and anything you are unsure about.

The kid may be watching a **live view** (`uv run lego live` in another terminal): it always
shows the model built last and reloads after every `lego build`, so they see each iteration
appear. Building into `out/` (the default) is all it needs; tell them when a version is worth
looking at.

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
  high-x side (low z on the left), **top** looks down, **iso** is front-right-above (it sees
  the low-z and high-x faces). Front/side/top renders are orthographic. For a vehicle or animal,
  put its length along x with its **head/nose at high x**, so the front view shows its profile
  and the iso view shows its face.

### Parts (only these exist)

| Call | Sizes |
|---|---|
| `m.brick(size, x=, y=, z=, color=, rot=0)` | `1x1`, `1x2`, `1x4`, `2x2`, `2x4` |
| `m.plate(size, x=, y=, z=, color=, rot=0)` | `1x1`, `1x2`, `1x4`, `2x2`, `2x4` |
| `m.slope(size, x=, y=, z=, color=, facing="front")` | `2x1`, `2x2`, `2x4` |
| `m.inverted_slope(size, x=, y=, z=, color=, facing="front")` | `2x1`, `2x2` |

Slopes are 45°, brick height (3 levels), always 2 studs deep in the direction they face.
`facing` is where the sloped face points: `"front"` (−z), `"back"` (+z), `"left"` (−x),
`"right"` (+x). A `"front"`/`"back"` slope `2xN` covers N studs along x and 2 along z; a
`"left"`/`"right"` one covers 2 along x and N along z. `(x, z)` is still the footprint's min
corner.

- **Slope:** full underside (sits on any studs), but **studs only on the row opposite the
  face**. Nothing can be attached on the sloped face.
- **Inverted slope:** full studs on top, but only the row opposite the face can sit on studs
  below; the sloped underside overhangs. Good for noses, wings and roof eaves.
- The checker treats a slope as its full box: nothing may be placed inside that box above the
  sloped face. A part sitting at the slope's top level (`y + 3`) on the stud row is fine, and
  so is a narrower slope row stacked one stud inward.
- Example: `models/examples/slopes.py` (all four directions).

Colors: LDraw names, lowercase with underscores. Good kid palette: `red`, `blue`, `yellow`,
`green`, `black`, `white`, `orange`, `lime`, `tan`, `brown`, `light_bluish_grey`,
`dark_bluish_grey`, `dark_blue`, `dark_red`, `bright_pink`, `medium_azure`. See-through:
`trans_clear`, `trans_yellow`, `trans_red`, `trans_light_blue`. The full list is the
`!COLOUR` lines in `ldraw/LDConfig.ldr`.

### Sub-assemblies

Legs, arms, wings, wheels or a cockpit can be built **separately** with their own steps and
coordinates, then attached in one step of the main model, like the "build this first" boxes in
real instructions. Copies of the same sub-assembly can be attached several times.

```python
leg = m.subassembly("leg")                     # one level deep; name must be unique
with leg.step():
    leg.plate("2x4", x=0, z=-1, y=0, color="black", rot=90)
    leg.brick("2x2", x=0, z=0, y=1, color="light_bluish_grey")
with leg.step():
    leg.brick("2x2", x=0, z=0, y=4, color="light_bluish_grey")

with m.step():                                  # hips
    m.plate("2x4", x=0, z=0, y=7, color="red")
with m.step():
    m.attach(leg, x=0, y=0, z=0)                # leg's (0, 0, 0) lands at (0, 0, 0)
    m.attach(leg, x=2, y=0, z=0, rot=0)         # second copy
```

- Finish all of a sub-assembly's steps before attaching it; it can't be changed afterwards.
- In the preview, its steps are shown on their own ("Build 2× the leg") right before the step
  that attaches it ("Attach 2× the leg").
- `attach(..., rot=...)` turns the copy about the sub-assembly's grid point (0, 0) — the corner
  where its x and z coordinates start — before moving it to (x, z). **Turning is not
  mirroring**: a left wing turned 180° is not a right wing. Build mirrored left/right parts as
  two sub-assemblies, or place them directly with a small mirror helper in your program.
- `lego render --step N` numbers instruction steps and prints `Step N / T · title | new: … |
  pink box …`: the caption, the new parts (including sub-assemblies being attached), and
  whether a weak part is marked. In step renders, earlier steps are faded so new parts stand
  out, and the weakest joint (B7) gets a magenta box. The final step is shown unfaded.
- Checks: the sub-assembly's own steps must follow the step rules (one piece after each step,
  ≤ 6 parts, nothing wedged). Attaching it counts as **one** item of the main step, and it must
  connect to what is already built, pressed on as one rigid piece. See the full example in
  `models/examples/two_legs.py`.

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
- A part can't be added if parts from **earlier steps** already touch both its top and its
  bottom: there is no room to press it on. With a gap on either side it can be slid in and
  pressed. Within a step the kid chooses the order, so parts of the same step never block
  each other.
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
- **B5 insertable**: no part is touched by parts from earlier steps both above and below. The
  usual fix: put the wedged part in the **same step** as the part above it (a part hanging
  under something goes in the same step as that thing).
- **B6 step size**: at most 6 parts per step.
- **B7 stable** (graded, score 0–1): a part that holds other parts with few studs, far out
  (centre of weight past its studs) or hanging underneath scores low. Below 0.3 in the finished
  model fails; 0.3–0.6, or any weak point only while building, is a **warning**: improve it if
  you can (more studs under it, shorter overhang, support the far end, or build the far end's
  support earlier). The finished model must not tip over: keep its weight over its footprint.
- **Sub-assemblies** are checked with their own steps; issues inside one start with "inside
  sub-assembly 'leg'" and name the part with its `leg.brick(...)` call.

## Design tips

- Two plate layers only lock together if **every top plate overlaps at least two bottom
  plates**. A plate sitting exactly on a same-sized plate is always a separate island. If the
  plates can't tie a base together on their own, put the first body bricks in the same steps.
- A proven square base: four 2x4 plates in a **pinwheel** around the centre (each turned 90°
  from its neighbour), and the second layer as a pinwheel turning the other way. More than 6
  bottom plates: lay 6 in step 1, lock them in step 2, press the rest up from below in step 3
  with the parts that lock them.
- Step 1 doesn't have to touch the table: it can be one connected piece in the air (e.g. hips
  that the legs are attached under in step 2).
- Two legs (or towers) can't be built side by side on the table and joined later. Build them as
  a sub-assembly and attach both under a hip part that is already there.
- Vehicles: build each axle (two wheel blocks joined by crossed plates) as a sub-assembly. Start
  the chassis on the rear axle and attach the front axle in the step where the floor reaches it.
  There are no round wheels; 2x2 bricks stand in for them.
- Alternate the direction of joints between layers so each layer locks the one below.
- **Watch for seams that line up through every layer.** Bricks stacked so their joints fall at
  the same x (or z) on every layer form separate towers that only touch side by side. Every
  such column must be bridged by at least one part on some layer.
- A 1-stud-wide column is weak; use 2×2 bricks or interleave.
- Details on **top** surfaces (lights, buttons, antennas) are 1×1 plates or bricks on studs.
  Details on **side faces** (eyes, windows, a chest light, a door) can't be attached sideways
  with these parts: build them into the wall as a differently colored brick in that layer.
- Symmetry is cheap in code: compute one side and mirror `x` (or `z`) with a helper.
- Roofs, car noses, wing edges: use slopes facing outward; stack a narrower slope row on top
  for a taller roof, and **fill the gable ends** (bricks in the wall's colour under each slope
  row) or the roof is hollow from the side. Without slopes, step the layers one stud narrower.
