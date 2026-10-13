from pathlib import Path

import pytest

from lego import ldraw
from lego.build import BuildError, load_program
from lego.dsl import DesignError, Model

pytestmark = pytest.mark.ldraw


def _with_leg(rot: int = 0) -> Model:
    m = Model("robot")
    leg = m.subassembly("leg")
    with leg.step():
        leg.plate("2x4", x=0, z=0, y=0, color="black")  # asymmetric: 4 along x
        leg.brick("1x2", x=3, z=1, y=1, color="red", rot=90)
    with leg.step():
        leg.brick("1x1", x=0, z=0, y=1, color="blue")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="white")
    with m.step():
        m.attach(leg, x=5, y=3, z=-2, rot=rot)
        m.brick("1x1", x=0, z=0, y=3, color="white")
    return m


def _ldu(line: str) -> tuple[list[float], list[int]]:
    tokens = line.split()
    return [float(t) for t in tokens[2:5]], [int(t) for t in tokens[5:14]]


@pytest.mark.parametrize("rot", [0, 90, 180, 270])
def test_flattened_copy_matches_how_ldraw_draws_the_submodel(rot):
    """World part = LDraw reference transform applied to the submodel's part line."""
    m = _with_leg(rot)
    a = m.attachments[0]
    r = ldraw._matrix(rot)
    origin = (a.x * 20, -a.y * 8, a.z * 20)
    flat = [p for p in m.placements if p.sub == "leg"]
    for local, world in zip(a.sub.placements, flat, strict=True):
        (lx, ly, lz), lm = _ldu(ldraw._line(local))
        (wx, wy, wz), wm = _ldu(ldraw._line(world))
        expected_pos = (
            r[0] * lx + r[1] * ly + r[2] * lz + origin[0],
            r[3] * lx + r[4] * ly + r[5] * lz + origin[1],
            r[6] * lx + r[7] * ly + r[8] * lz + origin[2],
        )
        expected_matrix = [
            sum(r[3 * i + k] * lm[3 * k + j] for k in range(3)) for i in range(3) for j in range(3)
        ]
        assert (wx, wy, wz) == expected_pos
        assert wm == expected_matrix


def test_attached_parts_belong_to_the_attach_step_and_keep_their_sub_step():
    m = _with_leg()
    flat = [(p.sub, p.step, p.sub_step) for p in m.placements]
    assert flat == [
        (None, 0, None),
        ("leg", 1, 0),
        ("leg", 1, 0),
        ("leg", 1, 1),
        (None, 1, None),
    ]


def test_mpd_round_trip_keeps_submodel_structure():
    m = _with_leg(90)
    text = ldraw.dumps(m)
    assert "0 FILE robot__leg.ldr" in text
    parsed = ldraw.loads(text)
    assert parsed.placements == m.placements
    assert [(a.label, a.x, a.y, a.z, a.rot, a.step) for a in parsed.attachments] == [
        ("leg", 5, 3, -2, 90, 1)
    ]
    assert parsed.subassemblies["leg"].num_steps == 2


def test_attaching_twice_labels_copies():
    m = Model("car")
    wheel = m.subassembly("wheel")
    with wheel.step():
        wheel.brick("2x2", x=0, z=0, y=0, color="black")
    with m.step():
        m.attach(wheel, x=0, y=0, z=0)
        m.attach(wheel, x=6, y=0, z=0)
    assert [p.sub for p in m.placements] == ["wheel", "wheel#2"]
    assert ldraw.dumps(m).count("0 FILE car__wheel.ldr") == 1


def test_sub_assembly_rules():
    m = Model("m")
    leg = m.subassembly("leg")
    with pytest.raises(DesignError, match="cannot be nested"):
        leg.subassembly("foot")
    with pytest.raises(DesignError, match="unique"):
        m.subassembly("leg")
    with pytest.raises(DesignError, match="finish building"), m.step():
        m.attach(leg, x=0, y=0, z=0)
    with leg.step():
        leg.brick("1x1", x=0, z=0, y=0, color="red")
    with m.step():
        m.attach(leg, x=0, y=0, z=0)
    with pytest.raises(DesignError, match=r"^leg\.brick.*already attached"), leg.step():
        leg.brick("1x1", x=1, z=0, y=0, color="red")
    other = Model("other").subassembly("x")
    with pytest.raises(DesignError, match="not a sub-assembly of this model"), m.step():
        m.attach(other, x=0, y=0, z=0)


def test_program_with_subassembly_loads_its_main_model(tmp_path: Path):
    program = tmp_path / "p.py"
    program.write_text(
        "from lego.dsl import Model\n"
        "m = Model('main')\n"
        "leg = m.subassembly('leg')\n"
        "with leg.step():\n"
        "    leg.brick('1x1', x=0, z=0, y=0, color='red')\n"
        "with m.step():\n"
        "    m.attach(leg, x=0, y=0, z=0)\n"
    )
    assert load_program(program).name == "main"
    program.write_text(program.read_text() + "n = Model('second')\n")
    with pytest.raises(BuildError, match="found 2"):
        load_program(program)
