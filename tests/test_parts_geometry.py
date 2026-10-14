"""Every part's declared geometry matches its LDraw library file.

Re-derives footprint, height, origin, top studs and bottom contact from the .dat files, so a
typo in parts.py (wrong size, stud row on the wrong side, missing origin offset) fails here.
"""

import math
import re
from functools import cache

import pytest

from lego.parts import PARTS, Part
from lego.paths import LDRAW_DIR

pytestmark = pytest.mark.ldraw

type Vec = tuple[float, float, float]
type Mat = tuple[tuple[float, ...], ...]

_I: Mat = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
_TOP_STUD = re.compile(r"stud(2a?|6a?|10|15|17a)?\.dat")


def _find(name: str):
    name = name.replace("\\", "/").lower()
    for folder in ("parts", "p"):
        path = LDRAW_DIR / folder / name
        if path.exists():
            return path
    raise FileNotFoundError(name)


def _apply(m: Mat, o: Vec, p: Vec) -> Vec:
    return tuple(sum(m[r][c] * p[c] for c in range(3)) + o[r] for r in range(3))  # type: ignore[return-value]


@cache
def _geometry(name: str) -> tuple[tuple[Vec, ...], tuple[Vec, ...]]:
    """(all polygon vertices, top-stud positions) of a library file, in its own coordinates."""
    points: list[Vec] = []
    studs: list[Vec] = []
    for line in _find(name).read_text(errors="ignore").splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "1":
            v = [float(x) for x in t[2:14]]
            sub = " ".join(t[14:]).replace("\\", "/").lower()
            m: Mat = (tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12]))
            o: Vec = (v[0], v[1], v[2])
            base = sub.split("/")[-1]
            if _TOP_STUD.fullmatch(base):
                studs.append(o)
            sub_points, sub_studs = _geometry(sub)
            points += [_apply(m, o, p) for p in sub_points]
            if not base.startswith("stud"):
                studs += [_apply(m, o, s) for s in sub_studs]
        elif t[0] in ("3", "4"):
            n = int(t[0])
            f = [float(x) for x in t[2 : 2 + 3 * n]]
            points += [(f[i], f[i + 1], f[i + 2]) for i in range(0, 3 * n, 3)]
    return tuple(points), tuple(studs)


def _measure(part: Part):
    points, studs = _geometry(part.filename)
    xs, ys, zs = zip(*points, strict=True)
    body_top = min(y for y in ys if not -4.01 < y < -0.01)  # stud cylinders sit in (-4, 0)
    x0, z0 = min(xs), min(zs)
    stud_cells = {
        (math.floor((s[0] - x0) / 20), math.floor((s[2] - z0) / 20))
        for s in studs
        if abs(s[1] - body_top) < 0.6
    }
    bottom = max(ys)
    contact = set()
    for cx in range(part.width):
        for cz in range(part.depth):
            lo_x, hi_x = x0 + 20 * cx + 2.5, x0 + 20 * (cx + 1) - 2.5
            lo_z, hi_z = z0 + 20 * cz + 2.5, z0 + 20 * (cz + 1) - 2.5
            if any(
                abs(p[1] - bottom) < 0.6 and lo_x < p[0] < hi_x and lo_z < p[2] < hi_z
                for p in points
            ):
                contact.add((cx, cz))
    return {
        "width": (max(xs) - x0) / 20,
        "depth": (max(zs) - z0) / 20,
        "height": (bottom - body_top) / 8,
        "centre": ((x0 + max(xs)) / 2, (z0 + max(zs)) / 2),
        "top": body_top,
        "studs": stud_cells,
        "contact": contact,
    }


# The wheel holder's pins stick out past its footprint and hang below it; it is checked by
# rendering (models/examples/car.py) instead.
CHECKED = [p for p in PARTS.values() if p.kind != "wheels"]


@pytest.mark.parametrize("part", CHECKED, ids=lambda p: f"{p.kind}-{p.size}-{p.ldraw_id}")
def test_part_matches_its_library_file(part: Part):
    g = _measure(part)
    assert round(g["width"]) == part.width
    assert round(g["depth"]) == part.depth
    # Baseplates are half a plate thick and the cheese slope is 15.6 LDU: they still fill a level.
    assert math.ceil(g["height"] - 0.1) == part.height
    assert (-g["centre"][0], -g["centre"][1]) == (part.origin[0], part.origin[2])
    assert abs(g["top"] + part.origin[1]) < 0.5  # the origin sits origin[1] LDU below the top
    assert g["studs"] == set(part.studs)
    # Never claim an anti-stud where the part doesn't reach its bottom face.
    assert set(part.antistuds) <= g["contact"]


def test_compound_components_exist_in_the_library():
    for part in PARTS.values():
        for c in part.components:
            assert (LDRAW_DIR / "parts" / f"{c.ldraw_id}.dat").is_file(), c
