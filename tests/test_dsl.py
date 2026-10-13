import pytest

from lego.dsl import DesignError, Model

# Color names resolve against LDConfig.ldr from the parts library.
pytestmark = pytest.mark.ldraw


def test_spec_example_places_parts_in_steps():
    m = Model("racing car")
    with m.step():
        m.plate("2x4", x=0, z=0, y=0, color="black")
        m.plate("2x4", x=0, z=2, y=0, color="black")
    with m.step():
        m.brick("2x4", x=0, z=1, y=1, color="red")

    assert m.num_steps == 2
    assert [(p.part.ldraw_id, p.step, p.color) for p in m.placements] == [
        ("3020", 0, 0),
        ("3020", 0, 0),
        ("3001", 1, 4),
    ]


@pytest.mark.parametrize(
    ("rot", "size_x", "size_z"), [(0, 4, 2), (90, 2, 4), (180, 4, 2), (270, 2, 4)]
)
def test_rotation_swaps_footprint_around_fixed_corner(rot, size_x, size_z):
    m = Model("t")
    with m.step():
        m.brick("2x4", x=3, z=5, y=0, color="red", rot=rot)
    p = m.placements[0]
    assert p.cells() == {(3 + dx, 5 + dz) for dx in range(size_x) for dz in range(size_z)}


def test_brick_is_three_plates_tall():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=2, color="red")
        m.plate("1x1", x=1, z=0, y=2, color="red")
    brick, plate = m.placements
    assert list(brick.levels()) == [2, 3, 4]
    assert list(plate.levels()) == [2]


def test_color_accepts_ldraw_code_and_is_case_insensitive():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=0, color=71)
        m.brick("1x1", x=1, z=0, y=0, color="Light_Bluish_Grey")
    assert [p.color for p in m.placements] == [71, 71]


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (lambda m: m.brick("2x5", x=0, z=0, y=0, color="red"), "unknown brick size"),
        (lambda m: m.plate("2x4", x=0, z=0, y=0, color="sparkly"), "unknown color"),
        (lambda m: m.brick("2x4", x=0, z=0, y=0, color=9999), "unknown LDraw color code"),
        (lambda m: m.brick("2x4", x=0.5, z=0, y=0, color="red"), "x must be an integer"),
        (lambda m: m.brick("2x4", x=0, z=0, y=True, color="red"), "y must be an integer"),
        (lambda m: m.brick("2x4", x=0, z=0, y=0, color="red", rot=45), "rot must be one of"),
    ],
)
def test_invalid_calls_name_the_call_and_reason(call, reason):
    m = Model("t")
    with pytest.raises(DesignError) as exc, m.step():
        call(m)
    message = str(exc.value)
    assert message.startswith(("brick(", "plate("))
    assert reason in message


def test_part_outside_step_is_rejected():
    m = Model("t")
    with pytest.raises(DesignError, match="inside `with m.step"):
        m.brick("2x4", x=0, z=0, y=0, color="red")


def test_empty_and_nested_steps_are_rejected():
    m = Model("t")
    with pytest.raises(DesignError, match="step 1 is empty"), m.step():
        pass
    with pytest.raises(DesignError, match="nested"), m.step(), m.step():
        pass
