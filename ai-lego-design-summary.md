# AI-Driven LEGO Design with Claude: Research Summary

*Compiled October 13, 2026*

## 1. Starting point: the Opus 5.5 demo video

**Video:** [Claude Opus 5.5 builds daydreams that hold together](https://www.youtube.com/watch?v=lCR9epzSNGc)

The question was whether the brick-building tool shown is a feature of Claude Desktop, Claude Design, or an app built with Opus 5.5.

**Conclusion:** It is a standalone, purpose-built app, not a feature of Claude Desktop or Claude Design. Claude (Opus 5.5) acts as the engine inside it.

Evidence from the screenshots:

- **A custom, brick-specific UI.** The header shows piece count, steps, sub-builds and baseplate size (e.g. 32×32 studs). There are Model / Manual / Parts / Design tabs, a 3D viewer (Front / Top / Spin), a step-by-step assembly player, a showcase library, Versions/Save/Download, and a paginated building manual with PDF export (e.g. 326 pages for a castle).
- **Claude in the chat panel.** Responses are labeled "CLAUDE" and include structural checks such as "Checked: every part connects" or "Checked: buildable, 4 warnings."
- **Iterative edits.** A request to add a watchtower, drawbridge and moat grew a Stone Castle from 1,796 to 2,057 pieces and regenerated the manual.
- **Demo framing.** The video carries a "Some sections of demo are accelerated" note and is titled around the model, which fits a capability showcase.

No evidence was found that the app is publicly available.

## 2. Core insight: LDraw is the common language

Nearly the entire brick-CAD ecosystem uses the open **LDraw** format (`.ldr` / `.mpd`). It is plain text with one line per part (part number, color, position, rotation matrix), so Claude can write, edit and reason about models directly. Studio, LeoCAD, LDCad, LPub3D and LDView all read it.

## 3. Tools that can be driven by Claude

### Claude integrations

| Tool | What it does | Link |
|---|---|---|
| **ldraw-mcp** | MCP server that renders LDraw files with real part geometry via headless Blender + ImportLDraw, so a vision model can see the build. Recent versions add bill-of-materials, color lookup and part search tools. Registers with Claude Code via `claude mcp add`. | [GitHub](https://github.com/musharna/ldraw-mcp) |
| **pyldraw3** | Python library for LDraw: STEP/ROTSTEP and LPub3D semantics, validation, MPD/LDR snapshots, JSON export, CLI for part search/info and BOM. Does not render PDFs or images itself. | [PyPI](https://pypi.org/project/pyldraw3/) |
| **lego-model-builder skill** (in pyldraw3) | Agent skill: natural-language description → pyldraw3 program + `.ldr` file, with a validate / geometry-check / render / fix loop. | [SKILL.md](https://github.com/hbmartin/pyldraw3/blob/main/skills/lego-model-builder/SKILL.md) |
| **rebrickable** (Python) | Typed client for the Rebrickable catalog and API v3, including inventories, BOMs and LDraw cross-references; works offline after an initial download. | [PyPI](https://pypi.org/project/rebrickable/) |

### Desktop applications

| App | Role in a pipeline | Scriptable? |
|---|---|---|
| **BrickLink Studio** | Final polishing, rendering, parts ordering. Imports `.ldr` / `.mpd`. Native `.io` files are password-protected ZIPs, so use LDraw for exchange. | No |
| **LPub3D** | Generates LEGO-style building instructions (PDF). Supports batch and headless console modes, previous-step fading, part lists. Needs STEP markers and submodels in the file. | Yes (CLI / headless) |
| **LeoCAD** | Open LDraw editor; can render from the command line. | Partly |
| **LDCad** | Open LDraw editor for manual touch-ups. | Limited |
| **LDView** | LDraw viewer/renderer; used by the lego-model-builder skill. | Yes (CLI) |

## 4. Assessment of the lego-model-builder skill

**Strengths**

- Claude writes a *program* that generates the model (loops, named constants), so builds are re-runnable and tweakable.
- Part numbers are confirmed via the CLI before use.
- Three verification layers: `validate` (unknown parts/colors, syntax), `check_geometry.py` (duplicate and floating pieces), and front/iso/top renders that Claude must inspect.
- Self-bootstrapping setup (installs pyldraw3, downloads the ~80 MB parts library, finds or installs LDView/LeoCAD) and a graceful validate-only fallback when no renderer is available.

**Gaps compared with the demo**

- Produces a **flat** model: no submodels or STEP markers, so no basis for a building manual (pyldraw3 itself supports both).
- Geometry check catches duplicates and floating parts only. It does not verify stud-to-antistud clutch or structural stability.
- Iteration is capped at 3–5 render-fix cycles: fine for small models, likely too few for 2,000-piece builds.
- Very young, small project; expect rough edges.
- Touches the local machine (config, cache, package managers), so it belongs in **Claude Code on your own computer**, not the claude.ai sandbox.

**Suggested extensions**

1. Add a sub-build and STEP phase, then hand the MPD to LPub3D in batch mode for a PDF manual.
2. Replace `check_geometry.py` with a real connectivity checker (stud contacts per part + connected-graph test), optionally plus a stability analysis.
3. Supplement LDView/LeoCAD renders with ldraw-mcp's Blender renders for clearer visual verification.

## 5. Proposed pipeline

1. **Design:** Claude writes the model as a pyldraw3 program → LDraw file, using Rebrickable / pyldraw3 for valid part numbers.
2. **Check:** connectivity and stability check (custom script, StableLego-style analysis, or BrickGPT's stability code).
3. **See:** ldraw-mcp renders; Claude inspects and fixes.
4. **Instructions:** Claude adds sub-builds and STEP markers; LPub3D generates the manual headlessly.
5. **Polish:** open the final model in BrickLink Studio for rendering or parts ordering.
6. **Optional:** a web front end on top, similar to the demo app.

## 6. Prior art

### Legolization: shape → buildable brick layout

- Evolutionary / genetic algorithm approaches since ~2001, including graph-based assembly representations (Peysakhov & Regli).
- **Legolization: Optimizing LEGO Designs** (Luo et al., SIGGRAPH Asia 2015). Force-based stability analysis that ranks structures, gives a stability threshold, identifies weak spots, and iteratively refines the layout. [Project page](http://www.cmlab.csie.ntu.edu.tw/~forestking/research/SIGA15-Legolization/) · [student implementation](https://github.com/debilin/Legolizer)

### Automatic building instructions

- **LEGO Builder** (Ono et al., 2013). 3D polygon model → building instructions, using a "legograph" connectivity structure so models don't fall apart. [J-STAGE](https://www.jstage.jst.go.jp/article/mta/1/4/1_354/_article)
- **Automatic generation of LEGO building instructions from multiple photographic images** (Computer-Aided Design, 2015). Photos → voxel model → instructions. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0010448515001037)
- LEGO patent **US 8,374,829** on automatic generation of building instructions.
- Deep RL approaches to physically executable assembly sequence planning.

### Physics / stability oracles

- **StableLego**. Stability analysis as an optimization over force-balancing equations; dataset of 50k+ LEGO layouts with stability labels. [arXiv 2402.10711](https://arxiv.org/abs/2402.10711) · [code](https://github.com/intelligent-control-lab/StableLego)
- **BrickSim** (2026). Real-time physics simulator for interlocking brick assemblies, modeling snap-fit and collapse. arXiv 2603.16853

### Learned generative models

- **BrickGPT** (CMU, ICCV 2025 Best Paper / Marr Prize). Text → stable brick structures, using validity checks and physics-aware rollback during generation. MIT-licensed; limited to simple bricks on a 20×20×20 grid; best results need a Gurobi license. [GitHub](https://github.com/AvaLovelace1/BrickGPT) · [Project](https://avalovelace1.github.io/BrickGPT/)
- **LegoACE** (SIGGRAPH Asia 2025). Autoregressive text- or normal-map-conditioned generation; LegoVerse dataset of 55k models and 9,314 brick types. Weights on Hugging Face, but may produce unstable or non-buildable results. [ACM](https://dl.acm.org/doi/10.1145/3757377.3763881) · [Hugging Face](https://huggingface.co/VAST-AI/LegoACE)
- **LEGO-Maker** (ACM TOG, Dec 2025). Image-conditioned generation with 100+ brick types.
- **Rollback-Free Stable Brick Structures Generation (STABLE)** (2026). [arXiv 2605.06947](https://arxiv.org/abs/2605.06947)
- **Sample-Efficient Post-Training for LEGO Spatial-Physics Reasoning** (2026). Frames LEGO assembly as LLM program synthesis. [arXiv 2606.07602](https://arxiv.org/abs/2606.07602)

### Benchmarks

- **LEGO-Puzzles: How Good Are MLLMs at Multi-Step Spatial Reasoning?** (2025). [arXiv 2503.19990](https://arxiv.org/abs/2503.19990)

## 7. Key takeaway

Prior work mostly relies on **specialized models trained on brick datasets**, which hit limits in model size, brick vocabulary and stability. The Opus 5.5 demo appears to take a different route: a **general model as designer**, paired with **deterministic verification tools**. That approach is reproducible without training anything:

- stability / connectivity ideas from Legolization, LEGO Builder's legograph and StableLego → **checker**
- instruction-sequencing ideas → **manual generation** (via LPub3D)
- Claude + pyldraw3 + ldraw-mcp → **design, render, iterate**

## 8. Possible next steps

- [ ] Install the lego-model-builder skill and ldraw-mcp in Claude Code
- [ ] Write a stud-connectivity checker (graph-based)
- [ ] Add sub-build / STEP generation and an LPub3D batch export
- [ ] Evaluate StableLego's stability analysis as a plug-in check
- [ ] Prototype a small end-to-end build (e.g. a 300-piece lighthouse) through the full pipeline
