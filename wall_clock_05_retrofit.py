'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
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

clockName="wall_clock_05_retrofit2"
clockOutDir="out"

#aiming for diameter of  17.881637930486566 and height of 13-14mm (13 keeps old endshake, 14 fits with sufficient endshake)
#the chain products chains aren't very good, pitch varies between batches. won't use again
#new_chainwheel = PocketChainWheel2(chain=CHAIN_PRODUCTS_1_4MM_CHAIN, ratchet_thick=5, ratchetOuterD=46, ratchetOuterThick=4.6, max_diameter=20, power_clockwise=False, looseOnRod=True, arbour_d=3, fixings=2)

#this new chain from cousins is promising so far. However I've seen degreased and oiled some bearings (anchor and escape wheel only) and now it's running on 1.25kg , so i could return to the original chain!!
#new_chainwheel = PocketChainWheel2(chain=COUSINS_1_5MM_CHAIN, ratchet_thick=4.5, ratchetOuterD=46, ratchetOuterThick=4.6, max_diameter=25, power_clockwise=False, looseOnRod=True, arbour_d=3, fixings=2, wall_thick=1)

#faithfull chains look promising but are too large for this clock
# new_chainwheel = PocketChainWheel2(chain=FAITHFULL_1_6MM_CHAIN, ratchet_thick=5, ratchetOuterD=46, ratchetOuterThick=4.6, max_diameter=30, power_clockwise=False, looseOnRod=True, arbour_d=3, fixings=2)

new_chainwheel = PocketChainWheel2(chain=REGULA_8_DAY_1_05MM_CHAIN, ratchet_thick=5, ratchetOuterD=46, ratchetOuterThick=4.6, max_diameter=25, power_clockwise=False, looseOnRod=True, arbour_d=3, fixings=2, wall_thick=1.5)

new_chainwheel.ratchet.ratchetTeeth=16
new_chainwheel.ratchet.clicks=8
print("diameter:",new_chainwheel.diameter, "height", new_chainwheel.getHeight())

new_chainwheel.outputSTLs(clockName, clockOutDir)

show_object(new_chainwheel.getAssembled())

# show_object(new_chainwheel.get_bottom_half())