# Implementation Plan: Kids' LEGO Designer

Spec: [SPEC.md](../SPEC.md) · Intent: [docs/intent/kids-lego-instructions.md](../docs/intent/kids-lego-instructions.md)
Tasks: [tasks/todo.md](todo.md)

## Overview

Build the pipeline prompt → DSL program → `.mpd` → checks → browser preview/render, driven by a
Claude Code skill. Pictures come first (Phase 0), then the model core, then the checker. The Claude
loop starts once B1–B3 exist so we learn early how well Claude fixes errors from JSON reports;
step, stability and slope checks follow.

## Dependency graph

```
setup (LDraw lib, Playwright)
 └─ preview (three.js page) ─ render (headless screenshots)
parts ─ dsl ─ ldraw (.mpd writer/reader, `lego build`)
              │      └─ preview/render consume .mpd
              └─ check B1/B2 ─ B3 ─┬─ skill v1 (loop) ─ eval baseline
                                   └─ B4/B6 ─ B5 ─ B7 ─ slopes ─ full eval + physical builds
```

## Architecture decisions

- **One renderer.** The preview page is also the renderer: `lego render` loads it in headless
  Chromium (Playwright) and screenshots fixed camera angles. Claude sees what kids see.
- **three.js vendored, not from a CDN**, so the preview works offline in workshops. LDraw parts are
  served from the local `ldraw/` directory by `lego preview`.
- **The checker works on the in-memory model, not on parsed LDraw.** `lego check file.mpd` parses
  back into the same model type via `ldraw.py`, so there is one code path.
- **Integer grid.** Positions are integers in studs (x, z) and plates (y); rotations are 0/90/180/270.
  This makes B2–B5 exact grid arithmetic. Non-grid parts are out of scope for v1.
- **Reports are data.** Every check returns `Report(check_id, ok, issues=[Issue(part, step, at, message)])`,
  serialized to JSON for Claude and printed readably for humans.
- **Stability behind an interface.** `score(model) -> dict[part, float]`; v1 heuristic now,
  StableLego later without touching callers.

## Phases

### Phase 0 — First picture
Tasks 1–3. Outcome: a hand-written `.ldr` shown in the browser and rendered to PNGs.

### Phase 1 — Model core
Tasks 4–5. Outcome: a DSL program builds an `.mpd` with steps; preview steps through it.

### Phase 2 — Checker core + first Claude loop
Tasks 6–8. Outcome: `lego check` catches collisions and floating parts; the skill runs the loop on
3 eval prompts. Baseline numbers recorded.

### Phase 3 — Instruction checks
Tasks 9–10. Outcome: every step is connected, small and physically insertable.

### Phase 4 — Stability
Tasks 11–12. Outcome: graded B7 score with thresholds, fragile parts highlighted in the preview.

### Phase 5 — Slopes
Task 13. Outcome: five slopes usable in the DSL and correctly handled by all checks.

### Phase 6 — Validation
Task 14. Outcome: full eval run and at least 3 physical builds; thresholds calibrated.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| WebGL in headless Chromium fails or is slow on macOS | High (no renders) | Task 3 is early; try Playwright's default, then `--use-angle=swiftshader`; fallback is headed Chromium off-screen. |
| LDrawLoader fetches thousands of subfiles per model → slow preview | Med | Measure in Task 2; if slow, pack used parts into the `.mpd` (LDrawLoader supports packed files) at build time. |
| Claude can't fix errors from JSON alone | High (core hypothesis) | Measured in Task 8 before investing in B4–B7; adjust report wording/content first. |
| B5 insertion rule too strict or too loose vs. real bricks | Med | Physical builds in Task 14; keep rule simple and explicit so it is easy to tune. |
| B7 heuristic disagrees with reality | Med | Graded score + thresholds; calibrate in Task 14; StableLego as v2. |
| LDraw library URL/layout changes | Low | `lego setup` checks for `ldraw/parts/3001.dat` and fails with a clear message. |

## Open questions

- B7 default thresholds (0.3 / 0.6) — calibrate in Task 14.
