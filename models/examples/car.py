"""Example: a small car on two wheel sets.

The car points along +x. Each `wheels` part is a 2x2 plate with wheel pins plus two rims and
tyres; turned 90° its axle runs along z, so the wheels stick out one stud on each side of the
2-stud-wide body and reach 2 plates below the holder (the tyres stand on the table).
"""

from lego.dsl import Model

m = Model("car")

with m.step():  # chassis, then the wheel sets pressed on from below
    m.plate("2x6", x=0, z=0, y=2, color="dark_bluish_grey")
with m.step():
    m.wheels(x=0, z=0, y=1, color="black", rot=90)
    m.wheels(x=4, z=0, y=1, color="black", rot=90)
with m.step():  # body
    m.brick("1x2", x=0, z=0, y=3, color="red", rot=90)
    m.brick("2x2", x=1, z=0, y=3, color="red")
    m.slope("2x2", x=3, z=0, y=3, color="trans_light_blue", facing="right")  # windscreen
    m.tile("1x2", x=5, z=0, y=3, color="red", rot=90)  # bonnet
with m.step():
    m.plate("2x2", x=0, z=0, y=6, color="red")
    m.tile("2x2", x=1, z=0, y=7, color="red")  # roof, overlapping both rear parts below
