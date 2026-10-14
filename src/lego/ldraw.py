"""Convert models to LDraw `.mpd` text and back.

LDraw conventions: 20 LDU per stud, 8 LDU per plate, −Y is up. Bricks and plates have their
origin at the centre of the top face (stud base), so a part filling levels [y, y + h) has its
origin at LDraw Y = −(y + h) · 8. Rotations are about the vertical axis:
    R(θ) = [[cos θ, 0, sin θ], [0, 1, 0], [−sin θ, 0, cos θ]]
"""

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from lego.dsl import ROTATIONS, Attachment, DesignError, Model, Placement, component_color
from lego.parts import LDU_PER_PLATE, LDU_PER_STUD, PARTS_BY_ID, Part
from lego.paths import write_atomic

type Matrix = tuple[int, ...]
type _Fail = Callable[[str], LDrawError]

_HALF_STUD = LDU_PER_STUD // 2


class LDrawError(ValueError):
    pass


def _matrix(rot: int) -> Matrix:
    c = round(math.cos(math.radians(rot)))
    s = round(math.sin(math.radians(rot)))
    return (c, 0, s, 0, 1, 0, -s, 0, c)


_ROT_BY_MATRIX: dict[Matrix, int] = {_matrix(r): r for r in ROTATIONS}


def _rotate(r: Matrix, v: tuple[int, int, int]) -> tuple[int, int, int]:
    return (
        r[0] * v[0] + r[1] * v[1] + r[2] * v[2],
        r[3] * v[0] + r[4] * v[1] + r[5] * v[2],
        r[6] * v[0] + r[7] * v[1] + r[8] * v[2],
    )


def _compose(a: Matrix, b: Matrix) -> Matrix:
    return tuple(
        sum(a[3 * i + k] * b[3 * k + j] for k in range(3)) for i in range(3) for j in range(3)
    )


def _origin(p: Placement) -> tuple[int, int, int]:
    """LDraw position of the part's origin: footprint centre and top, plus its rotated offset."""
    ox, oy, oz = _rotate(_matrix(p.rot), p.part.origin)
    x = p.x * LDU_PER_STUD + p.size_x * _HALF_STUD + ox
    z = p.z * LDU_PER_STUD + p.size_z * _HALF_STUD + oz
    y = -(p.y + p.part.height) * LDU_PER_PLATE + oy
    return x, y, z


def _line(p: Placement) -> str:
    x, y, z = _origin(p)
    matrix = " ".join(map(str, _matrix(p.rot)))
    return f"1 {p.color} {x} {y} {z} {matrix} {p.part.filename}"


def _lines(p: Placement) -> list[str]:
    """The part's LDraw lines; compound parts (wheels, windows, doors) are announced by a
    `0 !LEGO COMPOUND n` comment and followed by their n component lines."""
    if not p.part.components:
        return [_line(p)]
    r = _matrix(p.rot)
    origin = _origin(p)
    lines = [f"0 !LEGO COMPOUND {len(p.part.components)}", _line(p)]
    for c in p.part.components:
        dx, dy, dz = _rotate(r, c.offset)
        color = component_color(c, p)
        matrix = " ".join(map(str, _compose(r, c.matrix)))
        x, y, z = origin[0] + dx, origin[1] + dy, origin[2] + dz
        lines.append(f"1 {color} {x} {y} {z} {matrix} {c.ldraw_id}.dat")
    return lines


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_") or "model"


def file_name(model: Model) -> str:
    if model.parent is not None:
        return f"{_slug(model.parent.name)}__{_slug(model.name)}.ldr"
    return f"{_slug(model.name)}.ldr"


def _header(model: Model) -> list[str]:
    name = file_name(model)
    return [f"0 FILE {name}", f"0 {model.name}", f"0 Name: {name}", "0 Author: lego-designer"]


def _attachment_line(a: Attachment) -> str:
    matrix = " ".join(map(str, _matrix(a.rot)))
    x, y, z = a.x * LDU_PER_STUD, -a.y * LDU_PER_PLATE, a.z * LDU_PER_STUD
    return f"1 16 {x} {y} {z} {matrix} {file_name(a.sub)}"


def dumps(model: Model) -> str:
    """Main model first, then one `0 FILE` section per attached sub-assembly."""
    by_label = {a.label: a for a in model.attachments}
    lines = _header(model)
    for step in range(model.num_steps):
        for p in model.placements:
            if p.step != step:
                continue
            if p.sub is None:
                lines += _lines(p)
            elif p.sub_index == 0:
                lines.append(_attachment_line(by_label[p.sub]))
        lines.append("0 STEP")
    lines.append("0 NOFILE")
    attached = {a.sub.name: a.sub for a in model.attachments}
    for sub in attached.values():
        lines += _header(sub)
        for step in range(sub.num_steps):
            lines += [line for p in sub.placements if p.step == step for line in _lines(p)]
            lines.append("0 STEP")
        lines.append("0 NOFILE")
    return "\n".join(lines) + "\n"


def save(model: Model, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, dumps(model))


def _rotation(tokens: list[str], fail: _Fail) -> int:
    try:
        matrix = tuple(round(float(t)) for t in tokens[5:14])
        exact = all(abs(float(t) - m) <= 1e-6 for t, m in zip(tokens[5:14], matrix, strict=True))
    except ValueError as e:
        raise fail(f"malformed number: {e}") from e
    rot = _ROT_BY_MATRIX.get(matrix)
    if rot is None or not exact:
        raise fail("rotation must be 0/90/180/270 degrees about the vertical axis")
    return rot


def _grid(value: float, unit: int, what: str, fail: _Fail) -> int:
    cells = value / unit
    if abs(cells - round(cells)) > 1e-6:
        raise fail(f"{what} is not on the brick grid")
    return round(cells)


def _parse_attachment(tokens: list[str], lineno: int) -> dict[str, int]:
    def fail(reason: str) -> LDrawError:
        return LDrawError(f"line {lineno}: {reason}")

    try:
        x_ldu, y_ldu, z_ldu = (float(t) for t in tokens[2:5])
    except ValueError as e:
        raise fail(f"malformed number: {e}") from e
    return {
        "x": _grid(x_ldu, LDU_PER_STUD, f"{tokens[14]} x position", fail),
        "y": _grid(-y_ldu, LDU_PER_PLATE, f"{tokens[14]} height", fail),
        "z": _grid(z_ldu, LDU_PER_STUD, f"{tokens[14]} z position", fail),
        "rot": _rotation(tokens, fail),
    }


def _parse_part_line(tokens: list[str], lineno: int) -> tuple[Part, dict[str, int]]:
    """Return the part and its grid position, rotation and color for one type-1 line."""

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
    except ValueError as e:
        raise fail(f"malformed number: {e}") from e
    rot = _rotation(tokens, fail)
    size_x, size_z = (part.depth, part.width) if rot in (90, 270) else (part.width, part.depth)
    ox, oy, oz = _rotate(_matrix(rot), part.origin)
    x_ldu, y_ldu, z_ldu = x_ldu - ox, y_ldu - oy, z_ldu - oz
    x = _grid(x_ldu - size_x * _HALF_STUD, LDU_PER_STUD, f"{part.filename} x position", fail)
    z = _grid(z_ldu - size_z * _HALF_STUD, LDU_PER_STUD, f"{part.filename} z position", fail)
    y = _grid(-y_ldu, LDU_PER_PLATE, f"{part.filename} height", fail) - part.height
    return part, {"x": x, "y": y, "z": z, "rot": rot, "color": color}


@dataclass
class _Item:
    lineno: int
    tokens: list[str]
    components: list[list[str]] = field(default_factory=list)  # compound part lines


class _Section:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.title: str | None = None
        self.steps: list[list[_Item]] = [[]]


def _sections(text: str) -> list[_Section]:
    sections: list[_Section] = []
    compound = 0  # component lines still to collect for the last part
    announced = 0  # a `0 !LEGO COMPOUND n` comment is waiting for its base part
    for lineno, raw in enumerate(text.splitlines(), start=1):
        tokens = raw.split()
        if not tokens:
            continue
        if tokens[:2] == ["0", "FILE"]:
            sections.append(_Section(" ".join(tokens[2:]).lower()))
            continue
        if not sections:
            sections.append(_Section(""))  # plain .ldr without FILE headers
        section = sections[-1]
        if tokens[:3] == ["0", "!LEGO", "COMPOUND"]:
            announced = int(tokens[3])
        elif tokens[0] == "0":
            if tokens[1:2] == ["STEP"]:
                section.steps.append([])
            elif section.title is None and tokens[1:2] not in (["Name:"], ["Author:"]):
                section.title = " ".join(tokens[1:])
        elif tokens[0] == "1":
            if compound:
                section.steps[-1][-1].components.append(tokens)
                compound -= 1
            else:
                section.steps[-1].append(_Item(lineno, tokens))
                compound, announced = announced, 0
        elif tokens[0] in ("2", "3", "4", "5"):
            raise LDrawError(f"line {lineno}: raw geometry is not supported")
    return sections


def _fill(model: Model, section: _Section, subs: dict[str, Model]) -> None:
    for step in (s for s in section.steps if s):
        with model.step():
            for item in step:
                if len(item.tokens) != 15:
                    raise LDrawError(f"line {item.lineno}: expected 15 fields in a part line")
                try:
                    sub = subs.get(item.tokens[14].lower())
                    if sub is not None:
                        model.attach(sub, **_parse_attachment(item.tokens, item.lineno))
                        continue
                    part, at = _parse_part_line(item.tokens, item.lineno)
                    color2 = next(
                        (
                            int(line[1])
                            for c, line in zip(part.components, item.components, strict=False)
                            if c.color == "second"
                        ),
                        None,
                    )
                    model._place(
                        part.kind,
                        part.size,
                        at["x"],
                        at["y"],
                        at["z"],
                        at["color"],
                        rot=at["rot"],
                        color2=color2,
                    )
                except DesignError as e:
                    raise LDrawError(f"line {item.lineno}: {e}") from e


def loads(text: str, name: str = "model") -> Model:
    sections = _sections(text)
    model = Model(sections[0].title or name if sections else name)
    subs: dict[str, Model] = {}
    for section in sections[1:]:
        sub = model.subassembly(section.title or section.filename.removesuffix(".ldr"))
        _fill(sub, section, {})
        subs[section.filename] = sub
    if sections:
        _fill(model, sections[0], subs)
    return model


def load(path: Path) -> Model:
    return loads(path.read_text(), name=path.stem)
