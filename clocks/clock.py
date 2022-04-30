import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os
import datetime
import os

# INKSCAPE_PATH="C:\Program Files\Inkscape\inkscape.exe"
IMAGEMAGICK_CONVERT_PATH="C:\\Users\\Luke\\Documents\\Clocks\\3DPrintedClocks\\ImageMagick-7.1.0-portable-Q16-x64\\convert.exe"

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
GRAVITY = 9.81

#extra diameter to add to something that should be free to rotate over a rod
LOOSE_FIT_ON_ROD = 0.3

WASHER_THICK = 0.5

#extra diameter to add to the nut space if you want to be able to drop one in rather than force it in
NUT_WIGGLE_ROOM = 0.2

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

COUNTERSUNK_HEAD_WIGGLE = 0.3

def getNutHeight(metric_thread, nyloc=False, halfHeight=False):
    if halfHeight:
        return metric_thread*METRIC_HALF_NUT_DEPTH_MULT

    if metric_thread == 3:
        if nyloc:
            return 3.9

    return metric_thread * METRIC_NUT_DEPTH_MULT

def getScrewHeadHeight(metric_thread, countersunk=False):
    if metric_thread == 3:
        if countersunk:
            return 1.86
        return 2.6

    return metric_thread

def getScrewHeadDiameter(metric_thread, countersunk=False):
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
    def cutHACStyle(gear, armThick, rimRadius, innerRadius=-1):
        # vaguely styled after some HAC gears I've got, with nice arcing shapes cut out
        armAngle = armThick / rimRadius
        # # cadquery complains it can't make a radiusArc with a radius < rimRadius*0.85. this is clearly bollocks as the sagittaArc works.
        # innerRadius = rimRadius * 0.7

        if innerRadius < 0:
            #default, looks fine, works in most situations
            innerSagitta = rimRadius * 0.325
        else:
            #for more tightly controlled wheels were we need a certain amount of space in the centre
            #note, this is a bodge, I really need to calculate the sagitta of the outer circle so I can correctly calculate the desired inner sagitta
            innerSagitta = (rimRadius - innerRadius)*0.675

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

    @staticmethod
    def cutCirclesStyle(gear, outerRadius, innerRadius = 3, minGap = 2.4, cantUseCutThroughAllBodgeThickness=0):
        '''inspired (shamelessly stolen) by the clock on teh cover of the horological journal dated March 2022'''

        if innerRadius < 0:
            innerRadius = 3



        # #TEMP
        # gear = gear.faces(">Z").workplane().circle(innerRadius).cutThruAll()
        # return gear

        #sopme slight fudging occurs with minGap as using the diameter (gapSize) as a measure of how much circumference the circle takes up isn't accurate

        ringSize = (outerRadius - innerRadius)
        bigCircleR = ringSize*0.425
        bigCircleSpace = ringSize*1.1
        # smallCircleR = bigCircleR*0.3



        bigCirclescircumference = 2 * math.pi * (innerRadius + ringSize/2)

        bigCircleCount = math.floor(bigCirclescircumference / bigCircleSpace)
        if bigCircleCount > 0 :
            bigCircleAngle = math.pi*2/bigCircleCount

            bigCirclePos = polar(0, innerRadius + ringSize / 2)
            smallCirclePos = polar(bigCircleAngle / 2, innerRadius + ringSize * 0.75)
            distance = math.sqrt((bigCirclePos[0] - smallCirclePos[0])**2 + (bigCirclePos[1] - smallCirclePos[1])**2)
            smallCircleR = distance - bigCircleR - minGap

            hasSmallCircles = smallCircleR > 2

            for circle in range(bigCircleCount):
                angle = bigCircleAngle*circle
                pos = polar(angle, innerRadius + ringSize/2)

                if cantUseCutThroughAllBodgeThickness > 0:
                    cutter = cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(bigCircleR).extrude(cantUseCutThroughAllBodgeThickness)
                    gear = gear.cut(cutter)
                else:
                    gear = gear.faces(">Z").workplane().moveTo(pos[0], pos[1]).circle(bigCircleR).cutThruAll()
                if hasSmallCircles:
                    smallCirclePos = polar(angle + bigCircleAngle / 2, innerRadius + ringSize * 0.75)
                    if cantUseCutThroughAllBodgeThickness > 0:
                        cutter = cq.Workplane("XY").moveTo(smallCirclePos[0], smallCirclePos[1]).circle(smallCircleR).extrude(cantUseCutThroughAllBodgeThickness)
                        gear = gear.cut(cutter)
                    else:
                        gear = gear.faces(">Z").workplane().moveTo(smallCirclePos[0], smallCirclePos[1]).circle(smallCircleR).cutThruAll()

        return gear

    def __init__(self, isWheel, teeth, module, addendum_factor, addendum_radius_factor, dedendum_factor, toothFactor=math.pi/2, innerRadiusForStyle=-1):
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

        #purely for the fancy styling, is there anyhting in the centre (like a pinion or ratchet) to avoid?
        # self.innerRadiusForStyle=innerRadiusForStyle

        # # via practical addendum factor
        # self.addendum_height = 0.95 * addendum_factor * module

    def getMaxRadius(self):
        return self.pitch_diameter/2 + self.addendum_factor*self.module

    def get3D(self, holeD=0, thick=0, style="HAC", innerRadiusForStyle=-1):
        gear = self.get2D()

        if thick == 0:
            thick = round(self.pitch_diameter*0.05)
        gear = gear.extrude(thick)

        if holeD > 0:
            gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        if self.iswheel:
            rimThick = max(self.pitch_diameter * 0.035, 3)
            rimRadius = self.pitch_diameter / 2 - self.dedendum_factor * self.module - rimThick

            armThick = rimThick
            if style == "HAC":


                gear = Gear.cutHACStyle(gear, armThick, rimRadius, innerRadius=innerRadiusForStyle)
            elif style == "circles":
                # innerRadius = self.innerRadiusForStyle
                # if innerRadius < 0:
                #     innerRadius = self.
                gear = Gear.cutCirclesStyle(gear, outerRadius = self.pitch_diameter / 2 - rimThick, innerRadius=innerRadiusForStyle)



        return gear

    def addToWheel(self,wheel, holeD=0, thick=4, front=True, style="HAC", pinionThick=8, capThick=2):
        '''
        Intended to add a pinion (self) to a wheel (provided)
        if front is true ,added onto the top (+ve Z) of the wheel, else to -ve Z. Only really affects the escape wheel
        pinionthicker is a multiplier to thickness of the week for thickness of the pinion
        '''

        # pinionThick = thick * pinionthicker

        base = wheel.get3D(thick=thick, holeD=holeD, style=style, innerRadiusForStyle=self.getMaxRadius())

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
        if not self.iswheel:
            print("addendum radius", addendum_radius, self.module)
        # via practical addendum factor
        addendum_height = 0.95 * self.addendum_factor * self.module
        dedendum_height = self.dedendum_factor * self.module

        inner_radius = pitch_radius - dedendum_height
        outer_radius = pitch_radius + addendum_height
        if not self.iswheel:
            print("inner radius", inner_radius)

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
        #the pocket chain wheel or cord wheel (needed only to calculate full height)
        self.chainWheel=chainWheel
        self.style=style
        self.distanceToNextArbour=distanceToNextArbour
        self.nutSpaceMetric=None
        self.pinionOnTop=pinionAtFront
        self.anchor = anchor

        if self.getType() == "Unknown":
            raise ValueError("Not a valid arbour")

        # if self.getType() == "ChainWheel":
        #     self.wheel.innerRadiusForStyle=self.ratchet.outsideDiameter*0.6
        # elif self.getType() == "WheelAndPinion":
        #     self.wheel.innerRadiusForStyle = self.pinion.getMaxRadius()+1

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
            #the chainwheel (or cordwheel) now includes the ratceht thickness
            return self.wheelThick + self.chainWheel.getHeight()
        if self.getType() == "Anchor":
            #wheel thick being used for anchor thick
            return self.wheelThick

    def getWheelCentreZ(self):
        '''
        Get the centre of the height of the wheel - which drives the next arbour
        '''
        if self.pinionOnTop:
            return self.wheelThick / 2
        else:
            return self.getTotalThickness() - self.wheelThick/2

    def getPinionCentreZ(self):
        if self.getType() not in ["WheelAndPinion", "EscapeWheel"]:
            raise ValueError("This does not have a pinion")
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
            shape = shape.cut(getHoleWithHole(self.arbourD, getNutContainingDiameter(self.arbourD, NUT_WIGGLE_ROOM), deep , 6))

        if not forPrinting and not self.pinionOnTop:
            #make it the right way around for placing in a model
            #rotate not mirror! otherwise the escape wheels end up backwards
            shape = shape.rotate((0,0,0),(1,0,0),180).translate((0,0,self.getTotalThickness()))


        return shape

class GoingTrain:
    gravity = 9.81
    def __init__(self, pendulum_period=1, fourth_wheel=False, escapement_teeth=30, chainWheels=0, hours=30,chainAtBack=True, maxChainDrop=1800, max_chain_wheel_d=23, escapement=None):
        '''

        pendulum_period: desired period for the pendulum (full swing, there and back) in seconds
        fourth_wheel: if True there will be four wheels from minute hand to the escape wheel
        escapement_teeth: number of teeth on the escape wheel DEPRECATED, provide entire escapement instead
        chainWheels: if 0 the minute wheel is also the chain wheel, if >0, this many gears between the minute wheel and chain wheel (say for 8 day clocks)
        hours: intended hours to run for (dictates diameter of chain wheel)
        chainAtBack: Where the chain and ratchet mechanism should go relative to the minute wheel
        maxChainDrop: maximum length of chain drop to meet hours required, in mm
        max_chain_wheel_d: Desired diameter of the chain wheel, only used if chainWheels > 0. If chainWheels is 0 there is no flexibility here
        escapement: Escapement object. If not provided, falls back to defaults with esacpement_teeth


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

        self.chainAtBack = chainAtBack

        #if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.chainWheels = chainWheels
        self.hours = hours
        self.max_chain_wheel_d = max_chain_wheel_d
        self.maxChainDrop = maxChainDrop

        #calculate ratios from minute hand to escapement
        #the last wheel is the escapement
        self.wheels = 4 if fourth_wheel else 3

        self.escapement=escapement
        if escapement is None:
            self.escapement = Escapement(teeth=escapement_teeth)
        #
        self.escapement_time = pendulum_period * self.escapement.teeth
        # self.escapement_teeth = escapement_teeth
        # self.escapement_lift = 4
        # self.escapement_drop = 2
        # self.escapement_lock = 2
        # self.escapement_type = "deadbeat"

        # self.min_pinion_teeth=min_pinion_teeth
        # self.max_wheel_teeth=max_wheel_teeth
        # self.pinion_max_teeth = pinion_max_teeth
        # self.wheel_min_teeth = wheel_min_teeth
        self.trains=[]

    # def setEscapementDetails(self, lift = None, drop = None, lock=None, type=None):
    #     if lift is not None:
    #         self.lift = lift
    #     if drop is not None:
    #         self.drop = drop
    #     if lock is not None:
    #         self.lock = lock
    #     if type is not None:
    #         self.type = type

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
                    break
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
            if self.usingChain:
                chainWheelCircumference = self.chainWheel.circumference
            else:
                chainWheelCircumference = self.cordWheel.diameter*math.pi

            turns = self.poweredWheel.getTurnsForDrop(self.maxChainDrop)

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / self.hours

            desiredRatio = 1 / turnsPerHour

            print("Chain wheel turns per hour", turnsPerHour)
            print("Chain wheel ratio to minute wheel", desiredRatio)

            allGearPairCombos = []

            pinion_min = 10
            pinion_max = 20
            wheel_min = 20
            wheel_max = 120

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

    def genPowerWheelRatchet(self, ratchetThick=7.5):
        '''
        The ratchet and bits shared between chain and cord wheels
        '''
        if self.chainWheels == 0:
            self.chainWheelCircumference = self.maxChainDrop/self.hours
            self.max_chain_wheel_d = self.chainWheelCircumference/math.pi

        elif self.chainWheels == 1:
            self.chainWheelCircumference = self.max_chain_wheel_d * math.pi
            #use provided max_chain_wheel_d and calculate the rest

        # true for no chainwheels
        anticlockwise = self.chainAtBack

        for i in range(self.chainWheels):
            anticlockwise = not anticlockwise

        self.poweredWheelAnticlockwise = anticlockwise

    def genChainWheels(self, ratchetThick=7.5, holeD=3.3, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15,screwThreadLength=10):
        '''
        HoleD of 3.5 is nice and loose, but I think it's contributing to making the chain wheel wonky - the weight is pulling it over a bit
        Trying 3.3, wondering if I'm going to want to go back to the idea of a brass tube in the middle

        Generate the gear ratios for the wheels between chain and minute wheel
        again, I'd like to make this generic but the solution isn't immediately obvious and it would take
        longer to make it generic than just make it work
        '''

        self.genPowerWheelRatchet()


        self.chainWheel = ChainWheel(max_circumference=self.chainWheelCircumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)
        self.poweredWheel=self.chainWheel


        self.ratchet = Ratchet(totalD=self.max_chain_wheel_d * 2, innerRadius=self.chainWheel.outerDiameter / 2, thick=ratchetThick, powerAntiClockwise=self.poweredWheelAnticlockwise)

        self.chainWheel.setRatchet(self.ratchet)

        self.usingChain=True

    def genCordWheels(self,ratchetThick=7.5, rodMetricThread=3, cordCoilThick=10, useKey=False, cordThick=2, style="HAC", useFriction=False ):

        self.genPowerWheelRatchet()
        #slight hack, make this a little bit bigger as this works better with the standard 1 day clock (leaves enough space for the m3 screw heads)
        #21.2 comes from a mistake on clock 07, but a happy mistake as it was a good size. keeping this for now
        ratchetD = max(self.max_chain_wheel_d, 21.2)
        # ratchetD = 21.22065907891938
        self.ratchet = Ratchet(totalD=ratchetD * 2, thick=ratchetThick, powerAntiClockwise=self.poweredWheelAnticlockwise)

        self.cordWheel = CordWheel(self.max_chain_wheel_d, self.ratchet.outsideDiameter,self.ratchet,rodMetricSize=rodMetricThread, thick=cordCoilThick, useKey=useKey, cordThick=cordThick, style=style, useFriction=useFriction)
        self.poweredWheel = self.cordWheel
        self.usingChain=False

    def setTrain(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]

    def printInfo(self):
        print(self.trains[0])

        print("pendulum length: {}m period: {}s".format(self.pendulum_length, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement.teeth))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.getRunTime()))
        chainRatio = 1
        if self.chainWheels > 0:
            print(self.chainWheelRatio)
            chainRatio = self.chainWheelRatio[0]/self.chainWheelRatio[1]

        runtime = self.poweredWheel.getRunTime(chainRatio,self.maxChainDrop)

        print("runtime: {:.1f}hours. Chain wheel multiplier: {:.1f}".format(runtime, chainRatio))


    def genGears(self, module_size=1.5, holeD=3, moduleReduction=0.5, thick=6, chainWheelThick=-1, escapeWheelThick=-1, escapeWheelMaxD=-1, useNyloc=True, chainModuleIncrease=None, pinionThickMultiplier = 2.5, style="HAC", chainWheelPinionThickMultiplier=2):
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


        self.gearPinionEndCapLength=thick*0.25
        # self.gearTotalThick = self.gearWheelThick + self.gearPinionLength + self.gearPinionEndCapLength
        # self.chainGearTotalThick

        module_sizes = [module_size * math.pow(moduleReduction, i) for i in range(self.wheels)]

        #the module of each wheel is slightly smaller than the preceeding wheel
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_size* math.pow(moduleReduction, i)) for i,wheel in enumerate(self.trains[0]["train"])]




        # print(module_sizes)
        #make the escape wheel as large as possible, by default
        escapeWheelDiameter = (pairs[len(pairs)-1].centre_distance - pairs[len(pairs)-1].pinion.getMaxRadius() - 3)*2

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
        #escapment is now provided or configured in the constructor
        # self.escapement = Escapement(teeth=self.escapement_teeth, diameter=escapeWheelDiameter, type=self.escapement_type, lift=self.escapement_lift, lock=self.escapement_lock, drop=self.escapement_drop, anchorTeeth=None, clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide)
        self.escapement.setDiameter(escapeWheelDiameter)
        self.escapement.clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide
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
            self.chainWheelArbours=[Arbour(chainWheel=self.poweredWheel, wheel = self.chainWheelPair.wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=holeD, distanceToNextArbour=self.chainWheelPair.centre_distance, style=style)]
            pinionAtFront = not pinionAtFront

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                if self.chainWheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbour(chainWheel=self.poweredWheel, wheel = pairs[i].wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=holeD, distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=not self.chainAtBack)
                else:
                    #just a normal gear
                    arbour = Arbour(wheel = pairs[i].wheel, pinion=self.chainWheelPair.pinion, arbourD=holeD, wheelThick=thick, pinionThick=self.chainWheelArbours[-1].wheelThick*chainWheelPinionThickMultiplier, endCapThick=self.gearPinionEndCapLength, distanceToNextArbour= pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront)

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

        if self.usingChain:
            self.chainWheel.outputSTLs(name, path)
        else:
            self.cordWheel.outputSTLs(name, path)

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



class Escapement:
    def __init__(self, teeth=42, diameter=100, anchorTeeth=None, type="recoil", lift=4, drop=4, run=10, lock=2, clockwiseFromPinionSide=True, toothHeightFraction=0.2, toothTipAngle=9, toothBaseAngle=5.4):
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
        only makes sense for deadbeat

        clockwiseFromPinionSide is for the escape wheel
        '''

        self.lift_deg = lift
        self.halfLift = 0.5*degToRad(lift)
        self.lift = degToRad(lift)

        self.drop_deg= drop
        self.drop = degToRad(drop)

        self.lock_deg = lock
        self.lock=degToRad(lock)

        #to fine tune the teeth, the defaults work well with 30 teeth
        self.toothTipAngle=degToRad(toothTipAngle)
        self.toothBaseAngle=degToRad(toothBaseAngle)

        self.clockwiseFromPinionSide=clockwiseFromPinionSide
        self.run_deg = run
        self.run = degToRad(run)

        self.teeth = teeth
        self.toothHeightFraction = toothHeightFraction


        #it can't print a sharp tip, instead of the previous bodge with a different height for printing and letting the slicer do it, do it ourselves
        self.toothTipWidth=1

        self.type = type

        if anchorTeeth is None:
            # if type == "recoil":
            #     self.anchorTeeth = floor(self.teeth/4)+0.5
            # else:
            #     #very much TODO
            self.anchorTeeth = floor(self.teeth/4)+0.5
        else:
            self.anchorTeeth = anchorTeeth

        # angle that encompases the teeth the anchor encompases
        self.wheelAngle = math.pi * 2 * self.anchorTeeth / self.teeth

        #calculates things like tooth height from diameter
        self.setDiameter(diameter)


    def setDiameter(self, diameter):
        self.diameter = diameter
        # self.anchourDiameter=anchourDiameter

        self.innerDiameter = diameter * (1 - self.toothHeightFraction)

        self.radius = self.diameter / 2

        self.innerRadius = self.innerDiameter / 2

        self.toothHeight = self.diameter / 2 - self.innerRadius

        self.printedToothHeight = self.toothHeight
        # *8.36/7 worked for a diameter of about 82mm, it's not enough at about 60mm
        # self.printedToothHeight = self.toothHeight+1.4#*8.36/7
        # print("tooth height", self.toothHeight)

        # a tooth height of 8.36 gets printed to about 7mm

        # angle on teh wheel between teeth, not angle the tooth leans at
        self.toothAngle = math.pi * 2 / self.teeth

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
        '''
        Worked, but more by fluke than design, didn't properly take into account lift, drop and run
        '''
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
            nutSpace = cq.Workplane("XY").polygon(6,getNutContainingDiameter(nutMetricSize,NUT_WIGGLE_ROOM)).extrude(nutThick)
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
            toothTipAngle = -self.toothTipAngle#-math.pi*0.05
            toothBaseAngle = -self.toothBaseAngle#-math.pi*0.03
            toothTipArcAngle*=-1

        print("tooth tip angle: {} tooth base angle: {}".format(radToDeg(toothTipAngle), radToDeg(toothBaseAngle)))

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

        #rotate so a tooth is at 0deg on the edge of the entry pallet (makes animations of the escapement easier)
        wheel = wheel.rotate((0,0,0),(0,0,1),radToDeg(-toothTipAngle-toothTipArcAngle))

        return wheel
    def getWheelMaxR(self):
        return self.diameter/2

    def getWheel3D(self, thick=5, holeD=5, style="HAC", innerRadiusForStyle=-1):
        gear = self.getWheel2D().extrude(thick)

        if not self.clockwiseFromPinionSide:
            gear = gear.mirror("YZ", (0,0,0))

        rimThick = holeD*1.5
        #have toyed with making the escape wheel more solid to see if it improves the tick sound. not convinced it does
        rimRadius = self.innerRadius - holeD*0.5# - rimThick

        armThick = rimThick
        if style == "HAC":
            gear = Gear.cutHACStyle(gear, armThick, rimRadius)
        elif style == "circles":
            gear = Gear.cutCirclesStyle(gear, outerRadius=rimRadius, innerRadius=innerRadiusForStyle)

        # hole = cq.Workplane("XY").circle(holeD/2).extrude(thick+2).translate((0,0,-1))
        #
        # gear = gear.cut(hole)
        #for some reason this doesn't always work
        gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        return gear


    #hack to masquerade as a Gear, then we can use this with getArbour()
    def get3D(self, thick=5, holeD=5, style="HAC", innerRadiusForStyle=-1):
        return self.getWheel3D(thick=thick, holeD=holeD, style=style, innerRadiusForStyle=innerRadiusForStyle)

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

# class FrictionCordWheel:
#     '''
#     CordWheel works, but is very wide as it needs space to coil two cords - one for the weight and one to pull it up.
#
#     Instead this will be a hemp cord/rope (hemp should have more friction) with a counterweight and a V-shaped pulley.
#
#     Apparently this can work, I'll find out! Should be nearer to a drop in replacement for the chain wheel
#     '''
#
#     def __init__(self, diameter, cordDiameter=2.2, rodMetricSize=3, screwMetricSize=3):
#         self.diameter=diameter
#         self.cordDiameter=cordDiameter
#         self.rodMetricSize=rodMetricSize
#         self.screwMetricSize=screwMetricSize

class Pulley:
    '''
    Pulley wheel that can be re-used by all sorts of other things
    '''

    def __init__(self, diameter, cordDiameter=2.2, rodMetricSize=3, screwMetricSize=3, vShaped=False, style=None):
        self.diameter=diameter
        self.cordDiameter=cordDiameter
        self.vShaped=vShaped

        self.style=style

        #if negative, don't punch holes
        self.rodMetricSize=rodMetricSize
        self.rodHoleD = rodMetricSize + LOOSE_FIT_ON_ROD
        self.screwMetricSize=screwMetricSize

        self.edgeThick=cordDiameter*0.5
        self.taper = cordDiameter*0.2

    def getTotalThick(self):
        return self.edgeThick*2 + self.taper*2 + self.cordDiameter

    def getHalf(self):
        radius = self.diameter/2
        #from the side
        bottomPos = (radius + self.cordDiameter, 0)
        topOfEdgePos = (radius + self.cordDiameter, self.edgeThick)
        endOfTaperPos = (radius, self.edgeThick + self.taper)
        topPos = (endOfTaperPos[0]-self.cordDiameter/2, endOfTaperPos[1] + self.cordDiameter/2)

        # edgeR = self.diameter/2 + self.cordDiameter/4
        # middleR = self.diameter/2 - self.cordDiameter/2

        circle = cq.Workplane("XY").circle(self.diameter/2)
        pulley = cq.Workplane("XZ").moveTo(bottomPos[0], bottomPos[1]).lineTo(topOfEdgePos[0], topOfEdgePos[1]).lineTo(endOfTaperPos[0], endOfTaperPos[1])#.\

        if self.vShaped:
            pulley = pulley.lineTo(topPos[0], topPos[1])
        else:
            pulley = pulley.radiusArc(topPos, self.cordDiameter/2)

        pulley = pulley.lineTo(0,topPos[1]).lineTo(0,0).close().sweep(circle)
        # TODO cut out rod hole and screwholes if needed
        # if self.rodMetricSize > 0:
        #     shape = shape.faces(">Z").workplane().circle((self.rodMetricSize+LOOSE_FIT_ON_ROD)/2).cutThruAll()

        if self.style == "HAC":
            pulley = Gear.cutHACStyle(pulley,self.rodHoleD*0.75,self.diameter/2-self.rodHoleD*0.75, self.diameter/2)
        elif self.style == "circles":
            pulley = Gear.cutCirclesStyle(pulley, self.diameter/2-self.cordDiameter/2, innerRadius= self.rodHoleD, cantUseCutThroughAllBodgeThickness=self.getTotalThick())

        return pulley

class CordWheel:
    '''
    This will be a replacement for the chainwheel, instead of using a chain this will be clock cord.
    One end will be tied to the wheel and then the wheel wound up.

    Two options: use a key to wind it up, or have a double wheel and one half winds when the other unwinds, then you can tug the wound up side
    to wind up the weighted side.

    Made of two segments (one if using key) and a cap. Designed to be attached to the ratchet click wheel

    If useFriction is true: this will be a hemp cord/rope (hemp should have more friction) with a counterweight and a V-shaped pulley.
    Apparently this can work, I'll find out! Should be nearer to a drop in replacement for the chain wheel
    Didn't work.

    With key (but not gear) plan is for the key square bit (need name) to be part of the main segement, with a cap that just slots on top
    this makes the screws easier, hopefully
    '''

    def __init__(self, diameter, capDiameter, ratchet, rodMetricSize=3, thick=10, useKey=False, screwThreadMetric=3, cordThick=2, bearingInnerD=15, bearingHeight=5, keyKnobHeight=15, useGear=False, useFriction=False, gearThick=5, frontPlateThick=8, style="HAC", bearingLip=2.5, bearingOuterD=24):

        self.diameter=diameter
        #thickness of one segment
        self.thick=thick
        #if true, a key can be used to wind this cord wheel
        self.useKey=useKey
        #if true, this cord wheel has a gear and something (like a key) is used to turn that gear
        self.useGear=useGear
        #if true this is like the chain wheel, using friction and a counterweight for a loop of cord over the wheel
        self.useFriction = useFriction
        #1mm felt too flimsy
        self.capThick=2
        self.capDiameter = capDiameter
        self.rodMetricSize = rodMetricSize
        self.rodD=rodMetricSize+LOOSE_FIT_ON_ROD
        self.screwThreadMetric=screwThreadMetric
        #only if useKey is true will this be used
        self.bearingInnerD=bearingInnerD
        self.bearingOuterD=bearingOuterD
        self.bearingHeight=bearingHeight
        self.keyKnobHeight=keyKnobHeight
        self.gearThick = gearThick
        self.frontPlateThick=frontPlateThick
        # self.screwLength=screwLength

        self.style = style

        self.fixingDistance=self.diameter*0.3

        if self.useKey and not self.useGear:
            self.fixingDistance=self.diameter/2 - self.screwThreadMetric/2 - 3

        # # at angle so it can fit nicely with the polygon for the key - but this then clashes with teh simple cord hole
        # self.fixingPoints = [polar(math.pi / 4, self.fixingDistance), polar(math.pi + math.pi / 4, self.fixingDistance)]
        self.fixingPoints = [(self.fixingDistance,0), (-self.fixingDistance,0)]
        self.cordThick=cordThick

        #distance to keep the springs of the clickwheel from the cap, so they don't snag
        self.clickWheelExtra=LAYER_THICK*2
        self.beforeBearingExtraHeight= self.clickWheelExtra
        self.ratchet = ratchet
        self.keyScrewHoleD = self.screwThreadMetric

        if not self.useGear and not self.useKey and not self.useFriction:
            minScrewLength = self.ratchet.thick - (getScrewHeadHeight(self.screwThreadMetric) + LAYER_THICK) + self.clickWheelExtra + self.capThick * 2 + self.thick * 1.5
            if self.useKey:
                minScrewLength -= self.thick
            print("cord wheel screw length between", minScrewLength + getNutHeight(self.screwThreadMetric), minScrewLength + self.thick / 2 + self.capThick)
        elif self.useKey and not self.useGear and not self.useFriction:
            minScrewLength = self.ratchet.thick/2 + self.capThick*2 + self.thick
            print("cord wheel screw length between", minScrewLength, minScrewLength + self.ratchet.thick/2)
        #extra radius to add to stand off from a bearing
        self.bearingLip=bearingLip
        self.bearingWiggleRoom = 0.05
        self.keyWiggleRoom = 0.2

        #cap for key is extra chunky so there's space to put the nuts to hold it together
        self.keyCapExtraHeight=2

        # self.keyHeight = 20
        if self.useGear:
            wheelTeeth = 30
            # pinionTeeth = 11
            #TODO also want the pinion inner radius to be at last (bearingInnerD/2 + bearingLip)
            #do we actually we want the inner radius to be the same as the capdiameter? (inner_radius = pitch_radius - dedendum_height)
            module = self.capDiameter/wheelTeeth
            #fudging slightly to account for the innerradius rather than pitch circle
            pinionTeeth = math.ceil(1.4*(self.bearingInnerD + self.bearingLip*2)/module)
            self.wheelPinionPair = WheelPinionPair(wheelTeeth, pinionTeeth,module)
            # self.wheelPinionPair.wheel.innerRadiusForStyle =  self.diameter/2 + self.cordThick
            #self.gearDistance = self.wheelPinionPair.centre_distance
            self.keySize = math.sqrt(2) * (self.bearingInnerD / 2 - self.bearingWiggleRoom - 1)
            print("key size", self.keySize, "gear ratio", wheelTeeth/ pinionTeeth)

        if self.useFriction:
            self.pulley = Pulley(diameter=diameter, style=None)

    def getNutHoles(self):
        cutter = cq.Workplane("XY").add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).translate(self.fixingPoints[0]))
        cutter = cutter.add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).translate(self.fixingPoints[1]))
        return cutter

    def getPulleySegment(self, front=True):
        '''
        like the segment, but sufficiently not like it to have its own method
        '''
        segment = self.pulley.getHalf()

        holes = cq.Workplane("XY").pushPoints(self.fixingPoints).circle(self.screwThreadMetric/2).extrude(self.pulley.getTotalThick())

        # holes = cq.Workplane("XY")#.pushPoints(self.fixingPoints).makeCone(radius1=)

        if front:
            #countersunk screwhead holes
            for fixingPoint in self.fixingPoints:
                holes = holes.add(cq.Solid.makeCone(radius1=getScrewHeadDiameter(self.screwThreadMetric, countersunk=True)/2 + COUNTERSUNK_HEAD_WIGGLE, radius2=self.screwThreadMetric/2, height=getScrewHeadHeight(self.screwThreadMetric, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE).translate((fixingPoint[0], fixingPoint[1], 0)))

        holes = holes.add(cq.Workplane("XY").circle(self.rodD/2).extrude(self.pulley.getTotalThick()))
        segment = segment.cut(holes)

        return segment

    def getSegment(self, front=True):
        #if front segment, the holes for screws/nuts will be different
        #not for pulley (useFriction true)

        if self.useGear:
            #end is a gear
            segment = self.wheelPinionPair.wheel.get3D(holeD=self.rodD, thick=self.gearThick, innerRadiusForStyle=self.diameter/2 + self.cordThick, style=self.style)
        else:
            #end is the cap
            segment = self.getCap()

        #where the cord wraps
        segment = segment.faces(">Z").workplane().circle(self.diameter/2).extrude(self.thick)



        if not self.useGear and self.useKey:
            #put the key on the top!

            #space for the cap

            # segment = segment.faces(">Z").workplane().moveTo(0, 0).circle(self.bearingInnerD / 2 + self.bearingLip).extrude(self.beforeBearingExtraHeight)
            segment = segment.faces(">Z").workplane().moveTo(0, 0).circle(self.bearingInnerD / 2 - self.bearingWiggleRoom).extrude(self.bearingHeight + self.beforeBearingExtraHeight + self.capThick)
            #using polygon rather than rect so it calcualtes the size to fit in teh circle, rotating 45deg so we have more room for the screw heads
            key = cq.Workplane("XY").polygon(4, self.bearingInnerD - self.bearingWiggleRoom*2).extrude(self.keyKnobHeight)
            segment = segment.add(key.rotate((0,0,0),(0,0,1),45).translate((0,0,self.capThick + self.thick + self.bearingHeight + self.beforeBearingExtraHeight + self.capThick)))

            countersink = self.getScrewCountersinkCutter(self.thick + self.capThick*2)
            segment = segment.cut(countersink)

        #hole for the rod
        segment = segment.faces(">Z").circle(self.rodD/2).cutThruAll()

        #holes for the screws that hold this together
        segment = segment.faces(">Z").pushPoints(self.fixingPoints).circle(self.screwThreadMetric/2).cutThruAll()

        if front or self.useGear:
            #base of this needs space for the nuts
            #current plan is to put the screw heads in the ratchet, as this side gives us more wiggle room for screws of varying length
            segment = segment.cut(self.getNutHoles())





        cordHoleR = 1.5*self.cordThick/2
        cordHoleZ = self.capThick + cordHoleR
        if self.useGear:
            cordHoleZ = self.gearThick + cordHoleR

        #cut a hole so we can tie the cord
        cordHole = cq.Workplane("YZ").moveTo(self.diameter*0.25,cordHoleZ).circle(cordHoleR).extrude(self.diameter*4).translate((-self.diameter*2,0,0))

        segment = segment.cut(cordHole)

        return segment

    def getScrewCountersinkCutter(self, topOfScrewhead):
        countersink = cq.Workplane("XY")
        for fixingPoint in self.fixingPoints:
            coneHeight = getScrewHeadHeight(self.screwThreadMetric, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE
            topR = getScrewHeadDiameter(self.screwThreadMetric, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE
            countersink = countersink.add(cq.Solid.makeCone(radius2=topR, radius1=self.screwThreadMetric / 2,
                                                            height=coneHeight).translate((fixingPoint[0], fixingPoint[1], topOfScrewhead - coneHeight)))
            # punch thorugh the top circle so the screw can get in
            #self.beforeBearingExtraHeight
            top = cq.Workplane("XY").circle(topR).extrude(100).translate((fixingPoint[0], fixingPoint[1], topOfScrewhead))

            countersink = countersink.add(top)
        return countersink

    def getCap(self, top=False, extraThick=0):
        cap = cq.Workplane("XY").circle(self.capDiameter/2).extrude(self.capThick + extraThick)

        holeR = self.rodD / 2
        if self.useKey and not self.useGear and top:
            holeR = self.bearingInnerD/2 + self.bearingWiggleRoom

            #add small ring to keep this further away from the bearing
            cap = cap.faces(">Z").workplane().circle(holeR).circle(self.bearingInnerD/2 + self.bearingLip).extrude(self.beforeBearingExtraHeight)
            #add space for countersunk screw heads
            countersink = self.getScrewCountersinkCutter(self.capThick + extraThick)
            cap = cap.cut(countersink)

        # hole for the rod
        cap = cap.cut(cq.Workplane("XY").circle(holeR).extrude(self.capThick*10))

        # holes for the screws that hold this together
        cap = cap.faces(">Z").pushPoints(self.fixingPoints).circle(self.screwThreadMetric / 2).cutThruAll()
        if self.style == "HAC":
            cap = Gear.cutHACStyle(cap,self.rodD*0.75,self.capDiameter/2-self.rodD*0.75, self.diameter/2 + self.cordThick)
        elif self.style == "circles":
            cap = Gear.cutCirclesStyle(cap, self.capDiameter/2-self.rodD*0.75, innerRadius= self.diameter / 2 + self.cordThick)

        return cap

    def getKeyShape(self, shape):
        '''
        just part of the key
        '''

        keyCap = shape.faces(">Z").workplane().moveTo(0, 0).circle(self.bearingInnerD / 2 + 1).extrude(self.beforeBearingExtraHeight)
        keyCap = keyCap.faces(">Z").workplane().moveTo(0, 0).circle(self.bearingInnerD / 2 - self.bearingWiggleRoom).extrude(self.bearingHeight)
        keyCap = keyCap.faces(">Z").workplane().moveTo(0, 0).polygon(4, self.bearingInnerD - self.bearingWiggleRoom).extrude(self.keyKnobHeight)

        return keyCap


    def getKeyCap(self):
        '''
        Cap for the top, but with a key as well
        This is not quite finished, no hole for the nuts, but I don't think I'm going to use it as I want to gear down for a key to pull 2.5kg
        '''
        # screwHeight =
        #extra height so we have soemthign to hold the nuts

        keyCap = self.getCap(extraThick=self.keyCapExtraHeight)

        keyCap = self.getKeyShape(keyCap)


        keyCap = keyCap.faces(">Z").workplane().moveTo(0, 0).circle(self.rodD/2).cutThruAll()
        return keyCap

    # def getGearSegment(self):
    #
    #     gearCap = self.wheelPinionPair.wheel.get3D(holeD=self.rodD, thick=self.gearThick)
    #
    #     gearCap = gearCap.cut(self.getNutHoles())
    #
    #     return gearCap

    def getClickWheelForCord(self):
        clickwheel = self.ratchet.getInnerWheel()

        clickwheel = clickwheel.faces(">Z").workplane().circle(self.ratchet.clickInnerRadius*0.999).extrude(self.clickWheelExtra)

        # hole for the rod
        clickwheel = clickwheel.faces(">Z").circle(self.rodD / 2).cutThruAll()

        # holes for the screws that hold this together
        clickwheel = clickwheel.faces(">Z").pushPoints(self.fixingPoints).circle(self.screwThreadMetric / 2).cutThruAll()

        if self.useFriction or (self.useKey and not self.useGear):
            #space for a nut

            cutter = cq.Workplane("XY")
            for fixingPoint in self.fixingPoints:
                cutter = cutter.add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, 0.2), self.ratchet.thick/2, sides=6).translate(fixingPoint))
        else:
            #cut out space for screwheads
            # cutter = cq.Workplane("XY").pushPoints(self.fixingPoints).circle(getScrewHeadDiameter(self.screwThreadMetric) / 2).extrude(getScrewHeadHeight(self.screwThreadMetric))
            cutter = cq.Workplane("XY").add(getHoleWithHole(self.screwThreadMetric, getScrewHeadDiameter(self.screwThreadMetric), getScrewHeadHeight(self.screwThreadMetric)+LAYER_THICK).translate(self.fixingPoints[0]))
            cutter = cutter.add(getHoleWithHole(self.screwThreadMetric, getScrewHeadDiameter(self.screwThreadMetric), getScrewHeadHeight(self.screwThreadMetric) + LAYER_THICK).translate(self.fixingPoints[1]))
        clickwheel = clickwheel.cut(cutter)



        return clickwheel

    def getKeyGear(self):
        '''
        If using gear, this is the gear that the key slots into
        designed to be two parts screwed together on either side of a bearing in the front plate with a larger inner diameter
        '''
        holeD = self.keyScrewHoleD

        keyGear = self.wheelPinionPair.pinion.get3D(holeD=holeD, thick=self.gearThick)

        keyGear = keyGear.faces(">Z").workplane().circle(self.bearingInnerD/2 + self.bearingLip).extrude(self.beforeBearingExtraHeight)

        keyGear = keyGear.faces(">Z").workplane().circle(self.bearingInnerD / 2 - self.bearingWiggleRoom).extrude(self.bearingHeight)

        keySquareHole = cq.Workplane("XY").rect(self.keySize, self.keySize).extrude(self.bearingHeight).translate((0,0,self.gearThick + self.beforeBearingExtraHeight))

        keyGear = keyGear.cut(keySquareHole)

        keyGear = keyGear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        screwHeadHole = getHoleWithHole(self.screwThreadMetric,getScrewHeadDiameter(self.screwThreadMetric)+0.5,getScrewHeadHeight(self.screwThreadMetric))

        keyGear = keyGear.cut(screwHeadHole)

        return keyGear

    def getKeyKey(self):
        '''
        If using gear and key ,this is the square bit that will be out the front of the clock
        '''
        key = cq.Workplane("XY").rect(self.keySize-self.keyWiggleRoom, self.keySize - self.keyWiggleRoom).extrude(self.keyKnobHeight + self.bearingHeight)

        key = key.faces(">Z").workplane().circle(self.keyScrewHoleD / 2).cutThruAll()

        nutHeight = getNutHeight(self.screwThreadMetric)
        nutSpace = cq.Workplane("XY").polygon(6, getNutContainingDiameter(self.screwThreadMetric,0.2)).extrude(nutHeight).translate((0,0,self.keyKnobHeight + self.bearingHeight - nutHeight))

        key = key.cut(nutSpace)

        #this is a bit that sticks out so the gear can't fall inside the clock.
        #TODO take into account the front plate thickness, not just the bearing thickness
        clampyBitThick = 2
        clampyBit = cq.Workplane("XY").circle(self.bearingInnerD/2 + self.bearingLip).extrude(clampyBitThick)
        cutOffClampyBit = cq.Workplane("XY").moveTo(-self.bearingInnerD,-(self.keySize - self.keyWiggleRoom)/2).line(self.bearingInnerD*2,0).line(0,-self.bearingInnerD).line(-self.bearingInnerD*2,0).close().extrude(clampyBitThick)
        clampyBit = clampyBit.cut(cutOffClampyBit).translate((0,0,self.bearingHeight))

        clampyBit = clampyBit.faces(">Z").workplane().circle(self.keyScrewHoleD / 2).cutThruAll()
        # return clampyBit
        # clampyBit = cq.Workplane("XY").moveTo()
        key = key.add(clampyBit)


        # this needs to be sideways so we can print a lip that will hold it against the top of the bearing

        return key


    def getRunTime(self, minuteRatio=1, cordLength=2000):
        '''
        minuteRatio is teeth of chain wheel divided by pinions of minute wheel, or just 1 if there aren't any chainwheels
        therefore the chain wheel rotates by 1/minuteRatio per hour

        assuming the cord coils perfectly, make a reasonable estimate at runtime
        '''
        (rotations, layers, cordPerRotationPerLayer) = self.getCordTurningInfo(cordLength)

        print("layers of cord: {}, cord per hour: {:.1f}cm to {:.1f}cm".format(layers, (cordPerRotationPerLayer[-1] / minuteRatio) / 10, (cordPerRotationPerLayer[0] / minuteRatio) / 10))

        #minute hand rotates once per hour, so this answer will be in hours
        return (rotations * minuteRatio)

    def getCordTurningInfo(self, cordLength):
        '''
        returns (rotations, layers, cordPerRotationPerLayer)
        '''
        lengthSoFar = 0
        rotationsSoFar = 0
        coilsPerLayer = floor(self.thick / self.cordThick)
        layer = 0
        cordPerRotationPerLayer = []
        while lengthSoFar < cordLength:

            circumference = math.pi * (self.diameter + 2 * (layer * self.cordThick + self.cordThick / 2))
            cordPerRotationPerLayer.append(circumference)
            if lengthSoFar + circumference * coilsPerLayer < cordLength:
                # assume this hole layer is used
                lengthSoFar += circumference * coilsPerLayer
                rotationsSoFar += coilsPerLayer
            else:
                # not all of this layer
                lengthLength = cordLength - lengthSoFar
                rotationsSoFar += lengthLength / circumference
                break

            layer += 1
        return (rotationsSoFar, layer + 1, cordPerRotationPerLayer)


    def getTurnsForDrop(self, cordLength):


        return self.getCordTurningInfo(cordLength)[0]


    def getAssembled(self):

        model = self.getClickWheelForCord()
        if self.useKey and not self.useGear:
            model = model.add(self.getSegment(False).translate((0,0,self.ratchet.thick + self.clickWheelExtra)))
            model = model.add(self.getCap(top=True).translate((0, 0, self.ratchet.thick + self.clickWheelExtra + self.thick + self.capThick)))
        elif self.useGear:
            model = model.add(self.getCap().translate((0, 0, self.ratchet.thick + self.clickWheelExtra)))
            model = model.add(self.getSegment(False).mirror().translate((0,0,self.thick + self.gearThick)).translate((0,0,self.ratchet.thick + self.capThick + self.clickWheelExtra)))
            model = model.add(self.getKeyGear().translate((0,-self.wheelPinionPair.centre_distance,self.ratchet.thick + self.capThick + self.clickWheelExtra + self.thick )))
            model = model.add(self.getKeyKey().translate((0, -self.wheelPinionPair.centre_distance, self.ratchet.thick + self.capThick + self.clickWheelExtra + self.thick + self.gearThick + self.beforeBearingExtraHeight)))
        else:

            if self.useFriction:
                model = model.add(self.getPulleySegment(front=False).translate((0,0,self.ratchet.thick + self.clickWheelExtra)))
                model = model.add(self.getPulleySegment(front=True).mirror().translate((0,0,self.pulley.getTotalThick()/2)).translate((0, 0, self.ratchet.thick + self.clickWheelExtra + self.pulley.getTotalThick()/2)))
            else:
                model = model.add(self.getCap().translate((0, 0, self.ratchet.thick + self.clickWheelExtra)))
                model = model.add(self.getSegment(False).mirror().translate((0,0,self.thick + self.capThick)).translate((0,0,self.ratchet.thick + self.capThick + self.clickWheelExtra)))
                model = model.add(self.getSegment(True).mirror().translate((0,0,self.thick + self.capThick)).translate((0,0,self.ratchet.thick + self.clickWheelExtra + self.capThick + self.thick + self.capThick)))



        return model

    def getHeight(self):
        '''
        only ones currently working are: (!friction && !gear && !key) or (friction)

        NOTE = includes heighto of a washer as part of the cordwheel
        '''

        if self.useKey:
            return self.ratchet.thick + self.clickWheelExtra*2 + self.capThick*2 + self.thick
        elif self.useGear:
            return self.ratchet.thick + self.clickWheelExtra + self.capThick + self.thick + self.gearThick + WASHER_THICK

        if self.useFriction:
            return self.ratchet.thick + self.clickWheelExtra + self.pulley.getTotalThick() + WASHER_THICK

        #total ehight, once assembled
        #include space for a washer at the end, to stop the end cap rubbing too much on the top plate (wasn't really the same problem with the much smaller chain wheel)
        return self.ratchet.thick + self.clickWheelExtra + self.capThick*3 + self.thick*2 + WASHER_THICK

    def outputSTLs(self, name="clock", path="../out"):

        if self.useFriction:
            out = os.path.join(path, "{}_cordwheel_pulley_segment.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getPulleySegment(front=False), out)

            out = os.path.join(path, "{}_cordwheel_pulley_segment_front.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getPulleySegment(front=True), out)
        else:

            out = os.path.join(path, "{}_cordwheel_bottom_segment.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getSegment(False), out)

            if not self.useKey and not self.useGear:
                out = os.path.join(path, "{}_cordwheel_cap.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.getCap(), out)

                out = os.path.join(path, "{}_cordwheel_top_segment.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.getSegment(True), out)

            if self.useKey and not self.useGear:
                out = os.path.join(path, "{}_cordwheel_top_cap.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.getCap(top=True), out)

        out = os.path.join(path, "{}_cordwheel_click.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getClickWheelForCord(), out)



class ChainWheel:
    '''
    This is a pocket chain wheel, printed in two parts.

    Works well for lighter (<1kg) weights, doesn't work reliably for heavier weights.

    Note it's fiddly to get the tolerance right, you want a larger tolerance value ot make it more reliable, but then you get a little 'clunk'
    every time a link leaves.

    '''
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

    def getTurnsForDrop(self, chainDrop):
        return chainDrop / self.circumference

    def getHeight(self):
        '''
        Returns total height of the chain wheel, once assembled, including the ratchet
        '''
        return self.inner_width + self.wall_thick*2 + self.extra_height + self.ratchet.thick

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

    def setRatchet(self, ratchet):
        self.ratchet=ratchet

    def outputSTLs(self, name="clock", path="../out"):

        out = os.path.join(path,"{}_chain_wheel_with_click.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getWithRatchet(self.ratchet), out)
        out = os.path.join(path, "{}_chain_wheel_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHalf(False), out)


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
    gearWheel = gear.get3D(holeD=holeD, thick=thick, style=style, innerRadiusForStyle=ratchet.outsideDiameter*0.5)

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

    # def getArbour(self, wheel, pinion, holeD=0, thick=0, style="HAC"):
    #     base = wheel.get3D(thick=thick, holeD=holeD, style=style)
    #
    #     top = pinion.get3D(thick=thick * 3, holeD=holeD, style=style).translate([0, 0, thick])
    #
    #     arbour = base.add(top)
    #
    #     arbour = arbour.faces(">Z").workplane().circle(pinion.getMaxRadius()).extrude(thick * 0.5).circle(holeD / 2).cutThruAll()
    #     return arbour

    def getMotionArbour(self):
        #mini arbour that sits between the cannon pinion and the hour wheel
        wheel = self.pairs[0].wheel
        pinion = self.pairs[1].pinion

        base = wheel.get3D(thick=self.thick, holeD=self.holeD, style=self.style, innerRadiusForStyle= pinion.getMaxRadius())

        top = pinion.get3D(thick=self.thick * 3, holeD=self.holeD, style=self.style).translate([0, 0, self.thick])

        arbour = base.add(top)

        arbour = arbour.faces(">Z").workplane().circle(pinion.getMaxRadius()).extrude(self.thick * 0.5).circle(self.holeD / 2).cutThruAll()
        return arbour

        return getArbour(self.pairs[0].wheel, self.pairs[1].pinion,holeD=self.holeD, thick = self.thick, style=self.style)

    def getHourHolder(self):
        #the final wheel and arm that friction holds the hour hand

        # want it tapered so an hour hand can be pushed down for a friction fit
        topR = self.hourHandHolderD / 2 - 0.5
        midR = self.hourHandHolderD / 2
        bottomR = self.hourHandHolderD / 2

        #TODO the sides need to slope in slightly to make the friction fit easier
        hour = self.pairs[1].wheel.get3D(holeD=self.holeD,thick=self.thick,style=self.style, innerRadiusForStyle=bottomR)

        height = self.minuteHolderTotalHeight - self.cannonPinionThick - self.thick - self.thick  - self.minuteHandSlotHeight - self.space

        # hour = hour.faces(">Z").workplane().circle(self.hourHandHolderD/2).extrude(height)



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
    def __init__(self, goingTrain, motionWorks, pendulum, style="vertical", arbourD=3, bearingOuterD=10, bearingHolderLip=1.5, bearingHeight=4, screwheadHeight=2.5, pendulumAtTop=True, fixingScrewsD=3, plateThick=5, pendulumSticksOut=20, name="", dial=None, heavy=False, motionWorksAbove=False):
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

        self.motionWorksAbove=motionWorksAbove

        #is the weight heavy enough that we want to chagne the plate design?
        self.heavy = heavy

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

        if self.bearingPositions[-1][2] == 0:
            #the anchor would be directly up against the plate
            self.bearingPositions[-1][2] = WASHER_THICK#self.anchorThick*0.25

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
            self.motionWorksRelativePos = [0, motionWorksDistance * (1 if self.motionWorksAbove else -1)]
        if self.goingTrain.usingChain:
            self.chainHoleD = self.goingTrain.chainWheel.chain_width + 2
        else:
            self.chainHoleD = self.goingTrain.cordWheel.cordThick*3

        self.weightOnRightSide = self.goingTrain.isWeightOnTheRight()

        #absolute z position
        self.embeddedNutHeight = self.plateThick + self.plateDistance - 20


    def getPlate(self, back=True, getText=False):
        if self.style in ["round", "vertical"]:
            return self.getSimplePlate(back, getText)

    def getSimplePlate(self, back=True, getText=False):
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

        #original thinking was to make it the equivilant of a 45deg shelf bracket, but this is massive once cord wheels are used
        #so instead, make it just big enough to contain the holes for the chains/cord
        # bottomPillarR= self.plateDistance/2
        bottomPillarR = (self.goingTrain.poweredWheel.diameter + self.chainHoleD*2)/2
        topPillarR = holderWide/2







        if self.style == "round":
            screwHoleY = chainWheelR*1.4
        elif self.style == "vertical":
            screwHoleY = self.bearingPositions[-3][1] + (self.bearingPositions[-2][1] - self.bearingPositions[-3][1])*0.6

        chainX = 0

        weightOnSide = 1 if self.weightOnRightSide else -1
        if self.heavy:
            # line up the hole with the big heavy weight
            chainX = weightOnSide*self.goingTrain.poweredWheel.diameter/2

        #hole for hanging on the wall
        screwHolePos = (chainX , screwHoleY)

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


        plate = plate.tag("top")
        # #for the screwhole
        # screwHeadD = 9
        # screwBodyD = 6
        # slotLength = 7

        if back:
            #extra bit around the screwhole
            #r = self.goingTrain.chainWheel.diameter*1.25
            # plate = plate.workplaneFromTagged("base").moveTo(screwHolePos[0], screwHolePos[1]-7-11/2).circle(holderWide*0.75).extrude(self.plateThick)
            backThick = max(self.plateThick-5, 4)
            plate = self.addScrewHole(plate, screwHolePos, backThick=backThick, screwHeadD=11, addExtraSupport=True)
            #the pillars
            plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR*0.999).extrude(self.plateThick + self.plateDistance)
            plate = plate.workplaneFromTagged("base").moveTo(topPillarPos[0], topPillarPos[1]).circle(topPillarR*0.999).extrude(self.plateThick + self.plateDistance)

            textMultiMaterial = cq.Workplane("XY")
            textSize = topPillarR * 0.9
            textY = (self.bearingPositions[0][1] + fixingPositions[2][1])/2
            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{} {:.1f}".format(self.name, self.goingTrain.pendulum_length * 100), (-textSize*0.5, textY), textSize)

            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{}".format(datetime.date.today().strftime('%Y-%m-%d')), (textSize*0.5, textY), textSize)

            if getText:
                return textMultiMaterial

        plate = self.punchBearingHoles(plate, back)


        if back:



            chainHoles = self.getChainHoles(absoluteZ=True)
            plate = plate.cut(chainHoles)
        else:
           plate = self.frontAdditionsToPlate(plate)

        fixingScrewD = 3

        #screws to fix the plates together
        # if back:
        plate = plate.faces(">Z").workplane().pushPoints(fixingPositions).circle(fixingScrewD / 2).cutThruAll()
        # else:
        #can't get the countersinking to work
        #     plate = plate.workplaneFromTagged("top").pushPoints(fixingPositions).cskHole(diameter=fixingScrewD, cskAngle=90, cskDiameter=getScrewHeadDiameter(fixingScrewD), depth=None)#.cutThruAll()



        for fixingPos in fixingPositions:
            #embedded nuts!
            plate = plate.cut(getHoleWithHole(fixingScrewD,getNutContainingDiameter(fixingScrewD,NUT_WIGGLE_ROOM), getNutHeight(fixingScrewD)*1.4, sides=6).translate((fixingPos[0], fixingPos[1], self.embeddedNutHeight)))

        return plate

    def getChainHoles(self, absoluteZ=False):
        '''
        if absolute Z is false, these are positioned above the base plateThick
        this assumes an awful lot, it's likely to be a bit fragile
        '''
        if self.goingTrain.usingChain:
            chainZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - (self.goingTrain.chainWheel.getHeight() - self.goingTrain.chainWheel.ratchet.thick) / 2 + self.wobble/2
            leftZ = chainZ
            rightZ = chainZ
        else:
            if self.goingTrain.cordWheel.useFriction:
                #basically a chain wheel that uses friction instead of chain links
                chainZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.pulley.getTotalThick()/2 + self.wobble / 2
                leftZ = chainZ
                rightZ = chainZ
            else:
                #assuming a two-section cord wheel, one side coils up as the weight coils down
                #cord, leaving enough space for the washer as well (which is hackily included in getTotalThickness()
                bottomZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.thick*1.5 - self.goingTrain.cordWheel.capThick*2 + self.wobble / 2
                topZ = bottomZ +  self.goingTrain.cordWheel.thick - self.goingTrain.cordWheel.capThick

                if self.weightOnRightSide:
                    rightZ = bottomZ
                    leftZ = topZ
                else:
                    rightZ = topZ
                    leftZ = bottomZ

        if absoluteZ:
            leftZ += self.plateThick
            rightZ += self.plateThick

        chainHoles = cq.Workplane("XZ").pushPoints([(self.goingTrain.poweredWheel.diameter / 2, rightZ), (-self.goingTrain.poweredWheel.diameter / 2, leftZ)]).circle(self.chainHoleD / 2).extrude(1000)

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

    def addScrewHole(self, plate, screwholePos, screwHeadD = 9, screwBodyD = 6, slotLength = 7, backThick = -1, addExtraSupport=False):
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

        if addExtraSupport:
            #a circle around the big hole to strengthen the plate
            #assumes plate has been tagged
            extraSupportSize = screwHeadD*1.25
            supportCentre=[screwholePos[0], screwholePos[1]- slotLength]
            if self.heavy:
                extraSupportSize*=1.5
                supportCentre[0] += (-1 if self.weightOnRightSide else 1) * extraSupportSize*0.25
                supportCentre[1] += slotLength/2
            plate = plate.workplaneFromTagged("base").moveTo(supportCentre[0], supportCentre[1] ).circle(extraSupportSize).extrude(self.plateThick)

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

        nutDeep = getNutHeight(self.fixingScrewsD, halfHeight=True)
        screwheadHeight = getScrewHeadHeight(self.fixingScrewsD)
        #ideally want a nut embedded on the top, but that can leave the plate a bit thin here

        nutZ = max(screwheadHeight + 3, self.plateThick - nutDeep)
        nutSpace = cq.Workplane("XY").polygon(6, getNutContainingDiameter(self.fixingScrewsD)).extrude(nutDeep).translate(
            (self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1], nutZ))

        plate = plate.cut(nutSpace)

        screwheadSpace =  getHoleWithHole(self.fixingScrewsD, getScrewHeadDiameter(self.fixingScrewsD)+0.5, screwheadHeight).translate((self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1], 0))

        plate = plate.cut(screwheadSpace)

        if self.dial is not None:
            dialFixings = self.dial.getFixingDistance()
            minuteY = self.bearingPositions[self.goingTrain.chainWheels][1]
            plate = plate.faces(">Z").workplane().pushPoints([(0, minuteY + dialFixings / 2), (0, minuteY - dialFixings / 2)]).circle(self.dial.fixingD / 2).cutThruAll()

        # need an extra chunky hole for the big bearing that the key slots through
        if not self.goingTrain.usingChain and self.goingTrain.cordWheel.useKey and not self.goingTrain.cordWheel.useGear:
            cordWheel = self.goingTrain.cordWheel
            # cordBearingHole = cq.Workplane("XY").circle(cordWheel.bearingOuterD/2).extrude(cordWheel.bearingHeight)
            cordBearingHole = getHoleWithHole(cordWheel.bearingInnerD + cordWheel.bearingLip * 2, cordWheel.bearingOuterD, cordWheel.bearingHeight)
            cordBearingHole = cordBearingHole.faces(">Z").workplane().circle(cordWheel.bearingInnerD/2 + cordWheel.bearingLip).extrude(self.plateThick)

            plate = plate.cut(cordBearingHole.translate((self.bearingPositions[0][0], self.bearingPositions[0][1],0)))

        return plate

    def getArbourExtension(self, arbourID, top=True, arbourD=3, forModel=False):
        '''
        Get little cylinders we can use as spacers to keep the gears in the right place on the rod
        arbour from -chainwheels to +ve wheels + 1 (for the anchor)

        if for model, will return the way up needed to assemble the little model

        returns None if no extension is needed
        '''

        flaredBase = False

        bearingPos = self.bearingPositions[arbourID + self.goingTrain.chainWheels]
        if arbourID < self.goingTrain.wheels:
            arbourThick = self.goingTrain.getArbour(arbourID).getTotalThickness()
        else:
            #anchor!
            arbourThick = self.pendulum.anchorThick
            #the bearing is on the front of the plate! need something to stop it falling through the gap
            if self.pendulumSticksOut > 0 and top:
                flaredBase = True

        length = 0
        if top:
            length = self.plateDistance - arbourThick - bearingPos[2] - self.wobble
        else:
            length = bearingPos[2]

        if length > LAYER_THICK:
            extendoArbour = cq.Workplane("XY").tag("base").circle(arbourD).circle(arbourD/2).extrude(length)

            if flaredBase:
                baseLength = min(2, length)
                extendoArbour = extendoArbour.workplaneFromTagged("base").circle(arbourD*2).circle(arbourD).extrude(baseLength)
                if forModel:
                    extendoArbour = extendoArbour.mirror().translate((0,0,length))

            return extendoArbour
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


    def getBob(self, hollow=True):


        circle = cq.Workplane("XY").circle(self.bobR)

        #nice rounded edge
        bob = cq.Workplane("XZ").lineTo(self.bobR,0).radiusArc((self.bobR,self.bobThick),-self.bobThick*0.9).lineTo(0,self.bobThick).close().sweep(circle)

        #was 0.5, which is plenty of space, but can slowly rotate. 0.1 seems to be a tight fit that help stop it rotate over time
        extraR=0.1



        #rectangle for the nut, with space for the threaded rod up and down
        cut = cq.Workplane("XY").rect(self.gapWidth, self.gapHeight).extrude(self.bobThick*2).faces(">Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+extraR).extrude(self.bobR*2).\
            faces("<Y").workplane().moveTo(0,self.bobThick/2).circle(self.threadedRodM/2+extraR).extrude(self.bobR*2)
        bob=bob.cut(cut)


        if hollow:
            # could make hollow with shell, but that might be hard to print, so doing it manually
            # bob = bob.shell(-2)
            weightHole = cq.Workplane("XY").circle(self.bobR - self.wallThick).extrude(self.bobThick-self.wallThick*2).translate((0,0,self.wallThick))

            notHole = cut.shell(self.wallThick)
            #don't have a floating tube through the middle, give it something below
            notHole = notHole.add(cq.Workplane("XY").rect(self.threadedRodM+extraR*2 + self.wallThick*2, self.bobR*2).extrude(self.bobThick/2 - self.wallThick).translate((0,0,self.wallThick)))

            for pos in self.bobLidNutPositions:
                notHole = notHole.add(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(self.nutMetricSize*1.5).circle(self.nutMetricSize/2).extrude(self.bobThick-self.wallThick))

            weightHole = weightHole.cut(notHole)

            lid = self.getBobLid(True)

            weightHole = weightHole.add(lid.translate((0,0,self.bobThick-self.wallThick)))

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

        out = os.path.join(path, "{}_bob_solid.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getBob(hollow=False), out)

        out = os.path.join(path, "{}_bob_nut.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getBobNut(), out)

        out = os.path.join(path, "{}_bob_lid.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getBobLid(), out)


class Hands:
    def __init__(self, style="simple", minuteFixing="rectangle", hourFixing="circle", secondFixing="rod", minuteFixing_d1=1.5, minuteFixing_d2=2.5, hourfixing_d=3, secondFixing_d=3, length=25, secondLength=30, thick=1.6, fixing_offset=0, outline=0, outlineSameAsBody=True, handNutMetricSize=3):
        '''

        '''
        self.thick=thick
        #usually I print multicolour stuff with two layers, but given it's entirely perimeter I think it will look okay with just one
        self.outlineThick=LAYER_THICK
        #how much to rotate the minute fixing by
        self.fixing_offset=fixing_offset
        self.length = length
        self.style=style
        self.minuteFixing=minuteFixing
        self.minuteFixing_d1 = minuteFixing_d1
        self.minuteFixing_d2 = minuteFixing_d2
        self.secondFixing=secondFixing
        self.secondFixing_d = secondFixing_d
        self.secondFixing_thick = self.thick
        self.secondLength= secondLength
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

    def cutFixing(self, hand, hour, second=False):
        if second and self.secondFixing == "rod":
            #second hand, assuming threaded onto a threaded rod
            hand = hand.workplaneFromTagged("base").moveTo(0,0).circle(self.secondFixing_d).extrude(self.secondFixing_thick + self.thick)
            hand = hand.moveTo(0, 0).circle(self.secondFixing_d/2).cutThruAll()
            return hand

        if not hour and self.minuteFixing == "rectangle":
            #minute hand, assuming square or rectangle
            hand = hand.moveTo(0, 0).rect(self.minuteFixing_d1, self.minuteFixing_d2).cutThruAll()
        elif hour and self.hourFixing == "circle":
            #hour hand, assuming circular friction fit
            hand = hand.moveTo(0, 0).circle(self.hourFixing_d / 2).cutThruAll()
        else:
            #major TODO would be a collet for the minute hand
            raise ValueError("Combination not supported yet")

        return hand

    def getHand(self, hour=True, outline=False, second=False):
        '''
        if hour is true this ist he hour hand
        if outline is true, this is just the bit of the shape that should be printed in a different colour
        if second is true, this overrides hour and this is the second hand
        '''
        base_r = self.base_r
        length = self.length
        # width = self.length * 0.3
        if hour:
            length = self.length * 0.8
            # if self.style == "simple":
            #     width = width * 1.2
            # if self.style == "square":
            #     width = width * 1.75
        if second:
            length = self.secondLength
            base_r = self.secondLength * 0.2

            if self.style == "cuckoo":
                base_r = self.secondLength * 0.12


        hand = cq.Workplane("XY").tag("base").circle(radius=base_r).extrude(self.thick)

        if self.style == "simple":
            width = self.length * 0.1
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(width, length).extrude(self.thick)
        elif self.style == "simple_rounded":
            width = self.length * 0.1
            # if second:
            #     width = length * 0.2
            hand = hand.workplaneFromTagged("base").moveTo(width/2, 0).line(0,length).radiusArc((-width/2,length),-width/2).line(0,-length).close().extrude(self.thick)
        elif self.style == "square":
            handWidth = self.length * 0.3 * 0.25
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(handWidth, length).extrude(self.thick)
        elif self.style == "cuckoo":

            end_d = self.length * 0.3 * 0.1
            centrehole_y = length * 0.6
            width = self.length * 0.3
            if second:
                width = length*0.3
                end_d = length * 0.3 * 0.1
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
            if hour and not second:
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
            try:
                hand = hand.cutThruAll()
            except:
                print("Unable to cut detail in cuckoo hand")

        # fixing = self.hourFixing if hour else self.minuteFixing

        if self.fixing_offset != 0:
            hand = hand.workplaneFromTagged("base").transformed(rotate=(0, 0,self. fixing_offset))

        # if second:
        #     hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.secondFixing_d).extrude(self.secondFixing_thick + self.thick)

        hand = self.cutFixing(hand, hour, second)

        ignoreOutline = False
        if self.style == "cuckoo" and second:
            ignoreOutline = True

        if self.outline > 0 and not ignoreOutline:
            if self.style != "cuckoo":
                if outline:
                    #use a negative shell to get a thick line just inside the edge of the hand

                    #this doesn't work for fancier shapes - I think it can't cope if there isn't space to extrude the shell without it overlapping itself?
                    #works fine for simple hands, not for cuckoo hands

                    shell = hand.shell(-self.outline).translate((0,0,-self.outline))

                    notOutline = hand.cut(shell)
                    # return notOutline
                    #chop off the mess above the first few layers that we want

                    bigSlab = cq.Workplane("XY").rect(length*3, length*3).extrude(self.thick*10).translate((0,0,self.outlineThick))



                    if self.outlineSameAsBody:
                        notOutline = notOutline.cut(bigSlab)
                    else:
                        notOutline = notOutline.add(bigSlab)

                    hand = hand.cut(notOutline)

                else:
                    #chop out the outline from the shape
                    hand = hand.cut(self.getHand(hour, outline=True, second=second))
            else:
                #for things we can't use a negative shell on, we'll make the whole hand a bit bigger
                if outline:
                    shell = hand.shell(self.outline)

                    bigSlab = cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.outlineThick)

                    outline = shell.intersect(bigSlab)
                    outline = self.cutFixing(outline, hour, second)
                    return outline
                else:
                    #make the whole hand bigger by the outline amount
                    shell = hand.shell(self.outline).intersect(cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.thick-self.outlineThick).translate((0,0,self.outlineThick)))



                    # shell2 = hand.shell(self.outline+0.1).intersect(cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.outlineThick))

                    # return shell2
                    # hand = shell
                    hand = hand.add(shell)
                    hand = self.cutFixing(hand, hour, second)
                    return hand
                    # shell2 = self.cutFixing(shell2, hour)
                    #
                    # hand = hand.cut(shell2)


        return hand


    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_hour_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(hour=True), out)

        out = os.path.join(path, "{}_minute_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(hour=False), out)

        out = os.path.join(path, "{}_second_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(second=True), out)

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

            out = os.path.join(path, "{}_second_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(hour=False, second=True, outline=True), out)

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
    '''
    A cylindrical weight shell which can be filled with shot
    Also includes hooks and eyes for the cord
    '''


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

        self.hookInnerD = boltMetricSize*2.5
        self.hookOuterD = self.hookInnerD*1.5
        self.hookThick = self.lidWidth * 0.5

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

    def getHook(self):

        holeDistance=self.hookOuterD/2 + self.hookInnerD/2



        wallThick = (self.hookOuterD - self.hookInnerD)/2
        hook = cq.Workplane("XY").moveTo(-self.hookOuterD/2,0).radiusArc((self.hookOuterD/2,0),-self.hookOuterD/2).line(0,holeDistance).radiusArc((-self.hookOuterD/2, holeDistance), -self.hookOuterD/2)

        hook = hook.radiusArc((-self.hookInnerD/2, holeDistance), -wallThick/2).radiusArc((self.hookInnerD/2,holeDistance), self.hookInnerD/2).radiusArc((0,self.hookOuterD/2),self.hookInnerD/2).radiusArc((-self.hookOuterD/2,0),-self.hookOuterD/2).close()


        hook = hook.extrude(self.hookThick)

        #pushPoints([(0,0), (0,self.hookOuterD/2 + self.hookInnerD/2)])
        hook = hook.faces(">Z").workplane().circle(self.hookInnerD/2).cutThruAll()



        return hook

    def getRing(self):
        ring = cq.Workplane("XY").circle(self.hookOuterD/2).circle(self.hookInnerD/2).extrude(self.hookThick)

        return ring

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


        nutD = getNutContainingDiameter(self.boltMetricSize, NUT_WIGGLE_ROOM)
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

        out = os.path.join(path, "{}_weight_hook.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHook(), out)

        out = os.path.join(path, "{}_weight_ring.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getRing(), out)

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

        #the wheels
        for a in range(self.goingTrain.wheels + self.goingTrain.chainWheels):
            arbour = self.goingTrain.getArbourWithConventionalNaming(a)
            clock = clock.add(arbour.getShape(False).translate(self.plates.bearingPositions[a]).translate((0,0,self.plates.plateThick + self.plates.wobble/2)))

        #the chain wheel parts
        if self.goingTrain.usingChain:
            clock = clock.add(self.goingTrain.chainWheel.getWithRatchet(self.goingTrain.ratchet).translate(self.plates.bearingPositions[0]).translate((0,0,self.goingTrain.getArbour(-self.goingTrain.chainWheels).wheelThick + self.plates.plateThick + self.plates.wobble/2)))

            chainWheelTop =  self.goingTrain.chainWheel.getHalf().mirror().translate((0,0,(self.goingTrain.chainWheel.getHeight() - self.goingTrain.ratchet.thick)/2))

            clock = clock.add(
               chainWheelTop.translate(self.plates.bearingPositions[0]).translate((0, 0, self.goingTrain.getArbourWithConventionalNaming(0).wheelThick + self.plates.plateThick + self.plates.wobble / 2 + (self.goingTrain.chainWheel.getHeight() - self.goingTrain.ratchet.thick)/2 + self.goingTrain.ratchet.thick)))

        else:
            clock = clock.add(self.goingTrain.poweredWheel.getAssembled().translate(self.plates.bearingPositions[0]).translate((0,0,self.goingTrain.getArbour(-self.goingTrain.chainWheels).wheelThick + self.plates.plateThick + self.plates.wobble/2)))


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
        #mirror them so the outline is visible (consistent with second hand)
        minuteHand = self.hands.getHand(hour=False).mirror().translate((0,0,self.hands.thick)).rotate((0,0,0),(0,0,1), minuteAngle)
        hourHand = self.hands.getHand(hour=True).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), hourAngle)


        clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], self.plates.plateThick*2 + self.plates.plateDistance + motionWorksZOffset + self.motionWorks.minuteHolderTotalHeight - self.hands.thick)))

        clock = clock.add(hourHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1],
                                                self.plates.plateThick * 2 + self.plates.plateDistance + motionWorksZOffset + self.motionWorks.minuteHolderTotalHeight - self.hands.thick*3)))

        if self.goingTrain.escapement_time == 60:
            #second hand!! yay
            secondHand = self.hands.getHand(second=True).mirror().translate((0,0,self.hands.thick))#.rotate((0, 0, 0), (0, 0, 1), hourAngle)
            clock = clock.add(secondHand.translate((self.plates.bearingPositions[-2][0], self.plates.bearingPositions[-2][1], self.plates.plateThick*2 + self.plates.plateDistance+self.hands.secondFixing_thick )))


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
                extensionShape=self.plates.getArbourExtension(arbour, top=top, forModel=True)
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


def animateEscapement(escapement, frames=100, path="out", name="escapement_animation", overswing_deg=2, period=1.5):
    '''
    There is osmethign wrong here, it works for a 40 or 48 tooth escapment, but not for a 30 tooth
    '''
    svgOpt = {"showAxes": False,
                    "projectionDir": (0, 0, 1),
                    "width": 1280,
                    "height": 720,
                    }
    #in GIF terms (100ths of a second, I think)
    timePerFrame = int(round((period * 100) / frames))

    #can't find a better way to stop the camera moving about, than giving it something at the edges that doesn't change
    boundingBox = cq.Workplane("XY").rect(escapement.diameter * 1.25, escapement.diameter * 1.75)

    toothAngle_deg = 360 / escapement.teeth

    palletAngleFromWheel_deg = (toothAngle_deg / 2 - escapement.drop_deg)

    wheelAngle_toothAtEndOfExitPallet_deg = radToDeg(math.pi / 2 + escapement.anchorAngle / 2) -  palletAngleFromWheel_deg/ 2
    #increment (-ve for clockwise) by drop
    wheelAngle_toothAtStartOfEntryPallet_deg = wheelAngle_toothAtEndOfExitPallet_deg - escapement.drop_deg#(toothAngle_deg - escapement.drop_deg)
    wheelAngle_toothAtEndOfEntryPallet_deg = wheelAngle_toothAtStartOfEntryPallet_deg - palletAngleFromWheel_deg
    wheelAngle_toothAtStartOfExitPallet_deg = wheelAngle_toothAtEndOfEntryPallet_deg - escapement.drop_deg#(toothAngle_deg - escapement.drop_deg)

    # wheel_angle_deg = wheelAngle_toothAtEndOfExitPallet_deg  # -3.8  -4.1  -2 #- radToDeg(escapement.toothAngle - escapement.drop)/2#-3.3 - drop - 3.5 -
    anchorAngle_startOfExitPallet_deg = escapement.lock_deg / 2 -escapement.lift_deg / 2
    anchorAngle_endOfExitPallet_deg =  escapement.lock_deg / 2 + escapement.lift_deg / 2
    anchorAngle_startOfEntryPallet_deg = -escapement.lock_deg / 2 + escapement.lift_deg / 2
    anchorAngle_endOfEntryPallet_deg = -escapement.lock_deg / 2 - escapement.lift_deg / 2


    #pendulum swings by simple harmonic motion, a sine wave, so the entire animations spans 2pi
    circlePerFrame = math.pi*2/frames

    swingAmplitude_rad = (escapement.lift + escapement.lock + degToRad(overswing_deg)) / 2

    #when not free running, this is the pallet/lock face we're against, when free running it's where we'll be in contact with NEXT
    toothContactWithEntry=False
    wheelFreeRunning=False
    #not free running and also not against locking face
    toothOnPallet=True
    #angle per frame, when free running
    wheelSpeed = -4*toothAngle_deg/frames
    # wheelStartAngle_deg = wheelAngle_toothAtEndOfExitPallet_deg
    wheel_angle_deg = wheelAngle_toothAtEndOfExitPallet_deg

    # anchor_angle_rad_lastPos = degToRad(anchorAngle_toothAtEndOfExitPallet_deg)

    def getAnchorAngleForFrame_rad(frame):
        return math.sin(circlePerFrame * frame + math.asin(degToRad(anchorAngle_endOfExitPallet_deg) / swingAmplitude_rad)) * swingAmplitude_rad

    for frame in range(frames):

        print("frame", frame)

        #starting at the point where a tooth is leaving the exit pallet, when frame == 0 anchor angle == anchorAngle_toothAtEndOfExitPallet_deg
        anchor_angle_rad = getAnchorAngleForFrame_rad(frame)

        print("anchor_angle",radToDeg(anchor_angle_rad))
        print("anchorAngle_toothAtEndOfExitPallet_deg", anchorAngle_endOfExitPallet_deg)

        anchor_angle = radToDeg(anchor_angle_rad)
        #bodge
        if frame > 0:
            if wheelFreeRunning:
                print("wheel running free")
                if toothContactWithEntry:
                    print("heading towards entry")
                    if (wheel_angle_deg + wheelSpeed) < wheelAngle_toothAtStartOfEntryPallet_deg:
                        wheel_angle_deg =  wheelAngle_toothAtStartOfEntryPallet_deg
                        wheelFreeRunning = False
                        # exit locking face
                        toothContactWithEntry = True
                        toothOnPallet = False
                        print("locked against entry")
                else:
                    print("heading towards exit")
                    # remembering that clockwise is -ve
                    if wheel_angle_deg + wheelSpeed < wheelAngle_toothAtStartOfExitPallet_deg:
                        # this will come into contact with the locking edge of the entry pallet
                        wheel_angle_deg = wheelAngle_toothAtStartOfExitPallet_deg
                        wheelFreeRunning = False
                        toothContactWithEntry = False
                        toothOnPallet = False
                        print("locked against exit")

                #if we're still free-running, rotate
                if wheelFreeRunning:
                    #carry on rotating
                    wheel_angle_deg+= wheelSpeed
                    print("wheel still running free")

            else:
                #wheel is not free running, it is either in lock or in contact with a pallet
                print("wheel not running free")
                if toothOnPallet:
                    print("tooth on pallet")
                    #actually on the pallet
                    # rotate the wheel at teh same rate as the anchor (bodge?)

                    # wheel_angle_deg += -abs(radToDeg(getAnchorAngleForFrame_rad(frame) - getAnchorAngleForFrame_rad(frame -1)))

                    wheel_angle_deg += -abs(radToDeg(getAnchorAngleForFrame_rad(frame +1) - getAnchorAngleForFrame_rad(frame)))

                    if not toothContactWithEntry and anchor_angle > anchorAngle_endOfExitPallet_deg:
                        #tooth has left exit pallet
                        wheelFreeRunning = True
                        toothOnPallet = False
                        toothContactWithEntry=True
                        print("left exit pallet")
                    elif toothContactWithEntry and anchor_angle < anchorAngle_endOfEntryPallet_deg:
                        # tooth has left entry pallet
                        wheelFreeRunning = True
                        toothOnPallet = False
                        toothContactWithEntry = False
                        print("left entry pallet")
                else:
                    print("wheel is locked")
                    #against a locking face
                    if toothContactWithEntry and anchor_angle < anchorAngle_startOfEntryPallet_deg:
                        #now against the entry pallet
                        toothOnPallet = True
                        print("now in contact with entry pallet")

                    elif not toothContactWithEntry and anchor_angle > anchorAngle_startOfExitPallet_deg:
                        toothOnPallet = True
                        print("now in contact with exit pallet")




        #TODO, check if anchor angle is where the wheel should be locked, heading to being locked, or moving along one of the pallets
        #then choose a speed to move when the wheel is moving freely and work out how to match up the speed with the pallets
        #should be able to figure out how many frames are required across the lift angle with arcsine somehow?

        # #
        wholeObject = escapement.getAnchor2D().rotate((0, escapement.anchor_centre_distance, 0), (0, escapement.anchor_centre_distance, 1), anchor_angle).add(escapement.getWheel2D().rotateAboutCenter((0, 0, 1), wheel_angle_deg))

        wholeObject = wholeObject.add(boundingBox)

        exporters.export(wholeObject, os.path.join(path,"{}_{:02d}.svg".format(name, frame)), opt=svgOpt)

        # show_object(wholeObject.add(cq.Workplane("XY").circle(escapement.diameter/2)))
        # return
        # print("frame",frame)

        # # # svgString = exporters.getSVG(exporters.toCompound(wholeObject), opts=svgOpt)
        # # # print(svgString)

    os.system("{} -delay {}, -loop 0 {}/{}_*.svg {}/{}.gif".format(IMAGEMAGICK_CONVERT_PATH, timePerFrame,  path, name,path, name))


class BallWheel:
    '''
    Use steel balls in a waterwheel-like wheel instead of a weight on a cord or chain.
    Shouldn't need a power maintainer. Might need some sort of stop works to avoid getting stuck half empty

    stop works idea: sprung lever from the side, after where the ball drops in. If there's no ball there (or no ball falls on it), it would stop the wheel turning
    '''

    def __init__(self, ballDiameter=25.4, ballsAtOnce=10, ballWeight = 0.065):
        self.ballDiameter = ballDiameter
        # self.maxDiameter = maxDiameter
        #how many balls to fit onto half the wheel
        self.ballsAtOnce = ballsAtOnce
        self.ballWeightKg = ballWeight

        self.wallThick=3
        self.wiggleRoom=2
        self.taperAngleDeg = 3

        self.segmentArcLength = (ballDiameter + self.wallThick + self.wiggleRoom)

        self.pitchCircumference = ballsAtOnce*(ballDiameter + self.wallThick + self.wiggleRoom)*2
        self.pitchDiameter = self.pitchCircumference / math.pi
        print("pitch diameter", self.pitchDiameter)

    def getTorque(self):
        ballAngle = math.pi*2/(self.ballsAtOnce*2)

        torque = 0

        #from top to bottom, assuming clockwise for no particularily good reason
        for ball in range(self.ballsAtOnce):
            angle = math.pi/2 - ball*ballAngle
            print("angle", radToDeg(angle))

            xDir = math.cos(angle)*self.pitchDiameter/2
            print(xDir)
            xDirMetres = xDir/1000
            torque += xDirMetres * self.ballWeightKg * GRAVITY

        return torque



ballWheel = BallWheel()
torque = ballWheel.getTorque()
print("torque", torque, torque/0.037)

#trial for 48 tooth wheel
# drop = 1.5
# lift = 2
# lock = 1.5
# teeth = 48
# diameter = 65  # 64.44433859295404#61.454842805344896
# toothTipAngle = 4
# toothBaseAngle = 3
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat", diameter=diameter, teeth=teeth, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=toothTipAngle, toothBaseAngle=toothBaseAngle)

# drop =1.5
# lift =3
# lock=1.5
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat",teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

# animateEscapement(escapement, frames=100, period=1.5,overswing_deg=4)












# getRadiusForPointsOnACircle([10,20,15], math.pi)
#
#
# dial = Dial(120)
#
# show_object(dial.getDial())
#
# weight = Weight()
#
# show_object(weight.getHook())
#
# show_object(weight.getRing().translate((20,0,0)))
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

##### =========== escapement testing ======================
#drop of 1 and lift of 3 has good pallet angles with 42 teeth
# drop =1.5
# lift =2
# lock=1.5
# teeth = 48
# diameter = 65# 64.44433859295404#61.454842805344896
# toothTipAngle = 4
# toothBaseAngle = 3
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat",diameter=diameter, teeth=teeth, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=toothTipAngle, toothBaseAngle=toothBaseAngle)
# # # escapement = Escapement(teeth=30, diameter=61.454842805344896, lift=4, lock=2, drop=2, anchorTeeth=None,
# # #                              clockwiseFromPinionSide=False, type="deadbeat")
# ##
# svgOpt = opt={"showAxes":False,
# "projectionDir": (0, 0, 1),
# "width": 1280,
# "height": 720,
# }
#
# toothAngle = 360/teeth
# toothAtEndOfExitPallet = radToDeg(math.pi/2 +escapement.anchorAngle/2) - (toothAngle/2 - drop)/2
# wheel_angle = toothAtEndOfExitPallet#-3.8  -4.1  -2 #- radToDeg(escapement.toothAngle - escapement.drop)/2#-3.3 - drop - 3.5 -
# anchor_angle = lift/2+lock/2#lift/2 + lock/2
#
# frames = 100
# for frame in range(frames):
#     wholeObject = escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle).add(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))
#     exporters.export(wholeObject, "out/test_{:02d}.svg".format(frame), opt=svgOpt)
#     # svgString = exporters.getSVG(exporters.toCompound(wholeObject), opts=svgOpt)
#     # print(svgString)
#     # show_object(wholeObject)




# toothAngle = 360/teeth
# toothAtEndOfExitPallet = radToDeg(math.pi/2 +escapement.anchorAngle/2) - (toothAngle/2 - drop)/2
# wheel_angle = toothAtEndOfExitPallet#-3.8  -4.1  -2 #- radToDeg(escapement.toothAngle - escapement.drop)/2#-3.3 - drop - 3.5 -
# anchor_angle = lift/2+lock/2#lift/2 + lock/2
#
# wholeObject = escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle).add(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))
#
# show_object(wholeObject)
#
# svgOpt = opt={"showAxes":False,
# "projectionDir": (0, 0, 1),
# "width": 1280,
# "height": 720,
# }
#
# exporters.export(wholeObject, "out/test.svg", opt=svgOpt)

# show_object(escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle))
# show_object(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))

# anchor = escapement.getAnchorArbour(holeD=3, anchorThick=10, clockwise=False, arbourLength=0, crutchLength=0, crutchBoltD=3, pendulumThick=3, nutMetricSize=3)
# # show_object(escapement.getAnchor3D())
# show_object(anchor)
# exporters.export(anchor, "../out/anchor_test.stl")
# #
# #

# ### ============FULL CLOCK ============
# # # train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
# train=GoingTrain(pendulum_period=2,fourth_wheel=False,escapement_teeth=30, maxChainDrop=1800, chainAtBack=False)#,chainWheels=1, hours=180)
# train.calculateRatios()
# # train.setRatios([[64, 12], [63, 12], [60, 14]])
# # train.setChainWheelRatio([74, 11])
# # train.genChainWheels(ratchetThick=5)
# pendulumSticksOut=25
# # train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
# train.genCordWheels(ratchetThick=5, cordThick=2, cordCoilThick=11)
# train.genGears(module_size=1,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)
# motionWorks = MotionWorks(minuteHandHolderHeight=30)
# #trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
# pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, useNylocForAnchor=False)
#
#
# #printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
# plates = ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="Wall 05", style="vertical")#, heavy=True)
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

# ============ hands ==================
#
# hands = Hands(style="simple_rounded",minuteFixing="square", minuteFixing_d1=3, hourfixing_d=5, length=80, thick=4, outline=1, outlineSameAsBody=False)
# show_object(hands.getHand(True,True))
# show_object(hands.getHand(True,False).translate((50,0,0)))
# show_object(hands.getHand(hour=False,second=True).translate((-50,0,0)))

#
# shell = WeightShell(45,220, twoParts=True, holeD=5)
#
# show_object(shell.getShell())
#
# show_object(shell.getShell(False).translate((100,0,0)))

# ratchet = Ratchet()
# # cordWheel = CordWheel(23,50, ratchet=ratchet, useGear=True, style="circles")
# cordWheel = CordWheel(23,50, ratchet=ratchet, style="circles", useKey=True)
# #
# #
# #
#
# # pulley = Pulley(diameter=30, vShaped=False)
# #
# # show_object(pulley.getHalf())
#
# # show_object(cordWheel.getSegment())
# show_object(cordWheel.getAssembled())
# # show_object(cordWheel.getCap(top=True))
# show_object(cordWheel.getCap())



# show_object(cordWheel.getClickWheelForCord(ratchet))
# show_object(cordWheel.getCap().translate((0,0,ratchet.thick)))
# show_object(cordWheel.getSegment(False).mirror().translate((0,0,cordWheel.thick)).translate((0,0,ratchet.thick + cordWheel.capThick)))
# show_object(cordWheel.getSegment(True).mirror().translate((0,0,cordWheel.thick)).translate((0,0,ratchet.thick + cordWheel.capThick + cordWheel.thick)))

