"""Instruction checks: B4 step-wise connected, B5 insertable, B6 step size."""

from collections import Counter
from dataclasses import dataclass, field

from lego.check.connectivity import components, connections
from lego.check.report import Issue, PartRef, Report
from lego.dsl import Model

MAX_PARTS_PER_STEP = 6


def _pieces_after(model: Model, step: int) -> list[list[int]]:
    """Connected pieces (model part indices, largest first) once `step` (0-based) is done."""
    built = [i for i, p in enumerate(model.placements) if p.step <= step]
    local = components(len(built), connections([model.placements[i] for i in built]))
    return [[built[j] for j in group] for group in local]


@dataclass
class _LoosePiece:
    first_step: int  # 0-based step after which it is first loose
    parts: list[int]  # the piece at that moment
    current: set[int] = field(default_factory=set)  # the piece as it grows
    joined_step: int | None = None
    joiner: int | None = None  # part that joined it to the main piece


def steps_connected(model: Model) -> Report:
    """B4: after every step, everything built so far is one piece.

    Exception: step 1 may leave several loose pieces if all its parts lie on the model's bottom
    layer (plates laid out on the table). Each loose piece is reported once, at the step where it
    first appears, together with the step and part that eventually join it.
    """
    report = Report("B4", "step-wise connected")
    if not model.placements:
        return report
    bottom = min(p.y for p in model.placements)
    neighbours: dict[int, set[int]] = {i: set() for i in range(len(model.placements))}
    for a, b in connections(model.placements):
        neighbours[a].add(b)
        neighbours[b].add(a)

    loose: list[_LoosePiece] = []
    for step in range(model.num_steps):
        pieces = _pieces_after(model, step)
        main = set(pieces[0])
        added = [i for i, p in enumerate(model.placements) if p.step == step]
        for piece in loose:
            if piece.joined_step is not None:
                continue
            if piece.current <= main:
                piece.joined_step = step
                piece.joiner = next((i for i in added if neighbours[i] & piece.current), None)
            else:
                piece.current = next(set(g) for g in pieces if piece.current & set(g))
        if len(pieces) == 1:
            continue
        if step == 0:
            above = [i for i in added if model.placements[i].y != bottom]
            if not above:
                continue  # loose bottom-layer parts are allowed in step 1
            first = model.placements[above[0]]
            report.issues.append(
                Issue(
                    f"step 1 leaves {len(pieces)} separate pieces, which is only allowed when "
                    f"every step-1 part lies on the bottom layer (y={bottom}); these parts are "
                    "above it: move them to a later step or join everything in step 1",
                    [PartRef.of(model, i) for i in above],
                    (first.x, first.y, first.z),
                )
            )
        tracked = [p.current for p in loose if p.joined_step is None]
        for group in pieces[1:]:
            if not any(set(group) & t for t in tracked):
                loose.append(_LoosePiece(step, sorted(group), set(group)))

    for piece in sorted(loose, key=lambda p: (p.first_step, p.parts[0])):
        if piece.joined_step is None:
            fate = "never joined to the main piece"
        else:
            joiner = f" by #{piece.joiner}" if piece.joiner is not None else ""
            fate = f"first joined to the main piece in step {piece.joined_step + 1}{joiner}"
        first = model.placements[piece.parts[0]]
        report.issues.append(
            Issue(
                f"after step {piece.first_step + 1}, {len(piece.parts)} part(s) form a separate "
                f"piece; {fate}. Join them to the rest by the end of step "
                f"{piece.first_step + 1}",
                [PartRef.of(model, i) for i in piece.parts],
                (first.x, first.y, first.z),
            )
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
                (a, _), (b, _) = above, below
                report.issues.append(
                    Issue(
                        f"part #{i} (step {step + 1}) is wedged in: part #{a} is already above "
                        f"it and part #{b} already below it, so it can't be pressed on. Put it "
                        f"in the same step as #{a} (it then goes in before #{a} covers it) or "
                        f"as #{b}",
                        [PartRef.of(model, k) for k in (i, a, b)],
                        (p.x, p.y, p.z),
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
