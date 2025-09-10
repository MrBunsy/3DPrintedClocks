import math
import numpy as np

from .utility import *
from .geometry import *
import cadquery as cq

class CentrifugalFan:
    '''
    Not going to finish this, decided to just use a conventional bellows and fly on the slide whistle
    '''
    def __init__(self, outer_diameter=50, total_height=25, blade_angle_deg=30, bearing=None, screws=None, blades=10, endshake=1, clockwise=True):
        # dimensions of the outside of the casing
        self.outer_diameter = outer_diameter
        self.total_height = total_height

        self.clockwise = clockwise

        self.bearing = bearing
        if self.bearing is None:
            self.bearing = BEARING_3x10x4
        self.screws = screws
        if self.screws is None:
            self.screws = MachineScrew(3, countersunk=True)

        self.blade_angle = deg_to_rad(blade_angle_deg)
        self.endshake = endshake

        self.wall_thick=2
        self.base_thick = self.bearing.height+1.5
        self.gap = 2
        self.fan_radius = self.outer_diameter/2 - self.wall_thick - self.gap
        self.inner_radius = self.fan_radius*0.4
        self.fan_height = self.total_height - self.base_thick*2 - self.gap*2
        self.fan_thick = 1

        self.blades = blades
        self.blade_thick = 1

    def get_fan(self):
        fan = cq.Workplane("XY").circle(self.fan_radius).circle(self.screws.get_rod_cutter_r()).extrude(self.fan_thick)
        dir = 1 if self.clockwise else -1
        for blade in range(self.blades):
            angle = blade * math.pi * 2 / self.blades
            start = polar(angle, self.inner_radius + self.blade_thick/2)
            end = polar(angle + dir*self.blade_angle, self.fan_radius - self.blade_thick/2)
            fan = fan.union(get_stroke_line([start, end], wide=self.blade_thick, thick=self.fan_height))

        rod_r = self.screws.metric_thread
        #ignoring top gap, this goes up to the bearing with endshake
        standoff_height = 0.4
        rod_height = self.total_height - self.base_thick*2 - self.gap - self.endshake - standoff_height


        fan = fan.union(cq.Workplane("XY").circle(rod_r).circle(self.screws.get_rod_cutter_r()).extrude(rod_height).faces(">Z").workplane()
                        .circle(self.bearing.inner_safe_d/2).circle(self.screws.get_rod_cutter_r()).extrude(standoff_height))

        return fan

    def get_case(self):
        case = cq.Workplane("XY").circle(self.outer_diameter/2).extrude(self.base_thick)
        case = case.faces(">Z").workplane().circle(self.outer_diameter/2).circle(self.outer_diameter/2 - self.wall_thick).extrude(self.total_height - self.base_thick*2)



        x = 1 if self.clockwise else -1

        solid_vent = (cq.Workplane("XY").moveTo(x*self.outer_diameter/4, self.outer_diameter/4).rect(self.outer_diameter/2, self.outer_diameter/2)
                .extrude(self.total_height-self.base_thick))

        case = case.cut(solid_vent)

        vent = solid_vent.cut(cq.Workplane("XY").moveTo(x*self.outer_diameter/4-self.wall_thick/2, self.outer_diameter/4-self.wall_thick/2)
                              .rect(self.outer_diameter/2-self.wall_thick, self.outer_diameter/2-self.wall_thick).extrude(self.total_height-self.base_thick).translate((0,0,self.base_thick)))

        vent = vent.cut(cq.Workplane("XY").circle(self.outer_diameter/2 - self.wall_thick).extrude(self.total_height-self.base_thick).translate((0,0,self.base_thick)))

        case = case.union(vent)

        case = case.cut(self.bearing.get_cutter().translate((0, 0, self.base_thick - self.bearing.height)))

        return case

    def get_assembled(self):
        assembly = self.get_fan().translate((0,0,self.base_thick + self.gap))
        assembly = assembly.add(self.get_case())

        return assembly

