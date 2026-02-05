from clocks import *

from clocks.cq_gears import BevelGear, BevelGearPair, CrownGearPair

# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass



length = 50
contact_length = 5
arbor_d=3
centre = cq.Workplane("XY").circle(arbor_d/2+0.5).extrude(length - contact_length*2).translate((0,0,contact_length))
centre = centre.edges(">Z or <Z").chamfer(arbor_d*0.75, arbor_d*0.5)


show_object(centre)