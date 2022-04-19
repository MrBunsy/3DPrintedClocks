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

block = pivotBlock()
show_object(block)
exporters.export(block, "../out/pivot_block.stl")
