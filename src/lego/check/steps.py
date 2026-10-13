"""Instruction checks: B4 step-wise connected, B5 insertable, B6 step size."""

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


def insertable(model: Model) -> Report:
    """B5: every part can be pressed on straight down or straight up.

    A part is insertable if the column above its footprint holds no part from an earlier step
    (press down) or the column below does not (press up from underneath). Parts of the same step
    never block each other: the kid sees the whole step and picks the order. A part wedged
    between earlier parts above and below cannot be inserted.
    """
    report = Report("B5", "insertable")
    if not model.placements:
        return report
    lowest = min(p.y for p in model.placements)
    highest = max(p.top for p in model.placements)
    placed: dict[tuple[int, int, int], int] = {}  # parts of earlier steps only
    for step in range(model.num_steps):
        in_step = [(i, p) for i, p in enumerate(model.placements) if p.step == step]
        for i, p in in_step:
            cells = sorted(p.cells())
            above = _first_blocker(placed, cells, range(p.top, highest))
            below = _first_blocker(placed, cells, range(p.y - 1, lowest - 1, -1))
            if above and below:
                (a, at), (b, _) = above, below
                report.issues.append(
                    Issue(
                        f"part #{i} (step {step + 1}) is wedged in: part #{a} is already above "
                        f"it and part #{b} already below it, so it can't be pressed on; add it "
                        "in an earlier step than one of them",
                        [PartRef.of(model, k) for k in (i, a, b)],
                        at,
                    )
                )
        for i, p in in_step:
            for x, z in p.cells():
                for y in p.levels():
                    placed[(x, y, z)] = i
    return report


def _first_blocker(
    placed: dict[tuple[int, int, int], int], cells: list[tuple[int, int]], levels: range
) -> tuple[int, tuple[int, int, int]] | None:
    """First placed part met when sweeping `levels` (nearest first) over the footprint."""
    for y in levels:
        for x, z in cells:
            j = placed.get((x, y, z))
            if j is not None:
                return j, (x, y, z)
    return None
