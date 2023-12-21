from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
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


motionWorks = MotionWorks(compensate_loose_arbour=False, compact=True, bearing=get_bearing_info(3), cannon_pinion_friction_ring=True, module=1.2)
motionWorks.calculate_size(40)

# hands = Hands(style=HandStyle.SYRINGE, minuteFixing="rectangle", minuteFixing_d1=motionWorks.get_minute_hand_square_size(),minuteFixing_d2=motionWorks.get_minute_hand_square_size(),
#               hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=90, thick=3, outline=1, outlineSameAsBody=False,
#               second_hand_centred=True, secondFixing_d=get_diameter_for_die_cutting(3), chunky=True, hour_style_override=HandStyle.BREGUET, second_style_override=HandStyle.SIMPLE_ROUND)
dial_d = 205
dial = Dial(205, DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
            outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_d/6)
hands = Hands(style=HandStyle.FANCY_WATCH, minute_fixing="circle", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), minute_fixing_d2=motionWorks.get_minute_hand_square_size(),
              hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=dial.get_hand_length(), thick=2, outline=0, outline_same_as_body=False,
              second_hand_centred=True, second_fixing_d=get_diameter_for_die_cutting(3), chunky=True, outline_colour="black", seconds_hand_thick=1)


# hands.show_hands(show_object=show_object)



# show_object(dial.get_dial().rotate((0,0,0),(0,1,0),180), options={"color":"white"} )
# show_object(dial.get_main_dial_detail().rotate((0,0,0),(0,1,0),180), options={"color": Colour.BRASS} )#

show_object(motionWorks.get_assembled())

# show_object(hands.getHand(hand_type=HandType.SECOND, colour="white"))

# hands.show_hands(show_object=show_object, show_second_hand=True)

# hands.output_STLs("test_hands", "out")


