"""Example: a 3-layer running-bond wall on a plate base, one layer per step."""

from lego.dsl import Model

LENGTH = 8  # studs
m = Model("wall")

with m.step():
    m.plate("2x4", x=0, z=0, y=0, color="dark_bluish_grey")
    m.plate("2x4", x=4, z=0, y=0, color="dark_bluish_grey")

for layer in range(3):
    y = 1 + layer * 3
    color = ("red", "white")[layer % 2]
    with m.step():
        if layer % 2 == 0:
            m.brick("1x4", x=0, z=0, y=y, color=color)
            m.brick("1x4", x=4, z=0, y=y, color=color)
        else:
            # Offset by half a brick so joints are covered (running bond).
            m.brick("1x2", x=0, z=0, y=y, color=color)
            m.brick("1x4", x=2, z=0, y=y, color=color)
            m.brick("1x2", x=6, z=0, y=y, color=color)
