"""Star Wars inspired micro ship: a TIE-fighter-style twin-wing fighter.

Front faces low z. Two upright wing panels (x=0 and x=7, levels 0..12) are joined to a small
central cockpit pod by 2x4 pylon plates at level 6 that run through the middle of each wing.
Build order: cockpit, pylons, then each wing grows up from its pylon and hangs down below it,
so every step leaves one connected piece.
"""

from lego.dsl import Model

FRAME = "dark_bluish_grey"
PANEL = "black"
HULL = "light_bluish_grey"
WINDOW = "black"

PYLON_Y = 6
LEFT_WING_X, RIGHT_WING_X = 0, 7
COCKPIT_X, COCKPIT_Z = 3, 2

m = Model("micro tie fighter")

# Cockpit pod, lower half: a window row in front of a hull row, tied by a plate underneath.
with m.step():
    m.plate("2x2", x=COCKPIT_X, z=COCKPIT_Z, y=PYLON_Y - 4, color=HULL)
    m.brick("1x2", x=COCKPIT_X, z=COCKPIT_Z, y=PYLON_Y - 3, color=WINDOW)  # front face
    m.brick("1x2", x=COCKPIT_X, z=COCKPIT_Z + 1, y=PYLON_Y - 3, color=HULL)

# Pylons on top of the pod, then the pod's upper half.
with m.step():
    m.plate("2x4", x=LEFT_WING_X, z=COCKPIT_Z, y=PYLON_Y, color=FRAME)  # x 0..3
    m.plate("2x4", x=COCKPIT_X + 1, z=COCKPIT_Z, y=PYLON_Y, color=FRAME)  # x 4..7
    m.brick("2x2", x=COCKPIT_X, z=COCKPIT_Z, y=PYLON_Y + 1, color=HULL)
    m.plate("2x2", x=COCKPIT_X, z=COCKPIT_Z, y=PYLON_Y + 4, color=HULL)

# A wing course: (size, z, color) bricks turned 90° so they run along z in column x.
PANEL_BAND = [("1x1", 0, FRAME), ("1x4", 1, PANEL), ("1x1", 5, FRAME)]
TOP_EDGE = [("1x2", 0, FRAME), ("1x4", 2, FRAME)]
BOTTOM_EDGE = [("1x4", 0, FRAME), ("1x2", 4, FRAME)]


def wing(x: int) -> None:
    """Upright wing panel at column x, z 0..5, levels 0..12; the pylon is its level 6."""

    def course(y: int, pieces: list[tuple[str, int, str]]) -> None:
        for size, z, color in pieces:
            m.brick(size, x=x, z=z, y=y, color=color, rot=90)

    with m.step():  # plates beside the pylon, locked by the panel band above
        m.plate("1x2", x=x, z=0, y=PYLON_Y, color=FRAME, rot=90)
        m.plate("1x2", x=x, z=4, y=PYLON_Y, color=FRAME, rot=90)
        course(PYLON_Y + 1, PANEL_BAND)
    with m.step():
        course(PYLON_Y + 4, TOP_EDGE)
    with m.step():  # hangs under the pylon layer
        course(PYLON_Y - 3, PANEL_BAND)
    with m.step():  # bottom edge, stands on the table
        course(PYLON_Y - 6, BOTTOM_EDGE)


wing(LEFT_WING_X)
wing(RIGHT_WING_X)
