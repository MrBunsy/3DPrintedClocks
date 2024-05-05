from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *
from clocks.cuckoo_bits import roman_numerals, CuckooWhistle
from clocks.viewer import *

from clocks.cq_gears import BevelGear, BevelGearPair, CrownGearPair

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


rolling_ball = RollingBallEscapement()

tray = rolling_ball.get_track_assembled()

show_object(tray)
out = "tray.stl"
print("Outputting ", out)
exporters.export(rolling_ball.get_track(), out)



if False:
    #experiments for rolling ball
    #not the right font, but might still use it for the minutes
    dial_minutes = Dial(150, DialStyle.ARABIC_NUMBERS, dial_width=20, font="Gill Sans Medium", font_scale=0.8, font_path="../fonts/GillSans/Gill Sans Medium.otf",
                        inner_edge_style=DialStyle.LINES_RECT, minutes_only=True, top_fixing=False, bottom_fixing=False)
    #looks good for the hours
    dial_hours = Dial(100, DialStyle.ROMAN_NUMERALS, dial_width=15, font="Times New Roman", font_scale=0.6, inner_edge_style=DialStyle.LINES_RECT_LONG_INDICATORS, hours_only=True,
                      top_fixing=False, bottom_fixing=False)

    dial_seconds = Dial(100, dial_width=15, inner_edge_style=DialStyle.LINES_RECT_LONG_INDICATORS, style=DialStyle.ARABIC_NUMBERS, font="Gill Sans Medium", font_scale=0.9,
                        font_path="../fonts/GillSans/Gill Sans Medium.otf", seconds_only=True, top_fixing=False, bottom_fixing=False)

    # dial.configure_dimensions(support_length=10, support_d=21.7)

    hands_minutes = Hands(style=HandStyle.SPADE, minuteFixing="circle", minuteFixing_d1=3, hourFixing="circle", hourfixing_d=3, length=dial_minutes.get_hand_length(), thick=3, outline=0, outlineSameAsBody=False,
                  secondFixing_d=get_diameter_for_die_cutting(3), chunky=True)

    hands_hours_and_seconds = Hands(style=HandStyle.SPADE, minuteFixing="circle", minuteFixing_d1=3, hourFixing="circle", hourfixing_d=3, length=dial_hours.get_hand_length(), thick=3, outline=0, outlineSameAsBody=False,
                          secondFixing_d=get_diameter_for_die_cutting(3), chunky=True, second_hand_centred=True, seconds_hand_thick=2)

    def show_dial(dial, position):
        show_object(dial.get_dial().rotate((0,0,0),(0,1,0),180).translate(position), options={"color":Colour.LIGHTGREY} )
        show_object(dial.get_main_dial_detail().rotate((0,0,0),(0,1,0),180).translate(position), options={"color": Colour.BLACK} )

    show_dial(dial_hours, (-130,0,0))
    show_object(hands_hours_and_seconds.get_hand(hand_type=HandType.HOUR).translate((-130, 0, 10)), options={"color": Colour.BLACK})
    show_dial(dial_minutes, (0, 0, 0))
    show_object(hands_minutes.get_hand(hand_type=HandType.MINUTE).translate((0, 0, 10)), options={"color": Colour.BLACK})
    show_dial(dial_seconds, (130, 0, 0))
    show_object(hands_hours_and_seconds.get_hand(hand_type=HandType.SECOND).translate((130, 0, 10)), options={"color": Colour.BLACK})