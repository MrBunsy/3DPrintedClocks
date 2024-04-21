from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


# escapement = GrasshopperEscapement.get_harrison_compliant_grasshopper()#BrocotEscapment()
# show_object(escapement.get_assembled())

diameter = 55
#
# escapement2 = BrocotEscapment(use_rubies=True, diameter=diameter)
# teeth=30
# anchor_teeth = math.floor(teeth / 3) + 0.5
#
# escapement = AnchorEscapement(anchor_teeth=anchor_teeth, diameter=diameter)
#
# # show_object(escapement.get_anchor_2d().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1),-(escapement.lift_deg/2+escapement.lock_deg/2)))
# # show_object(escapement.get_anchor())
# # show_object(escapement.get_wheel_2d())
# show_object(escapement.get_assembled())
# show_object(escapement2.get_assembled())
#
# show_object(cq.Workplane("XY").circle(escapement.radius))


# show_object(cq.Workplane("XY").circle(escapement.diameter/2))

escapement = AnchorEscapement(diameter=diameter)
show_object(escapement.get_assembled())
