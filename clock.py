import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


# define the generating function
def hypocycloid(t, r1, r2):
    return ((r1-r2)*cos(t)+r2*cos(r1/r2*t-t), (r1-r2)*sin(t)+r2*sin(-(r1/r2*t-t)))

def epicycloid(t, r1, r2):
    return ((r1+r2)*cos(t)-r2*cos(r1/r2*t+t), (r1+r2)*sin(t)-r2*sin(r1/r2*t+t))

def gear(t, r1=4, r2=1):
    if (-1)**(1+floor(t/2/pi*(r1/r2))) < 0:
        return epicycloid(t, r1, r2)
    else:
        return hypocycloid(t, r1, r2)





class GearClass:
    def __init__(self, teeth=10, hole_d=2, thick = 10):
        '''

        :param teeth:
        :param radius:
        '''
        self.teeth = teeth
        self.hole_d = hole_d
        self.thick = thick

    def getCQ(self):
        # create the gear profile and extrude it
        result = (cq.Workplane('XY').parametricCurve(lambda t: gear(t * 2 * pi, 8, 1))
                  .extrude(self.thick).faces(">Z").workplane().circle(self.hole_d/2).cutThruAll())

        return result

gearObj = GearClass()
gearCQ = gearObj.getCQ()

show_object(gearCQ)

exporters.export(gearCQ, "out/gear.stl", tolerance=0.001, angularTolerance=0.01)