# Intent: Kids describe a model, get buildable instructions

*Confirmed 2026-10-13 via interview.*

- **Outcome:** A kid describes a model in their own words; Claude designs it, the kid previews it in 3D in a browser, and gets step-by-step instructions to build it from real bricks.
- **User:** Kids aged 10+, at home and in workshops. An adult/facilitator runs the tool; the kid describes and builds.
- **Why now:** The Opus 5.5 demo suggests a general model plus deterministic checkers can do this without training a specialized model.
- **Success:** The kid builds the model from the instructions without getting stuck — every step possible, every part connected, nothing collapses. Rough likeness to the description is fine.
- **Priority / constraint:** Buildability first, likeness second. Generation speed and workshop timing don't matter.
- **How it's driven:** Claude drives generation (e.g. via Claude Code). Kids only need a web preview of the model and steps.
- **Out of scope (for now):** parts inventory (assume all bricks available), full kid-facing web app with chat, parts ordering, 2,000-piece demo scale.
