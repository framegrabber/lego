"""A stone arch bridge over a blue river.

Length runs along x so the front view shows the arches. Footprint 16 x 6 studs:
green banks at x 0..3 and x 12..15, river x 4..11, bridge deck z 1..4.
Grey abutments on each bank, one pier in the middle of the river, inverted
slopes form two arches, dark grey road on top with red railings.
"""

from lego.dsl import Model

m = Model("e2_bridge")

LENGTH = 16
STONE = "light_bluish_grey"
ROAD = "dark_bluish_grey"
RAIL = "red"
GRASS = "green"
WATER = "blue"

# heights (plate levels)
BASE = 0           # bottom plates
L1, L2, L3 = 1, 4, 7  # brick layers of abutments / pier
DECK = 10          # deck beam plates
TOP = 11           # road plates + railing posts


def mx(x, w=1):
    """Mirror a min-corner x across the model's centre for a part w studs wide."""
    return LENGTH - x - w


def base_plate(col, row):
    color = GRASS if col in (0, 3) else WATER
    m.plate("2x4", x=4 * col, z=2 * row, y=BASE, color=color)


# railing segment: two posts and a rail, 4 studs long
rail = m.subassembly("railing")
with rail.step():
    rail.brick("1x1", x=0, z=0, y=0, color=RAIL)
    rail.brick("1x1", x=2, z=0, y=0, color=RAIL)
    rail.plate("1x4", x=0, z=0, y=3, color=RAIL)

# --- base: left bank + left half of the river, joined by abutment and pier ---
with m.step():
    for row in range(3):
        base_plate(0, row)
        base_plate(1, row)

with m.step():
    m.brick("2x4", x=0, z=1, y=L1, color=STONE, rot=90)
    m.brick("2x4", x=2, z=1, y=L1, color=STONE, rot=90)
    m.brick("2x4", x=7, z=1, y=L1, color=STONE, rot=90)    # pier
    m.plate("1x2", x=3, z=0, y=L1, color="dark_bluish_grey")  # rock on the shore

# --- right half of the river, pressed up under the pier ---
with m.step():
    for row in range(3):
        base_plate(2, row)
    base_plate(3, 0)
    m.plate("1x2", x=mx(3, 2), z=0, y=L1, color="dark_bluish_grey")

with m.step():
    base_plate(3, 1)
    base_plate(3, 2)
    m.brick("2x4", x=mx(0, 2), z=1, y=L1, color=STONE, rot=90)
    m.brick("2x4", x=mx(2, 2), z=1, y=L1, color=STONE, rot=90)

# --- back shore rocks and bushes on the banks ---
with m.step():
    m.plate("1x2", x=3, z=5, y=L1, color="dark_bluish_grey")
    m.plate("1x2", x=mx(3, 2), z=5, y=L1, color="dark_bluish_grey")
    m.brick("1x1", x=1, z=0, y=L1, color=GRASS)
    m.brick("1x1", x=mx(1), z=5, y=L1, color=GRASS)
with m.step():
    m.plate("1x1", x=1, z=0, y=L1 + 3, color="lime")
    m.plate("1x1", x=mx(1), z=5, y=L1 + 3, color="lime")
    # little boat on the river, in front of the right arch
    m.plate("1x2", x=9, z=0, y=L1, color="brown")
    m.brick("1x1", x=9, z=0, y=L1 + 1, color="white")


# --- second brick layer: seams shifted ---
def abutment_layer2(mirror):
    def X(x, w):
        return mx(x, w) if mirror else x
    m.brick("1x4", x=X(0, 1), z=1, y=L2, color=STONE, rot=90)
    m.brick("2x4", x=X(1, 2), z=1, y=L2, color=STONE, rot=90)
    m.brick("1x4", x=X(3, 1), z=1, y=L2, color=STONE, rot=90)


with m.step():
    abutment_layer2(False)
    m.brick("2x4", x=7, z=1, y=L2, color=STONE, rot=90)    # pier
with m.step():
    abutment_layer2(True)


# --- third layer: arch springers (inverted slopes reaching over the water) ---
def abutment_layer3(mirror):
    def X(x, w):
        return mx(x, w) if mirror else x
    m.brick("2x4", x=X(0, 2), z=1, y=L3, color=STONE, rot=90)
    m.brick("1x4", x=X(2, 1), z=1, y=L3, color=STONE, rot=90)
    for z in (1, 3):
        m.inverted_slope("2x2", x=X(3, 2), z=z, y=L3, color=STONE,
                         facing="left" if mirror else "right")


with m.step():
    abutment_layer3(False)
with m.step():
    abutment_layer3(True)
with m.step():  # top of the pier
    for z in (1, 3):
        m.inverted_slope("2x2", x=6, z=z, y=L3, color=STONE, facing="left")
        m.inverted_slope("2x2", x=8, z=z, y=L3, color=STONE, facing="right")

# --- deck beams: each plate rests on two supports ---
for xs in ((0, 4), (8, 12)):
    with m.step():
        for x in xs:
            for z in (1, 3):
                m.plate("2x4", x=x, z=z, y=DECK, color=STONE)

# --- road: crosses every deck seam ---
with m.step():
    m.plate("2x2", x=0, z=2, y=TOP, color=ROAD)
    m.plate("2x4", x=2, z=2, y=TOP, color=ROAD)
    m.plate("2x4", x=6, z=2, y=TOP, color=ROAD)
with m.step():
    m.plate("2x4", x=10, z=2, y=TOP, color=ROAD)
    m.plate("2x2", x=14, z=2, y=TOP, color=ROAD)

# --- railings along both edges ---
for xs in ((0, 4), (8, 12)):
    with m.step():
        for x in xs:
            m.attach(rail, x=x, y=TOP, z=1)
            m.attach(rail, x=x, y=TOP, z=4)
