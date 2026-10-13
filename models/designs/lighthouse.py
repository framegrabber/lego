"""A lighthouse with red and white stripes and a light on top.

Layers (bottom up):
- 8x8 rocky island: two plate layers with crossed joints.
- Wide lower tower: 6x6 hollow ring, 3 brick layers, striped.
- White plate cap that steps the tower in to 4x4.
- Slim upper tower: 4x4 hollow ring, 5 brick layers, striped, with black windows.
- Black 6x6 gallery plate, lamp room with a yellow light, stepped red roof.
"""

from lego.dsl import Model

m = Model("lighthouse")

STRIPES = ["red", "white"]

# --- island ------------------------------------------------------------------
# Grey rock: 2x4 plates in four rows of two, seams at x=4 and z=2, 4, 6.
# Green grass on top bridges every grey seam: 2-wide columns at the left and
# right edges, plus middle plates whose joints cross both x=4 and z=4.
def grey(x, z):
    m.plate("2x4", x=x, y=0, z=z, color="dark_bluish_grey")


def green(x, z, rot=0):
    m.plate("2x4", x=x, y=1, z=z, color="green", rot=rot)


with m.step():                       # front six grey plates, loose on the table
    for z in (0, 2, 4):
        for x in (0, 4):
            grey(x, z)

with m.step():                       # green locks the six into one piece
    green(2, 0)                      # across x=4 at the front
    green(0, 0, rot=90)              # left edge, across z=2
    green(6, 0, rot=90)              # right edge, across z=2
    green(2, 2, rot=90)              # middle left, across z=4
    green(4, 2, rot=90)              # middle right, across z=4

with m.step():                       # back row: grey underneath, green on top
    for x in (0, 4):
        grey(x, 6)
    green(0, 4, rot=90)              # left edge, across z=6
    green(6, 4, rot=90)              # right edge, across z=6
    green(2, 6)                      # across x=4 at the back


def ring6(y, color, layer, door=False):
    """6x6 hollow ring with min corner (1, 1); alternate joints by layer."""
    lo, hi = 1, 6
    if layer % 2 == 0:
        # front/back run full width, sides fill between
        with m.step():
            for x in (lo, hi):
                m.brick("1x4", x=x, y=y, z=lo + 1, color=color, rot=90)
            if door:
                # front: wall, brown door in the middle, wall
                m.brick("1x2", x=lo, y=y, z=lo, color=color)
                m.brick("1x2", x=lo + 2, y=y, z=lo, color="brown")
                m.brick("1x2", x=lo + 4, y=y, z=lo, color=color)
            else:
                m.brick("1x4", x=lo, y=y, z=lo, color=color)
                m.brick("1x2", x=lo + 4, y=y, z=lo, color=color)
        with m.step():
            m.brick("1x4", x=lo, y=y, z=hi, color=color)
            m.brick("1x2", x=lo + 4, y=y, z=hi, color=color)
        return
    # sides run full depth, front/back fill between
    with m.step():
        for x in (lo, hi):
            m.brick("1x4", x=x, y=y, z=lo, color=color, rot=90)
            m.brick("1x2", x=x, y=y, z=lo + 4, color=color, rot=90)
        for z in (lo, hi):
            m.brick("1x4", x=lo + 1, y=y, z=z, color=color)


def ring4(y, color, layer, window=False):
    """4x4 hollow ring with min corner (2, 2); alternate joints by layer."""
    lo, hi = 2, 5
    with m.step():
        if layer % 2 == 0:
            for z in (lo, hi):
                m.brick("1x4", x=lo, y=y, z=z, color=color)
            for x in (lo, hi):
                m.brick("1x2", x=x, y=y, z=lo + 1, color=color, rot=90)
        else:
            for x in (lo, hi):
                m.brick("1x4", x=x, y=y, z=lo, color=color, rot=90)
            for z in (lo, hi):
                m.brick("1x2", x=lo + 1, y=y, z=z,
                        color="black" if window else color)


def deck6(y, color):
    """Solid 6x6 plate layer with min corner (1, 1)."""
    with m.step():
        for z in (1, 3, 5):
            m.plate("2x4", x=1, y=y, z=z, color=color)
            m.plate("2x2", x=5, y=y, z=z, color=color)


# --- lower tower: 3 brick layers, y = 2, 5, 8 -------------------------------
y = 2
for i in range(3):
    ring6(y, STRIPES[i % 2], i, door=(i == 0))
    y += 3

# --- cap plate stepping in to 4x4 -------------------------------------------
deck6(y, "white")
y += 1

# --- upper tower: 5 brick layers --------------------------------------------
for i in range(5):
    ring4(y, STRIPES[i % 2], i, window=(i in (1, 3)))
    y += 3

# --- gallery ----------------------------------------------------------------
deck6(y, "black")
y += 1

# --- lamp room ---------------------------------------------------------------
with m.step():
    for x in (2, 5):
        for z in (2, 5):
            m.brick("1x1", x=x, y=y, z=z, color="black")
    m.brick("2x2", x=3, y=y, z=3, color="yellow")

with m.step():
    for z in (2, 5):
        m.brick("1x2", x=3, y=y, z=z, color="trans_yellow")
    for x in (2, 5):
        m.brick("1x2", x=x, y=y, z=3, color="trans_yellow", rot=90)
y += 3

# --- roof ---------------------------------------------------------------------
with m.step():
    for z in (2, 4):
        m.plate("2x4", x=2, y=y, z=z, color="red")
y += 1

with m.step():
    m.plate("2x2", x=3, y=y, z=3, color="red")
