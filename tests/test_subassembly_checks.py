import pytest

from lego.check import run_all
from lego.check.steps import insertable, step_size, steps_connected
from lego.dsl import Model

pytestmark = pytest.mark.ldraw


def _robot() -> Model:
    """Two identical legs built separately, then both hang under one hip plate."""
    m = Model("robot")
    leg = m.subassembly("leg")
    with leg.step():
        leg.plate("2x2", x=0, z=0, y=0, color="black")  # foot
        leg.brick("2x2", x=0, z=0, y=1, color="light_bluish_grey")
    with leg.step():
        leg.brick("2x2", x=0, z=0, y=4, color="light_bluish_grey")
    with m.step():
        m.plate("2x4", x=0, z=0, y=7, color="red")  # hips: x 0..3
    with m.step():
        m.attach(leg, x=0, y=0, z=0)  # under hip x 0..1
        m.attach(leg, x=2, y=0, z=0)  # under hip x 2..3
    return m


def test_two_legs_built_separately_pass_all_checks():
    assert all(r.ok for r in run_all(_robot()))


def test_disconnected_step_inside_sub_assembly_is_reported_with_sub_context():
    m = Model("m")
    arm = m.subassembly("arm")
    with arm.step():
        arm.brick("1x2", x=0, z=0, y=0, color="red")
        arm.brick("1x1", x=4, z=0, y=3, color="red")  # floats inside the arm
    with arm.step():
        arm.brick("1x4", x=1, z=0, y=3, color="red")
    with m.step():
        m.brick("2x4", x=0, z=0, y=0, color="white")
    with m.step():
        m.attach(arm, x=0, y=3, z=0)
    report = steps_connected(m)
    sub_issues = [i for i in report.issues if i.message.startswith("inside sub-assembly 'arm'")]
    assert sub_issues, report.issues
    part = sub_issues[-1].parts[0]
    assert (part.sub, part.sub_step, part.call.startswith("arm.brick('1x1'")) == ("arm", 1, True)


def test_attached_sub_assembly_counts_as_one_item_in_step_size():
    m = Model("m")
    wheel = m.subassembly("wheel")
    with wheel.step():
        for x in range(5):
            wheel.plate("1x1", x=x, z=0, y=0, color="black")
        wheel.plate("1x4", x=0, z=0, y=1, color="black")
    with wheel.step():
        wheel.plate("1x2", x=3, z=0, y=1, color="black")
    with m.step():
        for x in range(0, 30, 6):
            m.attach(wheel, x=x, y=0, z=0)  # 5 attachments of 7 parts each
        m.plate("1x1", x=40, z=0, y=0, color="red")
    assert step_size(m).ok  # 6 items, though 36 parts


def test_sub_assembly_wedged_between_earlier_parts_fails_b5():
    m = Model("m")
    block = m.subassembly("block")
    with block.step():
        block.brick("1x2", x=0, z=0, y=0, color="red")
    with m.step():
        m.brick("1x4", x=0, z=0, y=0, color="white")
        m.brick("1x1", x=0, z=0, y=3, color="white")
        m.brick("1x1", x=3, z=0, y=3, color="white")
    with m.step():
        m.plate("1x4", x=0, z=0, y=6, color="white")  # roof over the gap at x 1..2
    with m.step():
        m.attach(block, x=1, y=3, z=0)  # exactly fills the gap: touched above and below
    [issue] = insertable(m).issues
    assert issue.message.startswith("sub-assembly 'block' (attached in step 3) is wedged in")
    assert issue.parts[0].sub == "block"
