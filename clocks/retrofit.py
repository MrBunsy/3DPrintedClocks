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
#     slightly_smaller_big_bearing = BearingInfo(bearingOuterD=big_bearing.bearingOuterD-0.2, bearingHolderLip=big_bearing.bearingHolderLip, bearingHeight=big_bearing.bearingHeight,
#                                                innerD=big_bearing.innerD, innerSafeD=big_bearing.innerSafeD)
#
#     punch = plates.getBearingPunch(bearingOnTop=False, bearingInfo=slightly_smaller_big_bearing, back=back)