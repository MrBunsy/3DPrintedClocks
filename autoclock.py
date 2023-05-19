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
from clocks.autoclock import *
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass
'''
Plan is two scripts (or arguments?) - generate cache and typescript, and run the server
'''

# gen_gear_previews()
# gen_anchor_previews()
# gen_hand_previews()
#
# #clock = AutoWallClock(centred_second_hand=True, dial_style=DialStyle.LINES_ARC, has_dial=True, gear_style=GearStyle.CURVES)
# clock = AutoWallClock(dial_style=DialStyle.ROMAN, dial_seconds_style=DialStyle.LINES_ARC, has_dial=True, gear_style=GearStyle.ARCS, hand_style=HandStyle.BAROQUE, hand_has_outline=False,
#                       pendulum_period_s=1.25)
# if outputSTL:
#     clock.output_svg("autoclock")
# else:
#     show_object(clock.model.getClock(with_pendulum=True))


# print(enum_to_typescript(GearStyle))
if outputSTL:
    gen_typescript_enums("autoclock/web/autoclock-app/src/app/models/types.ts")
    gen_gear_previews("autoclock/web/autoclock-app/src/assets")
    gen_anchor_previews("autoclock/web/autoclock-app/src/assets")
    gen_hand_previews("autoclock/web/autoclock-app/src/assets")
    gen_dial_previews("autoclock/web/autoclock-app/src/assets")
    #5.5 days approx to run this, maybe not
    # gen_clock_previews("autoclock/web/autoclock-app/src/assets")

