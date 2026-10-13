"""Broken on purpose (B3): a brick hangs in the air above the base."""

from lego.dsl import Model

m = Model("floating")
with m.step():
    m.brick("2x4", x=0, z=0, y=0, color="red")
    m.brick("2x2", x=1, z=0, y=3, color="yellow")
with m.step():
    m.brick("1x2", x=0, z=0, y=9, color="blue")  # nothing at levels 6..8 below it
