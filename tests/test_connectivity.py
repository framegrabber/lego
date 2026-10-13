from pathlib import Path

import pytest

from lego.build import load_program
from lego.check.connectivity import connected, connections
from lego.dsl import Model

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


def _failing_indices(model: Model) -> list[list[int]]:
    return [[p.index for p in issue.parts] for issue in connected(model).issues]


def test_floating_brick_is_reported():
    assert _failing_indices(load_program(MODELS / "broken" / "floating.py")) == [[2]]


def test_spec_draft_with_gap_has_three_separate_parts():
    # All three parts are single-part components; part 0's is treated as main.
    assert _failing_indices(load_program(MODELS / "broken" / "gap.py")) == [[1], [2]]


def test_side_by_side_parts_are_not_connected():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="red")
        m.brick("2x4", x=4, z=0, y=0, color="red")
    assert _failing_indices(m) == [[1]]


def test_bridge_joins_two_towers():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=0, color="red")
        m.brick("1x1", x=3, z=0, y=0, color="red")
        m.brick("1x4", x=0, z=0, y=3, color="blue")
    assert connected(m).ok
    assert connections(m.placements) == {(0, 2): 1, (1, 2): 1}


def test_part_hanging_under_another_is_connected():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=3, color="red")
        m.plate("1x2", x=0, z=0, y=2, color="blue")  # its studs press into the brick above
    assert connections(m.placements) == {(1, 0): 2}


def test_stud_count_follows_rotated_footprint_overlap():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="red")  # x 0..3, z 0..1
        m.brick("2x4", x=3, z=0, y=3, color="red", rot=90)  # x 3..4, z 0..3
    assert connections(m.placements) == {(0, 1): 2}
