import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
import random
import numpy as np

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


def pivotBlock(height=50, length=100,thick=25):
    '''
    Rectangular block with a series of grooves in the top.

    Pivot can be rested in the right size of groove while the arbour is held in a pin vise and rotated by hand

    Then the burnisher/file can be rested on top of the pivot

    NOTE - never actually used
    '''

    block =cq.Workplane("XY").rect(thick,length).extrude(height)

    # radii=[range(0.1,)]

    radii = [0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1, 2, 3, 4]

    count = len(radii)
    space = length/(count+2)

    block.faces(">X").workplane().tag("side")

    for i,r in enumerate(radii):
        block = block.workplaneFromTagged("side").moveTo(-length/2 + space*1.5 + i*space,height).circle(r).cutThruAll()
        # pivot = cq.Workplane("YZ").moveTo(space/2 + i*space,height).circle(r).extrude(thick)
        # pivot = cq.Workplane("YZ").circle(r).extrude(thick)
        #
        # return pivot
        # block = block.cut(pivot)
        # block = block.workplaneFromTagged("side").moveTo(0, height-10).circle(r).extrude(10)  # .cutThruAll()



    return block


def cupWasher(innerD=3, topD=5.5, coutersinkDeep=2.5, height = 4.5):
    '''
    Used to repair the smiths striking wall clock in the dining room (I didn't have small enough screws)
    '''
    wallThick = 2
    washer = cq.Workplane("XY").circle(topD/2 + wallThick).circle(innerD/2).extrude(height)

    countersink = cq.Workplane("XY").add(cq.Solid.makeCone(radius1=innerD / 2, radius2=topD / 2,
                                        height=coutersinkDeep))

    washer = washer.cut(countersink.translate((0,0,height - coutersinkDeep)))

    return washer

def crystal_centre_press(fixing_r=9.4/2, outer_r=10, dome_r=15, fixing_thick=10):
    '''
    9.1 fitted on the end but not past the o-ring
    For putting acrylic crystals into pocket watch lids, I've got the press and round edge holding bits, need something to squeeze the centre of the crystal
    '''
    press = cq.Workplane("XY").circle(outer_r).circle(fixing_r).extrude(fixing_thick)
    # return cq.Workplane("XY").add(cq.Solid.makeSphere(dome_r)).intersect(cq.Workplane("XY").circle(outer_r).extrude(dome_r))

    press = press.union(cq.Workplane("XY").add(cq.Solid.makeSphere(dome_r)).translate((0,0,fixing_thick - (dome_r - outer_r))).intersect(cq.Workplane("XY").circle(outer_r).extrude(dome_r).translate((0,0,fixing_thick))))

    bevel=1

    press = press.cut(cq.Solid.makeCone(radius1=fixing_r+bevel,radius2=fixing_r,height=bevel))

    return press





# washer = cupWasher()
# show_object(washer)
# exporters.export(washer, "../out/smiths_cupwasher.stl")


# testForSteelTube = cq.Workplane("XY").circle(6.2-0.1).circle(6.2/2).extrude(15.6)
# exporters.export(testForSteelTube, "../out/testForSteelTube.stl")

press = crystal_centre_press()
show_object(press)
exporters.export(press, "../out/press.stl")

# block = pivotBlock()
# show_object(block)
# exporters.export(block, "../out/pivot_block.stl")
