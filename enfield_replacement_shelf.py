'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
import cadquery as cq
from pathlib import Path
from cadquery import exporters
import os

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

def get_enfield_shelf():

    width = 196
    length = 62
    thick = 9.5

    hole_d = 10
    hole_spacing = 73
    hole_from_front = 24
    hole_y = -length/2 + hole_from_front



    movement_space_wide_front = 60
    movement_space_wide_back = 65
    movement_space_front_y = -length/2 + 34
    movement_space_back_y = -length/2 + 52

    pendulum_space_wide_front = 115
    pendulum_space_wide_back = 130
    pendulum_space_front_y = movement_space_back_y
    pendulum_space_back_y = length/2

    shelf = cq.Workplane("XY").rect(width,length).extrude(thick).faces(">Z").workplane().moveTo(-pendulum_space_wide_back/2, pendulum_space_back_y)\
        .lineTo(pendulum_space_wide_back/2, pendulum_space_back_y).lineTo(pendulum_space_wide_front/2, pendulum_space_front_y).lineTo(movement_space_wide_back/2, movement_space_back_y).\
        lineTo(movement_space_wide_front/2, movement_space_front_y).lineTo(-movement_space_wide_front/2, movement_space_front_y).lineTo(-movement_space_wide_back/2, movement_space_back_y). \
        lineTo(-pendulum_space_wide_front / 2, pendulum_space_front_y).lineTo(-pendulum_space_wide_back/2, pendulum_space_back_y).close().cutThruAll()

    shelf = shelf.faces(">Z").workplane().pushPoints([(-hole_spacing/2, hole_y), (hole_spacing/2, hole_y)]).circle(hole_d/2).cutThruAll()



    return shelf


shelf = get_enfield_shelf()

show_object(shelf)

if outputSTL:
    path = "out"
    name = "enfield_shelf"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(shelf, out)