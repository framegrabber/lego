"""A tree with a brown trunk and green leaves.

Grass base 8 (x) by 6 (z), a 2x2 brown trunk four bricks tall with roots, and a round leafy
crown built as a sub-assembly (4 -> 6 -> 8 -> 8 wide, a sloped 8 -> 6 layer, a 4-wide ridge
and a 2x2 cap) with red apples tucked into the corner notches. The crown attaches onto the
trunk top in one step.
"""

from lego.dsl import Model

m = Model("tree")

LEAF = "green"
GRASS = "green"
WOOD = "brown"
TRUNK_X, TRUNK_Z = 3, 2          # min corner of the 2x2 trunk (centre of the 8x6 base)
TRUNK_BRICKS = 4
CROWN_Y = 2 + 3 * TRUNK_BRICKS   # roots plate top is y=2

# ---- crown sub-assembly: local (0, 0) is the trunk's min corner, crown spans -3..5 ----
crown = m.subassembly("crown")
with crown.step():  # 4x4 plate under the crown, tied by the first leaf bricks
    crown.plate("2x4", x=-1, z=-1, y=0, color=LEAF)
    crown.plate("2x4", x=-1, z=1, y=0, color=LEAF)
    crown.brick("2x4", x=-2, z=-2, y=1, color=LEAF, rot=90)
    crown.brick("2x2", x=0, z=0, y=1, color=LEAF)
with crown.step():  # rest of the 6x6 pinwheel layer
    crown.brick("2x4", x=0, z=-2, y=1, color=LEAF)
    crown.brick("2x4", x=2, z=0, y=1, color=LEAF, rot=90)
    crown.brick("2x4", x=-2, z=2, y=1, color=LEAF)
with crown.step():  # 8-wide plus layer: centre and side arms
    crown.brick("2x4", x=-1, z=-1, y=4, color=LEAF, rot=90)
    crown.brick("2x4", x=1, z=-1, y=4, color=LEAF, rot=90)
    crown.brick("2x4", x=-3, z=-1, y=4, color=LEAF, rot=90)
    crown.brick("2x4", x=3, z=-1, y=4, color=LEAF, rot=90)
with crown.step():  # front/back arms and apples in the corner notches
    crown.brick("2x4", x=-1, z=-3, y=4, color=LEAF)
    crown.brick("2x4", x=-1, z=3, y=4, color=LEAF)
    for ax, az in [(-2, -2), (3, -2), (-2, 3), (3, 3)]:
        crown.brick("1x1", x=ax, z=az, y=4, color="red")
with crown.step():  # second 8-wide plus layer, centre seam turned the other way
    crown.brick("2x4", x=-1, z=-1, y=7, color=LEAF)
    crown.brick("2x4", x=-1, z=1, y=7, color=LEAF)
    crown.brick("2x4", x=-3, z=-1, y=7, color=LEAF, rot=90)
    crown.brick("2x4", x=3, z=-1, y=7, color=LEAF, rot=90)
    crown.brick("2x4", x=-1, z=-3, y=7, color=LEAF)
    crown.brick("2x4", x=-1, z=3, y=7, color=LEAF)
with crown.step():  # rounded layer: slopes on the arms, bricks in the middle
    crown.brick("2x4", x=-1, z=-1, y=10, color=LEAF, rot=90)
    crown.brick("2x4", x=1, z=-1, y=10, color=LEAF, rot=90)
    crown.slope("2x4", x=-3, z=-1, y=10, color=LEAF, facing="left")
    crown.slope("2x4", x=3, z=-1, y=10, color=LEAF, facing="right")
    crown.slope("2x4", x=-1, z=-3, y=10, color=LEAF, facing="front")
    crown.slope("2x4", x=-1, z=3, y=10, color=LEAF, facing="back")
with crown.step():  # top: a ridge of two slopes, capped by a plate
    crown.slope("2x4", x=-1, z=-1, y=13, color=LEAF, facing="front")
    crown.slope("2x4", x=-1, z=1, y=13, color=LEAF, facing="back")
    crown.plate("2x2", x=0, z=0, y=16, color=LEAF)

# ---- main model ----
with m.step():  # grass base: three rows of two 2x4 plates
    for z in (0, 2, 4):
        for x in (0, 4):
            m.plate("2x4", x=x, z=z, y=0, color=GRASS)

with m.step():  # roots across every base plate, first trunk brick
    m.plate("2x4", x=TRUNK_X, z=TRUNK_Z - 1, y=1, color=WOOD, rot=90)
    m.plate("1x2", x=TRUNK_X - 2, z=TRUNK_Z, y=1, color=WOOD)
    m.plate("1x2", x=TRUNK_X + 2, z=TRUNK_Z + 1, y=1, color=WOOD)
    m.brick("2x2", x=TRUNK_X, z=TRUNK_Z, y=2, color=WOOD)

with m.step():  # trunk grows, grass tufts
    m.brick("2x2", x=TRUNK_X, z=TRUNK_Z, y=5, color=WOOD)
    m.brick("2x2", x=TRUNK_X, z=TRUNK_Z, y=8, color=WOOD)
    m.plate("1x2", x=0, z=5, y=1, color="lime")
    m.plate("1x2", x=6, z=0, y=1, color="lime")

with m.step():  # top of trunk, two flowers
    m.brick("2x2", x=TRUNK_X, z=TRUNK_Z, y=11, color=WOOD)
    for fx, fz, petal in [(1, 0, "red"), (6, 5, "yellow")]:
        m.brick("1x1", x=fx, z=fz, y=1, color="lime")
        m.plate("1x1", x=fx, z=fz, y=4, color=petal)

with m.step():
    m.attach(crown, x=TRUNK_X, y=CROWN_Y, z=TRUNK_Z)
