"""A small house with a door, two windows and a roof.

Footprint 8 studs wide (x) by 6 deep (z). Green base, white walls four bricks tall,
a brown door in the middle of the front wall, two see-through windows either side
of it, and a red pitched roof made of slopes that rises from both long walls.
"""

from lego.dsl import Model

m = Model("e2_house")

W, D = 8, 6                 # footprint: x 0..7, z 0..5
FRONT, BACK = 0, D - 1      # wall rows along z
LEFT, RIGHT = 0, W - 1      # wall columns along x
BASE = "green"
WALL = "white"
DOOR = "brown"
GLASS = "trans_light_blue"
ROOF = "red"
DOOR_X = 3                  # door covers x 3..4
WIN_X = (1, 6)              # windows are 1 stud wide, in layers 2 and 3


def ly(layer):
    """Bottom level of wall brick layer 1..4 (base plate is level 0)."""
    return 1 + 3 * (layer - 1)


ROOF_Y = ly(5)              # first roof row sits on top of the walls


def side_long(layer):
    """Side walls without corners (z 1..4): a 1x4 on each side."""
    for x in (LEFT, RIGHT):
        m.brick("1x4", x=x, z=1, y=ly(layer), color=WALL, rot=90)


def side_with_corners(layer):
    """Side walls owning both corners: 1x2 at the front, 1x4 to the back."""
    for x in (LEFT, RIGHT):
        m.brick("1x2", x=x, z=0, y=ly(layer), color=WALL, rot=90)
        m.brick("1x4", x=x, z=2, y=ly(layer), color=WALL, rot=90)


def door(layer):
    m.brick("1x2", x=DOOR_X, z=FRONT, y=ly(layer), color=DOOR)


def front_pillars_and_windows(layer):
    """x 1, 2, 5, 6: a window, a wall pillar, a wall pillar, a window."""
    for wx in WIN_X:
        m.brick("1x1", x=wx, z=FRONT, y=ly(layer), color=GLASS)
    for px in (2, 5):
        m.brick("1x1", x=px, z=FRONT, y=ly(layer), color=WALL)


def row_inner(z, layer):
    """Wall row between the side walls (x 1..6): 1x2 then 1x4."""
    m.brick("1x2", x=1, z=z, y=ly(layer), color=WALL)
    m.brick("1x4", x=3, z=z, y=ly(layer), color=WALL)


def row_full(z, layer):
    """Wall row across the whole width (x 0..7): two 1x4s."""
    m.brick("1x4", x=0, z=z, y=ly(layer), color=WALL)
    m.brick("1x4", x=4, z=z, y=ly(layer), color=WALL)


# --- base -------------------------------------------------------------------
with m.step():
    for z in (0, 2, 4):
        for x in (0, 4):
            m.plate("2x4", x=x, z=z, y=0, color=BASE)

# --- layer 1: door, sides lock the base plates together ----------------------
with m.step():
    door(1)
    side_long(1)

with m.step():
    m.brick("1x2", x=0, z=FRONT, y=ly(1), color=WALL)
    m.brick("1x1", x=2, z=FRONT, y=ly(1), color=WALL)
    m.brick("1x1", x=5, z=FRONT, y=ly(1), color=WALL)
    m.brick("1x2", x=6, z=FRONT, y=ly(1), color=WALL)
    row_full(BACK, 1)

# --- layer 2: windows start ---------------------------------------------------
with m.step():
    side_with_corners(2)
    door(2)

with m.step():
    front_pillars_and_windows(2)
    row_inner(BACK, 2)

# --- layer 3 -------------------------------------------------------------------
with m.step():
    side_long(3)
    door(3)
    for x in (LEFT, RIGHT):
        m.brick("1x1", x=x, z=FRONT, y=ly(3), color=WALL)

with m.step():
    front_pillars_and_windows(3)
    row_full(BACK, 3)

# --- layer 4: lintel over door and windows -------------------------------------
with m.step():
    side_with_corners(4)
    row_inner(FRONT, 4)

# --- roof: three slope rows per side, each one stud further in, then a ridge ---
# White gable bricks close the triangle under the roof at both ends.
with m.step():
    row_inner(BACK, 4)
    for x in (LEFT, RIGHT):
        m.brick("1x4", x=x, z=1, y=ROOF_Y, color=WALL, rot=90)

with m.step():
    for x in (0, 4):
        m.slope("2x4", x=x, z=FRONT - 1, y=ROOF_Y, color=ROOF, facing="front")
        m.slope("2x4", x=x, z=BACK, y=ROOF_Y, color=ROOF, facing="back")
    for x in (LEFT, RIGHT):
        m.brick("1x2", x=x, z=2, y=ROOF_Y + 3, color=WALL, rot=90)

with m.step():
    for size, x in (("2x2", 0), ("2x4", 2), ("2x2", 6)):
        m.slope(size, x=x, z=FRONT, y=ROOF_Y + 3, color=ROOF, facing="front")
        m.slope(size, x=x, z=BACK - 1, y=ROOF_Y + 3, color=ROOF, facing="back")

with m.step():
    for x in (0, 4):
        m.slope("2x4", x=x, z=FRONT + 1, y=ROOF_Y + 6, color=ROOF, facing="front")
        m.slope("2x4", x=x, z=BACK - 2, y=ROOF_Y + 6, color=ROOF, facing="back")
        m.plate("2x4", x=x, z=2, y=ROOF_Y + 9, color=ROOF)

with m.step():                                   # chimney on the ridge
    m.brick("2x2", x=5, z=2, y=ROOF_Y + 10, color="dark_bluish_grey")
