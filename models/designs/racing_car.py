"""A red racing car with a big spoiler at the back.

Plan: low red F1-style racer, 14 studs long along x (back at x=0, nose at x=13) and
6 studs wide along z (z=0..5). Black wheels stand beside the body on wide black axle
plates. Two-plate chassis (grey underbody + red top) in running bond, red bricks for the
rear block, side pods and nose, an open cockpit with a yellow helmet, and a tall black
rear wing (8 studs wide) on two pillars with red end plates.
"""

from lego.dsl import Model

m = Model("racing_car")

LENGTH = 14  # studs along x
WIDTH = 6  # studs along z

AXLE = 0  # wide black axle plates under each wheel pair
UNDER = AXLE + 1  # bottom chassis plate level
DECK = UNDER + 1  # top chassis plate level
BODY = DECK + 1  # first brick layer
TOP = BODY + 3  # top of the body bricks
COVER_TOP = TOP + 3  # top of the raised engine cover
WING = COVER_TOP + 3  # wing sits on one brick of pillar
REAR_AXLE_X = 2
FRONT_AXLE_X = 10

UNDER_COLOR = "dark_bluish_grey"
BODY_COLOR = "red"

# --- chassis: two plate layers ---
# Under layer (grey) runs along x in three rows; deck (red) runs across in 2-wide columns,
# alternating a 2x4 (spanning 4 rows' worth of z) with a 2x2. The z=0..1 row only bonds to
# the rest through the body bricks on top, so a few body parts are placed while the chassis
# grows: after every step the build is one piece.


def under(size: str, x: int, z: int) -> None:
    m.plate(size, x=x, z=z, y=UNDER, color=UNDER_COLOR)


def deck_long(x: int, z: int) -> None:
    """Red 2x4 deck plate across the width: x..x+1, z..z+3."""
    m.plate("2x4", x=x, z=z, y=DECK, color=BODY_COLOR, rot=90)


def deck_short(x: int, z: int) -> None:
    m.plate("2x2", x=x, z=z, y=DECK, color=BODY_COLOR)


def axle_plates(x: int) -> None:
    """Axle plates 10 studs wide (z=-2..7); each one reaches under the chassis."""
    m.plate("2x4", x=x, z=-2, y=AXLE, color="black", rot=90)
    m.plate("2x2", x=x, z=2, y=AXLE, color="black")
    m.plate("2x4", x=x, z=WIDTH - 2, y=AXLE, color="black", rot=90)


def wheels(x: int) -> None:
    for z in (-2, WIDTH):
        m.brick("2x2", x=x, z=z, y=AXLE + 1, color="black")


with m.step():  # rear axle plates on the table
    axle_plates(REAR_AXLE_X)

with m.step():  # first chassis plates lock all three axle plates together
    under("2x4", 0, 0)
    under("2x4", 2, 2)
    under("2x4", 0, 4)
    deck_long(0, 0)
    deck_long(2, 2)
    m.brick("2x4", x=0, z=2, y=BODY, color=BODY_COLOR)  # middle of the rear block

with m.step():  # rear wheels, rest of the rear chassis
    wheels(REAR_AXLE_X)
    deck_short(0, 4)
    deck_short(2, 0)
    under("2x2", 0, 2)

with m.step():  # rear block
    for z in (0, 4):
        m.brick("2x4", x=0, z=z, y=BODY, color=BODY_COLOR)

with m.step():  # chassis x=4..7 and the black seat that bonds it
    under("2x4", 4, 0)
    deck_long(4, 0)
    deck_short(6, 0)
    under("2x4", 4, 4)
    deck_long(6, 2)
    m.plate("2x2", x=5, z=2, y=BODY, color="black")  # seat

with m.step():  # chassis x=4..11
    deck_short(4, 4)
    under("2x4", 6, 2)
    deck_long(8, 0)
    under("2x4", 8, 0)
    deck_short(10, 0)

with m.step():  # chassis x=8..13 and the nose brick that bonds it
    under("2x4", 8, 4)
    deck_short(8, 4)
    deck_long(10, 2)
    under("2x4", 10, 2)
    m.brick("2x4", x=10, z=1, y=BODY, color=BODY_COLOR, rot=90)  # nose

with m.step():  # chassis tip and the front wing plate
    deck_long(12, 0)
    under("2x2", 12, 0)
    under("2x2", 12, 4)
    deck_short(12, 4)
    m.plate("2x4", x=12, z=1, y=BODY, color=BODY_COLOR, rot=90)

# --- front wheels hang under the chassis ---
with m.step():
    axle_plates(FRONT_AXLE_X)
    wheels(FRONT_AXLE_X)

# --- body ---
with m.step():  # side pods
    for z in (0, 4):
        m.brick("2x4", x=4, z=z, y=BODY, color=BODY_COLOR)
        m.brick("2x2", x=8, z=z, y=BODY, color=BODY_COLOR)

with m.step():  # cockpit: seat back, steering wheel, dashboard; front wing end plates
    m.brick("1x2", x=4, z=2, y=BODY, color="black", rot=90)
    m.plate("1x2", x=7, z=2, y=BODY, color="black", rot=90)
    m.brick("2x2", x=8, z=2, y=BODY, color=BODY_COLOR)
    for z in (0, WIDTH - 1):
        m.plate("1x2", x=12, z=z, y=BODY, color="black")

with m.step():  # driver, windscreen, racing stripes
    m.brick("2x2", x=5, z=2, y=BODY + 1, color="yellow")
    m.brick("1x2", x=8, z=2, y=TOP, color="trans_clear", rot=90)
    for z in (0, WIDTH - 1):
        m.plate("1x4", x=4, z=z, y=TOP, color="white")

with m.step():  # raised engine cover
    for x in (0, 2):
        m.brick("2x4", x=x, z=1, y=TOP, color=BODY_COLOR, rot=90)

# --- big rear wing ---
with m.step():  # pillars
    for z in (1, 4):
        m.brick("1x2", x=0, z=z, y=COVER_TOP, color="black")

with m.step():  # wing: two layers with staggered joints, 8 studs wide
    m.plate("2x4", x=0, z=-1, y=WING, color="black", rot=90)
    m.plate("2x4", x=0, z=3, y=WING, color="black", rot=90)
    m.plate("2x2", x=0, z=-1, y=WING + 1, color="black")
    m.plate("2x4", x=0, z=1, y=WING + 1, color="black", rot=90)
    m.plate("2x2", x=0, z=5, y=WING + 1, color="black")

with m.step():  # end plates hang under the wing tips
    for z in (-1, WIDTH):
        m.brick("1x2", x=0, z=z, y=COVER_TOP, color=BODY_COLOR)
