import pytest

from lego import ldraw
from lego.check import run_all
from lego.check.basic import collisions
from lego.check.connectivity import connections
from lego.check.stability import stable
from lego.dsl import DesignError, Model
from lego.instructions import instructions

pytestmark = pytest.mark.ldraw


def test_nothing_attaches_on_a_tile():
    m = Model("t")
    with m.step():
        m.plate("2x2", x=0, z=0, y=0, color="red")
        m.tile("2x2", x=0, z=0, y=1, color="white")
        m.plate("1x1", x=0, z=0, y=2, color="blue")  # sits on the smooth tile
    assert connections(m.placements) == {(0, 1): 4}


def test_arch_opening_is_free_and_only_its_ends_sit_on_studs():
    m = Model("t")
    with m.step():
        m.plate("1x6", x=0, z=0, y=0, color="white")
        m.arch("1x6", x=0, z=0, y=1, color="light_bluish_grey")  # ends at x=0 and x=5
        m.plate("1x2", x=2, z=0, y=1, color="red")  # in the opening: it is one plate high
    assert collisions(m).ok
    joined = connections(m.placements)
    assert joined[(0, 1)] == 2  # the arch's two ends
    assert (0, 2) in joined


def test_part_in_the_arch_crown_collides():
    m = Model("t")
    with m.step():
        m.arch("1x4", x=0, z=0, y=0, color="light_bluish_grey")  # crown: levels 1-2, x=1..2
        m.plate("1x1", x=1, z=0, y=2, color="red")
    assert not collisions(m).ok


def test_wheels_stick_out_beside_the_holder_and_the_car_stands_on_its_tyres():
    m = Model("t")
    with m.step():
        m.plate("2x4", x=0, z=0, y=2, color="light_bluish_grey")
    with m.step():
        m.wheels(x=0, z=0, y=1, color="black", rot=90)  # axle along z: wheels at z=-1 and z=2
        m.wheels(x=2, z=0, y=1, color="black", rot=90)
    wheel = m.placements[1]
    assert wheel.bottom == -1  # tyres reach 2 plates below the holder
    assert {(0, -1, -1), (1, 3, 2)} <= wheel.occupied()
    report = run_all(m)
    assert all(r.ok for r in report), report
    assert stable(m).issues == []  # stands on four tyres, not tipping

    blocked = Model("t")
    with blocked.step():
        blocked.wheels(x=0, z=0, y=2, color="black", rot=90)
        blocked.brick("1x1", x=0, z=2, y=2, color="red")  # where a wheel is
    assert not collisions(blocked).ok


def test_compound_parts_and_their_colours_survive_an_ldraw_round_trip():
    m = Model("t")
    with m.step():
        m.plate("2x6", x=0, z=0, y=0, color="white")
        m.window("1x2x2", x=0, z=0, y=1, color="white", glass_color="trans_light_blue")
        m.door("1x4x6", x=2, z=0, y=1, color="white", door_color="black", rot=180)
        m.wheels(x=0, z=3, y=1, color="black", rot=90, rim_color="black")
    text = ldraw.dumps(m)
    assert text.count("0 !LEGO COMPOUND") == 3
    assert ldraw.loads(text).placements == m.placements


def test_parts_list_names_components_separately():
    m = Model("t")
    with m.step():
        m.wheels(x=0, z=0, y=1, color="black", rim_color="white")
    parts_list = instructions(m)["main"][0]["parts"]
    assert {"count": 2, "part": "wheel rim 6.4x8", "color": "white"} in parts_list
    assert {"count": 2, "part": "tyre 6/50x8", "color": "black"} in parts_list
    assert {"count": 1, "part": "2x2 plate with wheel pins", "color": "black"} in parts_list


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda m: m.slope("3x2", x=0, z=0, y=0, color="red", angle=50), "angle must be one of"),
        (lambda m: m.slope("2x2", x=0, z=0, y=0, color="red", angle=33), "unknown slope33 size"),
        (
            lambda m: m.corner_slope("outside", x=0, z=0, y=0, color="red", facing="up"),
            "facing must be one of",
        ),
        (lambda m: m.tile("3x3", x=0, z=0, y=0, color="red"), "unknown tile size"),
    ],
)
def test_invalid_new_part_calls(call, message):
    m = Model("t")
    with pytest.raises(DesignError, match=message), m.step():
        call(m)
