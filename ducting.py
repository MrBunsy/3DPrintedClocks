import os

from clocks.utility import *
from clocks.geometry import *
from cadquery import exporters
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

class Fan:
    def __init__(self, size=120, screw_distance=105):
        self.size = size
        self.screw_distance = screw_distance

class Ducting:

    def __init__(self, diameter=100, wall_thick=5, screw=None, fan=None):
        self.diameter = diameter
        self.wall_thick = wall_thick
        self.screw = screw
        if self.screw is None:
            self.screw = CountersunkWoodScrew.get_wood_screw(4)
        self.fan = fan
        if self.fan is None:
            self.fan = Fan()
        # seen some listed on screwfix as 98mm wide
        self.ducting_radius_wiggle = 1

        self.fillet_r = 2

    def get_fan_fixing(self):
        fixing = self.get_flat_surface_fixing(base_wide=self.fan.size, screw_distance= self.fan.screw_distance)

        return fixing
    def get_flat_surface_fixing(self, base_wide=-1, screw_distance=-1):

        #maybe make wider?


        outer_radius = self.diameter/2 - self.ducting_radius_wiggle

        width = outer_radius*2 + self.fillet_r*2

        if base_wide > 0:
            width = base_wide
        tall = 50
        fixing = cq.Workplane("XY").rect(width, width).extrude(self.wall_thick).edges("|Z").fillet(self.fillet_r).edges(">Z").fillet(self.fillet_r)
        fixing = fixing.cut(cq.Workplane("XY").circle(outer_radius - self.wall_thick).extrude(self.wall_thick))

        # screw_from_corner = self.screw.head_diameter*1.5
        # r = math.sqrt(2*(width/2)**2) - screw_from_corner
        #
        # for i in range(4):
        #     angle = math.pi/4 + i*math.pi/2
        #     pos = polar(angle, r)
        #     fixing = fixing.cut(self.screw.get_cutter().rotate((0,0,0),(0,1,0),180).translate((0,0,self.wall_thick)).translate(pos))
        if screw_distance < 0:
            screw_distance = width - self.screw.get_head_diameter()*2.5
        screw_positions = []

        for x in [-1, 1]:
            for y in [-1, 1]:
                screw_positions += [(x*screw_distance/2, y*screw_distance/2)]

        for pos in screw_positions:
            fixing = fixing.cut(self.screw.get_cutter().rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, self.wall_thick)).translate(pos))

        fixing = fixing.union(cq.Workplane("XY").circle(outer_radius).circle(outer_radius - self.wall_thick).extrude(tall + self.wall_thick).edges(">Z").fillet(self.fillet_r))


        return fixing

ducting = Ducting(screw=MachineScrew(4, countersunk=True))

show_object(ducting.get_fan_fixing())
show_object(ducting.get_flat_surface_fixing().translate((120,120,0)))

if outputSTL:
    path = "out"
    name="duct_fixing"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(ducting.get_flat_surface_fixing(), out)

    name = "duct_fan_fixing"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(ducting.get_fan_fixing(), out)