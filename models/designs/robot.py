"""A standing robot: two legs on big feet, a boxy torso with a chest light,
arms hanging at its sides from the shoulders, and a head with a visor,
ears and an antenna.

Front of the robot faces low z. Body spans x 0..5, z 0..3; arms at x -2..-1 and 6..7.
Legs and arms are sub-assemblies: each is built bottom-up on its own, then both copies
are pressed on under the hips / shoulders in one step.
"""

from lego.dsl import Model

m = Model("robot")

BODY = "blue"
LIMB = "light_bluish_grey"
JOINT = "dark_bluish_grey"
FOOT = "black"
ACCENT = "red"

LEG_X = (0, 4)  # left and right leg min-x
ARM_X = (-2, 6)  # left and right arm min-x
LIMB_Z = 1  # legs, arms and neck are 2x2 at z 1..2
HIP_Y = 14  # legs end under the hip plates
ARM_Y = 15  # arms hang from the shoulder plates (y 24) down to the hips' top

# --- Leg sub-assembly, built bottom-up (y 0..13): foot, shin, knee, thigh ---------
leg = m.subassembly("leg")
with leg.step():
    leg.plate("2x4", x=0, y=0, z=-1, color=JOINT, rot=90)  # sole sticks out in front
    leg.brick("2x4", x=0, y=1, z=-1, color=FOOT, rot=90)
with leg.step():
    leg.brick("2x2", x=0, y=4, z=LIMB_Z, color=LIMB)
    leg.brick("2x2", x=0, y=7, z=LIMB_Z, color=LIMB)
with leg.step():
    leg.plate("2x2", x=0, y=10, z=LIMB_Z, color=JOINT)  # knee
    leg.brick("2x2", x=0, y=11, z=LIMB_Z, color=LIMB)

# --- Arm sub-assembly, built bottom-up (y 0..8): forearm points forward ------------
arm = m.subassembly("arm")
with arm.step():
    arm.brick("2x4", x=0, y=0, z=-1, color=LIMB, rot=90)  # forearm
    arm.brick("1x2", x=0, y=3, z=-1, color=JOINT)  # fist on the forearm tip
    arm.brick("2x2", x=0, y=3, z=LIMB_Z, color=LIMB)
with arm.step():
    arm.brick("2x2", x=0, y=6, z=LIMB_Z, color=ACCENT)  # upper arm

# --- Torso bottom layer with the hip plates pressed on underneath (y 14..17) -------
with m.step():
    for x in (0, 2, 4):
        m.brick("2x4", x=x, y=15, z=0, color=BODY, rot=90)
    m.plate("2x4", x=1, y=HIP_Y, z=LIMB_Z, color=JOINT)  # ties the three bricks

# --- Legs plug in under the hips ---------------------------------------------------
with m.step():
    m.plate("1x2", x=0, y=HIP_Y, z=LIMB_Z, color=JOINT, rot=90)
    m.plate("1x2", x=5, y=HIP_Y, z=LIMB_Z, color=JOINT, rot=90)
    for x in LEG_X:
        m.attach(leg, x=x, y=0, z=0)

# --- Torso upper layers (y 18..23), joints alternating with the bottom layer -------
with m.step():
    m.brick("2x2", x=0, y=18, z=0, color=BODY)
    m.brick("2x2", x=2, y=18, z=0, color="yellow")  # chest light
    m.brick("2x2", x=4, y=18, z=0, color=BODY)
    m.brick("2x2", x=0, y=18, z=2, color=BODY)
    m.brick("2x4", x=2, y=18, z=2, color=BODY)  # ties middle and right columns
with m.step():
    for x in (0, 2, 4):
        m.brick("2x4", x=x, y=21, z=0, color=BODY, rot=90)

# --- Shoulders (y 24) --------------------------------------------------------
with m.step():
    m.plate("2x4", x=ARM_X[0], y=24, z=LIMB_Z, color=ACCENT)
    m.plate("2x2", x=2, y=24, z=LIMB_Z, color=JOINT)
    m.plate("2x4", x=4, y=24, z=LIMB_Z, color=ACCENT)

# --- Arms press on under the shoulders ---------------------------------------------
with m.step():
    for x in ARM_X:
        m.attach(arm, x=x, y=ARM_Y, z=0)

# --- Neck and head (y 25..37) ------------------------------------------------
with m.step():
    m.brick("2x2", x=2, y=25, z=LIMB_Z, color=JOINT)  # neck
with m.step():
    m.brick("2x4", x=1, y=28, z=0, color=LIMB, rot=90)
    m.brick("2x4", x=3, y=28, z=0, color=LIMB, rot=90)
with m.step():
    m.brick("1x4", x=1, y=31, z=0, color="medium_azure")  # visor
    m.brick("2x4", x=1, y=31, z=1, color=LIMB)
    m.brick("1x4", x=1, y=31, z=3, color=LIMB)
with m.step():
    m.plate("2x4", x=0, y=34, z=1, color=LIMB)
    m.plate("2x2", x=4, y=34, z=1, color=LIMB)
    m.plate("1x4", x=1, y=34, z=0, color=LIMB)
    m.plate("1x4", x=1, y=34, z=3, color=LIMB)
    for x in (0, 5):  # ears hang under the top plate
        m.brick("1x2", x=x, y=31, z=1, color=ACCENT, rot=90)

# --- Antenna (y 35..38) ------------------------------------------------------
with m.step():
    m.brick("1x1", x=2, y=35, z=1, color=JOINT)
    m.plate("1x1", x=2, y=38, z=1, color=ACCENT)
