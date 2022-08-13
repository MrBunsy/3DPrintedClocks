import cadquery as cq
import math
from .utility import *

class Snail:
    '''
    Part of the rack and snail, should be attached to the hour holder
    '''
    def __init__(self, maxDiameter=40, minDiameter=12, thick=8, wallThick=2):
        self.maxR=maxDiameter/2
        self.minR=minDiameter/2
        self.thick = thick
        #making it not completely solid so it looks better and prints faster
        self.wallThick = wallThick
        # self.gapDistance=minDiameter*0.05


    def get2D(self):
        snail = cq.Workplane("XY")

        hours = 12
        dA = -math.pi*2/hours
        dR = (self.maxR - self.minR)/hours

        start = polar(0, self.minR)

        snail = snail.moveTo(start[0], start[1])

        for hour in range(hours):
            angle = dA * hour
            r = self.minR + dR * hour

            start = polar(angle, r)
            end = polar(angle + dA, r)
            if hour != 0:
                #lineTo(start[0], start[1]).lineTo(end[0], end[1])
                snail = snail.lineTo(start[0], start[1])

            snail=snail.radiusArc(end,r)

        snail = snail.close()




        return snail

    def get3D(self, extraThick=0):
        #TODO consider a ramp so the rack can slide over the 1 o'clock ledge if it's not been raised for any reason?
        #that mechanism hasn't been designed yet
        snail = self.get2D().extrude(self.thick + extraThick)

        shellThick = self.thick-self.wallThick*2

        #get a flat bit that we can use to chop away the inside
        shell = snail.shell(-self.wallThick).translate((0, 0, -self.wallThick)).intersect(cq.Workplane("XY").rect(self.maxR*8, self.maxR*8).extrude(shellThick))

        cutter = snail.cut(shell).cut(shell.translate((0,0,shellThick)))

        snail = snail.cut(cutter)

        return snail

class StrikeTrigger:
    '''
    Would like a better name - this is the bit that raises a lever to trigger the hourly and half hourly strikes.
    Should be attached to the minute wheel
    '''
    def __init__(self, minR=10, hourR=20, halfHourR=15):
        self.minR=minR
        self.hourR=hourR
        self.halfHourR=halfHourR

    def get2D(self):
        #was attempting to make a gradient that lifted at a steady rate, but given up

        # halfHourGradient = (self.halfHourR - self.minR)/math.pi
        #
        # def triggerCurve(angle, minR, gradient):
        #     return polar(angle, minR + gradient*(angle % math.pi))
        #
        # def triggerCurveWhole(angle, minR, hourR, halfHourR):
        #     halfHourGradient = (halfHourR - minR) / math.pi
        #     hourGradient = (hourR - minR)/math.pi
        #
        #     if angle < math.pi:
        #         return polar(angle, minR + halfHourGradient *angle)
        #     else:
        #         return polar(angle, minR + hourGradient * (angle - math.pi) + math.pi)
        #
        # # trigger = cq.Workplane("XY").moveTo(self.minR,0).parametricCurve(lambda a: triggerCurve(a, self.minR, halfHourGradient), start=0, stop = math.pi*2 )
        # trigger = cq.Workplane("XY").moveTo(self.minR,0).parametricCurve(lambda a: triggerCurveWhole(a, self.minR, self.hourR, self.halfHourR), start=0, stop = math.pi*2 )
        # # trigger = trigger.lineTo(-self.minR, 0)
        trigger = cq.Workplane("XY").moveTo(self.minR, 0).radiusArc((0,self.minR),-self.minR).tangentArcPoint((-self.halfHourR,0),relative=False).\
            lineTo(-self.minR,0).radiusArc((0,-self.minR),-self.minR).tangentArcPoint((self.hourR,0),relative=False).close()

        # .rotate((0,0,0),(0,0,1),90)
        #hour is currently at 0deg (+ve x)
        return trigger

class Rack:
    def __init__(self, radius=60, snail=None, holeR=3.5):
        self.radius=radius
        self.hourNotchSize=3
        self.holeR=holeR
        if snail is not None:
            self.hourNotchSize = (snail.maxDiameter - snail.minDiameter)/11

    def get2D(self):
        rack = cq.Workplane("XY")


        return rack