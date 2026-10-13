"""Instruction checks: B4 step-wise connected, B6 step size."""

from collections import Counter

from lego.check.connectivity import components, connections
from lego.check.report import Issue, PartRef, Report
from lego.dsl import Model

MAX_PARTS_PER_STEP = 6


def _pieces_after(model: Model, step: int) -> list[list[int]]:
    """Connected pieces (model part indices, largest first) once `step` (0-based) is done."""
    built = [i for i, p in enumerate(model.placements) if p.step <= step]
    local = components(len(built), connections([model.placements[i] for i in built]))
    return [[built[j] for j in group] for group in local]


def steps_connected(model: Model) -> Report:
    """B4: after every step, everything built so far is one piece.

    Exception: step 1 may leave several loose pieces if all its parts lie on the model's bottom
    layer (plates laid out on the table).
    """
    report = Report("B4", "step-wise connected")
    if not model.placements:
        return report
    bottom = min(p.y for p in model.placements)
    for step in range(model.num_steps):
        pieces = _pieces_after(model, step)
        if len(pieces) == 1:
            continue
        loose = [i for group in pieces[1:] for i in group]
        if step == 0:
            above_bottom = [i for g in pieces for i in g if model.placements[i].y != bottom]
            if not above_bottom:
                continue
            message = (
                f"after step 1 the model is {len(pieces)} separate pieces; step 1 may only lay "
                f"out loose parts on the bottom layer (y={bottom})"
            )
        else:
            message = (
                f"after step {step + 1} the model is {len(pieces)} separate pieces; the listed "
                f"parts are not joined to the main piece ({len(pieces[0])} parts) yet"
            )
        first = model.placements[loose[0]]
        report.issues.append(
            Issue(message, [PartRef.of(model, i) for i in loose], (first.x, first.y, first.z))
        )
    return report


def step_size(model: Model, limit: int = MAX_PARTS_PER_STEP) -> Report:
    """B6: each step adds at most `limit` parts."""
    report = Report("B6", "step size")
    counts = Counter(p.step for p in model.placements)
    for step in sorted(counts):
        if counts[step] > limit:
            parts = [i for i, p in enumerate(model.placements) if p.step == step]
            report.issues.append(
                Issue(
                    f"step {step + 1} adds {counts[step]} parts; at most {limit} per step",
                    [PartRef.of(model, i) for i in parts],
                )
            )
    return report
