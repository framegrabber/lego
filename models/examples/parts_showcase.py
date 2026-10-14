"""Example: one of each newer part family on a 32x32 baseplate.

Rows (front to back): tiles; round parts and cones; slopes (33°, 65°, 75°, cheese, curved,
corner); arches; window and door frames; long bricks and big plates.
"""

from lego.dsl import Model

m = Model("parts showcase")

with m.step():
    m.baseplate(x=0, y=0, z=0, color="green")

with m.step():  # tiles: smooth, nothing attaches on top
    m.tile("1x1", x=1, z=1, y=1, color="white")
    m.tile("1x2", x=3, z=1, y=1, color="white")
    m.tile("1x4", x=6, z=1, y=1, color="white")
    m.tile("1x6", x=11, z=1, y=1, color="white")
    m.tile("1x8", x=18, z=1, y=1, color="white")
    m.tile("2x2", x=27, z=1, y=1, color="dark_bluish_grey")
with m.step():
    m.tile("2x4", x=1, z=3, y=1, color="dark_bluish_grey")
    m.round_plate("1x1", x=7, z=4, y=1, color="yellow")
    m.round_brick("1x1", x=9, z=4, y=1, color="red")
    m.round_brick("2x2", x=11, z=4, y=1, color="blue")
    m.cone("1x1", x=14, z=4, y=1, color="orange")
    m.cone("1x1", x=9, z=4, y=4, color="white")  # on the round brick

with m.step():  # slopes, all facing front (−z)
    m.slope("3x2", x=1, z=8, y=1, color="red", angle=33)
    m.slope("3x4", x=4, z=8, y=1, color="red", angle=33)
    m.slope("2x1", x=9, z=9, y=1, color="blue", angle=65)
    m.slope("2x1", x=11, z=9, y=1, color="blue", angle=75)
    m.cheese_slope(x=13, z=10, y=1, color="lime")
    m.curved_slope("2x2", x=16, z=9, y=1, color="orange")
with m.step():
    m.curved_slope("2x1", x=19, z=9, y=1, color="orange")
    m.curved_slope("4x2", x=21, z=7, y=1, color="medium_azure")
    m.curved_slope("4x1", x=24, z=7, y=1, color="medium_azure")
    m.corner_slope("outside", x=26, z=9, y=1, color="tan")
    m.corner_slope("inside", x=29, z=9, y=1, color="tan")

with m.step():  # arches stand on their two ends
    m.arch("1x4", x=1, z=14, y=1, color="light_bluish_grey")
    m.arch("1x6", x=6, z=14, y=1, color="light_bluish_grey")
    m.arch("1x8", x=13, z=14, y=1, color="light_bluish_grey")

with m.step():  # window and door frames with their glass and door
    m.window("1x2x2", x=1, z=19, y=1, color="white")
    m.window("1x2x3", x=4, z=19, y=1, color="white")
    m.door("1x4x6", x=7, z=19, y=1, color="white", door_color="red")

with m.step():  # long bricks and big plates
    m.brick("1x12", x=1, z=23, y=1, color="yellow")
    m.brick("2x10", x=14, z=23, y=1, color="dark_red")
    m.plate("6x8", x=1, z=25, y=1, color="dark_bluish_grey")
    m.plate("4x10", x=14, z=26, y=1, color="tan")
    m.plate("8x8", x=24, z=22, y=1, color="white")
