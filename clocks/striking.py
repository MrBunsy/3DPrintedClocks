import cadquery as cq
import math
from .utility import *

class Snail:
    '''
    Part of the rack and snail, should be attached to the hour holder
    '''
    def __init__(self, maxDiameter=40, minDiameter=10, thick=3):
        self.maxR=maxDiameter/2
        self.minR=minDiameter/2
        self.thick = thick
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

    def get3D(self):
        snail = self.get2D().extrude(self.thick)

        return snail

class StrikeTrigger:
    '''
    Would like a better name - this is the bit that raises a lever to trigger the hourly and half hourly strikes.
    Should be attached to the minute wheel
    '''
    def __init__(self, minR=5, hourR=10, halfHourR=7.5):
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

        return trigger