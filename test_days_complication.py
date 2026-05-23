import math

from clocks.gearing import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


gear_style = GearStyle.ARCS

days_complication = DayOfWeekComplication(module=0.8, style=gear_style, bevel_module=1.1, angle_deg=-70, extra_z_height=0)

motion_works = MotionWorks(extra_height=14, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True,
                           cannon_pinion_to_hour_holder_gap_size=0.6, drives_complication=days_complication)

days_complication.set_motion_works_sizes(motion_works)

parts = days_complication.get_parts_in_situ()

motion_works_parts = motion_works.get_parts_in_situ(motion_works_relative_pos=polar(math.pi, motion_works.get_arbor_distance()))

for part in motion_works_parts:
    show_object(motion_works_parts[part].translate((0,0,motion_works.get_distance_from_front_plate())))


for part in parts:
    show_object(parts[part].translate((0,0, WASHER_THICK_M3)))

# show_object(days_complication.get_arbor_shapes(0)[0])
# show_object(days_complication.get_arbor_shapes(0)[1])