from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

dial_diameter=180
dial = Dial(dial_diameter, dial_width=210*0.15)
dial.second_hand_mini_dial_d=50


#centred second
motion_works = MotionWorks(compensate_loose_arbour=True, compact=True, bearing=get_bearing_info(3), cannon_pinion_friction_ring=True, minute_hand_thick=2.1)

motion_works = MotionWorks(compensate_loose_arbour=True, compact=True)

# hands = Hands(style=HandStyle.SIMPLE_POINTED, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#                     length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
#                     second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True, second_style_override=HandStyle.SIMPLE_ROUND, hour_style_override=HandStyle.SPADE)
hands = Hands(style=HandStyle.DIAMOND, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
              length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, second_hand_centred=False, chunky=True, outline_on_seconds=0,
              second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True, seconds_hand_thick=1)
# hands = Hands(style=HandStyle.FANCY_FRENCH, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#               length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
#               second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True)
#
#
#
hands.show_hands(show_object=show_object, show_second_hand=True)
#
# show_object(hands.get_hand(HandType.SECOND).rotate((0,0,0),(0,0,1),90))

# show_object(hands.get_basic_hand_shape(hour=False, minute=False, second=True, colour=None, thick=1))

# show_object(spade_hand(hand_width=5, thick=3,length=100))
# show_object(diamond_hand(base_r=15, hand_width=5, thick=3,length=100))