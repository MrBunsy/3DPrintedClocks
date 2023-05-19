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
import cadquery as cq
from pathlib import Path
from cadquery import exporters


class SmithsClip:
    def __init__(self, thick=0.8, diameter=2.3):
        '''
        I've seen two different thickenesses, 0.8 on the older striking movements and 0.5 on the time only spare movement
        inner diameter of the clip (rather than the post) appears to be about 2.35, entry wide about 2.8


        realised I can use bog standard c-clips!
        '''