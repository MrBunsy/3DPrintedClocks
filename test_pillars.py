from clocks import *

from clocks.cq_gears import BevelGear, BevelGearPair, CrownGearPair

# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

length = 100
x = 0
for pillar in PillarStyle:

    try:
        show_object(fancy_pillar(r=15,length=length, style=pillar).translate((x,0,0)))
        x += 45
    except:
        pass