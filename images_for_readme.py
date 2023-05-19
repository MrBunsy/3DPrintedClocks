
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