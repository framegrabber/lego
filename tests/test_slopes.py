import pytest

from lego import ldraw
from lego.check.connectivity import connections
from lego.dsl import DesignError, Model

pytestmark = pytest.mark.ldraw


@pytest.mark.parametrize(
    ("facing", "studs"),
    [
        ("front", {(0, 1), (1, 1)}),  # face points −z: studs on the back row
        ("back", {(0, 0), (1, 0)}),
        ("left", {(1, 0), (1, 1)}),  # face points −x: studs on the +x column
        ("right", {(0, 0), (0, 1)}),
    ],
)
def test_slope_studs_are_on_the_row_opposite_the_face(facing, studs):
    m = Model("t")
    with m.step():
        m.slope("2x2", x=0, z=0, y=0, color="red", facing=facing)
    p = m.placements[0]
    assert p.stud_cells() == studs
    assert p.antistud_cells() == p.cells()  # full underside


def test_nothing_connects_on_the_sloped_face_but_the_back_row_does():
    m = Model("t")
    with m.step():
        m.slope("2x1", x=0, z=0, y=0, color="red", facing="front")  # cells (0,0) face, (0,1) studs
        m.plate("1x1", x=0, z=0, y=3, color="blue")  # above the face
        m.plate("1x1", x=0, z=1, y=3, color="blue")  # on the stud
    assert connections(m.placements) == {(0, 2): 1}


def test_inverted_slope_sits_on_studs_only_with_its_back_row():
    m = Model("t")
    with m.step():
        m.brick("1x1", x=0, z=0, y=0, color="white")  # under the inverted slope's front
        m.brick("1x1", x=1, z=1, y=0, color="white")  # under the back row of the second one
        m.inverted_slope("2x1", x=0, z=0, y=3, color="red", facing="front")
        m.inverted_slope("2x1", x=1, z=0, y=3, color="red", facing="front")
    assert connections(m.placements) == {(1, 3): 1}


def test_slope_ldraw_origin_is_the_stud_row_centre_and_round_trips():
    m = Model("t")
    with m.step():
        m.slope("2x2", x=0, z=0, y=0, color="red", facing="front")
        for i, facing in enumerate(("front", "back", "left", "right")):
            m.slope("2x4", x=10 * i, z=5, y=0, color="blue", facing=facing)
            m.inverted_slope("2x2", x=10 * i, z=9, y=0, color="blue", facing=facing)
    first = ldraw.dumps(m).splitlines()[4]
    # Footprint x 0..1, z 0..1 → centre (20, 20); the origin sits half a stud back at z = 30.
    assert first == "1 4 20 -24 30 1 0 0 0 1 0 0 0 1 3039.dat"
    assert ldraw.loads(ldraw.dumps(m)).placements == m.placements


def test_unknown_facing_is_rejected():
    m = Model("t")
    with pytest.raises(DesignError, match="facing must be one of"), m.step():
        m.slope("2x2", x=0, z=0, y=0, color="red", facing="up")
