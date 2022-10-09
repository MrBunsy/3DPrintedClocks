import os

from .types import *

from .utility import *
from .gearing import *
import cadquery as cq

from cadquery import exporters

class AnchorEscapement:
    def __init__(self, teeth=30, diameter=100, anchorTeeth=None, type=EscapementType.DEADBEAT, lift=4, drop=2, run=10, lock=2, clockwiseFromPinionSide=True, escapeWheelClockwise=True, toothHeightFraction=0.2, toothTipAngle=9, toothBaseAngle=5.4):
        '''
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

        #note, these are bodgingly set in GoingTrain
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

        '''

        if self.type == EscapementType.RECOIL:
            #just in case I ever want this again?
            return self.getAnchor2DOld()

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

        #just temp - need proper arm and centre
        anchor = anchor.lineTo(anchorCentreTop[0], anchorCentreTop[1]).lineTo(outerRightPoint[0], outerRightPoint[1])

        if self.type == EscapementType.DEADBEAT:
            anchor = anchor.radiusArc(exitPalletEndPos, exitPalletEndR)

        anchor = anchor.lineTo(exitPalletStartPos[0], exitPalletStartPos[1])

        if self.type == EscapementType.DEADBEAT:
            anchor = anchor.radiusArc(innerRightPoint, -exitPalletStartR)

        anchor = anchor.lineTo(anchorCentreBottom[0], anchorCentreBottom[1]).lineTo(innerLeftPoint[0], innerLeftPoint[1])

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

        anchor = anchor.add(cq.Workplane("XY").moveTo(0, self.anchor_centre_distance).circle(holeD*4/2).extrude(thick))



        anchor = anchor.extrude(thick)

        if not clockwise:
            anchor = anchor.mirror("YZ", (0,0,0))

        anchor = anchor.faces(">Z").workplane().moveTo(0,self.anchor_centre_distance).circle(holeD/2).cutThruAll()

        return anchor

    def getAnchorMaxR(self):
        '''
        To allow enough space in the clock plates and anywhere else, HACK HACK HACK for now
        '''
        #holeD * 2, which for now is always going to be six. To fix in future.
        return 6

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

        # rimThick = holeD*1.5
        # #have toyed with making the escape wheel more solid to see if it improves the tick sound. not convinced it does
        # rimRadius = self.innerRadius - holeD*0.5# - rimThick
        #
        # armThick = rimThick
        # if style == "HAC":
        #     gear = Gear.cutHACStyle(gear, armThick, rimRadius)
        # elif style == "circles":
        #     gear = Gear.cutCirclesStyle(gear, outerRadius=rimRadius, innerRadius=innerRadiusForStyle)
        gear = Gear.cutStyle(gear,outerRadius=self.innerRadius - holeD*0.5,innerRadius=innerRadiusForStyle, style=style)
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

class GrasshopperEscapement:

    def __init__(self, diameter=152.4, pendulum_length=getPendulumLength(1), teeth=120, tooth_span=17.5, entry_angle_deg=90, T=3/2, mean_torque_arm_length=10, escaping_arc_deg=9.75, d=-1, ax_deg=-1):
        '''
        From Computer Aided Design of Harrison Twin Pivot and Twin Balance Grasshopper Escapement Geometries by David Heskin

        entry angle is "The angle clockwise from the entry pallet arm line of action at the start of entry impulse to the escape wheel radial at the start of entry impulse"
        and called 'an' in the doc

        'ax' is the exit angle, which will just adjusted to control arc

        T is the target end/start ratio (not quite sure what this means yet - I think ti's about the torque arm lengths

        mean torque arm. The "torque arms" are the length of an arm where the torque is applied to the pendulum by the entry pallet start/end and exit pallet start/end

        All angles are radians unless specifically called `_deg`

        If an escaping arc is provided this will calculate the best 'd' and 'ax' to provide that escaping arc. This is slow, so you can provide pre-calculated d and ax instead

        '''

        #escape wheel pitch circle (end of teeth)
        #"For example, the 120 tooth escape wheel, at almost 150 mm in diameter"  - Perfecting the Harrison Twin Pivot Grasshopper Escapement
        #Ken kuo's escapement animation on youtube has a diameter of 200mm
        #different David Heskin document says it was 6" originally - so 152.4mm
        self.diameter=diameter
        self.radius = diameter/2
        self.pendulum_length=pendulum_length
        self.teeth=teeth
        self.tooth_span=tooth_span
        self.an=degToRad(entry_angle_deg)
        self.T=T
        self.mean_torque_arm_length=mean_torque_arm_length
        # self.escaping_arc_deg=escaping_arc_deg
        self.escaping_arc = degToRad(escaping_arc_deg)

        self.diagrams = []
        self.geometry = {}

        #bits internally needed to generate an escaping arc that we want
        # self.ax_deg=ax_deg
        # self.d=d

        self.tooth_angle = math.pi*2/self.teeth

        '''with ax=90
        Iteration 52, testD: 12.220855468769212, errorTest: 1.9317880628477724e-14
        Balanced escaping arc of 9.65deg with d of 12.2209
        
        or with acceptable error = 0.1
        Iteration 6, testD: 12.203125, errorTest: -1.2386825430033e-05
        Balanced escaping arc of 9.64deg with d of 12.2031
        '''

        if ax_deg < 0 or d < 0:
            #auto calculate the best settings to get the chosen escaping arc
            # d, En, Ex = self.balanceEscapingArcs(91, 0.1)
            ax_deg, d, En, Ex = self.chooseEscapingArc(acceptableError=0.01)
            print("Balanced escaping arc of {:.2f}deg with d of {:.4f} and ax of {:.4f}".format(radToDeg(En), d, ax_deg))
        else:
            self.generate_geometry(d_deg=d, ax_deg=ax_deg)

    def chooseEscapingArc(self, iterations = 100, acceptableError = 0.1):
        '''
        Fiddle with values of ax (exit angle) and balance the escaping arcs so we can choose what we want the escaping arc to be

        uses same binary search idea as balanceEscapingArcs and getRadiusForPointsOnAnArc

        larger ax values seem to result in larger arcs
        '''

        #use acceptableError larger than zero to speed this up

        iterations = 100
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
        En, Ex = self.generate_geometry(testD, ax_deg=ax_deg)
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
                print("balanceEscapingArcs Iteration {}, testD: {}, errorTest: {}".format(i, testD, errorTest))
                # print("found after {} iterations".format(i))
                break
            lastTestD = testD
            testD = (minD + maxD) / 2
            En, Ex = self.generate_geometry(testD, ax_deg=ax_deg)
            errorTest = Ex - En

        return (testD, En, Ex)

    def generate_geometry(self, d_deg=11, ax_deg=90):

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
        D_start_of_exit_impulse = polar(0, self.radius)
        line_3 = Line((0,0), anotherPoint=D_start_of_exit_impulse)
        #[4] clockwise by half a tooth angle
        end_of_exit_impulse_angle = -self.tooth_angle/2
        C_end_of_exit_impulse = polar(end_of_exit_impulse_angle, self.radius)
        line_4 = Line((0,0), anotherPoint=C_end_of_exit_impulse)

        #[5]
        minimum_tooth_space = math.floor(self.tooth_span)
        minimum_tooth_angle = minimum_tooth_space * math.pi*2 / self.teeth
        #I think this is end of the entry impulse?
        K_end_of_entry_impulse = polar(0 + minimum_tooth_angle, self.radius)
        line_5 = Line((0,0), anotherPoint=K_end_of_entry_impulse)

        #[6]
        maximum_tooth_space = math.ceil(self.tooth_span)
        maxiumum_tooth_angle = maximum_tooth_space*math.pi*2 / self.teeth
        #anticlockwise from end of exit impulse by maximum arc of teeth
        J_angle = end_of_exit_impulse_angle + maxiumum_tooth_angle
        J_start_of_entry_impulse = polar( J_angle, self.radius)
        line_6 = Line((0,0), anotherPoint=J_start_of_entry_impulse)


        #[7]
        line_7_entry_start_of_impulse_action = Line(J_start_of_entry_impulse, angle= J_angle + math.pi + self.an)

        #[8]
        line_8_exit_pallet_start_line_of_action = Line(D_start_of_exit_impulse, angle = 0 + ax)

        step_one_figure_35 = cq.Workplane("XY").circle(self.radius)
        step_one_figure_35 = step_one_figure_35.add(line_3.get2D(self.radius))
        step_one_figure_35 = step_one_figure_35.add(line_4.get2D(self.radius))
        step_one_figure_35 = step_one_figure_35.add(line_5.get2D(self.radius))
        step_one_figure_35 = step_one_figure_35.add(line_6.get2D(self.radius))
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



        step_seven_figure_40 = cq.Workplane("XY").circle(self.radius)
        step_seven_figure_40 = step_seven_figure_40.add(line_3.get2D(self.radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_4.get2D(self.radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_5.get2D(self.radius))
        step_seven_figure_40 = step_seven_figure_40.add(line_6.get2D(self.radius))
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
        diagram_for_points = diagram_for_points.add(cq.Workplane("XY").circle(self.radius))
        diagram_for_points = diagram_for_points.add(line_6.get2D(length=self.radius))
        diagram_for_points = diagram_for_points.add(line_5.get2D(length=self.radius))
        diagram_for_points = diagram_for_points.add(line_3.get2D(length=self.radius))
        diagram_for_points = diagram_for_points.add(line_4.get2D(length=self.radius))
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

        self.diagrams = [step_one_figure_35, step_two_figure_36, step_three_figure_37, step_four_figure_38, step_five_figure_39, step_six_figure_40, step_seven_figure_40, diagram_for_points]

        return [En, Ex]

    def checkGeometry(self, geometry=None, acceptableError=0.00001, loud=False):
        if geometry is None:
            geometry = self.geometry
        #check 1: Angle COD should be the angle subtended by half an escape wheel tooth space
        half_tooth_angle = (math.pi*2/self.teeth)/2
        line_CO = Line(geometry["C"], anotherPoint=geometry["O"])
        line_OD = Line(geometry["O"], anotherPoint=geometry["D"])
        COD = line_CO.getAngleBetweenLines(line_OD)

        assert abs(COD - half_tooth_angle) < acceptableError, "check 1: Angle COD should be the angle subtended by half an escape wheel tooth space"
        if loud:
            print("COD: {}deg, half tooth angle:{}deg".format(radToDeg(COD), radToDeg(half_tooth_angle)))

        #check 2: Angle DOK should be the angle subtended by the minimum tooth spaces spanned.
        minimum_tooth_spaces = floor(self.tooth_span)*math.pi*2/self.teeth
        line_DO = Line(geometry["D"], anotherPoint=geometry["O"])
        line_OK = Line(geometry["O"], anotherPoint=geometry["K"])
        DOK = line_DO.getAngleBetweenLines(line_OK)
        assert abs(DOK - minimum_tooth_spaces) < acceptableError, "check 2: Angle DOK should be the angle subtended by the minimum tooth spaces spanned."
        if loud:
            print("DOK: {}deg, minimum_tooth_spaces: {}deg".format(radToDeg(DOK), radToDeg(minimum_tooth_spaces)))

        #check 3: Angle COJ should be the angle subtended by the maximum tooth spaces spanned.
        maximum_tooth_spaces = math.ceil(self.tooth_span)*math.pi*2/self.teeth
        line_OJ = Line(geometry["O"], anotherPoint=geometry["J"])
        COJ = line_CO.getAngleBetweenLines(line_OJ)
        assert abs(COJ - maximum_tooth_spaces) < acceptableError, "check 3: Angle COJ should be the angle subtended by the maximum tooth spaces spanned."
        if loud:
            print("COJ: {}deg, maximum_tooth_spaces: {}deg".format(radToDeg(COJ), radToDeg(maximum_tooth_spaces)))

        #check 4: Angle JOK should be the angle subtended by half an escape wheel tooth space
        JOK = line_OJ.getAngleBetweenLines(line_OK)
        assert abs(JOK - half_tooth_angle) < acceptableError, "check 4: Angle JOK should be the angle subtended by half an escape wheel tooth space"
        if loud:
            print("JOK: {}deg, half tooth: {}deg".format(radToDeg(JOK), radToDeg(half_tooth_angle)))

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

        self.anchor = self.escapement.getAnchorArbour(holeD=anchorHoleD, anchorThick=anchorThick, arbourLength=0, crutchLength=crutchLength, crutchBoltD=crutchBoltD, pendulumThick=threadedRodM, nutMetricSize=nutMetricSize if useNylocForAnchor else 0)

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
            notHole = notHole.add(cq.Workplane("XY").rect(self.threadedRodM+extraR*2 + self.wallThick*2, self.bobR*2).extrude(self.bobThick/2 - self.wallThick).translate((0,0,self.wallThick)))

            for pos in self.bobLidNutPositions:
                notHole = notHole.add(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(self.nutMetricSize*1.5).circle(self.nutMetricSize/2).extrude(self.bobThick-self.wallThick))

            weightHole = weightHole.cut(notHole)

            lid = self.getBobLid(True)

            weightHole = weightHole.add(lid.translate((0,0,self.bobThick-self.wallThick)))

            bob = bob.cut(weightHole)

        #add a little S <--> F text
        textSize = self.gapHeight
        bob = bob.add(cq.Workplane("XY").moveTo(0, 0).text("S", textSize, LAYER_THICK*2, cut=False, halign='center', valign='center', kind="bold").translate((-self.gapWidth/2 - textSize*0.75, 0, self.bobThick)))
        bob = bob.add(cq.Workplane("XY").moveTo(0, 0).text("F", textSize, LAYER_THICK * 2, cut=False, halign='center', valign='center', kind="bold").translate((self.gapWidth/2 + textSize*0.75, 0, self.bobThick)))

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
