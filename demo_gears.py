from clocks import *

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

# show_object(get_gear_demo(just_style=GearStyle.DIAMONDS))
show_object(get_gear_demo())
# show_object(getGearDemo())
# # show_object(getHandDemo(assembled=True, chunky=True).translate((0,400,0)))
# show_hand_demo(show_object, outline=1, length=200*0.45)