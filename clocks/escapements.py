import math

import numpy as np
import os

from .types import *

from .utility import *
from .gearing import *
from .decoration import *
import cadquery as cq

from cadquery import exporters

class AnchorEscapement:

    @staticmethod
    def get_with_45deg_pallets(teeth=30, type=EscapementType.DEADBEAT, lift_deg=3):
        '''
        Generate an anchor with pallets at 45 degrees, based only on the number of teeth

        lift is the angle of pendulum swing, in degrees

        drop is the rotation of the escape wheel between the teeth engaging the pallets - this is lost energy
        from the weight/spring.

        Lock "is the distance which the pallet has moved inside of the pitch circle of the escape wheel before being struck by the escape wheel tooth." (The Modern Clock)
        We add lock to the design by changing the position of the pallets

        Plan:
        Aim to calculate lock based on tooth size (maybe?)
        Use given lift where possible and report back the drop required to maintain that lift. Then I can decide how much lift to sacrifice to keep the clock reliable

        '''

        test_drop = 3
        test_anchor = AnchorEscapement(teeth=teeth, type=EscapementType.DEADBEAT, lift=lift_deg, drop=test_drop)
        test_anchor.getAnchor2D()
        print(test_anchor.pallet_angles)
        print(radToDeg(test_anchor.pallet_angles[0]), radToDeg(test_anchor.pallet_angles[1]))
        diff = radToDeg(test_anchor.pallet_angles[0] - test_anchor.pallet_angles[1])
        print(diff, "degrees")

    def __init__(self, teeth=30, diameter=100, anchorTeeth=None, type=EscapementType.DEADBEAT, lift=4, drop=2, run=10, lock=2, clockwiseFromPinionSide=True,
                 escapeWheelClockwise=True, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, wheelThick=3, forceDiameter=False, anchorThick=12,
                 style=AnchorStyle.STRAIGHT):
        '''
        originally: toothHeightFraction=0.2, toothTipAngle=9, toothBaseAngle=5.4
        This whole class needs a tidy up, there's a lot of dead code in here (recoil doesn't work anymore). The anchor STL is now primarily generated through the Arbour class
        because it ended up being more elegant to treat the anchor as the last arbour in the clock.



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
        The length and shape of the teeth will dictate the maximum lock achievable without clashing

        run is how much the anchor continues to move towards the centre of the escape wheel after locking (or in the recoil, how much it recoils) in degrees
        only makes sense for deadbeat
        Run is basically controlled by the weight/spring - it's how much power goes in. The value here is maximum run - the shape of the anchor

        clockwiseFromPinionSide is for the escape wheel

        anchorTeeth can override the size of teh anchor - by default we cover 1/4 of the teeth between the pallets to

        '''

        #if true, do not allow the gear train to override the diameter. The default is that the escape wheel size is adjusted to fit best.
        self.forceDiameter = forceDiameter

        #change the appearance of the anchor, doesn't affect function
        self.style = style

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

        #note, these set in setGearTrainInfo() called by the GoingTrain
        self.clockwiseFromPinionSide=clockwiseFromPinionSide
        self.escapeWheelClockwise=escapeWheelClockwise
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

        self.arbourD = 3
        self.anchorThick = anchorThick
        self.wheelThick = wheelThick

        self.pallet_angles = []

        self.centre_r = self.arbourD*2

    def getAnchorArbourD(self):
        return self.arbourD

    def getAnchorThick(self):
        return self.anchorThick

    def getWheelThick(self):
        return self.wheelThick

    def getWheelBaseToAnchorBaseZ(self):
        '''
        REturn Z change between the bottom of the wheel and the bottom of the anchor
        '''
        return -(self.anchorThick - self.wheelThick)/2

    def setGearTrainInfo(self, escapeWheelDiameter, escapeWheelClockwiseFromPinionSide, escapeWheelClockwise):
        '''
        Once the gear train has been calculated, it needs to provide info to the escapement (mostly used by the anchor escapment, not sure there's anything
        that the grasshopper actually needs to adjust here)
        '''
        if not self.forceDiameter:
            self.setDiameter(escapeWheelDiameter)
        self.clockwiseFromPinionSide = escapeWheelClockwiseFromPinionSide
        self.escapeWheelClockwise = escapeWheelClockwise

    def getDistanceBeteenArbours(self):
        return self.anchor_centre_distance

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
        NOTE - only deadbeat works at the moment, but since it's wonderfully reliable I don't see the need to revisit recoil

        As a side effect, this function sets self.pallet_angles. TODO refactor to perform all the maths elsewhere

        '''

        if self.type == EscapementType.RECOIL:
            #just in case I ever want this again?
            return self.getAnchor2DOld()

        anchor = cq.Workplane("XY").tag("anchorbase")

        anchorCentre = (0,self.anchor_centre_distance)
        wheelCentre = (0,0)



        armThick = self.diameter*0.05
        #aprox
        midEntryPalet = polar(math.pi + self.wheelAngle/2, self.radius)
        armLength = np.linalg.norm(np.subtract(midEntryPalet, anchorCentre))
        armThickAngle = armThick / armLength

        #angle of the arms holding the pallets - doesn't affect performance of escapement unless arc is really large (and then the arms crash into the teeth)
        deadbeatAngle=self.run#math.pi*0.05

        #for calculating the positions of the straight arms - this isn't quite right, but works
        if self.style == AnchorStyle.STRAIGHT:
            anchorCentreBottom = (0, self.anchor_centre_distance - (armThick/2)/ sin(self.anchorAngle/2))
            anchorCentreTop =  (0, self.anchor_centre_distance + (armThick/2)/ sin(self.anchorAngle/2))
        else:
            anchorCentreBottom = (0, self.anchor_centre_distance - self.centre_r)
            anchorCentreTop = (0, self.anchor_centre_distance + self.centre_r)

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

        # ========== pallet angles ==========

        entryPalletDifference = np.subtract(entryPalletEndPos, entryPalletStartPos)
        exitPalletDifference = np.subtract(exitPalletEndPos, exitPalletStartPos)

        self.pallet_angles = [math.atan2(entryPalletDifference[1], entryPalletDifference[0]), math.atan2(exitPalletDifference[1], exitPalletDifference[0])]

        # ========== points on the anchor =========

        #distance of the end of the entry pallet from the anchor centre
        entryPalletEndR = np.linalg.norm(np.subtract(entryPalletEndPos, anchorCentre))
        entryPalletStartR = np.linalg.norm(np.subtract(entryPalletStartPos, anchorCentre))
        innerLeftPoint = tuple(np.add(polar(math.pi*1.5 - self.anchorAngle/2 - palletLengthAngle/2 - deadbeatAngle, entryPalletEndR), anchorCentre))
        armThickAngleEntry = armThick/entryPalletEndR
        outerLeftPoint = tuple(np.add(polar(math.pi*1.5 - self.anchorAngle/2 - palletLengthAngle/2 - armThickAngleEntry - deadbeatAngle, entryPalletStartR), anchorCentre))

        exitPalletEndR = np.linalg.norm(np.subtract(exitPalletEndPos, anchorCentre))
        exitPalletStartR = np.linalg.norm(np.subtract(exitPalletStartPos, anchorCentre))
        innerRightPoint = tuple(np.add(polar(math.pi*1.5 + self.anchorAngle/2 + palletLengthAngle/2 + deadbeatAngle, exitPalletStartR), anchorCentre))
        armThickAngleExit = armThick/exitPalletEndR
        outerRightPoint = tuple(np.add(polar(math.pi*1.5 + self.anchorAngle/2 + palletLengthAngle/2 + deadbeatAngle + armThickAngleExit, exitPalletEndR), anchorCentre))

        if self.style == AnchorStyle.CURVED:
            #calculate the radii of the curved bits
            #sagitta (from wikipedia)
            #innerLeft and innerRight aren't quite parallel - inner right is slightly lower. I think this is expected as I don't attempt to keep inner radii the same
            s = anchorCentreBottom[1] - innerRightPoint[1]
            l = innerRightPoint[0] - innerLeftPoint[0]
            bottom_arm_r = s/2 + l**2/(8*s)
            top_arm_r = bottom_arm_r + armThick
        elif self.style == AnchorStyle.CURVED_MATCHING_WHEEL:
            bottom_arm_r = np.linalg.norm(innerRightPoint)
            top_arm_r = bottom_arm_r + armThick

        '''
        note - the locking faces are not equidistant (entryPalletStartR != exitPalletStartR). I don't know how necessary this actually is
        the current design clearly works, although I'm not certain that the escape wheel rotates the same amount with a 'tick' as a 'tock'.
        I'm also not convinced it's worth the effort - the current design works reliably and keeps as reasonable time as I would expect without temperature compensation
        save this for a rainy day?

        abbeyclock: "If the pallets were modified to make them with equidistant lock, the locking faces would be drawn on the same circle.
        However, the pendulum would receive unequal impulses in each direction. A pallet with equidistant drop could also be designed, but it has no practical application in horology."
        http://www.abbeyclock.com/aeb9.html
        
        So, in short, this is fine. equidistant lock is only required for watches according to abbeyclock (swiss or pin levers, I'm assuming) 
        
        
        
        other note:
        from Title: On the Mathematical Theory and Practical Defects of Clock Escapements, with a Description of a New Escapement; and some Observations connected with the same Subjects, on the Construction of other Parts of Clocks for Astronomical and Scientific Purposes
Authors: Mackenzie Bloxam, J.
Journal: Memoirs of the Royal Astronomical Society, Vol. 22, p.103

        "Hence the pendulum must be nearer to its vetical poisition, or position of rest, when the impulse begins, than when it ends;"
        So the impulse should be given when the pendulum is vertical, which I think I knew already but hadn't thought about. I think that means I should be adjusting lock more carefully?
        
        Given that these are never going to be precision regulators, I think I can be happy enough with reliable and semi-accurate.
        
        '''

        # entry pallet
        anchor = anchor.moveTo(entryPalletEndPos[0], entryPalletEndPos[1]).lineTo(entryPalletStartPos[0],entryPalletStartPos[1])

        if self.type == EscapementType.DEADBEAT:
            anchor = anchor.radiusArc(outerLeftPoint, entryPalletEndR+0.01)

        if self.style == AnchorStyle.STRAIGHT:
            #just temp - need proper arm and centre
            anchor = anchor.lineTo(anchorCentreTop[0], anchorCentreTop[1]).lineTo(outerRightPoint[0], outerRightPoint[1])
        elif self.style in [AnchorStyle.CURVED, AnchorStyle.CURVED_MATCHING_WHEEL]:
            anchor = anchor.radiusArc(outerRightPoint, top_arm_r)

        if self.type == EscapementType.DEADBEAT:
            anchor = anchor.radiusArc(exitPalletEndPos, exitPalletEndR)

        anchor = anchor.lineTo(exitPalletStartPos[0], exitPalletStartPos[1])

        if self.type == EscapementType.DEADBEAT:
            anchor = anchor.radiusArc(innerRightPoint, -exitPalletStartR)

        if self.style == AnchorStyle.STRAIGHT:
            anchor = anchor.lineTo(anchorCentreBottom[0], anchorCentreBottom[1]).lineTo(innerLeftPoint[0], innerLeftPoint[1])
        elif self.style in [AnchorStyle.CURVED, AnchorStyle.CURVED_MATCHING_WHEEL]:
            anchor = anchor.radiusArc(innerLeftPoint, -bottom_arm_r)

        if self.type == EscapementType.DEADBEAT:
            anchor = anchor.radiusArc(entryPalletEndPos, -entryPalletEndR)


        anchor = anchor.close()

        entryPalletAngle = math.atan2(entryPalletEndPos[1] - entryPalletStartPos[1], entryPalletEndPos[0] - entryPalletStartPos[0])

        # print("Entry Pallet Angle", radToDeg(entryPalletAngle))

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

        anchor = anchor.union(cq.Workplane("XY").moveTo(0, self.anchor_centre_distance).circle(self.centre_r).extrude(thick))



        anchor = anchor.extrude(thick)

        if not clockwise:
            anchor = anchor.mirror("YZ", (0,0,0))

        anchor = anchor.faces(">Z").workplane().moveTo(0,self.anchor_centre_distance).circle(holeD/2).cutThruAll()

        return anchor

    def getAnchor(self):
        '''
        compliant with the new escapement interface (now the grasshopper also exists)
        '''
        return self.getAnchor3D(thick = self.anchorThick, holeD=self.arbourD,clockwise=self.escapeWheelClockwise).translate((0,-self.anchor_centre_distance,0))

    def getAnchorMaxR(self):
        '''
        To allow enough space in the clock plates and anywhere else, HACK HACK HACK for now
        '''
        return self.arbourD*2

    def getAnchorArbour(self, holeD=3, anchorThick=10, arbourLength=0, crutchLength=0, crutchBoltD=3, pendulumThick=3, crutchToPendulum=35, nutMetricSize=0):#, forPrinting=True):
        '''
        Final plan: The crutch will be a solid part of the anchor, and a bolt will link it to a slot in the pendulum
        Thinking the anchor will be at the bottom of the clock, so the pendulum can be on the front

        length for how long to extend the 3d printed bit of the arbour - I'm still toying with the idea of using this to help keep things in place

        crutchToPendulum - top of the anchor to the start of the pendulum

        if nutMetricSize is provided, leave space for two nuts on either side (intended to be nyloc to fix the anchor to the rod)

        clockwise from the point of view of the side with the crutch - which may or may not be the front of the clock

        '''

        clockwise = self.escapeWheelClockwise

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

        #don't do this here, getting confusing
        # if crutchLength == 0 and nutMetricSize == 0 and arbourLength == 0 and forPrinting:
        #     #if we've got no crutch or nyloc nut, deliberately reverse it so the side facing forwards is the side printed on the nice textured sheet
        #     clockwise = not clockwise

        #get the anchor the other way around so we can build on top of it, and centre it on the pinion
        arbour = self.getAnchor3D(anchorThick, holeD, clockwise).translate([0,-self.anchor_centre_distance,0])

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

        if self.type == EscapementType.RECOIL:
            #based on the angle of the tooth being 20deg, but I want to calculate everyting in angles from the cetnre of the wheel
            #lazily assume arc along edge of inner wheel is a straight line
            toothAngle = math.pi*20/180
            toothTipAngle = 0
            toothBaseAngle = -math.atan(math.tan(toothAngle)*self.toothHeight/self.innerRadius)
        elif self.type == EscapementType.DEADBEAT:
            #done entirely by eye rather than working out the maths to adapt the book's geometry.
            toothTipAngle = -self.toothTipAngle#-math.pi*0.05
            toothBaseAngle = -self.toothBaseAngle#-math.pi*0.03
            toothTipArcAngle*=-1

        # print("tooth tip angle: {} tooth base angle: {}".format(radToDeg(toothTipAngle), radToDeg(toothBaseAngle)))

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

        gear = Gear.cutStyle(gear,outerRadius=self.innerRadius - holeD*0.5,innerRadius=innerRadiusForStyle, style=style, clockwise_from_pinion_side=self.clockwiseFromPinionSide)

        gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        return gear


    def getWheel(self, style=None, arbour_or_pivot_r=-1, holeD=3):
        return self.getWheel3D(thick = self.wheelThick, style=style,innerRadiusForStyle=arbour_or_pivot_r, holeD=holeD)

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

def getSpanner(size=4, thick=4, handle_length=150):
    '''
    Get a spanner for adjusting the anchor or pendulum fixing
    spannerBitThick is 4 by default
    centred on teh bit that turns
    '''
    
    sizeWithWiggle = size + 0.2

    strengthWidth = size*1.5
    armSize = strengthWidth# + size/2

    spanner = cq.Workplane("XY").moveTo(-sizeWithWiggle/2,sizeWithWiggle/2).line(-strengthWidth,0).line(0,-size - strengthWidth).line(strengthWidth*2 + sizeWithWiggle, 0).line(0, (strengthWidth + size) - armSize)\
        .line(handle_length,0).line(0,armSize).lineTo(sizeWithWiggle/2,sizeWithWiggle/2).line(0,-sizeWithWiggle).line(-sizeWithWiggle,0).close().extrude(thick)

    return spanner

class EscapmentInterface:
    '''
    Example of what the rest of the system expects from an escapement

    '''
    def __int__(self):
        self.teeth=None
        self.diameter=None
        self.type = EscapementType.NOT_IMPLEMENTED
        raise NotImplementedError()

    def setGearTrainInfo(self, escapeWheelDiameter, escapeWheelClockwiseFromPinionSide, escapeWheelClockwise):
        '''
        Once the gear train has been calculated, it needs to provide info to the escapement (mostly used by the anchor escapment, not sure there's anything
        that the grasshopper actually needs to adjust here)
        '''
        raise NotImplementedError()

    def getDistanceBeteenArbours(self):
        '''
        return distance between centre of escape wheel and the centre of the anchor/frame pivot point
        '''
        raise NotImplementedError()

    def getWheelThick(self):
        raise NotImplementedError()

    def getWheelMaxR(self):
        raise NotImplementedError()

    def getAnchorMaxR(self):
        raise NotImplementedError()

    def getAnchorArbourD(self):
        return 3

    def getAnchor(self):
        return None

    def getAnchorThick(self):
        return None

    def getWheel(self, style=None, arbour_or_pivot_r=-1, holeD=3):
        return None

    def getWheelBaseToAnchorBaseZ(self):
        '''
        REturn Z change between the bottom of the wheel and the bottom of the anchor
        '''

    # def get3D(self, holeD=0, thick=0, style="HAC", innerRadiusForStyle=-1):
    #     '''
    #     old bodge, pretend to be a gear wheel and return the wheel
    #     '''
    #     raise NotImplementedError()

class GrasshopperEscapement:

    @staticmethod
    def get_harrison_compliant_grasshopper():
        '''
        Return a grasshopper escapement which meets Harrison's stipulations as determined by David Heskin:
        9.75 escaping arc
        seconds pendulum
        mean torque arms 1% of pendulum length
        balanced escaping arcs
        '''

        #pre-calculated good values for a 9.75 escaping arc
        return GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)


    def __init__(self, pendulum_length_m=getPendulumLength(2), teeth=120, tooth_span=17.5, T=3/2, escaping_arc_deg=9.75,
                 mean_torque_arm_length=-1, d=-1, ax_deg=-1, diameter=-1, acceptableError=0.01, frame_thick=10, wheel_thick=5, pallet_thick=7, screws=None, arbourD=3,
                 loud_checks=False, skip_failed_checks=False, xmas=False, composer_min_distance=0, frame_screw_fixing_min_thick=10):
        '''
        From Computer Aided Design of Harrison Twin Pivot and Twin Balance Grasshopper Escapement Geometries by David Heskin

        T is the torque arm lengths ratio, defaults to harrison's stipulation. The "torque arms" are the length of an arm where the torque is applied to the pendulum by the entry pallet start/end and exit pallet start/end

        the following three can be provided, but if they aren't, will be auto generated within acceptableError:
         - 'ax' is the exit angle, which will just adjusted to control arc
         - 'd' is used in construction of the geometry, adjusted to provide balanced escape arcs
         - 'diameter' of the escape wheel. Automatically generated to provide the correct length mean torque arm

        For the construction of a 3D model (thick means in z direction here):
         - frame_thick: how thick the escapement frame should be, enough to be rigid
         - wheel_thick: how thick the escape wheel should be
         - pallet_thick: how thick the pallet arms should be, aiming for wider than the wheel thickness
         - screws: a MachineScrew to be used for pivot pins and composer stops
         - composer_min_distance: Should the composers be extra far away from the frame? (Useful if the means of mounting the frame is a bit chunky as the entry composer is very close to
         the axis)
         - frame_screw_fixing_min_thick: for a thin frame there may not be much for the screws that are the pivot for the pallet and composer arms, so extend the frame out the back

        All angles are radians unless specifically called `_deg`

        If an escaping arc is provided this will calculate the best 'd' and 'ax' to provide that escaping arc. This is slow, so you can provide pre-calculated d and ax instead

        loud_checks: if true then the geometry checking function will print out everything it is checking
        skip_failed_checks: if true then the geometry checking will just print, rather than assert, failures

        xmas: a special addition to the frame (a star) to make this christmassy
        '''

        self.type = EscapementType.GRASSHOPPER

        self.skip_failed_checks = skip_failed_checks
        self.xmas = xmas

        self.pendulum_length=pendulum_length_m*1000
        self.teeth=teeth
        self.tooth_span=tooth_span
        #I don't think there's actually anything to be gained from modifying this
        self.an=degToRad(90)
        self.T=T
        self.mean_torque_arm_length=mean_torque_arm_length
        if self.mean_torque_arm_length < 0:
            #harrison's stipulation, "The mean  torque  arm  should be  one hundredth  of  the pendulum length"
            self.mean_torque_arm_length = self.pendulum_length/100
        # self.escaping_arc_deg=escaping_arc_deg
        self.escaping_arc = degToRad(escaping_arc_deg)

        self.diagrams = []
        self.geometry = {}

        self.frame_thick = frame_thick
        # #for front mounted grasshopper, split the frame into two parts
        # self.frame_back_thick = frame_thick*0.5
        self.wheel_thick = wheel_thick
        self.pallet_thick = pallet_thick
        self.composer_min_distance = composer_min_distance
        self.frame_screw_fixing_min_thick = frame_screw_fixing_min_thick
        #angle from the arm to the nib, from the arm pivot, so the arm stays out the way of the wheel
        self.nib_offset_angle = degToRad(8)
        self.pallet_arm_wide=3
        self.screws = screws
        if self.screws is None:
            self.screws = MachineScrew(3)
        self.arbourD=arbourD

        self.frame_wide = self.screws.metric_thread * 2.5
        #I'd like to auto calculate this so the weight screw rests on top of the frame arm, but that can make things very complicated for the entry pallet
        #so, the weight screw will still rest on the frame arm, but the frame arm will adapt its shape to ensure that happens
        self.composer_height=10#7.5
        self.composer_thick=2.5

        #how much z between frame and the start of the composer, to leave space for screws and bits
        self.composer_z_distance_from_frame = WASHER_THICK_M3 + 0.2

        if self.composer_z_distance_from_frame < self.composer_min_distance:
            self.composer_z_distance_from_frame = self.composer_min_distance

        self.loose_on_pivot = 0.5

        #how much space along the threaded rod should be allowed to ensure the composer is loose (total space, half on each side of the pallet arm)
        self.composer_pivot_space = 0.5
        self.composer_arm_wide=self.screws.metric_thread*2.5

        #how much closer to the escape wheel should the composers keep the pallet arms?
        #first test revealed the exit pallet arm needed to be a tiny bit closer.
        #might this be because things are slightly wonky with the escapement out the front? - I'm leaning towards this thought
        #I may be able to make up for this with larger nibs as well (or instead of?)

        #note - first design resulted in the escape wheel arbour drooping down a bit and anchor arbour pointing up a bit (from weight of pendulum)
        # an exit composer fudge of 1mm and increasing the nib sizes made it reliable. However, there was more recoil on the exit side, maybe caused by this fudge?
        #with extra bearing holders (at back for anchor arbour and extended out from for escape arbour) I'm hoping these fudges will no longer be needed
        self.exit_composer_extra_fudge = 0#1
        self.entry_composer_extra_fudge = 0#0.8#0


        self.tooth_angle = math.pi*2/self.teeth

        '''with ax=90
        Iteration 52, testD: 12.220855468769212, errorTest: 1.9317880628477724e-14
        Balanced escaping arc of 9.65deg with d of 12.2209
        
        or with acceptable error = 0.1
        Iteration 6, testD: 12.203125, errorTest: -1.2386825430033e-05
        Balanced escaping arc of 9.64deg with d of 12.2031
        '''

        if ax_deg < 0 or d < 0 or diameter < 0:
            #auto calculate the best settings to get the chosen escaping arc and mean torque arm
            # d, En, Ex = self.balanceEscapingArcs(91, 0.1)
            if ax_deg < 0 and d< 0:
                ax_deg, d, En, Ex = self.chooseEscapingArc(acceptableError=acceptableError)
            elif d < 0 :
                d, En, Ex = self.balanceEscapingArcs(ax_deg, acceptableError)
            print("Balanced escaping arc of {:.4f}deg with d of {:.8f} and ax of {:.8f}".format(radToDeg(En), d, ax_deg))
            if diameter < 0:
                diameter, M = self.chooseDiameter(d_deg=d, ax_deg=ax_deg)
                print("Diameter of {:.8f} results in mean torque arm of {:.4f}".format(diameter, M))
            self.diameter = diameter
            self.radius = diameter / 2
        else:
            #all variables provided, just use them
            self.generate_geometry(d_deg=d, ax_deg=ax_deg, diameter=diameter)
            self.diameter = diameter
            self.radius = diameter / 2

        self.checkGeometry(loud=loud_checks)

        self.clockwiseFromPinionSide=True
        self.clockwise = True

    def setGearTrainInfo(self, escapeWheelDiameter, escapeWheelClockwiseFromPinionSide, escapeWheelClockwise):
        '''
        Once the gear train has been calculated, it needs to provide info to the escapement (mostly used by the anchor escapment, not sure there's anything
        that the grasshopper actually needs to adjust here)
        '''
        # self.escapement.setDiameter(escapeWheelDiameter)
        #if this isn't true, we'll need to flip the escape wheel when it's printed as part of the arbour
        self.clockwiseFromPinionSide = escapeWheelClockwiseFromPinionSide
        self.clockwise = escapeWheelClockwise
        if not self.clockwise:
            raise ValueError("Grasshopper escapement not yet supported anticlockwise")

    def getDistanceBeteenArbours(self):
        return distanceBetweenTwoPoints(self.geometry["Z"],self.geometry["O"])

    def getWheelMaxR(self):
        return self.diameter/2

    def getAnchorMaxR(self):
        #TODO
        return 10

    def getAnchorArbourD(self):
        return self.arbourD

    def chooseDiameter(self, d_deg, ax_deg):
        '''
        Once the escaping arcs are balanced, use this to get the mean torque arm length correct

        linear scaling works fine for this - didn't need a binary search!
        '''
        testD = 100
        En, Ex, M = self.generate_geometry(ax_deg=ax_deg, d_deg=d_deg, diameter=testD)
        MRatio = self.mean_torque_arm_length/M
        diameter = testD * MRatio
        En, Ex, M = self.generate_geometry(ax_deg=ax_deg, d_deg=d_deg, diameter=diameter)
        return diameter, M

    def chooseEscapingArc(self, iterations = 100, acceptableError = 0.1):
        '''
        Fiddle with values of ax (exit angle) and balance the escaping arcs so we can choose what we want the escaping arc to be

        uses same binary search idea as balanceEscapingArcs and getRadiusForPointsOnAnArc

        larger ax values seem to result in larger arcs
        '''

        #use acceptableError larger than zero to speed this up
        minAx=85
        maxAx=95
        testAx_deg=minAx
        d, En, Ex = self.balanceEscapingArcs(testAx_deg, acceptableError)
        errorTest=self.escaping_arc - En
        lastTestAx = 0

        for i in range(iterations):
            print("chooseEscapingArc Iteration {}, testAx: {}, errorTest: {}".format(i,testAx_deg, errorTest))
            if errorTest > 0:
                # ax is too small
                minAx = testAx_deg

            if errorTest < 0:
                # ax is too large
                maxAx = testAx_deg

            if errorTest == 0 or abs(testAx_deg - lastTestAx) <= acceptableError:
                # turns out errorTest == 0 can happen. hurrah for floating point! Sometimes however we don't get to zero, but we can't refine testD anymore
                print("Iteration {}, testAx: {}, errorTest: {}".format(i,testAx_deg, errorTest))
                # print("found after {} iterations".format(i))
                d, En, Ex = self.balanceEscapingArcs(testAx_deg, acceptableError=0)
                break
            lastTestAx = testAx_deg
            testAx_deg = (minAx + maxAx) / 2
            d, En, Ex = self.balanceEscapingArcs(testAx_deg, acceptableError)
            errorTest = self.escaping_arc - En

        return (testAx_deg, d, En, Ex)

    def balanceEscapingArcs(self, ax_deg=90, acceptableError=0, iterations = 100):
        # inspired by getRadiusForPointsOnAnArc, binary search to find best D, which balances the escaping arcs
        # see BALANCING THE ESCAPING ARCS

        minD = 9
        maxD = 14
        testD = minD
        En, Ex, M = self.generate_geometry(testD, ax_deg=ax_deg)
        errorTest = Ex - En
        lastTestD = 0

        for i in range(iterations):
            # print("Iteration {}, testR: {}, errorTest: {}".format(i,testR, errorTest))
            if errorTest < 0:
                # d is too small
                minD = testD

            if errorTest > 0:
                # d is too large
                maxD = testD

            if errorTest == 0 or abs(testD - lastTestD) <= acceptableError:
                # turns out errorTest == 0 can happen. hurrah for floating point! Sometimes however we don't get to zero, but we can't refine testD anymore
                # print("balanceEscapingArcs Iteration {}, testD: {}, errorTest: {}".format(i, testD, errorTest))
                # print("found after {} iterations".format(i))
                break
            lastTestD = testD
            testD = (minD + maxD) / 2
            En, Ex, M = self.generate_geometry(testD, ax_deg=ax_deg)
            errorTest = Ex - En

        return (testD, En, Ex)

    def generate_geometry(self, d_deg=11, ax_deg=90, diameter=152):

        radius = diameter/2
        #default to 90, can adjust to control the arc
        ax = degToRad(ax_deg)

        #these can apparently be arbitrary as the result comes out the same
        active_length_entry_pallet_arm = 10
        active_length_exit_pallet_arm = 7.5

        def circleAt(point, r=0.5, text=None):
            circle = cq.Workplane("XY").moveTo(point[0], point[1]).circle(r)
            if text is not None:
                circle = circle.add(cq.Workplane("XY").text(text, fontsize=r*4, distance=0.1).translate((point[0] + r*2, point[1])))

            return circle

        #escape wheel centred on 0,0
        # ========== STEP ONE ===========

        #[3] At the start of exit impulse, the exit pallet nib locking corner is captured by an escape wheel tooth tip located at point D
        D_start_of_exit_impulse = polar(0, radius)
        line_3 = Line((0,0), anotherPoint=D_start_of_exit_impulse)
        #[4] clockwise by half a tooth angle
        end_of_exit_impulse_angle = -self.tooth_angle/2
        C_end_of_exit_impulse = polar(end_of_exit_impulse_angle, radius)
        line_4 = Line((0,0), anotherPoint=C_end_of_exit_impulse)

        #[5]
        minimum_tooth_space = math.floor(self.tooth_span)
        minimum_tooth_angle = minimum_tooth_space * math.pi*2 / self.teeth
        #I think this is end of the entry impulse?
        K_end_of_entry_impulse = polar(0 + minimum_tooth_angle, radius)
        line_5 = Line((0,0), anotherPoint=K_end_of_entry_impulse)

        #[6]
        maximum_tooth_space = math.ceil(self.tooth_span)
        maxiumum_tooth_angle = maximum_tooth_space*math.pi*2 / self.teeth
        #anticlockwise from end of exit impulse by maximum arc of teeth
        J_angle = end_of_exit_impulse_angle + maxiumum_tooth_angle
        J_start_of_entry_impulse = polar( J_angle, radius)
        line_6 = Line((0,0), anotherPoint=J_start_of_entry_impulse)


        #[7]
        line_7_entry_start_of_impulse_action = Line(J_start_of_entry_impulse, angle= J_angle + math.pi + self.an)

        #[8]
        line_8_exit_pallet_start_line_of_action = Line(D_start_of_exit_impulse, angle = 0 + ax)

        step_one_figure_35 = cq.Workplane("XY").circle(radius)
        step_one_figure_35 = step_one_figure_35.add(line_3.get2D(radius))
        step_one_figure_35 = step_one_figure_35.add(line_4.get2D(radius))
        step_one_figure_35 = step_one_figure_35.add(line_5.get2D(radius))
        step_one_figure_35 = step_one_figure_35.add(line_6.get2D(radius))
        step_one_figure_35 = step_one_figure_35.add(line_7_entry_start_of_impulse_action.get2D())
        step_one_figure_35 = step_one_figure_35.add(line_8_exit_pallet_start_line_of_action.get2D())

        # return step_one_figure_35
        # ============ STEP TWO ============
        #what happened to [9]?


        #[10]
        #arbitary to start with
        d = degToRad(d_deg)
        #I think this will be the centre of the torque arms?
        line_10 = Line([0,0],d)

        #[11]
        # lines_8_and_10_intersect = radial_ten.intersection(line_8_exit_pallet_start_line_of_action)
        # lines_7_and_10_intersect = radial_ten.intersection(line_7_entry_start_of_impulse_action)

        intersection_of_lines_7_and_8 = line_7_entry_start_of_impulse_action.intersection(line_8_exit_pallet_start_line_of_action)

        line_8_downwards = Line(line_8_exit_pallet_start_line_of_action.start, direction=[line_8_exit_pallet_start_line_of_action.dir[0]*-1, line_8_exit_pallet_start_line_of_action.dir[1]*-1])

        average_direction_of_lines_7_and_8 = averageOfTwoPoints(line_7_entry_start_of_impulse_action.dir, line_8_downwards.dir)
        #line 11 bisects the acute angle between lines [7] and [8]
        line_11 = Line(intersection_of_lines_7_and_8, direction=average_direction_of_lines_7_and_8)
        #[12]
        # line_12 = Line(Z, line_7_entry_start_of_impulse_action.get_perpendicular_direction(clockwise=False))

        Z = line_11.intersection(line_10)

        #[12]

        line_12 = Line(Z, direction=line_7_entry_start_of_impulse_action.get_perpendicular_direction(clockwise=False))

        line_12_intersect_line_7_point = line_12.intersection(line_7_entry_start_of_impulse_action)

        line_12_length = distanceBetweenTwoPoints(Z, line_12_intersect_line_7_point)

        circle_13_r = line_12_length

        step_two_figure_36 = step_one_figure_35
        step_two_figure_36 = step_two_figure_36.add(line_10.get2D())
        step_two_figure_36 = step_two_figure_36.add(line_11.get2D())
        step_two_figure_36 = step_two_figure_36.add(line_12.get2D(line_12_length))
        step_two_figure_36 = step_two_figure_36.add(cq.Workplane("XY").moveTo(Z[0], Z[1]).circle(circle_13_r))

        # return step_two_figure_36

        # =========== STEP THREE =========

        #[14]
        circle_14_r = circle_13_r * self.T

        #[15]
        line_15_end_of_entry_impulse = getPreferredTangentThroughPoint(Z, circle_14_r, K_end_of_entry_impulse, clockwise=True)

        #[16]
        line_16_end_of_exit_impulse = getPreferredTangentThroughPoint(Z, circle_14_r, C_end_of_exit_impulse, clockwise=True)

        step_three_figure_37 = step_two_figure_36
        step_three_figure_37 = step_three_figure_37.add(cq.Workplane("XY").moveTo(Z[0], Z[1]).circle(circle_14_r))
        #hackery: anotherPoint is the tangent point
        step_three_figure_37 = step_three_figure_37.add(line_15_end_of_entry_impulse.get2D(distanceBetweenTwoPoints(line_15_end_of_entry_impulse.start, line_15_end_of_entry_impulse.anotherPoint)))
        step_three_figure_37 = step_three_figure_37.add(line_16_end_of_exit_impulse.get2D(distanceBetweenTwoPoints(line_16_end_of_exit_impulse.start, line_16_end_of_exit_impulse.anotherPoint)))

        # return step_three_figure_37

        # ============ STEP FOUR =================

        circle_17_r = active_length_entry_pallet_arm
        circle_17_centre = J_start_of_entry_impulse
        towardsS = polar(line_7_entry_start_of_impulse_action.getAngle(), circle_17_r)
        S = (circle_17_centre[0] + towardsS[0], circle_17_centre[1] + towardsS[1])


        circle_18_r = active_length_entry_pallet_arm
        circle_18_centre = K_end_of_entry_impulse
        towardsT = polar(line_15_end_of_entry_impulse.getAngle(), circle_18_r)
        T = (circle_18_centre[0] + towardsT[0], circle_18_centre[1] + towardsT[1])

        circle_19_centre = D_start_of_exit_impulse
        circle_19_r = active_length_exit_pallet_arm
        circle_20_centre = C_end_of_exit_impulse
        circle_20_r = active_length_exit_pallet_arm

        towardsQ = polar(line_8_exit_pallet_start_line_of_action.getAngle() + math.pi, circle_19_r)
        Q = (circle_19_centre[0] + towardsQ[0], circle_19_centre[1] + towardsQ[1])

        towardsR = polar(line_16_end_of_exit_impulse.getAngle() + math.pi, circle_20_r)
        R = (circle_20_centre[0] + towardsR[0], circle_20_centre[1] + towardsR[1])

        step_four_figure_38 = step_three_figure_37
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(circle_17_centre[0], circle_17_centre[1]).circle(circle_17_r))
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(circle_18_centre[0], circle_18_centre[1]).circle(circle_18_r))
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(S[0], S[1]).circle(0.5))
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(T[0], T[1]).circle(0.5))

        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(circle_19_centre[0], circle_19_centre[1]).circle(circle_19_r))
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(circle_20_centre[0], circle_20_centre[1]).circle(circle_20_r))
        step_four_figure_38 = step_four_figure_38.add(line_8_exit_pallet_start_line_of_action.get2D(-circle_19_r))
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(Q[0], Q[1]).circle(0.5))
        step_four_figure_38 = step_four_figure_38.add(line_16_end_of_exit_impulse.get2D(-circle_20_r))
        step_four_figure_38 = step_four_figure_38.add(cq.Workplane("XY").moveTo(R[0], R[1]).circle(0.5))

        # return step_four_figure_38

        # ========== STEP FIVE =================

        #entry geometry
        line_23_ST = Line(S, anotherPoint=T)
        line_24_dir = line_23_ST.get_perpendicular_direction(clockwise=False)
        line_24 = Line(averageOfTwoPoints(S,T), direction=line_24_dir)

        line_25_JK = Line(J_start_of_entry_impulse, anotherPoint=K_end_of_entry_impulse)
        line_26_dir = line_25_JK.get_perpendicular_direction(clockwise=False)
        line_26 = Line(averageOfTwoPoints(J_start_of_entry_impulse, K_end_of_entry_impulse), direction=line_26_dir)

        V = line_26.intersection(line_24)

        #exit geometry

        line_27_QR = Line(Q, anotherPoint=R)
        line_28_dir = line_27_QR.get_perpendicular_direction(clockwise=False)
        line_28 = Line(averageOfTwoPoints(Q,R), direction = line_28_dir)

        line_29_DC = Line(D_start_of_exit_impulse, anotherPoint=C_end_of_exit_impulse)
        line_30_dir = line_29_DC.get_perpendicular_direction(clockwise=False)
        line_30 = Line(averageOfTwoPoints(D_start_of_exit_impulse, C_end_of_exit_impulse), direction=line_30_dir)

        W = line_30.intersection(line_28)


        step_five_figure_39 = step_four_figure_38
        step_five_figure_39 = step_five_figure_39.add(line_24.get2D())
        step_five_figure_39 = step_five_figure_39.add(line_26.get2D())
        step_five_figure_39 = step_five_figure_39.add(cq.Workplane("XY").moveTo(V[0], V[1]).circle(0.5))
        step_five_figure_39 = step_five_figure_39.add(line_28.get2D(20))
        step_five_figure_39 = step_five_figure_39.add(line_30.get2D(20))
        step_five_figure_39 = step_five_figure_39.add(cq.Workplane("XY").moveTo(W[0], W[1]).circle(0.5))

        # return step_five_figure_39
        # ============= STEP SIX =============

        line_31_VZ = Line(V, anotherPoint=Z)
        line_32_JKmid_STmid = Line(averageOfTwoPoints(J_start_of_entry_impulse, K_end_of_entry_impulse), anotherPoint=averageOfTwoPoints(S,T))

        PN_centre = line_31_VZ.intersection(line_32_JKmid_STmid)

        line_33_PN = Line(PN_centre, direction=line_31_VZ.get_perpendicular_direction())

        #For an escapement frame arbor axis at Z, point P is the entry pallet arm pivot location at the start of entry impulse and JP is the entry pallet arm active length.
        P = line_33_PN.intersection(line_7_entry_start_of_impulse_action)
        #For an escapement frame arbor axis at Z, point N is the entry pallet arm pivot location at the end of entry impulse and KN is the entry pallet arm active length.
        N = line_33_PN.intersection(line_15_end_of_entry_impulse)



        line_34_ZW = Line(Z, anotherPoint=W)
        line_35_CDmid_QRmid = Line(averageOfTwoPoints(C_end_of_exit_impulse,D_start_of_exit_impulse), anotherPoint=averageOfTwoPoints(Q,R))
        FG_centre = line_35_CDmid_QRmid.intersection(line_34_ZW)
        line_36_FG = Line(FG_centre, direction=line_34_ZW.get_perpendicular_direction())

        #could have been defined earlier, doesn't seem to have been (I think this one was 'obvious' previously)
        line_21_DQ = Line(D_start_of_exit_impulse, anotherPoint=Q)
        line_22_CR = Line(C_end_of_exit_impulse, anotherPoint=R)
        F = line_36_FG.intersection(line_21_DQ)
        G = line_36_FG.intersection(line_22_CR)

        '''
        ■ By virtue of universal properties of W (see APPENDIX), DF will match CG, FW will match GW and (therefore)
        FZ will match GZ, thereby ensuring correct functioning of the exit geometry incorporating Z, D, C, F and G.
        TODO check this has worked!
        '''


        step_six_figure_40 = step_five_figure_39
        step_six_figure_40 = step_six_figure_40.add(line_31_VZ.get2D())
        step_six_figure_40 = step_six_figure_40.add(line_32_JKmid_STmid.get2D())
        step_six_figure_40 = step_six_figure_40.add(line_33_PN.get2D(length=5, both_directions=True))
        step_six_figure_40 = step_six_figure_40.add(cq.Workplane("XY").moveTo(P[0], P[1]).circle(0.5))
        step_six_figure_40 = step_six_figure_40.add(cq.Workplane("XY").moveTo(N[0], N[1]).circle(0.5))
        step_six_figure_40 = step_six_figure_40.add(line_34_ZW.get2D())
        step_six_figure_40 = step_six_figure_40.add(line_35_CDmid_QRmid.get2D())
        step_six_figure_40 = step_six_figure_40.add(line_36_FG.get2D(length=5, both_directions=True))
        step_six_figure_40 = step_six_figure_40.add(cq.Workplane("XY").moveTo(F[0], F[1]).circle(0.5))
        step_six_figure_40 = step_six_figure_40.add(cq.Workplane("XY").moveTo(G[0], G[1]).circle(0.5))
        # return step_six_figure_40


        # ============= STEP SEVEN ==============
        #This line represents the physical connection between the escapement frame arbor axis and the entry pallet arm pivot at the end of entry impulse
        line_37_ZN = Line(Z, anotherPoint=N)
        line_38_ZP = Line(Z, anotherPoint=P)

        #. This is the escaping arc of the entry geometry.
        En = line_38_ZP.getAngle() - line_37_ZN.getAngle()



        line_39_ZF = Line(Z, anotherPoint=F)
        line_40_ZG = Line(Z, anotherPoint=G)

        Ex = line_40_ZG.getAngle() - line_39_ZF.getAngle()



        step_seven_figure_40 = cq.Workplane("XY").circle(radius)
        step_seven_figure_40 = step_seven_figure_40.add(line_3.get2D(radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_4.get2D(radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_5.get2D(radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_6.get2D(radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_10.get2D())
        step_seven_figure_40 = step_seven_figure_40.add(cq.Workplane("XY").moveTo(Z[0], Z[1]).circle(0.5))
        step_seven_figure_40 = step_seven_figure_40.add(cq.Workplane("XY").moveTo(P[0], P[1]).circle(0.5))
        step_seven_figure_40 = step_seven_figure_40.add(cq.Workplane("XY").moveTo(N[0], N[1]).circle(0.5))
        step_seven_figure_40 = step_seven_figure_40.add(cq.Workplane("XY").moveTo(F[0], F[1]).circle(0.5))
        step_seven_figure_40 = step_seven_figure_40.add(cq.Workplane("XY").moveTo(G[0], G[1]).circle(0.5))

        step_seven_figure_40 = step_seven_figure_40.add(line_37_ZN.get2D())
        step_seven_figure_40 = step_seven_figure_40.add(line_38_ZP.get2D())

        step_seven_figure_40 = step_seven_figure_40.add(line_39_ZF.get2D())
        step_seven_figure_40 = step_seven_figure_40.add(line_40_ZG.get2D())


        # return step_seven_figure_40

        # ============= INSTANTANEOUS PALLET NIB LOCKING CORNER LIFTS ====================
        #where the entry composer should keep the pallet arms - this where they come to rest after they "spring" away from the tooth

        #Perfecting the Harrison Twin Pivot Grasshopper Escapement, an older publication from David Heskin, goes into slightly more detail but is slightly different

        #K* is where the entry nib comes to rest: "derived from circular arcs through J centred at Z, through K centred at N"
        circle_around_Z_to_J_r = distanceBetweenTwoPoints(Z, J_start_of_entry_impulse)
        circle_around_N_r = distanceBetweenTwoPoints(K_end_of_entry_impulse, N)

        Kstar_possibilities = get_circle_intersections(Z, circle_around_Z_to_J_r, N, circle_around_N_r)
        #find the one that's nearest to K, not the one that's mirrored on the other size soemwhere
        Kstar_possibility_distances = [distanceBetweenTwoPoints(K_end_of_entry_impulse, Kstar) for Kstar in Kstar_possibilities]
        if Kstar_possibility_distances[0] < Kstar_possibility_distances[1]:
            Kstar = Kstar_possibilities[0]
        else:
            Kstar = Kstar_possibilities[1]

        # C* is where the exit nib comes to rest : "derived from circular arcs ... through Dcentred at Z and through C centred at G"
        circle_around_Z_to_D_r = distanceBetweenTwoPoints(Z, D_start_of_exit_impulse)
        circle_around_G_r = distanceBetweenTwoPoints(G, C_end_of_exit_impulse)
        Cstar_posibilities = get_circle_intersections(Z, circle_around_Z_to_D_r, G, circle_around_G_r)

        Cstar_possibility_distances = [distanceBetweenTwoPoints(C_end_of_exit_impulse, Cstar) for Cstar in Cstar_posibilities]
        if Cstar_possibility_distances[0] < Cstar_possibility_distances[1]:
            Cstar = Cstar_posibilities[0]
        else:
            Cstar = Cstar_posibilities[1]

        diagram_for_points = cq.Workplane("XY")
        diagram_for_points = diagram_for_points.add(cq.Workplane("XY").circle(radius))
        diagram_for_points = diagram_for_points.add(line_6.get2D(length=radius))
        diagram_for_points = diagram_for_points.add(line_5.get2D(length=radius))
        diagram_for_points = diagram_for_points.add(line_3.get2D(length=radius))
        diagram_for_points = diagram_for_points.add(line_4.get2D(length=radius))
        diagram_for_points.add(circleAt(Z, text="Z"))
        diagram_for_points = diagram_for_points.add(line_10.get2D(length=distanceBetweenTwoPoints((0,0), Z)))
        diagram_for_points.add(circleAt(J_start_of_entry_impulse, text="J"))
        diagram_for_points.add(circleAt(K_end_of_entry_impulse, text="K"))
        diagram_for_points.add(circleAt(Kstar, text="K*"))
        diagram_for_points.add(circleAt(P, text="P"))
        diagram_for_points.add(circleAt(N, text="N"))
        diagram_for_points.add(circleAt(C_end_of_exit_impulse, text="C"))
        diagram_for_points.add(circleAt(D_start_of_exit_impulse, text="D"))
        diagram_for_points.add(circleAt(F, text="F"))
        diagram_for_points.add(circleAt(G, text="G"))
        diagram_for_points.add(circleAt(Cstar, text="C*"))

        self.geometry={}
        #centre of escape wheel, just assumed until now
        self.geometry["O"]=(0,0)
        #entry nib start of impulse
        self.geometry["J"]=J_start_of_entry_impulse
        #entry nib end of impulse. Angle JOK is half a tooth
        self.geometry["K"] = K_end_of_entry_impulse
        #where the nib ends up just after being released. K* (relative to N) is where the exit composer should hold the entry pivot arm
        self.geometry["Kstar"]=Kstar
        #the entry pallet pivot point at start of impulse
        self.geometry["P"]=P
        #the entry pallet pivot point at end of impulse (when the nib swings from K to K*)
        self.geometry["N"]=N
        #The 'anchor' arbour pivot point - fixed to the clock.
        self.geometry["Z"]=Z
        #exit nib start of impulse
        self.geometry["D"]=D_start_of_exit_impulse
        #exit nib end of impulse. Angle DOC is half a tooth
        self.geometry["C"]=C_end_of_exit_impulse
        #where the exit nib ends up just after being released. C* (relative to G) is where the exit composer should hold the exit pivot arm
        self.geometry["Cstar"]=Cstar
        #exit pallet pivot point at start of exit impulse
        self.geometry["F"]=F
        #exit pallet pivot point at end of impulse
        self.geometry["G"]=G

        self.geometry["ax"]=ax


        '''
        The mean torque arm circle is, i think, ultimately dervived from teh choice of diameter, so it needs to be calculated here so we can iterate the diameter to get it right!
        the below copy-pasted and tweaked from the geometry check function
        '''
        geometry = self.geometry
        line_PJ = Line(geometry["P"], anotherPoint=geometry["J"])
        line_DF = Line(geometry["D"], anotherPoint=geometry["F"])
        start_of_impulse_torque_circle_radius_entry = line_PJ.getShortestDistanceToPoint(geometry["Z"])
        start_of_impulse_torque_circle_radius_exit = line_DF.getShortestDistanceToPoint(geometry["Z"])
        line_KN = Line(geometry["K"], anotherPoint=geometry["N"])
        line_GC = Line(geometry["G"], anotherPoint=geometry["C"])
        end_of_impulse_torque_circle_radius_entry = line_KN.getShortestDistanceToPoint(geometry["Z"])
        end_of_impulse_torque_circle_radius_exit = line_GC.getShortestDistanceToPoint(geometry["Z"])
        # check 10b (there are two check 10s): EZ / HZ should match the designer-chosen end/start ratio, T. For Harrison compliant geometries, the ratio should be 3 / 2.
        HZ = start_of_impulse_torque_circle_radius_entry
        EZ = end_of_impulse_torque_circle_radius_entry
        T = EZ / HZ
        # check 12: In the final, scaled geometry, 0.5 (HZ + EZ) = dimension M in Fig. 46 should match the designer-chosen mean torque arm, M*
        M = (EZ + HZ) / 2

        self.geometry["M"] = M





        self.diagrams = [step_one_figure_35, step_two_figure_36, step_three_figure_37, step_four_figure_38, step_five_figure_39, step_six_figure_40, step_seven_figure_40, diagram_for_points]

        return [En, Ex, M]

    def checkGeometry(self, geometry=None, acceptableError=0.00001, loud=False):
        if geometry is None:
            geometry = self.geometry
        #check 1: Angle COD should be the angle subtended by half an escape wheel tooth space
        half_tooth_angle = (math.pi*2/self.teeth)/2
        line_CO = Line(geometry["C"], anotherPoint=geometry["O"])
        line_OD = Line(geometry["O"], anotherPoint=geometry["D"])
        COD = line_CO.getAngleBetweenLines(line_OD)
        if loud:
            print("COD: {}deg, half tooth angle:{}deg".format(radToDeg(COD), radToDeg(half_tooth_angle)))
        if not self.skip_failed_checks:
            assert abs(COD - half_tooth_angle) < acceptableError, "check 1: Angle COD should be the angle subtended by half an escape wheel tooth space"

        #check 2: Angle DOK should be the angle subtended by the minimum tooth spaces spanned.
        minimum_tooth_spaces = floor(self.tooth_span)*math.pi*2/self.teeth
        line_DO = Line(geometry["D"], anotherPoint=geometry["O"])
        line_OK = Line(geometry["O"], anotherPoint=geometry["K"])
        DOK = line_DO.getAngleBetweenLines(line_OK)
        if loud:
            print("DOK: {}deg, minimum_tooth_spaces: {}deg".format(radToDeg(DOK), radToDeg(minimum_tooth_spaces)))
        if not self.skip_failed_checks:
            assert abs(DOK - minimum_tooth_spaces) < acceptableError, "check 2: Angle DOK should be the angle subtended by the minimum tooth spaces spanned."

        #check 3: Angle COJ should be the angle subtended by the maximum tooth spaces spanned.
        maximum_tooth_spaces = math.ceil(self.tooth_span)*math.pi*2/self.teeth
        line_OJ = Line(geometry["O"], anotherPoint=geometry["J"])
        COJ = line_CO.getAngleBetweenLines(line_OJ)
        if loud:
            print("COJ: {}deg, maximum_tooth_spaces: {}deg".format(radToDeg(COJ), radToDeg(maximum_tooth_spaces)))
        if not self.skip_failed_checks:
            assert abs(COJ - maximum_tooth_spaces) < acceptableError, "check 3: Angle COJ should be the angle subtended by the maximum tooth spaces spanned."

        #check 4: Angle JOK should be the angle subtended by half an escape wheel tooth space
        JOK = line_OJ.getAngleBetweenLines(line_OK)
        if loud:
            print("JOK: {}deg, half tooth: {}deg".format(radToDeg(JOK), radToDeg(half_tooth_angle)))
        if not self.skip_failed_checks:
            assert abs(JOK - half_tooth_angle) < acceptableError, "check 4: Angle JOK should be the angle subtended by half an escape wheel tooth space"

        #check 5: JP should equal KN (equal entry pallet arm active lengths at the start and end of impulse).
        JP = distanceBetweenTwoPoints(geometry["J"], geometry["P"])
        KN = distanceBetweenTwoPoints(geometry["K"], geometry["N"])
        if loud:
            print("JP: {}, KN: {}".format(JP, KN))
        if not self.skip_failed_checks:
            assert abs(JP - KN) < acceptableError, "check 5: JP should equal KN (equal entry pallet arm active lengths at the start and end of impulse)."

        #check 6: DF should equal CG (equal exit pallet arm active lengths at the start and end of impulse).
        DF = distanceBetweenTwoPoints(geometry["D"], geometry["F"])
        CG = distanceBetweenTwoPoints(geometry["C"], geometry["G"])
        if loud:
            print("DF: {} CG: {}".format(DF, CG))
        if not self.skip_failed_checks:
            assert abs(DF - CG) < acceptableError, "check 6: DF should equal CG (equal exit pallet arm active lengths at the start and end of impulse)."

        #check 7: PZ should equal NZ (entry pallet pivot to escapement frame axis at the start and end of impulse).
        PZ = distanceBetweenTwoPoints(geometry["P"], geometry["Z"])
        NZ = distanceBetweenTwoPoints(geometry["N"], geometry["Z"])
        if loud:
            print("PZ: {}, NZ: {}".format(PZ, NZ))
        if not self.skip_failed_checks:
            assert abs(PZ - NZ) < acceptableError, "check 7: PZ should equal NZ (entry pallet pivot to escapement frame axis at the start and end of impulse)."

        #check 8: FZ should equal GZ (exit pallet pivot to escapement frame axis at the start and end of impulse).
        FZ = distanceBetweenTwoPoints(geometry["F"], geometry["Z"])
        GZ = distanceBetweenTwoPoints(geometry["G"], geometry["Z"])
        if loud:
            print("FZ: {}, GZ: {}".format(FZ, GZ))
        if not self.skip_failed_checks:
            assert abs(FZ - GZ) < acceptableError, "check 8: FZ should equal GZ (exit pallet pivot to escapement frame axis at the start and end of impulse)."

        #check 9: Angle PJO should match the designer-chosen STEP ONE entry angle (self.an)
        line_PJ = Line(geometry["P"], anotherPoint=geometry["J"])
        PJO = line_PJ.getAngleBetweenLines(line_OJ)
        if loud:
            print("PJO: {}deg an: {}deg".format(radToDeg(PJO), radToDeg(self.an)))
        if not self.skip_failed_checks:
            assert abs(PJO - self.an) < acceptableError, " Angle PJO should match the designer-chosen STEP ONE entry angle (an)"

        '''check 10: Angle HDO should almost match the designer-chosen STEP ONE initial exit angle. Within two
        degrees is proposed, although opinions may differ. A greater deviation from the initial choice suggests
        that an alteration to the mean span should be investigated, as explained on page 41.
        '''
        #I don't ever calculate H, but HDF are in a line, so use line DF instead of HD
        line_DF = Line(geometry["D"], anotherPoint=geometry["F"])
        HDO = line_DF.getAngleBetweenLines(line_DO)
        if loud:
            print("HDO/DFO: {}deg ax: {}deg".format(radToDeg(HDO), radToDeg(geometry["ax"])))
        if not self.skip_failed_checks:
            assert abs(HDO - geometry["ax"]) < degToRad(2), "check 10: Angle HDO should almost match the designer-chosen STEP ONE initial exit angle ax"

        '''
        check 11: Start of impulse lines of action JL and FH should be tangential to the smaller, green, start of impulse
        torque arm circle and end of impulse lines of action KM and GE should be tangential to the larger, red,
        end of impulse torque arm circle.
        
        Again, I've don't calculate L or H (points on the start of impulse torque circle), so I'll try and check that lines JP and FD pass at the right distance from Z
        
        I haven't written a "find the nearest point on the circle from a line" function, so I'll create a circle, find the tangent point that goes through D/P and check the angle between LP and JP is 0
        ...I can't do that as I don't know what the radius is of the torque circle. I'll have to write that function or skip these tests for now
        '''
        start_of_impulse_torque_circle_radius_entry = line_PJ.getShortestDistanceToPoint(geometry["Z"])
        start_of_impulse_torque_circle_radius_exit = line_DF.getShortestDistanceToPoint(geometry["Z"])
        if loud:
            print("Start of impulse torque circle radii: {} {}".format(start_of_impulse_torque_circle_radius_entry, start_of_impulse_torque_circle_radius_exit))

        if not self.skip_failed_checks:
            assert abs(start_of_impulse_torque_circle_radius_entry - start_of_impulse_torque_circle_radius_exit) < acceptableError, "start impulse torque circle radii not equal"

        line_KN = Line(geometry["K"], anotherPoint=geometry["N"])
        line_GC = Line(geometry["G"], anotherPoint=geometry["C"])
        end_of_impulse_torque_circle_radius_entry = line_KN.getShortestDistanceToPoint(geometry["Z"])
        end_of_impulse_torque_circle_radius_exit = line_GC.getShortestDistanceToPoint(geometry["Z"])
        if loud:
            print("End of impulse torque circle radii: {} {}".format(end_of_impulse_torque_circle_radius_entry, end_of_impulse_torque_circle_radius_exit))
        if not self.skip_failed_checks:
            assert abs(end_of_impulse_torque_circle_radius_entry - end_of_impulse_torque_circle_radius_exit) < acceptableError, "End impulse torque circle radii not equal"

        #check 10b (there are two check 10s): EZ / HZ should match the designer-chosen end/start ratio, T. For Harrison compliant geometries, the ratio should be 3 / 2.
        HZ = start_of_impulse_torque_circle_radius_entry
        EZ = end_of_impulse_torque_circle_radius_entry
        T = EZ/HZ
        if loud:
            print("calculated T: {} design T: {}".format(T, self.T))
        if not self.skip_failed_checks:
            assert abs(T - self.T) < acceptableError, " EZ / HZ should match the designer-chosen end/start ratio, T. For Harrison compliant geometries, the ratio should be 3 / 2"

        #check 12: In the final, scaled geometry, 0.5 (HZ + EZ) = dimension M in Fig. 46 should match the designer-chosen mean torque arm, M*
        M = (EZ + HZ)/2
        if loud:
            print("Calculated M: {}, design mean torque arm length: {}".format(M, self.mean_torque_arm_length))
        if not self.skip_failed_checks:
            assert abs(M - self.mean_torque_arm_length) < acceptableError, "In the final, scaled geometry, 0.5 (HZ + EZ) = dimension M in Fig. 46 should match the designer-chosen mean torque arm, M*"

        #check 13: Escaping arcs NZP and FZG should both match the designer-chosen escaping arc, E*, with at least the designer-chosen degree of precision.
        #I think this is a given, because of how I iterate the choice of d/ax to select the escaping arc
        line_NZ = Line(geometry["N"], anotherPoint=geometry["Z"])
        line_ZP = Line(geometry["Z"], anotherPoint=geometry["P"])
        NZP = line_NZ.getAngleBetweenLines(line_ZP)

        line_FZ = Line(geometry["F"], anotherPoint=geometry["Z"])
        line_ZG = Line(geometry["Z"], anotherPoint=geometry["G"])
        FZG = line_FZ.getAngleBetweenLines(line_ZG)

        if loud:
            print("Escaping angles, NZP: {}deg, FZG:{}deg design:{}deg".format(radToDeg(NZP), radToDeg(FZG), radToDeg(self.escaping_arc)))
        if not self.skip_failed_checks:
            assert abs(FZG - NZP) < acceptableError, "Escaping angles aren't balanced"
            assert abs(FZG - self.escaping_arc) < degToRad(0.1), "Escaping arc isn't close to designed escaping arc"

    def getAnchor(self):
        #comply with expected interface
        return self.getFrame(leave_in_situ=False)

    def getFramePivotArmExtenders(self):
        '''
        if composer_z_distance_from_frame is larger than a few washers, print little arms to thread on to the screws to keep the composers and thus pallets in the right place on the z axis
        '''

        if self.composer_z_distance_from_frame > 0.8:
            return cq.Workplane("XY").circle(self.frame_wide/2).circle(self.screws.metric_thread/2).extrude(self.composer_z_distance_from_frame - WASHER_THICK_M3)

        return None


    def getFrame(self, leave_in_situ=False, thick=-1):
        '''
        Get the anchor-like part (fully 3D) which attaches to the arbour
        rotated and translated so taht (0,0) is in the centre of its arbour
        also rotated so that it lines up with the pendulum being vertical
        HACKY SIDE EFFECTS: sets self.entry_side_end, self.exit_side_end


        '''
        #optionally override the thickness - so we have more options on how to print it, including optionally in two parts
        if thick < 0:
            thick =self.frame_thick
        holeD = self.arbourD
        arm_wide = self.frame_wide
        arbour_circle_r = self.screws.metric_thread * 3.5/2

        #make taller so it's rigid on the arbour? Not sure how to do this iwthout it potentially clashing with pallet arms
        frame = cq.Workplane("XY").tag("base").moveTo(self.geometry["Z"][0], self.geometry["Z"][1]).circle(arm_wide/2).extrude(thick)

        #larger around the arbour - do this instead in ArboursForPlate, where we have a better idea of how the escapement is laid out
        # frame = frame.workplaneFromTagged("base").moveTo(self.geometry["Z"][0], self.geometry["Z"][1]).circle(arbour_circle_r).extrude(self.frame_thick)

        # entry  side
        line_ZP = Line(self.geometry["Z"], anotherPoint=self.geometry["P"])
        dir_ZP_perpendicular = line_ZP.get_perpendicular_direction()

        entry_composer_rest = self.getComposerRestScrewCentrePos(self.geometry["J"], self.geometry["P"])
        entry_composer_rest_distance = np.dot(np.subtract(entry_composer_rest, self.geometry["Z"]), line_ZP.dir)


        entry_side_end = np.add(self.geometry["Z"], np.multiply(line_ZP.dir, entry_composer_rest_distance))#self.geometry["P"]#
        #hacky side effect, setting these values to aid with cosmetics
        Z_dir = np.multiply(self.geometry["Z"], 1/np.linalg.norm(self.geometry["Z"]))
        self.entry_side_end = entry_side_end
        entry_side_end_relative_in_situ = np.subtract(entry_side_end, self.geometry["Z"])
        entry_side_end_relative_x = np.dot(np.cross(Z_dir, (0, 0, 1))[:2], entry_side_end_relative_in_situ)
        entry_side_end_relative_y = np.dot(Z_dir, entry_side_end_relative_in_situ)
        # for lining up cosmetics with the end
        self.entry_side_end_relative = (entry_side_end_relative_x, entry_side_end_relative_y)

        frame = frame.workplaneFromTagged("base").moveTo(self.geometry["Z"][0] + dir_ZP_perpendicular[0] * arm_wide * 0.5, self.geometry["Z"][1] + dir_ZP_perpendicular[1] * arm_wide * 0.5)
        frame = frame.lineTo(entry_side_end[0] + dir_ZP_perpendicular[0] * arm_wide * 0.5, entry_side_end[1] + dir_ZP_perpendicular[1] * arm_wide * 0.5)
        endArc = (entry_side_end[0] - dir_ZP_perpendicular[0] * arm_wide * 0.5, entry_side_end[1] - dir_ZP_perpendicular[1] * arm_wide * 0.5)
        frame = frame.radiusArc(endArc, -arm_wide * 0.50001).lineTo(self.geometry["Z"][0] - dir_ZP_perpendicular[0] * arm_wide * 0.5, self.geometry["Z"][1] - dir_ZP_perpendicular[1] * arm_wide * 0.5)
        frame = frame.close().extrude(thick)

        line_entry_end_to_entry_composer_rest = Line(entry_side_end, anotherPoint=entry_composer_rest)
        holder_r = self.screws.metric_thread*1.5
        arm_to_rest_distance = distanceBetweenTwoPoints(entry_composer_rest, entry_side_end)
        holder_circle_distance = arm_to_rest_distance + (holder_r - self.screws.metric_thread/2)
        holder_circle_centre = np.add(entry_side_end, np.multiply(line_entry_end_to_entry_composer_rest.dir, holder_circle_distance))
        frame = frame.cut(cq.Workplane("XY").moveTo(holder_circle_centre[0], holder_circle_centre[1]).circle(holder_r).extrude(thick))

        # cut hole for entry pallet & composer pivot
        if thick < self.frame_screw_fixing_min_thick:
            frame = frame.union(cq.Workplane("XY").moveTo(self.geometry["P"][0], self.geometry["P"][1]).circle(arm_wide/2).extrude(self.frame_screw_fixing_min_thick).translate((0,0,-self.frame_screw_fixing_min_thick)))
        frame = frame.faces(">Z").workplane().moveTo(self.geometry["P"][0], self.geometry["P"][1]).circle(self.screws.metric_thread / 2).cutThruAll()

        #exit side
        line_ZG = Line(self.geometry["Z"], anotherPoint=self.geometry["G"])
        dir_ZG_perpendicular = line_ZG.get_perpendicular_direction()

        #hacky side effect
        self.exit_side_end = self.geometry["G"]
        exit_side_end_relative_in_situ = np.subtract(self.exit_side_end, self.geometry["Z"])
        exit_side_end_relative_x = np.dot(np.cross(Z_dir,(0,0,1))[:2], exit_side_end_relative_in_situ)
        exit_side_end_relative_y = np.dot(Z_dir, exit_side_end_relative_in_situ)
        #for lining up cosmetics with the end
        self.exit_side_end_relative = (exit_side_end_relative_x, exit_side_end_relative_y)
        frame = frame.workplaneFromTagged("base").moveTo(self.geometry["Z"][0] + dir_ZG_perpendicular[0]*arm_wide*0.5, self.geometry["Z"][1] + dir_ZG_perpendicular[1]*arm_wide*0.5)
        frame = frame.lineTo(self.geometry["G"][0] + dir_ZG_perpendicular[0]*arm_wide*0.5, self.geometry["G"][1] + dir_ZG_perpendicular[1]*arm_wide*0.5)
        endArc = (self.geometry["G"][0] - dir_ZG_perpendicular[0]*arm_wide*0.5, self.geometry["G"][1] - dir_ZG_perpendicular[1]*arm_wide*0.5)
        frame = frame.radiusArc(endArc, -arm_wide*0.50001).lineTo(self.geometry["Z"][0] - dir_ZG_perpendicular[0]*arm_wide*0.5, self.geometry["Z"][1] - dir_ZG_perpendicular[1]*arm_wide*0.5)
        frame = frame.close().extrude(thick)

        #exit composer rest
        exit_composer_rest = self.getComposerRestScrewCentrePos(self.geometry["Cstar"], self.geometry["G"])
        #negatives here because line ZG goes in the opposite way. we could let them cancel out, but this is clearer in terms of what we want to happen
        exit_composer_rest_along_arm = -np.dot(np.subtract(exit_composer_rest, self.geometry["G"]), line_ZG.dir)
        exit_composer_rest_base = np.add(self.geometry["G"], np.multiply(line_ZG.dir, -exit_composer_rest_along_arm))

        exit_composer_rest_line = Line(exit_composer_rest_base, anotherPoint=exit_composer_rest)
        exit_composer_rest_base_left = np.add(exit_composer_rest_base, np.multiply(line_ZG.dir, -arm_wide/2))
        exit_composer_rest_base_right = np.add(exit_composer_rest_base, np.multiply(line_ZG.dir, arm_wide / 2))
        exit_composer_rest_top_left = np.add(exit_composer_rest, np.multiply(line_ZG.dir, -arm_wide / 2))
        exit_composer_rest_top_right = np.add(exit_composer_rest, np.multiply(line_ZG.dir, arm_wide / 2))
        # exit_composer

        #radiusArc(npToSet(exit_composer_rest_top_right), arm_wide/2)
        #lineTo(exit_composer_rest_top_right[0], exit_composer_rest_top_right[1])
        frame = frame.workplaneFromTagged("base").moveTo(exit_composer_rest_base_left[0], exit_composer_rest_base_left[1]).lineTo(exit_composer_rest_top_left[0], exit_composer_rest_top_left[1]).\
            sagittaArc(npToSet(exit_composer_rest_top_right),-self.screws.metric_thread/2).lineTo(exit_composer_rest_base_right[0], exit_composer_rest_base_right[1]).close().extrude(thick)

        # cut hole for exit pallet pivot
        if thick < self.frame_screw_fixing_min_thick:
            #make it chunkier first
            frame = frame.union(cq.Workplane("XY").moveTo(self.geometry["G"][0], self.geometry["G"][1]).circle(arm_wide/2).extrude(self.frame_screw_fixing_min_thick).translate((0,0,-self.frame_screw_fixing_min_thick)))
        frame = frame.faces(">Z").workplane().moveTo(self.geometry["G"][0], self.geometry["G"][1]).circle(self.screws.metric_thread / 2).cutThruAll()
            # frame = frame.add(star)



        #cut hole for arbour
        frame = frame.cut(cq.Workplane("XY").moveTo(self.geometry["Z"][0], self.geometry["Z"][1]).circle(holeD/2).extrude(thick*2))

        if not leave_in_situ:
            #rotate and translate so it's upright with 0,0 where the arbour should be
            frame = self.rotateToUpright(frame).translate((0,-np.linalg.norm(self.geometry["Z"]),0))

            #rotate so it's aligned with a vertical pendulum
            frame = frame.rotate((0, 0, 0), (0, 0, 1), radToDeg(-self.escaping_arc / 2))
            #
            # if self.xmas:
            #     #this is a massive bodge doing it here, if I'm giong to make a habit of themed clocks I should create a more generic way of customising parts
            #     star_thick=3
            #     star_size = 75
            #     star = get_star(star_thick=star_thick, star_size=star_size)
            #     start_inset_thick = LAYER_THICK*2
            #     star_inset = get_star(star_thick=start_inset_thick, star_size=star_size*0.7)
            #
            #
            #     # star = self.rotateToUpright(star.translate(self.geometry["Z"]))
            #     #arbour_circle_r isn't actually used anymore, so go for 10mm, which is the size of the inner d of the bearing used, so the tip of the bottom of the star lines up with the bottom of the
            #     #circle around the arbour
            #     star = star.translate((0, star_size/2 - 10/2, self.frame_thick - star_thick))
            #     star_inset = star_inset.translate((0, star_size/2 - 10/2, self.frame_thick - start_inset_thick))
            #     #the geometry is in the position of the start of entry pallet engaging, rotate so it's in the centre of the escaping arc
            #     # star = star.rotate((0, 0, 0), (0, 0, 1), radToDeg(self.escaping_arc / 2))
            #     #.translate(self.geometry["Z"])
            #     frame = frame.add(star)
            #
            #     frame = frame.cut(star_inset)
            #     #bodgily save this
            #     self.star_inset=star_inset
            #
            #     # recut hole for arbour
            #     frame = frame.cut(cq.Workplane("XY").circle(holeD / 2).extrude(self.frame_thick * 2))



        return frame

    def rotateToUpright(self, part, in_situ=True):
        '''
        take a part made from the geometry and realign so the frame arbour is at the top

        if in-situ assume 0,0 is centre of the escaep wheel
        '''
        # rotate so that Z is at the top
        line_OZ = Line(self.geometry["O"], anotherPoint=self.geometry["Z"])
        part = part.rotate((0, 0, 0), (0, 0, 1), radToDeg((math.pi / 2 - line_OZ.getAngle())))

        return part

    def getPalletArmBendStart(self, nib_pos, pivot_pos):
        '''
        Get the position of where the arm bends. Assume arm is a straight line of width self.pallet_arm_wide from pivot_pos to
        arm_bend_start (returned)
        '''
        # angle between line of arm and the nib
        nib_offset_angle = self.nib_offset_angle

        line_pivot_to_nib = Line(pivot_pos, anotherPoint=nib_pos)
        distance_to_nib = distanceBetweenTwoPoints(nib_pos, pivot_pos)
        # distance from pivot that the bend towards the nib starts
        distance_nib_bend_start = distance_to_nib * 0.8


        # angle that is along the tangent of the wheel
        nib_tangent_angle = line_pivot_to_nib.getAngle()
        arm_angle = line_pivot_to_nib.getAngle() - nib_offset_angle

        line_along_arm = Line(pivot_pos, angle=arm_angle)

        arm_bend_start = np.add(pivot_pos, np.multiply(line_along_arm.dir, distance_nib_bend_start))
        return arm_bend_start

    def getComposerRestScrewCentrePos(self, nib_pos, pivot_pos):
        '''
        In the top left corner of the composer is a screw to add weight. this screw will extend out the back of the composer so it will come into contact with the frame arm
        This gets the position of the centre of that screw when the composer should be resting on that arm

        the screw centre is :
        (-composer_length, self.composer_height)
        '''
        pallet_arm_bend_start = self.getPalletArmBendStart(nib_pos=nib_pos, pivot_pos=pivot_pos)

        line_along_arm = Line(pivot_pos, anotherPoint=pallet_arm_bend_start)

        composer_length = distanceBetweenTwoPoints(pivot_pos, pallet_arm_bend_start)

        arm_angle = line_along_arm.getAngle()

        rest_pos_base = np.add(pivot_pos, np.multiply(line_along_arm.dir, composer_length))
        rest_screw_pos = np.add(rest_pos_base, polar(arm_angle - math.pi/2, self.composer_height))

        return rest_screw_pos

    def getComposer(self, nib_pos, pivot_pos, forPrinting=True, extra_length_fudge=0):
        '''
        like pallet arm, assumes wheel rotates clockwise and both arms have their nibs 'left' of the pivot point
        '''


        pallet_arm_bend_start = self.getPalletArmBendStart(nib_pos=nib_pos, pivot_pos=pivot_pos)
        line_along_arm = Line(pivot_pos, anotherPoint=pallet_arm_bend_start)

        #make a shape which has the pivot_pos at (0,0) and assumes pallet arm is horizontal facing left, then rotate and translate into position
        composer_length = distanceBetweenTwoPoints(pivot_pos, pallet_arm_bend_start)

        screw_position =  (-composer_length, self.composer_height)
        around_screw_r = self.screws.metric_thread / 2 + self.composer_thick
        top_left_corner = (screw_position[0] - around_screw_r, screw_position[1] + around_screw_r)


        #bottom chunky arm which attaches to the pivot
        composer_arm = cq.Workplane("XY").tag("base").moveTo(-self.composer_arm_wide/2,0).radiusArc((self.composer_arm_wide/2, 0), -self.composer_arm_wide/2)\
            .line(0, top_left_corner[1]).line(-self.composer_arm_wide,0).close().extrude(self.composer_thick)

        #top arm
        composer = composer_arm.union(composer_arm.translate((0,0,self.pallet_thick + self.composer_thick + self.composer_pivot_space)))

        #rest of composer
        composer_total_thick = self.pallet_thick + self.composer_thick*2 + self.composer_pivot_space
        #arm along the top
        composer = composer.workplaneFromTagged("base").moveTo(self.composer_arm_wide/2, top_left_corner[1]).lineTo(screw_position[0], screw_position[1] + around_screw_r).\
            line(0, - self.composer_thick).lineTo(self.composer_arm_wide/2, top_left_corner[1] - self.composer_thick).close().extrude(composer_total_thick)
        #arm that holds the pallet in place
        composer = composer.workplaneFromTagged("base").moveTo(screw_position[0] - self.composer_thick/2, screw_position[1]).lineTo(screw_position[0] - self.composer_thick/2, self.pallet_arm_wide/2 - extra_length_fudge).\
            line(self.composer_thick, 0).lineTo(screw_position[0] + self.composer_thick/2, screw_position[1]).close().extrude(composer_total_thick)

        #hole to rotate around pivot
        composer = composer.cut(cq.Workplane("XY").circle(self.screws.metric_thread/2 + self.loose_on_pivot/2).extrude(1000))
        #hole to hold screw for weight
        composer = composer.union(cq.Workplane("XY").moveTo(screw_position[0], screw_position[1]).circle(around_screw_r).extrude(self.composer_thick*2 + self.pallet_thick + self.composer_pivot_space))
        composer = composer.cut(cq.Workplane("XY").moveTo(screw_position[0], screw_position[1]).circle(self.screws.metric_thread/2).extrude(1000))

        if not forPrinting:
            #rotate and translate into place
            composer = composer.rotate((0,0,0), (0,0,1), radToDeg(line_along_arm.getAngle()) - 180)
            composer = composer.translate(pivot_pos)
        else:
            #put flat on its back
            composer = composer.rotate((0,0,0),(1,0,0),-90)

        return composer

    def getPalletArm(self, nib_pos, pivot_pos, forPrinting=False):
        '''
        Assumes wheel rotates clockwise and both arms have their nibs left of the pivot point
        '''
        arm = cq.Workplane("XY").tag("base").moveTo(pivot_pos[0], pivot_pos[1]).circle(self.screws.metric_thread).extrude(self.pallet_thick)

        line_pivot_to_nib = Line(pivot_pos, anotherPoint=nib_pos)
        distance_to_nib = distanceBetweenTwoPoints(nib_pos, pivot_pos)
        #I want this to be longer so the counterweight works better, but any larger than this and the entry arm will clash with any extra rod that stick through the frame
        distance_to_counterweight = distance_to_nib * 0.4

        # #angle that is along the tangent of the wheel
        nib_tangent_angle = line_pivot_to_nib.getAngle()
        # 0.6 works when there's no wonkyness in the frame and wheel
        #0.8 looks awfully close on the preview, but I think when printed should be much better
        #basically want these to be as big as possible to help make up for wonkyness from having the escapement out the front
        nib_end_r = self.pallet_arm_wide*0.75#0.6




        arm_bend_start = self.getPalletArmBendStart(nib_pos=nib_pos, pivot_pos=pivot_pos)

        nib_bend_r = (distance_to_nib - distanceBetweenTwoPoints(pivot_pos, arm_bend_start))

        line_along_arm = Line(pivot_pos, anotherPoint=arm_bend_start)
        arm_angle = line_along_arm.getAngle()

        nib_base = np.add(nib_pos, polar(nib_tangent_angle + math.pi / 2, nib_end_r))
        nib_top = np.add(nib_pos, polar(nib_tangent_angle - math.pi / 6, nib_end_r))
        nib_before_base = np.add(nib_pos, polar(arm_angle - math.pi, self.pallet_arm_wide/2))

        bottom_of_pivot = np.add(pivot_pos, polar(arm_angle + math.pi/2, self.pallet_arm_wide/2))
        top_of_pivot = np.add(pivot_pos, polar(arm_angle - math.pi / 2, self.pallet_arm_wide/2))

        #from pivot to the nib
        arm = arm.workplaneFromTagged("base").moveTo(bottom_of_pivot[0], bottom_of_pivot[1])

        bottom_of_bend_start = np.add(arm_bend_start, polar(arm_angle + math.pi/2, self.pallet_arm_wide/2))
        top_of_bend_start = np.add(arm_bend_start, polar(arm_angle - math.pi / 2, self.pallet_arm_wide/2))

        arm = arm.lineTo(bottom_of_bend_start[0], bottom_of_bend_start[1])
        arm = arm.radiusArc((nib_before_base[0], nib_before_base[1]), -( nib_bend_r - self.pallet_arm_wide/2 ))
        arm = arm.tangentArcPoint((nib_base[0], nib_base[1]), relative=False)
        arm = arm.lineTo(nib_pos[0], nib_pos[1])
        arm = arm.lineTo(nib_top[0], nib_top[1])

        arm = arm.radiusArc((top_of_bend_start[0], top_of_bend_start[1]), nib_bend_r + nib_end_r)
        arm = arm.lineTo(top_of_pivot[0], top_of_pivot[1])

        arm = arm.close().extrude(self.pallet_thick)

        #from pivot to the counterweight
        counteweight_pos = np.add(pivot_pos, np.multiply(line_along_arm.dir, -distance_to_counterweight))
        bottom_of_counterweight = np.add(counteweight_pos, polar(arm_angle + math.pi/2, self.pallet_arm_wide/2))
        top_of_counterweight = np.add(counteweight_pos, polar(arm_angle - math.pi / 2, self.pallet_arm_wide/2))
        arm = arm.workplaneFromTagged("base").moveTo(bottom_of_pivot[0], bottom_of_pivot[1]).lineTo(bottom_of_counterweight[0], bottom_of_counterweight[1])
        arm = arm.lineTo(top_of_counterweight[0], top_of_counterweight[1]).lineTo(top_of_pivot[0], top_of_pivot[1])
        arm = arm.close().extrude(self.pallet_thick)

        #counterweight screw hole holder
        arm = arm.moveTo(counteweight_pos[0], counteweight_pos[1]).circle(self.screws.metric_thread).extrude(self.pallet_thick)

        #
        # # pallet_angle = line_pivot_to_nib.getAngle() - nib_angle
        #

        #
        #
        # #if the pallet arm continued into a straight line, this would be perpendicularily above the nib
        # virtual_corner = polar(line_pivot_to_nib.getAngle() - nib_angle, distance_to_nib)
        #
        # bend_r = distanceBetweenTwoPoints(virtual_corner, nib_pos)
        #
        # distance_bend_start_from_pivot = math.cos(nib_angle) * distance_to_nib - bend_r
        #
        # line_pivot_to_virtual_corner = Line(pivot_pos, anotherPoint=virtual_corner)
        #
        # bend_start = (pivot_pos[0] + line_pivot_to_virtual_corner.dir[0]*distance_bend_start_from_pivot, pivot_pos[1] + line_pivot_to_virtual_corner.dir[1]*distance_bend_start_from_pivot)

        # line_along_arm = Line(pivot_pos, angle=pallet_angle)
        #
        # start_of_bend = (pivot_pos[0] + line_along_arm.dir[0]*bend_start_from_pivot, pivot_pos[1] + line_along_arm.dir[1]*bend_start_from_pivot)
        #
        # start_of_bend_to_nib = Line(start_of_bend, anotherPoint=nib_pos)



        arm = arm.cut(cq.Workplane("XY").moveTo(pivot_pos[0], pivot_pos[1]).circle(self.screws.metric_thread / 2 + self.loose_on_pivot/2).extrude(self.pallet_thick))
        arm = arm.cut(cq.Workplane("XY").moveTo(counteweight_pos[0], counteweight_pos[1]).circle(self.screws.metric_thread / 2).extrude(self.pallet_thick))

        return arm

    def getExitPalletArm(self, forPrinting=True):
        return self.getPalletArm(self.geometry["Cstar"], self.geometry["G"], forPrinting=forPrinting)

    def getExitComposer(self, forPrinting=True):
        return self.getComposer(self.geometry["Cstar"], self.geometry["G"], forPrinting=forPrinting, extra_length_fudge=self.exit_composer_extra_fudge)

    def getEntryPalletArm(self, forPrinting=True):
        return self.getPalletArm(self.geometry["J"], self.geometry["P"], forPrinting=forPrinting)

    def getEntryComposer(self, forPrinting=True):
        return self.getComposer(self.geometry["J"], self.geometry["P"], forPrinting=forPrinting, extra_length_fudge=self.entry_composer_extra_fudge)


    def getWheelThick(self):
        return self.wheel_thick

    def getAnchorThick(self):
        '''
        Just the thickness of the bit which is on the arbour (in case I ever put the grasshopper between the plates)
        '''
        return self.frame_thick# + self.composer_z_distance_from_frame + self.composer_thick + self.pallet_thick + self.composer_thick + self.composer_pivot_space

    def getWheel(self, style=None, arbour_or_pivot_r=-1, holeD=3):

        if holeD < 0:
            holeD = self.arbourD

        #only used for the gear style cutter
        if arbour_or_pivot_r < 0:
            arbour_or_pivot_r = holeD# / 2

        #angles from O
        tooth_base_angle=(math.pi*2/self.teeth)*0.3
        tooth_tip_angle=(math.pi*2/self.teeth)/2
        tooth_tip_width=1.2
        tooth_tip_width_angle = tooth_tip_width/self.diameter
        tooth_height = self.radius*0.1
        inner_r = self.radius - tooth_height
        tooth_angle = math.pi * 2 / self.teeth

        wheel = cq.Workplane("XY")

        start = polar(0, inner_r)
        wheel = wheel.moveTo(start[0], start[1])


        for tooth in range(self.teeth):
            angle = -tooth*tooth_angle

            start = polar(angle, inner_r)
            tip_start = polar(angle - tooth_tip_angle + tooth_tip_width_angle/2, self.radius)
            tip_end = polar(angle - tooth_tip_angle - tooth_tip_width_angle/2, self.radius)
            base = polar(angle - tooth_base_angle, inner_r)
            end = polar(angle - tooth_angle, inner_r)

            wheel = wheel.lineTo(tip_start[0], tip_start[1])
            wheel = wheel.radiusArc(tip_end, -self.radius)
            wheel = wheel.lineTo(base[0], base[1])
            wheel = wheel.radiusArc(end, -inner_r)

        wheel = wheel.close().extrude(self.wheel_thick)

        wheel = Gear.cutStyle(wheel, outerRadius=inner_r, innerRadius=arbour_or_pivot_r, style=style)

        wheel = wheel.cut(cq.Workplane("XY").circle(holeD / 2).extrude(self.wheel_thick))

        return wheel

    def getAssembled(self, style=None, leave_out_wheel_and_frame=False, centre_on_anchor=False, mid_pendulum_swing=False):
        grasshopper = cq.Workplane("XY")
        composer_z = self.frame_thick + self.composer_z_distance_from_frame
        pallet_arm_z = composer_z + self.composer_thick + self.composer_pivot_space / 2

        def rotate_anchor(anchor_part):
            # centre = (0, 0)
            # if not centre_on_anchor:
            centre = self.geometry["Z"]
            anchor_part = anchor_part.rotate((centre[0], centre[1], 0), (centre[0], centre[1], 1), radToDeg(-self.escaping_arc / 2))
            return anchor_part

        if not leave_out_wheel_and_frame:
            grasshopper = grasshopper.add(self.getWheel(style=style).translate((0, 0, pallet_arm_z + (self.pallet_thick - self.wheel_thick) / 2)))
            grasshopper = grasshopper.add(rotate_anchor(self.rotateToUpright(self.getFrame(leave_in_situ=True))))

        pivot_extenders = self.getFramePivotArmExtenders()
        if pivot_extenders is not None:
            grasshopper = grasshopper.add(self.rotateToUpright(rotate_anchor(pivot_extenders.translate((self.geometry["G"][0], self.geometry["G"][1], self.frame_thick)))))
            grasshopper = grasshopper.add(self.rotateToUpright(rotate_anchor(pivot_extenders.translate((self.geometry["P"][0], self.geometry["P"][1], self.frame_thick)))))

        grasshopper = grasshopper.add(self.rotateToUpright(rotate_anchor((self.getExitPalletArm(forPrinting=False)).translate((0, 0, pallet_arm_z)))))
        grasshopper = grasshopper.add(self.rotateToUpright(rotate_anchor((self.getEntryPalletArm(forPrinting=False)).translate((0, 0, pallet_arm_z)))))
        grasshopper = grasshopper.add(self.rotateToUpright(rotate_anchor((self.getEntryComposer(forPrinting=False)).translate((0, 0, composer_z)))))
        grasshopper = grasshopper.add(self.rotateToUpright(rotate_anchor((self.getExitComposer(forPrinting=False)).translate((0, 0, composer_z)))))

        if centre_on_anchor:
            grasshopper = grasshopper.translate((0,-np.linalg.norm(self.geometry["Z"]),0))


        return grasshopper

    def getComposerZThick(self):
        return self.pallet_thick + self.composer_pivot_space + self.composer_thick*2

    def getWheelBaseToAnchorBaseZ(self):
        '''
        REturn Z change between the bottom of the wheel and the bottom of the anchor
        '''
        return -(self.getComposerZThick()/2 + self.composer_z_distance_from_frame + self.frame_thick - self.wheel_thick/2)

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_grasshopper_wheel.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getWheel(), out)

        out = os.path.join(path, "{}_grasshopper_frame.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getFrame(), out)

        out = os.path.join(path, "{}_grasshopper_entry_pallet_arm.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getEntryPalletArm(), out)

        out = os.path.join(path, "{}_grasshopper_exit_pallet_arm.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getExitPalletArm(), out)

        out = os.path.join(path, "{}_grasshopper_entry_composer.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getEntryComposer(), out)

        out = os.path.join(path, "{}_grasshopper_exit_composer.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getExitComposer(), out)

        pivot_extenders = self.getFramePivotArmExtenders()
        if pivot_extenders is not None:
            out = os.path.join(path, "{}_grasshopper_pivot_extender.stl".format(name))
            print("Outputting ", out)
            exporters.export(pivot_extenders, out)

class Pendulum:
    '''
    Class to generate the anchor&crutch arbour and pendulum parts
    NOTE - the anchor is now usually accessed via being a special case of Arbour

    plan: add a square bit to the anchor (probably in the Arbour class, part of the arbour extensions)
    and make two special longish spanners in order to make setting the beat much easier (thinking ahead to fixing clock to the wall with two screws, will need ability to delicately adjust beat)
    '''
    def __init__(self, escapement, length, crutchLength=50, anchorThick=10, anchorAngle=-math.pi/2, anchorHoleD=2, crutchBoltD=3, suspensionScrewD=3, threadedRodM=3, nutMetricSize=0, handAvoiderInnerD=100, bobD=100, bobThick=15, useNylocForAnchor=True, handAvoiderHeight=-1):
        self.escapement = escapement
        self.crutchLength = crutchLength
        self.anchorAngle = anchorAngle
        #NOTE - deprecated, trying to switch over to making the anchor another arbour
        self.anchorThick=anchorThick
        #if this is teh default (-1), then the hand avoider is round, if this is provided then it's a round ended rectangle
        self.handAvoiderHeight=handAvoiderHeight

        if self.handAvoiderHeight < 0:
            self.handAvoiderHeight = handAvoiderInnerD

        #nominal length of the pendulum
        self.length = length
        # self.crutchWidth = 9

        #if true, we're using a nyloc nut to fix the anchor to the rod, if false we're not worried about fixing it, or we're using glue
        self.useNylocForAnchor=useNylocForAnchor

        #space for a nut to hold the anchor to the rod
        self.nutMetricSize=nutMetricSize

        # self.anchor = self.escapement.getAnchorArbour(holeD=anchorHoleD, anchorThick=anchorThick, arbourLength=0, crutchLength=crutchLength, crutchBoltD=crutchBoltD, pendulumThick=threadedRodM, nutMetricSize=nutMetricSize if useNylocForAnchor else 0)

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



    def getPendulumForRod(self, holeD=3, forPrinting=True):
        '''
        Will allow a threaded rod for the pendulum to be attached to threaded rod for the arbour
        '''

        pendulum = cq.Workplane("XY")

        width = 12#holeD*4
        height = 22#26#holeD*6

        #I've noticed that the pendulum doesn't always hang vertical, so give more room for the rod than the minimum so it can hang forwards relative to the holder
        extraRodSpace=1

        #(0,0,0) is the rod from the anchor, the rod is along the z axis

        #hole that the pendulum (threaded rod with nyloc nut on the end) rests in
        holeStartY=-getNutContainingDiameter(self.threadedRodM)*0.5-0.4#-5#-8#-height*0.2
        holeHeight = getNutHeight(self.threadedRodM,nyloc=True) + getNutHeight(self.threadedRodM) + 1

        nutD = getNutContainingDiameter(holeD)

        wall_thick = (width - (nutD + 1))/2

        pendulum = pendulum.moveTo(-width/2,0).radiusArc((width/2,0), width/2).line(0,-height).radiusArc((-width/2,-height), width/2).close().extrude(self.pendulumTopThick)

        pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()

        #nut to hold to anchor rod
        nutThick = getNutHeight(holeD, nyloc=True)
        nutSpace = cq.Workplane("XY").polygon(6,nutD).extrude(nutThick).translate((0,0,self.pendulumTopThick-nutThick))
        pendulum = pendulum.cut(nutSpace)


        # pendulum = pendulum.faces(">Z").moveTo(0,-height*3/4).rect(width-wall_thick*2,height/2).cutThruAll()
        space = cq.Workplane("XY").moveTo(0,holeStartY-holeHeight/2).rect(width-wall_thick*2,holeHeight).extrude(self.pendulumTopThick).translate((0,0,LAYER_THICK*3))
        pendulum = pendulum.cut(space)

        extraSpaceForRod = 0.1
        extraSpaceForNut = 0.2
        #
        rod = cq.Workplane("XZ").tag("base").moveTo(0, self.pendulumTopThick / 2 - extraRodSpace).circle(self.threadedRodM/2 + extraSpaceForRod/2).extrude(100)
        # add slot for rod to come in and out
        rod = rod.workplaneFromTagged("base").moveTo(0,self.pendulumTopThick - extraRodSpace).rect(self.threadedRodM + extraSpaceForRod, self.pendulumTopThick).extrude(100)

        rod = rod.translate((0,holeStartY,0))




        pendulum = pendulum.cut(rod)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(6, nutD+extraSpaceForNut).extrude(nutThick).translate((0,holeStartY-holeHeight,0))
        pendulum = pendulum.cut(nutSpace2)


        if not forPrinting:
            pendulum = pendulum.mirror().translate((0, 0, self.pendulumTopThick))

        return pendulum

    def handAvoiderIsCircle(self):
        return self.handAvoiderHeight == self.handAvoiderInnerD

    def getHandAvoider(self):
        '''
        Get a circular part which attaches inline with pendulum rod, so it can go over the hands (for a front-pendulum)
        '''
        extraR=5
        if self.handAvoiderIsCircle():
            avoider = cq.Workplane("XY").circle(self.handAvoiderInnerD/2).circle(self.handAvoiderInnerD/2 + extraR).extrude(self.handAvoiderThick)
        else:
            avoider = cq.Workplane("XY").moveTo(-self.handAvoiderInnerD/2-extraR,0).line(0,self.handAvoiderHeight/2-self.handAvoiderInnerD/2).\
                radiusArc((self.handAvoiderInnerD/2+extraR,self.handAvoiderHeight/2-self.handAvoiderInnerD/2), self.handAvoiderInnerD/2 + extraR).line(0,-self.handAvoiderHeight/2+self.handAvoiderInnerD/2).mirrorX().extrude(self.handAvoiderThick)

            avoider = avoider.cut(cq.Workplane("XY").moveTo(-self.handAvoiderInnerD / 2, 0).line(0, self.handAvoiderHeight / 2-self.handAvoiderInnerD/2). \
                radiusArc((self.handAvoiderInnerD / 2 , self.handAvoiderHeight / 2-self.handAvoiderInnerD/2), self.handAvoiderInnerD / 2).line(0, -self.handAvoiderHeight / 2+self.handAvoiderInnerD/2).mirrorX().extrude(self.handAvoiderThick))



        nutD = getNutContainingDiameter(self.threadedRodM)
        nutThick = METRIC_NUT_DEPTH_MULT * self.threadedRodM

        nutSpace = cq.Workplane("XZ").moveTo(0, self.handAvoiderThick/2).polygon(6, nutD).extrude(nutThick).translate((0, -self.handAvoiderHeight/2+0.5, 0))
        avoider = avoider.cut(nutSpace)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.handAvoiderThick / 2).polygon(6, nutD).extrude(nutThick).translate((0, self.handAvoiderHeight / 2 +nutThick - 0.5, 0))
        avoider = avoider.cut(nutSpace2)

        # avoider = avoider.faces(">Y").workplane().moveTo(0,self.handAvoiderThick/2).circle(self.threadedRodM/2).cutThruAll()
        avoider = avoider.cut(cq.Workplane("XZ").circle(self.threadedRodM/2).extrude(self.handAvoiderHeight*4).translate((0,self.handAvoiderHeight,self.handAvoiderThick/2)))

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
            notHole = notHole.union(cq.Workplane("XY").rect(self.threadedRodM+extraR*2 + self.wallThick*2, self.bobR*2).extrude(self.bobThick/2 - self.wallThick).translate((0,0,self.wallThick)))

            for pos in self.bobLidNutPositions:
                notHole = notHole.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(self.nutMetricSize*1.5).circle(self.nutMetricSize/2).extrude(self.bobThick-self.wallThick))

            weightHole = weightHole.cut(notHole)

            lid = self.getBobLid(True)

            weightHole = weightHole.union(lid.translate((0,0,self.bobThick-self.wallThick)))

            bob = bob.cut(weightHole)

        #add a little S <--> F text
        textSize = self.gapHeight
        bob = bob.union(cq.Workplane("XY").moveTo(0, 0).text("S", textSize, LAYER_THICK*2, cut=False, halign='center', valign='center', kind="bold").translate((-self.gapWidth/2 - textSize*0.75, 0, self.bobThick)))
        bob = bob.union(cq.Workplane("XY").moveTo(0, 0).text("F", textSize, LAYER_THICK * 2, cut=False, halign='center', valign='center', kind="bold").translate((self.gapWidth/2 + textSize*0.75, 0, self.bobThick)))

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
        # out = os.path.join(path, "{}_anchor.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(self.anchor, out)

        #these haven't been used since the very first prototype clock!
        # out = os.path.join(path, "{}_suspension.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(self.getSuspension(), out)
        #
        # out = os.path.join(path, "{}_pendulum_for_knife_edge.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(self.getPendulumForKnifeEdge(), out)#,tolerance=0.01)

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
