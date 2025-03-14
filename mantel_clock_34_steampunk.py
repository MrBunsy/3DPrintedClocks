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
import cadquery as cq
from clocks import *

'''
Tinkering with using a smaller spring in a similar gear train to clocks 32/33

this has gone through a few iterations - I'm not sure a smaller spring is a good idea so this has gone back to clock 33 but without the moon
'''
output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Mantel Clock 34"
clock_out_dir= "out"

#dial sizes will be overriden
dial_d=210
dial_width = dial_d*0.15
# dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.ARABIC_NUMBERS, font=CustomFont(FancyFrenchArabicNumbers),
#             outer_edge_style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, inner_edge_style=None, raised_detail=True, dial_width=dial_width, seconds_style=DialStyle.LINES_RECT)
dial =  Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, font=CustomFont(FancyFrenchArabicNumbers),
            outer_edge_style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, inner_edge_style=None, raised_detail=True, dial_width=dial_width, seconds_style=DialStyle.CONCENTRIC_CIRCLES)
hands = Hands(style=HandStyle.SPADE, minute_fixing="square", length=dial_d/2, outline=1, chunky=False, outline_same_as_body=False)

assembly = get_mantel_clock(clock_name=clock_name, hands = hands, dial=dial, second_hand=True, prefer_tall=False, zig_zag_side=False)


plate_colours=[Colour.DARKGREY, Colour.BRASS, Colour.BRASS]#[Colour.DARK_GREEN, Colour.BRASS, Colour.BRASS]



if output_STL:
    assembly.get_BOM().export()
else:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.BLACK], motion_works_colours=[Colour.BRASS],
                        bob_colours=[Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=Colour.PURPLE, dial_colours=[Colour.WHITE, Colour.BLACK],
                        plate_colours=plate_colours)
    # for a, arbor in enumerate(assembly.plates.arbors_for_plate):
    #     show_object(arbor.get_assembled(), name="Arbour {}".format(a))






