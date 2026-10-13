from pathlib import Path

import pytest

from lego.build import load_program
from lego.check.steps import insertable
from lego.dsl import Model

pytestmark = pytest.mark.ldraw

MODELS = Path(__file__).resolve().parents[1] / "models"


def test_brick_wedged_under_an_existing_overhang_fails():
    [issue] = insertable(load_program(MODELS / "broken" / "wedged.py")).issues
    # The wedged part, then what is above it, then what is below it.
    assert [p.index for p in issue.parts] == [3, 2, 0]
    assert issue.at == (2, 6, 0)


def test_same_parts_in_buildable_order_pass():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="red")
        m.brick("1x2", x=0, z=0, y=3, color="blue")
        m.brick("1x2", x=2, z=0, y=3, color="yellow")  # before the plate covers it
    with m.step():
        m.plate("2x4", x=0, z=0, y=6, color="white")
    assert insertable(m).ok


def test_parts_of_one_step_never_block_each_other():
    # The upper plate is written first; a kid simply places the lower one first.
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="red")
    with m.step():
        m.plate("2x4", x=0, z=0, y=4, color="white")
        m.plate("2x4", x=0, z=0, y=3, color="blue")
    assert insertable(m).ok


def test_part_pressed_on_from_below_with_free_space_passes():
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=3, color="red")
    with m.step():
        m.plate("1x2", x=0, z=0, y=2, color="blue")  # hangs underneath, nothing below it
    assert insertable(m).ok


def test_bottom_plate_added_under_an_existing_part_passes():
    # Pressing up from below works for the bottom layer too: lift the model, press it on.
    m = Model("t")
    with m.step():
        m.brick("2x4", x=0, z=0, y=1, color="red")
    with m.step():
        m.plate("2x4", x=0, z=0, y=0, color="black")
    assert insertable(m).ok


def test_blocker_far_above_still_blocks_pressing_down():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=0, color="red")
        m.brick("1x2", x=1, z=0, y=0, color="red")
        m.brick("1x4", x=0, z=0, y=3, color="red")
        m.brick("1x1", x=4, z=0, y=0, color="red")  # free column: fine
    with m.step():
        m.plate("1x1", x=0, z=0, y=9, color="blue")  # far above x=0, nothing between yet
    with m.step():
        m.plate("1x1", x=0, z=0, y=6, color="green")  # x=0: blue above, 1x4 below
    [issue] = insertable(m).issues
    assert [p.index for p in issue.parts] == [5, 4, 2]
