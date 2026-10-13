"""Example: two identical legs built as a sub-assembly, attached under a body.

Shows the sub-assembly pattern: build a part group separately with its own steps, then attach
copies of it in one step of the main model.
"""

from lego.dsl import Model

m = Model("two legs")

leg = m.subassembly("leg")
with leg.step():
    leg.plate("2x4", x=0, z=-1, y=0, color="black", rot=90)  # foot sticks out front and back
    leg.brick("2x2", x=0, z=0, y=1, color="light_bluish_grey")
with leg.step():
    leg.brick("2x2", x=0, z=0, y=4, color="light_bluish_grey")
    leg.brick("2x2", x=0, z=0, y=7, color="dark_bluish_grey")

with m.step():  # hips, x 0..5: two layers with offset seams
    m.plate("2x4", x=0, z=0, y=10, color="red")
    m.plate("2x2", x=4, z=0, y=10, color="red")
    m.plate("2x2", x=0, z=0, y=11, color="red")
    m.plate("2x4", x=2, z=0, y=11, color="red")
with m.step():
    m.attach(leg, x=0, y=0, z=0)
    m.attach(leg, x=4, y=0, z=0)
with m.step():
    m.brick("2x4", x=0, z=0, y=12, color="blue")
    m.brick("2x2", x=4, z=0, y=12, color="blue")
