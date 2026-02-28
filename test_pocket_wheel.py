from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *
from clocks.cq_gears import SpurGear

# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

chain = REGULA_8_DAY_1_05MM_CHAIN

powered_wheel = PocketChainWheel2(chain=chain, ratchet_thick=10, max_diameter=25, ratchet_diameter=35, arbor_d=10)
print(powered_wheel.get_run_time(cordLength=1000))
show_object(powered_wheel.get_model())