from pathlib import Path

import pytest

from lego.build import load_program
from lego.check import run_all, to_json
from lego.check.basic import collisions
from lego.dsl import Model

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


@pytest.mark.parametrize("program", ["wall.py"])
def test_good_models_pass_all_checks(program):
    assert all(r.ok for r in run_all(load_program(MODELS / program)))


def test_overlap_fixture_fails_b2_naming_both_parts_and_first_cell():
    report = collisions(load_program(MODELS / "broken" / "overlap.py"))
    assert not report.ok
    [issue] = report.issues
    assert [p.index for p in issue.parts] == [0, 1]
    assert issue.at == (2, 0, 0)


def test_touching_and_stacked_parts_do_not_collide():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="red")
        m.brick("2x4", x=4, z=0, y=0, color="red")  # side by side
        m.plate("2x4", x=0, z=0, y=3, color="red")  # directly on top
    assert collisions(m).ok


def test_plate_inside_brick_volume_collides():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=0, color="red")  # levels 0..2
        m.plate("1x1", x=0, z=0, y=2, color="red")
    [issue] = collisions(m).issues
    assert issue.at == (0, 2, 0)


def test_json_report_shape():
    data = to_json(run_all(load_program(MODELS / "broken" / "overlap.py")))
    assert data["ok"] is False
    b2 = next(c for c in data["checks"] if c["check"] == "B2")
    assert b2["issues"][0]["parts"][1] == {
        "index": 1,
        "step": 1,
        "call": "brick('2x4', x=2, y=0, z=0, color='blue', rot=0)",
        "sub": None,
        "sub_step": None,
    }
