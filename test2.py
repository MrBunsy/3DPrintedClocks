from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *
from clocks.cuckoo_bits import roman_numerals, CuckooWhistle
# from clocks.viewer import *

from clocks.cq_gears import BevelGear, BevelGearPair, CrownGearPair

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


# motionWorks = MotionWorks(compensate_loose_arbour=False, compact=True, bearing=get_bearing_info(3), cannon_pinion_friction_ring=True, module=1.2, minute_hand_thick=2)
# motionWorks.calculate_size(40)
#
# # hands = Hands(style=HandStyle.SYRINGE, minuteFixing="rectangle", minuteFixing_d1=motionWorks.get_minute_hand_square_size(),minuteFixing_d2=motionWorks.get_minute_hand_square_size(),
# #               hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=90, thick=3, outline=1, outlineSameAsBody=False,
# #               second_hand_centred=True, secondFixing_d=get_diameter_for_die_cutting(3), chunky=True, hour_style_override=HandStyle.BREGUET, second_style_override=HandStyle.SIMPLE_ROUND)
# dial_d = 205
# dial = Dial(205, DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
#             outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_d/6)
# hands = Hands(style=HandStyle.FANCY_WATCH, minute_fixing="circle", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), minute_fixing_d2=motionWorks.get_minute_hand_square_size(),
#               hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=0, outline_same_as_body=False,
#               second_hand_centred=True, second_fixing_d=get_diameter_for_die_cutting(3), chunky=True, outline_colour="black", seconds_hand_thick=1)
#
#
# # hands.show_hands(show_object=show_object)
#
#
#
# # show_object(dial.get_dial().rotate((0,0,0),(0,1,0),180), options={"color":"white"} )
# # show_object(dial.get_main_dial_detail().rotate((0,0,0),(0,1,0),180), options={"color": Colour.BRASS} )#
#
# # show_object(motionWorks.get_assembled())
#
# # show_object(hands.getHand(hand_type=HandType.SECOND, colour="black"))
#
# # hands.show_hands(show_object=show_object, show_second_hand=True)
#
# # hands.output_STLs("test_hands", "out")
#
#
# pendulum = Pendulum(bob_d=120, bob_text=["Paul","34"], font=[SANS_GILL_FONT, FANCY_WATCH_FONT])
#
# show_object(pendulum.get_bob())

# show_object(fancy_pillar(30, 100))
#
# show_object(fancy_pillar(30, 100, style=PillarStyle.CLASSIC))
#

# show_object(get_stroke_arc((50,0), (-50,0), 150, wide=10, thick=5 , style=StrokeStyle.ROUND, fill_in=True))

if False:
    cylinder_r=7
    square_side_length = math.sqrt(2) * cylinder_r

    if cylinder_r < 5:
        #square with rounded edges, so we can get something as big as possible
       square_side_length = math.sqrt(2) * cylinder_r * 1.2

    square_side_length=6.14

    pendulum_holder = ColletFixingPendulumWithBeatSetting(collet_size=square_side_length, length=30)

    show_object(pendulum_holder.get_assembled())
    #
    # export_STL(pendulum_holder.get_collet(), "test_collet", path="out/")
    # export_STL(pendulum_holder.get_pendulum_holder(), "test_pendulum_holder", path="out/")

# cone = cq.Workplane("XY").add(cq.Solid.makeCone(radius1=15, radius2=0,height=15,pnt=(0,0,15), dir=(0,0,-1)))

# pendulum = Pendulum()
#
# show_object(pendulum.get_bob_assembled())
#
# holder = ColletFixingPendulumWithBeatSetting(6)
#
# show_object(holder.get_assembled())

# pendulum = FancyPendulum(bob_d=40)#, lid_fixing_screws=MachineScrew(2, countersunk=True, length=10))
#
# # show_object(pendulum.get_bob_assembled(hollow=True))
# #
# show_object(pendulum.get_bob())
# #
# show_object(pendulum.get_bob_lid())
#
# numbers = FancyFrenchArabicNumbers(30)
# digit = 0
# show_object(numbers.get_digit(digit))
# show_object(cq.Workplane("XY").rect(numbers.get_width(digit), numbers.height))
# show_object(numbers.get_twirly_bit(numbers.get_width(digit), numbers.height/2)["shape"])
# show_object(cq.Workplane("XY").rect(numbers.get_width(digit), numbers.height/2))

# show_object(numbers.get_tadpole((0,0), (10,10), clockwise=False)["shape"])
# show_object(cq.Workplane("XY").circle(1).extrude(10).translate((10,10)))

# if False:
#     x = 0
#     for digit in range(0,10):
#         wide = numbers.get_width(digit)
#         x+= wide/2
#         show_object(numbers.get_digit(digit).translate((x,0)))
#         show_object(cq.Workplane("XY").moveTo(x,0).rect(numbers.get_width(digit), numbers.height))
#         x+= wide/2
#         print(f"digit {digit} x {x}")
#
# if True:
#     y = 0
#     for number in range(13):
#         show_object(numbers.get_number(number).translate((0, y)))
#         y+= numbers.height

# show_object(numbers.get_tadpole((0,0), r=5, tail_end_pos=(10,-10)))

threaded_rod = MachineScrew(3)

threaded_rod_cutter = threaded_rod.get_cutter(length=1000, ignore_head=True, self_tapping=True).translate((0,0,-500))#.rotate((0,0,0),(0,0,1),0)

show_object(threaded_rod_cutter)