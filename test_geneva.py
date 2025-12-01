from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass





geneva_wheels = GenevaGearPair(stop=True, teeth=5)

# show_object(geneva_wheels.debug_diagram())
show_object(geneva_wheels.get_cross_wheel().translate((geneva_wheels.distance, 0)))
