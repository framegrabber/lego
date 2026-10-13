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

# --- chassis: two plate layers, joints staggered so every column is locked ---


def deck_column(x: int, even: bool) -> None:
    """Top chassis plates spanning the width at x..x+1 (alternating split)."""
    if even:
        m.plate("2x4", x=x, z=0, y=DECK, color=BODY_COLOR, rot=90)
        m.plate("2x2", x=x, z=4, y=DECK, color=BODY_COLOR)
    else:
        m.plate("2x2", x=x, z=0, y=DECK, color=BODY_COLOR)
        m.plate("2x4", x=x, z=2, y=DECK, color=BODY_COLOR, rot=90)


def under_outer_rows(x: int, size: str) -> None:
    """Bottom plates in the outer rows (z=0 and z=4)."""
    for z in (0, 4):
        m.plate(size, x=x, z=z, y=UNDER, color=UNDER_COLOR)


def wheel_pair(x: int) -> None:
    """Axle plates 10 studs wide (z=-2..7) with a wheel standing on each end.

    Every axle plate reaches under the 6-wide chassis, so the chassis locks them.
    """
    m.plate("2x4", x=x, z=-2, y=AXLE, color="black", rot=90)
    m.plate("2x2", x=x, z=2, y=AXLE, color="black")
    m.plate("2x4", x=x, z=WIDTH - 2, y=AXLE, color="black", rot=90)
    for z in (-2, WIDTH):
        m.brick("2x2", x=x, z=z, y=AXLE + 1, color="black")


with m.step():  # rear wheels
    wheel_pair(REAR_AXLE_X)

with m.step():
    under_outer_rows(0, "2x4")
    m.plate("2x2", x=0, z=2, y=UNDER, color=UNDER_COLOR)
    deck_column(0, even=True)

# columns x=2..12: outer rows join at x=4, 8, 12; middle row at x=2, 6, 10
for x in range(2, LENGTH, 2):
    with m.step():
        deck_column(x, even=(x // 2) % 2 == 0)
        if x % 4 == 2:
            m.plate("2x4", x=x, z=2, y=UNDER, color=UNDER_COLOR)
        else:
            under_outer_rows(x, "2x4" if x + 4 <= LENGTH else "2x2")

# --- front wheels hang under the chassis ---
with m.step():
    wheel_pair(FRONT_AXLE_X)

# --- body ---
with m.step():  # rear block
    for z in (0, 2, 4):
        m.brick("2x4", x=0, z=z, y=BODY, color=BODY_COLOR)

with m.step():  # side pods
    for z in (0, 4):
        m.brick("2x4", x=4, z=z, y=BODY, color=BODY_COLOR)
        m.brick("2x2", x=8, z=z, y=BODY, color=BODY_COLOR)

with m.step():  # cockpit: seat back, seat, steering wheel, dashboard
    m.brick("1x2", x=4, z=2, y=BODY, color="black", rot=90)
    m.plate("2x2", x=5, z=2, y=BODY, color="black")
    m.plate("1x2", x=7, z=2, y=BODY, color="black", rot=90)
    m.brick("2x2", x=8, z=2, y=BODY, color=BODY_COLOR)

with m.step():  # nose and front wing end plates
    m.brick("2x4", x=10, z=1, y=BODY, color=BODY_COLOR, rot=90)
    m.plate("2x4", x=12, z=1, y=BODY, color=BODY_COLOR, rot=90)
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
