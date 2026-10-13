"""B3: the stud/anti-stud connection graph of the model is one component."""

from collections import Counter
from collections.abc import Iterable

from lego.check.report import Issue, PartRef, Report
from lego.dsl import Model, Placement


def connections(placements: list[Placement]) -> Counter[tuple[int, int]]:
    """(lower index, upper index) → number of studs joining them.

    A joins B when B sits exactly on A's top level and one of A's studs lies under one of B's
    anti-studs. Parts that only touch side by side are not connected.
    """
    studs: dict[tuple[int, int, int], int] = {}
    for i, p in enumerate(placements):
        for x, z in p.stud_cells():
            studs[(x, p.top, z)] = i
    joined: Counter[tuple[int, int]] = Counter()
    for j, p in enumerate(placements):
        for x, z in p.antistud_cells():
            i = studs.get((x, p.y, z))
            if i is not None:
                joined[(i, j)] += 1
    return joined


def components(n: int, edges: Iterable[tuple[int, int]]) -> list[list[int]]:
    """Connected components of parts 0..n-1, each sorted, largest first (ties: lowest index)."""
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in edges:
        parent[find(a)] = find(b)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: (-len(g), g[0]))


def connected(model: Model) -> Report:
    report = Report("B3", "connected")
    groups = components(len(model.placements), connections(model.placements))
    for group in groups[1:]:
        first = model.placements[group[0]]
        report.issues.append(
            Issue(
                f"{len(group)} part(s) not connected to the main structure "
                f"({len(groups[0])} parts); nothing joins them by studs",
                [PartRef.of(model, i) for i in group],
                (first.x, first.y, first.z),
            )
        )
    return report
