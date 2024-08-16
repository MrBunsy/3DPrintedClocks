from clocks import *

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

show_object(get_gear_demo(just_style=GearStyle.BENT_ARMS5))
