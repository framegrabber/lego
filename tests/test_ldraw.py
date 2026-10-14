from pathlib import Path

import pytest

from lego import ldraw
from lego.dsl import Model
from lego.ldraw import LDrawError

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


def _sample() -> Model:
    m = Model("sample")
    with m.step():
        m.plate("2x4", x=0, z=0, y=0, color="black")
        m.plate("1x2", x=-3, z=7, y=-2, color="white", rot=90)
    with m.step():
        for rot in (0, 90, 180, 270):
            m.brick("2x4", x=rot // 10, z=1, y=1, color="red", rot=rot)
        m.brick("1x1", x=5, z=5, y=4, color=71)
    return m


def test_round_trip_preserves_parts_positions_rotations_colors_steps():
    model = _sample()
    parsed = ldraw.loads(ldraw.dumps(model))
    assert parsed.num_steps == model.num_steps
    assert parsed.placements == model.placements


def test_writes_ldraw_units_and_rotation_matrix():
    m = Model("t")
    with m.step():
        # 2x4 brick turned 90°: footprint x 1..3, z 2..6, levels 1..3 → centre (40, 80), top y=4.
        m.brick("2x4", x=1, z=2, y=1, color="blue", rot=90)
    part_lines = [line for line in ldraw.dumps(m).splitlines() if line.startswith("1 ")]
    assert part_lines == ["1 1 40 -32 80 0 0 1 0 1 0 -1 0 0 3001.dat"]


def test_hand_written_model_parses_onto_grid():
    model = ldraw.load(MODELS / "hello.ldr")
    assert model.num_steps == 2
    assert len(model.placements) == 8
    white = model.placements[-1]
    assert (white.part.size, white.x, white.y, white.z) == ("1x1", 0, 3, 1)


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        ("1 15 0 -48 20 1 0 0 0 1 0 0 0 1 3005.dat", "x position is not on the brick grid"),
        ("1 4 0 -30 0 1 0 0 0 1 0 0 0 1 3001.dat", "height is not on the brick grid"),
        ("1 4 0 0 0 0.7071 0 0.7071 0 1 0 -0.7071 0 0.7071 3001.dat", "rotation must be"),
        ("1 4 0 0 0 1 0 0 0 1 0 0 0 1 3794b.dat", "not in the supported vocabulary"),
        ("1 9999 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat", "unknown LDraw color code"),
    ],
)
def test_rejects_lines_outside_the_supported_model(line, reason):
    with pytest.raises(LDrawError, match=reason) as exc:
        ldraw.loads(line + "\n")
    assert str(exc.value).startswith("line 1:")
