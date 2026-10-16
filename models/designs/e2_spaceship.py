"""A spaceship with wings.

Nose points to +x (front view shows the profile, the left wing faces the camera). The fuselage
runs x 0..13, z 0..3. A dark keel stands on the table and lifts a two-layer plate deck (levels
3-4) that forms both stepped delta wings (left wing z < 0, right wing mirrored to z > 3). The body
rises from the deck with a blue cockpit and a pointed nose; engine pods sit on the wing roots and
small red fins stand on the wing tips.
"""

from lego.dsl import Model

HULL = "white"
STRIPE = "red"
DARK = "dark_bluish_grey"
GREY = "light_bluish_grey"
GLASS = "trans_light_blue"
GLOW = "trans_red"

DECK_Y = 3  # lower deck layer; the upper layer is DECK_Y + 1
BODY_Y = DECK_Y + 1  # first body brick course
TOP_Y = BODY_Y + 3  # second body brick course
WING_TOP = DECK_Y + 2  # top of the upper deck layer

m = Model("spaceship")


def depth(kind: str, size: str, rot: int = 0, facing: str = "front") -> int:
    """Studs a part covers along z."""
    a, b = (int(n) for n in size.split("x"))
    if kind in ("slope", "inverted_slope"):
        return 2 if facing in ("front", "back") else b
    return a if rot in (0, 180) else b


def mirror_z(z: int, d: int) -> int:
    """Min corner of the part mirrored across the fuselage centre line (z 0..3)."""
    return 4 - z - d


def pair(kind: str, size: str, x: int, y: int, z: int, color: str, rot: int = 0) -> None:
    """Place a brick/plate on the left wing side and its mirror on the right."""
    place = getattr(m, kind)
    place(size, x=x, y=y, z=z, color=color, rot=rot)
    place(size, x=x, y=y, z=mirror_z(z, depth(kind, size, rot)), color=color, rot=rot)


# Engine pod: built separately, one sits on each wing root.
pod = m.subassembly("engine")
with pod.step():
    pod.brick("2x4", x=0, z=0, y=0, color=DARK)
    pod.plate("2x2", x=0, z=0, y=3, color=DARK)
    pod.slope("2x2", x=2, z=0, y=3, color=HULL, facing="right")
with pod.step():
    pod.plate("1x1", x=0, z=0, y=4, color=GLOW)
    pod.plate("1x1", x=0, z=1, y=4, color=GLOW)

# Keel on the table: two rows of bricks, x 1..10.
with m.step():
    for z in (0, 2):
        m.brick("2x4", x=1, z=z, y=0, color=DARK)
        m.brick("2x4", x=5, z=z, y=0, color=DARK)
        m.brick("2x2", x=9, z=z, y=0, color=DARK)

# Centre strip of the lower deck ties both keel rows together.
with m.step():
    m.plate("2x2", x=0, z=1, y=DECK_Y, color=GREY)
    m.plate("2x4", x=2, z=1, y=DECK_Y, color=GREY)
    m.plate("2x4", x=6, z=1, y=DECK_Y, color=GREY)
    m.plate("2x4", x=10, z=1, y=DECK_Y, color=GREY)  # reaches under the nose

# Lower wing band: plates running across from the wing into the fuselage edge.
for side_z in (-3, mirror_z(-3, 4)):
    with m.step():
        for x in range(0, 12, 2):
            m.plate("2x4", x=x, z=side_z, y=DECK_Y, color=HULL, rot=90)

# Upper wing row next to the fuselage locks the band plates.
with m.step():
    for x in (0, 4, 8):
        pair("plate", "2x4", x=x, y=DECK_Y + 1, z=-2, color=HULL)

# Middle wing row: outer lower plates hang under the upper row, so they share a step.
for mirrored in (False, True):
    with m.step():

        def z_of(z: int, d: int) -> int:
            return mirror_z(z, d) if mirrored else z

        m.plate("2x4", x=0, z=z_of(-5, 2), y=DECK_Y, color=HULL)
        m.plate("2x2", x=4, z=z_of(-5, 2), y=DECK_Y, color=HULL)
        m.plate("2x4", x=0, z=z_of(-4, 2), y=DECK_Y + 1, color=STRIPE)
        m.plate("2x4", x=4, z=z_of(-4, 2), y=DECK_Y + 1, color=STRIPE)

# Wing tips.
with m.step():
    pair("plate", "2x4", x=0, y=DECK_Y + 1, z=-6, color=HULL)

# First body course: bricks across the full fuselage width tie both wings together.
for xs in ((0, 2, 4), (6, 8, 10)):
    with m.step():
        for x in xs:
            m.brick("2x4", x=x, z=0, y=BODY_Y, color=HULL, rot=90)

# Laser cannons fill the front of the lower wing band.
with m.step():
    pair("plate", "1x4", x=8, y=DECK_Y + 1, z=-3, color=DARK)
    pair("plate", "1x2", x=8, y=DECK_Y + 2, z=-3, color=GREY)
    pair("plate", "1x1", x=11, y=DECK_Y + 2, z=-3, color=GLOW)

# Nose wedge on the deck's front plate.
with m.step():
    m.slope("2x4", x=12, z=0, y=BODY_Y, color=STRIPE, facing="right")

# Second body course runs along x to lock the first one.
with m.step():
    m.brick("2x4", x=0, z=0, y=TOP_Y, color=HULL)
    m.brick("2x4", x=4, z=0, y=TOP_Y, color=HULL)
    m.brick("2x2", x=8, z=0, y=TOP_Y, color=HULL)
with m.step():
    m.brick("2x2", x=0, z=2, y=TOP_Y, color=HULL)
    m.brick("2x4", x=2, z=2, y=TOP_Y, color=HULL)
    m.brick("2x4", x=6, z=2, y=TOP_Y, color=HULL)

# Cockpit canopy and a stripe behind it.
with m.step():
    m.slope("2x4", x=10, z=0, y=TOP_Y, color=GLASS, facing="right")
    m.plate("2x4", x=8, z=0, y=TOP_Y + 3, color=STRIPE, rot=90)
    m.plate("2x2", x=0, z=1, y=TOP_Y + 3, color=DARK)

# Engines on the wing roots.
with m.step():
    m.attach(pod, x=0, y=WING_TOP, z=-2)
    m.attach(pod, x=0, y=WING_TOP, z=mirror_z(-2, 2))

# Fins on the wing tips.
with m.step():
    pair("brick", "1x2", x=0, y=WING_TOP, z=-6, color=STRIPE)
    for z in (-6, mirror_z(-6, 1)):
        m.slope("2x1", x=2, z=z, y=WING_TOP, color=STRIPE, facing="right")
with m.step():
    pair("brick", "1x1", x=0, y=WING_TOP + 3, z=-6, color=STRIPE)
    for z in (-6, mirror_z(-6, 1)):
        m.slope("2x1", x=1, z=z, y=WING_TOP + 3, color=STRIPE, facing="right")
