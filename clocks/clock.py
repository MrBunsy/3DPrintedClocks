import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os
import datetime

'''
Long term plan: this will be a library of useful classes to generate all the components and bits of clock plates
But another script will generate specific clock plates and arbours (note - the GoingTrain class has become a bit of a jack of all trades generating most of the arbours)

Note: naming conventions I can find for clock gears seem to assume you always have the same number of gears between the chain and the minute hand
this is blatantly false (I can see this just looking at the various clocks I have) so I'm adopting a different naming convention:

The minute hand arbour is arbour 0.
In the direction of the escapement is +=ve
in the direction of the chain/spring wheel is -ve

NOTE - although I thought it would be useful to always have the minute wheel as 0, it has actually proven to be more of a bother
A lot of operations require looping through all the bearings, and it would have been much easier to stick with the convention
It's probably too late now to refactor, but worth thinking about for the future 


So for a very simple clock where the minute arbour is also the chain wheel, there could be only three arbours: 0, 1 and 2 (the escape wheel itself)

This way I can add more gears in either direction without confusing things too much.

The gears that drive the hour hand are the motion work. The cannon pinion is attached to the minute hand arbour, this drives the minute wheel.
The minute wheel is on a mini arbour with the hour pinion, which drives the hour wheel. The hour wheel is on the hour shaft.
The hour shaft fits over the minute arbour (on the clock face side) and the hour hand is friction fitted onto the hour shaft

Current plan: the cannon pinion will be loose over the minute arbour, and have a little shaft for the minute hand.
A nyloc nut underneath it and a normal nut on top of the minute hand will provide friction from the minute arbour to the motion work.
I think this is similar to older cuckoos I've seen. It will result in a visible nut, but a more simple time train. Will try it
for the first clock and decide if I want to switch to something else later. 
'''

#aprox 1.13kg per 200ml for number 9 steel shot (2.25mm diameter)
#this must be a bit low, my height=100, diameter=38 wallThick=2.7 could fit nearly 350g of shot (and weighed 50g itself)
#STEEL_SHOT_DENSITY=1.13/0.2
STEEL_SHOT_DENSITY=0.35/0.055
#"Steel shot has a density of 7.8 g/cc" "For equal spheres in three dimensions, the densest packing uses approximately 74% of the volume. A random packing of equal spheres generally has a density around 64%."
#and 70% of 7.8 is 5.46, which is lower than my lowest measured :/

#TODO - pass around metric thread size rather than diameter and have a set of helper methods spit these values out for certain thread sizes
LAYER_THICK=0.2
#assuming m2 screw has a head 2*m2, etc
#note, pretty sure this is often wrong.
METRIC_HEAD_D_MULT=1.9
#assuming an m2 screw has a head of depth 1.5
METRIC_HEAD_DEPTH_MULT=0.75
#metric nut width is double the thread size
METRIC_NUT_WIDTH_MULT=2

#depth of a nut, right for m3, might be right for others
METRIC_NUT_DEPTH_MULT=0.77
METRIC_HALF_NUT_DEPTH_MULT=0.57

def getNutHeight(metric_thread, nyloc=False, halfHeight=False):
    if halfHeight:
        return metric_thread*METRIC_HALF_NUT_DEPTH_MULT

    if metric_thread == 3:
        if nyloc:
            return 3.9

    return metric_thread * METRIC_NUT_DEPTH_MULT

def getScrewHeadHeight(metric_thread):
    if metric_thread == 3:
        return 2.6

    return metric_thread

def getScrewHeadDiameter(metric_thread):
    if metric_thread == 3:
        return 6
    return METRIC_HEAD_D_MULT * metric_thread

def getNutContainingDiameter(metric_thread, wiggleRoom=0):
    '''
    Given a metric thread size we can safely assume the side-to-side size of the nut is 2*metric thread size
    but the poly() in cq requires:
    "the size of the circle the polygon is inscribed into"

    so this calculates that

    '''

    nutWidth = metric_thread*METRIC_NUT_WIDTH_MULT

    if metric_thread == 3:
        nutWidth=5.4

    nutWidth+=wiggleRoom

    return nutWidth/math.cos(math.pi/6)

class Line:
    def __init__(self, start, angle=None, direction=None, anotherPoint=None):
        '''
        start = (x,y)
        Then one of:
        angle in radians
        direction (x,y) vector - will be made unit
        anotherPoint (x,y) - somewhere this line passes through as well as start
        '''

        self.start = start

        if direction is not None:
            self.dir = direction

        elif angle is not None:
            self.dir = (math.cos(angle), math.sin(angle))
        elif anotherPoint is not None:
            self.dir = (anotherPoint[0] - start[0], anotherPoint[1] - start[1])
        else:
            raise ValueError("Need one of angle, direction or anotherPoint")
        # make unit vector
        self.dir = np.divide(self.dir, np.linalg.norm(self.dir))

    # def getGradient(self):
    #     return self.dir[1] / self.dir[0]

    def intersection(self, b):
        '''
        https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection#Given_two_points_on_each_line
        I used to be able to do this stuff off the top of my head :(

        First we consider the intersection of two lines {\displaystyle L_{1}}L_{1} and {\displaystyle L_{2}}L_{2} in 2-dimensional space, with line {\displaystyle L_{1}}L_{1} being defined by two distinct points {\displaystyle (x_{1},y_{1})}(x_{1},y_{1}) and {\displaystyle (x_{2},y_{2})}(x_{2},y_{2}), and line {\displaystyle L_{2}}L_{2} being defined by two distinct points {\displaystyle (x_{3},y_{3})}(x_3,y_3) and {\displaystyle (x_{4},y_{4})}{\displaystyle (x_{4},y_{4})}

        '''

        x1 = self.start[0]
        x2 = self.start[0] + self.dir[0]
        y1 = self.start[1]
        y2 = self.start[1] + self.dir[1]

        x3 = b.start[0]
        x4 = b.start[0] + b.dir[0]
        y3 = b.start[1]
        y4 = b.start[1] + b.dir[1]

        D = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 - x4)

        if D == 0:
            raise ValueError("Lines do not intersect")

        Px = ((x1*y2 - y1*x2) * (x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / D
        Py = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4))/D

        return (Px, Py)





# line1 = Line((10,0), math.pi)
# line2 = Line((0,10), math.pi/2)
#
# print(line1.intersection(line2))

class Gear:
    @staticmethod
    def cutHACStyle(gear,armThick, rimRadius):
        # vaguely styled after some HAC gears I've got, with nice arcing shapes cut out
        armAngle = armThick / rimRadius
        # cadquery complains it can't make a radiusArc with a radius < rimRadius*0.85. this is clearly bollocks as the sagittaArc works.
        innerRadius = rimRadius * 0.7
        # TODO might want to adjust this based on size of pinion attached to this wheel
        innerSagitta = rimRadius * 0.325

        arms = 5
        #line it up so there's a nice arm a the bottom
        offsetAngle = -math.pi/2 + armAngle/2
        for i in range(arms):
            startAngle = i * math.pi * 2 / arms + offsetAngle
            endAngle = (i + 1) * math.pi * 2 / arms - armAngle + offsetAngle

            startPos = (math.cos(startAngle) * rimRadius, math.sin(startAngle) * rimRadius)
            endPos = (math.cos(endAngle) * rimRadius, math.sin(endAngle) * rimRadius)

            gear = gear.faces(">Z").workplane()
            gear = gear.moveTo(startPos[0], startPos[1]).radiusArc(endPos, -rimRadius).sagittaArc(startPos, -innerSagitta).close().cutThruAll()
            # .radiusArc(startPos,-innerRadius)\
            # .close().cutThruAll()
        return gear

    def __init__(self, isWheel, teeth, module, addendum_factor, addendum_radius_factor, dedendum_factor, toothFactor=math.pi/2):
        self.iswheel = isWheel
        self.teeth = teeth
        self.module=module
        self.addendum_factor=addendum_factor
        # # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl
        # self.addendum_radius_factor=addendum_factor * 1.4
        self.addendum_radius_factor=addendum_radius_factor
        self.dedendum_factor=dedendum_factor

        self.toothFactor = toothFactor

        self.pitch_diameter = self.module * self.teeth
        # # via practical addendum factor
        # self.addendum_height = 0.95 * addendum_factor * module

    def getMaxRadius(self):
        return self.pitch_diameter/2 + self.addendum_factor*self.module

    def get3D(self, holeD=0, thick=0, style="HAC"):
        gear = self.get2D()

        if thick == 0:
            thick = round(self.pitch_diameter*0.05)
        gear = gear.extrude(thick)

        if holeD > 0:
            gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        if self.iswheel:
            if style == "HAC":

                rimThick = max(self.pitch_diameter * 0.035 , 3)
                rimRadius = self.pitch_diameter/2 - self.dedendum_factor*self.module - rimThick

                armThick = rimThick
                gear = Gear.cutHACStyle(gear, armThick, rimRadius)



        return gear

    def addToWheel(self,wheel, holeD=0, thick=4, front=True, style="HAC", pinionThick=8, capThick=2):
        '''
        Intended to add a pinion (self) to a wheel (provided)
        if front is true ,added onto the top (+ve Z) of the wheel, else to -ve Z. Only really affects the escape wheel
        pinionthicker is a multiplier to thickness of the week for thickness of the pinion
        '''

        # pinionThick = thick * pinionthicker

        base = wheel.get3D(thick=thick, holeD=holeD, style=style)

        if front:
            #pinion is on top of the wheel
            distance = thick
            topFace = ">Z"
        else:
            distance = -pinionThick
            topFace = "<Z"

        top = self.get3D(thick=pinionThick, holeD=holeD, style=style).translate([0, 0, distance])

        arbour = base.add(top)

        arbour = arbour.faces(topFace).workplane().circle(self.getMaxRadius()).extrude(capThick).circle(holeD / 2).cutThruAll()

        if not front:
            #make sure big side is on the bottom.
            #wanted to mirror the wheel, but can't due to bug in cadquery https://github.com/ukaea/paramak/issues/548 (I can't see to get a later version to work either)
            arbour = arbour.rotateAboutCenter((0,1,0),180)

        return arbour

    def get2D(self):
        '''
        Return a 2D cadquery profile of a single gear

        note - might need somethign different for pinions?
        '''


        pitch_radius = self.pitch_diameter / 2
        addendum_radius = self.module * self.addendum_radius_factor
        # via practical addendum factor
        addendum_height = 0.95 * self.addendum_factor * self.module
        dedendum_height = self.dedendum_factor * self.module

        inner_radius = pitch_radius - dedendum_height
        outer_radius = pitch_radius + addendum_height

        tooth_angle = self.toothFactor / (self.teeth/2)
        gap_angle = (math.pi - self.toothFactor) / (self.teeth/2)

        gear = cq.Workplane("XY")

        gear = gear.moveTo(inner_radius, 0)

        for t in range(self.teeth):
            # print("teeth: {}, angle: {}".format(t,tooth_angle*(t*2 + 1)))

            toothStartAngle = (tooth_angle + gap_angle)*t + gap_angle
            toothTipAngle = (tooth_angle + gap_angle)*t + gap_angle + tooth_angle/2
            toothEndAngle = (tooth_angle + gap_angle)*(t + 1)

            midBottomPos = ( math.cos(toothStartAngle)*inner_radius, math.sin(toothStartAngle)*inner_radius )
            addendum_startPos = ( math.cos(toothStartAngle)*pitch_radius, math.sin(toothStartAngle)*pitch_radius )
            tipPos = ( math.cos(toothTipAngle)*outer_radius, math.sin(toothTipAngle)*outer_radius )
            addendum_endPos = (math.cos(toothEndAngle) * pitch_radius, math.sin(toothEndAngle) * pitch_radius)
            endBottomPos = (math.cos(toothEndAngle) * inner_radius, math.sin(toothEndAngle) * inner_radius)

            # print(midBottomPos)

            #the gap
            gear = gear.radiusArc(midBottomPos, -inner_radius)
            gear = gear.lineTo(addendum_startPos[0], addendum_startPos[1])
            gear = gear.radiusArc(tipPos, -addendum_radius)
            gear = gear.radiusArc(addendum_endPos, -addendum_radius)
            gear = gear.lineTo(endBottomPos[0], endBottomPos[1])

            # gear = gear.lineTo(midBottomPos[0], midBottomPos[1])
            # gear = gear.lineTo(addendum_startPos[0], addendum_startPos[1])
            # gear = gear.lineTo(tipPos[0], tipPos[1])
            # gear = gear.lineTo(addendum_endPos[0], addendum_endPos[1])
            # gear = gear.lineTo(endBottomPos[0], endBottomPos[1])

        # gear = cq.Workplane("XY").circle(pitch_radius)
        gear = gear.close()

        return gear

class WheelPinionPair:
    '''
    Wheels drive pinions, and wheels and pinions are made to mesh together

    Each arbour will have the wheel of one pair and a pinion of a different pair - which need not have the same size module

    This class creates teh basic shapes for a wheel that drives a specific pinion. There is not much reason for this class to be used outside teh GoingTrain
    The Arbour class combines the wheels and pinions that are on the same rod
    '''

    errorLimit=0.000001
    def __init__(self, wheelTeeth, pinionTeeth, module=1.5):
        '''

        :param teeth:
        :param radius:
        '''
        # self.wheelTeeth = wheelTeeth
        # self.pinionTeeth=pinionTeeth
        self.module=module
        self.thick = module

        self.gear_ratio = wheelTeeth/pinionTeeth

        self.pinion_pitch_radius = self.module * pinionTeeth / 2
        self.wheel_pitch_radius = self.module * wheelTeeth / 2

        self.centre_distance = self.pinion_pitch_radius + self.wheel_pitch_radius

        # self.Diameter_generating_circle = self.pinion_pitch_radius



        wheel_addendum_factor = self.calcWheelAddendumFactor(pinionTeeth)
        # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl says addendum radius factor is 1.4*addendum factor
        wheel_addendum_radius_factor=wheel_addendum_factor*1.4
        #TODO consider custom slop, this is from http://hessmer.org/gears/CycloidalGearBuilder.html
        wheel_dedendum_factor = math.pi/2
        self.wheel = Gear(True, wheelTeeth, module, wheel_addendum_factor, wheel_addendum_radius_factor, wheel_dedendum_factor)

        #based on the practical wheel addendum factor
        pinion_dedendum_factor = wheel_addendum_factor*0.95 + 0.4
        pinion_tooth_factor = 1.25
        if pinionTeeth <= 10:
            pinion_tooth_factor = 1.05
        #https://www.csparks.com/watchmaking/CycloidalGears/index.jxl
        if pinionTeeth == 6 or pinionTeeth == 7:
            pinion_addendum_factor=0.855
            pinion_addendum_radius_factor = 1.05
        elif pinionTeeth == 8 or pinionTeeth == 9:
            pinion_addendum_factor = 0.67
            pinion_addendum_radius_factor = 0.7
        else:
            pinion_addendum_factor = 0.625
            pinion_addendum_radius_factor = 0.625


        self.pinion=Gear(False, pinionTeeth, module, pinion_addendum_factor, pinion_addendum_radius_factor, pinion_dedendum_factor, pinion_tooth_factor)

    def calcWheelAddendumFactor(self,pinionTeeth):
        #http://hessmer.org/gears/CycloidalGearBuilder.html MIT licence
        beta = 0.0
        theta = 1.0
        thetaNew = 0.0
        R = self.gear_ratio
        while (abs(thetaNew - theta) > self.errorLimit):
            theta = thetaNew
            beta = math.atan2(math.sin(theta), (1.0 + 2 * R - math.cos(theta)))
            thetaNew = math.pi/pinionTeeth + 2 * R * beta

        theta = thetaNew

        k = 1.0 + 2 * R

        #addendum factor af
        addendumFactor = pinionTeeth / 4.0 * (1.0 - k + math.sqrt( 1.0 + k * k - 2.0 * k * math.cos(theta)) )
        return addendumFactor

class Arbour:
    def __init__(self, arbourD, wheel=None, wheelThick=None, pinion=None, pinionThick=None, ratchet=None, chainWheel=None, escapement=None, anchor=None, endCapThick=1, style="HAC", distanceToNextArbour=-1, pinionAtFront=True):
        '''
        This represents a combination of wheel and pinion. But with special versions:
        - chain wheel is wheel + ratchet (pinionThick is used for ratchet thickness)
        - escape wheel is pinion + escape wheel
        - anchor is just the escapement anchor ( NOTE - NOT FULLY IMPLEMENTED)

        Trying to store all the special logic for thicknesses and radii in one place
        '''
        self.arbourD=arbourD
        self.wheel=wheel
        self.wheelThick=wheelThick
        self.pinion=pinion
        self.pinionThick=pinionThick
        self.ratchet=ratchet
        self.escapement=escapement
        self.endCapThick=endCapThick
        #the pocket chain wheel (needed only to calculate full height)
        self.chainWheel=chainWheel
        self.style=style
        self.distanceToNextArbour=distanceToNextArbour
        self.nutSpaceMetric=None
        self.pinionOnTop=pinionAtFront
        self.anchor = anchor

        if self.getType() == "Unknown":
            raise ValueError("Not a valid arbour")

    def setNutSpace(self, nutMetricSize=3):
        '''
        This arbour is fixed firmly to the rod, so needs space for a nyloc nut
        '''
        self.nutSpaceMetric=nutMetricSize

    def getType(self):
        if self.wheel is not None and self.pinion is not None:
            return "WheelAndPinion"
        if self.wheel is not None and self.ratchet is not None and self.chainWheel is not None:
            return "ChainWheel"
        if self.wheel is None and self.escapement is not None:
            return "EscapeWheel"
        # if self.escapement is not None:
        #     return "Anchor"
        return "Unknown"


    def getTotalThickness(self):
        '''
        return total thickness of everything that will be on the rod
        '''
        if self.getType() == "WheelAndPinion" or self.getType() == "EscapeWheel":
            return self.wheelThick + self.pinionThick + self.endCapThick
        if self.getType() == "ChainWheel":
            return self.wheelThick + self.ratchet.thick + self.chainWheel.getHeight()
        # if self.getType() == "Anchor":
        #     #wheel thick being used for anchor thick
        #     return self.wheelThick

    def getWheelCentreZ(self):
        '''
        Get the centre of the height of the wheel - which drives the next arbour
        '''
        if self.pinionOnTop:
            return self.wheelThick / 2
        else:
            return self.getTotalThickness() - self.wheelThick/2

    def getPinionCentreZ(self):
        if self.pinionOnTop:
            return self.getTotalThickness() - self.endCapThick - self.pinionThick/2
        else:
            return self.endCapThick + self.pinionThick/2

    def getPinionToWheelZ(self):
        '''
        Useful for calculating the height of the next part of the power train
        '''
        return self.getWheelCentreZ() - self.getPinionCentreZ()

    def getMaxRadius(self):
        if self.wheel is not None:
            #chain wheel, WheelAndPinion
            return self.wheel.getMaxRadius()
        if self.getType() == "EscapeWheel":
            return self.escapement.getWheelMaxR()
        # if self.getType() == "Anchor":
        #     return -1
        raise NotImplementedError("Max Radius not yet implemented for arbour type {}".format(self.getType()))

    def getShape(self, forPrinting=True):
        '''
        return a shape that can be exported to STL
        if for printing, wheel is on the bottom, if false, this is in the orientation required for the final clock
        '''
        if self.getType() == "WheelAndPinion":
            shape = self.pinion.addToWheel(self.wheel, holeD=self.arbourD, thick=self.wheelThick, style=self.style, pinionThick=self.pinionThick, capThick=self.endCapThick)
        elif self.getType() == "EscapeWheel":
            shape = self.pinion.addToWheel(self.escapement, holeD=self.arbourD, thick=self.wheelThick, style=self.style, pinionThick=self.pinionThick, capThick=self.endCapThick)
        elif self.getType() == "ChainWheel":
            shape = getWheelWithRatchet(self.ratchet,self.wheel,holeD=self.arbourD, thick=self.wheelThick, style=self.style)
        else:
            # if self.getType() == "Anchor":
            #     return self.escapement.getAnchorArbour
            raise NotImplementedError("GetShape not yet implemented for arbour type {}".format(self.getType()))
        if self.nutSpaceMetric is not None:
            #cut out a space for a nyloc nut
            deep = self.wheelThick * 0.25
            if self.pinion is not None:
                #can make this much deeper
                deep = min(self.wheelThick*0.75, getNutHeight(self.nutSpaceMetric, nyloc=True))
            shape = shape.cut(getHoleWithHole(self.arbourD, getNutContainingDiameter(self.arbourD, 0.2), deep , 6))

        if not forPrinting and not self.pinionOnTop:
            #make it the right way around for placing in a model
            shape = shape.mirror().translate((0,0,self.getTotalThickness()))


        return shape

class GoingTrain:
    gravity = 9.81
    def __init__(self, pendulum_period=1, fourth_wheel=False, escapement_teeth=30, chainWheels=0, hours=30,chainAtBack=True, scapeAtFront=False, maxChainDrop=1800, max_chain_wheel_d=23):
        '''

        pendulum_period: desired period for the pendulum (full swing, there and back) in seconds
        fourth_wheel: if True there will be four wheels from minute hand to the escape wheel
        escapement_teeth: number of teeth on the escape wheel
        chainWheels: if 0 the minute wheel is also the chain wheel, if >0, this many gears between the minute wheel and chain wheel (say for 8 day clocks)
        hours: intended hours to run for (dictates diameter of chain wheel)
        chainAtBack: Where the chain and ratchet mechanism should go relative to the minute wheel
        scapeAtFront: Where the escape wheel should go relative to its pinion - so the teeth face the right direction.
        maxChainDrop: maximum length of chain drop to meet hours required, in mm
        max_chain_wheel_d: Desired diameter of the chain wheel, only used if chainWheels > 0. If chainWheels is 0 there is no flexibility here


        Grand plan: auto generate gear ratios.
        Naming convention seems to be powered (spring/weight) wheel is first wheel, then minute hand wheel is second, etc, until the escapement
        However, all the 8-day clocks I've got have an intermediate wheel between spring powered wheel and minute hand wheel
        And only the little tiny balance wheel clocks have a "fourth" wheel.
        Regula 1-day cuckoos have the minute hand driven directly from the chain wheel, but then also drive the wheels up the escapment from the chain wheel, effectively making the chain
        wheel part of the gearing from the escapement to the minute wheel

        So, the plan: generate gear ratios from escapement to the minute hand, then make a wild guess about how much weight is needed and the ratio from the weight and
         where it should enter the escapment->minute hand chain

         so sod the usual naming convention until otherwise. Minute hand wheel is gonig to be zero, +ve is towards escapment and -ve is towards the powered wheel
         I suspect regula are onto something, so I may end up just stealing their idea

         This is intended to be agnostic to how the gears are laid out - the options are manually provided for which ways round the gear and scape wheel should face

        '''

        #in seconds
        self.pendulum_period = pendulum_period
        #in metres
        self.pendulum_length = self.gravity * pendulum_period * pendulum_period / (4 * math.pi * math.pi)

        self.scapeAtFront = scapeAtFront
        self.chainAtBack = chainAtBack

        #if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.chainWheels = chainWheels
        self.hours = hours
        self.max_chain_wheel_d = max_chain_wheel_d
        self.maxChainDrop = maxChainDrop

        #calculate ratios from minute hand to escapement
        #the last wheel is the escapement
        self.wheels = 4 if fourth_wheel else 3

        self.escapement_time = pendulum_period * escapement_teeth
        self.escapement_teeth = escapement_teeth
        self.escapement_lift = 4
        self.escapement_drop = 2
        self.escapement_lock = 2
        self.escapement_type = "deadbeat"

        # self.min_pinion_teeth=min_pinion_teeth
        # self.max_wheel_teeth=max_wheel_teeth
        # self.pinion_max_teeth = pinion_max_teeth
        # self.wheel_min_teeth = wheel_min_teeth
        self.trains=[]

    def setEscapementDetails(self, lift = None, drop = None, lock=None, type=None):
        if lift is not None:
            self.lift = lift
        if drop is not None:
            self.drop = drop
        if lock is not None:
            self.lock = lock
        if type is not None:
            self.type = type

    def calculateRatios(self,moduleReduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth = 20, wheel_min_teeth = 50, max_error=0.1, loud=False):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        module recution used to caculate smallest possible wheels - assumes each wheel has a smaller module than the last
        '''

        desired_minute_time = 60*60
        #[ {time:float, wheels:[[wheelteeth,piniontheeth],]} ]
        options = []

        pinion_min=min_pinion_teeth
        pinion_max=pinion_max_teeth
        wheel_min=wheel_min_teeth
        wheel_max=max_wheel_teeth

        '''
        https://needhamia.com/clock-repair-101-making-sense-of-the-time-gears/
        “With an ‘integer ratio’, the same pairs of teeth (gear/pinion) always mesh on each revolution.
         With a non-integer ratio, each pass puts a different pair of teeth in mesh. (Some fractional 
         ratios are also called a ‘hunting ratio’ because a given tooth ‘hunts’ [walks around] the other gear.)”
         
         "So it seems clock designers prefer non-whole-number gear ratios to even out the wear of the gears’ teeth. "
         
         seems reasonable to me
        '''
        allGearPairCombos = []

        for p in range(pinion_min,pinion_max):
            for w in range(wheel_min, wheel_max):
                allGearPairCombos.append([w,p])
        if loud:
            print("allGearPairCombos", len(allGearPairCombos))
        #[ [[w,p],[w,p],[w,p]] ,  ]
        allTrains = []

        allTrainsLength = 1
        for i in range(self.wheels):
            allTrainsLength*=len(allGearPairCombos)

        #this can be made generic for self.wheels, but I can't think of it right now. A stack or recursion will do the job
        #one fewer pairs than wheels
        allcomboCount=len(allGearPairCombos)
        if self.wheels == 3:
            for pair_0 in range(allcomboCount):
                for pair_1 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
        elif self.wheels == 4:
            for pair_0 in range(allcomboCount):
                if loud and pair_0 % 10 == 0:
                    print("{:.1f}% of calculating trains".format(100*pair_0/allcomboCount))
                for pair_1 in range(allcomboCount):
                    for pair_2 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1], allGearPairCombos[pair_2]])
        if loud:
            print("allTrains", len(allTrains))
        allTimes=[]
        totalTrains = len(allTrains)
        for c in range(totalTrains):
            if loud and c % 100 == 0:
                print("{:.1f}% of combos".format(100*c/totalTrains))
            totalRatio = 1
            intRatio = False
            totalTeeth = 0
            #trying for small wheels and big pinions
            totalWheelTeeth = 0
            totalPinionTeeth = 0
            weighting = 0
            lastSize=0
            fits=True
            for p in range(len(allTrains[c])):
                ratio = allTrains[c][p][0] / allTrains[c][p][1]
                if ratio == round(ratio):
                    intRatio=True
                    break
                totalRatio*=ratio
                totalTeeth +=  allTrains[c][p][0] + allTrains[c][p][1]
                totalWheelTeeth += allTrains[c][p][0]
                totalPinionTeeth += allTrains[c][p][1]
                #module * number of wheel teeth - proportional to diameter
                size =  math.pow(moduleReduction, p)*allTrains[c][p][0]
                weighting += size
                if p > 0 and size > lastSize*0.9:
                    #this wheel is unlikely to physically fit
                    fits=False
                    break;
                lastSize = size
            totalTime = totalRatio*self.escapement_time
            error = 60*60-totalTime

            train = {"time":totalTime, "train":allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth, "weighting": weighting }
            if fits and  abs(error) < max_error and not intRatio:
                allTimes.append(train)

        allTimes.sort(key = lambda x: x["weighting"])
        print(allTimes)

        self.trains = allTimes

        if len(allTimes) == 0:
            raise RuntimeError("Unable to calculate valid going train")

        return allTimes

    def setRatios(self, gearPinionPairs):
        #keep in the format of the autoformat
        time={'train': gearPinionPairs}

        self.trains = [time]

    def calculateChainWheelRatios(self):
        if self.chainWheels == 0:
            '''
            nothing to do
            '''
        elif self.chainWheels == 1:
            chainWheelCircumference = self.max_chain_wheel_d * math.pi

            # get the actual circumference (calculated from the length of chain segments)
            chainWheelCircumference = self.chainWheel.circumference

            turns = self.maxChainDrop / chainWheelCircumference

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / self.hours

            desiredRatio = 1 / turnsPerHour

            print("Chain wheel turns per hour", turnsPerHour)
            print("Chain wheel ratio to minute wheel", desiredRatio)

            allGearPairCombos = []

            pinion_min = 10
            pinion_max = 20
            wheel_min = 20
            wheel_max = 100

            for p in range(pinion_min, pinion_max):
                for w in range(wheel_min, wheel_max):
                    allGearPairCombos.append([w, p])
            print("ChainWheel: allGearPairCombos", len(allGearPairCombos))

            allRatios = []
            for i in range(len(allGearPairCombos)):
                ratio = allGearPairCombos[i][0] / allGearPairCombos[i][1]
                if round(ratio) == ratio:
                    # integer ratio
                    continue
                totalTeeth = 0
                # trying for small wheels and big pinions
                totalWheelTeeth = allGearPairCombos[i][0]
                totalPinionTeeth = allGearPairCombos[i][1]

                error = desiredRatio - ratio
                # want a fairly large wheel so it can actually fit next to the minute wheel (which is always going to be pretty big)
                train = {"ratio": ratio, "pair": allGearPairCombos[i], "error": abs(error), "teeth": totalWheelTeeth / 1000}
                if abs(error) < 0.1:
                    allRatios.append(train)

            allRatios.sort(key=lambda x: x["error"] - x["teeth"])  #

            print(allRatios)

            self.chainWheelRatio = allRatios[0]["pair"]
        else:
            raise ValueError("Unsupported number of chain wheels")

    def setChainWheelRatio(self, pinionPair):
        self.chainWheelRatio = pinionPair

    def isWeightOnTheRight(self):
        '''
        returns true if the weight dangles from the right side of the chain wheel (as seen from the front)
        '''

        clockwise = self.ratchet.isClockwise()
        chainAtFront = not self.chainAtBack

        #XNOR
        clockwiseFromFront = not (clockwise != chainAtFront)

        return clockwiseFromFront

    def genChainWheels(self, ratchetThick=7.5, holeD=3.3, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15,screwThreadLength=10):
        '''
        HoleD of 3.5 is nice and loose, but I think it's contributing to making the chain wheel wonky - the weight is pulling it over a bit
        Trying 3.3, wondering if I'm going to want to go back to the idea of a brass tube in the middle

        Generate the gear ratios for the wheels between chain and minute wheel
        again, I'd like to make this generic but the solution isn't immediately obvious and it would take
        longer to make it generic than just make it work
        '''


        if self.chainWheels == 0:
            chainWheelCircumference = self.maxChainDrop/self.hours
            self.max_chain_wheel_d = chainWheelCircumference/math.pi

        elif self.chainWheels == 1:
            chainWheelCircumference = self.max_chain_wheel_d * math.pi
            #use provided max_chain_wheel_d and calculate the rest

        self.chainWheel = ChainWheel(max_circumference=chainWheelCircumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)


        #true for no chainwheels
        anticlockwise = self.chainAtBack

        for i in range(self.chainWheels):
            anticlockwise = not anticlockwise

        self.ratchet = Ratchet(totalD=self.max_chain_wheel_d * 2, innerRadius=self.chainWheel.outerDiameter / 2, thick=ratchetThick, powerAntiClockwise=anticlockwise)

        self.chainWheelWithRatchet = self.chainWheel.getWithRatchet(self.ratchet)
        self.chainWheelHalf = self.chainWheel.getHalf(False)

    def setTrain(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]

    def printInfo(self):
        print(self.trains[0])

        print("pendulum length: {}m period: {}s".format(self.pendulum_length, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement_teeth))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.getRunTime()))
        chainRatio = 1
        if self.chainWheels > 0:
            print(self.chainWheelRatio)
            chainRatio = self.chainWheelRatio[0]/self.chainWheelRatio[1]
        runtime = self.chainWheel.getRunTime(chainRatio,self.maxChainDrop)
        print("runtime: {:.1f}hours. Chain wheel multiplier: {:.1f}".format(runtime, chainRatio))


    def genGears(self, module_size=1.5, holeD=3, moduleReduction=0.85, thick=6, chainWheelThick=-1, escapeWheelThick=-1, escapeWheelMaxD=-1, useNyloc=True, chainModuleIncrease=None):
        '''
        escapeWheelMaxD - if <0 (default) escape wheel will be as big as can fit
        if > 1 escape wheel will be as big as can fit, or escapeWheelMaxD big, if that is smaller
        if > 0 and < 1, escape wheel will be this fraction of the previous wheel
        '''
        arbours = []
        # ratchetThick = holeD*2
        #thickness of just the wheel
        self.gearWheelThick=thick
        #thickness of arbour assembly
        #wheel + pinion (3*wheel) + pinion top (0.5*wheel)

        if chainWheelThick < 0:
            chainWheelThick = thick

        if escapeWheelThick < 0:
            escapeWheelThick = thick

        # self.gearPinionLength=thick*3
        # self.chainGearPinionLength = chainWheelThick*2.5
        pinionThickMultiplier = 2.5

        self.gearPinionEndCapLength=thick*0.25
        # self.gearTotalThick = self.gearWheelThick + self.gearPinionLength + self.gearPinionEndCapLength
        # self.chainGearTotalThick
        style="HAC"
        module_sizes = [module_size * math.pow(moduleReduction, i) for i in range(self.wheels)]

        #the module of each wheel is slightly smaller than the preceeding wheel
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_size* math.pow(moduleReduction, i)) for i,wheel in enumerate(self.trains[0]["train"])]




        # print(module_sizes)
        #make the escape wheel as large as possible, by default
        escapeWheelDiameter = pairs[len(pairs)-1].wheel.getMaxRadius()*2 - pairs[len(pairs)-1].pinion.getMaxRadius() - 5

        #we might choose to override this
        if escapeWheelMaxD > 1 and escapeWheelDiameter > escapeWheelMaxD:
            escapeWheelDiameter = escapeWheelMaxD
        elif escapeWheelMaxD >0 and escapeWheelMaxD < 1:
            #treat as fraction of previous wheel
            escapeWheelDiameter = pairs[len(pairs) - 1].wheel.getMaxRadius() * 2 * escapeWheelMaxD

        # chain wheel imaginary pinion (in relation to deciding which way the next wheel faces) is opposite to where teh chain is
        chainWheelImaginaryPinionAtFront = self.chainAtBack

        #TODO - does this work when chain wheels are involved?
        secondWheelR = pairs[1].wheel.getMaxRadius()
        firstWheelR = pairs[0].wheel.getMaxRadius() + pairs[0].pinion.getMaxRadius()
        ratchetOuterR = self.ratchet.outsideDiameter/2
        space = firstWheelR - ratchetOuterR
        if secondWheelR < space - 3:
            #the second wheel can actually fit on the same side as the ratchet
            chainWheelImaginaryPinionAtFront = not chainWheelImaginaryPinionAtFront

        #using != as XOR, so if an odd number of wheels, it's the same as chainAtBack. If it's an even number of wheels, it's the opposite
        escapeWheelPinionAtFront =  chainWheelImaginaryPinionAtFront != ((self.wheels + self.chainWheels) % 2 == 0)

        #only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escapeWheelClockwise = self.wheels %2 == 1

        escapeWheelClockwiseFromPinionSide = escapeWheelPinionAtFront == escapeWheelClockwise

        pinionAtFront = chainWheelImaginaryPinionAtFront

        print("Escape wheel pinion at front: {}, clockwise (from front) {}, clockwise from pinion side: {} ".format(escapeWheelPinionAtFront, escapeWheelClockwise, escapeWheelClockwiseFromPinionSide))
        self.escapement = Escapement(teeth=self.escapement_teeth, diameter=escapeWheelDiameter, type=self.escapement_type, lift=self.escapement_lift, lock=self.escapement_lock, drop=self.escapement_drop, anchorTeeth=None, clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide)
        self.chainWheelArbours=[]
        if self.chainWheels > 0:
            # assuming one chain wheel for now
            if chainModuleIncrease is None:
                chainModuleIncrease = (1 / moduleReduction)

            chainModule = module_size * chainModuleIncrease
            chainDistance = chainModule * (self.chainWheelRatio[0] + self.chainWheelRatio[1]) / 2

            minuteWheelSpace = pairs[0].wheel.getMaxRadius() + holeD*2

            #check if the chain wheel will fit next to the minute wheel
            if chainDistance < minuteWheelSpace:
                # calculate module for the chain wheel based on teh space available
                chainModule = 2 * minuteWheelSpace / (self.chainWheelRatio[0] + self.chainWheelRatio[1])
            self.chainWheelPair = WheelPinionPair(self.chainWheelRatio[0], self.chainWheelRatio[1], chainModule)
            #only supporting one at the moment, but open to more in the future if needed
            self.chainWheelPairs=[self.chainWheelPair]
            self.chainWheelArbours=[Arbour(chainWheel=self.chainWheel, wheel = self.chainWheelPair.wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=holeD, distanceToNextArbour=self.chainWheelPair.centre_distance, style=style)]
            pinionAtFront = not pinionAtFront

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                if self.chainWheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbour(chainWheel=self.chainWheel, wheel = pairs[i].wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=holeD, distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront)
                else:
                    #just a normal gear
                    arbour = Arbour(wheel = pairs[i].wheel, pinion=self.chainWheelPair.pinion, arbourD=holeD, wheelThick=thick, pinionThick=self.chainWheelArbours[-1].wheelThick*pinionThickMultiplier, endCapThick=self.gearPinionEndCapLength, distanceToNextArbour= pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront)

                if useNyloc:
                    #regardless of chains, we need a nyloc nut to fix the wheel to the rod
                    arbour.setNutSpace(holeD)

                arbours.append(arbour)

            elif i < self.wheels-1:

                #intermediate wheels
                #no need to worry about front and back as they can just be turned around
                arbours.append(Arbour(wheel=pairs[i].wheel, pinion=pairs[i-1].pinion, arbourD=holeD, wheelThick=thick, pinionThick=arbours[-1].wheelThick * pinionThickMultiplier, endCapThick=self.gearPinionEndCapLength,
                                distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront))
            else:
                #last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                arbours.append(Arbour(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbourD=holeD, wheelThick=escapeWheelThick, pinionThick=arbours[-1].wheelThick * pinionThickMultiplier, endCapThick=self.gearPinionEndCapLength,
                                      distanceToNextArbour=self.escapement.anchor_centre_distance, style=style, pinionAtFront=pinionAtFront))

            pinionAtFront = not pinionAtFront
        self.wheelPinionPairs = pairs
        self.arbours = arbours




        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

    def getArbourWithConventionalNaming(self, i):
        '''
        Use the traditional naming of the chain wheel being zero
        '''
        return self.getArbour(i - self.chainWheels)

    def getArbour(self, i):
        '''
        +ve is in direction of the anchor
        0 is minute wheel
        -ve is in direction of power ( so last chain wheel is -1, first chain wheel is -chainWheels)
        '''

        if i >= 0:
            return self.arbours[i]
        else:
            return self.chainWheelArbours[self.chainWheels+i]


    # def getMinuteWheelPinionPair(self):
    #     return self.wheelPinionPairs[0]

    def outputSTLs(self, name="clock", path="../out"):
        for i,arbour in enumerate(self.arbours):
            out = os.path.join(path,"{}_wheel_{}.stl".format(name,i))
            print("Outputting ",out)
            exporters.export(arbour.getShape(), out)
        out = os.path.join(path,"{}_chain_wheel_with_click.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.chainWheelWithRatchet, out)
        out = os.path.join(path, "{}_chain_wheel_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.chainWheelHalf, out)

        for i,arbour in enumerate(self.chainWheelArbours):
            out = os.path.join(path, "{}_chain_wheel_{}.stl".format(name, i))
            print("Outputting ", out)
            exporters.export(arbour.getShape(), out)

        out = os.path.join(path, "{}_escapement_test_rig.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.escapement.getTestRig(), out)

def degToRad(deg):
    return math.pi*deg/180

def radToDeg(rad):
    return rad*180/math.pi

def polar(angle, radius):
    return (math.cos(angle) * radius, math.sin(angle) * radius)

def toPolar(x,y):
    r= math.sqrt(x*x + y*y)
    angle = math.atan2(y,x)
    return (angle, r)

def getArbour(wheel,pinion, holeD=0, thick=0, style="HAC"):
    base = wheel.get3D(thick=thick, holeD=holeD,style=style)

    top = pinion.get3D(thick=thick*3, holeD=holeD,style=style).translate([0,0,thick])

    arbour = base.add(top)

    arbour = arbour.faces(">Z").workplane().circle(pinion.getMaxRadius()).extrude(thick*0.5).circle(holeD/2).cutThruAll()
    return arbour

class Escapement:
    def __init__(self, teeth=42, diameter=100, anchorTeeth=None, type="recoil", lift=4, drop=4, run=10, lock=2, clockwiseFromPinionSide=True):
        '''
        Roughly following Mark Headrick's Clock and Watch Escapement Mechanics.
        Also from reading of The Modern Clock
        Type: "recoil", "deadbeat"

        Choose recoil for the first attempt as it's supposedly more reliable (even if less accurate) and should have less wear on the teeth, since
        most of the side of the tooth is in contact, rather than just the tip

        "With the recoil escapements, there is no need to adjust for lock, only drop" Escapment Mechanics

        lift is the angle of pendulum swing, in degrees

        drop is the rotation of the escape wheel between the teeth engaging the pallets - this is lost energy
        from the weight/spring. However it seems to be required in a real clock. I *think* this is why some clocks are louder than others
        I think this should be used to dictate exact anchor angle?

        Lock "is the distance which the pallet has moved inside of the pitch circle of the escape wheel before being struck by the escape wheel tooth." (The Modern Clock)
        We add lock to the design by changing the position of the pallets

        run is how much the anchor continues to move towards the centre of the escape wheel after locking (or in the recoil, how much it recoils) in degrees
        not sure how to actually use desired run to design anchor

        clockwiseFromPinionSide is for the escape wheel
        '''

        self.lift_deg = lift
        self.halfLift = 0.5*degToRad(lift)
        self.lift = degToRad(lift)

        self.drop_deg= drop
        self.drop = degToRad(drop)

        self.lock_deg = lock
        self.lock=degToRad(lock)

        self.clockwiseFromPinionSide=clockwiseFromPinionSide
        self.run_deg = run
        self.run = degToRad(run)

        self.teeth = teeth
        self.diameter=diameter
        # self.anchourDiameter=anchourDiameter

        self.innerDiameter = diameter * 0.8

        self.radius = self.diameter/2

        self.innerRadius = self.innerDiameter/2

        self.toothHeight = self.diameter/2 - self.innerRadius
        #it can't print a sharp tip, instead of the previous bodge with a different height for printing and letting the slicer do it, do it ourselves
        self.toothTipWidth=1
        self.printedToothHeight = self.toothHeight
        #*8.36/7 worked for a diameter of about 82mm, it's not enough at about 60mm
        # self.printedToothHeight = self.toothHeight+1.4#*8.36/7
        # print("tooth height", self.toothHeight)


        #a tooth height of 8.36 gets printed to about 7mm

        self.type = type

        if anchorTeeth is None:
            # if type == "recoil":
            #     self.anchorTeeth = floor(self.teeth/4)+0.5
            # else:
            #     #very much TODO
            self.anchorTeeth = floor(self.teeth/4)+0.5
        else:
            self.anchorTeeth = anchorTeeth

        # self.anchorTeeth = floor(self.teeth / 4)  + 0.5

        # angle that encompases the teeth the anchor encompases
        self.wheelAngle = math.pi * 2 * self.anchorTeeth / self.teeth



        self.toothAngle = math.pi*2 / self.teeth

        # height from centre of escape wheel to anchor pinion - assuming this is at the point the tangents (from the wheelangle on the escape wheel teeth) meet
        anchor_centre_distance = self.radius / math.cos(self.wheelAngle / 2)

        self.anchor_centre_distance = anchor_centre_distance

        self.anchorAngle = math.pi - self.wheelAngle

        self.anchorTopThickBase = (self.anchor_centre_distance - self.radius) * 0.6
        self.anchorTopThickMid = (self.anchor_centre_distance - self.radius) * 0.1
        self.anchorTopThickTop = (self.anchor_centre_distance - self.radius) * 0.75

    def getAnchor2D(self):
        '''
        Old design works, but is a bit lopsided and I'm not sure it's that efficient.
        I'm also convinced I have a neater idea:

        Draw lines from the anchor centre for the lift angles
        draw lines from the scape wheel centre for the run angles (or rather, tooth angle minus run)
        draw the entry and exit pallets using the intersections of these lines

        draw the rest of the anchor depending on if it's recoil or deadbeat

        '''
        anchor = cq.Workplane("XY").tag("anchorbase")
        centreRadius = self.diameter * 0.09

        anchorCentre = (0,self.anchor_centre_distance)
        wheelCentre = (0,0)



        armThick = self.diameter*0.15
        #aprox
        midEntryPalet = polar(math.pi + self.wheelAngle/2, self.radius)
        armLength = np.linalg.norm(np.subtract(midEntryPalet, anchorCentre))
        armThickAngle = armThick / armLength

        deadbeatAngle=self.run#math.pi*0.05

        #why is this armThick/4 rather than /2?
        anchorCentreBottom = (0, self.anchor_centre_distance - (armThick/4)/ sin(self.anchorAngle/2))
        anchorCentreTop =  (0, self.anchor_centre_distance + (armThick/4)/ sin(self.anchorAngle/2))

        #from the anchor centre, the length of the pallets determines how wide the pendulum will swing (the lift)
        palletLengthAngle=self.lift
        #from the scape wheel, this is the angle of the pallet thickness. For a perfect clock it's half the tooth angle,
        # but we must subtract drop (the angle the escape wheel spins before coming back into contact with the anchor)
        palletThickAngle = self.toothAngle/2 - self.drop

        anchorToEntryPalletCentreAngle = math.pi*1.5 - self.anchorAngle/2 + self.lock/2
        anchorToExitPalletCentreAngle = math.pi * 1.5 + self.anchorAngle / 2 - self.lock/2
        wheelToEntryPalletCentreAngle = math.pi/2 + self.wheelAngle/2
        wheelToExitPalletCentreAngle = math.pi/2 - self.wheelAngle/2

        # =========== entry pallet ============
        entryPalletStartLineFromAnchor = Line(anchorCentre, anchorToEntryPalletCentreAngle - palletLengthAngle/2)
        entryPalletEndLineFromAnchor = Line(anchorCentre, anchorToEntryPalletCentreAngle + palletLengthAngle / 2)

        entryPalletStartLineFromWheel = Line(wheelCentre, wheelToEntryPalletCentreAngle + palletThickAngle/2)
        entryPalletEndLineFromWheel = Line(wheelCentre, wheelToEntryPalletCentreAngle - palletThickAngle /2 )

        entryPalletStartPos = entryPalletStartLineFromAnchor.intersection(entryPalletStartLineFromWheel)
        entryPalletEndPos = entryPalletEndLineFromAnchor.intersection(entryPalletEndLineFromWheel)

        # =========== exit pallet ============
        exitPalletStartLineFromAnchor = Line(anchorCentre, anchorToExitPalletCentreAngle + palletLengthAngle / 2)
        exitPalletEndLineFromAnchor = Line(anchorCentre, anchorToExitPalletCentreAngle - palletLengthAngle / 2)

        exitPalletStartLineFromWheel = Line(wheelCentre, wheelToExitPalletCentreAngle + palletThickAngle / 2)
        exitPalletEndLineFromWheel = Line(wheelCentre, wheelToExitPalletCentreAngle - palletThickAngle / 2)

        exitPalletStartPos = exitPalletStartLineFromAnchor.intersection(exitPalletStartLineFromWheel)
        exitPalletEndPos = exitPalletEndLineFromAnchor.intersection(exitPalletEndLineFromWheel)

        # ========== points on the anchor =========

        #distance of the end of the entry pallet from the anchor centre
        entryPalletEndR = np.linalg.norm(np.subtract(entryPalletEndPos, anchorCentre))
        entryPalletStartR = np.linalg.norm(np.subtract(entryPalletStartPos, anchorCentre))
        innerLeftPoint = tuple(np.add(polar(math.pi*1.5 - self.anchorAngle/2 - palletLengthAngle/2 - deadbeatAngle, entryPalletEndR), anchorCentre))
        outerLeftPoint = tuple(np.add(polar(math.pi*1.5 - self.anchorAngle/2 - palletLengthAngle/2 - armThickAngle - deadbeatAngle, entryPalletStartR), anchorCentre))

        exitPalletEndR = np.linalg.norm(np.subtract(exitPalletEndPos, anchorCentre))
        exitPalletStartR = np.linalg.norm(np.subtract(exitPalletStartPos, anchorCentre))
        innerRightPoint = tuple(np.add(polar(math.pi*1.5 + self.anchorAngle/2 + palletLengthAngle/2 + deadbeatAngle, exitPalletStartR), anchorCentre))
        outerRightPoint = tuple(np.add(polar(math.pi*1.5 + self.anchorAngle/2 + palletLengthAngle/2 + deadbeatAngle + armThickAngle, exitPalletEndR), anchorCentre))

        # entry pallet
        anchor = anchor.moveTo(entryPalletEndPos[0], entryPalletEndPos[1]).lineTo(entryPalletStartPos[0],entryPalletStartPos[1])

        if self.type == "deadbeat":
            anchor = anchor.radiusArc(outerLeftPoint, entryPalletEndR+0.01)

        #just temp - need proper arm and centre
        anchor = anchor.lineTo(anchorCentreTop[0], anchorCentreTop[1]).lineTo(outerRightPoint[0], outerRightPoint[1])

        if self.type == "deadbeat":
            anchor = anchor.radiusArc(exitPalletEndPos, exitPalletEndR)

        anchor = anchor.lineTo(exitPalletStartPos[0], exitPalletStartPos[1])

        if self.type == "deadbeat":
            anchor = anchor.radiusArc(innerRightPoint, -exitPalletStartR)

        anchor = anchor.lineTo(anchorCentreBottom[0], anchorCentreBottom[1]).lineTo(innerLeftPoint[0], innerLeftPoint[1])

        if self.type == "deadbeat":
            anchor = anchor.radiusArc(entryPalletEndPos, -entryPalletEndR)


        anchor = anchor.close()

        entryPalletAngle = math.atan2(entryPalletEndPos[1] - entryPalletStartPos[1], entryPalletEndPos[0] - entryPalletStartPos[0])

        print("Entry Pallet Angle", radToDeg(entryPalletAngle))

        return anchor

    def getAnchor2DOld(self):

        anchor = cq.Workplane("XY").tag("anchorbase")

        centreRadius = self.diameter * 0.09

        #TODO, what should this be for most efficiency?
        #currently bodged in order to get enough drop to be reliable
        entryPalletAngle=degToRad(12)
        exitPalletAngle=-math.pi/2-degToRad(12)#entryPalletAngle






        #distance from anchor pinion to the nominal point the anchor meets the escape wheel
        x = math.sqrt(math.pow(self.anchor_centre_distance,2) - math.pow(self.radius,2))

        #the point on the anchor swing that intersects the escape wheel tooth tip circle
        entryPoint = (math.cos(math.pi/2+self.wheelAngle/2)*self.radius, math.sin(+math.pi/2+self.wheelAngle/2)*self.radius)

        # entrySideDiameter = anchor_centre_distance - entryPoint[1]

        #how far the entry pallet extends into the escape wheel (along the angle of entryPalletAngle)
        liftExtension = x * math.sin(self.halfLift)/math.sin(math.pi - self.halfLift - entryPalletAngle - self.wheelAngle/2)

        # arbitary, just needs to be long enough to contain recoil and lift
        entryPalletLength = liftExtension*3

        # #crude aprox
        # liftExtension2 = math.sin(self.halfLift)*x
        #
        # print(liftExtension)
        # print(liftExtension2)

        # liftExtension = 100

        entryPalletTip = (entryPoint[0] + math.cos(entryPalletAngle)*liftExtension, entryPoint[1] - math.sin(entryPalletAngle)*liftExtension)

        entryPalletEnd = (entryPalletTip[0] - math.cos(entryPalletAngle)* entryPalletLength, entryPalletTip[1] + math.sin(entryPalletAngle) * entryPalletLength)

        exitPalletMiddle = ( -entryPoint[0], entryPoint[1])

        # #try and calculate the actual run
        #
        # #when the tooth is resting on the entryPoint, where is the entry pallet tip?
        # entryPalletEndFromAnchorCentre = np.subtract(entryPalletEnd,[0,self.anchor_centre_distance])


        # anchor = anchor.moveTo(entryPoint[0], entryPoint[1])
        # anchor = anchor.moveTo(entryPalletTip[0], entryPalletTip[1])

        #just assuming this is the same as entry is *nearly* but not quite right
        exitPalletTip=(exitPalletMiddle[0]+liftExtension*math.cos(exitPalletAngle), exitPalletMiddle[1]+liftExtension*math.sin(exitPalletAngle) )
        exitPalletEnd=(exitPalletMiddle[0]-(liftExtension + entryPalletLength)*math.cos(exitPalletAngle), exitPalletMiddle[1]-(liftExtension + entryPalletLength)*math.sin(exitPalletAngle))


        endOfEntryPalletAngle = degToRad(35) # math.pi + wheelAngle/2 +
        endOfExitPalletAngle = degToRad(45)

        h = self.anchor_centre_distance - self.anchorTopThickBase - entryPalletTip[1]

        innerLeft = (entryPalletTip[0] - h*math.tan(endOfEntryPalletAngle), entryPoint[1] + h)
        innerRight = (exitPalletTip[0], innerLeft[1])


        h2 = self.anchor_centre_distance - self.anchorTopThickMid - exitPalletTip[1]
        farRight = (exitPalletTip[0] + h2*math.tan(endOfExitPalletAngle), exitPalletTip[1] + h2)
        farLeft = (-(exitPalletTip[0] + h2*math.tan(endOfExitPalletAngle)), exitPalletTip[1] + h2)



        top = (0, self.anchor_centre_distance + self.anchorTopThickTop)
        topRight = (centreRadius, self.anchor_centre_distance )
        topLeft =  (-centreRadius, self.anchor_centre_distance )


        # anchor = anchor.lineTo(innerLeft[0], innerLeft[1]).lineTo(innerRight[0], innerRight[1]).lineTo(exitPalletTip[0], exitPalletTip[1])
        #
        # anchor = anchor.lineTo(farRight[0], farRight[1]).lineTo(top[0], top[1]).lineTo(farLeft[0], farLeft[1])

        # anchor = anchor.tangentArcPoint(entryPalletEnd, relative=False)
        # anchor = anchor.sagittaArc(entryPalletEnd, (farLeft[0] - entryPalletEnd[0])*1.75)
           #.lineTo(entryPalletEnd[0], entryPalletEnd[1])

        anchor = anchor.moveTo(entryPalletTip[0], entryPalletTip[1]).lineTo(entryPalletEnd[0],entryPalletEnd[1]).tangentArcPoint(farLeft,relative=False)

        #making the anchor a bit smaller
        # anchor = anchor.lineTo(top[0], top[1])
        anchor = anchor.lineTo(topLeft[0], topLeft[1]).radiusArc(topRight, centreRadius+0.1)

        anchor = anchor.lineTo(farRight[0], farRight[1]).lineTo(exitPalletTip[0], exitPalletTip[1]).lineTo(exitPalletEnd[0],exitPalletEnd[1]).lineTo(innerRight[0], innerRight[1])

        anchor = anchor.lineTo(innerLeft[0], innerLeft[1])

        anchor = anchor.close()

        return anchor

    def getAnchor3D(self, thick=15, holeD=2, clockwise=True):

        anchor = self.getAnchor2D()

        anchor = anchor.add(cq.Workplane("XY").moveTo(0, self.anchor_centre_distance).circle(holeD*4/2).extrude(thick))



        anchor = anchor.extrude(thick)

        if not clockwise:
            anchor = anchor.mirror("YZ", (0,0,0))

        anchor = anchor.faces(">Z").workplane().moveTo(0,self.anchor_centre_distance).circle(holeD/2).cutThruAll()

        return anchor

    def getAnchorArbour(self, holeD=3, anchorThick=10, clockwise=True, arbourLength=0, crutchLength=50, crutchBoltD=3, pendulumThick=3, crutchToPendulum=35, nutMetricSize=0):
        '''
        Final plan: The crutch will be a solid part of the anchor, and a bolt will link it to a slot in the pendulum
        Thinking the anchor will be at the bottom of the clock, so the pendulum can be on the front

        length for how long to extend the 3d printed bit of the arbour - I'm still toying with the idea of using this to help keep things in place

        crutchToPendulum - top of the anchor to the start of the pendulum

        if nutMetricSize is provided, leave space for two nuts on either side (intended to be nyloc to fix the anchor to the rod)

        clockwise from the point of view of the side with the crutch - which may or may not be the front of the clock

        '''

        # crutchWidth = crutchBoltD*3
        crutchWidth = pendulumThick*4

        pendulum_space = 30
        if crutchLength > 0:
            crutch = cq.Workplane("XY").tag("base").moveTo(0,crutchLength/2).rect(crutchWidth,crutchLength).extrude(anchorThick/2)
            crutch = crutch.workplaneFromTagged("base").moveTo(0,crutchLength-crutchWidth/2).rect(crutchWidth,crutchWidth).extrude(crutchToPendulum + anchorThick - pendulum_space/2)

            crutch = crutch.faces(">Z").workplane().pushPoints([(-crutchWidth/2 + pendulumThick/2, crutchLength-crutchWidth/2 ), (crutchWidth/2 - pendulumThick/2 , crutchLength-crutchWidth/2)]).rect(pendulumThick, crutchWidth).extrude(pendulum_space)

            #.moveTo(0,crutchLength-crutchBoltD*1.5).circle(crutchBoltD/2)
            crutch = crutch.faces(">Z").workplane().moveTo(0,0).circle(holeD/2).cutThruAll()


        #add a length for the arbour - if required

        if crutchLength == 0 and nutMetricSize == 0:
            #if we've got no crutch or nyloc nut, deliberately reverse it so the side facing forwards is the side printed on the nice textured sheet
            clockwise = not clockwise

        #get the anchor the other way around so we can build on top of it, and centre it on the pinion
        arbour = self.getAnchor3D(anchorThick, holeD, not clockwise).translate([0,-self.anchor_centre_distance,0])

        #clearly soemthing's wrong in the maths so anchorTopThickBase isn't being used as I'd hoped
        #bodgetime
        arbourRadius = min(self.anchorTopThickBase*0.85, self.anchorTopThickTop)

        if arbourLength > 0:
            arbour = arbour.faces(">Z").workplane().circle(arbourRadius).circle(holeD/2).extrude(arbourLength - anchorThick)

        if crutchLength > 0:
            arbour = arbour.add(crutch)


        if nutMetricSize > 0:
            nutThick = METRIC_NUT_DEPTH_MULT * nutMetricSize
            nutSpace = cq.Workplane("XY").polygon(6,getNutContainingDiameter(nutMetricSize,0.2)).extrude(nutThick)
            arbour = arbour.cut(nutSpace.translate((0,0, anchorThick-nutThick)))

        return arbour

    def getWheel2D(self):

        diameterForPrinting = self.diameter + (self.printedToothHeight - self.toothHeight)*2

        dA = -math.pi*2/self.teeth
        toothTipArcAngle = self.toothTipWidth/diameterForPrinting

        if self.type == "recoil":
            #based on the angle of the tooth being 20deg, but I want to calculate everyting in angles from the cetnre of the wheel
            #lazily assume arc along edge of inner wheel is a straight line
            toothAngle = math.pi*20/180
            toothTipAngle = 0
            toothBaseAngle = -math.atan(math.tan(toothAngle)*self.toothHeight/self.innerRadius)
        else:
            #done entirely by eye rather than working out the maths to adapt the book's geometry.
            toothTipAngle = -math.pi*0.05
            toothBaseAngle = -math.pi*0.03
            toothTipArcAngle*=-1

        wheel = cq.Workplane("XY").moveTo(self.innerRadius, 0)

        for i in range(self.teeth):
            angle = dA*i
            tipPosStart = (math.cos(angle+toothTipAngle)*diameterForPrinting/2, math.sin(angle+toothTipAngle)*diameterForPrinting/2)
            tipPosEnd = (math.cos(angle + toothTipAngle + toothTipArcAngle) * diameterForPrinting / 2, math.sin(angle + toothTipAngle + toothTipArcAngle) * diameterForPrinting / 2)
            nextbasePos = (math.cos(angle+dA) * self.innerRadius, math.sin(angle + dA) * self.innerRadius)
            endPos = (math.cos(angle+toothBaseAngle) * self.innerRadius, math.sin(angle + toothBaseAngle) * self.innerRadius)
            # print(tipPos)
            # wheel = wheel.lineTo(0,tipPos[1])
            wheel = wheel.lineTo(tipPosStart[0], tipPosStart[1]).lineTo(tipPosEnd[0], tipPosEnd[1]).lineTo(endPos[0],endPos[1]).radiusArc(nextbasePos,self.innerDiameter)

        wheel = wheel.close()

        return wheel
    def getWheelMaxR(self):
        return self.diameter/2

    def getWheel3D(self, thick=5, holeD=5, style="HAC"):
        gear = self.getWheel2D().extrude(thick)

        if not self.clockwiseFromPinionSide:
            gear = gear.mirror("YZ", (0,0,0))

        rimThick = holeD*1.5
        rimRadius = self.innerRadius - rimThick

        armThick = rimThick
        if style == "HAC":
            gear = Gear.cutHACStyle(gear, armThick, rimRadius)

        # hole = cq.Workplane("XY").circle(holeD/2).extrude(thick+2).translate((0,0,-1))
        #
        # gear = gear.cut(hole)
        #for some reason this doesn't always work
        gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        return gear


    #hack to masquerade as a Gear, then we can use this with getArbour()
    def get3D(self, thick=5, holeD=5, style="HAC"):
        return self.getWheel3D(thick=thick, holeD=holeD, style=style)

    def getTestRig(self, holeD=3, tall=4):
        #simple rig to place both parts on and check they actually work
        holeD=holeD*0.85

        height = self.anchor_centre_distance+holeD
        width = holeD

        testrig = cq.Workplane("XY").rect(width,height).extrude(3).faces(">Z").workplane().pushPoints([(0,self.anchor_centre_distance/2),(0,-self.anchor_centre_distance/2)]).circle(holeD/2).extrude(tall).translate([0,self.anchor_centre_distance/2,0])

        return testrig

    # def getWithPinion(self, pinion, clockwise=True, thick=5, holeD=5, style="HAC"):
    #     base = self.getWheel3D(thick=thick,holeD=holeD, style=style)
    #
    #     top = pinion.get3D(thick=thick * 3, holeD=holeD, style=style).translate([0, 0, thick])
    #
    #     wheel = base.add(top)

        # # face = ">Z" if clockwise else "<Z"
        # #cut hole through both
        # wheel = wheel.faces(">Z").workplane().circle(pinion.getMaxRadius()).extrude(ratchetThick * 0.5).circle(holeD / 2).cutThruAll()

def getHoleWithHole(innerD,outerD,deep, sides=1, layerThick=LAYER_THICK):
    '''
    Generate the shape of a hole ( to be used to cut out of another shape)
    that can be printed with bridging

      |  | inner D
    __|  |__
    |       | outer D       | deep

    if sides is 1 it's a circle, else it's a polygone with that number of sides
    funnily enough zero and 2 are invalid values

    '''

    if sides <= 0 or sides == 2:
        raise ValueError("Impossible polygon, can't have {} sides".format(sides))

    hole = cq.Workplane("XY")
    if sides == 1:
        hole = hole.circle(outerD/2)
    else:
        hole = hole.polygon(sides,outerD)
    hole = hole.extrude(deep+layerThick*2)

    #the shape we want the bridging to end up
    bridgeCutterCutter= cq.Workplane("XY").rect(innerD, outerD).extrude(layerThick).faces(">Z").workplane().rect(innerD,innerD).extrude(layerThick)#

    bridgeCutter = cq.Workplane("XY")
    if sides == 1:
        bridgeCutter = bridgeCutter.circle(outerD/2)
    else:
        bridgeCutter = bridgeCutter.polygon(sides,outerD)

    bridgeCutter = bridgeCutter.extrude(layerThick*2).cut(bridgeCutterCutter).translate((0,0,deep))

    hole = hole.cut(bridgeCutter)

    return hole


class ChainWheel:

    # def anglePerLink(self, radius):
    #     return math.atan(((self.chain_thick + self.chain_inside_length)/2) / (radius + self.chain_thick/2))

    # def getRadiusFromAnglePerLink(self, angle):
    #     return ( (self.chain_thick + self.chain_inside_length)/2 ) / math.tan(angle/2) - self.chain_thick/2

    def __init__(self, max_circumference=75, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15, holeD=3.5 ,screwD=2, screwThreadLength=10, bearing=None):
        '''
        0.2 tolerance worked but could be tighter
        Going for a pocket-chain-wheel as this should be easiest to print in two parts

        default chain is for the spare hubert hurr chain I've got and probably don't need (wire_thick=1.25, inside_length=6.8, width=5)
        '''

        self.holeD=holeD
        self.screwD=screwD
        self.screwThreadLength=screwThreadLength
        self.bearing=bearing
        if bearing is None:
            # I'd been pondering using bearings to reduce chance of hands turning backwards when winidn the chain
            # I've changed  my mind and I think that having the minute wheel firmly attached to the minute rod will be sufficient to avoid the problem
            self.useBearings = False


        self.chain_width = width
        self.chain_thick = wire_thick
        self.chain_inside_length = inside_length

        # max_circumference = math.pi * max_diameter
        self.tolerance = tolerance
        link_length = inside_length*2 - tolerance
        leftover = max_circumference %  link_length

        #this is a circumference that fits exactly an even number of chain segments
        self.circumference = (max_circumference - leftover)

        #shouldn't need rounding
        self.pockets = int(self.circumference / link_length)

        n = self.pockets*2
        #https://en.wikipedia.org/wiki/Apothem "it is the line drawn from the center of the polygon that is perpendicular to one of its sides"
        apothem = ( self.chain_inside_length/2 - self.tolerance ) * math.tan((math.pi * (n - 2)) / (2*n))

        #diameter of the inner bit
        #a pocket is for two link segments
        # angle_per_single_link = math.pi*2/(self.pockets*2)

        self.diameter = (apothem - self.chain_thick/2)*2#self.getRadiusFromAnglePerLink(angle_per_single_link) * 2

        self.radius = self.diameter/2

        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference,self.getRunTime()))
        self.outerDiameter = self.diameter + width * 0.75
        self.outerRadius = self.outerDiameter/2



        self.wall_thick = 1.5
        self.pocket_wall_thick = inside_length - wire_thick*4

        if self.useBearings:
            #so the bearing can fit in and still have space for the screws
            self.extra_height=self.bearing.bearingHeight
        else:
            self.extra_height = 0


        self.inner_width = width*1.2

        self.hole_distance = self.diameter*0.25

    def getHeight(self):
        '''
        Returns total height of the chain wheel, once assembled, ignoring the ratchet
        '''
        return self.inner_width + self.wall_thick*2 + self.extra_height

    def getRunTime(self,minuteRatio=1,chainLength=2000):
        #minute hand rotates once per hour, so this answer will be in hours
        return chainLength/((self.pockets*self.chain_inside_length*2)/minuteRatio)

    def getHalf(self, sideWithClicks=False):
        '''
        I'm hoping to be able to keep both halves identical - so long as there's space for the m3 screws and the m3 pinion then this should remain possible
        both halves are identical if we're not using bearings
        '''

        halfWheel = cq.Workplane("XY")
        extraHeight = 0
        if not sideWithClicks:
            extraHeight = self.extra_height
            # halfWheel = halfWheel.circle(self.outerDiameter/2).extrude(self.wall_thick + extraHeight).faces(">Z").workplane().tag("inside")
        # else:
        #     #not having a wall if we're going to be attached to the ratchet
        #     # halfWheel = halfWheel.tag("inside")
        #     #changed mind, it looks like the chain might catch a bit
        #     halfWheel = halfWheel.circle(self.outerDiameter / 2).extrude(self.wall_thick*0.5).faces(">Z").workplane().tag("inside")

        halfWheel = halfWheel.circle(self.outerDiameter / 2).extrude(self.wall_thick + extraHeight).faces(">Z").workplane().tag("inside")

        # width = self.chain_width*1.2

        #the U shape when looking at a slice through the pocket
        topGap = self.chain_thick*2.5
        midGap = self.chain_thick*2
        bottomGap = self.chain_thick*1.25

        h1 = (self.inner_width - midGap)/2
        h2 = (self.inner_width - bottomGap)/2
        h3 = self.inner_width/2

        bottomGapHeight = self.chain_width*0.5

        halfWheel = halfWheel.circle(self.diameter/2).extrude(h1).faces(">Z").workplane().circle(self.diameter/2).\
            workplane(offset=h2-h1).tag("inside2").circle(self.diameter/2-bottomGapHeight).loft(combine=True). \
            faces(">Z").workplane().circle(self.diameter/2-bottomGapHeight).extrude(bottomGap/2)

        dA = math.pi * 2 / self.pockets
        pocketA = self.pocket_wall_thick/self.outerRadius
        #angle the pocket ends inwards slightly
        pocketA_end_diff = pocketA*0.2

        for i in range(self.pockets):
            #the offset is a lazy way to ensure both halves can be identical, with the screw holes vertical
            angle = i*dA - pocketA/2


            halfWheel = halfWheel.workplaneFromTagged("inside")
            # .rotateAboutCenter(axisEndPoint=(0,0,1),angleDegrees=dA)
            # wp2 = halfWheel.transformed(offset=(0,0,self.inner_width/2)).moveTo(0, self.diameter/2).rect(self.chain_thick,self.chain_thick)
            # halfWheel = halfWheel.moveTo(0, self.diameter / 2).rect(self.chain_thick * 2, self.chain_thick * 2). \
            #     workplane(offset=self.inner_width / 2).moveTo(0, self.diameter / 2).rect(self.chain_thick, self.chain_thick).loft(combine=True)

            # radiusArc((math.cos(angle+pocketA)*self.outerRadius, math.sin(angle+pocketA)*self.outerRadius), -self.outerRadius).close().extrude(h1)

            #yay more weird cadquery bugs, can't have it with the full radius but 0.9999 is fine :/
            halfWheel = halfWheel.moveTo(0,0).lineTo(math.cos(angle)*self.radius, math.sin(angle)*self.radius).\
                lineTo(math.cos(angle+pocketA_end_diff) * self.outerRadius, math.sin(angle+pocketA_end_diff) * self.outerRadius).\
                radiusArc((math.cos(angle + pocketA - pocketA_end_diff) * self.outerRadius, math.sin(angle + pocketA- pocketA_end_diff) * self.outerRadius), -self.outerRadius*0.999).\
                lineTo(math.cos(angle+pocketA) * self.radius, math.sin(angle+pocketA) * self.radius).close().extrude(h1)
                # lineTo(math.cos(angle+pocketA)*self.outerRadius, math.sin(angle+pocketA)*self.outerRadius).close().extrude(h1)

        halfWheel = halfWheel.faces(">Z").workplane().circle(self.holeD/2).cutThruAll()
        if sideWithClicks or not self.useBearings:
            halfWheel = halfWheel.faces(">Z").workplane().moveTo(0,self.hole_distance).circle(self.screwD / 2).cutThruAll()
            halfWheel = halfWheel.faces(">Z").workplane().moveTo(0,-self.hole_distance).circle(self.screwD / 2).cutThruAll()
        else:
            #don't need screw heads
            holes = cq.Workplane("XY").pushPoints([(0, self.hole_distance), (0,-self.hole_distance)]).circle(self.screwD/2).extrude(200).translate((0,0,self.bearing.bearingHeight + LAYER_THICK*2))

            halfWheel = halfWheel.cut(holes)

        if not sideWithClicks and self.useBearings:
            #space for the bearing
            halfWheel = halfWheel.cut(getHoleWithHole(self.holeD, self.bearing.bearingOuterD, self.bearing.bearingHeight))

        if not sideWithClicks:
            #need space for the nuts
            nutSpace = getHoleWithHole(self.screwD, getNutContainingDiameter(self.screwD), self.screwD*METRIC_HEAD_DEPTH_MULT, 6).translate((0, self.hole_distance, 0))
            nutSpace = nutSpace.add(getHoleWithHole(self.screwD, getNutContainingDiameter(self.screwD), self.screwD*METRIC_HEAD_DEPTH_MULT, 6).translate((0, -self.hole_distance, 0)))
            halfWheel = halfWheel.cut(nutSpace)

        return halfWheel

    def getWithRatchet(self, ratchet):


        chain =self.getHalf(True).translate((0, 0, ratchet.thick))

        clickwheel = ratchet.getInnerWheel()

        #holes for screws
        clickwheel = clickwheel.faces(">Z").workplane().circle(self.holeD / 2).moveTo(0, self.hole_distance).circle(self.screwD / 2).moveTo(0, -self.hole_distance).circle(self.screwD / 2).cutThruAll()

        combined = clickwheel.add(chain)

        if self.useBearings:
            bearingHole = getHoleWithHole(self.holeD, self.bearing.bearingOuterD, self.bearing.bearingHeight)
            combined = combined.cut(bearingHole)
        else:

            totalHeight=self.inner_width + self.wall_thick*2 + self.extra_height + ratchet.thick

            #if I don't have screws long enough, sink them further into the click bit
            headDepth = self.screwD*METRIC_HEAD_DEPTH_MULT
            if self.screwThreadLength + headDepth < totalHeight:
                headDepth +=totalHeight - (self.screwThreadLength + headDepth)
                print("extra head depth: ", headDepth)
            else:
                print("need M{} screw of length {}mm".format(self.screwD, totalHeight-headDepth))

            #space for the heads of the screws
            #general assumption: screw heads are double the diameter of the screw and the same depth as the screw diameter
            screwHeadSpace = getHoleWithHole(self.screwD,self.screwD*2,headDepth).translate((0,self.hole_distance,0))
            screwHeadSpace =  screwHeadSpace.add(getHoleWithHole(self.screwD, self.screwD * 2, headDepth).translate((0, -self.hole_distance, 0)))
            # return screwHeadSpace
            combined = combined.cut(screwHeadSpace)

        return combined

class Ratchet:

    '''
    Plan is to do this slightly backwards - so the 'clicks' are attached to the chain wheel and the teeth are on the
    gear-wheel.

    This means that they can be printed as only two parts with minimal screws to keep everything together
    '''

    def __init__(self, totalD=50, thick=5, powerAntiClockwise=True, innerRadius=0):
        # , chain_hole_distance=10, chain_hole_d = 3):
        # #distance of the screw holes on the chain wheel, so the ratchet wheel can be securely attached
        # self.chain_hole_distance = chain_hole_distance
        # self.chain_hole_d = chain_hole_d
        self.outsideDiameter=totalD

        self.outer_thick = self.outsideDiameter*0.1


        self.clickInnerDiameter = self.outsideDiameter * 0.5
        if innerRadius == 0:
            self.clickInnerRadius = self.clickInnerDiameter / 2
        else:
            self.clickInnerRadius = innerRadius

        self.anticlockwise = 1 if powerAntiClockwise else -1

        self.toothLength = self.outsideDiameter*0.025
        self.toothAngle = degToRad(2)* self.anticlockwise

        self.toothRadius = self.outsideDiameter / 2 - self.outer_thick
        self.toothTipR = self.toothRadius - self.toothLength

        self.clicks = 8
        #ratchetTeet must be a multiple of clicks
        self.ratchetTeeth = self.clicks*2


        self.thick = thick

    def isClockwise(self):
        return self.anticlockwise == -1

    def getInnerWheel(self):
        '''
        Contains the ratchet clicks, hoping that PETG will be strong and springy enough, if not I'll have to go for screws as pinions and some spring wire (stainless steel wire might work?)
        Intended to be larger than the chain wheel so it can be printed as part of teh same object
        '''
        wheel = cq.Workplane("XY")

        thick = 1.25

        innerClickR = self.clickInnerRadius

        #arc aprox ratchetThick
        clickArcAngle = self.anticlockwise * thick / innerClickR
        clickOffsetAngle = -(math.pi*2/self.clicks)*1 * self.anticlockwise

        dA = -math.pi*2 / self.clicks * self.anticlockwise

        start = polar(clickOffsetAngle, innerClickR)
        wheel = wheel.moveTo(start[0], start[1])

        outerR = self.toothRadius
        innerR = self.toothRadius-thick


        for i in range(self.clicks):
            toothAngle = dA * i
            clickStartAngle = dA * i + clickOffsetAngle
            clickEndAngle = clickStartAngle - clickArcAngle
            clickNextStartAngle = clickStartAngle + dA

            clickTip = polar(toothAngle, self.toothRadius)
            toothInner = polar(toothAngle-self.toothAngle, self.toothTipR)
            tipToInner = np.subtract(toothInner, clickTip)
            clickInner = tuple(np.add(clickTip, np.multiply(tipToInner, thick/np.linalg.norm(tipToInner))))

            clickStart = polar(clickStartAngle, innerClickR)
            clickEnd = polar(clickEndAngle, innerClickR)
            nextClickStart = polar(clickNextStartAngle, innerClickR)

            wheel = wheel.radiusArc(clickInner, -innerR * self.anticlockwise).lineTo(clickTip[0], clickTip[1]).radiusArc(clickEnd, outerR * self.anticlockwise).radiusArc(nextClickStart, innerClickR * self.anticlockwise)


        wheel = wheel.close().extrude(self.thick)

        return wheel

    def getOuterWheel(self):
        '''
        contains the ratchet teeth, designed so it can be printed as part of the same object as a gear wheel
        '''
        wheel = cq.Workplane("XY").circle(self.outsideDiameter/2)#.circle(self.outsideDiameter/2-self.outer_thick)


        dA = math.pi * 2 / self.ratchetTeeth * self.anticlockwise


        wheel = wheel.moveTo(self.toothRadius,0)

        for i in range(self.ratchetTeeth):
            angle = dA * i

            wheel = wheel.lineTo(math.cos(angle - self.toothAngle) * self.toothTipR, math.sin(angle - self.toothAngle) * self.toothTipR)
            # wheel = wheel.radiusArc(polar(angle - self.toothAngle, self.toothTipR), self.toothTipR)
            # wheel = wheel.lineTo(math.cos(angle + dA) * self.toothRadius, math.sin(angle + dA) * self.toothRadius)
            wheel = wheel.radiusArc(polar(angle+dA, self.toothRadius), -self.toothRadius * self.anticlockwise)

        wheel = wheel.close().extrude(self.thick)


        return wheel


def getWheelWithRatchet(ratchet, gear, holeD=3, thick=5, style="HAC"):
    gearWheel = gear.get3D(holeD=holeD, thick=thick, style=style)

    ratchetWheel = ratchet.getOuterWheel().translate((0,0,thick))

    #space for a nyloc nut

    nutSpace = getHoleWithHole(holeD, getNutContainingDiameter(holeD), METRIC_HEAD_DEPTH_MULT*holeD, 6)
    gearWheel = gearWheel.cut(nutSpace)

    #in case the ratchet wheel is larger than the space in the middle of whichever style is being used
    gearWheel = gearWheel.add(cq.Workplane("XY").circle(ratchet.outsideDiameter/2).circle(holeD/2).extrude(thick))

    return gearWheel.add(ratchetWheel)

class MotionWorks:

    def __init__(self, holeD=3.6, thick=3, cannonPinionLoose=True, module=1, minuteHandThick=3, minuteHandHolderSize=5, minuteHandHolderHeight=50, style="HAC"):
        '''
        if cannon pinion is loose, then the minute wheel is fixed to the arbour, and the motion works must only be friction-connected to the minute arbour.
        '''
        self.holeD=holeD
        self.thick = thick
        self.style=style
        self.cannonPinionLoose = cannonPinionLoose

        #pinching ratios from The Modern Clock
        #adjust the module so the diameters work properly
        self.arbourDistance = module * (36 + 12) / 2
        secondModule = 2 * self.arbourDistance / (40 + 10)
        # print("module: {}, secondMOdule: {}".format(module, secondModule))
        self.pairs = [WheelPinionPair(36,12, module), WheelPinionPair(40,10,secondModule)]

        self.cannonPinionThick = self.thick*2

        self.minuteHandHolderSize=minuteHandHolderSize
        self.minuteHandHolderD = minuteHandHolderSize*math.sqrt(2)+0.5
        # print("minute hand holder D: {}".format(self.minuteHandHolderD))
        self.minuteHolderTotalHeight = minuteHandHolderHeight
        self.minuteHandSlotHeight = minuteHandThick

        self.wallThick = 1.5
        self.space = 1
        self.hourHandHolderD = self.minuteHandHolderD + self.space + self.wallThick*2

    def getHourHandHoleD(self):
        return self.hourHandHolderD

    def getArbourDistance(self):
        return self.arbourDistance

    def getCannonPinionBaseThick(self):
        '''
        get the thickness of the pinion + caps at the bottom of the cannon pinion

        '''

        return self.thick + self.cannonPinionThick

    def getCannonPinion(self):

        base = cq.Workplane("XY").circle(self.pairs[0].pinion.getMaxRadius()).extrude(self.thick/2)
        pinion = self.pairs[0].pinion.get2D().extrude(self.cannonPinionThick).translate((0,0,self.thick/2))

        top = base.translate((0,0,self.thick/2+self.cannonPinionThick))

        pinion = pinion.add(base).add(top)


        if self.cannonPinionLoose:
            #has an arm to hold the minute hand
            pinion = pinion.faces(">Z").workplane().circle(self.minuteHandHolderD/2).extrude(self.minuteHolderTotalHeight-self.minuteHandSlotHeight-self.cannonPinionThick - self.thick)
            pinion = pinion.faces(">Z").workplane().rect(self.minuteHandHolderSize,self.minuteHandHolderSize).extrude(self.minuteHandSlotHeight)

        pinion = pinion.faces(">Z").workplane().circle(self.holeD/2).cutThruAll()

        return pinion

    def getMotionArbour(self):
        #mini arbour that sits between the cannon pinion and the hour wheel
        return getArbour(self.pairs[0].wheel, self.pairs[1].pinion,holeD=self.holeD, thick = self.thick, style=self.style)

    def getHourHolder(self):
        #the final wheel and arm that friction holds the hour hand



        #TODO the sides need to slope in slightly to make the friction fit easier
        hour = self.pairs[1].wheel.get3D(holeD=self.holeD,thick=self.thick,style=self.style)

        height = self.minuteHolderTotalHeight - self.cannonPinionThick - self.thick - self.thick  - self.minuteHandSlotHeight - self.space

        # hour = hour.faces(">Z").workplane().circle(self.hourHandHolderD/2).extrude(height)

        #want it tapered so an hour hand can be pushed down for a friction fit
        topR = self.hourHandHolderD/2-0.5
        midR = self.hourHandHolderD/2
        bottomR = self.hourHandHolderD/2

        holeR = self.minuteHandHolderD / 2 + self.space / 2

        # return hour
        circle = cq.Workplane("XY").circle(bottomR)
        shape = cq.Workplane("XZ").moveTo(bottomR,0).lineTo(midR,height/2).lineTo(topR,height).lineTo(holeR,height).lineTo(holeR,0).close().sweep(circle).translate((0,0,self.thick))

        hour = hour.add(shape)
        # return shape

        #something very strange is going on with trying to combine shapes. once again cadquery doesn't quite do anything that makes sense.
        # shape = cq.Workplane("XY").add(cq.Solid.makeCone(bottomR,topR,height))
        # # shape= shape.faces(">Z").workplane().circle(self.minuteHandHolderD/2 + self.space/2).cutThruAll()
        # hour = hour.add(shape)

        hole = cq.Workplane("XY").circle(holeR).extrude(height*2)
        hour = hour.cut(hole)

        #seems like we can't cut through all when we've added shapes? I'm sure this has worked elsewhere!
        # hour = hour.faces(">Z").workplane().circle(self.minuteHandHolderD/2 + self.space/2).cutThruAll()



        return hour

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_motion_cannon_pinion.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getCannonPinion(), out)

        out = os.path.join(path, "{}_motion_arbour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getMotionArbour(), out)

        out = os.path.join(path, "{}_motion_hour_holder.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHourHolder(), out)

# class PinionHole:
#     def __init__(self):

class BearingInfo():
    '''
    I'm undecided how to pass this info about
    '''
    def __init__(self, bearingOuterD=10, bearingHolderLip=1.5, bearingHeight=4, innerD=3):
        self.bearingOuterD = bearingOuterD
        # how much space we need to support the bearing (and how much space to leave for the arbour + screw0
        self.bearingHolderLip = bearingHolderLip
        self.bearingHeight = bearingHeight
        self.inner=innerD


class ClockPlates:
    '''
    This was intended to be generic, but has become specific to each clock. Until the design is more settled, the only way to get old designs is going to be version control
    back to the reusable bits
    '''
    def __init__(self, goingTrain, motionWorks, pendulum, style="vertical", arbourD=3, bearingOuterD=10, bearingHolderLip=1.5, bearingHeight=4, screwheadHeight=2.5, pendulumAtTop=True, fixingScrewsD=3, plateThick=5, pendulumSticksOut=20, name="", dial=None):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!
        '''

        anglesFromMinute = None
        anglesFromChain = None

        #"round" or "vertical"
        self.style=style
        #to print on the back
        self.name = name
        #to get fixing positions
        self.dial = dial

        #just for the first prototype
        self.anchorHasNormalBushing=True
        self.motionWorks = motionWorks
        self.goingTrain = goingTrain
        self.pendulum=pendulum
        #up to and including the anchor
        self.anglesFromMinute = anglesFromMinute
        self.anglesFromChain=anglesFromChain
        self.plateThick=plateThick
        self.arbourD=arbourD
        #maximum dimention of the bearing
        self.bearingOuterD=bearingOuterD
        #how chunky to make the bearing holders
        self.bearingWallThick = 4
        #how much space we need to support the bearing (and how much space to leave for the arbour + screw0
        self.bearingHolderLip=bearingHolderLip
        self.bearingHeight = bearingHeight
        self.screwheadHeight = screwheadHeight
        self.pendulumAtTop = pendulumAtTop
        self.pendulumSticksOut = pendulumSticksOut

        # how much space to leave around the edge of the gears for safety
        self.gearGap = 3

        #TODO make some sort of object to hold all this info we keep passing around?
        self.anchorThick=self.pendulum.anchorThick

        self.fixingScrewsD = fixingScrewsD

        self.holderInnerD=self.bearingOuterD - self.bearingHolderLip*2

        #if angles are not given, assume clock is entirely vertical

        if anglesFromMinute is None:
            #assume simple pendulum at top
            angle = math.pi/2 if self.pendulumAtTop else math.pi / 2

            #one extra for the anchor
            self.anglesFromMinute = [angle for i in range(self.goingTrain.wheels + 1)]
        if anglesFromChain is None:
            angle = math.pi / 2 if self.pendulumAtTop else -math.pi / 2

            self.anglesFromChain = [angle for i in range(self.goingTrain.chainWheels)]

        if self.style=="round":

            # TODO decide if we want the train to go in different directions based on which side the weight is
            side = -1 if self.goingTrain.isWeightOnTheRight() else 1
            arbours = [self.goingTrain.getArbourWithConventionalNaming(arbour) for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels)]
            distances = [arbour.distanceToNextArbour for arbour in arbours]
            maxRs = [arbour.getMaxRadius() for arbour in arbours]
            arcAngleDeg = 270

            foundSolution=False
            while(not foundSolution and arcAngleDeg > 180):
                arcRadius = getRadiusForPointsOnAnArc(distances, degToRad(arcAngleDeg))

                # minDistance = max(distances)

                if arcRadius > max(maxRs):
                    #if none of the gears cross the centre, they should all fit
                    #pretty sure there are other situations where they all fit
                    #and it might be possible for this to be true and they still don't all fit
                    #but a bit of playing around and it looks true enough
                    foundSolution=True
                    self.compactRadius = arcRadius
                else:
                    arcAngleDeg-=1
            if not foundSolution:
                raise ValueError("Unable to calculate radius for gear ring, try a vertical clock instead")

            angleOnArc = -math.pi/2
            lastPos = polar(angleOnArc, arcRadius)

            for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels):
                '''
                Calculate angle of the isololese triangle with the distance at the base and radius as the other two sides
                then work around the arc to get the positions
                then calculate the relative angles so the logic for finding bearing locations still works
                bit over complicated
                '''
                print("angle on arc: {}deg".format(radToDeg(angleOnArc)))
                nextAngleOnArc = angleOnArc + 2*math.asin(distances[i+self.goingTrain.chainWheels]/(2*arcRadius))*side
                nextPos = polar(nextAngleOnArc, arcRadius)

                relativeAngle = math.atan2(nextPos[1] - lastPos[1], nextPos[0] - lastPos[0])
                if i < 0 :
                    self.anglesFromChain[i + self.goingTrain.chainWheels] = relativeAngle
                else:
                    self.anglesFromMinute[i] = relativeAngle
                lastPos = nextPos
                angleOnArc = nextAngleOnArc


        #[[x,y,z],]
        #for everything, arbours and anchor
        self.bearingPositions=[]
        #TODO consider putting the anchor on a bushing
        # self.bushingPositions=[]
        self.arbourThicknesses=[]
        #how much the arbours can wobble back and forth. aka End-shake.
        #2mm seemed a bit much
        self.wobble = 1
        #height of the centre of the wheel that will drive the next pinion
        drivingZ = 0
        for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels +1):
            print(str(i))
            if  i == -self.goingTrain.chainWheels:
                #the wheel with chain wheel ratchet
                #assuming this is at the very back of the clock
                #note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearingPositions.append(pos)
                #note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.goingTrain.getArbour(i).getWheelCentreZ()
                self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())
                print("pinionAtFront: {} wheel {} drivingZ: {}".format(self.goingTrain.getArbour(i).pinionOnTop, i, drivingZ), pos)
            else:
                r = self.goingTrain.getArbour(i - 1).distanceToNextArbour
                print("r", r)
                #all the other going wheels up to and including the escape wheel
                if i == self.goingTrain.wheels:
                    # the anchor
                    baseZ = drivingZ - self.anchorThick / 2
                    self.arbourThicknesses.append(self.anchorThick)
                    print("is anchor")
                else:
                    #any of the other wheels
                    # pinionAtBack = not pinionAtBack
                    print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(), self.goingTrain.getArbour(i).getPinionCentreZ()))
                    pinionToWheel = self.goingTrain.getArbour(i).getPinionToWheelZ()
                    pinionZ = self.goingTrain.getArbour(i).getPinionCentreZ()
                    baseZ = drivingZ - pinionZ

                    drivingZ = drivingZ + pinionToWheel


                    self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())

                if i <= 0:
                    angle = self.anglesFromChain[i - 1 + self.goingTrain.chainWheels]
                else:
                    angle = self.anglesFromMinute[i - 1]
                v = polar(angle, r)
                # v = [v[0], v[1], baseZ]
                lastPos = self.bearingPositions[-1]
                # pos = list(np.add(self.bearingPositions[i-1],v))
                pos = [lastPos[0] + v[0], lastPos[1] + v[1], baseZ]
                if i < self.goingTrain.wheels:
                    print("pinionAtFront: {} wheel {} r: {} angle: {}".format( self.goingTrain.getArbour(i).pinionOnTop, i, r, angle), pos)
                print("baseZ: ",baseZ, "drivingZ ", drivingZ)

                self.bearingPositions.append(pos)


        # print(self.bearingPositions)

        topZs = [self.arbourThicknesses[i] + self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZs = [self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZ = min(bottomZs)
        if bottomZ < 0:
            #positions are relative (chain at front), so readjust everything
            topZs = [z-bottomZ for z in topZs]
            # bottomZs = [z - bottomZ for z in bottomZs]
            for i in range(len(self.bearingPositions)):
                self.bearingPositions[i][2] -= bottomZ

        # print(self.bearingPositions)
        self.plateDistance=max(topZs) + self.wobble

        print("Plate distance", self.plateDistance)

        motionWorksDistance = self.motionWorks.getArbourDistance()
        #get position of motion works relative to the minute wheel
        if style == "round":
            #place the motion works on the same circle as the rest of the bearings
            angle =  2*math.asin(motionWorksDistance/(2*self.compactRadius))
            compactCentre = (0, self.compactRadius)
            minuteAngle = math.atan2(self.bearingPositions[self.goingTrain.chainWheels][1] - compactCentre[1], self.bearingPositions[self.goingTrain.chainWheels][0] - compactCentre[0])
            motionWorksPos = polar(minuteAngle - angle, self.compactRadius)
            motionWorksPos=(motionWorksPos[0] + compactCentre[0], motionWorksPos[1] + compactCentre[1])
            self.motionWorksRelativePos = (motionWorksPos[0] - self.bearingPositions[self.goingTrain.chainWheels][0], motionWorksPos[1] - self.bearingPositions[self.goingTrain.chainWheels][1])
        else:
            #motion works is directly below the minute rod
            self.motionWorksRelativePos = [0, -motionWorksDistance]

        self.chainHoleD = self.goingTrain.chainWheel.chain_width + 2


    def getPlate(self, back=True, getText=False):
        '''
        Two plates that are almost idential, with pillars at the very top and bottom to hold them together.
        Designed to be flat up against the wall, with everything offset to avoid the wall and picture rail

        styles: round or vertical
        round minimises total height by placing the gear train in a circle, so more complicated clocks can still fit on the print bed
        vertical just has everything directly above each other.

        The screwhole is placed directly above the weight to make the clock easier to hang straight

        '''

        #width of thin bit
        holderWide =  self.bearingOuterD + self.bearingWallThick*2



        chainWheelR = self.goingTrain.getArbour(-self.goingTrain.chainWheels).getMaxRadius() + self.gearGap

        plate = cq.Workplane("XY").tag("base")
        if self.style=="round":
            radius = self.compactRadius + holderWide / 2
            #the ring that holds the gears
            plate = plate.moveTo(self.bearingPositions[0][0], self.bearingPositions[0][1] + self.compactRadius).circle(radius).circle(radius - holderWide).extrude(self.plateThick)
        elif self.style == "vertical":
            #rectangle that just spans from the top bearing to the bottom pillar (so we can vary the width of the bottom section later)
            plate = plate.moveTo(self.bearingPositions[0][0]-holderWide/2, self.bearingPositions[0][1] - chainWheelR).line(holderWide,0).\
                lineTo(self.bearingPositions[-1][0]+holderWide/2, self.bearingPositions[-1][1]).line(-holderWide,0).close().extrude(self.plateThick)

        bottomPillarR= self.plateDistance/2
        topPillarR = holderWide/2



        weightOnSide = 1 if self.goingTrain.chainWheels % 2 == 0 else -1

        if self.style == "round":
            screwHoleY = chainWheelR*1.4
        elif self.style == "vertical":
            screwHoleY = self.bearingPositions[-3][1] + (self.bearingPositions[-2][1] - self.bearingPositions[-3][1])*0.6

        # line up the hole with the big heavy weight
        screwHolePos = (weightOnSide*self.goingTrain.chainWheel.diameter/2, screwHoleY)

        #find the Y position of the bottom of the top pillar
        topY = self.bearingPositions[0][1]
        if self.style == "round":
            #find the highest point on the going train
            #TODO for potentially large gears this might be lower if they're spaced right
            for i in range(len(self.bearingPositions)-1):
                y = self.bearingPositions[i][1] + self.goingTrain.getArbourWithConventionalNaming(i).getMaxRadius() + self.gearGap
                if y > topY:
                    topY = y
        else:
            anchorSpace = self.bearingOuterD / 2 + self.gearGap
            topY = self.bearingPositions[-1][1] + anchorSpace

        bottomPillarPos = [self.bearingPositions[0][0], self.bearingPositions[0][1] - chainWheelR - bottomPillarR]
        topPillarPos = [self.bearingPositions[0][0], topY + topPillarR]
        #where the extra-wide bit of the plate stops
        topOfBottomBitPos = self.bearingPositions[0]


        fixingPositions = [(topPillarPos[0] -topPillarR / 2, topPillarPos[1]), (topPillarPos[0] + topPillarR / 2, topPillarPos[1]), (bottomPillarPos[0], bottomPillarPos[1] + bottomPillarR * 0.5), (bottomPillarPos[0], bottomPillarPos[1] - bottomPillarR * 0.5)]


        #supports all the combinations of round/vertical and chainwheels or not
        topRound = self.style == "vertical"
        narrow = self.goingTrain.chainWheels == 0
        bottomBitWide = holderWide if narrow else bottomPillarR*2

        #link the bottom pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(topOfBottomBitPos[0] - bottomBitWide/2, topOfBottomBitPos[1])
        if topRound:
            # do want the wide bit nicely rounded
            plate = plate.radiusArc((topOfBottomBitPos[0] + bottomBitWide/2, topOfBottomBitPos[1]), bottomBitWide/2)
        else:
            # square top
            plate = plate.line(bottomBitWide, 0)

        #just square, will pop a round bit on after
        plate = plate.lineTo(bottomPillarPos[0] + bottomBitWide/2, bottomPillarPos[1]).line(-bottomBitWide,0)

        plate = plate.close().extrude(self.plateThick)

        plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR).extrude(self.plateThick)



        if self.style == "round":
            #centre of the top of the ring
            topOfPlate = (self.bearingPositions[0][0], self.bearingPositions[0][1] + self.compactRadius * 2)
        elif self.style == "vertical":
            #topmost bearing
            topOfPlate = self.bearingPositions[-1]

        # link the top pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - topPillarR, topOfPlate[1]) \
            .lineTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR) \
            .lineTo(topOfPlate[0] + topPillarR, topOfPlate[1]).close().extrude(self.plateThick)

        if back:
            #extra bit around the screwhole
            #r = self.goingTrain.chainWheel.diameter*1.25
            plate = plate.workplaneFromTagged("base").moveTo(screwHolePos[0], screwHolePos[1]).circle(holderWide).extrude(self.plateThick)

            #the pillars
            plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR*0.9999).extrude(self.plateThick + self.plateDistance)
            plate = plate.workplaneFromTagged("base").moveTo(topPillarPos[0], topPillarPos[1]).circle(topPillarR*0.9999).extrude(self.plateThick + self.plateDistance)

            textMultiMaterial = cq.Workplane("XY")
            textSize = bottomPillarR * 0.5
            textY = (self.bearingPositions[0][1] + fixingPositions[2][1])/2
            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{} {:.1f}".format(self.name, self.goingTrain.pendulum_length * 100), (-textSize*0.7, textY), textSize)

            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{}".format(datetime.date.today().strftime('%Y-%m-%d')), (textSize*0.8, textY), textSize)

            if getText:
                return textMultiMaterial

        plate = self.punchBearingHoles(plate, back)


        if back:

            plate = self.addScrewHole(plate, screwHolePos , backThick=5, screwHeadD=11)

            chainHoles = self.getChainHoles()
            plate = plate.cut(chainHoles)
        else:
           plate = self.frontAdditionsToPlate(plate)

        fixingScrewD = 3

        #screws to fix the plates together
        plate = plate.faces(">Z").workplane().pushPoints(fixingPositions).circle(fixingScrewD / 2).cutThruAll()

        embeddedNutHeight = self.plateThick + self.plateDistance/2
        for fixingPos in fixingPositions:
            #embedded nuts!
            plate = plate.cut(getHoleWithHole(fixingScrewD,getNutContainingDiameter(fixingScrewD,0.2), getNutHeight(fixingScrewD)*1.4, sides=6).translate((fixingPos[0], fixingPos[1], embeddedNutHeight)))

        return plate

    def getChainHoles(self, absoluteZ=False):
        '''
        if absolute Z is false, these are positioned above the base plateThick
        '''
        chainZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - self.goingTrain.chainWheel.getHeight() / 2 + self.wobble/2

        if not absoluteZ:
            chainZ += self.plateThick

        chainHoles = cq.Workplane("XZ").pushPoints([(self.goingTrain.chainWheel.diameter / 2, chainZ), (-self.goingTrain.chainWheel.diameter / 2, chainZ)]).circle(self.chainHoleD / 2).extrude(1000)

        return chainHoles

    def getBearingHolder(self, height, addSupport=True):
        #height from base (outside) of plate, so this is inclusive of base thickness, not in addition to

        wallThick = self.bearingWallThick
        diameter = self.bearingOuterD + wallThick*2
        holder = cq.Workplane("XY").circle(diameter/2).circle(self.holderInnerD/2).extrude(height - self.bearingHeight)


        holder = holder.faces(">Z").workplane().circle(diameter/2).circle(self.bearingOuterD/2).extrude(self.bearingHeight)
        # extra support?
        if addSupport:
            support = cq.Workplane("YZ").moveTo(-self.bearingOuterD/2,0).lineTo(-height-self.bearingOuterD/2,0).lineTo(-self.bearingOuterD/2,height).close().extrude(wallThick).translate([-wallThick/2,0,0])
            holder = holder.add(support)

        return holder

    def getBearingPunch(self, bearingOnTop=True):
        '''
        A shape that can be cut out of a clock plate to hold a bearing
        '''

        height = self.plateThick

        if bearingOnTop:
            punch = cq.Workplane("XY").circle(self.holderInnerD/2).extrude(height - self.bearingHeight)
            punch = punch.faces(">Z").workplane().circle(self.bearingOuterD/2).extrude(self.bearingHeight)
        else:
            punch = getHoleWithHole(self.holderInnerD,self.bearingOuterD, self.bearingHeight).faces(">Z").workplane().circle(self.holderInnerD/2).extrude(height - self.bearingHeight)

        return punch

    def punchBearingHoles(self, plate, back):
        for i, pos in enumerate(self.bearingPositions):
            if i == len(self.bearingPositions)-1 and not back and self.pendulumSticksOut > 0:
                #don't need three bearings for the anchor - it's not taking much weight! Just using one on the end of the pendulumSticksOut bit so it can't bend as easily
                plate = plate.cut(cq.Workplane("XY").circle(self.holderInnerD/2).extrude(self.plateThick).translate((pos[0], pos[1], 0)))
            else:
                plate = plate.cut(self.getBearingPunch(back).translate((pos[0], pos[1], 0)))
        return plate

    def addScrewHole(self, plate, screwholePos, screwHeadD = 9, screwBodyD = 6, slotLength = 7, backThick = -1):
        '''
        screwholePos is the position the clock will hang from
        this is an upside-down-lollypop shape

        if backThick is default, this cuts through the whole plate
        if not, backthick is the thickness of the plastic around the screw


          /-\   circle of screwBodyD diameter (centre of the circle is the screwholePos)
          |  |  screwbodyD wide
          |  |  distance between teh two circle centres is screwholeHeight
        /     \
        |     |  circle of screwHeadD diameter
        \_____/
        '''

        #big hole
        plate = plate.faces(">Z").workplane().tag("top").moveTo(screwholePos[0], screwholePos[1] - slotLength).circle(screwHeadD / 2).cutThruAll()
        #slot
        plate = plate.workplaneFromTagged("top").moveTo(screwholePos[0], screwholePos[1] - slotLength/2).rect(screwBodyD, slotLength).cutThruAll()
        # small hole
        plate = plate.workplaneFromTagged("top").moveTo(screwholePos[0], screwholePos[1]).circle(screwBodyD / 2).cutThruAll()

        if backThick > 0:
            extraY = screwBodyD*0.5
            cutter = cq.Workplane("XY").moveTo(screwholePos[0], screwholePos[1] + extraY).circle(screwHeadD/2).extrude(self.plateThick - backThick).translate((0,0,backThick))
            cutter = cutter.add(cq.Workplane("XY").moveTo(screwholePos[0], screwholePos[1] - slotLength / 2 + extraY/2).rect(screwHeadD, slotLength+extraY).extrude(self.plateThick - backThick).translate((0, 0, backThick)))
            plate = plate.cut(cutter)

        return plate

    def addText(self,plate, multimaterial, text, pos, textSize):
        # textSize =  width*0.25
        # textYOffset = width*0.025
        y = pos[1]
        textYOffset = 0  + pos[0]# width*0.1
        text = cq.Workplane("XY").moveTo(0, 0).text(text, textSize, LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotateAboutCenter((0, 0, 1), 90).rotateAboutCenter((1, 0, 0), 180).translate((textYOffset, y, 0))

        return plate.cut(text), multimaterial.add(text)

    def frontAdditionsToPlate(self, plate):
        '''
        stuff shared between all plate designs
        '''
        plateThick = self.plateThick
        # FRONT

        # note - works fine with the pendulum on the same rod as teh anchor, but I'm not sure about the long term use of ball bearings for just rocking back and forth
        # suspensionBaseThick=0.5
        # suspensionPoint = self.pendulum.getSuspension(False,suspensionBaseThick ).translate((self.bearingPositions[len(self.bearingPositions)-1][0], self.bearingPositions[len(self.bearingPositions)-1][1], plateThick-suspensionBaseThick))
        #         #
        #         # plate = plate.add(suspensionPoint)
        # new plan: just put the pendulum on the same rod as the anchor, and use nyloc nuts to keep both firmly on the rod.
        # no idea if it'll work without the rod bending!

        if self.pendulumSticksOut > 0:
            #trying this WITHOUT the support
            extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, False).translate((self.bearingPositions[len(self.bearingPositions) - 1][0], self.bearingPositions[len(self.bearingPositions) - 1][1], plateThick))
            plate = plate.add(extraBearingHolder)

        plate = plate.faces(">Z").workplane().moveTo(self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1]).circle(
            self.arbourD / 2).cutThruAll()
        nutDeep = METRIC_HALF_NUT_DEPTH_MULT * self.arbourD
        nutSpace = cq.Workplane("XY").polygon(6, getNutContainingDiameter(self.arbourD)).extrude(nutDeep).translate(
            (self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1], plateThick - nutDeep))

        plate = plate.cut(nutSpace)

        if self.dial is not None:
            dialFixings = self.dial.getFixingDistance()
            minuteY = self.bearingPositions[self.goingTrain.chainWheels][1]
            plate = plate.faces(">Z").workplane().pushPoints([(0, minuteY + dialFixings / 2), (0, minuteY - dialFixings / 2)]).circle(self.dial.fixingD / 2).cutThruAll()

        return plate

    def getArbourExtension(self, arbourID, top=True, arbourD=3):
        '''
        Get little cylinders we can use as spacers to keep the gears in the right place on the rod
        arbour from -chainwheels to +ve wheels + 1 (for the anchor)
        returns None if no extension is needed
        '''
        bearingPos = self.bearingPositions[arbourID + self.goingTrain.chainWheels]
        if arbourID < self.goingTrain.wheels:
            arbourThick = self.goingTrain.getArbour(arbourID).getTotalThickness()
        else:
            #anchor!
            arbourThick = self.pendulum.anchorThick

        length = 0
        if top:
            length = self.plateDistance - arbourThick - bearingPos[2] - self.wobble
        else:
            length = bearingPos[2]

        if length > LAYER_THICK:
            return  cq.Workplane("XY").circle(arbourD).circle(arbourD/2).extrude(length)
        return None



    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_front_plate.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(False), out)

        out = os.path.join(path, "{}_back_plate_platecolour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True), out)
        out = os.path.join(path, "{}_back_plate_textcolour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True, True), out)

        for arbour in range(-self.goingTrain.chainWheels, self.goingTrain.wheels+1):
            for top in [True, False]:
                extensionShape=self.getArbourExtension(arbour, top=top)
                if extensionShape is not None:
                    out = os.path.join(path, "{}_arbour_{}_{}_extension.stl".format(name, arbour, "top" if top else "bottom"))
                    print("Outputting ", out)
                    exporters.export(extensionShape, out)

class Pendulum:
    '''
    Class to generate the anchor&crutch arbour and pendulum parts
    '''
    def __init__(self, escapement, length, clockwise=False, crutchLength=50, anchorThick=10, anchorAngle=-math.pi/2, anchorHoleD=2, crutchBoltD=3, suspensionScrewD=3, threadedRodM=3, nutMetricSize=0, handAvoiderInnerD=100, bobD=100, bobThick=15, useNylocForAnchor=True):
        self.escapement = escapement
        self.crutchLength = crutchLength
        self.anchorAngle = anchorAngle
        self.anchorThick=anchorThick

        #nominal length of the pendulum
        self.length = length
        # self.crutchWidth = 9

        #if true, we're using a nyloc nut to fix the anchor to the rod, if false we're not worried about fixing it, or we're using glue
        self.useNylocForAnchor=useNylocForAnchor

        #space for a nut to hold the anchor to the rod
        self.nutMetricSize=nutMetricSize

        self.anchor = self.escapement.getAnchorArbour(holeD=anchorHoleD, anchorThick=anchorThick, clockwise=clockwise, arbourLength=0, crutchLength=crutchLength, crutchBoltD=crutchBoltD, pendulumThick=threadedRodM, nutMetricSize=nutMetricSize if useNylocForAnchor else 0)

        self.crutchSlackWidth=crutchBoltD*1.5
        self.crutchSlackHeight = 30
        self.suspensionD=20
        self.pendulumTopD = self.suspensionD*1.75
        self.pendulumTopExtraRadius = 5
        self.pendulumTopThick = 15#getNutContainingDiameter(threadedRodM) + 2
        self.handAvoiderThick = getNutContainingDiameter(threadedRodM) + 2
        self.threadedRodM=threadedRodM

        self.suspensionOpenAngle=degToRad(120)
        self.knifeEdgeAngle = self.suspensionOpenAngle*0.25
        self.suspension_length=25
        self.suspension_cap_length=2
        self.suspension_cap_d = self.suspensionD*1.2
        self.thick = 5
        self.suspensionScrewD=suspensionScrewD

        self.suspensionAttachmentPoints=[(-20,25),(20,25)]

        self.handAvoiderInnerD=handAvoiderInnerD

        self.bobNutD = bobD*0.3
        self.bobNutThick=bobThick*2/3
        self.bobR=bobD/2
        self.bobThick = bobThick

        self.gapHeight = self.bobNutThick + 0.5
        self.gapWidth = self.bobNutD + 1

        # space to put stuff for extra weight! Will try some steel shot soon
        self.wallThick = 2.5
        self.slotThick = self.wallThick / 2

        #pretty well centred, but might make it hard to fit larger stuff inside!
        #self.bobLidNutPositions=[(self.gapWidth/3, self.bobR*0.55), (-self.gapWidth/3, self.bobR*0.55)]

        self.bobLidNutPositions = [(self.gapWidth / 3, self.bobR * 0.75), (-self.gapWidth / 3, self.bobR * 0.75)]


    def getSuspensionAttachmentHoles(self):
        '''
        get relative positions of the holes used to screw the pendulum suspension to the front/back plate
        '''
        return self.suspensionAttachmentPoints


    def getSuspension(self, withAttachment=True, bottomThick=0):
        '''
        Can be attached to the front plate to hold the weight of the pendulum.
        if withAttachment is false, this is just the knife-edge holder ready to be combined with the clock plate
        Knife-edge rather than suspension spring
        '''

        smallAngle = (math.pi - self.suspensionOpenAngle) / 2

        left = polar(math.pi - smallAngle, self.suspensionD / 2)
        right = polar(smallAngle, self.suspensionD / 2)

        sus = cq.Workplane("XY")
        if withAttachment:
            padding = 7.5
            sus = sus.moveTo(self.suspensionD/2, 0).radiusArc((-self.suspensionD/2,0),self.suspensionD/2).lineTo(self.suspensionAttachmentPoints[0][0]-padding, self.suspensionAttachmentPoints[0][1]).\
                radiusArc((self.suspensionAttachmentPoints[0][0], self.suspensionAttachmentPoints[0][1]+padding), padding).lineTo(self.suspensionAttachmentPoints[1][0], self.suspensionAttachmentPoints[1][1]+padding).\
                radiusArc((self.suspensionAttachmentPoints[1][0] + padding, self.suspensionAttachmentPoints[0][1]), padding).close()

            sus = sus.extrude(self.thick)

            #screw holes
            sus = sus.faces(">Z").pushPoints(self.suspensionAttachmentPoints).circle(self.suspensionScrewD/2).cutThruAll()

            sus = sus.faces(">Z").workplane()
        elif bottomThick > 0:
            sus = sus.moveTo(right[0], right[1]).radiusArc((self.suspensionD / 2, 0), self.suspensionD / 2).radiusArc((-self.suspensionD / 2, 0), self.suspensionD / 2). \
                radiusArc(left, self.suspensionD / 2).close().extrude(bottomThick)
        # width = self.suspensionAttachmentPoints[0][0] - self.suspensionAttachmentPoints[1][0] + padding*2
        # height = self.suspensionAttachmentPoints[0][1] + padding + su



        sus = sus.moveTo(right[0], right[1]).radiusArc((self.suspensionD/2,0),self.suspensionD/2).radiusArc((-self.suspensionD/2,0), self.suspensionD/2).\
            radiusArc(left, self.suspensionD/2).lineTo(0,0).close().extrude(self.suspension_length)

        # sus = sus.faces(">Z").workplane().moveTo(0,0).circle(self.suspension_cap_d/2).extrude(self.suspension_cap_length)
        sus = sus.faces(">Z").workplane().moveTo(right[0], right[1]).radiusArc((self.suspensionD/2,0),self.suspensionD/2).radiusArc((-self.suspensionD/2,0), self.suspensionD/2).\
            radiusArc(left, self.suspensionD/2).close().extrude(self.suspension_cap_length)
        return sus

    def getPendulumForKnifeEdge(self):

        pendulum = cq.Workplane("XY")

        left = polar(math.pi/2 + self.knifeEdgeAngle/2, self.pendulumTopD/2)
        right = polar(math.pi / 2 - self.knifeEdgeAngle / 2, self.pendulumTopD/2)

        #head that knife-edges on the suspension point
        pendulum = pendulum.circle(self.pendulumTopD / 2 + self.pendulumTopExtraRadius).extrude(self.pendulumTopThick)
        pendulum = pendulum.faces(">Z").workplane().moveTo(0,0).lineTo(right[0], right[1]).radiusArc((0,-self.pendulumTopD/2), self.pendulumTopD/2).radiusArc(left, self.pendulumTopD/2).close().cutThruAll()

        #arm to the crutch
        #current plan - have a Y shape from the crutch come to meet the pendulum, which is just the top + a threaded rod
        # top = -self.pendulumTopD/2
        # note - this seems to result in a malformed shape
        # rod = cq.Workplane("XZ").moveTo(0,self.pendulumTopThick/2).circle(self.threadedRodM/2).extrude(100)
        #workaroudn is to use a polygon
        rod = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(20,self.threadedRodM ).extrude(100)
        # return rod

        pendulum = pendulum.cut(rod)

        # pendulum = pendulum.faces("<Y").workplane().circle(self.threadedRodM/2).cutThruAll()#.moveTo(0, self.pendulumTopThick)


        # arm = cq.Workplane("XY").moveTo()

        return pendulum

    def getPendulumForRod(self, holeD=3):
        '''
        Will allow a threaded rod for the pendulum to be attached to threaded rod for the arbour
        '''

        pendulum = cq.Workplane("XY")

        width = holeD*4
        height = holeD*6

        #(0,0,0) is the rod from the anchor, the rod is along the z axis

        holeStartY=-height*0.2
        holeHeight = getNutHeight(self.threadedRodM,nyloc=True) + 1
        holeEndY = holeStartY - holeHeight

        nutD = getNutContainingDiameter(holeD)

        wall_thick = (width - (nutD + 1))/2

        pendulum = pendulum.moveTo(-width/2,0).radiusArc((width/2,0), width/2).line(0,-height).radiusArc((-width/2,-height), width/2).close().extrude(self.pendulumTopThick)

        pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()

        #nut to hold to anchor rod
        nutThick = METRIC_NUT_DEPTH_MULT * holeD
        nutSpace = cq.Workplane("XY").polygon(6,nutD).extrude(nutThick).translate((0,0,self.pendulumTopThick-nutThick))
        pendulum = pendulum.cut(nutSpace)


        # pendulum = pendulum.faces(">Z").moveTo(0,-height*3/4).rect(width-wall_thick*2,height/2).cutThruAll()
        space = cq.Workplane("XY").moveTo(0,holeStartY-holeHeight/2).rect(width-wall_thick*2,holeHeight).extrude(self.pendulumTopThick).translate((0,0,LAYER_THICK*3))
        pendulum = pendulum.cut(space)

        extraSpaceForRod = 0.2
        #
        rod = cq.Workplane("XZ").tag("base").moveTo(0, self.pendulumTopThick / 2).circle(self.threadedRodM/2 + extraSpaceForRod/2).extrude(100)
        # add slot for rod to come in and out
        rod = rod.workplaneFromTagged("base").moveTo(0,self.pendulumTopThick).rect(self.threadedRodM + extraSpaceForRod, self.pendulumTopThick).extrude(100)

        rod = rod.translate((0,holeStartY,0))




        pendulum = pendulum.cut(rod)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(6, nutD+extraSpaceForRod).extrude(nutThick).translate((0,holeStartY-holeHeight,0))
        pendulum = pendulum.cut(nutSpace2)


        return pendulum

    # def getPendulumForRod(self, holeD=3):
    #     '''
    #     Attaches to a threaded rod and provides something for the pendulum to slot over in a detachable way
    #     '''
    #
    #     pendulum = cq.Workplane("XY")
    #
    #
    #
    #
    #
    #     nutD = getNutContainingDiameter(holeD)
    #
    #     wall_thick = (width - (nutD + 1))/2
    #
    #     pendulum = pendulum.rect(width, height ).extrude(self.pendulumTopThick)
    #
    #     #hole for rod
    #     pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()
    #
    #     #nut to hold to anchor rod
    #     nutThick = METRIC_NUT_DEPTH_MULT * holeD
    #     nutSpace = cq.Workplane("XY").polygon(6,nutD).extrude(nutThick).translate((0,0,self.pendulumTopThick-nutThick))
    #     pendulum = pendulum.cut(nutSpace)




        return pendulum

    def getHandAvoider(self):
        '''
        Get a circular part which attaches inline with pendulum rod, so it can go over the hands (for a front-pendulum)
        '''
        extraR=5
        avoider = cq.Workplane("XY").circle(self.handAvoiderInnerD/2).circle(self.handAvoiderInnerD/2 + extraR).extrude(self.handAvoiderThick)

        nutD = getNutContainingDiameter(self.threadedRodM)
        nutThick = METRIC_NUT_DEPTH_MULT * self.threadedRodM

        nutSpace = cq.Workplane("XZ").moveTo(0, self.handAvoiderThick/2).polygon(6, nutD).extrude(nutThick).translate((0, -self.handAvoiderInnerD/2+0.5, 0))
        avoider = avoider.cut(nutSpace)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.handAvoiderThick / 2).polygon(6, nutD).extrude(nutThick).translate((0, self.handAvoiderInnerD / 2 +nutThick - 0.5, 0))
        avoider = avoider.cut(nutSpace2)

        avoider = avoider.faces(">Y").workplane().moveTo(0,self.handAvoiderThick/2).circle(self.threadedRodM/2).cutThruAll()

        return avoider


    def getCrutchExtension(self):
        '''
        Attaches to the bottom of the anchor to finish linking the crutch to the pendulum
        '''


    def getBob(self):


        circle = cq.Workplane("XY").circle(self.bobR)

        #nice rounded edge
        bob = cq.Workplane("XZ").lineTo(self.bobR,0).radiusArc((self.bobR,self.bobThick),-self.bobThick*0.9).lineTo(0,self.bobThick).close().sweep(circle)

        #was 0.5, which is plenty of space, but can slowly rotate. 0.1 seems to be a tight fit that help stop it rotate over time
        extraR=0.1



        #rectangle for the nut, with space for the threaded rod up and down
        cut = cq.Workplane("XY").rect(self.gapWidth, self.gapHeight).extrude(self.bobThick*2).faces(">Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+extraR).extrude(self.bobR*2).\
            faces("<Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+extraR).extrude(self.bobR*2)
        bob=bob.cut(cut)

        #could make hollow with shell, but that might be hard to print, so doing it manually
        # bob = bob.shell(-2)


        #
        # startAngle =
        #
        # weightHole = cq.Workplane("XY").moveTo(self.threadedRodM/2 + self.wallThick, self.bobR - self.wallThick).radiusArc((self.threadedRodM/2 + self.wallThick, -self.bobR + self.wallThick), self.bobR-self.wallThick).\
        #     lineTo(self.threadedRodM/2 + self.wallThick, -gapHeight/2 - self.wallThick).line(gapWidth/2 + self.wallThick,0).line(0,gapHeight + self.wallThick*2).line(-gapWidth/2 - self.wallThick,0)\
        #     .close().extrude(self.bobThick).translate((0,0,self.wallThick))
        weightHole = cq.Workplane("XY").circle(self.bobR - self.wallThick).extrude(self.bobThick-self.wallThick*2).translate((0,0,self.wallThick))

        notHole = cut.shell(self.wallThick)
        #don't have a floating tube through the middle, give it something below
        notHole = notHole.add(cq.Workplane("XY").rect(self.threadedRodM+extraR*2 + self.wallThick*2, self.bobR*2).extrude(self.bobThick/2 - self.wallThick).translate((0,0,self.wallThick)))

        for pos in self.bobLidNutPositions:
            notHole = notHole.add(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(self.nutMetricSize*1.5).circle(self.nutMetricSize/2).extrude(self.bobThick-self.wallThick))

        weightHole = weightHole.cut(notHole)

        lid = self.getBobLid(True)

        weightHole = weightHole.add(lid.translate((0,0,self.bobThick-self.wallThick)))

        #
        bob = bob.cut(weightHole)

        return bob

    def getBobLid(self, forCutting=False):
        '''
        extraslot size for the slot, but not for the lid itself
        '''

        wallThick = self.wallThick
        slotThick = self.slotThick

        if not forCutting:
            #reduce size a tiny bit so it can fit into the slot
            slotThick-=0.2
            wallThick+=0.2

        # add space for a lid
        # don't want the whole of the back open, just some
        angle = math.acos((self.gapWidth / 2) / (self.bobR - wallThick))
        angle2 = math.acos((self.gapWidth / 2 + slotThick) / (self.bobR - wallThick + slotThick))
        lid = cq.Workplane("XY").moveTo(self.gapWidth / 2, self.gapHeight / 2 + wallThick).lineTo(self.gapWidth / 2, math.sin(angle) * (self.bobR - wallThick)). \
            radiusArc((-self.gapWidth / 2, math.sin(angle) * (self.bobR - wallThick)), -(self.bobR - wallThick)).lineTo(-self.gapWidth / 2, self.gapHeight / 2 + wallThick).close().extrude(wallThick - slotThick)
        lid = lid.faces(">Z").workplane().moveTo(self.gapWidth / 2 + slotThick, self.gapHeight / 2 + wallThick - slotThick).lineTo(math.cos(angle2) * (self.bobR - wallThick + slotThick),
                                                                                                                                   math.sin(angle2) * (self.bobR - wallThick + slotThick)). \
            radiusArc((-math.cos(angle2) * (self.bobR - wallThick + slotThick), math.sin(angle2) * (self.bobR - wallThick + slotThick)), -(self.bobR - wallThick + slotThick)).lineTo(-self.gapWidth / 2 - slotThick,
                                                                                                                                                                                      self.gapHeight / 2 + wallThick - slotThick).close().extrude(
            wallThick - slotThick)
        if not forCutting:
            for pos in self.bobLidNutPositions:
                lid =  lid.faces(">Z").workplane().moveTo(pos[0], pos[1]).circle(self.nutMetricSize/2).cutThruAll()

        return lid

    def getBobNut(self):
        #TODO consider calculating how much time+- a single segment might be
        segments = 20
        knobbleR = self.bobNutD/30
        r=self.bobNutD/2 - knobbleR

        knobbleAngle = knobbleR*2/r
        # nonSegmentAngle=math.pi*2/segments - segmentAngle

        nut = cq.Workplane("XY").moveTo(r,0)

        dA = math.pi*2 / segments

        for i in range(segments):
            angle = dA * i
            start = polar(angle, r)
            nobbleStart = polar(angle + dA - knobbleAngle, r)
            nobbleEnd = polar(angle + dA, r)
            nut = nut.radiusArc(nobbleStart,-r)
            nut = nut.radiusArc(nobbleEnd, -knobbleR)
        nut = nut.close().extrude(self.bobNutThick).faces(">Z").workplane().circle(self.threadedRodM/2+0.25).cutThruAll()

        # currently assuming M3
        nutD=getNutContainingDiameter(3, 0.1)
        #and going to try a nyloc nut to see if that stops it untightening itself
        nutHeight=getNutHeight(3,nyloc=True)

        nutSpace=cq.Workplane("XY").polygon(6,nutD).extrude(nutHeight).translate((0,0,self.bobNutThick-nutHeight))

        nut = nut.cut(nutSpace)

        # nut = cq.Workplane("XY").polygon(20,self.bobNutD/2)
        #TODO print in place nut
        return nut

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_anchor.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.anchor, out)

        out = os.path.join(path, "{}_suspension.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getSuspension(), out)

        out = os.path.join(path, "{}_pendulum_for_knife_edge.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPendulumForKnifeEdge(), out)#,tolerance=0.01)

        out = os.path.join(path, "{}_pendulum_for_rod.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPendulumForRod(), out)

        out = os.path.join(path, "{}_pendulum_hand_avoider.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHandAvoider(), out)

        out = os.path.join(path, "{}_bob.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getBob(), out)

        out = os.path.join(path, "{}_bob_nut.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getBobNut(), out)

        out = os.path.join(path, "{}_bob_lid.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getBobLid(), out)


class Hands:
    def __init__(self, style="simple", minuteFixing="rectangle", hourFixing="circle", minuteFixing_d1=1.5, minuteFixing_d2=2.5, hourfixing_d=3, length=25, thick=1.6, fixing_offset=0, outline=0, outlineSameAsBody=True, handNutMetricSize=3):
        '''

        '''
        self.thick=thick
        #usually I print multicolour stuff with two layers, but given it's entirely perimeter I think it will look okay with just one
        self.outlineThick=LAYER_THICK
        #how much to rotate the minute fixing by
        self.fixing_offset=fixing_offset
        self.length = length
        # self.width = length * 0.3
        # self.end_d = self.width * 0.1
        self.style=style
        #for the hour hand,
        self.minuteFixing=minuteFixing
        self.minuteFixing_d1 = minuteFixing_d1
        self.minuteFixing_d2 = minuteFixing_d2
        #Add a different coloured outline that is this many mm ratchetThick
        self.outline = outline
        #if true the outline will be part of the same STL as the main body, if false, it'll just be a small sliver
        self.outlineSameAsBody = outlineSameAsBody
        self.handNutMetricSize=handNutMetricSize

        if self.minuteFixing == "square":
            self.minuteFixing_d2 = self.minuteFixing_d1
            self.minuteFixing="rectangle"

        self.hourFixing=hourFixing
        self.hourFixing_d = hourfixing_d
        #the found bit that attaches to the clock
        self.base_r = length * 0.12

        if self.style == "square":
            self.base_r /= 2

        #ensure it's actually big enoguh to fit onto the fixing
        if self.base_r < minuteFixing_d1 * 0.7:
            self.base_r = minuteFixing_d1 * 1.5 / 2

        if self.base_r < minuteFixing_d2 * 0.7:
            self.base_r = minuteFixing_d2 * 1.5 / 2

        if self.base_r < hourfixing_d * 0.7:
            self.base_r = hourfixing_d * 1.5 / 2

    def getHandNut(self):
        #fancy bit to hide the actual nut
        r = self.handNutMetricSize*2.5
        height = r*0.75


        circle = cq.Workplane("XY").circle(r)
        nut = cq.Workplane("XZ").moveTo(self.handNutMetricSize/2,0).lineTo(r,0).line(0,height*0.25).lineTo(self.handNutMetricSize/2,height).close().sweep(circle)

        nutSpace = getHoleWithHole(innerD=self.handNutMetricSize,outerD=getNutContainingDiameter(self.handNutMetricSize),sides=6, deep=getNutHeight(self.handNutMetricSize))

        nut = nut.cut(nutSpace)

        return nut

    def getHand(self, hour=True, outline=False):
        '''
        if hour is true this ist he hour hand
        if outline is true, this is just the bit of the shape that should be printed in a different colour
        '''
        length = self.length
        # width = self.length * 0.3
        if hour:
            length = self.length * 0.8
            # if self.style == "simple":
            #     width = width * 1.2
            # if self.style == "square":
            #     width = width * 1.75



        hand = cq.Workplane("XY").tag("base").circle(radius=self.base_r).extrude(self.thick)
        # hand = hand.workplaneFromTagged("base").moveTo(0,length/2).rect(length*0.1,length).extrude(ratchetThick)

        if self.style == "simple":
            width = self.length * 0.1
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(width, length).extrude(self.thick)
        elif self.style == "simple_rounded":
            width = self.length * 0.1
            hand = hand.workplaneFromTagged("base").moveTo(width/2, 0).line(0,length).radiusArc((-width/2,length),-width/2).line(0,-length).close().extrude(self.thick)
        elif self.style == "square":
            handWidth = self.length * 0.3 * 0.25
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(handWidth, length).extrude(self.thick)
        elif self.style == "cuckoo":

            end_d = self.length * 0.3 * 0.1
            centrehole_y = length * 0.6
            width = self.length * 0.3
            centrehole_r = width * 0.15

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).threePointArc((end_d *0.75, length/2),(end_d / 2, length)).radiusArc(
            #    (-end_d / 2, length), -end_d / 2).threePointArc((-end_d *0.75, length/2),(-width * 0.4, 0)).close().extrude(ratchetThick)

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.25, length*0.3).lineTo(end_d / 2, length).radiusArc(
            #     (-end_d / 2, length), -end_d / 2).lineTo(-width * 0.25, length*0.3).close().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(width * 0.2, length * 0.3).lineTo(end_d / 2, length).threePointArc((0, length + end_d / 2), (-end_d / 2, length)).lineTo(-width * 0.2, length * 0.3).close().extrude(self.thick)

            # extra round bits towards the end of the hand
            little_sticky_out_dist = width * 0.3
            little_sticky_out_d = width * 0.35
            little_sticky_out_y = centrehole_y - centrehole_r * 0.4
            little_sticky_out_d2 = width * 0.125
            little_sticky_out_dist2 = width * 0.2
            stickyoutblobs = hand.workplaneFromTagged("base")
            # the two smaller blobs, justcircles
            for angle_d in [45]:
                angle = math.pi * angle_d / 180
                # just circle, works but needs more
                stickyoutblobs = stickyoutblobs.moveTo(0 + math.cos(angle) * little_sticky_out_dist2, centrehole_y + little_sticky_out_d2 * 0.25 + math.sin(angle) * little_sticky_out_dist2).circle(little_sticky_out_d2)
                # hand =  hand.workplaneFromTagged("base").moveTo(0+math.cos(angle+math.pi/2)*little_sticky_out_d/2,centrehole_y+math.sin(angle+math.pi/2)*little_sticky_out_d/2).lineTo()
                # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y).rot
            hand = stickyoutblobs.mirrorY().extrude(self.thick)

            # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y-centrehole_r).spline([(little_sticky_out_dist*1.6,centrehole_y-little_sticky_out_d*0.6),(little_sticky_out_dist*1.6,centrehole_y+little_sticky_out_d*0.2),(0,centrehole_y)],includeCurrent=True)\
            #     .mirrorY().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(0, little_sticky_out_y - little_sticky_out_d / 2 + little_sticky_out_d * 0.1).lineTo(little_sticky_out_dist, little_sticky_out_y - little_sticky_out_d / 2).threePointArc(
                (little_sticky_out_dist + little_sticky_out_d / 2, little_sticky_out_y), (little_sticky_out_dist, little_sticky_out_y + little_sticky_out_d / 2)).line(-little_sticky_out_dist, 0) \
                .mirrorY().extrude(self.thick)

            petalend = (width * 0.6, length * 0.45)

            # petal-like bits near the centre of the hand
            hand = hand.workplaneFromTagged("base").lineTo(width * 0.1, 0).spline([(petalend[0] * 0.3, petalend[1] * 0.1), (petalend[0] * 0.7, petalend[1] * 0.4), (petalend[0] * 0.6, petalend[1] * 0.75), petalend], includeCurrent=True) \
                .line(0, length * 0.005).spline([(petalend[0] * 0.5, petalend[1] * 0.95), (0, petalend[1] * 0.8)], includeCurrent=True).mirrorY()
            # return hand
            hand = hand.extrude(self.thick)

            # sticky out bottom bit for hour hand
            if hour:
                hand = hand.workplaneFromTagged("base").lineTo(width * 0.4, 0).lineTo(0, -width * 0.9).mirrorY().extrude(self.thick)
                # return hand
            # cut bits out
            # roudn bit in centre of knobbly bit
            hand = hand.moveTo(0, centrehole_y).circle(centrehole_r).cutThruAll()
            heartbase = self.base_r + length * 0.025  # length*0.175

            hearttop = length * 0.425
            heartheight = hearttop - heartbase
            heartwidth = length * 0.27 * 0.3  # width*0.3
            # heart shape (definitely not a dick)
            # hand = hand.moveTo(0, heartbase).spline([(heartwidth*0.6,heartbase*0.9),(heartwidth*0.8,heartbase+heartheight*0.15),(heartwidth*0.6,heartbase+heartheight*0.4),(heartwidth*0.3,heartbase + heartheight/2)],includeCurrent=True).lineTo(heartwidth*0.5,heartbase + heartheight*0.75).lineTo(0,hearttop).mirrorY().cutThruAll()
            hand = hand.moveTo(0, heartbase).spline(
                [(heartwidth * 0.6, heartbase * 0.9), (heartwidth * 0.8, heartbase + heartheight * 0.15),
                 (heartwidth * 0.6, heartbase + heartheight * 0.4), (heartwidth * 0.3, heartbase + heartheight / 2)],
                includeCurrent=True).lineTo(heartwidth * 0.5, heartbase + heartheight * 0.75).lineTo(0,
                                                                                                     hearttop).mirrorY()  # .cutThruAll()
            # return hand.extrude(ratchetThick*2)
            hand = hand.cutThruAll()

        # fixing = self.hourFixing if hour else self.minuteFixing

        if self.fixing_offset != 0:
            hand = hand.workplaneFromTagged("base").transformed(rotate=(0, 0,self. fixing_offset))

        if not hour and self.minuteFixing == "rectangle":
            hand = hand.moveTo(0, 0).rect(self.minuteFixing_d1, self.minuteFixing_d2).cutThruAll()
        elif hour and self.hourFixing == "circle":
            hand = hand.moveTo(0, 0).circle(self.hourFixing_d / 2).cutThruAll()
        else:
            raise ValueError("Combination not supported yet")

        if self.outline > 0:
            if outline:

                #this doesn't work for fancier shapes - I think it can't cope if there isn't space to extrude the shell without it overlapping itself?
                #works fine for simple hands, not for cuckoo hands

                # mould = cq.Workplane("XY").rect(self.length*4,self.length*4).extrude(self.thick).cut(hand)
                # #try and make entirely solid so the shell stuff actually works in all cases
                # hand = cq.Workplane("XY").rect(self.length*3,self.length*3).extrude(self.thick).cut(mould)
                # return hand
                # return hand
                # hand = hand.combine(clean=True)
                # return hand
                # hand = hand.shell(self.outline).shell(-self.outline)
                # return hand
                #thinner internal bit
                shell = hand.shell(-self.outline).translate((0,0,-self.outline))
                # return shell
                # return mould
                # shell = mould.shell(-self.outline)

                notOutline = hand.cut(shell)
                # return notOutline
                #chop off the mess above the first few layers that we want

                bigSlab = cq.Workplane("XY").rect(length*3, length*3).extrude(self.thick).translate((0,0,self.outlineThick))



                if self.outlineSameAsBody:
                    notOutline = notOutline.cut(bigSlab)
                else:
                    notOutline = notOutline.add(bigSlab)

                hand = hand.cut(notOutline)

            else:
                #chop out the outline from the shape
                hand = hand.cut(self.getHand(hour, outline=True))

        return hand


    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_hour_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(True), out)

        out = os.path.join(path, "{}_minute_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(False), out)

        out = os.path.join(path, "{}_hand_nut.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHandNut(), out)

        if self.outline > 0:
            out = os.path.join(path, "{}_hour_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(True, outline=True), out)

            out = os.path.join(path, "{}_minute_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(False, outline=True), out)

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass

class Dial:
    '''
    WIP
    '''
    def __init__(self, outsideD, hollow=True, style="simple", fixingD=3, supportLength=0):
        self.outsideD=outsideD
        self.hollow = hollow
        self.style = style
        self.fixingD=fixingD
        self.supportLength=supportLength
        self.thick = 3

    def getFixingDistance(self):
        return self.outsideD - self.fixingD*4

    def getDial(self):
        r = self.outsideD / 2

        bigLineThick=3
        smallLineThick=1

        bigAngle = math.asin((bigLineThick/2)/r)*2
        smallAngle = math.asin((smallLineThick / 2) / r) * 2

        lineThick = LAYER_THICK*2

        innerR = r*0.8

        dial = cq.Workplane("XY").circle(r).circle(innerR).extrude(self.thick)

        dial = dial.faces(">Z").workplane().tag("top")

        lines = 60

        dA = math.pi*2/lines

        fromEdge = self.outsideD*0.01

        lineInnerR = innerR + fromEdge
        lineOuterR = r - fromEdge

        for i in range(lines):
            big = i % 5 == 0
            # big=True
            lineAngle = bigAngle if big else smallAngle
            angle = math.pi/2 - i*dA

            # if not big:
            #     continue

            bottomLeft=polar(angle - lineAngle/2, lineInnerR)
            bottomRight=polar(angle + lineAngle/2, lineInnerR)
            topRight=polar(angle + lineAngle/2, lineOuterR)
            topLeft=polar(angle - lineAngle / 2, lineOuterR)
            #keep forgetting cq does not line shapes that line up perfectly, so have a 0.001 bodge... again
            dial = dial.workplaneFromTagged("top").moveTo(bottomLeft[0], bottomLeft[1]).radiusArc(bottomRight, 0.001-innerR).lineTo(topRight[0], topRight[1]).radiusArc(topLeft, r-0.001).close().extrude(lineThick)
            # dial = dial.workplaneFromTagged("top").moveTo(bottomLeft[0], bottomLeft[1]).lineTo(bottomRight[0], bottomRight[1]).lineTo(topRight[0], topRight[1]).lineTo(topLeft[0], topLeft[1]).close().extrude(lineThick)

        return dial

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_dial.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getDial(), out)

class Weight:

    # @staticmethod
    # def getMaxWeightForDimensions(h, d, wallThick=3):
    #     r = (d / 2 - wallThick * 2) / 1000
    #     h = (h - wallThick * 2) / 1000
    #     # in litres
    #     volume = math.pi * r * r * h * 1000

    def __init__(self, height=100, diameter=38, boltMetricSize=3, wallThick=2.7, boltThreadLength=30):
        '''
        34mm diameter fits nicely with a 40mm m3 screw
        38mm diameter results in a weight of ~0.3kg
        wallThick of 2.6 should result in no infill with three layers of walls
        '''



        self.height=height
        self.diameter=diameter
        self.boltMetricSize=boltMetricSize
        self.boltThreadLength=boltThreadLength
        self.wallThick=wallThick
        # self.baseThick=4
        self.slotThick = self.wallThick/3
        self.lidWidth = self.diameter * 0.3

    def printInfo(self):
        vol = self.getVolume_L()
        weight = self.getMaxWeight()
        print("Volume: {:.3f}L Weight Aprox: {:.3f}kg".format(vol, weight))

    def getVolume_L(self):
        # get everything in metres
        r = (self.diameter / 2 - self.wallThick * 2) / 1000
        h = (self.height - self.wallThick * 2) / 1000
        # in litres
        volume = math.pi * r * r * h * 1000

        return volume
    def getMaxWeight(self, density = STEEL_SHOT_DENSITY):
        '''
        calculate maximum weight (in kg) this could fit, ignoring lots of details
        '''
        weight = density * self.getVolume_L()

        return weight

    def getWeight(self):
        '''
        get the body of teh weight
        '''
        #main body of the weight
        weight = cq.Workplane("XY").circle(self.diameter/2).extrude(self.height).shell(-self.wallThick)

        # hole to fill with shot
        lidHole = self.getLid(True).translate((0,0,self.height - self.wallThick))
        weight = weight.cut(lidHole)

        #something to be hooked onto - two sticky out bits with a machine screw through them
        extraWidth = 0

        r = self.diameter/2
        angle = math.acos((self.lidWidth/2 + extraWidth) / r)
        corner = polar(angle, r)
        # more cadquery fudgery with r
        weight = weight.faces(">Z").workplane().moveTo(corner[0], corner[1]).radiusArc((corner[0], -corner[1]), r - 0.001).close().mirrorY().extrude(r)


        nutD = getNutContainingDiameter(self.boltMetricSize, 0.2)
        nutHeight = getNutHeight(self.boltMetricSize) + 0.5
        headHeight = getScrewHeadHeight(self.boltMetricSize) + 0.5
        headD = getScrewHeadDiameter(self.boltMetricSize) + 0.5
        screwHeight = r - nutD

        largeCut = self.diameter
        wiggleSpace = 1
        boltSpace = self.boltThreadLength - nutHeight - wiggleSpace

        extraCutter = 1
        screwSpace = cq.Workplane("YZ").polygon(6,nutD).extrude(largeCut).faces(">X").workplane()\
            .circle(self.boltMetricSize/2).extrude(boltSpace).faces(">X").workplane()\
            .circle(headD/2).extrude(largeCut).translate((-largeCut - boltSpace/2,0,screwHeight + self.height))

        weight = weight.cut(screwSpace)


        #pretty shape

        topCutterToKeep = cq.Workplane("YZ").circle(r).extrude(self.diameter*2).translate((-self.diameter,0,0))
        topCutter = cq.Workplane("XY").rect(self.diameter*2, self.diameter*2).extrude(self.diameter)
        topCutter = topCutter.cut(topCutterToKeep).translate((0,0,self.height))

        weight = weight.cut(topCutter)

        return weight

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_weight.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getWeight(), out)

        out = os.path.join(path, "{}_weight_lid.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getLid(), out)

    def getLid(self, forCutting=False):
        wallThick = self.wallThick
        slotThick = self.slotThick


        width = self.lidWidth

        if not forCutting:
            # reduce size a tiny bit so it can fit into the slot
            slotThick -= 0.3
            wallThick += 0.4
            width -= 0.2

        #cadquery just can't cope with cuts that line up perfectly
        wallR = self.diameter/2 - wallThick-0.001
        topR = self.diameter/2 - wallThick + slotThick

        wallAngle = math.acos((width/2)/wallR)
        topAngle = math.acos((width / 2) / topR)

        wallCorner = polar(wallAngle, wallR)
        topCorner = polar(topAngle, topR)



        lid = cq.Workplane("XY").moveTo(-wallCorner[0], wallCorner[1]).radiusArc(wallCorner, wallR).lineTo(wallCorner[0], - wallCorner[1]).radiusArc((-wallCorner[0], -wallCorner[1]), wallR).close().extrude(wallThick - slotThick)
        lid = lid.faces(">Z").workplane().moveTo(-topCorner[0], topCorner[1]).radiusArc(topCorner, topR).lineTo(topCorner[0], - topCorner[1]).radiusArc((-topCorner[0], -topCorner[1]), topR).close().extrude(slotThick)

        # lid = cq.Workplane("XY").moveTo(-topCorner[0], topCorner[1]).radiusArc(topCorner, topR).lineTo(topCorner[0], - topCorner[1]).radiusArc((-topCorner[0], -topCorner[1]), topR).close().extrude(slotThick)


        return lid

def getAngleCovered(distances,r):
    totalAngle = 0

    for dist in distances:
        totalAngle += math.asin(dist/(2*r))

    totalAngle*=2

    return totalAngle

def getRadiusForPointsOnAnArc(distances, arcAngle=math.pi, iterations=100):
    '''
    given a list of distances between points, place them on the edge of a circle at those distances apart (to cover circleangle of the circle)
    find the radius of a circle where this is possible
    circleAngle is in radians
    '''



    #treat as circumference
    aproxR = sum(distances) / arcAngle

    minR = aproxR
    maxR = aproxR*1.2
    lastTestR = 0
    # errorMin = circleAngle - getAngleCovered(distances, minR)
    # errorMax = circleAngle - getAngleCovered(distances, maxR)
    testR = aproxR
    errorTest = arcAngle - getAngleCovered(distances, testR)

    for i in range(iterations):
        # print("Iteration {}, testR: {}, errorTest: {}".format(i,testR, errorTest))
        if errorTest < 0:
            #r is too small
            minR = testR

        if errorTest > 0:
            maxR = testR

        if errorTest == 0 or testR == lastTestR:
            #turns out errorTest == 0 can happen. hurrah for floating point! Sometimes however we don't get to zero, but we can't refine testR anymore
            print("Iteration {}, testR: {}, errorTest: {}".format(i, testR, errorTest))
            # print("found after {} iterations".format(i))
            break
        lastTestR = testR
        testR = (minR + maxR)/2
        errorTest = arcAngle - getAngleCovered(distances, testR)

    return testR

class Assembly:
    '''
    Produce a fully (or near fully) assembled clock
    likely to be fragile as it will need to delve into the detail of basically everything

    currently assumes pendulum and chain wheels are at front - doesn't listen to their values
    '''
    def __init__(self, plates, hands=None, dial=None, timeMins=10, timeHours=10):
        self.plates = plates
        self.hands = hands
        self.dial=dial
        self.goingTrain = plates.goingTrain
        self.arbourCount = self.goingTrain.chainWheels + self.goingTrain.wheels
        self.pendulum = self.plates.pendulum
        self.motionWorks = self.plates.motionWorks
        self.timeMins = timeMins
        self.timeHours = timeHours

    def getClock(self):
        bottomPlate = self.plates.getPlate(True)
        topPlate  = self.plates.getPlate(False)

        clock = bottomPlate.add(topPlate.translate((0,0,self.plates.plateDistance + self.plates.plateThick)))

        for a in range(-self.goingTrain.chainWheels, self.goingTrain.wheels):
            arbour = self.goingTrain.getArbour(a)
            clock = clock.add(arbour.getShape(False).translate(self.plates.bearingPositions[a+self.goingTrain.chainWheels]).translate((0,0,self.plates.plateThick + self.plates.wobble/2)))

        #the chain wheel parts
        clock = clock.add(self.goingTrain.chainWheelWithRatchet.translate(self.plates.bearingPositions[0]).translate((0,0,self.goingTrain.getArbour(-self.goingTrain.chainWheels).wheelThick + self.plates.plateThick + self.plates.wobble/2)))

        chainWheelTop =  self.goingTrain.chainWheelHalf.mirror().translate((0,0,self.goingTrain.chainWheel.getHeight()/2))

        clock = clock.add(
           chainWheelTop.translate(self.plates.bearingPositions[0]).translate((0, 0, self.goingTrain.getArbour(-self.goingTrain.chainWheels).wheelThick + self.plates.plateThick + self.plates.wobble / 2 + self.goingTrain.chainWheel.getHeight()/2 + self.goingTrain.ratchet.thick)))

        anchorAngle = math.atan2(self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[-2][1], self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[-2][0]) - math.pi/2

        #the anchor is upside down for better printing, so flip it back
        anchor = self.pendulum.anchor.mirror("YZ", (0,0,0))
        #and rotate it into position
        anchor = anchor.rotate((0,0,0),(0,0,1), radToDeg(anchorAngle)).translate(self.plates.bearingPositions[-1]).translate((0,0,self.plates.plateThick + self.plates.wobble/2))
        clock = clock.add(anchor)

        #where the nylock nut and spring washer would be
        motionWorksZOffset = 3

        time_min = self.timeMins
        time_hour = self.timeHours

        minuteAngle = - 360 * (time_min / 60)
        hourAngle = - 360 * (time_hour + time_min / 60) / 12

        #motion work in place
        motionWorksModel = self.motionWorks.getCannonPinion().rotate((0,0,0),(0,0,1), minuteAngle)
        motionWorksModel = motionWorksModel.add(self.motionWorks.getHourHolder().translate((0,0,self.motionWorks.getCannonPinionBaseThick())))
        motionWorksModel = motionWorksModel.add(self.motionWorks.getMotionArbour().translate((self.plates.motionWorksRelativePos[0],self.plates.motionWorksRelativePos[1], self.motionWorks.getCannonPinionBaseThick()/2)))

        clock = clock.add(motionWorksModel.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], self.plates.plateThick*2 + self.plates.plateDistance + motionWorksZOffset)))



        #hands on the motion work, showing the time set above
        minuteHand = self.hands.getHand(hour=False).rotate((0,0,0),(0,0,1), minuteAngle)
        hourHand = self.hands.getHand(hour=True).rotate((0, 0, 0), (0, 0, 1), hourAngle)
        clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], self.plates.plateThick*2 + self.plates.plateDistance + motionWorksZOffset + self.motionWorks.minuteHolderTotalHeight - self.hands.thick)))

        clock = clock.add(hourHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1],
                                                self.plates.plateThick * 2 + self.plates.plateDistance + motionWorksZOffset + self.motionWorks.minuteHolderTotalHeight - self.hands.thick*3)))

        pendulumRodExtraZ = 2

        pendulumRodFixing = self.pendulum.getPendulumForRod().mirror().translate((0,0,self.pendulum.pendulumTopThick))

        clock = clock.add(pendulumRodFixing.translate((self.plates.bearingPositions[-1][0], self.plates.bearingPositions[-1][1], self.plates.plateThick*2 + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ)))

        minuteToPendulum = (self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[self.goingTrain.chainWheels][1])

        if abs(minuteToPendulum[0]) < 50:
            #assume we need the ring to go around the hands
            ring = self.pendulum.getHandAvoider()
            handAvoiderExtraZ = (self.pendulum.pendulumTopThick - self.pendulum.handAvoiderThick)/2
            #ring is over the minute wheel/hands
            clock = clock.add(ring.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1],self.plates.plateThick * 2 + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ + handAvoiderExtraZ)))



        for arbour in range(-self.goingTrain.chainWheels, self.goingTrain.wheels+1):
            bearingPos = self.plates.bearingPositions[arbour + self.goingTrain.chainWheels]
            for top in [True, False]:
                extensionShape=self.plates.getArbourExtension(arbour, top=top)
                z =  0
                if top:
                    if arbour < self.goingTrain.wheels:
                        z = self.goingTrain.getArbour(arbour).getTotalThickness() +  bearingPos[2]
                    else:
                        z = self.pendulum.anchorThick + bearingPos[2]
                if extensionShape is not None:
                    clock=clock.add(extensionShape.translate((bearingPos[0], bearingPos[1], z + self.plates.plateThick + self.plates.wobble/2)))

        #TODO pendulum bob and nut

        #TODO weight?

        return clock

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getClock(), out)

class WeightShell:
    '''
    A shell to go around the large and ugly weights from cousins
    '''
    def __init__(self, diameter, height, twoParts=True, holeD=5):
        #internal diameter
        self.diameter=diameter
        self.height = height
        self.wallThick=1.2
        #if True then (probably because it's too tall...) print in two sections that slot over top and bottom
        self.twoParts=twoParts
        self.holeD=holeD

    def getShell(self, top=True):
        shell = cq.Workplane("XY")
        outerR = self.diameter/2 + self.wallThick
        height = self.height
        overlap = 3
        if self.twoParts:
            height=height/2 - overlap/2

        shell = shell.circle(outerR).circle(self.holeD/2).extrude(self.wallThick)
        shell = shell.faces(">Z").workplane().circle(outerR).circle(self.diameter/2).extrude(height)

        if self.twoParts:
            if top:
                shell = shell.faces(">Z").workplane().circle(outerR).circle(outerR - self.wallThick/2).extrude(overlap)
            else:
                shell = shell.faces(">Z").workplane().circle(outerR - self.wallThick / 2).circle(outerR - self.wallThick).extrude(overlap)

        return shell

    def outputSTLs(self, name="clock", path="../out"):

        out = os.path.join(path, "{}_weight_shell_top.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getShell(True), out)

        out = os.path.join(path, "{}_weight_shell_bottom.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getShell(False), out)

# getRadiusForPointsOnACircle([10,20,15], math.pi)
#
#
# dial = Dial(120)
#
# show_object(dial.getDial())

# weight = Weight()
#
# show_object(weight.getWeight())
#
# weight.printInfo()
#
# print("Weight max: {:.2f}kg".format(weight.getMaxWeight()))
# show_object(weight.getLid(forCutting=True))
#
# train=GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=30, maxChainDrop=2100, chainAtBack=False)
# train.calculateRatios()
# train.printInfo()
# train.genChainWheels()
# # show_object(train.chainWheelWithRatchet)
# # show_object(train.chainWheelHalf.translate((0,30,0)))
# train.genGears(module_size=1.2,moduleReduction=0.85, ratchetThick=4)
# # show_object(train.ratchet.getInnerWheel())
# # show_object(train.arbours[0])
#
# motionWorks = MotionWorks(minuteHandHolderHeight=30)
#
# pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=8)
#
#
# # show_object(pendulum.getPendulumForRod())
# # show_object(pendulum.getHandAvoider())
# # show_object(pendulum.getBob())
# show_object(pendulum.getBobNut())
#
#
# plates = ClockPlates(train, motionWorks, pendulum,plateThick=10)
# #
# backplate = plates.getPlate(True)
# frontplate = plates.getPlate(False)
# show_object(backplate)
# show_object(frontplate.translate((100,0,0)))

# holepunch = getHoleWithHole(3,10,4)
# show_object(holepunch)
# shape = cq.Workplane("XY").circle(10).extrude(20)
# shape = shape.cut(holepunch)
#
# show_object(shape)

# escapement = Escapement(teeth=30, diameter=60)
# pendulum = Pendulum(escapement, 0.388, anchorHoleD=3, anchorThick=8, nutMetricSize=3, crutchLength=0, bobD=60, bobThick=10)
# show_object(pendulum.getPendulumForRod())
# # show_object(pendulum.getBob())

# # show_object(escapement.getAnchor3D())
# show_object(escapement.getAnchorArbour(holeD=3, crutchLength=0, nutMetricSize=3))
#
# # hands = Hands(style="simple", minuteFixing="square", minuteFixing_d1=5, hourfixing_d=5, length=100, outline=1, outlineSameAsBody=False)
# hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=5, hourfixing_d=5, length=100, thick=4, outline=1, outlineSameAsBody=False)
# #
# # show_object(hands.getHand(outline=False))
# show_object(hands.getHandNut())
# hands.outputSTLs(clockName, clockOutDir)

# #drop of 1 and lift of 3 has good pallet angles with 42 teeth
# drop =2
# lift =4
# lock=2
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat",diameter=61.454842805344896, teeth=30, lock=lock, anchorTeeth=None)
# # escapement = Escapement(teeth=30, diameter=61.454842805344896, lift=4, lock=2, drop=2, anchorTeeth=None,
# #                              clockwiseFromPinionSide=False, type="deadbeat")
#
# wheel_angle = 0#-3.8  -4.1  -2 #- radToDeg(escapement.toothAngle - escapement.drop)/2#-3.3 - drop - 3.5 -
# anchor_angle = 0#lift/2 + lock/2
#
# show_object(escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle))
# show_object(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))
#
# anchor = escapement.getAnchorArbour(holeD=3, anchorThick=10, clockwise=False, arbourLength=0, crutchLength=0, crutchBoltD=3, pendulumThick=3, nutMetricSize=3)
# # show_object(escapement.getAnchor3D())
# show_object(anchor)
# # exporters.export(anchor, "../out/anchor_test.stl")
# #
# #

# ### ============FULL CLOCK ============
# # # train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
# train=GoingTrain(pendulum_period=2,fourth_wheel=False,escapement_teeth=30, maxChainDrop=1800, chainAtBack=False,chainWheels=0)#, hours=180)
# train.calculateRatios()
# # train.setRatios([[64, 12], [63, 12], [60, 14]])
# # train.setChainWheelRatio([74, 11])
# # train.genChainWheels(ratchetThick=5)
# pendulumSticksOut=25
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
# train.genGears(module_size=1,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)
# motionWorks = MotionWorks(minuteHandHolderHeight=30)
# #trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
# pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, useNylocForAnchor=False)
#
#
# #printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
# plates = ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="Wall 05", style="round")
#
# plate = plates.getPlate(True)
# #
# show_object(plate)
#
# show_object(plates.getPlate(False).translate((0,0,plates.plateDistance + plates.plateThick)))
# #
# # hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=3, hourfixing_d=5, length=100, thick=4, outline=0, outlineSameAsBody=False)
# hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# assembly = Assembly(plates, hands=hands)
#
# show_object(assembly.getClock())
# # #

# # anchorAngle = math.atan2(plates.bearingPositions[-1][1] - plates.bearingPositions[-2][1], plates.bearingPositions[-1][0] - plates.bearingPositions[-2][0]) - math.pi / 2
# # # anchorAngle=0
# # anchor = pendulum.anchor.rotate((0,0,0),(0, 0, 1), radToDeg(anchorAngle))#.translate(plates.bearingPositions[-1]).translate((0, 0, plates.plateThick + plates.wobble / 2))
# # show_object(anchor)
#
# # exporters.export(plate, "../out/platetest.stl")
# #
# # hands = Hands(minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, ratchetThick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
#
# #
# #
# # show_object(plates.goingTrain.getArbour(0).getShape(False).translate((0,200,0)))
# # hands = Hands(style="cuckoo",minuteFixing="square", minuteFixing_d1=3, hourfixing_d=5, length=100, thick=4, outline=1, outlineSameAsBody=False)
# # show_object(hands.getHand(False,True))
# # show_object(hands.getHand(False,False).translate((50,0,0)))

#
# shell = WeightShell(45,220, twoParts=True, holeD=5)
#
# show_object(shell.getShell())
#
# show_object(shell.getShell(False).translate((100,0,0)))