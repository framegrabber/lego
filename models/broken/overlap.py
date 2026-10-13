"""Broken on purpose (B2): the second brick overlaps the first by two studs."""

from lego.dsl import Model

m = Model("overlap")
with m.step():
    m.brick("2x4", x=0, z=0, y=0, color="red")
    m.brick("2x4", x=2, z=0, y=0, color="blue")
