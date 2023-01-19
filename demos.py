from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

# show_object(getGearDemo())
show_object(getHandDemo(assembled=True, chunky=True).translate((0,400,0)))
