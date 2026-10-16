"""A castle tower with battlements.

Plan: a 6x6 hollow stone tower (light grey, dark grey plinth) on an 8x8 green lawn. Brown door
on the front, black window slits on all four sides. Near the top, inverted slopes corbel the
walls out to 8x8, a dark grey floor plate layer caps it and crenellations (merlons with gaps)
run round the edge. A red flag on a pole flies from the roof.

Tower walls occupy x 1..6, z 1..6 (1 stud thick); the lawn and the battlements span x 0..7,
z 0..7.
"""

from lego.dsl import Model

m = Model("castle tower")

LAWN = "green"
STONE = "light_bluish_grey"
PLINTH = "dark_bluish_grey"
DOOR = "brown"
WINDOW = "black"
ROOF = "dark_bluish_grey"
FLAG = "red"

LO, HI = 1, 6  # wall ring min / max stud
WALL_LAYERS = 9  # brick courses; the course above them is the corbel ring of inverted slopes
DOOR_LAYERS = (1, 2)  # courses with the door (x 3..4 on the front)
WINDOW_LAYERS = (6, 7)  # courses with windows (centre two studs of every side)
MID = (3, 4)  # centre two studs of a side


def course_y(n):
    """Bottom level of brick course n (1-based), on top of the lawn plate."""
    return 1 + 3 * (n - 1)


def split(run):
    """Split a run length into brick lengths 4, 2, 1 (greedy)."""
    out = []
    while run:
        piece = 4 if run >= 4 else 2 if run >= 2 else 1
        out.append(piece)
        run -= piece
    return out


def sides(pattern):
    """The four wall segments of a course: (axis, fixed, start, end, reverse).

    Pattern A runs the front and back walls full width (corners), pattern B the left and right
    walls; alternating them interlocks the corners. Back and right walls fill from the far end
    so the short pieces sit at opposite corners (a pinwheel), staggering every seam.
    """
    if pattern == "A":
        return [
            ("x", LO, LO, HI, False),
            ("x", HI, LO, HI, True),
            ("z", LO, LO + 1, HI - 1, False),
            ("z", HI, LO + 1, HI - 1, True),
        ]
    return [
        ("z", LO, LO, HI, False),
        ("z", HI, LO, HI, True),
        ("x", LO, LO + 1, HI - 1, False),
        ("x", HI, LO + 1, HI - 1, True),
    ]


def course(n):
    """Brick specs (size, x, z, color, rot) for wall course n, with door and windows."""
    pattern = "B" if n % 2 else "A"
    specs = []
    for axis, fixed, start, end, reverse in sides(pattern):
        cells = list(range(start, end + 1))

        def colour(c):
            front = axis == "x" and fixed == LO
            if n in DOOR_LAYERS and front and c in MID:
                return DOOR
            if n in WINDOW_LAYERS and c in MID:
                return WINDOW
            return STONE if n > 1 else PLINTH

        # group consecutive cells of the same colour into runs
        runs = []
        for c in cells:
            if runs and runs[-1][0] == colour(c):
                runs[-1][1].append(c)
            else:
                runs.append((colour(c), [c]))
        for col, run in runs:
            pos = list(run)
            if reverse:
                pos.reverse()
            i = 0
            for length in split(len(pos)):
                chunk = pos[i : i + length]
                i += length
                lo = min(chunk)
                if axis == "x":
                    specs.append((f"1x{length}", lo, fixed, col, 0))
                else:
                    specs.append((f"1x{length}", fixed, lo, col, 90))
    return specs


def brick(spec, y):
    size, x, z, col, rot = spec
    m.brick(size, x=x, y=y, z=z, color=col, rot=rot)


def in_steps(items, place, size=6):
    for i in range(0, len(items), size):
        with m.step():
            for it in items[i : i + size]:
                place(it)


# --- Lawn: 8 plates (2x4) in rows z 0-1, 2-3, 4-5, 6-7 and columns x 0-3, 4-7 -------------
lawn = [(x, z) for z in (0, 2, 4, 6) for x in (0, 4)]
late_lawn = [(4, 2), (4, 4)]  # added in steps 2 and 3, under / beside the plinth bricks
first = course(1)
# Step 2 bricks: the ones that join every lawn plate of steps 1-2 into one piece.
locking = [
    s
    for s in first
    if (s[1], s[2], s[0])
    in {
        (LO, LO, "1x4"),  # left wall z 1..4: rows 0, 1, 2 (left)
        (HI, 3, "1x4"),  # right wall z 3..6: rows 1, (2), 3 (right)
        (HI, LO, "1x2"),  # right wall z 1..2: rows 0, 1 (right)
        (3, LO, "1x2"),  # door x 3..4: row 0 left + right
        (2, HI, "1x4"),  # back wall x 2..5: row 3 left + right
    }
]
rest = [s for s in first if s not in locking]
assert len(locking) == 5, locking

with m.step():  # lawn plates loose on the table
    for x, z in lawn:
        if (x, z) not in late_lawn:
            m.plate("2x4", x=x, z=z, y=0, color=LAWN)
with m.step():  # one more lawn plate; five plinth bricks lock the lawn together
    x, z = late_lawn[0]
    m.plate("2x4", x=x, z=z, y=0, color=LAWN)
    for s in locking:
        brick(s, course_y(1))
with m.step():  # last lawn plate pressed up under the right wall; finish the plinth
    x, z = late_lawn[1]
    m.plate("2x4", x=x, z=z, y=0, color=LAWN)
    for s in rest:
        brick(s, course_y(1))

# --- Walls, courses 2..WALL_LAYERS -----------------------------------------------------------
for n in range(2, WALL_LAYERS + 1):
    in_steps(course(n), lambda s, n=n: brick(s, course_y(n)))

# --- Corbel course: inverted slopes push the wall out one stud on every side -----------------
cy = course_y(WALL_LAYERS + 1)
corbels = [(x, 0, "front") for x in (1, 3, 5)] + [(x, 6, "back") for x in (1, 3, 5)]
corbels += [(0, z, "left") for z in (2, 4)] + [(6, z, "right") for z in (2, 4)]
in_steps(
    corbels,
    lambda c: m.inverted_slope("2x2", x=c[0], z=c[1], y=cy, color=STONE, facing=c[2]),
    size=5,
)

# --- Roof floor: 8x8 of plates, same layout as the lawn but rotated, over the corbels --------
ry = cy + 3
roof = [(x, z) for x in (0, 2, 4, 6) for z in (0, 4)]
in_steps(roof, lambda p: m.plate("2x4", x=p[0], z=p[1], y=ry, color=ROOF, rot=90), size=4)

# --- Battlements: 2x2 corner towers, 1x2 merlons mid-side, gaps between ------------------------
my = ry + 1
with m.step():
    for x in (0, 6):
        for z in (0, 6):
            m.brick("2x2", x=x, z=z, y=my, color=STONE)
with m.step():
    m.brick("1x2", x=3, z=0, y=my, color=STONE)
    m.brick("1x2", x=3, z=7, y=my, color=STONE)
    m.brick("1x2", x=0, z=3, y=my, color=STONE, rot=90)
    m.brick("1x2", x=7, z=3, y=my, color=STONE, rot=90)

# --- Flag pole in the middle of the roof, red flag on top -------------------------------------
with m.step():
    m.brick("1x1", x=3, z=3, y=my, color="dark_bluish_grey")
    m.brick("1x1", x=3, z=3, y=my + 3, color="dark_bluish_grey")
with m.step():
    m.brick("1x1", x=3, z=3, y=my + 6, color="dark_bluish_grey")
    m.brick("1x2", x=3, z=3, y=my + 9, color=FLAG)
