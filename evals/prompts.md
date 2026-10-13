# Eval prompts

Fixed descriptions, phrased the way a 10+ year old might say them. Run with the
`lego-designer` skill; record one row per run.

| # | Prompt |
|---|---|
| 1 | A red racing car with a big spoiler at the back |
| 2 | A small house with a door, two windows and a roof |
| 3 | A lighthouse with red and white stripes and a light on top |
| 4 | A robot with arms and a head |
| 5 | A rocket standing on a launch pad |
| 6 | A dog sitting down |
| 7 | A castle tower with battlements |
| 8 | A bridge over a river |
| 9 | A tree with a brown trunk and green leaves |
| 10 | A spaceship with wings |

## Results

Columns: checks = B1–B3 at delivery; iterations = build/check/render cycles until delivery;
likeness 1–3 (1 = unrecognizable, 3 = clearly it). "Self" is the designing agent's own rating,
"human" is filled in by a person looking at the preview.

| Date | # | Program | Parts | Steps | Max/step | Iterations | Checks | Likeness self | Likeness human | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-13 | 1 | `models/designs/racing_car.py` | 66 | 18 | 5 | 2 | B1–B3 ok | 2.5 | | Checks passed first build; iteration 2 fixed wheels that looked like blocks. Wheels are 2×2 bricks — vocabulary limits likeness. Wing overhangs 2 studs on 1×2 pillars (B7 risk). |
| 2026-10-13 | 3 | `models/designs/lighthouse.py` | 79 | 20 | 6 | 3 | B1–B3 ok | 3 | | Checks passed first build; iterations fixed stripe/window placement and lamp visibility. Base plates have aligned seams: base is 4 loose quarters until the tower ring (will fail B4). |
| 2026-10-13 | 4 | `models/designs/robot.py` | 50 | 17 | 5 | 3 | B1–B3 ok | 3 | | Iteration 1 failed B3: seams at x=4 through all torso layers split the robot in two; fixed from the B3 report alone. Arms overhang 2 studs (B7 risk). |
| 2026-10-13 | 7 | `models/designs/castle_tower.py` | 85 | 21 | 6 | 2 | B1–B3 ok | 3 | | Run in the main session (designer knows the codebase). Checks passed first build; iteration 2 made it taller (5→8 courses) and added a second window level. Per-step pieces (throwaway script): 6 after step 1, 3 after step 2, 2 after step 3 — the "staggered" floor does not lock by itself; the first wall course joins it. |
| 2026-10-13 | — | `models/designs/micro_tie_fighter.py` | 31 | 10 | 5 | 2 | B1–B3 ok | 3 | | Ad-hoc user prompt "Star Wars inspired micro ship" (main session). TIE-style: upright wings joined by pylon plates that run through each wing. Iteration 2 centred wings and pod on the pylon. One connected piece after every step (throwaway script) — wings built from the pylon outward, lower courses hang underneath. |

### Baseline findings (skill v1, run by fresh agents with no other context)

- **Core hypothesis holds:** 3/3 delivered, 0 coordinate-convention mistakes; the one check
  failure (robot B3) was fixed from the JSON report on the next iteration. Iterations were
  driven by *visual* problems, not check failures.
- **Skill gaps fixed after this run:** transparent colors and where the full color list is;
  render file names; side-view orientation; "don't run preview"; step-order rule (each step must
  leave one connected piece); aligned-seam trap; details on side faces; interim overhang rule.
- **Open tool improvement:** the B3 message could name the touching-but-unconnected neighbors or
  the seam where islands meet (robot agent's suggestion).
- **Not yet enforced, hand-checked by agents:** step size (B6), step-wise connectivity (B4),
  stability (B7). The lighthouse base shows B4 is needed.
