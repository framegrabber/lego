"""Supported part vocabulary and the LDraw color table.

Grid units: 1 stud = 20 LDU horizontally, 1 plate = 8 LDU vertically (a brick is 3 plates).
Every part is described unrotated: `width` studs along x, `depth` studs along z, `height` plates.
Stud and anti-stud cells are listed in that unrotated frame, relative to the footprint's min corner.
Slope-like parts face −z when unrotated (their high side and stud row are at +z).

The geometry of every part (footprint, height, studs, anti-studs, origin) was read from the LDraw
library files and is re-checked against them by tests/test_parts_geometry.py.
"""

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from lego.paths import LDRAW_DIR

LDU_PER_STUD = 20
LDU_PER_PLATE = 8

type Cell = tuple[int, int]
type Matrix = tuple[int, int, int, int, int, int, int, int, int]

IDENTITY: Matrix = (1, 0, 0, 0, 1, 0, 0, 0, 1)


@dataclass(frozen=True)
class Component:
    """An extra LDraw part that always comes with a compound part (wheel, tyre, glass, door)."""

    ldraw_id: str
    name: str  # for the parts list
    offset: tuple[int, int, int]  # LDU from the main part's LDraw origin, unrotated, LDraw axes
    matrix: Matrix
    color: str  # "main", "second" (chosen in the DSL call) or a fixed LDraw color name


@dataclass(frozen=True)
class Part:
    ldraw_id: str
    kind: str  # e.g. "brick", "plate", "tile", "slope33", "wheels"
    size: str  # DSL size name, e.g. "2x4"
    width: int  # studs along x (unrotated)
    depth: int  # studs along z (unrotated)
    height: int  # plates
    studs: frozenset[Cell]  # cells with a stud on top
    antistuds: frozenset[Cell]  # cells that accept a stud from below
    name: str  # for the parts list, e.g. "2x4 brick"
    call: str  # DSL method that places it
    turn: str = "rot"  # how the DSL call orients it: "rot", "facing" or "corner"
    extra_arg: str = ""  # extra DSL argument shown in calls, e.g. "angle=33"
    # LDraw origin relative to (footprint centre x, top, footprint centre z), unrotated, LDU
    # with y pointing down. Slopes: stud-row centre; parts with their origin at the bottom: y > 0.
    origin: tuple[int, int, int] = (0, 0, 0)
    # Occupied (x, level, z) cells relative to the min corner and bottom level; None = the full
    # footprint × height. Arches leave their opening free; wheels stick out beside the holder.
    occupancy: frozenset[tuple[int, int, int]] | None = None
    components: tuple[Component, ...] = ()
    second_param: str = ""  # DSL argument for the "second" component color
    second_default: str = ""

    @property
    def filename(self) -> str:
        return f"{self.ldraw_id}.dat"


def _rect(width: int, depth: int) -> frozenset[Cell]:
    return frozenset((x, z) for x in range(width) for z in range(depth))


def _box(x: range, levels: range, z: range) -> frozenset[tuple[int, int, int]]:
    return frozenset((cx, level, cz) for cx in x for level in levels for cz in z)


_HEIGHTS = {"brick": 3, "plate": 1, "tile": 1, "round_plate": 1, "round_brick": 3, "cone": 3}
_NAMES = {"round_plate": "round plate", "round_brick": "round brick"}


def _block(ldraw_id: str, kind: str, depth: int, width: int) -> Part:
    # Name "AxB" lists the short side first; in LDraw the long side runs along x.
    cells = _rect(width, depth)
    studs = frozenset() if kind == "tile" else cells
    size = f"{depth}x{width}"
    name = f"{size} {_NAMES.get(kind, kind)}"
    return Part(ldraw_id, kind, size, width, depth, _HEIGHTS[kind], studs, cells, name, kind)


def _slope(
    ldraw_id: str,
    kind: str,
    width: int,
    depth: int = 2,
    height: int = 3,
    angle: int = 45,
    inverted: bool = False,
) -> Part:
    """Straight slopes: the sloped face points to −z; the stud row (normal slopes) or the row
    that sits on studs (inverted slopes) is the back row z = depth − 1."""
    full = _rect(width, depth)
    back_row = frozenset((x, depth - 1) for x in range(width))
    studs, antistuds = (full, back_row) if inverted else (back_row, full)
    label = "inverted slope" if inverted else f"slope {angle}°"
    return Part(
        ldraw_id,
        kind,
        f"{depth}x{width}",
        width,
        depth,
        height,
        studs,
        antistuds,
        f"{depth}x{width} {label}",
        "inverted_slope" if inverted else "slope",
        turn="facing",
        extra_arg="" if inverted or angle == 45 else f"angle={angle}",
        origin=(0, 0, (depth - 1) * 10),
    )


def _curved(
    ldraw_id: str,
    width: int,
    depth: int,
    height: int,
    antistud_rows: int,
    origin_y: int,
    occupancy: frozenset[tuple[int, int, int]] | None = None,
) -> Part:
    """Curved slopes have no studs; only their low front rows sit on studs (they are hollow under
    the curve)."""
    antistuds = frozenset((x, z) for x in range(width) for z in range(antistud_rows))
    return Part(
        ldraw_id,
        "curved_slope",
        f"{depth}x{width}",
        width,
        depth,
        height,
        frozenset(),
        antistuds,
        f"{depth}x{width} curved slope",
        "curved_slope",
        turn="facing",
        origin=(0, origin_y, 0),
        occupancy=occupancy,
    )


def _arch(ldraw_id: str, width: int, height: int, column_levels: list[int]) -> Part:
    """Arches: studs along the top, they sit on studs only at their two ends, and the opening
    below stays free. column_levels[i] = levels occupied from the top in column i."""
    occupancy = frozenset(
        (x, level, 0) for x, n in enumerate(column_levels) for level in range(height - n, height)
    )
    return Part(
        ldraw_id,
        "arch",
        f"1x{width}",
        width,
        1,
        height,
        _rect(width, 1),
        frozenset({(0, 0), (width - 1, 0)}),
        f"1x{width} arch",
        "arch",
        occupancy=occupancy,
    )


def _frame(
    ldraw_id: str,
    kind: str,
    size: str,
    width: int,
    height: int,
    studs: frozenset[Cell],
    insert: Component,
    second_param: str,
    second_default: str,
) -> Part:
    return Part(
        ldraw_id,
        kind,
        size,
        width,
        1,
        height,
        studs,
        _rect(width, 1),
        f"{size} {kind} frame",
        kind,
        components=(insert,),
        second_param=second_param,
        second_default=second_default,
    )


_ROT90 = (0, 0, 1, 0, 1, 0, -1, 0, 0)
_ROT270 = (0, 0, -1, 0, 1, 0, 1, 0, 0)

PARTS: dict[tuple[str, str], Part] = {
    (p.kind, p.size): p
    for p in [
        # Bricks and plates (name "AxB": A studs along z, B along x).
        *(
            _block(i, "brick", d, w)
            for i, d, w in [
                ("3005", 1, 1),
                ("3004", 1, 2),
                ("3622", 1, 3),
                ("3010", 1, 4),
                ("3009", 1, 6),
                ("3008", 1, 8),
                ("6111", 1, 10),
                ("6112", 1, 12),
                ("3003", 2, 2),
                ("3002", 2, 3),
                ("3001", 2, 4),
                ("2456", 2, 6),
                ("3007", 2, 8),
                ("3006", 2, 10),
            ]
        ),
        *(
            _block(i, "plate", d, w)
            for i, d, w in [
                ("3024", 1, 1),
                ("3023b", 1, 2),
                ("3623", 1, 3),
                ("3710", 1, 4),
                ("3666", 1, 6),
                ("3460", 1, 8),
                ("3022", 2, 2),
                ("3021", 2, 3),
                ("3020", 2, 4),
                ("3795", 2, 6),
                ("3034", 2, 8),
                ("3832", 2, 10),
                ("3031", 4, 4),
                ("3032", 4, 6),
                ("3035", 4, 8),
                ("3030", 4, 10),
                ("3958", 6, 6),
                ("3036", 6, 8),
                ("3033", 6, 10),
                ("41539", 8, 8),
                ("91405", 16, 16),
            ]
        ),
        *(
            _block(i, "tile", d, w)
            for i, d, w in [
                ("3070b", 1, 1),
                ("3069b", 1, 2),
                ("2431", 1, 4),
                ("6636", 1, 6),
                ("4162", 1, 8),
                ("3068b", 2, 2),
                ("87079", 2, 4),
            ]
        ),
        _block("6141", "round_plate", 1, 1),
        _block("3062b", "round_brick", 1, 1),
        _block("3941", "round_brick", 2, 2),
        _block("4589", "cone", 1, 1),
        Part(
            "3811",
            "baseplate",
            "32x32",
            32,
            32,
            1,
            _rect(32, 32),
            frozenset(),
            "32x32 baseplate",
            "baseplate",
        ),
        # Slopes (face −z when unrotated).
        _slope("3040b", "slope", 1),
        _slope("3039", "slope", 2),
        _slope("3037", "slope", 4),
        _slope("3298", "slope33", 2, depth=3, angle=33),
        _slope("3297", "slope33", 4, depth=3, angle=33),
        _slope("60481a", "slope65", 1, height=6, angle=65),
        _slope("4460b", "slope75", 1, height=9, angle=75),
        _slope("3665b", "inverted_slope", 1, inverted=True),
        _slope("3660b", "inverted_slope", 2, inverted=True),
        Part(
            "85984",
            "cheese_slope",
            "1x2",
            2,
            1,
            2,
            frozenset(),
            _rect(2, 1),
            "1x2 cheese slope",
            "cheese_slope",
            turn="facing",
            origin=(0, 16, 0),
        ),
        _curved("15068", 2, 2, 2, 1, origin_y=16),
        _curved("11477", 1, 2, 2, 1, origin_y=16),
        _curved(
            "93606",
            2,
            4,
            3,
            2,
            origin_y=0,
            occupancy=_box(range(2), range(3), range(2))
            | _box(range(2), range(1, 3), range(2, 3))
            | _box(range(2), range(2, 3), range(3, 4)),
        ),
        _curved(
            "61678",
            1,
            4,
            3,
            2,
            origin_y=0,
            occupancy=_box(range(1), range(3), range(2))
            | _box(range(1), range(1, 3), range(2, 3))
            | _box(range(1), range(2, 3), range(3, 4)),
        ),
        # Corner slopes: unrotated, the faces point front (−z) and right (+x).
        Part(
            "3045",
            "corner_slope",
            "outside",
            2,
            2,
            3,
            frozenset({(0, 1)}),
            _rect(2, 2),
            "2x2 outside corner slope",
            "corner_slope",
            turn="corner",
            origin=(-10, 0, 10),
        ),
        Part(
            "3046",
            "corner_slope",
            "inside",
            2,
            2,
            3,
            frozenset({(0, 0), (0, 1), (1, 1)}),
            _rect(2, 2),
            "2x2 inside corner slope",
            "corner_slope",
            turn="corner",
            origin=(-10, 0, 10),
        ),
        # Arches: the opening below stays free.
        _arch("3659", 4, 3, [3, 2, 2, 3]),
        _arch("3455", 6, 3, [3, 3, 2, 2, 3, 3]),
        _arch("3308a", 8, 6, [6, 6, 3, 2, 2, 3, 6, 6]),
        # Windows and doors come with their glass / door (positions from the library's own
        # 60592c01 / 60593c01 assemblies and the door frame's hinge holes).
        _frame(
            "60592",
            "window",
            "1x2x2",
            2,
            6,
            _rect(2, 1),
            Component("60601", "1x2x2 window glass", (0, 0, 0), IDENTITY, "second"),
            "glass_color",
            "trans_clear",
        ),
        _frame(
            "60593",
            "window",
            "1x2x3",
            2,
            9,
            _rect(2, 1),
            Component("60602", "1x2x3 window glass", (0, 0, 0), IDENTITY, "second"),
            "glass_color",
            "trans_clear",
        ),
        _frame(
            "60596",
            "door",
            "1x4x6",
            4,
            18,
            frozenset({(1, 0), (2, 0)}),
            Component("60623", "1x4x6 door", (-32, 0, 5), IDENTITY, "second"),
            "door_color",
            "red",
        ),
        # Wheels: a 2x2 plate with wheel pins plus two rims with tyres (as in the library's
        # car.ldr). The wheels stick out one stud on each side and reach 2 plates lower.
        Part(
            "4600",
            "wheels",
            "small",
            2,
            2,
            1,
            _rect(2, 2),
            _rect(2, 2),
            "2x2 plate with wheel pins",
            "wheels",
            occupancy=_box(range(2), range(1), range(2))
            | _box(range(-1, 0), range(-2, 3), range(2))
            | _box(range(2, 3), range(-2, 3), range(2)),
            components=(
                Component("4624", "wheel rim 6.4x8", (-30, 6, 0), _ROT90, "second"),
                Component("3641", "tyre 6/50x8", (-30, 6, 0), _ROT90, "black"),
                Component("4624", "wheel rim 6.4x8", (30, 6, 0), _ROT270, "second"),
                Component("3641", "tyre 6/50x8", (30, 6, 0), _ROT270, "black"),
            ),
            second_param="rim_color",
            second_default="light_bluish_grey",
        ),
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
