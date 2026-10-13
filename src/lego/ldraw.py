"""Convert models to LDraw `.mpd` text and back.

LDraw conventions: 20 LDU per stud, 8 LDU per plate, −Y is up. Bricks and plates have their
origin at the centre of the top face (stud base), so a part filling levels [y, y + h) has its
origin at LDraw Y = −(y + h) · 8. Rotations are about the vertical axis:
    R(θ) = [[cos θ, 0, sin θ], [0, 1, 0], [−sin θ, 0, cos θ]]
"""

import math
from pathlib import Path

from lego.dsl import ROTATIONS, DesignError, Model, Placement
from lego.parts import LDU_PER_PLATE, LDU_PER_STUD, PARTS_BY_ID

type Matrix = tuple[int, ...]

_HALF_STUD = LDU_PER_STUD // 2


class LDrawError(ValueError):
    pass


def _matrix(rot: int) -> Matrix:
    c = round(math.cos(math.radians(rot)))
    s = round(math.sin(math.radians(rot)))
    return (c, 0, s, 0, 1, 0, -s, 0, c)


_ROT_BY_MATRIX: dict[Matrix, int] = {_matrix(r): r for r in ROTATIONS}


def _line(p: Placement) -> str:
    x = p.x * LDU_PER_STUD + p.size_x * _HALF_STUD
    z = p.z * LDU_PER_STUD + p.size_z * _HALF_STUD
    y = -(p.y + p.part.height) * LDU_PER_PLATE
    matrix = " ".join(map(str, _matrix(p.rot)))
    return f"1 {p.color} {x} {y} {z} {matrix} {p.part.filename}"


def _file_name(model: Model) -> str:
    stem = "".join(ch if ch.isalnum() else "_" for ch in model.name.lower()).strip("_")
    return f"{stem or 'model'}.ldr"


def dumps(model: Model) -> str:
    name = _file_name(model)
    lines = [f"0 FILE {name}", f"0 {model.name}", f"0 Name: {name}", "0 Author: lego-designer"]
    for step in range(model.num_steps):
        lines += [_line(p) for p in model.placements if p.step == step]
        lines.append("0 STEP")
    lines.append("0 NOFILE")
    return "\n".join(lines) + "\n"


def save(model: Model, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(model))


def _parse_part_line(tokens: list[str], lineno: int) -> tuple[str, dict[str, int | str]]:
    """Return (kind method name, DSL keyword arguments incl. size) for one type-1 line."""

    def fail(reason: str) -> LDrawError:
        return LDrawError(f"line {lineno}: {reason}")

    if len(tokens) != 15:
        raise fail("expected 15 fields in a part line")
    filename = tokens[14].lower()
    part = PARTS_BY_ID.get(filename.removesuffix(".dat"))
    if part is None:
        raise fail(f"part {tokens[14]} is not in the supported vocabulary")
    try:
        color = int(tokens[1])
        x_ldu, y_ldu, z_ldu = (float(t) for t in tokens[2:5])
        matrix = tuple(round(float(t)) for t in tokens[5:14])
    except ValueError as e:
        raise fail(f"malformed number: {e}") from e
    rot = _ROT_BY_MATRIX.get(matrix)
    if rot is None or any(
        abs(float(t) - m) > 1e-6 for t, m in zip(tokens[5:14], matrix, strict=True)
    ):
        raise fail("rotation must be 0/90/180/270 degrees about the vertical axis")
    size_x, size_z = (part.depth, part.width) if rot in (90, 270) else (part.width, part.depth)

    def grid(value: float, unit: int, what: str) -> int:
        cells = value / unit
        if abs(cells - round(cells)) > 1e-6:
            raise fail(f"{part.filename} {what} is not on the brick grid")
        return round(cells)

    x = grid(x_ldu - size_x * _HALF_STUD, LDU_PER_STUD, "x position")
    z = grid(z_ldu - size_z * _HALF_STUD, LDU_PER_STUD, "z position")
    y = grid(-y_ldu, LDU_PER_PLATE, "height") - part.height
    return part.kind, {"size": part.size, "x": x, "y": y, "z": z, "rot": rot, "color": color}


def loads(text: str, name: str = "model") -> Model:
    steps: list[list[tuple[int, str, dict[str, int | str]]]] = [[]]
    files = 0
    for lineno, raw in enumerate(text.splitlines(), start=1):
        tokens = raw.split()
        if not tokens:
            continue
        if tokens[:2] == ["0", "FILE"]:
            files += 1
            if files > 1:
                raise LDrawError(f"line {lineno}: submodels are not supported yet")
        elif tokens[:2] == ["0", "STEP"]:
            steps.append([])
        elif tokens[0] == "1":
            kind, kwargs = _parse_part_line(tokens, lineno)
            steps[-1].append((lineno, kind, kwargs))
        elif tokens[0] in ("2", "3", "4", "5"):
            raise LDrawError(f"line {lineno}: raw geometry is not supported")

    model = Model(name)
    for step in (s for s in steps if s):
        with model.step():
            for lineno, kind, kwargs in step:
                size = str(kwargs.pop("size"))
                try:
                    getattr(model, kind)(size, **kwargs)
                except DesignError as e:
                    raise LDrawError(f"line {lineno}: {e}") from e
    return model


def load(path: Path) -> Model:
    return loads(path.read_text(), name=path.stem)
