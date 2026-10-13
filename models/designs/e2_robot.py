"""A robot with arms and a head.

Boxy robot standing on two legs: interlocked hips, a 6x4 blue torso with chest lights,
shoulders that carry two hanging arms, a neck and a grey head with yellow eyes and two
red-tipped antennas. Robot faces front (-z); torso spans x 0..5, z 0..3.
"""

from lego.dsl import Model

m = Model("robot")

TORSO_W = 6
LEG_TOP = 10  # legs (foot plate + 3 bricks) end here
HIP_Y = LEG_TOP  # two plate layers: 10, 11
TORSO_Y = HIP_Y + 2  # four brick layers: 12, 15, 18, 21
SHOULDER_Y = TORSO_Y + 4 * 3  # 24
HEAD_Y = SHOULDER_Y + 3  # on top of the neck brick

BODY = "blue"
DARK = "dark_bluish_grey"
LIGHT = "light_bluish_grey"

# --- legs: foot plate sticks out one stud in front and behind --------------------------
leg = m.subassembly("leg")
with leg.step():
    leg.plate("2x4", x=0, z=-1, y=0, color="black", rot=90)
    leg.brick("2x2", x=0, z=0, y=1, color=DARK)
with leg.step():
    leg.brick("2x2", x=0, z=0, y=4, color=DARK)
    leg.brick("2x2", x=0, z=0, y=7, color=LIGHT)

# --- arms: hand at the bottom, built upward; hung under a shoulder ---------------------
arm = m.subassembly("arm")
with arm.step():
    arm.brick("2x2", x=0, z=0, y=0, color="black")  # hand
    arm.brick("2x2", x=0, z=0, y=3, color=LIGHT)
with arm.step():
    arm.brick("2x2", x=0, z=0, y=6, color=LIGHT)
    arm.brick("2x2", x=0, z=0, y=9, color=DARK)  # shoulder joint


def torso_layer_p(y):
    """Three 2x4 bricks running front-to-back."""
    for x in (0, 2, 4):
        m.brick("2x4", x=x, z=0, y=y, color=BODY, rot=90)


def torso_layer_q(y):
    """Two 2x4 bricks running left-right, flanked by 1x4 side bricks (seams offset from P)."""
    m.brick("1x4", x=0, z=0, y=y, color=BODY, rot=90)
    m.brick("1x4", x=TORSO_W - 1, z=0, y=y, color=BODY, rot=90)
    m.brick("2x4", x=1, z=0, y=y, color=BODY)
    m.brick("2x4", x=1, z=2, y=y, color=BODY)


# Step 1: hips — three plates front-to-back, locked by two plates across all three.
with m.step():
    for x in (0, 2, 4):
        m.plate("2x4", x=x, z=0, y=HIP_Y, color=DARK, rot=90)
    m.plate("2x4", x=1, z=0, y=HIP_Y + 1, color=DARK)
    m.plate("2x4", x=1, z=2, y=HIP_Y + 1, color=DARK)

# Step 2: legs under the hips, fill the hip edges.
with m.step():
    m.attach(leg, x=0, y=0, z=1)
    m.attach(leg, x=TORSO_W - 2, y=0, z=1)
    m.plate("1x4", x=0, z=0, y=HIP_Y + 1, color=DARK, rot=90)
    m.plate("1x4", x=TORSO_W - 1, z=0, y=HIP_Y + 1, color=DARK, rot=90)

# Torso layer 1.
with m.step():
    torso_layer_p(TORSO_Y)

# Torso layer 2: chest panel with lights in the front row.
with m.step():
    y = TORSO_Y + 3
    m.brick("1x4", x=0, z=0, y=y, color=BODY, rot=90)
    m.brick("1x4", x=TORSO_W - 1, z=0, y=y, color=BODY, rot=90)
    m.brick("2x4", x=1, z=2, y=y, color=BODY)
    m.brick("1x4", x=1, z=1, y=y, color=BODY)
with m.step():
    for x, color in ((1, "white"), (2, "red"), (3, "yellow"), (4, "white")):
        m.brick("1x1", x=x, z=0, y=TORSO_Y + 3, color=color)

# Torso layers 3 and 4.
with m.step():
    torso_layer_p(TORSO_Y + 6)
with m.step():
    torso_layer_q(TORSO_Y + 9)

# Shoulders stick out two studs on each side; neck in the middle.
with m.step():
    m.plate("2x4", x=-2, z=1, y=SHOULDER_Y, color=DARK)
    m.plate("2x4", x=TORSO_W - 2, z=1, y=SHOULDER_Y, color=DARK)
    m.brick("2x2", x=2, z=1, y=SHOULDER_Y, color=DARK)

# Arms hang under the shoulders.
with m.step():
    m.attach(arm, x=-2, y=SHOULDER_Y - 12, z=1)
    m.attach(arm, x=TORSO_W, y=SHOULDER_Y - 12, z=1)

# Head: chin brick, then eye row (yellow eyes in the front corners).
with m.step():
    m.brick("2x4", x=1, z=1, y=HEAD_Y, color=LIGHT)
    m.brick("1x4", x=1, z=2, y=HEAD_Y + 3, color=LIGHT)
    m.brick("1x1", x=1, z=1, y=HEAD_Y + 3, color="yellow")
    m.brick("1x2", x=2, z=1, y=HEAD_Y + 3, color=LIGHT)
    m.brick("1x1", x=4, z=1, y=HEAD_Y + 3, color="yellow")

# Head top and two antennas.
with m.step():
    m.plate("2x4", x=1, z=1, y=HEAD_Y + 6, color=LIGHT)
    for x in (1, 4):
        m.brick("1x1", x=x, z=1, y=HEAD_Y + 7, color=DARK)
        m.plate("1x1", x=x, z=1, y=HEAD_Y + 10, color="red")
