import re
from pathlib import Path

import pytest

from lego.build import load_program
from lego.check.steps import step_size, steps_connected
from lego.dsl import Model

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


def _loose_pieces(report) -> list[tuple[int, list[int], str]]:
    """(step it first appears loose, its parts, how it ends) per loose-piece issue."""
    out = []
    for issue in report.issues:
        found = re.match(r"after step (\d+), .*?; (.*?)\. ", issue.message)
        if found:
            out.append((int(found[1]), [p.index for p in issue.parts], found[2]))
    return out


def test_part_joined_only_by_a_later_step_fails_b4_at_its_step():
    report = steps_connected(load_program(MODELS / "broken" / "future_support.py"))
    assert _loose_pieces(report) == [(2, [1], "first joined to the main piece in step 3 by #2")]


def test_loose_bottom_plates_in_step_1_pass_when_step_2_joins_them():
    m = Model("t")
    with m.step():
        m.plate("2x4", x=0, z=0, y=0, color="black")
        m.plate("2x4", x=4, z=0, y=0, color="black")
    with m.step():
        m.plate("2x4", x=2, z=0, y=1, color="red")
    assert steps_connected(m).ok


def test_loose_parts_above_the_bottom_layer_in_step_1_fail_naming_them():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="black")
        m.brick("1x1", x=6, z=0, y=6, color="red")  # in the air
    with m.step():
        m.brick("1x4", x=3, z=0, y=3, color="red")  # on the 2x4, under the 1x1
    report = steps_connected(m)
    step_rule = report.issues[0]
    assert step_rule.message.startswith("step 1 leaves 2 separate pieces")
    assert [p.index for p in step_rule.parts] == [1]  # only the part above the bottom layer
    assert _loose_pieces(report) == [(1, [1], "first joined to the main piece in step 2 by #2")]


def test_each_loose_piece_is_reported_once_with_its_parts_grouped():
    # Two separate islands next to a main row; each stays loose for several steps.
    m = Model("t")
    with m.step():
        for x in (0, 4, 8, 12):
            m.plate("2x4", x=x, z=0, y=0, color="black")
    with m.step():
        m.plate("2x4", x=2, z=0, y=1, color="red")  # joins plates 0 and 1
        m.plate("1x4", x=12, z=0, y=1, color="red")  # sits on plate 3 only
    with m.step():
        m.plate("2x4", x=0, z=0, y=2, color="blue")  # main grows; islands unchanged
    with m.step():
        m.plate("2x4", x=6, z=0, y=1, color="red")  # joins plate 2
    with m.step():
        m.plate("2x4", x=10, z=0, y=1, color="red")  # joins plate 3 + its 1x4
    assert _loose_pieces(steps_connected(m)) == [
        (2, [2], "first joined to the main piece in step 4 by #7"),
        (2, [3, 5], "first joined to the main piece in step 5 by #8"),
    ]


def test_piece_that_never_joins_says_so():
    m = Model("t")
    with m.step():
        m.plate("2x4", x=0, z=0, y=0, color="black")
        m.plate("2x4", x=6, z=0, y=0, color="black")
    with m.step():
        m.plate("2x4", x=0, z=0, y=1, color="red")
    assert _loose_pieces(steps_connected(m)) == [(2, [1], "never joined to the main piece")]


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
    assert report.issues[0].message.startswith("step 1 adds 7 parts; at most 6 per step")
    assert step_size(m, limit=7).ok
