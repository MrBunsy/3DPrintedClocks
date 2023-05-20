
from clocks.autoclock import *
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

if outputSTL:
    # gen_dial_previews("images/", image_size=125)
    gen_motion_works_preview("images/")
    motion_works = MotionWorks(compact=True, bearing=getBearingInfo(3), extra_height=20)
    motion_works.calculateGears(arbourDistance=30)
    gen_motion_works_preview("images/", motion_works)

    gen_anchor_previews("images/", two_d=False)

    gen_grasshopper_previews("images/", two_d=False)