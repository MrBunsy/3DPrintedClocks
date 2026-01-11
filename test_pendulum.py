from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

knife_edge = KnifeEdgePendulumBits(8)

show_object(knife_edge.get_pendulum_top())

#holder = holder.cut(get_pendulum_holder_cutter(z=z, extra_nut_space=0.4, extra_space_for_rod=0.0).translate((0, self.top_of_pendulum_holder_hole_y)).rotate((0, 0, z), (0, 1, z), 180))
# show_object(get_pendulum_holder_cutter(z=50, extra_nut_space=0.4, extra_space_for_rod=0.0))