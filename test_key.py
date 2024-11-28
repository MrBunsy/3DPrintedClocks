from clocks import *


# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

key_sides=6
key_containing_diameter=12
wall_thick=2.5
# incircle_diameter = WindingKey.get_screw_length_for_polygon_with_walls(key_containing_diameter, key_sides, wall_thick)
incircle_radius = get_incircle_for_regular_polygon(key_containing_diameter/2 + wall_thick, key_sides)

diagram = cq.Workplane("XY").polygon(key_sides, key_containing_diameter+wall_thick*2)
diagram.add(cq.Workplane("XY").circle(incircle_radius))

# show_object(diagram)
#
key = WindingCrank(key_containing_diameter=12, cylinder_length=21, key_hole_deep=20, key_sides=6, max_radius=40)
#
#
# # #
# # show_object(key.get_let_down_adapter())
show_object(key.get_assembled())
# show_object(key.get_key(for_printing=True))
