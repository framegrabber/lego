"""A lighthouse with red and white stripes and a light on top.

Plan: 6x6 grey rock base (two plate layers), a hollow 4x4 tower of 10 brick layers in
stripes of two layers (red/white), a brown door at the bottom and two small windows, a black
6x6 gallery, a yellow lamp room with black corner posts, and a red gable roof.
Tower footprint x 0..3, z 0..3; base and gallery x -1..4, z -1..4.
"""

from lego.dsl import Model

m = Model("e2_lighthouse")

BASE = "dark_bluish_grey"
GALLERY = "black"
STRIPE_COLORS = ["red", "white"]
LAYERS = 10  # tower brick layers
STRIPE = 2  # layers per stripe
TOWER_Y = 2  # tower starts on top of the two base plate layers
DOOR = "brown"
WINDOW = "trans_light_blue"


def base_pinwheel(y, mirror):
    """Four 2x4 plates around the (hollow) centre; the two layers turn opposite ways so every
    top plate crosses a joint of the layer below."""
    if not mirror:
        plates = [(-1, -1, 0), (3, -1, 90), (1, 3, 0), (-1, 1, 90)]
    else:
        plates = [(-1, -1, 90), (1, -1, 0), (3, 1, 90), (-1, 3, 0)]
    with m.step():
        for x, z, rot in plates:
            m.plate("2x4", x=x, z=z, y=y, color=BASE, rot=rot)


def tower_layer(i):
    """One hollow 4x4 ring. Even layers: long walls left/right; odd: long walls front/back."""
    y = TOWER_Y + 3 * i
    c = STRIPE_COLORS[(i // STRIPE) % 2]
    with m.step():
        if i % 2 == 0:
            front = DOOR if i == 0 else WINDOW if i in (4, 8) else c
            m.brick("1x4", x=0, z=0, y=y, color=c, rot=90)
            m.brick("1x4", x=3, z=0, y=y, color=c, rot=90)
            m.brick("1x2", x=1, z=0, y=y, color=front)
            m.brick("1x2", x=1, z=3, y=y, color=c)
        else:
            if i == 1:  # door top: split the front wall
                m.brick("1x1", x=0, z=0, y=y, color=c)
                m.brick("1x2", x=1, z=0, y=y, color=DOOR)
                m.brick("1x1", x=3, z=0, y=y, color=c)
            else:
                m.brick("1x4", x=0, z=0, y=y, color=c)
            m.brick("1x4", x=0, z=3, y=y, color=c)
            m.brick("1x2", x=0, z=1, y=y, color=c, rot=90)
            m.brick("1x2", x=3, z=1, y=y, color=c, rot=90)


base_pinwheel(0, mirror=False)
base_pinwheel(1, mirror=True)
for i in range(LAYERS):
    tower_layer(i)

GALLERY_Y = TOWER_Y + 3 * LAYERS
with m.step():  # gallery: overhangs the tower by one stud all round
    m.plate("2x4", x=-1, z=-1, y=GALLERY_Y, color=GALLERY)
    m.plate("2x2", x=3, z=-1, y=GALLERY_Y, color=GALLERY)
    m.plate("2x2", x=-1, z=1, y=GALLERY_Y, color=GALLERY)
    m.plate("2x4", x=1, z=1, y=GALLERY_Y, color=GALLERY)
    m.plate("2x4", x=-1, z=3, y=GALLERY_Y, color=GALLERY)
    m.plate("2x2", x=3, z=3, y=GALLERY_Y, color=GALLERY)

LAMP_Y = GALLERY_Y + 1
with m.step():  # the light and the window frame corners
    m.brick("2x2", x=1, z=1, y=LAMP_Y, color="trans_yellow")
    for x, z in [(0, 0), (3, 0), (0, 3), (3, 3)]:
        m.brick("1x1", x=x, z=z, y=LAMP_Y, color="black")
with m.step():  # lamp room windows glow yellow
    m.brick("1x2", x=1, z=0, y=LAMP_Y, color="trans_yellow")
    m.brick("1x2", x=1, z=3, y=LAMP_Y, color="trans_yellow")
    m.brick("1x2", x=0, z=1, y=LAMP_Y, color="trans_yellow", rot=90)
    m.brick("1x2", x=3, z=1, y=LAMP_Y, color="trans_yellow", rot=90)

ROOF_Y = LAMP_Y + 3
with m.step():  # red roof
    m.slope("2x4", x=0, z=0, y=ROOF_Y, color="red", facing="front")  # studs on z=1
    m.slope("2x4", x=0, z=2, y=ROOF_Y, color="red", facing="back")  # studs on z=2
with m.step():  # cap on both stud rows of the roof
    m.plate("2x2", x=1, z=1, y=ROOF_Y + 3, color="red")
