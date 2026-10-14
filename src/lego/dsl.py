"""Model-building API that Claude writes programs against.

Coordinates are integers on the brick grid:
  x, z  studs; a part occupies cells [x, x + w) × [z, z + d), w/d after rotation
  y     plates, upward; the part's bottom sits at level y and it fills [y, y + height)
  rot   0 | 90 | 180 | 270 degrees about the vertical axis; position stays the footprint's
        min corner, so rotating never moves the footprint's corner

Every part belongs to the step it was placed in:

    m = Model("wall")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="red")

Sub-assemblies are built separately in their own coordinates and steps, then attached in one
step of the main model (one level deep):

    leg = m.subassembly("leg")
    with leg.step():
        leg.brick("2x2", x=0, z=0, y=0, color="grey")
    with m.step():
        m.attach(leg, x=4, y=0, z=0)       # leg's (0, 0, 0) lands at (4, 0, 0)
"""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from lego import parts
from lego.parts import Cell, Component, Part

ROTATIONS = (0, 90, 180, 270)
# Slope face direction → rotation (the unrotated slope faces −z, "front"; see ldraw.R(θ)).
FACINGS = {"front": 0, "left": 90, "back": 180, "right": 270}
# Corner slopes face two ways; unrotated they face front (−z) and right (+x).
CORNER_FACINGS = {"front-right": 0, "front-left": 90, "back-left": 180, "back-right": 270}
SLOPE_ANGLES = {45: "slope", 33: "slope33", 65: "slope65", 75: "slope75"}


class DesignError(ValueError):
    """Invalid DSL call; the message names the offending call."""


@dataclass(frozen=True)
class Placement:
    part: Part
    x: int
    y: int
    z: int
    rot: int
    color: int  # LDraw color code
    step: int  # 0-based main step (for sub-assembly parts: the step that attaches them)
    sub: str | None = None  # attachment label, e.g. "leg" or "leg#2" for a second copy
    sub_index: int | None = None  # index of this part within the sub-assembly
    sub_step: int | None = None  # 0-based step within the sub-assembly
    color2: int | None = None  # color of the "second" components (glass, door, wheel rims)

    @property
    def size_x(self) -> int:
        return self.part.depth if self.rot in (90, 270) else self.part.width

    @property
    def size_z(self) -> int:
        return self.part.width if self.rot in (90, 270) else self.part.depth

    def cells(self) -> frozenset[Cell]:
        """World (x, z) cells covered by the footprint."""
        return frozenset(
            (self.x + dx, self.z + dz) for dx in range(self.size_x) for dz in range(self.size_z)
        )

    def levels(self) -> range:
        return range(self.y, self.y + self.part.height)

    def occupied(self) -> frozenset[tuple[int, int, int]]:
        """World (x, y, z) cells the part fills (footprint × height unless the part says
        otherwise: arches leave their opening free, wheels stick out beside the holder)."""
        if self.part.occupancy is None:
            return frozenset((x, y, z) for x, z in self.cells() for y in self.levels())
        return frozenset(
            (wx, self.y + level, wz)
            for cx, level, cz in self.part.occupancy
            for wx, wz in [self._to_world((cx, cz))]
        )

    @property
    def bottom(self) -> int:
        """Lowest occupied level (wheels reach below the holder)."""
        if self.part.occupancy is None:
            return self.y
        return self.y + min(level for _, level, _ in self.part.occupancy)

    @property
    def top(self) -> int:
        """Level just above the part, where its studs connect."""
        return self.y + self.part.height

    def stud_cells(self) -> frozenset[Cell]:
        """World (x, z) cells with a stud on top."""
        return frozenset(map(self._to_world, self.part.studs))

    def antistud_cells(self) -> frozenset[Cell]:
        """World (x, z) cells that accept a stud from below."""
        return frozenset(map(self._to_world, self.part.antistuds))

    def _to_world(self, cell: Cell) -> Cell:
        # Same rotation as the LDraw writer, R(θ) = [[c, 0, s], [0, 1, 0], [−s, 0, c]], applied
        # to the cell centre relative to the part centre. Doubled coordinates keep it integer.
        c = (1, 0, -1, 0)[self.rot // 90]
        s = (0, 1, 0, -1)[self.rot // 90]
        lx = 2 * cell[0] + 1 - self.part.width
        lz = 2 * cell[1] + 1 - self.part.depth
        wx = 2 * self.x + self.size_x + c * lx + s * lz
        wz = 2 * self.z + self.size_z - s * lx + c * lz
        return (wx - 1) // 2, (wz - 1) // 2


@dataclass(frozen=True)
class Attachment:
    label: str  # unique per attachment: sub-assembly name, "#2" etc. for repeats
    sub: Model
    x: int
    y: int
    z: int
    rot: int
    step: int  # 0-based main step


def component_color(component: Component, p: Placement) -> int:
    """LDraw color code of a compound part's component."""
    if component.color == "main":
        return p.color
    if component.color == "second" and p.color2 is not None:
        return p.color2
    return parts.colors()[component.color]


def turn_text(part: Part, rot: int) -> str:
    """How a DSL call shows the orientation of `part` turned by `rot`."""
    if part.turn == "facing":
        return f"facing={next(f for f, r in FACINGS.items() if r == rot)!r}"
    if part.turn == "corner":
        return f"facing={next(f for f, r in CORNER_FACINGS.items() if r == rot)!r}"
    return f"rot={rot}"


class Model:
    def __init__(self, name: str, parent: Model | None = None) -> None:
        self.name = name
        self.parent = parent
        self.placements: list[Placement] = []  # flattened: own parts and attached copies
        self.num_steps = 0
        self.subassemblies: dict[str, Model] = {}
        self.attachments: list[Attachment] = []
        self._current_step: int | None = None
        self._attached = False

    @contextmanager
    def step(self) -> Generator[None]:
        if self._current_step is not None:
            raise DesignError("step(): steps cannot be nested")
        self._current_step = self.num_steps
        count_before = len(self.placements)
        try:
            yield
        finally:
            self._current_step = None
        if len(self.placements) == count_before:
            raise DesignError(f"step {self.num_steps + 1} is empty")
        self.num_steps += 1

    def save(self, path: str | Path) -> None:
        """Write the model as an LDraw `.mpd` file."""
        from lego import ldraw  # ldraw imports this module

        ldraw.save(self, Path(path))

    # Basic parts, oriented with rot (0/90/180/270).

    def brick(self, size: str, *, x: int, y: int, z: int, color: str | int, rot: int = 0) -> None:
        self._place("brick", size, x, y, z, color, rot=rot)

    def plate(self, size: str, *, x: int, y: int, z: int, color: str | int, rot: int = 0) -> None:
        self._place("plate", size, x, y, z, color, rot=rot)

    def tile(self, size: str, *, x: int, y: int, z: int, color: str | int, rot: int = 0) -> None:
        """Plate-height part with a smooth top: nothing can be attached on it."""
        self._place("tile", size, x, y, z, color, rot=rot)

    def round_plate(self, size: str, *, x: int, y: int, z: int, color: str | int) -> None:
        self._place("round_plate", size, x, y, z, color)

    def round_brick(self, size: str, *, x: int, y: int, z: int, color: str | int) -> None:
        self._place("round_brick", size, x, y, z, color)

    def cone(self, size: str, *, x: int, y: int, z: int, color: str | int) -> None:
        self._place("cone", size, x, y, z, color)

    def arch(self, size: str, *, x: int, y: int, z: int, color: str | int, rot: int = 0) -> None:
        """Arch: studs along the top, sits on studs only at its two ends; the opening is free."""
        self._place("arch", size, x, y, z, color, rot=rot)

    def baseplate(
        self, size: str = "32x32", *, x: int, y: int, z: int, color: str | int = "green"
    ) -> None:
        """Thin baseplate to build on; nothing attaches underneath it."""
        self._place("baseplate", size, x, y, z, color)

    def window(
        self,
        size: str,
        *,
        x: int,
        y: int,
        z: int,
        color: str | int,
        rot: int = 0,
        glass_color: str | int = "trans_clear",
    ) -> None:
        """Window frame with its glass ("1x2x2", "1x2x3")."""
        self._place("window", size, x, y, z, color, rot=rot, color2=glass_color)

    def door(
        self,
        size: str,
        *,
        x: int,
        y: int,
        z: int,
        color: str | int,
        rot: int = 0,
        door_color: str | int = "red",
    ) -> None:
        """Door frame with its door ("1x4x6"); studs only on the middle two top cells."""
        self._place("door", size, x, y, z, color, rot=rot, color2=door_color)

    def wheels(
        self,
        size: str = "small",
        *,
        x: int,
        y: int,
        z: int,
        color: str | int,
        rot: int = 0,
        rim_color: str | int = "light_bluish_grey",
    ) -> None:
        """2x2 plate with two wheels (rims + black tyres) on its sides. Unrotated the axle runs
        along x: the wheels stick out one stud left and right and reach 2 plates below it."""
        self._place("wheels", size, x, y, z, color, rot=rot, color2=rim_color)

    # Slopes, oriented by the direction their sloped face points.

    def slope(
        self,
        size: str,
        *,
        x: int,
        y: int,
        z: int,
        color: str | int,
        facing: str = "front",
        angle: int = 45,
    ) -> None:
        """Straight slope; `facing` is where the sloped face points: "front" (−z), "back" (+z),
        "left" (−x), "right" (+x). Studs only on the row opposite the face.
        angle 45: "2x1", "2x2", "2x4"; 33: "3x2", "3x4"; 65 and 75: "2x1" (taller)."""
        if angle not in SLOPE_ANGLES:
            raise DesignError(
                f"slope({size!r}, ..., angle={angle!r}): angle must be one of "
                f"{', '.join(map(str, SLOPE_ANGLES))}"
            )
        self._place_facing(SLOPE_ANGLES[angle], size, x, y, z, color, facing)

    def inverted_slope(
        self, size: str, *, x: int, y: int, z: int, color: str | int, facing: str = "front"
    ) -> None:
        """Upside-down 45° slope ("2x1", "2x2"): full studs on top, sloped underside points to
        `facing`; only the row opposite the face can sit on studs below."""
        self._place_facing("inverted_slope", size, x, y, z, color, facing)

    def curved_slope(
        self, size: str, *, x: int, y: int, z: int, color: str | int, facing: str = "front"
    ) -> None:
        """Curved slope without studs ("2x1", "2x2" plate-and-a-bit high; "4x1", "4x2" brick
        high). Only the low front rows sit on studs; the high end is hollow underneath."""
        self._place_facing("curved_slope", size, x, y, z, color, facing)

    def cheese_slope(
        self, size: str = "1x2", *, x: int, y: int, z: int, color: str | int, facing: str = "front"
    ) -> None:
        """Small 1x2 slope, 2 plates high, no studs."""
        self._place_facing("cheese_slope", size, x, y, z, color, facing)

    def corner_slope(
        self,
        corner: str,
        *,
        x: int,
        y: int,
        z: int,
        color: str | int,
        facing: str = "front-right",
    ) -> None:
        """2x2 corner slope, "outside" (convex, one stud) or "inside" (concave, three studs);
        `facing` names the two directions its faces point: "front-right", "front-left",
        "back-left", "back-right"."""
        if facing not in CORNER_FACINGS:
            raise DesignError(
                f"corner_slope({corner!r}, ..., facing={facing!r}): facing must be one of "
                f"{', '.join(CORNER_FACINGS)}"
            )
        self._place("corner_slope", corner, x, y, z, color, rot=CORNER_FACINGS[facing])

    def _place_facing(
        self, kind: str, size: str, x: int, y: int, z: int, color: str | int, facing: str
    ) -> None:
        if facing not in FACINGS:
            raise DesignError(
                f"{kind}({size!r}, ..., facing={facing!r}): facing must be one of "
                f"{', '.join(FACINGS)}"
            )
        self._place(kind, size, x, y, z, color, rot=FACINGS[facing])

    # Sub-assemblies.

    def subassembly(self, name: str) -> Model:
        """A part group built separately (own steps, own coordinates), attached later."""
        if self.parent is not None:
            raise DesignError(f"subassembly({name!r}): sub-assemblies cannot be nested")
        if not name or name in self.subassemblies or name == self.name:
            raise DesignError(f"subassembly({name!r}): name must be unique and non-empty")
        sub = Model(name, parent=self)
        self.subassemblies[name] = sub
        return sub

    def attach(self, sub: Model, *, x: int, y: int, z: int, rot: int = 0) -> None:
        """Attach a finished sub-assembly: its point (0, 0, 0) lands on (x, y, z), turned by rot.

        The same sub-assembly can be attached several times (e.g. two identical wheels).
        """
        call = f"attach({sub.name!r}, x={x!r}, y={y!r}, z={z!r}, rot={rot!r})"

        def fail(reason: str) -> DesignError:
            return DesignError(f"{call}: {reason}")

        if self._current_step is None:
            raise fail("attach inside `with m.step():`")
        if sub.parent is not self:
            raise fail("not a sub-assembly of this model (create it with m.subassembly)")
        if sub._current_step is not None or sub.num_steps == 0:
            raise fail("finish building the sub-assembly (at least one closed step) first")
        _check_grid(x, y, z, rot, fail)
        copies = sum(1 for a in self.attachments if a.sub is sub)
        label = sub.name if copies == 0 else f"{sub.name}#{copies + 1}"
        step = self._current_step
        self.attachments.append(Attachment(label, sub, x, y, z, rot, step))
        for j, p in enumerate(sub.placements):
            self.placements.append(_moved(p, x, y, z, rot, step, label, j))
        sub._attached = True

    def _place(
        self,
        kind: str,
        size: str,
        x: int,
        y: int,
        z: int,
        color: str | int,
        *,
        rot: int = 0,
        color2: str | int | None = None,
    ) -> None:
        """The one place every part goes through (the LDraw reader uses it too)."""
        part = parts.PARTS.get((kind, size))
        shown = turn_text(part, rot) if part and rot in ROTATIONS else f"rot={rot!r}"
        extra = f", {part.extra_arg}" if part and part.extra_arg else ""
        second = f", {part.second_param}={color2!r}" if part and part.second_param else ""
        method = part.call if part else kind
        args = f"x={x!r}, y={y!r}, z={z!r}, color={color!r}, {shown}{extra}{second}"
        call = f"{method}({size!r}, {args})"
        if self.parent is not None:
            call = f"{self.name}.{call}"

        def fail(reason: str) -> DesignError:
            return DesignError(f"{call}: {reason}")

        if self._current_step is None:
            raise fail("parts must be placed inside `with m.step():`")
        if self._attached:
            raise fail("this sub-assembly is already attached; add all its parts before attaching")
        if part is None:
            raise fail(f"unknown {kind} size; known: {', '.join(parts.sizes(kind))}")
        _check_grid(x, y, z, rot, fail)
        code2 = None
        if part.second_param:
            code2 = _color_code(part.second_default if color2 is None else color2, fail)
        self.placements.append(
            Placement(
                part, x, y, z, rot, _color_code(color, fail), self._current_step, color2=code2
            )
        )


def _check_grid(x: int, y: int, z: int, rot: int, fail: Callable[[str], DesignError]) -> None:
    for axis, value in (("x", x), ("y", y), ("z", z)):
        # bool is an int subclass; reject it explicitly.
        if not isinstance(value, int) or isinstance(value, bool):
            raise fail(f"{axis} must be an integer on the grid")
    if rot not in ROTATIONS:
        raise fail(f"rot must be one of {ROTATIONS}")


def _moved(
    p: Placement, x: int, y: int, z: int, rot: int, step: int, label: str, j: int
) -> Placement:
    """`p` (in sub-assembly coordinates) turned by `rot` about the origin and moved to (x, y, z).

    Uses the LDraw rotation R(θ) on the footprint centre; doubled coordinates keep it exact.
    """
    c = (1, 0, -1, 0)[rot // 90]
    s = (0, 1, 0, -1)[rot // 90]
    cx2 = 2 * p.x + p.size_x  # doubled centre
    cz2 = 2 * p.z + p.size_z
    wx2 = c * cx2 + s * cz2
    wz2 = -s * cx2 + c * cz2
    new_rot = (p.rot + rot) % 360
    turned = Placement(p.part, 0, 0, 0, new_rot, p.color, step)
    return Placement(
        p.part,
        x + (wx2 - turned.size_x) // 2,
        y + p.y,
        z + (wz2 - turned.size_z) // 2,
        new_rot,
        p.color,
        step,
        sub=label,
        sub_index=j,
        sub_step=p.step,
        color2=p.color2,
    )


def _color_code(color: str | int, fail: Callable[[str], DesignError]) -> int:
    table = parts.colors()
    if isinstance(color, int) and not isinstance(color, bool):
        if color not in table.values():
            raise fail("unknown LDraw color code")
        return color
    if isinstance(color, str) and color.lower() in table:
        return table[color.lower()]
    raise fail("unknown color name (LDConfig names, e.g. 'red', 'light_bluish_grey')")
