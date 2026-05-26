from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass





geneva_wheels = GenevaGearInlinePair(stop=False, teeth=7, distance=36.0)


demo_bits = geneva_wheels.get_demo_platform_bits()
i = 0
for bit in demo_bits:
    show_object(bit)
    export_STL(bit, f"geneva_demo_{i}", clock_name="geneva_demo", path="out")
    i+=1

# # show_object(geneva_wheels.debug_diagram())
# show_object(geneva_wheels.get_cross_wheel().rotate((0,0,0),(0,0,1),180/7).translate(geneva_wheels.wheel_pos))
# show_object(geneva_wheels.get_finger().rotate((0,0,0),(0,0,1),180))
# # show_object(Gear.cut_style(geneva_wheels.get_finger(), geneva_wheels.get_finger_inner_solid_radius(),inner_radius=3, style=GearStyle.ROUNDED_ARMS5))
#
# show_object(cq.Workplane("XY").circle(geneva_wheels.get_finger_inner_solid_radius()))