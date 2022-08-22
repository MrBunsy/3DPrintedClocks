import cadquery as cq
import math
from .utility import *

class Rack:
    '''
    designed to be paired with a snail

    Copying Smiths - the pin that rests on the snail is part way along the arm
    '''

    def __init__(self, snail=None, hinge_to_snail=50, fixingScrew=None):

        self.snail = snail

        if self.snail is None:
            self.snail = Snail()

        if fixingScrew is None:
            fixingScrew = MachineScrew(3)
        self.fixingScrew = fixingScrew

        #distance from the hinge of the rack to the centre of the snail
        self.hinge_to_snail = hinge_to_snail
        #specifically, where the gathering pallet pin will be when closest to the hinge
        self.hinge_to_rack = self.hinge_to_snail + self.snail.maxR*1.5

        # since 1 o'clock is maxR, we always need to add one more
        self.snail_per_strike = (self.snail.maxR - self.snail.minR) / 11

        self.angle_per_strike = self.snail_per_strike / self.hinge_to_snail

        self.tip_thick = 1

        self.arm_wide = 2.4
        self.arm_thick = 2.4

        self.hinge_thick = 15

        #have more ratchet than needed, in case the rack ever falls down beside the snail
        self.max_strikes = 13

        self.ratchet_angle = math.pi/4

        '''
        relative to the arm, so if this is zero the bottom of the rack is at the end of the arm, if this is one the top of the rack is at the end of teh arm
        
        0:
        <
        <
        <
        <----------------O
        
        1:
        <----------------O
        <
        <
        <
        <
        
        since I'm not quite sure which is going to be needed yet, this is going to stay flexible
        
        '''
        self.rack_starts_at=0


    def getSprungSnailTip(self):
        '''
        Get the bit that will rest on the snail - this is a separate piece so it can be sprung and thus cope with hands being wound backwards or the strike not being powered

        can this be printed as part of the rack?
        Yes I think it can - if it can jut be a thin vertical bit, it'll bend easily left and right, but notvertically - but will this result in an inconsistent drop?
        I'm wondering if I can just make this bit sacraficial? Or if it's strong enough, then the clock will stop if the strike doesn't work?
        '''

    def getRack(self):
        '''
        This has a spring-like bit that branches off near the hinge, and passes under a small bridge. this should allow the hands to be turned backwards
        or the time to run without the strike, without causing any damage. This is broadly copying the smiths design
        '''



        rack = cq.Workplane("XY").tag("base")

        rack = rack.moveTo(self.hinge_to_rack/2,0).rect(self.hinge_to_rack, self.arm_wide).extrude(self.arm_thick)

        rack = rack.workplaneFromTagged("base").circle(self.fixingScrew.metric_thread*2).extrude(self.hinge_thick)

        rack = rack.faces(">Z").workplane().circle(self.fixingScrew.metric_thread+LOOSE_FIT_ON_ROD).cutThruAll()

        start_angle = 0 - self.rack_starts_at * self.max_strikes * self.angle_per_strike

        for strike in range(self.max_strikes):
            angle = start_angle + self.angle_per_strike * strike
            next_angle = angle + self.angle_per_strike



        return rack


class Snail:
    '''
    Part of the rack and snail, should be attached to the hour holder
    default values work well with default motion works
    '''
    def __init__(self, maxDiameter=40, minDiameter=12, thick=8, wallThick=0):
        self.maxR=maxDiameter/2
        self.minR=minDiameter/2
        self.thick = thick
        #making it not completely solid so it looks better and prints faster
        #note - this worked fine, but actually it *needs* to be solid so if the rack isn't raised it doesn't get stuck on the inside
        #unless I come up with a different mechanism for that
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

        if self.wallThick > 0:
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

# class Rack:
#     def __init__(self, radius=60, snail=None, holeR=3.5):
#         self.radius=radius
#         self.hourNotchSize=3
#         self.holeR=holeR
#         if snail is not None:
#             self.hourNotchSize = (snail.maxDiameter - snail.minDiameter)/11
#
#     def get2D(self):
#         rack = cq.Workplane("XY")
#
#
#         return rack