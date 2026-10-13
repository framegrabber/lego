"""A standing robot: two legs on big feet, a boxy torso with a chest light,
arms hanging at its sides from the shoulders, and a head with a visor,
ears and an antenna.

Front of the robot faces low z. Body spans x 0..5, z 0..3; arms at x -2..-1 and 6..7.
"""

from lego.dsl import Model

m = Model("robot")

BODY = "blue"
LIMB = "light_bluish_grey"
JOINT = "dark_bluish_grey"
FOOT = "black"
ACCENT = "red"

LEG_X = (0, 4)          # left and right leg min-x
ARM_X = (-2, 6)         # left and right arm min-x
LIMB_Z = 1              # legs, arms and neck are 2x2 at z 1..2

# The two legs can't be built side by side: they would stay two loose towers until
# the hips join them. Build the left leg up, lay the hips across both leg positions,
# then hang the right leg underneath the hips, top to bottom.
L, R = LEG_X

# --- Left foot and leg (y 0..13) -------------------------------------------------
with m.step():
    m.plate("2x4", x=L, y=0, z=-1, color=JOINT, rot=90)
    m.brick("2x4", x=L, y=1, z=-1, color=FOOT, rot=90)
with m.step():
    m.brick("2x2", x=L, y=4, z=LIMB_Z, color=LIMB)
    m.brick("2x2", x=L, y=7, z=LIMB_Z, color=LIMB)
with m.step():
    m.plate("2x2", x=L, y=10, z=LIMB_Z, color=JOINT)       # knee
    m.brick("2x2", x=L, y=11, z=LIMB_Z, color=LIMB)

# --- Hips (y 14): a 2x4 reaches from the left leg over the right leg's top stud --
with m.step():
    m.plate("2x4", x=1, y=14, z=LIMB_Z, color=JOINT)
    m.plate("1x2", x=0, y=14, z=LIMB_Z, color=JOINT, rot=90)

# --- Right leg hangs under the hips (y 13 down to 0) -----------------------------
with m.step():
    m.brick("2x2", x=R, y=11, z=LIMB_Z, color=LIMB)
    m.plate("1x2", x=5, y=14, z=LIMB_Z, color=JOINT, rot=90)
    m.plate("2x2", x=R, y=10, z=LIMB_Z, color=JOINT)       # knee
with m.step():
    m.brick("2x2", x=R, y=7, z=LIMB_Z, color=LIMB)
    m.brick("2x2", x=R, y=4, z=LIMB_Z, color=LIMB)
with m.step():
    m.brick("2x4", x=R, y=1, z=-1, color=FOOT, rot=90)
    m.plate("2x4", x=R, y=0, z=-1, color=JOINT, rot=90)

# --- Torso (y 15..23), three brick layers with alternating joints ------------
with m.step():
    for x in (0, 2, 4):
        m.brick("2x4", x=x, y=15, z=0, color=BODY, rot=90)
with m.step():
    m.brick("2x2", x=0, y=18, z=0, color=BODY)
    m.brick("2x2", x=2, y=18, z=0, color="yellow")      # chest light
    m.brick("2x2", x=4, y=18, z=0, color=BODY)
    m.brick("2x2", x=0, y=18, z=2, color=BODY)
    m.brick("2x4", x=2, y=18, z=2, color=BODY)        # ties middle and right columns
with m.step():
    for x in (0, 2, 4):
        m.brick("2x4", x=x, y=21, z=0, color=BODY, rot=90)

# --- Shoulders (y 24) --------------------------------------------------------
with m.step():
    m.plate("2x4", x=ARM_X[0], y=24, z=LIMB_Z, color=ACCENT)
    m.plate("2x2", x=2, y=24, z=LIMB_Z, color=JOINT)
    m.plate("2x4", x=4, y=24, z=LIMB_Z, color=ACCENT)

# --- Arms hang under the shoulders (y 15..23), forearms bent forward ---------
for x in ARM_X:
    with m.step():
        m.brick("2x2", x=x, y=21, z=LIMB_Z, color=ACCENT)    # upper arm
        m.brick("2x2", x=x, y=18, z=LIMB_Z, color=LIMB)
        m.brick("2x4", x=x, y=15, z=-1, color=LIMB, rot=90)  # forearm points forward
        m.brick("1x2", x=x, y=18, z=-1, color=JOINT)         # fist on the forearm tip

# --- Neck and head (y 25..37) ------------------------------------------------
with m.step():
    m.brick("2x2", x=2, y=25, z=LIMB_Z, color=JOINT)          # neck
with m.step():
    m.brick("2x4", x=1, y=28, z=0, color=LIMB, rot=90)
    m.brick("2x4", x=3, y=28, z=0, color=LIMB, rot=90)
with m.step():
    m.brick("1x4", x=1, y=31, z=0, color="medium_azure")     # visor
    m.brick("2x4", x=1, y=31, z=1, color=LIMB)
    m.brick("1x4", x=1, y=31, z=3, color=LIMB)
with m.step():
    m.plate("2x4", x=0, y=34, z=1, color=LIMB)
    m.plate("2x2", x=4, y=34, z=1, color=LIMB)
    m.plate("1x4", x=1, y=34, z=0, color=LIMB)
    m.plate("1x4", x=1, y=34, z=3, color=LIMB)
    for x in (0, 5):                                         # ears hang under the top plate
        m.brick("1x2", x=x, y=31, z=1, color=ACCENT, rot=90)

# --- Antenna (y 35..38) ------------------------------------------------------
with m.step():
    m.brick("1x1", x=2, y=35, z=1, color=JOINT)
    m.plate("1x1", x=2, y=38, z=1, color=ACCENT)
