from .utility import *
from .gearing import *
import cadquery as cq
import os
from cadquery import exporters


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


    note - little cheap plastic bearings don't like being squashed, 24mm wasn't quite enough for the outer diameter.
    '''

    def __init__(self, diameter, capDiameter, ratchet, rodMetricSize=3, thick=10, useKey=False, screwThreadMetric=3, cordThick=2, bearingInnerD=15, bearingHeight=5, keyKnobHeight=15, useGear=False, useFriction=False, gearThick=5, frontPlateThick=8, style="HAC", bearingLip=2.5, bearingOuterD=24.2):

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
        self.keyWiggleRoom = 0.75

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

        if self.useKey:
            self.keyWallThick = 2.5
            # enough to cut out the key itself
            self.keyWidth = self.keyWallThick * 2 + self.bearingInnerD
            self.keyLength = 40
            self.keyHeight = 50
            self.keyThick = 5

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


    def getKey(self):
        '''
        get the key that can wind the clock, this is one with a little arm and handle

        Exact size of the key is based on the bearing and tolerance:
        key = cq.Workplane("XY").polygon(4, self.bearingInnerD - self.bearingWiggleRoom*2).extrude(self.keyKnobHeight)
        '''



        key = cq.Workplane("XY").radiusArc((self.keyWidth,0),-self.keyWidth/2).lineTo(self.keyWidth,self.keyLength).radiusArc((0,self.keyLength),-self.keyWidth/2).close().extrude(self.keyThick)

        #hole to screw in the knob (loose)
        key = key.faces(">Z").workplane().tag("top").moveTo(self.keyWidth/2,self.keyLength).circle(self.screwThreadMetric/2 + 0.2).cutThruAll()

        #key bit
        key = key.workplaneFromTagged("top").moveTo(self.keyWidth/2,0).circle(0.999*self.keyWidth/2).extrude(self.keyHeight)

        keyHole = cq.Workplane("XY").moveTo(self.keyWidth/2,0).polygon(4, self.bearingInnerD - self.bearingWiggleRoom*2 + self.keyWiggleRoom).extrude(self.keyKnobHeight).translate((0,0,self.keyThick + self.keyHeight-self.keyKnobHeight))

        key = key.cut(keyHole)

        return key


    def getKeyKnob(self):
        r = self.bearingInnerD/2

        screwLength = 30 - self.keyThick

        # circle = cq.Workplane("XY").circle(r)
        # knob = cq.Workplane("XZ").lineTo(r, 0).radiusArc((r*2,r),r).radiusArc((r*2,r*3),-r).lineTo(0,r*3).close().sweep(circle)
        knob = cq.Workplane("XY").circle(self.keyWidth/2).extrude(screwLength)


        nutHeightSpace = getNutHeight(self.screwThreadMetric,True)*2
        screwHole = cq.Workplane("XY").circle(self.screwThreadMetric/2).extrude(screwLength*1.5)
        screwHole = screwHole.add(cq.Workplane("XY").polygon(6,getNutContainingDiameter(self.screwThreadMetric,0.2)).extrude(nutHeightSpace).translate((0,0,screwLength-nutHeightSpace)))

        knob = knob.cut(screwHole)

        return knob

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

                out = os.path.join(path, "{}_cordwheel_key.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.getKey(), out)

                out = os.path.join(path, "{}_cordwheel_key_knob.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.getKeyKnob(), out)



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
