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
from .utility import *

import cadquery as cq
import os
from cadquery import exporters
# from random import *

from .types import *

'''
Often I want to fit a new mechanism to an old clock, or something didn't work and I don't want to reprint the whole thing. Here is where the re-usable bits can be stored
'''


# def get_bearing_in_bearing_hole(big_bearing, little_bearing, plates, back=True):
#     '''
#     The large bearings have a lot more friction than I'd realised, so my direct arbour can't work as-is.
#     For now, block up the holes and allow a small bearing to go in place, so i can turn it back into the friction arbour
#     '''
#
#     fake_plate = cq.Workplane("XY").rect(100,100).extrude(plate_thick)
#
#     slightly_smaller_big_bearing = BearingInfo(outer_d=big_bearing.outer_d-0.2, bearingHolderLip=big_bearing.bearingHolderLip, height=big_bearing.height,
#                                                innerD=big_bearing.innerD, innerSafeD=big_bearing.innerSafeD)
#
#     punch = plates.getBearingPunch(bearingOnTop=False, bearingInfo=slightly_smaller_big_bearing, back=back)

