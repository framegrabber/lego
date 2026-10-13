"""Example: slopes facing all four directions, plus an inverted slope.

Two 2x4 slopes face front and back and lock the base plates; on a plate across their stud rows,
two 2x2 slopes face left and right; an inverted slope on top overhangs to the front.
"""

from lego.dsl import Model

m = Model("slopes")
with m.step():  # loose on the table; the slopes lock them
    m.plate("2x4", x=0, z=0, y=0, color="dark_bluish_grey", rot=90)  # x 0..1, z 0..3
    m.plate("2x4", x=2, z=0, y=0, color="dark_bluish_grey", rot=90)  # x 2..3, z 0..3
with m.step():
    m.slope("2x4", x=0, z=0, y=1, color="red", facing="front")  # studs on z=1
    m.slope("2x4", x=0, z=2, y=1, color="blue", facing="back")  # studs on z=2
with m.step():
    m.plate("2x4", x=0, z=1, y=4, color="light_bluish_grey")  # on both stud rows
with m.step():
    m.slope("2x2", x=0, z=1, y=5, color="yellow", facing="left")  # studs on x=1
    m.slope("2x2", x=2, z=1, y=5, color="green", facing="right")  # studs on x=2
with m.step():
    m.plate("1x2", x=1, z=1, y=8, color="white")  # on (1, 1) and (2, 1)
    m.inverted_slope("2x1", x=1, z=0, y=9, color="orange", facing="front")  # back row on (1, 1)
