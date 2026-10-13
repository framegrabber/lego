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
"""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from lego import parts
from lego.parts import Cell, Part

ROTATIONS = (0, 90, 180, 270)


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
    step: int  # 0-based

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


class Model:
    def __init__(self, name: str) -> None:
        self.name = name
        self.placements: list[Placement] = []
        self.num_steps = 0
        self._current_step: int | None = None

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

    def _place(
        self, kind: str, size: str, *, x: int, y: int, z: int, color: str | int, rot: int
    ) -> None:
        call = f"{kind}({size!r}, x={x!r}, y={y!r}, z={z!r}, color={color!r}, rot={rot!r})"

        def fail(reason: str) -> DesignError:
            return DesignError(f"{call}: {reason}")

        if self._current_step is None:
            raise fail("parts must be placed inside `with m.step():`")
        part = parts.PARTS.get((kind, size))
        if part is None:
            raise fail(f"unknown {kind} size; known: {', '.join(parts.sizes(kind))}")
        for axis, value in (("x", x), ("y", y), ("z", z)):
            # bool is an int subclass; reject it explicitly.
            if not isinstance(value, int) or isinstance(value, bool):
                raise fail(f"{axis} must be an integer on the grid")
        if rot not in ROTATIONS:
            raise fail(f"rot must be one of {ROTATIONS}")
        self.placements.append(
            Placement(part, x, y, z, rot, _color_code(color, fail), self._current_step)
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
