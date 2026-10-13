from pathlib import Path

import pytest

from lego.build import load_program
from lego.check.steps import step_size, steps_connected
from lego.dsl import Model

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


def _issues(report) -> list[tuple[str, list[int]]]:
    return [
        (issue.message.split(" the model")[0], [p.index for p in issue.parts])
        for issue in report.issues
    ]


def test_part_joined_only_by_a_later_step_fails_b4_at_its_step():
    report = steps_connected(load_program(MODELS / "broken" / "future_support.py"))
    assert _issues(report) == [("after step 2", [1])]


def test_loose_bottom_plates_in_step_1_pass_when_step_2_joins_them():
    m = Model("t")
    with m.step():
        m.plate("2x4", x=0, z=0, y=0, color="black")
        m.plate("2x4", x=4, z=0, y=0, color="black")
    with m.step():
        m.plate("2x4", x=2, z=0, y=1, color="red")
    assert steps_connected(m).ok


def test_loose_parts_above_the_bottom_layer_in_step_1_fail():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="black")
        m.brick("1x1", x=6, z=0, y=6, color="red")  # in the air
    with m.step():
        m.brick("1x4", x=3, z=0, y=3, color="red")  # on the 2x4, under the 1x1
    report = steps_connected(m)
    assert [msg for msg, _ in _issues(report)] == ["after step 1"]
    assert "bottom layer" in report.issues[0].message


def test_bottom_plates_still_apart_after_step_2_fail():
    # Like the castle tower floor: step 2 bridges only some of the step-1 plates.
    m = Model("t")
    with m.step():
        for x in (0, 4, 8):
            m.plate("2x4", x=x, z=0, y=0, color="black")
    with m.step():
        m.plate("2x4", x=2, z=0, y=1, color="red")  # joins plates 0 and 1, not 2
    with m.step():
        m.plate("2x4", x=6, z=0, y=1, color="red")
    assert _issues(steps_connected(m)) == [("after step 2", [2])]


def test_step_with_seven_parts_fails_b6():
    m = Model("t")
    with m.step():
        for x in range(7):
            m.plate("1x1", x=x, z=0, y=0, color="red")
    with m.step():
        m.plate("1x4", x=0, z=0, y=1, color="red")
        m.plate("1x4", x=3, z=0, y=1, color="red")
    report = step_size(m)
    assert len(report.issues) == 1
    assert report.issues[0].message == "step 1 adds 7 parts; at most 6 per step"
    assert step_size(m, limit=7).ok
