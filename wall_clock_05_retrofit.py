import math

from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *
from clocks.cosmetics import *
from clocks.dial import *

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_05_retrofit"
clockOutDir="out"

#aiming for diameter of  17.881637930486566
new_chainwheel = PocketChainWheel2(chain=CHAIN_PRODUCTS_1_4MM_CHAIN, ratchet_thick=5, ratchetOuterD=46, ratchetOuterThick=4.6, max_diameter=20, power_clockwise=False, looseOnRod=True, arbour_d=3, fixings=2)
new_chainwheel.ratchet.ratchetTeeth=16
new_chainwheel.ratchet.clicks=8
print("diameter:",new_chainwheel.diameter, "height", new_chainwheel.getHeight())

new_chainwheel.outputSTLs(clockName, clockOutDir)

# show_object(new_chainwheel.getAssembled())

show_object(new_chainwheel.get_bottom_half())