"""Supported part vocabulary and the LDraw color table.

Grid units: 1 stud = 20 LDU horizontally, 1 plate = 8 LDU vertically (a brick is 3 plates).
Every part is described unrotated: `width` studs along x, `depth` studs along z, `height` plates.
Stud and anti-stud cells are listed in that unrotated frame, relative to the footprint's min corner.
"""

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from lego.paths import LDRAW_DIR

LDU_PER_STUD = 20
LDU_PER_PLATE = 8

type Cell = tuple[int, int]


@dataclass(frozen=True)
class Part:
    ldraw_id: str
    kind: str  # "brick" | "plate"
    size: str  # e.g. "2x4" (DSL name)
    width: int  # studs along x (unrotated)
    depth: int  # studs along z (unrotated)
    height: int  # plates
    studs: frozenset[Cell]  # cells with a stud on top
    antistuds: frozenset[Cell]  # cells that accept a stud from below

    @property
    def filename(self) -> str:
        return f"{self.ldraw_id}.dat"


def _rect(width: int, depth: int) -> frozenset[Cell]:
    return frozenset((x, z) for x in range(width) for z in range(depth))


def _block(ldraw_id: str, kind: str, depth: int, width: int) -> Part:
    # Name "AxB" lists the short side first; in LDraw the long side runs along x.
    height = 3 if kind == "brick" else 1
    cells = _rect(width, depth)
    return Part(ldraw_id, kind, f"{depth}x{width}", width, depth, height, cells, cells)


PARTS: dict[tuple[str, str], Part] = {
    (p.kind, p.size): p
    for p in [
        _block("3005", "brick", 1, 1),
        _block("3004", "brick", 1, 2),
        _block("3010", "brick", 1, 4),
        _block("3003", "brick", 2, 2),
        _block("3001", "brick", 2, 4),
        _block("3024", "plate", 1, 1),
        _block("3023b", "plate", 1, 2),
        _block("3710", "plate", 1, 4),
        _block("3022", "plate", 2, 2),
        _block("3020", "plate", 2, 4),
    ]
}
PARTS_BY_ID: dict[str, Part] = {p.ldraw_id: p for p in PARTS.values()}


def sizes(kind: str) -> list[str]:
    return [size for k, size in PARTS if k == kind]


_COLOUR_RE = re.compile(r"^0\s+!COLOUR\s+(\S+)\s+CODE\s+(\d+)", re.MULTILINE)


@cache
def colors(ldconfig: Path = LDRAW_DIR / "LDConfig.ldr") -> dict[str, int]:
    """Color name (lowercase, e.g. "light_bluish_grey") → LDraw color code."""
    if not ldconfig.is_file():
        raise FileNotFoundError(f"{ldconfig} not found; run `lego setup`")
    return {name.lower(): int(code) for name, code in _COLOUR_RE.findall(ldconfig.read_text())}
