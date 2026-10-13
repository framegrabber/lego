"""A dog sitting down, seen in profile: it faces -x (left in the front view).

White-socked front legs stand straight at x 0..1 on paws that stick forward. The haunches sit on
the ground behind them (x 2..7) and the back rises from the rump to the shoulders in slope steps,
with a tail poking out at the back. Above: a white chest, a red collar, a neck, then a head with a
snout that juts forward, a black nose, black eyes and long floppy brown ears.

Width: z 0..5 (legs at z 0..1 and z 4..5); torso and head z 1..4.
"""

from lego.dsl import Model

m = Model("dog")

FUR = "tan"
WHITE = "white"
EAR = "brown"
DARK = "black"
COLLAR = "red"

BASE_Y = 0
L1 = 1    # haunch, front legs
L2 = 4    # haunch, front legs, rump + tail
L3 = 7    # shoulders, thighs
L4 = 10   # chest and back
COLLAR_Y = 13
NECK_Y = 14
HEAD1 = 17  # muzzle row, x -2..3
HEAD2 = 20  # eyes row, x -2..3 (nose on the muzzle)
HEAD_TOP = 23

# --- Ground layer: front paws (stick forward) and haunch bottom ------------------------
with m.step():
    m.plate("2x4", x=-1, z=0, y=BASE_Y, color=WHITE)           # front paw, x -1..2
    m.plate("2x4", x=-1, z=4, y=BASE_Y, color=WHITE)
    m.plate("2x4", x=4, z=0, y=BASE_Y, color=FUR)              # hind foot, x 4..7
    m.plate("2x4", x=4, z=4, y=BASE_Y, color=FUR)
    m.plate("2x4", x=4, z=2, y=BASE_Y, color=FUR)
    m.plate("2x2", x=2, z=2, y=BASE_Y, color=FUR)

# --- Haunches, first brick layer: locks the ground plates ------------------------------
with m.step():
    m.brick("2x4", x=2, z=0, y=L1, color=FUR)                  # x 2..5
    m.brick("2x4", x=2, z=4, y=L1, color=FUR)
    m.brick("2x4", x=2, z=2, y=L1, color=FUR)
    m.brick("2x4", x=6, z=1, y=L1, color=FUR, rot=90)          # x 6..7, z 1..4
with m.step():
    m.brick("1x2", x=6, z=0, y=L1, color=FUR)
    m.brick("1x2", x=6, z=5, y=L1, color=FUR)
    m.brick("2x2", x=0, z=0, y=L1, color=WHITE)                # front leg
    m.brick("2x2", x=0, z=4, y=L1, color=WHITE)

# --- Second layer: legs, haunch, rounded rump with the tail between the slopes ----------
with m.step():
    m.brick("2x2", x=0, z=0, y=L2, color=WHITE)
    m.brick("2x2", x=0, z=4, y=L2, color=WHITE)
    m.brick("2x4", x=2, z=0, y=L2, color=FUR, rot=90)          # x 2..3, z 0..3
    m.brick("2x2", x=2, z=4, y=L2, color=FUR)
    m.brick("2x4", x=4, z=2, y=L2, color=FUR, rot=90)          # x 4..5, z 2..5
    m.brick("2x2", x=4, z=0, y=L2, color=FUR)
with m.step():
    m.slope("2x2", x=6, z=0, y=L2, color=FUR, facing="right")  # rump, z 0..1
    m.brick("1x4", x=6, z=2, y=L2, color=FUR)                  # tail, x 6..9
    m.slope("2x1", x=6, z=3, y=L2, color=FUR, facing="right")
    m.slope("2x2", x=6, z=4, y=L2, color=FUR, facing="right")

# --- Third layer: shoulders tie the legs to the body; thighs slope down to the rump ----
with m.step():
    m.brick("2x4", x=0, z=0, y=L3, color=FUR)                  # shoulder, x 0..3
    m.brick("2x4", x=0, z=4, y=L3, color=FUR)
    m.brick("2x2", x=2, z=2, y=L3, color=FUR)
    m.slope("2x4", x=4, z=0, y=L3, color=FUR, facing="right")  # thigh, z 0..3
    m.slope("2x2", x=4, z=4, y=L3, color=FUR, facing="right")

# --- Chest and back; the white chest between the shoulders hangs under the chest brick --
with m.step():
    m.brick("2x2", x=0, z=2, y=L3, color=WHITE)                # between the legs
    m.brick("2x4", x=0, z=1, y=L4, color=WHITE, rot=90)        # chest, z 1..4
    m.brick("2x4", x=2, z=1, y=L4, color=FUR, rot=90)
    m.slope("2x4", x=4, z=1, y=L4, color=FUR, facing="right")  # back, x 4..5

# --- Collar (crosses the x=2 seam) and neck ----------------------------------------------
with m.step():
    m.plate("2x4", x=0, z=1, y=COLLAR_Y, color=COLLAR)         # x 0..3, z 1..2
    m.plate("2x4", x=0, z=3, y=COLLAR_Y, color=COLLAR)
    m.brick("2x4", x=0, z=1, y=NECK_Y, color=WHITE, rot=90)    # throat
    m.slope("2x4", x=2, z=1, y=NECK_Y, color=FUR, facing="right")  # nape

# --- Head: a 2-wide muzzle juts forward to x -2, cheeks beside it -----------------------
with m.step():
    m.brick("2x4", x=-2, z=2, y=HEAD1, color=FUR)              # muzzle, x -2..1, z 2..3
    m.brick("1x2", x=0, z=1, y=HEAD1, color=FUR)               # cheek
    m.brick("1x2", x=0, z=4, y=HEAD1, color=FUR)               # cheek
    m.brick("2x4", x=2, z=1, y=HEAD1, color=FUR, rot=90)       # back of head
with m.step():                                                 # forehead row, x 0..3
    m.brick("1x1", x=0, z=1, y=HEAD2, color=DARK)              # eye
    m.brick("1x1", x=0, z=4, y=HEAD2, color=DARK)              # eye
    m.brick("1x2", x=0, z=2, y=HEAD2, color=FUR, rot=90)
    m.brick("2x4", x=1, z=1, y=HEAD2, color=FUR, rot=90)       # x 1..2, crosses the seam
    m.brick("1x4", x=3, z=1, y=HEAD2, color=FUR, rot=90)
    m.plate("1x2", x=-2, z=2, y=HEAD2, color=DARK, rot=90)     # nose on the muzzle tip

# --- Top of head and long floppy ears hanging from the ear plates -----------------------
with m.step():
    m.plate("2x4", x=0, z=1, y=HEAD_TOP, color=FUR, rot=90)    # x 0..1
    m.plate("2x2", x=2, z=2, y=HEAD_TOP, color=FUR)
    m.plate("2x2", x=2, z=0, y=HEAD_TOP, color=EAR)            # ear top, overhangs z 0
    m.plate("2x2", x=2, z=4, y=HEAD_TOP, color=EAR)            # overhangs z 5
with m.step():
    m.brick("1x2", x=2, z=0, y=HEAD2, color=EAR)               # ear, under the ear plate
    m.brick("1x2", x=2, z=5, y=HEAD2, color=EAR)
    m.brick("1x2", x=2, z=0, y=HEAD1, color=EAR)               # ear tip
    m.brick("1x2", x=2, z=5, y=HEAD1, color=EAR)
