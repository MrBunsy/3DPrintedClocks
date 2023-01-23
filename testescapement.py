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


escapement = AnchorEscapement(run=10)

show_object(escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1),-(escapement.lift_deg/2+escapement.lock_deg/2)))

show_object(escapement.getWheel2D())

show_object(cq.Workplane("XY").circle(escapement.diameter/2))
