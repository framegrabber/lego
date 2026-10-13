"""Broken on purpose (B3): the first draft of the spec example.

Unrotated 2x4 parts are 2 studs deep in z, so the plates at z=0 and z=4 leave a gap and the
brick at z=2 lands on nothing.
"""

from lego.dsl import Model

m = Model("gap")
with m.step():
    m.plate("2x4", x=0, z=0, y=0, color="black")
    m.plate("2x4", x=0, z=4, y=0, color="black")
with m.step():
    m.brick("2x4", x=0, z=2, y=1, color="red")
