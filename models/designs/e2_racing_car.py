"""A red racing car with a big spoiler at the back.

Length runs along x: the spoiler is at x=0 (left in the front view), the nose at x=15.
The body is 4 studs wide (z 1..4); the wheels and the rear wing stick out to the sides.
"""

from lego.dsl import Model

BODY = "red"
TYRE = "black"
AXLE = "black"
POST = "dark_bluish_grey"
GLASS = "trans_light_blue"

m = Model("e2 racing car")

# Wheel pair + axle: two tyres on the table, tied by two crossed plate layers (6 wide, z 0..5).
axle = m.subassembly("axle")
with axle.step():
    axle.brick("2x2", x=0, z=0, y=0, color=TYRE)
    axle.brick("2x2", x=0, z=4, y=0, color=TYRE)
with axle.step():
    axle.plate("2x4", x=0, z=0, y=3, color=AXLE, rot=90)  # z 0..3
    axle.plate("2x2", x=0, z=4, y=3, color=AXLE)
    axle.plate("2x2", x=0, z=0, y=4, color=AXLE)
    axle.plate("2x4", x=0, z=2, y=4, color=AXLE, rot=90)  # z 2..5, locks the layer below

REAR_AXLE_X = 2
FRONT_AXLE_X = 10
ROWS = (1, 3)  # the body is two 2-stud rows: z 1..2 and z 3..4

# Rear axle with the back of the floor (y=5) on it.
with m.step():
    m.attach(axle, x=REAR_AXLE_X, y=0, z=0)
    for z in ROWS:
        m.plate("2x4", x=0, z=z, y=5, color=BODY)  # x 0..3, on the rear axle

# Middle floor plates hang under the first body bricks.
with m.step():
    for z in ROWS:
        m.plate("2x4", x=4, z=z, y=5, color=BODY)  # x 4..7
        m.brick("2x4", x=2, z=z, y=6, color=BODY)  # x 2..5

# Front floor on the front axle, joined by the next body bricks.
with m.step():
    m.attach(axle, x=FRONT_AXLE_X, y=0, z=0)
    for z in ROWS:
        m.plate("2x4", x=8, z=z, y=5, color=BODY)  # x 8..11, on the front axle
        m.brick("2x4", x=6, z=z, y=6, color=BODY)  # x 6..9

# Nose: floor plates hang under the front bricks; a slope finishes the tip.
with m.step():
    for z in ROWS:
        m.plate("2x4", x=12, z=z, y=5, color=BODY)  # x 12..15
        m.brick("2x4", x=10, z=z, y=6, color=BODY)  # x 10..13
    m.slope("2x4", x=14, z=1, y=6, color=BODY, facing="right")  # x 14..15

# Front wing under the nose, rear end of the body.
with m.step():
    m.plate("2x4", x=14, z=0, y=4, color=TYRE, rot=90)  # z 0..3
    m.plate("2x2", x=14, z=4, y=4, color=TYRE)
    for z in ROWS:
        m.brick("2x2", x=0, z=z, y=6, color=BODY)

# Engine cover and cockpit sides.
with m.step():
    m.brick("2x4", x=2, z=1, y=9, color=BODY, rot=90)  # x 2..3, across both rows
    m.brick("2x4", x=4, z=1, y=9, color=BODY, rot=90)  # x 4..5
    m.brick("1x4", x=6, z=1, y=9, color=BODY)  # cockpit side, x 6..9
    m.brick("1x4", x=6, z=4, y=9, color=BODY)

# Driver, windscreen, air intake.
with m.step():
    m.brick("2x2", x=7, z=2, y=9, color="white")  # helmet
    m.slope("2x4", x=10, z=1, y=9, color=GLASS, facing="right")  # windscreen
    m.brick("2x4", x=2, z=1, y=12, color=BODY, rot=90)
    m.slope("2x4", x=4, z=1, y=12, color=BODY, facing="right")

# Spoiler posts: three bricks tall so the wing stands well above the engine.
with m.step():
    for y in (9, 12, 15):
        m.brick("1x2", x=0, z=1, y=y, color=POST)
        m.brick("1x2", x=0, z=4, y=y, color=POST)

# The big rear wing: 10 studs wide, two plates thick, seams crossed.
with m.step():
    m.plate("2x4", x=0, z=-2, y=18, color=BODY, rot=90)  # z -2..1, on the left post
    m.plate("2x2", x=0, z=2, y=18, color=BODY)  # z 2..3, held by the layer above
    m.plate("2x4", x=0, z=4, y=18, color=BODY, rot=90)  # z 4..7, on the right post
    m.plate("2x4", x=0, z=-1, y=19, color=BODY, rot=90)  # z -1..2
    m.plate("2x4", x=0, z=3, y=19, color=BODY, rot=90)  # z 3..6

# End fins on the wing tips.
with m.step():
    m.brick("1x2", x=0, z=-2, y=19, color=TYRE)
    m.brick("1x2", x=0, z=7, y=19, color=TYRE)
