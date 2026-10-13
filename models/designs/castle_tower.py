"""Eval #7: a castle tower with battlements.

6x6 hollow stone tower on a two-layer floor, five brick courses with alternating corners,
a door and arrow slits, an 8x8 plate ring overhanging by one stud, and 1x2 merlons on top.
"""

from lego.dsl import Model

FLOOR = "dark_bluish_grey"
STONE = "light_bluish_grey"
DOOR = "reddish_brown"
SLIT = "black"

m = Model("castle tower")

# Floor, levels 0-1. Each layer is four 2x4 plates and one 2x2 in a different arrangement, so
# every bottom plate is crossed by a top plate and step 2 locks the floor into one piece.
with m.step():
    m.plate("2x4", x=0, z=0, y=0, color=FLOOR)
    m.plate("2x4", x=0, z=2, y=0, color=FLOOR)
    m.plate("2x4", x=0, z=4, y=0, color=FLOOR)
    m.plate("2x4", x=4, z=0, y=0, color=FLOOR, rot=90)
    m.plate("2x2", x=4, z=4, y=0, color=FLOOR)
with m.step():
    m.plate("2x4", x=0, z=0, y=1, color=FLOOR, rot=90)
    m.plate("2x2", x=0, z=4, y=1, color=FLOOR)
    m.plate("2x4", x=2, z=0, y=1, color=FLOOR)
    m.plate("2x4", x=2, z=2, y=1, color=FLOOR, rot=90)
    m.plate("2x4", x=4, z=2, y=1, color=FLOOR, rot=90)

# Walls: ring at x 0..5, z 0..5, one stud thick. Eight brick courses from level 2 up.
COURSES = [2 + 3 * i for i in range(8)]
SLIT_COURSES = (3, 5)


def course_a(y: int, door: bool = False) -> None:
    """Front and back walls own the corners."""
    if door:
        m.brick("1x2", x=0, z=0, y=y, color=STONE)
        m.brick("1x2", x=2, z=0, y=y, color=DOOR)
        m.brick("1x2", x=4, z=0, y=y, color=STONE)
    else:
        m.brick("1x4", x=0, z=0, y=y, color=STONE)
        m.brick("1x2", x=4, z=0, y=y, color=STONE)
    m.brick("1x2", x=0, z=5, y=y, color=STONE)
    m.brick("1x4", x=2, z=5, y=y, color=STONE)


def course_a_sides(y: int) -> None:
    m.brick("1x4", x=0, z=1, y=y, color=STONE, rot=90)
    m.brick("1x4", x=5, z=1, y=y, color=STONE, rot=90)


def course_b_front_back(y: int, door: bool = False, slit: bool = False) -> None:
    """Left and right walls own the corners; front/back fill x 1..4."""
    if door or slit:
        m.brick("1x1", x=1, z=0, y=y, color=STONE)
        m.brick("1x2", x=2, z=0, y=y, color=DOOR if door else SLIT)
        m.brick("1x1", x=4, z=0, y=y, color=STONE)
    else:
        m.brick("1x4", x=1, z=0, y=y, color=STONE)
    m.brick("1x4", x=1, z=5, y=y, color=STONE)


def course_b_sides(y: int, slit: bool = False) -> None:
    if slit:
        for x in (0, 5):
            m.brick("1x2", x=x, z=0, y=y, color=STONE, rot=90)
            m.brick("1x2", x=x, z=2, y=y, color=SLIT, rot=90)
            m.brick("1x2", x=x, z=4, y=y, color=STONE, rot=90)
    else:
        m.brick("1x4", x=0, z=0, y=y, color=STONE, rot=90)
        m.brick("1x2", x=0, z=4, y=y, color=STONE, rot=90)
        m.brick("1x2", x=5, z=0, y=y, color=STONE, rot=90)
        m.brick("1x4", x=5, z=2, y=y, color=STONE, rot=90)


for i, y in enumerate(COURSES):
    if i % 2 == 0:
        with m.step():
            course_a(y, door=(i == 0))
        with m.step():
            course_a_sides(y)
    else:
        with m.step():
            course_b_sides(y, slit=(i in SLIT_COURSES))
        with m.step():
            course_b_front_back(y, door=(i == 1), slit=(i in SLIT_COURSES))

# Battlement ring: 8x8 outline two studs wide, overhanging the walls by one stud.
RING_Y = COURSES[-1] + 3
with m.step():
    m.plate("2x4", x=-1, z=-1, y=RING_Y, color=STONE)
    m.plate("2x4", x=3, z=-1, y=RING_Y, color=STONE)
    m.plate("2x4", x=-1, z=5, y=RING_Y, color=STONE)
    m.plate("2x4", x=3, z=5, y=RING_Y, color=STONE)
    m.plate("2x4", x=-1, z=1, y=RING_Y, color=STONE, rot=90)
    m.plate("2x4", x=5, z=1, y=RING_Y, color=STONE, rot=90)

# Merlons on the outer edge: three per front/back side, one in the middle of each side wall.
MERLON_Y = RING_Y + 1
with m.step():
    for x in (-1, 2, 5):
        m.brick("1x2", x=x, z=-1, y=MERLON_Y, color=STONE)
    m.brick("1x2", x=-1, z=2, y=MERLON_Y, color=STONE, rot=90)
with m.step():
    for x in (-1, 2, 5):
        m.brick("1x2", x=x, z=6, y=MERLON_Y, color=STONE)
    m.brick("1x2", x=6, z=2, y=MERLON_Y, color=STONE, rot=90)
