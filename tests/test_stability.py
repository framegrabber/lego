from pathlib import Path

import pytest

from lego.build import load_program
from lego.check.stability import FAIL, WARN, stable
from lego.dsl import Model

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


def _cantilevered_tower(supported_in_last_step: bool = False) -> Model:
    """A 1x2 arm held by one stud carries a tall 2x2 tower beyond the base."""
    m = Model("t")
    with m.step():
        m.brick("1x4", x=0, z=0, y=0, color="white")  # x 0..3, on the table
    with m.step():
        m.brick("1x2", x=3, z=0, y=3, color="red")  # x 3..4: one stud on the base
    for level in range(6):
        with m.step():
            m.brick("2x2", x=4, z=0, y=6 + 3 * level, color="blue")
    if supported_in_last_step:
        with m.step():  # pillar from the table up to the arm's free end... and the tower
            m.brick("1x1", x=4, z=1, y=0, color="white")
            m.brick("1x1", x=5, z=1, y=0, color="white")
            m.brick("2x2", x=4, z=0, y=3, color="white")
    return m


def test_one_stud_cantilever_carrying_a_tower_is_unstable():
    report = stable(_cantilevered_tower())
    assert not report.ok
    assert report.score is not None and report.score < FAIL
    arm = report.issues[0]
    assert arm.level == "error"
    assert arm.parts[0].index == 1  # the arm is the weak joint
    assert "held by 1 stud(s)" in arm.message


def test_weak_point_that_only_exists_while_building_is_a_warning():
    report = stable(_cantilevered_tower(supported_in_last_step=True))
    assert report.ok
    assert report.score is not None and report.score >= WARN
    assert report.issues and all(i.level == "warning" for i in report.issues)
    assert "(while building)" in report.issues[0].message


def test_solid_wall_scores_high():
    report = stable(load_program(MODELS / "wall.py"))
    assert report.ok and not report.issues
    assert report.score is not None and report.score >= WARN


def test_free_standing_model_with_weight_outside_its_footprint_tips_over():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=0, color="white")  # the only part on the table
        m.plate("1x4", x=0, z=0, y=3, color="white")
    with m.step():
        for level in range(4):
            m.brick("1x1", x=3, z=0, y=4 + 3 * level, color="red")
    report = stable(m)
    tip = [i for i in report.issues if "tips over" in i.message]
    assert tip and tip[0].level == "error"
    assert report.score == 0.0


def test_body_on_two_legs_does_not_hang_off_either_leg():
    # Regression: both feet touch the table, so the body depends on neither leg alone.
    report = stable(load_program(MODELS / "examples" / "two_legs.py"))
    assert report.ok and not report.issues
