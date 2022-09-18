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
    wallThick = 2
    washer = cq.Workplane("XY").circle(topD/2 + wallThick).circle(innerD/2).extrude(height)

    countersink = cq.Workplane("XY").add(cq.Solid.makeCone(radius1=innerD / 2, radius2=topD / 2,
                                        height=coutersinkDeep))

    washer = washer.cut(countersink.translate((0,0,height - coutersinkDeep)))

    return washer



washer = cupWasher()
show_object(washer)
exporters.export(washer, "../out/smiths_cupwasher.stl")

# block = pivotBlock()
# show_object(block)
# exporters.export(block, "../out/pivot_block.stl")
