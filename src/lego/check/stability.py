"""B7: graded stability score (heuristic v1).

Parts on the model's bottom layer rest on the table. For every other part p, S(p) is p plus
everything that depends on it: the parts whose only way down to the table runs through p
(found as articulation-point subtrees of a DFS from the table). All connections from S(p) to the
rest of the model therefore go through p's own studs; call their number C.

The demand on those studs grows with the weight of S(p) (W, in 2x2-brick units) and with how
badly it is held:
  lever    distance (studs) from S(p)'s centre of weight to the area of p's support studs
  hanging  +1 if p hangs underneath its supports (the studs carry the weight in tension)
  twist    +0.5 if p is wider than one stud but held by a single stud (it can rotate)

    score = K·C / (K·C + W · (lever + hanging + twist)),   K = 4 per stud

Free-standing models also tip over if their centre of weight leaves the convex hull of the
table footprint; that gives a tipping score per step. Every score is evaluated after every step
(a half-built model must hold together in a kid's hands too); a part's reported score is its
worst one. score < FAIL is an error, FAIL <= score < WARN a warning. The model score is the
minimum. This is a heuristic ranking, not physics; thresholds are to be calibrated against real
builds (SPEC.md).
"""

import math
from dataclasses import dataclass

from lego.check.connectivity import connections
from lego.check.report import Issue, PartRef, Report
from lego.dsl import Model, Placement

WARN = 0.6
FAIL = 0.3
K_PER_STUD = 4.0
WEIGHT_UNIT = 12.0  # volume of a 2x2 brick in stud×stud×plate cells

type Point = tuple[float, float]


@dataclass
class _Worst:
    score: float  # worst over all steps
    step: int  # step where the worst score occurs
    held: int  # parts in S(p)
    studs: int
    lever: float
    hanging: bool
    final: float | None = None  # score in the finished model


def _volume(p: Placement) -> int:
    return len(p.cells()) * p.part.height


def _centre(p: Placement) -> Point:
    return (p.x + p.size_x / 2, p.z + p.size_z / 2)


def _shared_studs(lower: Placement, upper: Placement) -> set[tuple[int, int]]:
    return set(lower.stud_cells() & upper.antistud_cells())


def _dependents(n: int, adjacency: list[set[int]], grounded: list[int]) -> dict[int, list[int]]:
    """For each node reachable from the table: the nodes that lose the table if it is removed.

    Iterative Tarjan DFS from a virtual table node (index n) linked to every grounded part.
    """
    table = n
    neighbours = [set(a) for a in adjacency] + [set(grounded)]
    for g in grounded:
        neighbours[g].add(table)  # the table is a neighbour both ways (back edges to it)
    disc = [-1] * (n + 1)
    low = [0] * (n + 1)
    order: list[int] = []
    size = [1] * (n + 1)
    children: list[list[int]] = [[] for _ in range(n + 1)]
    disc[table] = 0
    order.append(table)
    stack = [(table, -1, iter(neighbours[table]))]
    while stack:
        node, parent, it = stack[-1]
        advanced = False
        for nxt in it:
            if nxt == parent:
                continue
            if disc[nxt] == -1:
                disc[nxt] = low[nxt] = len(order)
                order.append(nxt)
                children[node].append(nxt)
                stack.append((nxt, node, iter(neighbours[nxt])))
                advanced = True
                break
            low[node] = min(low[node], disc[nxt])
        if not advanced:
            stack.pop()
            if stack:
                up = stack[-1][0]
                low[up] = min(low[up], low[node])
                size[up] += size[node]
    result: dict[int, list[int]] = {}
    for node in range(n):
        if disc[node] == -1:
            continue
        held = [node]
        for child in children[node]:
            if low[child] >= disc[node]:
                held += order[disc[child] : disc[child] + size[child]]
        result[node] = held
    return result


def _distance_to_box(point: Point, cells: set[tuple[int, int]]) -> float:
    xs = [x + 0.5 for x, _ in cells]
    zs = [z + 0.5 for _, z in cells]
    dx = max(min(xs) - point[0], 0.0, point[0] - max(xs))
    dz = max(min(zs) - point[1], 0.0, point[1] - max(zs))
    return math.hypot(dx, dz)


def _hull(points: list[Point]) -> list[Point]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _margin_inside(point: Point, hull: list[Point]) -> float:
    """Distance from point to the hull edge; negative if outside."""

    def seg_dist(a: Point, b: Point) -> float:
        ax, az, bx, bz = *a, *b
        t = ((point[0] - ax) * (bx - ax) + (point[1] - az) * (bz - az)) / max(
            (bx - ax) ** 2 + (bz - az) ** 2, 1e-12
        )
        t = min(1.0, max(0.0, t))
        return math.hypot(point[0] - (ax + t * (bx - ax)), point[1] - (az + t * (bz - az)))

    edges = list(zip(hull, hull[1:] + hull[:1], strict=True))
    distance = min(seg_dist(a, b) for a, b in edges)
    inside = all(
        (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0]) >= 0 for a, b in edges
    )
    return distance if inside else -distance


def _tipping(built: list[Placement], bottom: int) -> float | None:
    grounded = [p for p in built if p.y == bottom]
    if not grounded:
        return None
    corners = [
        (float(x + dx), float(z + dz))
        for p in grounded
        for x, z in p.cells()
        for dx in (0, 1)
        for dz in (0, 1)
    ]
    hull = _hull(corners)
    total = sum(_volume(p) for p in built)
    com = (
        sum(_centre(p)[0] * _volume(p) for p in built) / total,
        sum(_centre(p)[1] * _volume(p) for p in built) / total,
    )
    if len(hull) < 3:
        return 1.0
    margin = _margin_inside(com, hull)
    return 0.0 if margin < 0 else min(1.0, 0.5 + margin)


def _verdict(score: float) -> str:
    return "unstable" if score < FAIL else "fragile" if score < WARN else "ok"


def stability_scores(model: Model) -> tuple[dict[int, _Worst], list[tuple[int, float]]]:
    """Worst score per non-grounded part, and the tipping score per step."""
    worst: dict[int, _Worst] = {}
    tipping: list[tuple[int, float]] = []
    if not model.placements:
        return worst, tipping
    bottom = min(p.y for p in model.placements)
    for step in range(model.num_steps):
        built = [i for i, p in enumerate(model.placements) if p.step <= step]
        parts = [model.placements[i] for i in built]
        joined = connections(parts)
        adjacency: list[set[int]] = [set() for _ in parts]
        for a, b in joined:
            adjacency[a].add(b)
            adjacency[b].add(a)
        grounded = [j for j, p in enumerate(parts) if p.y == bottom]
        for j, held in _dependents(len(parts), adjacency, grounded).items():
            p = parts[j]
            if p.y == bottom:
                continue
            inside = set(held)
            studs: set[tuple[int, int]] = set()
            hanging = True
            for k in adjacency[j] - inside:
                q = parts[k]
                if q.top == p.y:  # q is below p: p rests on it
                    studs |= _shared_studs(q, p)
                    hanging = False
                else:
                    studs |= _shared_studs(p, q)
            if not studs:
                continue
            volume = sum(_volume(parts[k]) for k in held)
            com = (
                sum(_centre(parts[k])[0] * _volume(parts[k]) for k in held) / volume,
                sum(_centre(parts[k])[1] * _volume(parts[k]) for k in held) / volume,
            )
            lever = _distance_to_box(com, studs)
            twist = 0.5 if len(studs) == 1 and len(p.cells()) > 1 else 0.0
            demand = volume / WEIGHT_UNIT * (lever + (1.0 if hanging else 0.0) + twist)
            capacity = K_PER_STUD * len(studs)
            score = capacity / (capacity + demand)
            index = built[j]
            if index not in worst or score < worst[index].score:
                final = worst[index].final if index in worst else None
                worst[index] = _Worst(score, step, len(held), len(studs), lever, hanging, final)
            if step == model.num_steps - 1:
                worst[index].final = score
        if step == model.num_steps - 1:
            # While building, the kid holds the model; tipping matters once it stands finished.
            tip = _tipping(parts, bottom)
            if tip is not None:
                tipping.append((step, tip))
    return worst, tipping


def stable(model: Model) -> Report:
    """B7: graded stability (see module docstring).

    A weak point in the finished model below FAIL is an error. A weak point that exists only
    while building (the kid is holding the model) is at most a warning. The report score is the
    finished model's score.
    """
    report = Report("B7", "stable")
    worst, tipping = stability_scores(model)
    finals = [w.final for w in worst.values() if w.final is not None]
    scores = finals + [t for _, t in tipping]
    report.score = min(scores) if scores else 1.0
    finished = {i: w.final for i, w in worst.items() if w.final is not None}
    if finished:
        weakest = min(finished, key=lambda i: finished[i])
        ref = PartRef.of(model, weakest)
        report.note = f"weakest joint in the finished model: #{weakest} {ref.call}"
    for index, w in sorted(worst.items(), key=lambda kv: kv[1].score):
        if w.score >= WARN:
            continue
        p = model.placements[index]
        how = (
            "hangs underneath them"
            if w.hanging
            else f"its weight sits {w.lever:.1f} studs past them"
        )
        building = w.final is None or w.final > w.score
        when = f"after step {w.step + 1}" + (" (while building)" if building else "")
        error = w.final is not None and w.final < FAIL
        report.issues.append(
            Issue(
                f"part #{index} and the {w.held - 1} part(s) depending on it score {w.score:.2f} "
                f"({_verdict(w.score)}) {when}: held by {w.studs} stud(s), {how}. Add studs "
                "under it, shorten the overhang, support the far end, or build that end earlier",
                [PartRef.of(model, index)],
                (p.x, p.y, p.z),
                level="error" if error else "warning",
            )
        )
    tip_step, tip = min(tipping, key=lambda t: t[1], default=(0, 1.0))
    if tip < WARN:
        report.issues.append(
            Issue(
                f"the model {'tips over' if tip == 0 else 'is close to tipping'} after step "
                f"{tip_step + 1} (score {tip:.2f}): its centre of weight is "
                f"{'outside' if tip == 0 else 'near the edge of'} the footprint on the table. "
                "Widen the base or move weight over it",
                [],
                None,
                level="error" if tip < FAIL else "warning",
            )
        )
    return report
