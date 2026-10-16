"""A rocket standing on a launch pad.

Layers (bottom up):
- 12x8 launch pad: dark grey plates under light grey plates with crossed joints, yellow markers.
- Rocket (4x4, centred on x 2..5, z 2..5): red fins on all four sides at the base, white body
  with two red stripes and a blue window, red pointed nose of stacked slopes.
- Orange launch tower (2x2) at the right with a yellow arm reaching toward the rocket.
"""

from lego.dsl import Model

m = Model("rocket")

PAD_LOW = "dark_bluish_grey"
PAD_TOP = "light_bluish_grey"
BODY = "white"
STRIPE = "red"
TOWER = "orange"

BX, BZ = 2, 2  # rocket body min corner (4x4)
TX, TZ = 8, 3  # tower min corner (2x2), right next to the right fin
PAD_Y = 2  # top of the pad

# --- launch pad ----------------------------------------------------------------
# Bottom: 2x4 plates in 3 columns (x 0, 4, 8) and 4 rows (z 0, 2, 4, 6).
# Top: 2x4 plates shifted by 2 in x and 1 in z so each crosses four bottom plates.


def low(x, z):
    m.plate("2x4", x=x, y=0, z=z, color=PAD_LOW)


def top(x, z, size="2x4", rot=0):
    m.plate(size, x=x, y=1, z=z, color=PAD_TOP, rot=rot)


with m.step():  # front two rows, loose on the table
    for z in (0, 2):
        for x in (0, 4, 8):
            low(x, z)

with m.step():  # lock them together
    top(2, 1)
    top(6, 1)

for z in (4, 6):  # next row underneath + its locking plates on top
    with m.step():
        for x in (0, 4, 8):
            low(x, z)
        top(2, z - 1)
        top(6, z - 1)

with m.step():  # left and right edges of the top layer
    for x in (0, 10):
        for z in (0, 4):
            top(x, z, rot=90)

with m.step():  # front and back edges of the top layer
    for z in (0, 7):
        for x in (2, 6):
            top(x, z, size="1x4")

with m.step():  # yellow markers in the corners
    for x in (0, 10):
        for z in (0, 7):
            m.plate("1x2", x=x, y=PAD_Y, z=z, color="yellow")


# --- rocket body ---------------------------------------------------------------
def body_layer(y, i, color=BODY):
    """4x4 layer of two 2x4 bricks; joints alternate direction every layer."""
    if i % 2 == 0:
        for x in (BX, BX + 2):
            m.brick("2x4", x=x, y=y, z=BZ, color=color, rot=90)
    else:
        for z in (BZ, BZ + 2):
            m.brick("2x4", x=BX, y=y, z=z, color=color)


def window_layer(y):
    """Like an odd body layer, but the front row has a blue window in the middle."""
    m.brick("1x1", x=BX, y=y, z=BZ, color=BODY)
    m.brick("1x2", x=BX + 1, y=y, z=BZ, color="trans_light_blue")
    m.brick("1x1", x=BX + 3, y=y, z=BZ, color=BODY)
    m.brick("1x4", x=BX, y=y, z=BZ + 1, color=BODY)
    m.brick("2x4", x=BX, y=y, z=BZ + 2, color=BODY)


FIN_Y = PAD_Y
FINS = {  # facing: (x, z) of the 2x2 fin brick and slope
    "left": (BX - 2, BZ + 1),
    "right": (BX + 4, BZ + 1),
    "front": (BX + 1, BZ - 2),
    "back": (BX + 1, BZ + 4),
}


def fin_brick(facing):
    x, z = FINS[facing]
    m.brick("2x2", x=x, y=FIN_Y, z=z, color=STRIPE)


def fin_slope(facing):
    x, z = FINS[facing]
    m.slope("2x2", x=x, y=FIN_Y + 3, z=z, color=STRIPE, facing=facing)


y = PAD_Y
with m.step():
    body_layer(y, 0)
    fin_brick("left")
    fin_brick("right")

with m.step():
    fin_brick("front")
    fin_brick("back")
    fin_slope("left")
    fin_slope("right")

with m.step():
    body_layer(y + 3, 1)
    fin_slope("front")
    fin_slope("back")
y += 6

# body layers above the fins
LAYERS = [STRIPE, BODY, BODY, "window", BODY, BODY, STRIPE, BODY]
i = 2
for group in ([0, 1], [2], [3], [4, 5], [6, 7]):
    with m.step():
        for k in group:
            kind = LAYERS[k]
            if kind == "window":
                window_layer(y)
            else:
                body_layer(y, i, color=kind)
            y += 3
            i += 1

# --- nose cone ------------------------------------------------------------------
with m.step():  # front/back slopes, studs on the middle two rows
    for x in (BX, BX + 2):
        m.slope("2x2", x=x, y=y, z=BZ, color=STRIPE, facing="front")
        m.slope("2x2", x=x, y=y, z=BZ + 2, color=STRIPE, facing="back")
y += 3

with m.step():  # left/right slopes on the middle rows, then the tip
    m.slope("2x2", x=BX, y=y, z=BZ + 1, color=STRIPE, facing="left")
    m.slope("2x2", x=BX + 2, y=y, z=BZ + 1, color=STRIPE, facing="right")
    m.plate("2x2", x=BX + 1, y=y + 3, z=BZ + 1, color=STRIPE)


# --- launch tower -----------------------------------------------------------------
ty = PAD_Y
TOWER_LAYERS = 8
with m.step():
    for k in range(4):
        m.brick("2x2", x=TX, y=ty, z=TZ, color=TOWER if k % 2 == 0 else "light_bluish_grey")
        ty += 3

with m.step():
    for k in range(4, TOWER_LAYERS):
        m.brick("2x2", x=TX, y=ty, z=TZ, color=TOWER if k % 2 == 0 else "light_bluish_grey")
        ty += 3

with m.step():  # arm toward the rocket, cap and warning light
    m.plate("2x4", x=TX - 2, y=ty, z=TZ, color="yellow")
    m.plate("2x2", x=TX, y=ty + 1, z=TZ, color=TOWER)
    m.plate("1x1", x=TX, y=ty + 2, z=TZ, color="trans_red")
