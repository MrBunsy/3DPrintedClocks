from clocks.autoclock import *
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


# gen_gear_previews()
# gen_anchor_previews()
# gen_hand_previews()

clock = AutoWallClock()
if outputSTL:
    clock.output_svg("autoclock")
else:
    show_object(clock.model.getClock())

