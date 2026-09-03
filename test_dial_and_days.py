from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

gear_style = GearStyle.ARCS
right_side=True

days_complication = DayOfWeekComplication(module=0.7, style=gear_style, bevel_module=1.0, angle_deg=-45, extra_z_height=0, cylinder_length=10, shortened_days=True, text_on_plaques=True, right_side=right_side)
motion_works = MotionWorks(extra_height=14, style=gear_style, thick=3, compensate_loose_arbor=False, compact=True,
                           cannon_pinion_to_hour_holder_gap_size=0.6, drives_complication=days_complication)

days_complication.set_motion_works_sizes(motion_works)

parts = days_complication.get_parts_in_situ()

motion_works_angle = math.pi
if not right_side:
    motion_works_angle = 0

motion_works_parts = motion_works.get_parts_in_situ(motion_works_relative_pos=polar(motion_works_angle, motion_works.get_arbor_distance()))

for part in motion_works_parts:
    show_object(motion_works_parts[part].translate((0,0,motion_works.get_distance_from_front_plate())))
#
#
for part in parts:
    show_object(parts[part],  name=part)
dial_d=190
dial = Dial(dial_d, DialStyle.ARABIC_NUMBERS, font="Dutch Courage", font_scale=0.9,
            font_path="../fonts/dutch_courage/CCDutchCourageLite/CCDutchCourageLite.ttf", outer_edge_style=DialStyle.LINES_RECT, inner_edge_style=None,
            dial_width=30, days_complication=days_complication)

dial_z = motion_works.get_distance_from_front_plate() + motion_works.get_hand_holder_height() - dial.thick - dial.get_hand_space_z()

show_object(dial.get_dial().rotate((0,0,0),(0,1,0),180).translate((0,0,dial_z)), options={"color": "white"}, name="Dial")
show_object(dial.get_all_detail().rotate((0,0,0),(0,1,0),180).translate((0,0,dial_z)), options={"color": Colour.BRASS}, name="Detail")

