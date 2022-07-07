from .utility import *
import cadquery as cq
import os
from cadquery import exporters

from enum import Enum
class GearStyle(Enum):
    SOLID = None
    ARCS = "HAC"
    CIRCLES = "circles"
    SIMPLE4 = "simple4"
    SIMPLE5 = "simple5"

'''
ideas for new styles:
 - bicycle sprockets
 - bicycle disc brakes (both ideas knicked from etsy quartz clocks)
 - honeycomb
 - Voronoi Diagram
 - curved arms
'''

class ArbourType(Enum):
    WHEEL_AND_PINION = "WheelAndPinion"
    CHAIN_WHEEL = "ChainWheel"
    ESCAPE_WHEEL = "EscapeWheel"
    ANCHOR = "Anchor"
    UNKNOWN = "Unknown"




class Gear:


    @staticmethod
    def cutStyle(gear, outerRadius, innerRadius = -1, style=None):
        '''
        Could still do with a little more tidying up, outerRadius should be a few mm shy of the edge of teh gear to give a solid rim,
        but innerRadius should be at the edge of whatever can't be cut into
        '''
        #lots of old designs used a literal string "HAC"
        if style == GearStyle.ARCS or style == GearStyle.ARCS.value:
            if innerRadius < outerRadius*0.5:
                innerRadius=outerRadius*0.5
            return Gear.cutHACStyle(gear,armThick=outerRadius*0.1, rimRadius=outerRadius-2, innerRadius=innerRadius*1.15)
        if style == GearStyle.CIRCLES:
            if innerRadius < 0:
                innerRadius = 3
            return Gear.cutCirclesStyle(gear,outerRadius=outerRadius, innerRadius=innerRadius)
        if style == GearStyle.SIMPLE4:
            return Gear.cutSimpleStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2, arms=4)
        if style == GearStyle.SIMPLE5:
            return Gear.cutSimpleStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2, arms=5)

        return gear
    @staticmethod
    def cutSimpleStyle(gear, outerRadius, innerRadius, arms=4):
        armThick = outerRadius*0.2#0.15

        thick = 100

        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(thick)

        dA=math.pi*2/arms

        for arm in range(arms):
            angle = arm*dA
            #cut out arms
            cutter = cutter.cut(cq.Workplane("XY").moveTo((outerRadius+innerRadius)/2,0).rect((outerRadius-innerRadius)*1.1,armThick).extrude(thick).rotate((0,0,1),(0,0,0),radToDeg(angle)))

        gear = gear.cut(cutter)

        return gear

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

            # armThick = rimThick
            # if style == "HAC":
            #
            #
            #     gear = Gear.cutHACStyle(gear, armThick, rimRadius, innerRadius=innerRadiusForStyle)
            # elif style == "circles":
            #     # innerRadius = self.innerRadiusForStyle
            #     # if innerRadius < 0:
            #     #     innerRadius = self.
            #     gear = Gear.cutCirclesStyle(gear, outerRadius = self.pitch_diameter / 2 - rimThick, innerRadius=innerRadiusForStyle)
            gear = Gear.cutStyle(gear, outerRadius=self.pitch_diameter / 2 - rimThick, innerRadius=innerRadiusForStyle, style=style)

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
        # if not self.iswheel:
        #     print("addendum radius", addendum_radius, self.module)
        # via practical addendum factor
        addendum_height = 0.95 * self.addendum_factor * self.module
        dedendum_height = self.dedendum_factor * self.module

        inner_radius = pitch_radius - dedendum_height
        outer_radius = pitch_radius + addendum_height
        # if not self.iswheel:
        #     print("inner radius", inner_radius)

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
    def __init__(self, wheelTeeth, pinionTeeth, module=1.5, looseArbours=False):
        '''

        :param teeth:
        :param radius:

        if loose arbours, then this is probably for hte motion works, where there's a lot of play and
        they don't mesh well
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

        if looseArbours:
            #extend the addendum a bit
            wheel_addendum_factor*=1.2

        # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl says addendum radius factor is 1.4*addendum factor
        #(this is aproximating the real curve, i think?)
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
        if pinionTeeth == 6 or pinionTeeth == 7 or looseArbours:
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
        #this function ported from http://hessmer.org/gears/CycloidalGearBuilder.html MIT licence
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
    def __init__(self, arbourD, wheel=None, wheelThick=None, pinion=None, pinionThick=None, ratchet=None, chainWheel=None, escapement=None, endCapThick=1, style=GearStyle.ARCS, distanceToNextArbour=-1, pinionAtFront=True, ratchetInset=True, screwSize=2, ratchetScrewsPanHead=True):
        '''
        This represents a combination of wheel and pinion. But with special versions:
        - chain wheel is wheel + ratchet (pinionThick is used for ratchet thickness)
        - escape wheel is pinion + escape wheel
        - anchor is just the escapement anchor

        NOTE currently assumes chain/cord is at the front - needs top be controlled by something like pinionAtFront

        Trying to store all the special logic for thicknesses and radii in one place
        '''
        self.arbourD=arbourD
        self.wheel=wheel
        self.wheelThick=wheelThick
        self.pinion=pinion
        self.pinionThick=pinionThick
        #could get this via chainwheel?
        self.ratchet=ratchet
        self.escapement=escapement
        self.endCapThick=endCapThick
        #the pocket chain wheel or cord wheel (needed only to calculate full height)
        self.chainWheel=chainWheel
        self.style=style
        self.distanceToNextArbour=distanceToNextArbour
        self.nutSpaceMetric=None
        self.pinionAtFront=pinionAtFront



        self.frontSideExtension=0
        self.rearSideExtension=0
        self.arbourExtensionMaxR=self.arbourD

        if self.getType() == ArbourType.UNKNOWN:
            raise ValueError("Not a valid arbour")

        if self.getType() == ArbourType.CHAIN_WHEEL:
            #chain/cord wheel specific bits:
            # the ratchet on the chain/cord wheel can be bolted onto the outside, allowing it to be printable with the arbour extension as part of the
            # wheel.
            self.boltOnRatchet = True
            # allow the ratchet to be partially (or fully) inset into the wheel. will require bridging to print
            self.ratchetInset = ratchetInset
            # minimum thickness of wheel, limiting how far the ratchet can be inset
            self.wheelMinThick = 2.5
            self.bridgingThickBodge = 1
            bolts=4
            self.screwSize=screwSize
            outerR = self.ratchet.outsideDiameter/2
            innerR = self.ratchet.toothRadius
            boltDistance = (outerR+innerR)/2
            #offsetting so it's in the middle of a click (where it's slightly wider)
            self.boltPositions=[polar(i*math.pi*2/bolts + math.pi/self.ratchet.ratchetTeeth, boltDistance) for i in range(bolts)]
            self.ratchetScrewsPanHead = ratchetScrewsPanHead

        #anchor specific, will be refined once arbour extension info is provided
        # want a square bit so we can use custom long spanners to set the beat
        self.spannerBitThick = 4
        self.spannerBitOnFront=False


    def setArbourExtensionInfo(self, frontSide=0, rearSide=0, maxR=0):
        '''
        This info is only known after the plates are configured, so retrospectively add it to the arbour.

        Currently only used for the chain wheel to make it more rigid (using pinion to mean side with the chain/cord)
        '''
        self.frontSideExtension=frontSide
        self.rearSideExtension=rearSide
        self.arbourExtensionMaxR=maxR

        #can now calculate the location and size of the spanner nut for the anchor
        if self.getType() == ArbourType.ANCHOR:
            # place it where there's most space

            if self.rearSideExtension > self.spannerBitThick:
                # enough space to hide it at the back
                self.spannerBitOnFront = False
            else:
                # where there's most space
                self.spannerBitOnFront = self.frontSideExtension > self.rearSideExtension
                # limit its size to the amount of space there is
                self.spannerBitThick = min(10, self.frontSideExtension if self.spannerBitOnFront else self.rearSideExtension)

            #bit hacky, treat spanner bit like a pinion for the arbour extension stuff
            self.pinionAtFront = self.spannerBitOnFront


    def setNutSpace(self, nutMetricSize=3):
        '''
        This arbour is fixed firmly to the rod using a nyloc nut
        '''
        self.nutSpaceMetric=nutMetricSize

    def getType(self):
        if self.wheel is not None and self.pinion is not None:
            return ArbourType.WHEEL_AND_PINION
        if self.wheel is not None and self.ratchet is not None and self.chainWheel is not None:
            return ArbourType.CHAIN_WHEEL
        if self.wheel is None and self.escapement is not None and self.pinion is not None:
            return ArbourType.ESCAPE_WHEEL
        if self.escapement is not None:
            return ArbourType.ANCHOR
        return ArbourType.UNKNOWN

    def getRodD(self):
        return self.arbourD

    def getRatchetInsetness(self, toCarve=False):
        '''
        Get how much the ratchet is inset
        if toCarve, this is how deep the hole should be (with extra space to allow for the bridging not be perfectly flat)
        if not toCarve, this is how far the ratchet will insert into the whole
        '''

        if not self.ratchetInset:
            return 0

        if self.wheelThick < self.wheelMinThick:
            #wheel isn't thick enough to support an inset ratchet
            return 0

        holeDeep = self.wheelThick - self.wheelMinThick



        if holeDeep <= self.bridgingThickBodge:
            #wheel isn't deep enough to get any benefit from an inset ratchet
            return 0

        if holeDeep - self.bridgingThickBodge > self.ratchet.thick:
            #too deep!
            holeDeep = self.ratchet.thick+self.bridgingThickBodge

        if toCarve:
            return holeDeep
        else:
            return holeDeep - self.bridgingThickBodge


    def getTotalThickness(self):
        '''
        return total thickness of everything that will be on the rod
        '''
        if self.getType() == ArbourType.WHEEL_AND_PINION or self.getType() == ArbourType.ESCAPE_WHEEL:
            return self.wheelThick + self.pinionThick + self.endCapThick
        if self.getType() == ArbourType.CHAIN_WHEEL:
            #the chainwheel (or cordwheel) now includes the ratceht thickness
            return self.wheelThick + self.chainWheel.getHeight() - self.getRatchetInsetness(toCarve=False)
        if self.getType() == ArbourType.ANCHOR:
            #wheel thick being used for anchor thick
            return self.wheelThick

    def getWheelCentreZ(self):
        '''
        Get the centre of the height of the wheel - which drives the next arbour
        '''
        if self.pinionAtFront:
            return self.wheelThick / 2
        else:
            return self.getTotalThickness() - self.wheelThick/2

    def getPinionCentreZ(self):
        if self.getType() not in [ArbourType.WHEEL_AND_PINION, ArbourType.ESCAPE_WHEEL]:
            raise ValueError("This arbour (type {}) does not have a pinion".format(self.getType()))
        if self.pinionAtFront:
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
        if self.getType() == ArbourType.ESCAPE_WHEEL:
            return self.escapement.getWheelMaxR()
        if self.getType() == ArbourType.ANCHOR:
            return self.escapement.getAnchorMaxR()
        raise NotImplementedError("Max Radius not yet implemented for arbour type {}".format(self.getType()))

    def getShape(self, forPrinting=True):
        '''
        return a shape that can be exported to STL
        if for printing, wheel is on the bottom, if false, this is in the orientation required for the final clock
        '''
        if self.getType() == ArbourType.WHEEL_AND_PINION:
            shape = self.pinion.addToWheel(self.wheel, holeD=self.arbourD, thick=self.wheelThick, style=self.style, pinionThick=self.pinionThick, capThick=self.endCapThick)
        elif self.getType() == ArbourType.ESCAPE_WHEEL:
            shape = self.pinion.addToWheel(self.escapement, holeD=self.arbourD, thick=self.wheelThick, style=self.style, pinionThick=self.pinionThick, capThick=self.endCapThick)
        elif self.getType() == ArbourType.CHAIN_WHEEL:
            shape = self.getWheelWithRatchet(forPrinting=forPrinting)
        else:
            if self.getType() == ArbourType.ANCHOR:
                shape = self.getAnchor(forPrinting=forPrinting)
        if self.nutSpaceMetric is not None:
            #cut out a space for a nyloc nut
            deep = self.wheelThick * 0.25
            if self.pinion is not None:
                #can make this much deeper
                deep = min(self.wheelThick*0.75, getNutHeight(self.nutSpaceMetric, nyloc=True))
            shape = shape.cut(getHoleWithHole(self.arbourD, getNutContainingDiameter(self.arbourD, NUT_WIGGLE_ROOM), deep , 6))

        # note, the included extension is always on the pinion side (unprintable otherwise)
        if self.needArbourExtension(front=True) and self.pinionAtFront:
            #need arbour extension on the front
            shape = shape.add(self.getArbourExtension(front=True).translate((0,0,self.getTotalThickness())))

        if self.needArbourExtension(front=False) and not self.pinionAtFront:
            # need arbour extension on the rear
            shape = shape.add(self.getArbourExtension(front=False).translate((0, 0, self.getTotalThickness())))

        if not forPrinting and not self.pinionAtFront and (self.getType() in [ArbourType.WHEEL_AND_PINION, ArbourType.ESCAPE_WHEEL]):
            #make it the right way around for placing in a model
            #rotate not mirror! otherwise the escape wheels end up backwards
            shape = shape.rotate((0,0,0),(1,0,0),180).translate((0,0,self.getTotalThickness()))


        return shape

    def getAnchor(self, forPrinting=True):

        remainingExtension = (self.frontSideExtension if self.spannerBitOnFront else self.rearSideExtension) - self.spannerBitThick

        anchor = self.escapement.getAnchorArbour(holeD=self.arbourD, anchorThick=self.wheelThick)#, forPrinting=forPrinting)

        face = ">Z" if self.spannerBitOnFront else "<Z"

        width = self.getRodD() * 2

        #add the rest of the arbour extension
        anchor = anchor.faces(face).workplane().moveTo(0,0).rect(width,width).extrude(self.spannerBitThick)
        if remainingExtension > 0:
            anchor = anchor.faces(face).workplane().moveTo(0,0).circle(self.getRodD()).extrude(remainingExtension)

        anchor = anchor.faces(face).workplane().circle(self.getRodD()/2).cutThruAll()


        if forPrinting and not self.spannerBitOnFront:
            #flip so it can be printed as-is
            anchor=anchor.rotate((0,0,0),(0,1,0),180)

        return anchor

    def getArbourExtension(self, front=True):
        '''
        Get little cylinders we can use as spacers to keep the gears in the right place on the rod

        returns None if no extension is needed
        '''

        length = self.frontSideExtension if front else self.rearSideExtension

        if length >= LAYER_THICK:
            extendoArbour = cq.Workplane("XY").tag("base").circle(self.getRodD()).circle(self.getRodD() / 2 + ARBOUR_WIGGLE_ROOM/2).extrude(length)

            return extendoArbour
        return None

    def getAssembled(self):
        '''
        return this arbour fully assembled, for the model rather than printing
        (0,0,0) should be in the centre of the arbour, at the back of the wheel or pinion
        this is because bearingPosition already has the rear extension included, so no need to replicate it here
        '''

        #get the main bit, the right way round
        shape = self.getShape(forPrinting=False)

        #pinion side extensions are now included in the arbour shape
        #the chain wheel with a bolt on ratchet includes its own special arbour extension
        #built in extensions are always on the pinion side
        if self.needArbourExtension(front=True) and not self.pinionAtFront:
            shape = shape.add(self.getArbourExtension(front=True).translate((0,0,self.getTotalThickness())))
        if self.needArbourExtension(front=False) and self.pinionAtFront:
            shape = shape.add(self.getArbourExtension(front=False).translate((0,0,-self.rearSideExtension)))

        if self.getType() == ArbourType.CHAIN_WHEEL:
            # should work for both chain and cord

            boltOnRatchet = self.getExtraRatchet(forPrinting=False)
            if boltOnRatchet is not None:
                #already in the right place
                shape = shape.add(boltOnRatchet)

            shape = shape.add(self.chainWheel.getAssembled().translate((0, 0, self.wheelThick - self.getRatchetInsetness())))


        return shape

    def needArbourExtension(self, front=True):

        if front and self.frontSideExtension < LAYER_THICK:
            return False
        if (not front) and self.rearSideExtension < LAYER_THICK:
            return False

        if self.getType() == ArbourType.ANCHOR:
            return not (front == self.spannerBitOnFront)

        if self.getType() == ArbourType.CHAIN_WHEEL:
            #assuming chain is at front
            if front:
                return False
            else:
                return not self.boltOnRatchet

        return True


    def getExtras(self):
        '''
        are there any extra bits taht need printing for this arbour?
        returns {'name': shape,}
        '''
        extras = {}

        if self.getType() == ArbourType.CHAIN_WHEEL and self.getExtraRatchet() is not None:
            extras['ratchet']= self.getExtraRatchet()

        if self.pinionAtFront and self.needArbourExtension(front=False):
            extras['arbour_extension_rear'] = self.getArbourExtension(front=False)
        if not self.pinionAtFront and self.needArbourExtension(front=True):
            extras['arbour_extension_front'] = self.getArbourExtension(front=True)


        return extras
    def getExtraRatchet(self, forPrinting=True):
        '''
        returns None if the ratchet is fully embedded in teh wheel
        otherwise returns a shape that can either be adapted to be bolted, or combined with the wheel

        Note: shape is returned translated into the position relative to the chain wheel

        '''

        ratchetOutsideWheelRequired = self.ratchet.thick - self.getRatchetInsetness(toCarve=False)

        if ratchetOutsideWheelRequired <= 0:
            return None

        ratchetWheel = self.ratchet.getOuterWheel(thick=ratchetOutsideWheelRequired)

        if self.boltOnRatchet:
            #add holes
            for holePos in self.boltPositions:
                countersunk = not self.ratchetScrewsPanHead
                ratchetWheel = ratchetWheel.faces(">Z").moveTo(holePos[0], holePos[1]).circle(self.screwSize/2).cutThruAll()
                headHeight = getScrewHeadHeight(self.screwSize, countersunk=countersunk)
                if not countersunk:

                    cutter = cq.Workplane("XY").circle(getScrewHeadDiameter(self.screwSize,countersunk=countersunk)/2+0.1).extrude(headHeight).translate((holePos[0], holePos[1],ratchetOutsideWheelRequired-headHeight))
                else:
                    coneHeight = getScrewHeadHeight(self.screwSize, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE_SMALL
                    topR = getScrewHeadDiameter(self.screwSize, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE_SMALL
                    cutter = cq.Workplane("XY").add(cq.Solid.makeCone(radius2=topR, radius1=self.screwSize / 2, height=coneHeight).translate((holePos[0], holePos[1],ratchetOutsideWheelRequired-coneHeight)))
                # return cutter
                ratchetWheel = ratchetWheel.cut(cutter)

        ratchetWheel = ratchetWheel.translate((0, 0, self.wheelThick))

        # if not forPrinting:
        #     ratchetWheel = ratchetWheel.rotate((0,0,0),(1,0,0),180)

        return ratchetWheel

    def printScrewLength(self):
        if self.getExtraRatchet() is not None:
            length = self.wheelThick-self.getRatchetInsetness(toCarve=False) + self.ratchet.thick
            if self.ratchetScrewsPanHead:
                length -= getScrewHeadHeight(self.screwSize)
            print("Ratchet needs {} screws (m{}) of length {}mm".format("panhead" if self.ratchetScrewsPanHead else "countersunk", self.screwSize,length))

    def getWheelWithRatchet(self, forPrinting=True):
        gearWheel = self.wheel.get3D(holeD=self.arbourD, thick=self.wheelThick, style=self.style, innerRadiusForStyle=self.ratchet.outsideDiameter * 0.5)

        holeDeep = self.getRatchetInsetness(toCarve=True)
        if holeDeep > 0:
            #note, if the ratchet is inset the wheel will need some other mechanism to keep it at right angles on the rod, like the wheelSideExtension set

            #bare in mind this wheel is now upside down in the case of an inset ratchet
            ratchetHole = getHoleWithHole(self.arbourD,self.ratchet.outsideDiameter,holeDeep).rotate((0,0,0),(1,0,0),180).translate((0,0,self.wheelThick))
            gearWheel = gearWheel.cut(ratchetHole)
            ratchetZ = self.wheelThick - holeDeep
            #extra layer thick so the hole-in-a-hole doesn't print with gaps at the edges
            ratchetWheel = self.ratchet.getOuterWheel(thick=holeDeep+LAYER_THICK).translate((0, 0, ratchetZ-LAYER_THICK))
            gearWheel = gearWheel.add(ratchetWheel)



        if self.boltOnRatchet:
            #only extend out this way if the ratchet is inset - otherwise this is unprintable
            #have it stand off from the bearing slightly

            if self.rearSideExtension > 0:
                #limit to r of 1cm
                extensionR = min(10,self.arbourExtensionMaxR)

                bearingStandoffHeight = LAYER_THICK * 2
                extendedArbour = cq.Workplane("XY").circle(extensionR).extrude(self.rearSideExtension - bearingStandoffHeight).faces(">Z").workplane().circle(self.arbourD).extrude(bearingStandoffHeight)
                #add hole for rod!
                extendedArbour = extendedArbour.faces(">Z").circle(self.arbourD/2).cutThruAll()

                gearWheel = gearWheel.add(extendedArbour.rotate((0,0,0),(1,0,0),180))

            if self.getExtraRatchet() is not None:
                #need screwholes to attach the rest of the ratchet
                for holePos in self.boltPositions:
                    cutter = cq.Workplane("XY").moveTo(holePos[0], holePos[1]).circle(self.screwSize/2).extrude(self.wheelThick)
                    gearWheel = gearWheel.cut(cutter)
                    cutter = cq.Workplane("XY").moveTo(holePos[0],holePos[1]).polygon(nSides=6,diameter=getNutContainingDiameter(self.screwSize)+NUT_WIGGLE_ROOM).extrude(getNutHeight(self.screwSize))
                    gearWheel=gearWheel.cut(cutter)

        else:
            gearWheel = gearWheel.add(self.getExtraRatchet().translate((0,0,self.wheelThick)))

        if self.ratchetInset and forPrinting:
            #put flat side down
            gearWheel = gearWheel.rotate((0,0,0),(1,0,0),180)

        # if not self.ratchetInset and self.wheelSideExtension > 0:
        #     print("UNPRINTABLE CHAIN WHEEL, cannot have bits sticking out both sides")
        return gearWheel

class MotionWorks:

    def __init__(self, holeD=3.5, thick=3, cannonPinionLoose=True, module=1, minuteHandThick=3, minuteHandHolderSize=5, minuteHandHolderHeight=50,
                 style="HAC", compensateLooseArbour=False, snail=None, strikeTrigger=None, strikeHourAngleDeg=45):
        '''
        if cannon pinion is loose, then the minute wheel is fixed to the arbour, and the motion works must only be friction-connected to the minute arbour.

        NOTE hour hand is very loose when motion works arbour is mounted above the cannon pinion. compensateLooseArbour attempts to compensate for this

        If snail and strikeTrigger are provided, this motion works will be for a striking clock

        The modern clock:
        'The meshing of the minute wheel and cannon pinion should be as deep as is consistent with perfect freedom, as should also that of the hour wheel
         and minute pinion in order to prevent the hour hand from having too much shake, as the minute wheel and pinion are loose on the stud and the hour
         wheel is loose on the cannon, so that a shallow depthing here will give considerable back lash, which is especially noticeable when winding.'

        '''
        self.holeD=holeD
        self.thick = thick
        self.style=style
        self.cannonPinionLoose = cannonPinionLoose

        self.strikeTrigger=strikeTrigger
        #angle the hour strike should be at
        self.strikeHourAngleDeg=strikeHourAngleDeg
        self.snail=snail

        self.pinionCapThick = thick/2

        #pinching ratios from The Modern Clock
        #adjust the module so the diameters work properly
        self.arbourDistance = module * (36 + 12) / 2
        secondModule = 2 * self.arbourDistance / (40 + 10)
        # print("module: {}, secondMOdule: {}".format(module, secondModule))
        self.pairs = [WheelPinionPair(36,12, module, looseArbours=compensateLooseArbour), WheelPinionPair(40,10,secondModule, looseArbours=compensateLooseArbour)]
        # self.pairs = [WheelPinionPair(36, 12, module), WheelPinionPair(40, 10, secondModule)]
        self.cannonPinionThick = self.thick*2

        self.minuteHandHolderSize=minuteHandHolderSize
        self.minuteHandHolderD = minuteHandHolderSize*math.sqrt(2)+0.5
        # print("minute hand holder D: {}".format(self.minuteHandHolderD))
        self.minuteHolderTotalHeight = minuteHandHolderHeight
        self.minuteHandSlotHeight = minuteHandThick

        self.wallThick = 1.5
        self.space = 0.5
        #old size of space so i can reprint without reprinting the hands
        self.hourHandHolderD = self.minuteHandHolderD + 1 + self.wallThick*2

    def getAssembled(self, motionWorksRelativePos=None,minuteAngle=10):
        if motionWorksRelativePos is None:
            motionWorksRelativePos = [0, self.getArbourDistance()]

        motionWorksModel = self.getCannonPinion().rotate((0, 0, 0), (0, 0, 1), minuteAngle)
        motionWorksModel = motionWorksModel.add(self.getHourHolder().translate((0, 0, self.getCannonPinionBaseThick())))
        motionWorksModel = motionWorksModel.add(self.getMotionArbour().translate((motionWorksRelativePos[0], motionWorksRelativePos[1], self.getCannonPinionBaseThick() / 2)))

        return motionWorksModel

    def getHourHandHoleD(self):
        return self.hourHandHolderD

    def getArbourDistance(self):
        return self.arbourDistance

    def getCannonPinionBaseThick(self):
        '''
        get the thickness of the pinion + caps at the bottom of the cannon pinion

        '''

        thick = self.pinionCapThick*2 + self.cannonPinionThick

        return thick

    def getCannonPinion(self):

        base = cq.Workplane("XY")

        if self.strikeTrigger is not None:
            base = self.strikeTrigger.get2D().extrude(self.pinionCapThick).rotate((0,0,0),(0,0,1),self.strikeHourAngleDeg).faces(">Z").workplane()


        base = base.circle(self.pairs[0].pinion.getMaxRadius()).extrude(self.pinionCapThick)
        pinion = self.pairs[0].pinion.get2D().extrude(self.cannonPinionThick).translate((0,0,self.pinionCapThick))

        top = cq.Workplane("XY").circle(self.pairs[0].pinion.getMaxRadius()).extrude(self.pinionCapThick).translate((0,0,self.pinionCapThick+self.cannonPinionThick))

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


        style=self.style
        # if self.snail is not None:
        #     style = None

        hour = self.pairs[1].wheel.get3D(holeD=self.holeD,thick=self.thick,style=style, innerRadiusForStyle=bottomR)

        if self.snail is not None:
            hour = hour.add(self.snail.get3D(self.thick))

        height = self.minuteHolderTotalHeight - self.cannonPinionThick - self.thick - self.thick  - self.minuteHandSlotHeight - self.space

        # hour = hour.faces(">Z").workplane().circle(self.hourHandHolderD/2).extrude(height)

        taperStartZ = height - 10

        if taperStartZ < 0:
            taperStartZ = 0

        holeR = self.minuteHandHolderD / 2 + self.space / 2

        # return hour
        circle = cq.Workplane("XY").circle(bottomR)
        shape = cq.Workplane("XZ").moveTo(bottomR,0).lineTo(midR,taperStartZ).lineTo(topR,height).lineTo(holeR,height).lineTo(holeR,0).close().sweep(circle).translate((0,0,self.thick))

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
