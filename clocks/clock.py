import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os

'''
Long term plan: this will be a library of useful classes to generate all the components and bits of clock plates
But another script will generate specific clock plates and arbours (note - the GoingTrain class has become a bit of a jack of all trades generating most of the arbours)

Note: naming conventions I can find for clock gears seem to assume you always have the same number of gears between the chain and the minute hand
this is blatantly false (I can see this just looking at the various clocks I have) so I'm adopting a different naming convention:

The minute hand arbour is arbour 0.
In the direction of the escapement is +=ve
in the direction of the chain/spring wheel is -ve

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
        for i in range(arms):
            startAngle = i * math.pi * 2 / arms
            endAngle = (i + 1) * math.pi * 2 / arms - armAngle

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
    def __init__(self, arbourD, wheel=None, wheelThick=None, pinion=None, pinionThick=None, ratchet=None, chainWheel=None, escapement=None, endCapThick=1, style="HAC", distanceToNextArbour=-1):
        '''
        This represents a combination of wheel and pinion. But with special versions:
        - chain wheel is wheel + ratchet (pinionThick is used for ratchet thickness)
        - escape wheel is pinion + escape wheel
        - anchor is just the escapement anchor (NOTE - DECIDED IT'S NOT WORTH HAVING THAT AS PART OF THIS)

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

    def getWheelCentreZ(self, pinionOnTop=True):
        '''
        Get the centre of the height of the wheel - which drives the next arbour
        '''
        if pinionOnTop:
            return self.wheelThick / 2
        else:
            return self.getTotalThickness() - self.wheelThick/2

    def getPinionCentreZ(self, pinionOnTop=True):
        if pinionOnTop:
            return self.getTotalThickness() - self.endCapThick - self.pinionThick/2
        else:
            return self.endCapThick + self.pinionThick/2

    def getPinionToWheelZ(self, pinionOnTop=True):
        '''
        Useful for calculating the height of the next part of the power train
        '''
        return self.getWheelCentreZ(pinionOnTop) - self.getPinionCentreZ(pinionOnTop)

    def getMaxRadius(self):
        if self.wheel is not None:
            #chain wheel, WheelAndPinion
            return self.wheel.getMaxRadius()
        if self.getType() == "EscapeWheel":
            return self.escapement.getWheelMaxR()
        raise NotImplementedError("Max Radius not yet implemented for arbour type {}".format(self.getType()))

    def getShape(self):
        '''
        return a shape that can be exported to STL
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

        return shape

class GoingTrain:
    gravity = 9.81
    def __init__(self, pendulum_period=1, fourth_wheel=False, escapement_teeth=30, chainWheels=0, hours=30,chainAtBack=True, scapeAtFront=False, maxChainDrop=1800, max_chain_wheel_d=23, min_pinion_teeth=10, max_wheel_teeth=100):
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

        self.min_pinion_teeth=min_pinion_teeth
        self.max_wheel_teeth=max_wheel_teeth
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

    def calculateRatios(self):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        '''

        desired_minute_time = 60*60
        #[ {time:float, wheels:[[wheelteeth,piniontheeth],]} ]
        options = []

        pinion_min=self.min_pinion_teeth
        pinion_max=20
        wheel_min=50
        wheel_max=self.max_wheel_teeth

        #TODO prefer non-integer combos.
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
        print("allGearPairCombos", len(allGearPairCombos))
        #[ [[w,p],[w,p],[w,p]] ,  ]
        allTrains = []

        allTrainsLength = 1
        for i in range(self.wheels):
            allTrainsLength*=len(allGearPairCombos)

        #this can be made generic for self.wheels, but I can't think of it right now. A stack or recursion will do the job
        #one fewer pairs than wheels
        if self.wheels == 3:
            for pair_0 in range(len(allGearPairCombos)):
                for pair_1 in range(len(allGearPairCombos)):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
        elif self.wheels == 4:
            for pair_0 in range(len(allGearPairCombos)):
                for pair_1 in range(len(allGearPairCombos)):
                    for pair_2 in range(len(allGearPairCombos)):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1], allGearPairCombos[pair_2]])
        print("allTrains", len(allTrains))
        allTimes=[]
        for c in range(len(allTrains)):
            totalRatio = 1
            intRatio = False
            totalTeeth = 0
            #trying for small wheels and big pinions
            totalWheelTeeth = 0
            totalPinionTeeth = 0
            for p in range(len(allTrains[c])):
                ratio = allTrains[c][p][0] / allTrains[c][p][1]
                if ratio == round(ratio):
                    intRatio=True
                totalRatio*=ratio
                totalTeeth +=  allTrains[c][p][0] + allTrains[c][p][1]
                totalWheelTeeth += allTrains[c][p][0]
                totalPinionTeeth += allTrains[c][p][1]
            totalTime = totalRatio*self.escapement_time
            error = 60*60-totalTime

            train = {"time":totalTime, "train":allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth/100-totalPinionTeeth/10 }
            if abs(error) < 1 and not intRatio:
                allTimes.append(train)

        allTimes.sort(key = lambda x: x["error"]+x["teeth"])
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

    def genChainWheels(self, ratchetThick=7.5, holeD=3.5, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15):
        '''

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

        self.chainWheel = ChainWheel(max_circumference=chainWheelCircumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance)


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


    def genGears(self, module_size=1.5, holeD=3, moduleReduction=0.85, thick=6, chainWheelThick=-1, escapeWheelThick=-1):
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

        #TODO variable thicknesses? thickness per gear? or is just extra for the chain wheels enough?
        #having chain wheels different thicknesses is enough to warrent thickness per gear i think
        #and possibly a new class to hold this info together
        self.gearPivotLength=thick*2
        self.chainGearPivotLength = chainWheelThick*2

        self.gearPivotEndCapLength=thick*0.25
        self.gearTotalThick = self.gearWheelThick + self.gearPivotLength + self.gearPivotEndCapLength
        # self.chainGearTotalThick
        style="HAC"
        module_sizes = [module_size * math.pow(moduleReduction, i) for i in range(self.wheels)]

        #the module of each wheel is slightly smaller than the preceeding wheel
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_size* math.pow(moduleReduction, i)) for i,wheel in enumerate(self.trains[0]["train"])]




        # print(module_sizes)
        #make the esacpe wheel smaller than the last wheel by modulereduction
        # self.escapement = Escapement(self.escapement_teeth,pairs[len(pairs)-1].wheel.getMaxRadius()*2*moduleReduction)
        # with lift of 4deg, 30 teeth, a drop adjustment of -7 results in 3deg of drop evenly on both pallets
        #trying a tiny bit more lift to make up for shorter plates due to printing?
        # lift = 5
        # drop = -7

        escapeWheelDiameter = pairs[len(pairs)-1].wheel.getMaxRadius()*2*0.75

        #chain wheel imaginary pivot (in relation to deciding which way the next wheel faces) is opposite to where teh chain is
        #using != as XOR, so if an odd number of wheels, it's the same as chainAtBack. If it's an even number of wheels, it's the opposite
        escapeWheelPivotAtFront = self.chainAtBack != ((self.wheels + self.chainWheels) % 2 == 0)

        #only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escapeWheelClockwise = self.wheels %2 == 1

        escapeWheelClockwiseFromPivotSide = escapeWheelPivotAtFront == escapeWheelClockwise

        print("Escape wheel pivot at front: {}, clockwise (from front) {}, clockwise from pivot side: {} ".format(escapeWheelPivotAtFront, escapeWheelClockwise, escapeWheelClockwiseFromPivotSide))
        self.escapement = Escapement(teeth=self.escapement_teeth, diameter=escapeWheelDiameter, type=self.escapement_type, lift=self.escapement_lift, lock=self.escapement_lock, drop=self.escapement_drop, anchorTeeth=None, clockwiseFromPivotSide=escapeWheelClockwiseFromPivotSide)
        self.chainWheelArbours=[]
        if self.chainWheels > 0:
            # assuming one chain wheel for now
            chainModule = module_size * (1 / moduleReduction)
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

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                if self.chainWheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbour(chainWheel=self.chainWheel, wheel = pairs[i].wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=holeD, distanceToNextArbour=pairs[i].centre_distance)
                else:
                    #just a normal gear
                    arbour = Arbour(wheel = pairs[i].wheel, pinion=self.chainWheelPair.pinion, arbourD=holeD, wheelThick=thick, pinionThick=self.chainWheelArbours[-1].wheelThick*2, endCapThick=self.gearPivotEndCapLength, distanceToNextArbour= pairs[i].centre_distance, style=style)

                #regardless of chains, we need a nyloc nut to fix the wheel to the rod
                arbour.setNutSpace(holeD)

                arbours.append(arbour)

            elif i < self.wheels-1:

                #intermediate wheels
                #no need to worry about front and back as they can just be turned around
                arbours.append(Arbour(wheel=pairs[i].wheel, pinion=pairs[i-1].pinion, arbourD=holeD, wheelThick=thick, pinionThick=arbours[-1].wheelThick * 2, endCapThick=self.gearPivotEndCapLength,
                                distanceToNextArbour=pairs[i].centre_distance, style=style))
            else:
                #last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                arbours.append(Arbour(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbourD=holeD, wheelThick=escapeWheelThick, pinionThick=arbours[-1].wheelThick * 2, endCapThick=self.gearPivotEndCapLength,
                                      distanceToNextArbour=self.escapement.anchor_centre_distance, style=style))
        self.wheelPinionPairs = pairs
        self.arbours = arbours




        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

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
    def __init__(self, teeth=42, diameter=100, anchorTeeth=None, type="recoil", lift=4, drop=4, run=10, lock=2, clockwiseFromPivotSide=True):
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

        clockwiseFromPivotSide is for the escape wheel
        '''

        self.lift_deg = lift
        self.halfLift = 0.5*degToRad(lift)
        self.lift = degToRad(lift)

        self.drop_deg= drop
        self.drop = degToRad(drop)

        self.lock_deg = lock
        self.lock=degToRad(lock)

        self.clockwiseFromPivotSide=clockwiseFromPivotSide
        self.run_deg = run
        self.run = degToRad(run)

        self.teeth = teeth
        self.diameter=diameter
        # self.anchourDiameter=anchourDiameter

        self.innerDiameter = diameter * 0.8

        self.radius = self.diameter/2

        self.innerRadius = self.innerDiameter/2

        self.toothHeight = self.diameter/2 - self.innerRadius
        #*8.36/7 worked for a diameter of about 82mm, it's not enough at about 60mm
        self.printedToothHeight = self.toothHeight+1.4#*8.36/7
        print("tooth height", self.toothHeight)

        # print("WARNING NOT PRINTED TOOTH HEIGHT")
        # self.printedToothHeight = self.toothHeight


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

        # height from centre of escape wheel to anchor pivot - assuming this is at the point the tangents (from the wheelangle on the escape wheel teeth) meet
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
            anchor = anchor.radiusArc(outerLeftPoint, entryPalletEndR)

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






        #distance from anchor pivot to the nominal point the anchor meets the escape wheel
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

        #get the anchor the other way around so we can build on top of it, and centre it on the pivot
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

        # if self.type == "deadbeat":
        #     # toothAngle*=-1
        #     toothTipAngle*=-1
        #     toothBaseAngle*=


        wheel = cq.Workplane("XY").moveTo(self.innerRadius, 0)

        for i in range(self.teeth):
            angle = dA*i
            tipPos = (math.cos(angle+toothTipAngle)*diameterForPrinting/2, math.sin(angle+toothTipAngle)*diameterForPrinting/2)
            nextbasePos = (math.cos(angle+dA) * self.innerRadius, math.sin(angle + dA) * self.innerRadius)
            endPos = (math.cos(angle+toothBaseAngle) * self.innerRadius, math.sin(angle + toothBaseAngle) * self.innerRadius)
            # print(tipPos)
            # wheel = wheel.lineTo(0,tipPos[1])
            wheel = wheel.lineTo(tipPos[0], tipPos[1]).lineTo(endPos[0],endPos[1]).radiusArc(nextbasePos,self.innerDiameter)

        wheel = wheel.close()

        return wheel
    def getWheelMaxR(self):
        return self.diameter/2

    def getWheel3D(self, thick=5, holeD=5, style="HAC"):
        gear = self.getWheel2D().extrude(thick)

        if not self.clockwiseFromPivotSide:
            gear = gear.mirror("YZ", (0,0,0))

        rimThick = holeD*1.5
        rimRadius = self.innerRadius - rimThick

        armThick = rimThick
        if style == "HAC":
            gear = Gear.cutHACStyle(gear, armThick, rimRadius)

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
        I'm hoping to be able to keep both halves identical - so long as there's space for the m3 screws and the m3 pivot then this should remain possible
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
        self.ratchetTeeth = self.clicks*1


        self.thick = thick

    def getInnerWheel(self):
        '''
        Contains the ratchet clicks, hoping that PETG will be strong and springy enough, if not I'll have to go for screws as pivots and some spring wire (stainless steel wire might work?)
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

# class PivotHole:
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
    def __init__(self, goingTrain, motionWorks,  pendulum, compact=False, arbourD=3, bearingOuterD=10, bearingHolderLip=1.5, bearingHeight=4, screwheadHeight=2.5, pendulumAtFront=True, anchorThick=10, fixingScrewsD=3, plateThick=5, pendulumSticksOut=20):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!
        '''

        anglesToScape = None
        anglesToChain = None

        #reduce the height/width as much as possible
        self.compact = compact

        #just for the first prototype
        self.anchorHasNormalBushing=True
        self.motionWorks = motionWorks
        self.goingTrain = goingTrain
        self.pendulum=pendulum
        #up to and including the anchor
        self.anglesToScape = anglesToScape
        self.anglesToChain=anglesToChain
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
        self.pendulumAtFront = pendulumAtFront
        self.pendulumSticksOut = pendulumSticksOut

        #TODO make some sort of object to hold all this info we keep passing around?
        self.anchorThick=anchorThick

        self.fixingScrewsD = fixingScrewsD

        self.holderInnerD=self.bearingOuterD - self.bearingHolderLip*2

        #if angles are not given, assume clock is entirely vertical

        if anglesToScape is None:
            #assume simple pendulum at top
            angle = math.pi/2 if self.pendulumAtFront else math.pi/2

            #one extra for the anchor
            self.anglesToScape = [angle for i in range(self.goingTrain.wheels+1)]
        if anglesToChain is None:
            angle = math.pi / 2 if self.pendulumAtFront else -math.pi / 2

            self.anglesToChain = [angle for i in range(self.goingTrain.chainWheels)]


        drivenToPivotEnd = self.goingTrain.gearPivotLength/2 + self.goingTrain.gearPivotEndCapLength
        drivenToWheelEnd = self.goingTrain.gearPivotLength/2 + self.goingTrain.gearWheelThick

        #[[x,y,z],]
        #for everything, arbours and anchor
        self.bearingPositions=[]
        #the anchor is having a simple bushing
        # self.bushingPositions=[]
        self.arbourThicknesses=[]
        #how much the arbours can wobble back and forth. aka End-shake.
        #note - might not have much effect anymore since I might not elevant the bearing holders
        self.wobble = 1
        #height of the centre of the wheel that will drive the next pivot
        drivingZ = 0
        # bearingZ = 0
        #this flip flops between gears, set it opposite of where the chain is, because the next wheel doesn't fit next to the chain wheel
        pinionAtBack = not self.goingTrain.chainAtBack
        print("initial pinionAtBack", pinionAtBack)
        for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels +1):
            print(str(i))
            if  (i == 0 and self.goingTrain.chainWheels == 0) or (i == -self.goingTrain.chainWheels):
                #the wheel with chain wheel ratchet
                #assuming this is at the very back of the clock
                #note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearingPositions.append(pos)
                #note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.goingTrain.getArbour(i).getWheelCentreZ(pinionAtBack)
                self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())
                print("pinionAtBack: {} wheel {} drivingZ: {}".format(pinionAtBack, i, drivingZ), pos)
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
                    pinionAtBack = not pinionAtBack
                    print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(not pinionAtBack), self.goingTrain.getArbour(i).getPinionCentreZ(not pinionAtBack)))
                    drivingZ = drivingZ + self.goingTrain.getArbour(i).getPinionToWheelZ(not pinionAtBack)
                    baseZ = drivingZ - self.goingTrain.getArbour(i).getPinionCentreZ(not pinionAtBack)
                    self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())

                angle=self.anglesToScape[i-1]
                v = polar(angle, r)
                # v = [v[0], v[1], baseZ]
                lastPos = self.bearingPositions[-1]
                # pos = list(np.add(self.bearingPositions[i-1],v))
                pos = [lastPos[0] + v[0], lastPos[1] + v[1], baseZ]

                print("pinionAtBack: {} wheel {} r: {} angle: {}".format(pinionAtBack, i, r, angle), pos)
                print("baseZ: ",baseZ, "drivingZ ", drivingZ)

                self.bearingPositions.append(pos)


        print(self.bearingPositions)

        topZs = [self.arbourThicknesses[i] + self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZs = [self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZ = min(bottomZs)
        if bottomZ < 0:
            #positions are relative (chain at front), so readjust everything
            topZs = [z-bottomZ for z in topZs]
            # bottomZs = [z - bottomZ for z in bottomZs]
            for i in range(len(self.bearingPositions)):
                self.bearingPositions[i][2] -= bottomZ

        print(self.bearingPositions)

        # self.bearingStartHeight = self.plateThick + self.bearingHeight

        self.plateDistance=max(topZs) + self.wobble# + self.bearingStartHeight*2

        print("Plate distance", self.plateDistance)

        # self.pilarR=15
        # self.pillarToGearGap=10
        # how much space to leave around the edge of the gears for safety
        self.gearGap = 3

        #hack for now
        #use vertical plate-things, not pillars!
        # self.width = 50







        #TODO chain wheels in the future

    def getPlate(self, back=True):
        if self.compact:
            return self.getCompactPlate(back)
        else:
            return self.getSimpleVerticalPlate(back)




    def getCompactPlate(self, back=True):
        '''
        a plate design to minimise total height, so more complicated clocks can still fit on the print bed

        Still trying to keep the pendulum, hands and weight in a line
        '''


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

    def getLeg(self, left=True, fixingD=3.1):
        '''
        The legs should overlap and a screw & nut will hold them tight
        Original plan was that all legs are identical, but if there is any thickness mismatch then the bearing holes could be misaligned
        so instead making them mirrored around the Y axis, so if any thickness mismatch occurs they can bend and keep the bearing holes aligned
        '''
        leg = cq.Workplane("XY")
        overlap = self.plateDistance*0.2

        width = self.legWidth
        length= self.legLength
        neg = 1 if left else -1

        leg = leg.rect(width,length).extrude(self.plateDistance/2 - overlap/2)
        leg = leg.faces(">Z").workplane().moveTo(neg*width*0.25,0).rect(width/2,length).extrude(overlap)
        leg = leg.faces(">X").workplane().moveTo(0,overlap/2).circle(fixingD/2).cutThruAll()

        return leg

    # def getPosForWheel(self, wheel):
    #     '''
    #     Wheel from 0 +ve toward escape wheel and -ve towards chain wheel
    #     '''
    #     if wheel == 0:
    #         return [0,0]
    #     elif wheel > 0:


    def getPlateWithSideArms(self, back=True):
        '''
        This was wall_clock_02 - it didn't work very well as the weight of the weight caused the front plate to droop
        and the gears get out of alignment

        note - this will likely be broken as it will depend on assumptions that have changed
        '''

        self.legWidth = 10
        self.legLength = 15

        safetySpace = 10 + self.legWidth / 2
        topGearR = self.goingTrain.wheelPinionPairs[0].wheel.getMaxRadius()
        bottomGearR = self.goingTrain.escapement.getWheelMaxR()
        bottomLegsPos = (self.bearingPositions[2][0], (self.bearingPositions[2][1] + self.bearingPositions[3][1])/2, 0 )

        self.legs = [(-topGearR - safetySpace, 0, 0), (topGearR + safetySpace, 0, 0),
                (bottomLegsPos[0] - (safetySpace + bottomGearR), bottomLegsPos[1], 0), (bottomLegsPos[0] + (safetySpace + bottomGearR), bottomLegsPos[1], 0)]


        neg = 1 if back else -1


        minHeight = self.bearingStartHeight


        # bearingHoles = [(b[0], b[1]) for b in self.bearingPositions]
        # if self.anchorHasNormalBushing:
        #     #TODO for first attempt I'm gonig to be lazy and do the same bearing based bushing for the anchor
        #     #I've read and it seems reasonable that ball bearings will wear out quickly just rocking back and forth
        #     #but right now I just want to see if the clock as a whole is viable
        allBearings = self.bearingPositions[:]
        # allBearings.extend(self.bushingPositions)
        #
        # if self.anchorHasNormalBushing:
        #     bearingHoles.append((self.bushingPositions[0][0], self.bushingPositions[0][1]))
        #



        #some extra support
        shortest = min([p[2] for p in allBearings[1:]])

        supportLength = allBearings[len(allBearings)-1][1] - allBearings[1][1]

        leftMost = min([b[0] for b in allBearings])
        rightMost = max([b[0] for b in allBearings])

        padding_width=self.bearingWallThick + self.bearingOuterD/2
        self.width = rightMost - leftMost + padding_width*2
        self.centreX=neg*(leftMost + (rightMost - leftMost)/2)

        plate = cq.Workplane("XY").tag("base").moveTo(self.centreX, self.topY - self.height / 2).rect(self.width, self.height).extrude(self.plateThick).tag("basetop")
        for i, pos in enumerate(allBearings):

            if back:
                height = pos[2] + minHeight
            else:
                height = self.plateDistance - (pos[2]) - self.arbourThicknesses[i] - self.bearingStartHeight - self.wobble
            plate = plate.add(self.getBearingHolder(height).translate((pos[0], pos[1], 0)))

        #cut away uneeded material
        topLeftToCut=(self.centreX - self.width/2 + self.bearingWallThick*2 + self.bearingOuterD, allBearings[1][1])
        cutterSize = 500
        cutter = cq.Workplane("XY").moveTo(topLeftToCut[0] + cutterSize/2, topLeftToCut[1] - cutterSize/2).rect(cutterSize, cutterSize).extrude(self.plateThick)
        #wish I knew why cutThroughAll has stopped working
        plate = plate.cut(cutter)

        support = cq.Workplane("XY").moveTo(0,allBearings[1][1] + supportLength/2).rect(5,abs(supportLength)).extrude(shortest+minHeight)
        #TODO tidy up later
        # plate = plate.add(support)

        legHolder = cq.Workplane("XY")
        for i, leg in enumerate(self.legs):
            if i % 2 == 0:
                legHolder = legHolder.moveTo(neg*leg[0], leg[1] + self.legLength / 2)
                legHolder = legHolder.lineTo(neg*leg[0], leg[1] - self.legLength / 2)
            else:
                legHolder = legHolder.lineTo(neg*leg[0], leg[1] - self.legLength / 2)
                legHolder = legHolder.lineTo(neg*leg[0], leg[1] + self.legLength / 2)
                legHolder = legHolder.close().extrude(self.plateThick)
            faceIn=i%2 == 0
            if not back:
                faceIn = not faceIn
            plate = plate.add(self.getLeg(faceIn).translate(leg))

        plate = plate.add(legHolder)




        # punch extra holes through the plates
        #faces(">Z").workplane()
        extraHoles= cq.Workplane("XY").pushPoints([(b[0], b[1]) for b in allBearings]).circle(self.holderInnerD / 2).extrude(200)
        plate = plate.cut(extraHoles)
        # plate = plate.workplaneFromTagged("basetop").pushPoints([(b[0], b[1]) for b in allBearings]).circle(self.holderInnerD / 2).cutThruAll()

        # if self.anchorHasNormalBushing:
        #     #TODO for first attempt I'm gonig to be lazy and do the same bearing based bushing for the anchor
        #     #I've read and it seems reasonable that ball bearings will wear out quickly just rocking back and forth
        #     #but right now I just want to see if the clock as a whole is viable
        #     for i, pos in enumerate(self.bushingPositions):
        #         plate = plate.add(self.getBearingHolder(pos[2] + minHeight).translate((pos[0], pos[1], 0)))

        if back:
            # screwhole to hang on the wall
            #this looks fine, but I think with the weight at the top it's going to be a bit unstable.
            #if I put the weight at the bottom (future plan) then it doesn't need to stick out the top at all
            screwHeadD = 11
            screwBodyD = 6
            screwHoleHeight = 7.5
            #sticking off the top makes the plate a bit too big to print nicely
            screwholeStartY=-45#self.bearingOuterD / 2
            hookPadding = 10
            x = screwHeadD / 2 + hookPadding
            if screwholeStartY > 0:
                plate = plate.workplaneFromTagged("base").moveTo(self.centreX-x, screwholeStartY).line(0, screwHoleHeight + hookPadding + screwHeadD ).tangentArcPoint((2 * x, 0)).line(0, -( screwHoleHeight + hookPadding + screwHeadD )).close().extrude(self.plateThick)

            plate = plate.faces(">Z").workplane().tag("top").moveTo(self.centreX, screwholeStartY + hookPadding + screwHeadD/2).circle(screwHeadD/2).cutThruAll()
            plate = plate.workplaneFromTagged("top").moveTo(self.centreX, screwholeStartY + hookPadding + screwHeadD*3/4 + screwHoleHeight/2).rect(screwBodyD,screwHoleHeight + screwHeadD/2).cutThruAll()
            plate = plate.workplaneFromTagged("top").moveTo(self.centreX, screwholeStartY + hookPadding + screwHeadD + screwHoleHeight).circle(screwBodyD/2).cutThruAll()


            holeWidth = 40
            holeD = 6
            #plan b, two holes to attach string or wire
            plate = plate.faces(">Z").workplane().pushPoints([(self.centreX-holeWidth/2,0),(self.centreX+holeWidth/2,0)]).circle(holeD/2).cutThruAll()
        else:
            #holes for motionworks and pendulum suspension point
            #TODO take into account chain wheels and whatnot for now assume first bearing is the minute wheel
            plate = plate.faces(">Z").workplane().moveTo(self.bearingPositions[0][0],self.bearingPositions[0][1] - self.motionWorks.arbourDistace).circle(self.motionWorks.holeD/2).cutThruAll()

            suspensionAttachments=self.pendulum.getSuspensionAttachmentHoles()

            for p in suspensionAttachments:
                plate = plate.faces(">Z").workplane().moveTo(self.bearingPositions[self.goingTrain.wheels][0]+p[0],self.bearingPositions[self.goingTrain.wheels][1]+p[1]).circle(self.fixingScrewsD/2).cutThruAll()





        return plate

    def getSimpleVerticalPlate(self, back=True):
        '''
        Just two vertical slats, with a shelf-bracket like brace at the bottom to stop it bending.
        Works pretty well! just a bit more chunky than needed
        '''



        # print("Height: ", self.minHeight)


        chainHoleD = self.goingTrain.chainWheel.chain_width+3
        print("chain hole D", chainHoleD)

        #making the plates wide enough that there can be vaguely strong holes for the chains to go through
        baseWidth = self.goingTrain.chainWheel.diameter + chainHoleD + 3
        #
        # width=chainHoleHolderWidth#25

        #just wide enough to safely hold the bearings
        width = self.bearingOuterD + self.bearingWallThick*2 #18#self.goingTrain.chainWheel.diameter - chainHoleD
        print("width", width)
        plateThick = self.plateThick

        # if not back:
        #     #the back plate is pretty solid, don't think the front needs to be quite as chunky?
        #     plateThick *= 0.75

        #https://en.wikipedia.org/wiki/Sagitta_(geometry)
        bottomGearR = self.goingTrain.getArbour(-self.goingTrain.chainWheels).getMaxRadius()
        l=width
        #aprox
        sagittaOfBottomGear = l*2/(8*bottomGearR)

        #was originally planning an angle bracket, but decided to just make it square and have screws vertically
        bottomBracketLength=self.plateDistance - width/2
        bottomBracketOffset = self.gearGap + bottomGearR - sagittaOfBottomGear
        #bottom of teh top bracket
        #making it now just a circle - not the most compact, but I think it looks better
        topBracketOffset =  self.bearingOuterD/2 + self.gearGap
        topBracketLength = width/2
        fixingScrewD=3

        #height of the rectangular bit
        height = abs(self.bearingPositions[len(self.bearingPositions) - 1][1]) + bottomBracketOffset + bottomBracketLength + topBracketLength + topBracketOffset
        topY = self.bearingPositions[len(self.bearingPositions) - 1][1] + topBracketOffset + topBracketLength

        # fixingSpace = width - fixingScrewD*2.5

        totalBracketHeight = bottomBracketLength + width/2

        # fixingPositions=[ (-width/4, topY + width*0.2), (width/4, topY + width*0.2),
        #     (0, topY - height + bottomBracketLength - totalBracketHeight/5), (0, topY - height + bottomBracketLength - totalBracketHeight/2), (0, topY - height + bottomBracketLength - totalBracketHeight*4/5) ]

        fixingPositions = [(-width/4, topY), (width/4, topY),  (0, topY - height + bottomBracketLength - totalBracketHeight/4), (0, topY - height + bottomBracketLength - totalBracketHeight*2/3)]

        # if back:
        #     #for the triangular bracket
        #     height+= self.plateDistance

        # plate = cq.Workplane("XY").moveTo(0, - self.minHeight/2).rect(width, self.minHeight).extrude(10)

        plate = cq.Workplane("XY").moveTo(-width/2, topY).radiusArc((width/2, topY), width/2).line(0, -height).radiusArc((-width/2, topY-height), width/2).close().extrude(plateThick)

        for i, pos in enumerate(self.bearingPositions):

            plate = plate.cut(self.getBearingPunch(back).translate((pos[0], pos[1], 0)))

        if not back:
            # suspensionBaseThick=0.5
            # suspensionPoint = self.pendulum.getSuspension(False,suspensionBaseThick ).translate((self.bearingPositions[len(self.bearingPositions)-1][0], self.bearingPositions[len(self.bearingPositions)-1][1], plateThick-suspensionBaseThick))
            #
            # plate = plate.add(suspensionPoint)
            #new plan: just put the pendulum on the same rod as the anchor, and use nyloc nuts to keep both firmly on the rod.
            #no idea if it'll work without the rod bending!

            if self.pendulumSticksOut > 0:
                extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, True).translate((self.bearingPositions[len(self.bearingPositions)-1][0],self.bearingPositions[len(self.bearingPositions)-1][1],plateThick))
                plate = plate.add(extraBearingHolder)

            motionWorksDistance = self.motionWorks.getArbourDistance()

            plate = plate.faces(">Z").workplane().moveTo(self.bearingPositions[self.goingTrain.chainWheels][0], self.bearingPositions[self.goingTrain.chainWheels][1]-motionWorksDistance).circle(self.arbourD/2).cutThruAll()
            nutDeep = METRIC_HALF_NUT_DEPTH_MULT*self.arbourD
            nutSpace = cq.Workplane("XY").polygon(6, getNutContainingDiameter(self.arbourD)).extrude(nutDeep).translate((self.bearingPositions[self.goingTrain.chainWheels][0], self.bearingPositions[self.goingTrain.chainWheels][1]-motionWorksDistance, plateThick-nutDeep))

            plate = plate.cut(nutSpace)



        if back:
            # screwhole to hang on the wall
            screwHeadD = 9
            screwBodyD = 6
            screwHoleHeight = 5
            # sticking off the top makes the plate a bit too big to print nicely
            screwholeStartY = (self.bearingPositions[len(self.bearingPositions)-1][1] + self.bearingPositions[len(self.bearingPositions)-2][1] )/2 - screwHoleHeight - screwHeadD/2

            centreX=0
            plate = plate.faces(">Z").workplane().tag("top").moveTo(centreX, screwholeStartY + screwHeadD / 2).circle(screwHeadD / 2).cutThruAll()
            plate = plate.workplaneFromTagged("top").moveTo(centreX, screwholeStartY + screwHeadD * 3 / 4 + screwHoleHeight / 2).rect(screwBodyD, screwHoleHeight + screwHeadD / 2).cutThruAll()
            plate = plate.workplaneFromTagged("top").moveTo(centreX, screwholeStartY + screwHeadD + screwHoleHeight).circle(screwBodyD / 2).cutThruAll()




            # bracket = cq.Workplane("YZ").lineTo(-self.plateDistance-bottomBracketLength,0).lineTo(-bottomBracketLength,self.plateDistance).lineTo(0,self.plateDistance).close().extrude(width)
            #sometimes cadquery complains the radius isn't large enough to reach. it blatently is, but add 0.1 to bodge it
            bracket = cq.Workplane("XY").tag("base").moveTo(-width/2, topY - height + bottomBracketLength).radiusArc((width/2, topY - height + bottomBracketLength), -bottomGearR-2).line(0, -bottomBracketLength).radiusArc((-width/2,topY - height), width/2).close().extrude(self.plateDistance)
            #TODO tidier way to hold the chains
            # bracket = bracket.workplaneFromTagged("base").moveTo(0,self.topY - height + chainHoleHolderThick/2).rect(chainHoleHolderWidth, chainHoleHolderThick).extrude(self.plateDistance)


            # holes for the chain
            chainFromBack =self.bearingPositions[0][2] + self.goingTrain.gearWheelThick + self.goingTrain.chainWheel.getHeight()/2 + self.goingTrain.ratchet.thick

            bracket = bracket.faces(">Y").workplane().pushPoints([(self.goingTrain.chainWheel.diameter / 2, chainFromBack), (-self.goingTrain.chainWheel.diameter / 2, chainFromBack)]).circle(chainHoleD/2).cutThruAll()
            # bracket = bracket.faces(">Y").workplane().moveTo(0,chainHoleD).circle(chainHoleD / 2).cutThruAll()

            # minuteWheelR = self.goingTrain.getMinuteWheelPair().wheel.getMaxRadius()
            #shelf-like bracket to hold the front plate

            # plate = plate.faces(">Z").workplane().moveTo(0, -minuteWheelR -bottomBracketLength/2 - self.gearGap).rect(bracketWidth, bottomBracketLength).extrude(self.plateDistance)

            plate = plate.add(bracket.translate((0,0,plateThick)))#.translate((-width/2,-minuteWheelR - self.gearGap, plateThick)))


            # topBracket = cq.Workplane("XY").moveTo(-width/2,topY -topBracketLength).line(0, topBracketLength)\
            #     .radiusArc((width/2, topY), width/2).line(0, -topBracketLength).close().extrude(self.plateDistance)
            # #.radiusArc((-width/2, topY - topBracketLength), -width)
            topBracket = cq.Workplane("XY").moveTo(0, topY).circle(width/2).extrude(self.plateDistance)

            plate = plate.add(topBracket.translate((0,0,plateThick)))





        # currently punching holes all the way through the front and back, might revisit this idea with something like embedded nuts
        plate = plate.faces(">Z").workplane().pushPoints(fixingPositions).circle(fixingScrewD / 2).cutThruAll()

        return plate


    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_front_plate.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(False), out)

        out = os.path.join(path, "{}_back_plate.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True), out)

class Pendulum:
    '''
    Class to generate the anchor&crutch arbour and pendulum parts
    '''
    def __init__(self, escapement, length, clockwise=False, crutchLength=50, anchorThick=10, anchorAngle=-math.pi/2, anchorHoleD=2, crutchBoltD=3, suspensionScrewD=3, threadedRodM=3, nutMetricSize=0, handAvoiderInnerD=100):
        self.escapement = escapement
        self.crutchLength = crutchLength
        self.anchorAngle = anchorAngle

        #nominal length of the pendulum
        self.length = length
        # self.crutchWidth = 9

        #space for a nut to hold the anchor to the rod
        self.nutMetricSize=nutMetricSize

        self.anchor = self.escapement.getAnchorArbour(holeD=anchorHoleD, anchorThick=anchorThick, clockwise=clockwise, arbourLength=0, crutchLength=crutchLength, crutchBoltD=crutchBoltD, pendulumThick=threadedRodM, nutMetricSize=nutMetricSize)

        self.crutchSlackWidth=crutchBoltD*1.5
        self.crutchSlackHeight = 30
        self.suspensionD=20
        self.pendulumTopD = self.suspensionD*1.75
        self.pendulumTopExtraRadius = 5
        self.pendulumTopThick = getNutContainingDiameter(threadedRodM) + 2
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

        self.bobNutD = 30
        self.bobNutThick=10
        self.bobR=50
        self.bobThick = 15

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
        if False:
            #tried out a fancy one with the HAC style cut, looks alright but going to stick to soemthign more simple
            outerR = self.pendulumTopD / 2 + self.pendulumTopExtraRadius

            pendulum = pendulum.circle(outerR).extrude(self.pendulumTopThick)

            centreD= holeD*2.5

            pendulum = Gear.cutHACStyle(pendulum,holeD, outerR - holeD)

            pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()

        width = holeD*4
        height = holeD*5


        nutD = getNutContainingDiameter(holeD)

        wall_thick = (width - (nutD + 1))/2

        pendulum = pendulum.moveTo(-width/2,0).radiusArc((width/2,0), width/2).line(0,-height).radiusArc((-width/2,-height), width/2).close().extrude(self.pendulumTopThick)

        pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()

        #nut to hold to anchor rod
        nutThick = METRIC_NUT_DEPTH_MULT * holeD
        nutSpace = cq.Workplane("XY").polygon(6,nutD).extrude(nutThick).translate((0,0,self.pendulumTopThick-nutThick))
        pendulum = pendulum.cut(nutSpace)


        # pendulum = pendulum.faces(">Z").moveTo(0,-height*3/4).rect(width-wall_thick*2,height/2).cutThruAll()
        space = cq.Workplane("XY").moveTo(0,-height*3/4).rect(width-wall_thick*2,height/2).extrude(self.pendulumTopThick).translate((0,0,0.6))
        pendulum = pendulum.cut(space)

        #
        rod = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).circle(self.threadedRodM/2).extrude(100).translate((0,-height/2,0))
        pendulum = pendulum.cut(rod)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(6, nutD).extrude(nutThick).translate((0,-height,0))
        pendulum = pendulum.cut(nutSpace2)


        return pendulum

    def getHandAvoider(self):
        '''
        Get a circular part which attaches inline with pendulum rod, so it can go over the hands (for a front-pendulum)
        '''
        extraR=5
        avoider = cq.Workplane("XY").circle(self.handAvoiderInnerD/2).circle(self.handAvoiderInnerD/2 + extraR).extrude(self.pendulumTopThick)

        nutD = getNutContainingDiameter(self.threadedRodM)
        nutThick = METRIC_NUT_DEPTH_MULT * self.threadedRodM

        nutSpace = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick/2).polygon(6, nutD).extrude(nutThick).translate((0, -self.handAvoiderInnerD/2+0.5, 0))
        avoider = avoider.cut(nutSpace)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(6, nutD).extrude(nutThick).translate((0, self.handAvoiderInnerD / 2 +nutThick - 0.5, 0))
        avoider = avoider.cut(nutSpace2)

        avoider = avoider.faces(">Y").workplane().moveTo(0,self.pendulumTopThick/2).circle(self.threadedRodM/2).cutThruAll()

        return avoider


    def getCrutchExtension(self):
        '''
        Attaches to the bottom of the anchor to finish linking the crutch to the pendulum
        '''


    def getBob(self):


        circle = cq.Workplane("XY").circle(self.bobR)

        bob = cq.Workplane("XZ").lineTo(self.bobR,0).radiusArc((self.bobR,self.bobThick),-self.bobThick*0.9).lineTo(0,self.bobThick).close().sweep(circle)

        #was 0.5, which is plenty of space. Giong to try 0.1 to see if being a tight fit helps stop it rotate over time
        extraR=0.1

        #rectangle for the nut, with space for the threaded rod up and down
        cut = cq.Workplane("XY").rect(self.bobNutD*1.2,self.bobNutThick+1).extrude(self.bobThick*2).faces(">Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+extraR).extrude(self.bobR*2).\
            faces("<Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+extraR).extrude(self.bobR*2)
        bob=bob.cut(cut)

        # bob = bob.faces(">Z").workplane().rect(self.bobNutD*1.2,self.bobNutThick+1).cutThruAll()#.faces(">Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+0.5).cutThruAll()
        # bob = bob.faces(">Z").workplane().rect(70,10).cutThruAll()

        return bob

    def getBobNut(self):
        #TODO consider calculating how much time+- a single segment might be
        segments = 20
        knobbleR = 1
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
        nutD=getNutContainingDiameter(3)
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


class Hands:
    def __init__(self, style="simple", minuteFixing="rectangle", hourFixing="circle", minuteFixing_d1=1.5, minuteFixing_d2=2.5, hourfixing_d=3, length=25, thick=1.6, fixing_offset=0, outline=0, outlineSameAsBody=True):
        '''

        '''
        self.thick=thick
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
            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).lineTo(end_d / 2, length).radiusArc((-end_d / 2, length), -end_d / 2).lineTo(-width * 0.4, 0).close().extrude(ratchetThick)
            #
            #
            # if outline:
            #     #top right
            #     hand = cq.Workplane("XY").moveTo(width,length).lineTo()


            # else:
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(width, length).extrude(self.thick)

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
                #thinner internal bit
                shell = hand.shell(-self.outline).translate((0,0,-self.outline))
                # return shell
                notOutline = hand.cut(shell)
                #chop off the mess above the first few layers that we want

                bigSlab = cq.Workplane("XY").rect(length*3, length*3).extrude(self.thick).translate((0,0,LAYER_THICK*2))



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


# plates = ClockPlates(train, motionWorks, pendulum,plateThick=10)
#
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
# # show_object(escapement.getAnchor3D())
# show_object(escapement.getAnchorArbour(holeD=3, crutchLength=0, nutMetricSize=3))
#
# hands = Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=5, hourfixing_d=5, length=100, ratchetThick=3, outline=1, outlineSameAsBody=False)
#
# show_object(hands.getHand(outline=True))
# hands.outputSTLs(clockName, clockOutDir)

# #drop of 1 and lift of 3 has good pallet angles with 42 teeth
# drop =2
# lift =4
# lock=2
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat",diameter=61.454842805344896, teeth=30, lock=lock, anchorTeeth=None)
# # escapement = Escapement(teeth=30, diameter=61.454842805344896, lift=4, lock=2, drop=2, anchorTeeth=None,
# #                              clockwiseFromPivotSide=False, type="deadbeat")
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

#
# # train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
# train=GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=30, maxChainDrop=2100, chainAtBack=False)
# train.calculateRatios()
# train.genChainWheels(ratchetThick=5)
# pendulumSticksOut=20
# train.genGears(module_size=1,moduleReduction=0.85, ratchetThick=4)
# motionWorks = MotionWorks(minuteHandHolderHeight=pendulumSticksOut+20, )
# #trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
# pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=8, nutMetricSize=3, crutchLength=0)
#
#
# #printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
# plates = ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut)
#
# show_object(plates.getSimpleVerticalPlate(True))
# #
# # hands = Hands(minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, ratchetThick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
#
#
#
