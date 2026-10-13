"""Broken on purpose (B5): a brick added into the gap under an existing overhang.

The plate in step 2 already covers the gap, and the red brick is under the gap, so the yellow
brick in step 3 would have to pass through one of them.
"""

from lego.dsl import Model

m = Model("wedged")
with m.step():
    m.brick("2x4", x=0, z=0, y=0, color="red")  # x 0..3, levels 0..2
    m.brick("1x2", x=0, z=0, y=3, color="blue")  # support at x 0..1
with m.step():
    m.plate("2x4", x=0, z=0, y=6, color="white")  # bridges over the gap at x 2..3
with m.step():
    m.brick("1x2", x=2, z=0, y=3, color="yellow")  # into the gap: red below, white above
