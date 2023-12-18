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


motionWorks = MotionWorks(compensate_loose_arbour=True, compact=True)

hands = Hands(style=HandStyle.SYRINGE, minuteFixing="rectangle", minuteFixing_d1=motionWorks.get_minute_hand_square_size(),minuteFixing_d2=motionWorks.get_minute_hand_square_size(),
              hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=90, thick=3, outline=1, outlineSameAsBody=False,
              second_hand_centred=True, secondFixing_d=get_diameter_for_die_cutting(3), chunky=True, hour_style_override=HandStyle.BREGUET, second_style_override=HandStyle.SIMPLE_ROUND)

# hands.show_hands(show_object=show_object)

dial = Dial(200, DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
            outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, dial_width=32.5)

show_object(dial.get_dial().rotate((0,0,0),(0,1,0),180), options={"color":"white"} )
show_object(dial.get_main_dial_detail().rotate((0,0,0),(0,1,0),180), options={"color": Colour.BRASS} )