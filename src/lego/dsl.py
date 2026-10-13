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
from lego.parts import Cell, Part

ROTATIONS = (0, 90, 180, 270)
# Slope face direction → rotation (the unrotated slope faces −z, "front"; see ldraw.R(θ)).
FACINGS = {"front": 0, "left": 90, "back": 180, "right": 270}


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

    def brick(self, size: str, *, x: int, y: int, z: int, color: str | int, rot: int = 0) -> None:
        self._place("brick", size, x=x, y=y, z=z, color=color, rot=rot)

    def plate(self, size: str, *, x: int, y: int, z: int, color: str | int, rot: int = 0) -> None:
        self._place("plate", size, x=x, y=y, z=z, color=color, rot=rot)

    def slope(
        self, size: str, *, x: int, y: int, z: int, color: str | int, facing: str = "front"
    ) -> None:
        """45° slope, 2 studs deep ("2x1", "2x2", "2x4"); `facing` is where the sloped face
        points: "front" (−z), "back" (+z), "left" (−x), "right" (+x). Studs only on the row
        opposite the face."""
        self._place_slope("slope", size, x=x, y=y, z=z, color=color, facing=facing)

    def inverted_slope(
        self, size: str, *, x: int, y: int, z: int, color: str | int, facing: str = "front"
    ) -> None:
        """Upside-down 45° slope ("2x1", "2x2"): full studs on top, sloped underside points to
        `facing`; only the row opposite the face can sit on studs below."""
        self._place_slope("inverted_slope", size, x=x, y=y, z=z, color=color, facing=facing)

    def _place_slope(
        self, kind: str, size: str, *, x: int, y: int, z: int, color: str | int, facing: str
    ) -> None:
        shown = f"facing={facing!r}"
        if facing not in FACINGS:
            call = f"{kind}({size!r}, x={x!r}, y={y!r}, z={z!r}, color={color!r}, {shown})"
            raise DesignError(f"{call}: facing must be one of {', '.join(FACINGS)}")
        self._place(kind, size, x=x, y=y, z=z, color=color, rot=FACINGS[facing], shown=shown)

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
        *,
        x: int,
        y: int,
        z: int,
        color: str | int,
        rot: int,
        shown: str | None = None,
    ) -> None:
        last = shown if shown is not None else f"rot={rot!r}"
        call = f"{kind}({size!r}, x={x!r}, y={y!r}, z={z!r}, color={color!r}, {last})"
        if self.parent is not None:
            call = f"{self.name}.{call}"

        def fail(reason: str) -> DesignError:
            return DesignError(f"{call}: {reason}")

        if self._current_step is None:
            raise fail("parts must be placed inside `with m.step():`")
        if self._attached:
            raise fail("this sub-assembly is already attached; add all its parts before attaching")
        part = parts.PARTS.get((kind, size))
        if part is None:
            raise fail(f"unknown {kind} size; known: {', '.join(parts.sizes(kind))}")
        _check_grid(x, y, z, rot, fail)
        self.placements.append(
            Placement(part, x, y, z, rot, _color_code(color, fail), self._current_step)
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
