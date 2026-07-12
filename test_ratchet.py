from clocks import *


# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

diameter = 40
thick = 4

ratchet = Ratchet2(totalD=diameter, thick=thick, blocks_clockwise=True)

show_object(ratchet.get_outer_wheel())
show_object(ratchet.get_inner_wheel().translate((0,0,ratchet.thick - ratchet.pawl_and_click_thick)))
show_object(ratchet.get_click())
show_object(cq.Workplane("XY").circle(ratchet.screws_radius))