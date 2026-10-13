"""Broken on purpose (B4): the step-2 brick floats until a step-3 plate joins it to the base."""

from lego.dsl import Model

m = Model("future support")
with m.step():
    m.brick("2x4", x=0, z=0, y=0, color="red")  # x 0..3, top at level 3
with m.step():
    m.brick("2x2", x=4, z=0, y=4, color="blue")  # nothing under it yet
with m.step():
    m.plate("2x4", x=2, z=0, y=3, color="yellow")  # on the red brick, under the blue one
