"""Instruction data for the preview: parts per step and weak points, written next to the .mpd.

The preview maps entries to three.js objects by position: a main-model object is the n-th
part or sub-assembly line of the main file (`[n]`), a sub-assembly part is the m-th part line
inside that sub-assembly (`[n, m]`). `lego.ldraw.dumps` writes lines in exactly this order.
"""

import json
from collections import Counter
from pathlib import Path

from lego.check.stability import FAIL, WARN, stability_scores
from lego.dsl import Model, Placement
from lego.ldraw import file_name
from lego.parts import colors


def object_paths(model: Model) -> dict[int, list[int]]:
    """Placement index → position of its three.js object (see module docstring)."""
    paths: dict[int, list[int]] = {}
    top: dict[str, int] = {}  # attachment label → its line index in the main file
    line = 0
    for step in range(model.num_steps):
        for i, p in enumerate(model.placements):
            if p.step != step:
                continue
            if p.sub is None:
                paths[i] = [line]
                line += 1
            else:
                if p.sub not in top:
                    top[p.sub] = line
                    line += 1
                assert p.sub_index is not None
                paths[i] = [top[p.sub], p.sub_index]
    return paths


def instruction_steps(model: Model) -> int:
    """Steps the preview shows: main steps plus, per main step, each attached sub-assembly's
    steps once (copies are shown as "2×")."""
    total = model.num_steps
    for step in range(model.num_steps):
        kinds = {a.sub.name: a.sub for a in model.attachments if a.step == step}
        total += sum(sub.num_steps for sub in kinds.values())
    return total


def _items(placements: list[Placement]) -> list[dict]:
    names = {code: name.replace("_", " ") for name, code in colors().items()}
    counts = Counter(
        (p.part.size, p.part.kind, names.get(p.color, str(p.color))) for p in placements
    )
    return [
        {"count": n, "part": f"{size} {kind}", "color": color}
        for (size, kind, color), n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def instructions(model: Model) -> dict:
    main_steps = []
    for step in range(model.num_steps):
        own = [p for p in model.placements if p.step == step and p.sub is None]
        attached = Counter(a.sub.name for a in model.attachments if a.step == step)
        main_steps.append(
            {
                "parts": _items(own),
                "attach": [{"count": n, "name": name} for name, n in attached.items()],
            }
        )
    subs = {}
    for a in model.attachments:
        sub = a.sub
        subs[file_name(sub)] = [
            {"parts": _items([p for p in sub.placements if p.step == step]), "attach": []}
            for step in range(sub.num_steps)
        ]
    paths = object_paths(model)
    worst, _ = stability_scores(model)
    weak = [
        {
            "path": paths[i],
            "step": w.step,
            "score": round(w.score, 2),
            "level": "unstable" if w.score < FAIL else "fragile",
        }
        for i, w in sorted(worst.items())
        if w.score < WARN
    ]
    return {"main": main_steps, "subs": subs, "weak": weak}


def save(model: Model, mpd_path: Path) -> Path:
    target = mpd_path.with_suffix(".json")
    target.write_text(json.dumps(instructions(model), indent=1))
    return target
