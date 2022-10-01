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

    def __init__(self, height=100, diameter=38, wallThick=2.7, bolt = None):
        '''
        34mm diameter fits nicely with a 40mm m3 screw
        38mm diameter results in a weight of ~0.3kg
        wallThick of 2.6 should result in no infill with three layers of walls
        '''



        self.height=height
        self.diameter=diameter
        self.bolt=bolt
        if self.bolt is None:
            self.bolt = MachineScrew(3)
        self.wallThick=wallThick
        # self.baseThick=4
        self.slotThick = self.wallThick/3
        self.lidWidth = self.diameter * 0.3

        self.hookInnerD = self.bolt.metric_thread*2.5
        self.hookOuterD = self.hookInnerD*1.5
        self.hookThick = self.lidWidth * 0.75

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

        r = self.diameter/2
        angle = math.acos((self.lidWidth/2) / r)
        corner = polar(angle, r)
        # more cadquery fudgery with r
        weight = weight.faces(">Z").workplane().moveTo(corner[0], corner[1]).radiusArc((corner[0], -corner[1]), r - 0.00001).close().mirrorY().extrude(r)



        screwHeight = r - self.bolt.getHeadDiameter()

        screwSpace = self.bolt.getCutter().rotate((0,0,0),(0,1,0),90).translate((-r + self.bolt.getHeadHeight()/2,0,screwHeight + self.height))

        screwSpace = screwSpace.add(self.bolt.getNutCutter(height=1000).rotate((0,0,0),(0,1,0),90).translate((r*0.6,0,screwHeight + self.height)))

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
        self.wallThick=0.45
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

    stop works idea: sprung/weighted lever from the side, after where the ball drops in. If there's no ball there (or no ball falls on it), it would stop the wheel turning
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
        '''
        Kg metre^2 per second squared
        km^2s^-2
        '''
        ballAngle = math.pi*2/(self.ballsAtOnce*2)

        torque = 0

        #from top to bottom, assuming clockwise for no particularily good reason
        for ball in range(self.ballsAtOnce):
            angle = math.pi/2 - ball*ballAngle
            # print("angle", radToDeg(angle))

            xDir = math.cos(angle)*self.pitchDiameter/2
            # print(xDir)
            xDirMetres = xDir/1000
            torque += xDirMetres * self.ballWeightKg * GRAVITY

        return torque

    def getPower(self, rotationsPerHour=1/12):
        '''
        power = mass * gravity * distance / time

        no need to faff around with torque and whatnot, treat the total mass of balls on the wheel as a single weight travelling at a set speed

        return answer in microwatts
        '''

        #one ball falls the distance of the diameter in half a rotation
        halfRotationsPerHour = rotationsPerHour*2

        #time taken for one ball to enter and leave the wheel in seconds
        timeForOneBall_s = 60*60/halfRotationsPerHour
        print("timeforone ball", timeForOneBall_s)

        power = self.ballsAtOnce * self.ballWeightKg * GRAVITY * self.pitchDiameter / timeForOneBall_s

        return power*math.pow(1,6)


class Pulley:
    '''
    Pulley wheel that can be re-used by all sorts of other things
    '''

    def __init__(self, diameter, cordDiameter=2.2, rodMetricSize=3, screwMetricSize=3, screwsCountersunk=True, vShaped=False, style=None, bearing=None, bearingHolderThick=0.8):
        self.diameter=diameter
        self.cordDiameter=cordDiameter
        self.vShaped=vShaped

        self.style=style

        #if negative, don't punch holes
        self.rodMetricSize=rodMetricSize
        self.rodHoleD = rodMetricSize + LOOSE_FIT_ON_ROD
        self.screwMetricSize=screwMetricSize

        self.edgeThick=cordDiameter*0.5
        self.taperThick = cordDiameter * 0.2
        #if not none, a BearingInfo for a bearing instead of a rod
        self.bearing=bearing
        self.bearingHolderThick=bearingHolderThick
        self.screwsCountersunk=screwsCountersunk

        screws = 3

        self.screwPositions=[polar(angle,diameter*0.35) for angle in [i*math.pi*2/screws for i in range(screws)]]



        if bearing is not None:
            #see if we can adjust our total thickness to be the same as the bearing
            totalThick = self.getTotalThick()
            bearingWiggleHeight=0.4
            if totalThick < bearing.bearingHeight + self.bearingHolderThick*2 +bearingWiggleHeight:
                #too narrow
                extraThickNeeded = (bearing.bearingHeight + self.bearingHolderThick*2 + bearingWiggleHeight) - totalThick
                self.edgeThick+=extraThickNeeded/4
                self.taperThick+=extraThickNeeded/4
            else :
                print("Can't fit bearing neatly inside pulley")

        self.hookThick = 7.5
        self.hookBottomGap = 3
        self.hookSideGap = 1

        self.hookWide = 16
        #using a metal cuckoo chain hook to hold the weight, hoping it can stand up to 4kg
        self.cuckooHookOuterD=14#13.2
        self.cuckooHookThick = 1.2#0.9

    def getTotalThick(self):
        return self.edgeThick * 2 + self.taperThick * 2 + self.cordDiameter

    def getMaxRadius(self):
        #needs to be kept consistent with bottomPos below
        return self.diameter/2 + self.cordDiameter

    def getHalf(self, top=False):
        radius = self.diameter/2
        #from the side
        bottomPos = (radius + self.cordDiameter, 0)
        topOfEdgePos = (radius + self.cordDiameter, self.edgeThick)
        endOfTaperPos = (radius, self.edgeThick + self.taperThick)
        topPos = (endOfTaperPos[0]-self.cordDiameter/2, endOfTaperPos[1] + self.cordDiameter/2)

        # edgeR = self.diameter/2 + self.cordDiameter/4
        # middleR = self.diameter/2 - self.cordDiameter/2

        circle = cq.Workplane("XY").circle(self.diameter/2)
        pulley = cq.Workplane("XZ").moveTo(bottomPos[0], bottomPos[1]).lineTo(topOfEdgePos[0], topOfEdgePos[1]).lineTo(endOfTaperPos[0], endOfTaperPos[1])#.\

        if self.vShaped:
            pulley = pulley.lineTo(topPos[0], topPos[1])
        else:
            #pulley = pulley.tangentArcPoint(topPos, relative=False)
            pulley = pulley.radiusArc(topPos, self.cordDiameter/2)

        pulley = pulley.lineTo(0,topPos[1]).lineTo(0,0).close().sweep(circle)

        holeD = self.rodHoleD
        if self.bearing is not None:
            holeD = self.bearing.bearingOuterD

        # TODO cut out rod hole and screwholes if needed
        # if self.rodMetricSize > 0:
        #     shape = shape.faces(">Z").workplane().circle((self.rodMetricSize+LOOSE_FIT_ON_ROD)/2).cutThruAll()

        pulley = Gear.cutStyle(pulley, outerRadius=self.diameter/2-self.cordDiameter/2, innerRadius=holeD/2, style=self.style)



        # pulley = pulley.faces(">Z").workplane().circle(holeD/2).cutThroughAll()
        hole = cq.Workplane("XY").circle(holeD/2).extrude(1000)

        if self.bearing is not None:
            hole = hole.translate((0,0,self.bearingHolderThick))
            hole = hole.add(cq.Workplane("XY").circle(self.bearing.innerD/2+self.bearing.bearingHolderLip).extrude(1000))

        pulley = pulley.cut(hole)

        screwHoles = cq.Workplane("XY").tag("base")

        for screwPos in self.screwPositions:
            screwHoles = screwHoles.workplaneFromTagged("base").moveTo(screwPos[0], screwPos[1]).circle(self.screwMetricSize/2).extrude(1000)

            if top:
                if self.screwsCountersunk:
                    #countersunk for screw heads
                    screwHoles = screwHoles.add(cq.Solid.makeCone(radius1=getScrewHeadDiameter(self.screwMetricSize, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE, radius2=self.screwMetricSize / 2,
                                                        height=getScrewHeadHeight(self.screwMetricSize, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE).translate(screwPos))
                else:
                    #cq.Workplane("XY").moveTo(screwPos[0], screwPos[1]).circle(getScrewHeadDiameter(self.screwMetricSize, countersunk=False)/2 + NUT_WIGGLE_ROOM/2).extrude(getScrewHeadHeight(self.screwMetricSize, countersunk=False))
                    screwHoles = screwHoles.add(getHoleWithHole(innerD=self.screwMetricSize,outerD=getScrewHeadDiameter(self.screwMetricSize, countersunk=False),deep=getScrewHeadHeight(self.screwMetricSize, countersunk=False)).translate(screwPos))
            else:
                #space for a nut
                #screwHoles = screwHoles.workplaneFromTagged("base").moveTo(screwPos[0], screwPos[1]).polygon(6, getNutContainingDiameter(self.screwMetricSize,0.2)).extrude(getNutHeight(self.screwMetricSize))
                #rotate so flat side is towards centre. Assumes 3 screws....
                # screwHoles = screwHoles.add(cq.Workplane("XY").polygon(6, getNutContainingDiameter(self.screwMetricSize, 0.2)).extrude(getNutHeight(self.screwMetricSize)).rotate((0,0,0),(0,0,1),360/12).translate(screwPos))
                screwHoles = screwHoles.add(getHoleWithHole(innerD=self.screwMetricSize,outerD=getNutContainingDiameter(self.screwMetricSize, NUT_WIGGLE_ROOM),deep=getNutHeight(self.screwMetricSize),sides=6).rotate((0, 0, 0), (0, 0, 1), 360 / 12).translate(screwPos))

        pulley = pulley.cut(screwHoles)

        return pulley

    def getHookTotalThick(self):
        return self.getTotalThick() + self.hookSideGap*2 + self.hookThick*2

    def getHookHalf(self):
        '''
        Get a way to attach a weight to a pulley wheel
        assumes we're using a bearing
        '''



        axleHeight = self.getMaxRadius() + self.hookBottomGap + self.hookThick*0.5

        extraHeight = 0

        length = self.getTotalThick() + self.hookSideGap*2 + self.hookThick*2

        # hook = cq.Workplane("XY").lineTo(length/2,0).line(0,axleHeight+extraHeight).line(- thick,0).line(0,-(axleHeight + extraHeight - thick) ).lineTo(0,thick).mirrorY().extrude(wide)

        #make a large block of a nice shape and cut out space for a pulley wheel
        r = self.hookWide/2#*0.75
        pulleyHoleWide = self.getTotalThick() + self.hookSideGap * 2

        hook = cq.Workplane("XY").lineTo(axleHeight + extraHeight, 0).radiusArc((axleHeight + extraHeight, self.hookWide), -r).lineTo(0, self.hookWide).radiusArc((0, 0), -r).close().extrude(length/2)

        holeR = self.getMaxRadius() + self.hookBottomGap

        #leave two sticky out bits on the hook that will press right up to the inside of the bearing
        pulleyHole = cq.Workplane("XY").circle(holeR).extrude(self.getTotalThick()-self.bearingHolderThick)\
             .faces("<Z").workplane().circle(holeR).circle(self.bearing.innerSafeD/2).extrude(self.hookSideGap+self.bearingHolderThick)

        #            .faces(">Z").workplane().circle(holeR).circle(self.bearing.innerSafeD).extrude(self.hookSideGap)\

        #.translate((axleHeight, self.hookWide/2, self.hookThick))
        pulleyHole = pulleyHole.translate((axleHeight, self.hookWide/2, self.hookThick + self.hookSideGap+self.bearingHolderThick))

        # return pulleyHole
        hook = hook.cut(pulleyHole)

        # cut out hole for m4 rod for the pulley axle
        rodHole = cq.Workplane("XY").circle(self.bearing.innerD / 2).extrude(1000).translate((axleHeight, self.hookWide/2, 0))

        hook = hook.cut(rodHole)


        #hole at the bottom for a screw to hold the pulley together and take the cuckoo hook to hold a weight

        screwhole = cq.Workplane("XY").circle(self.bearing.innerD / 2).extrude(1000).translate((0,self.hookWide/2, 0))

        hook = hook.cut(screwhole)




        #translate so hole is at 0,0
        hook = hook.translate((-axleHeight, -self.hookWide / 2,0))

        cuckooHookHole = cq.Workplane("XY").moveTo(0,self.cuckooHookOuterD/2).radiusArc((0,-self.cuckooHookOuterD/2),self.cuckooHookOuterD/2).line(-100,0).line(0,self.cuckooHookOuterD).close().extrude(self.cuckooHookThick)

        hook = hook.cut(cuckooHookHole.translate((0, 0, self.getHookTotalThick() / 2 - self.cuckooHookThick / 2)))

        return hook

    def getAssembled(self):
        pulley = self.getHalf(top=False).add(self.getHalf(top=True).rotate((0,0,self.getTotalThick()/2),(1,0,self.getTotalThick()/2),180))

        if self.bearing is not None:
            # hook = self.getHookHalf()
            # pulley = hook.add(pulley.translate((0,0,-self.getTotalThick()/2)).rotate((0,0,0),(0,1,0),90))

            hook = self.getHookHalf().add(self.getHookHalf().rotate((0,0,self.getHookTotalThick()/2),(1,0,self.getHookTotalThick()/2),180))
            pulley = hook.add(pulley.translate((0,0,self.getHookTotalThick()/2-self.getTotalThick()/2)))

        return pulley

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_pulley_wheel_top.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHalf(top=True), out)

        out = os.path.join(path, "{}_pulley_wheel_bottom.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHalf(top=False), out)

        if self.bearing is not None:
            out = os.path.join(path, "{}_pulley_hook_half.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHookHalf(), out)

class MainSpring:
    '''
    Class to represent the dimensions of a mainspring
    '''
    def __init__(self, height=7.5, hook_height = -1, thick = 0.32, loop_end=True):
        self.height=height
        if hook_height < 0:
            hook_height = height / 3
        self.hook_height = hook_height
        self.thick=thick
        self.loop_end=loop_end


class SpringArbour:

    def __init__(self, metric_rod_size=3, spring=None, bearing=None, min_inner_diameter=4.5, power_clockwise=True, ratchet_thick=4):
        '''
        arbour that could go inside a barrel, or be used with a loop end spring
        ends in just a flat base, so it can be used by either a loop end or barrel class later
        top is designed to go through a bearing and end in a key, just like a key-wound cord wheel
        '''

        if spring is None:
            #default, which is a smiths alarm clock loop end
            spring = MainSpring()

        self.spring = spring

        #if zero, no ratchet
        self.ratchet_thick=ratchet_thick

        self.metric_rod_size = metric_rod_size
        if bearing is None:
            #default to a 10mm inner diameter bearing (I've got little cheap plastic ones of these)
            bearing = getBearingInfo(10)
        self.bearing = bearing
        #the bit the inside of the spring wraps around, if it's too small then larger springs will struggle, but I imagine with the small
        #alarm clock springs I'll usually be too big
        self.min_inner_diameter = min_inner_diameter

        self.min_wall_thick=1.5

        self.diameter = self.metric_rod_size + self.min_wall_thick*2

        self.spring_bit_height = self.spring.height/0.75

        #smiths' alarm it's ~0.8 for a spring of ~0.25 (x3.2)
        #for the astral, it's ~1.5 for a spring of ~0.4 (3.75)
        self.hook_deep = self.spring.thick*3.5

        # self.hook_centre_height = self.hook_height*0.6
        #taper the bottom of the hook so it's printable
        self.hook_taper_height = self.spring.hook_height*0.3

        self.power_clockwise = power_clockwise
        self.bearingWiggleRoom = 0.05
        self.keySquareBitHeight = 20

        #radius for that bit that slots inside the bearing
        self.bearingBitR = self.bearing.innerD / 2 - self.bearingWiggleRoom

        self.bearingStandoffThick=0.6

        self.beforeBearingTaperHeight=0

        if self.diameter < self.bearingBitR*2:
            #need to taper up to the bearing, as it's bigger!
            r = self.bearing.innerSafeD/2  - self.diameter/2
            angle=degToRad(30)
            self.beforeBearingTaperHeight = r * math.sqrt(1/math.sin(angle) - 1)

        self.ratchet = None
        if self.ratchet_thick > 0:
            self.ratchet = Ratchet(totalD=self.diameter*4,thick=self.ratchet_thick, power_clockwise = self.power_clockwise)

    def getArbour(self):
        arbour = cq.Workplane("XY")

        if self.ratchet is not None:
            arbour = self.ratchet.getInnerWheel().faces(">Z").workplane().circle(self.diameter/2).extrude(self.spring_bit_height)

        # return arbour

        arbour = arbour.circle(self.diameter/2).extrude(self.spring_bit_height)


        hook_r = self.diameter/3

        # hook_taper_height = (self.hook_height - self.hook_centre_height)/2
        #don't need to taper both ends, only the one that would be printing mid-air!
        spring_hook = cq.Workplane("XY").add(cq.Solid.makeCone(radius1=hook_r - self.hook_deep, radius2=hook_r,height = self.hook_taper_height))
        spring_hook = spring_hook.faces(">Z").workplane().circle(hook_r).extrude(self.spring.hook_height - self.hook_taper_height)

        #I'm not sure it want it completely flat, I think slightly angled will help hold the spring more reliably?
        #angle relative to completely flat
        hook_angle = 10
        #crudely create a large triangle that will chop away everything not needed
        point = polar(degToRad(hook_angle),hook_r*200)

        #cutting it flat
        # spring_hook = spring_hook.cut(cq.Workplane("XY").moveTo(0,self.hook_deep).rect(self.hook_deep*2,self.hook_deep*2).extrude(self.spring.hook_height))
        spring_hook = spring_hook.cut(cq.Workplane("XY").moveTo(0,0).lineTo(point[0],point[1]).lineTo(-point[0], point[1]).close().extrude(self.spring.hook_height))

        clockwise = 1 if self.power_clockwise else -1

        spring_hook = spring_hook.translate((clockwise*(self.hook_deep + (self.diameter/2 - hook_r)),0,self.spring_bit_height/2 - self.spring.hook_height/2 + self.ratchet_thick))
        #for some reason just adding results in a malformed STL, but cutting and then adding is much better?!
        spring_hook = spring_hook.cut(arbour)

        arbour = arbour.add(spring_hook)

        if self.beforeBearingTaperHeight > 0:
            arbour = arbour.add(cq.Solid.makeCone(radius1=self.diameter/2, radius2=self.bearing.innerSafeD/2, height = self.beforeBearingTaperHeight).translate((0,0,self.spring_bit_height + self.ratchet_thick)))
            arbour = arbour.faces(">Z").workplane().moveTo(0, 0).circle(self.bearing.innerSafeD/2).extrude(self.bearingStandoffThick)

        arbour = arbour.faces(">Z").workplane().moveTo(0, 0).circle(self.bearing.innerD/2 - self.bearingWiggleRoom).extrude(self.bearing.bearingHeight)
        # using polygon rather than rect so it calcualtes the size to fit in teh circle
        arbour = arbour.faces(">Z").workplane().polygon(4, self.bearing.innerD - self.bearingWiggleRoom * 2).extrude(self.keySquareBitHeight)

        arbour = arbour.faces(">Z").workplane().circle(self.metric_rod_size/2).cutThruAll()



        return arbour

class LoopEndSpringArbour:

    def __init__(self, spring=None):
        if spring is None:
            #default, which is a smiths alarm clock loop end
            spring = MainSpring()
        self.spring = spring

class WeightPoweredWheel:
    '''
    Python doesn't have interfaces, but this is the interface for the powered wheel classes (for weights! I forgot entirely about springs when I wrote this)
    '''

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 30

    def __init__(self):
        #diameter/circumference for the path the rope or chain takes. For the cord, this is the minimum diameter for the first layer of coils
        self.diameter=30
        self.circumference=math.pi * self.diameter
        self.ratchet = Ratchet()
        self.type = PowerType.NOT_CONFIGURED
        self.looseOnRod = False

    def getChainHoleD(self):
        '''
        Returns diameter of hole for the rope/chain/cord to pass through. It needs a hole to prevent winding the weight up too far
        '''

    def getAssembled(self):
        '''
        return 3D model of fully assembled wheel with ratchet (for the model, not printing)
        '''

    def getHeight(self):
        '''
        returns total thickness of the assembled wheel, with ratchet. If it needs a washer, this is included in the height
        '''

    def outputSTLs(self, name="clock", path="../out"):
        '''
        save STL files to disc for all the objects required to print this wheel
        '''

    def getChainPositionsFromTop(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

    def getTurnsForDrop(self, maxChainDrop):
        '''
        Given a chain drop, return number of rotations of this wheel.
        this is trivial for rope or chain, but not so much for the cord
        '''

    def getRunTime(self, minuteRatio=1, cordLength=2000):
        '''
        print information about runtime based on the info provided
        '''

    def printScrewLength(self):
        '''
        print to console information on screws required to assemble
        '''


class RopeWheel:
    '''
    Drop in replacement for chainwheel, but uses friction to hold a hemp rope
    '''

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 20

    def __init__(self, diameter, ratchet_thick, rodMetricSize=3, screw=None, ropeThick=2.2, wallThick=2, power_clockwise=True):

        #diameter for the rope
        self.diameter=diameter
        self.circumference = math.pi*diameter

        self.looseOnRod = False
        self.type = PowerType.ROPE

        #using just diamtere, aim 17 got

        #aim: 17, got 22.3

        #rough guess based on the first printed wheel using 2.2mm hemp rope
        self.innerDiameter = diameter - ropeThick*5.5

        # TODO the rope doesn't get anywhere near this diameter! it's almost double. That's fine, so long as I can work out what the actual diameter is for the rope

        self.rodMetricSize=rodMetricSize
        self.screw = screw
        if self.screw is None:
            self.screw = MachineScrew(2)
        self.ropeThick=ropeThick
        distance = self.screw.metric_thread*2
        self.screwPositions = [(-distance, 0), (distance, 0)]


        #min thickness, adjustable to help with selecting screws
        self.wallThick=wallThick
        #width of the opening the rope will slot into
        self.gulleyWide = self.ropeThick*2
        #how far our the gulley extends (extra diameter)
        self.extraRim = self.ropeThick*4

        self.rodD = rodMetricSize + LOOSE_FIT_ON_ROD

        circumference = math.pi*self.innerDiameter
        self.nibs= math.floor(0.5*circumference/ropeThick)
        self.nibThick = 1

        ratchetOuterD = self.diameter*2.25
        self.ratchet = Ratchet(thick=ratchet_thick, totalD=ratchetOuterD, innerRadius=self.innerDiameter / 2 - self.ropeThick / 2 + self.extraRim, power_clockwise=power_clockwise)


    def printScrewLength(self):
        if self.screw.countersunk:
            screwLength = self.getHeight()-WASHER_THICK
        else:
            screwLength = self.getHeight() - WASHER_THICK - self.screw.getHeadHeight()
        #nut hole is extra deep by thickness of the ratchet
        print("RopeWheel needs: {} screw length {}-{}".format(self.screw.getString(), screwLength, screwLength-self.ratchet.thick))

    def getTurnsForDrop(self, maxChainDrop):
        return maxChainDrop/self.circumference

    def getChainHoleD(self):
        return self.ropeThick + 4

    def getHalf(self, top=False):
        radius = self.innerDiameter / 2 - self.ropeThick/2



        # from the side
        bottomPos = (radius + self.extraRim, 0)
        topOfEdgePos = (radius + self.extraRim, self.wallThick)
        middlePos = (radius, self.wallThick + self.gulleyWide/2)

        circle = cq.Workplane("XY").circle(self.innerDiameter / 2)
        ropeWheel = cq.Workplane("XZ").moveTo(bottomPos[0], bottomPos[1]).lineTo(topOfEdgePos[0], topOfEdgePos[1]).lineTo(middlePos[0], middlePos[1])


        ropeWheel = ropeWheel.lineTo(0, middlePos[1]).lineTo(0, 0).close().sweep(circle)

        offset = 0 if top else 0.5*math.pi*2/self.nibs
        nibOuterOuterX = radius + self.extraRim * 0.95
        nibOuterX=radius + self.extraRim*0.9
        nibInnerX = radius + self.extraRim*0.4
        nibStart = radius*0.9
        nibEdgeHeight = self.wallThick + self.gulleyWide*0.25
        nibMiddleHeight = self.wallThick + self.gulleyWide*0.5
        for i in range(self.nibs):
            angle = i*math.pi*2/self.nibs + offset

            nib = cq.Workplane("XZ").moveTo(nibStart,self.wallThick).lineTo(nibOuterOuterX,self.wallThick).lineTo(nibOuterX,nibEdgeHeight).lineTo(nibInnerX,nibMiddleHeight).lineTo(nibStart,nibMiddleHeight).close().extrude(self.nibThick).translate((0,self.nibThick/2,0))
            # return nib
            ropeWheel = ropeWheel.add(nib.rotate((0,0,0), (0,0,1), radToDeg(angle)))




        if not top:
            ropeWheel = ropeWheel.translate((0,0,self.ratchet.thick)).add(self.ratchet.getInnerWheel())

        holeD = self.rodD
        # pulley = pulley.faces(">Z").workplane().circle(holeD/2).cutThroughAll()
        hole = cq.Workplane("XY").circle(holeD / 2).extrude(1000)

        ropeWheel = ropeWheel.cut(hole)



        for pos in self.screwPositions:
            if not top:
                #have a bigger hole than needed for the nut in the ratchet side, so we can get away with shorter screws
                cutter = self.screw.getNutCutter(withScrewLength=100, withBridging=True, height=self.ratchet.thick + self.screw.getNutHeight()).rotate((0,0,0),(0,0,1),360/12)
            else:
                cutter = self.screw.getCutter(withBridging=True)

            ropeWheel = ropeWheel.cut(cutter.translate(pos))

        return ropeWheel

    def getAssembled(self):

        assembly = self.getHalf(top=False)

        assembly = assembly.add(self.getHalf(top=True).rotate((0,0,0),(1,0,0),180).translate((0, 0, self.getHeight()-WASHER_THICK)))

        return assembly
    def getHeight(self):

        return self.wallThick*2 + self.gulleyWide + self.ratchet.thick + WASHER_THICK

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path,"{}_rope_wheel_with_click.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHalf(top=False), out)
        out = os.path.join(path, "{}_rope_wheel_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHalf(top=True), out)

    def getChainPositionsFromTop(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

        zOffset = - WASHER_THICK - self.wallThick - self.gulleyWide / 2
        #if the calculation of innerDiameter is right, then the rope will be diameter apart
        return [[(-self.diameter / 2, zOffset)], [(self.diameter / 2, zOffset)]]

    def getRunTime(self,minuteRatio=1,chainLength=2000):
        #minute hand rotates once per hour, so this answer will be in hours
        return minuteRatio*chainLength/self.circumference


class CordWheel:
    '''
    This will be a replacement for the chainwheel, instead of using a chain this will be a coiled up clock cord.
    One end will be tied to the wheel and then the wheel wound up.

    Two options: use a key to wind it up, or have a double wheel and one half winds when the other unwinds, then you can tug the wound up side
    to wind up the weighted side.

    Made of two segments (one if using key) and a cap. Designed to be attached to the ratchet click wheel

    note - little cheap plastic bearings don't like being squashed, 24mm wasn't quite enough for the outer diameter.

    '''

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 21

    def __init__(self,  diameter, ratchet_thick=4, power_clockwise=True, rodMetricSize=3, thick=10, useKey=False, screwThreadMetric=3, cordThick=2, bearing=None, keySquareBitHeight=30, gearThick=5, frontPlateThick=8, style="HAC", windingKeyHeightFromPlate=70, windingKeyHandleLength=30, cordLength=2000, looseOnRod=True):
        '''
        looseOnRod - if True then the cord/chain/rope section of the wheel (this bit) is loose on the arbour. If true, then that is fixed and the actual gear wheel is loose on the arbour
        for now assume that is this is loose, it's just bare PETG on threaded rod, but if the wheel is loose it's a steel tube on the threaded rod. Also to consider are smaller diameter of bearings

        '''
        self.type = PowerType.CORD

        self.diameter=diameter
        #thickness of one segment (the bit where the cord coils up)
        self.thick=thick
        #if true, a key can be used to wind this cord wheel (if false, there are two cord winding segements)
        self.useKey=useKey
        #1mm felt too flimsy
        #2mm was fine, but I'm trying to reduce depth as much as possible
        #note - if the clock is leaning forwards even slightly, then the cord can put a lot of weight on the top cap, bending it and forcing it against the front plate
        #beforeBearingExtraHeight helps compensate, but thicker caps do too
        self.capThick=1.6
        self.topCapThick = self.capThick

        # using as proxy for heavy
        self.heavyDuty = self.useKey
        self.fixingScrews = 2

        self.topCapOverlap=0
        # even the 2mm cap got a bit wonky, so ensure lots of clearence from the front plate
        self.beforeBearingExtraHeight = 1

        if self.heavyDuty:
            #trying to prevent the end cap warping and rubbing against front plate
            #and there being a gap that the cord can get stuck down
            self.topCapThick = 3

            self.fixingScrews=4

            #I think I might be able get away with just using 3 screws and a thicker cap, and avoid this complication entirely
            #but it is implemented anyway, just might not print perfectly as the bridging hasn't been done
            # self.topCapOverlap = LAYER_THICK * 4
            self.topCapOverlap = 0
            self.overlapSlotWide=self.diameter*0.075
            self.overlapSlotWiggle=0.1

        #keeping large so there's space for the screws and screwheads
        self.capDiameter = diameter + 30#diameter*2#.5
        self.rodMetricSize = rodMetricSize
        self.holeD = rodMetricSize
        self.looseOnRod = looseOnRod

        if self.looseOnRod:
            self.holeD += LOOSE_FIT_ON_ROD

        self.screwThreadMetric=screwThreadMetric

        '''
        bearingInnerD=15, bearingHeight=5, bearingLip=2.5, bearingOuterD=24.2,
        '''

        if bearing is None:
            bearing = getBearingInfo(15)

        #only if useKey is true will this be used
        self.bearing = bearing
        # extra radius to add to stand off from a bearing
        self.bearingWiggleRoom = 0.05
        #this is the square bit that sticks out the front of the clock. I suck at names
        self.keySquareBitHeight=keySquareBitHeight
        self.gearThick = gearThick
        self.frontPlateThick=frontPlateThick

        #default length, in mm
        self.cordLength=cordLength

        self.style = style

        #how far from the centre are the screws that hold this together
        self.fixingDistance=self.diameter*0.3

        if self.useKey:
            self.fixingDistance=self.diameter/2 - self.screwThreadMetric/2 - 1.5

        self.fixingPoints = [polar(a*math.pi*2/self.fixingScrews, self.fixingDistance) for a in range(self.fixingScrews)]#[(self.fixingDistance,0), (-self.fixingDistance,0)]
        self.cordThick=cordThick

        #distance to keep the springs of the clickwheel from the cap, so they don't snag
        self.clickWheelExtra=LAYER_THICK

        self.ratchet = Ratchet(totalD=self.capDiameter, thick=ratchet_thick, power_clockwise=power_clockwise, innerRadius=self.capDiameter/2 - 12.5)
        self.keyScrewHoleD = self.screwThreadMetric

        self.keyWiggleRoom = 0.75


        if self.useKey:
            self.keyWallThick = 2.5
            # enough to cut out the key itself
            self.keyWidth = self.keyWallThick * 2 + self.bearing.innerD
            #this is the length of the handle of the key if it's knob-type (needs to be short enough that it won't bump into the motion works, or else windingKeyHeightFromPlate needs to be
            #long enough that we're above the motion works)
            self.windingKeyHandleLength = windingKeyHandleLength
            #this is how far from the front of the clock the winding handle of the key will be
            self.windingKeyHeightFromPlate = windingKeyHeightFromPlate
            #thickness of the handle
            self.windingKeyHandleThick = 5
            self.keyHoleDeep = self.keySquareBitHeight - 5


    def printScrewLength(self):
        if self.useKey:
            minScrewLength = self.ratchet.thick/2 + self.capThick + self.topCapThick + self.thick
            print("cord wheel screw (m{}) length between".format(self.screwThreadMetric), minScrewLength, minScrewLength + self.ratchet.thick/2)
        else:
            # two sections, one for winding up while the other winds down
            minScrewLength = self.ratchet.thick - (getScrewHeadHeight(self.screwThreadMetric) + LAYER_THICK) + self.clickWheelExtra + self.capThick + self.topCapThick + self.thick * 1.5
            if self.useKey:
                minScrewLength -= self.thick
            #I think this might assume caps all the same thickness? which is true when not using a key
            print("cord wheel screw (m{}) length between".format(self.screwThreadMetric), minScrewLength + getNutHeight(self.screwThreadMetric), minScrewLength + self.thick / 2 + self.capThick)


    def getChainHoleD(self):
        (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.getCordTurningInfo()

        #assume that the cord is going to squish a bit, so don't need to make this too excessive
        return self.cordThick * layers

    def getChainPositionsFromTop(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

        (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.getCordTurningInfo(cordLength=self.cordLength)

        #not in the centre of hte layers, assuming that the cord will be fairly squashed, so offset slightly towards the wheel
        chainX = (self.diameter / 2 + self.cordThick * layers *0.4)

        if self.useKey:
            #one hole only
            chainZTop = -self.beforeBearingExtraHeight - self.topCapThick
            chainZBottom = chainZTop - self.thick

            side = 1 if self.ratchet.isClockwise() else -1
            chainX *= side
            #don't worry about the pulley hole, the plates will do that if needed
            return [ [(chainX, chainZTop), (chainX, chainZBottom)] ]
        else:
            #make the weight segment the one nearer the wall to be consistent with old designs (idea was to ensure less flexing of plates, but as they've got closer this might
            #make the weight a bit close to teh wall?)
            weightSegmentBottomZ = - WASHER_THICK - self.topCapThick - self.thick - self.capThick - self.thick
            weightSegmentTopZ = - WASHER_THICK - self.topCapThick - self.thick - self.capThick
            windSegmentBottomZ = - WASHER_THICK - self.topCapThick - self.thick
            windSegmentTopZ = - WASHER_THICK - self.topCapThick

            if self.ratchet.isClockwise():
                weightSide = 1
            else:
                weightSide = -1
            return [ [ (chainX*weightSide, weightSegmentTopZ), (chainX*weightSide, weightSegmentBottomZ) ], [(chainX*weightSide*(-1), windSegmentTopZ), (chainX*weightSide*(-1), windSegmentBottomZ)] ]


    def getNutHoles(self):

        #rotate by 1/12th so there's a tiny bit more space near the main hole
        cutter = cq.Workplane("XY").add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).rotate((0,0,0),(0,0,1),360/12).translate(self.fixingPoints[0]))
        cutter = cutter.add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).rotate((0,0,0),(0,0,1),360/12).translate(self.fixingPoints[1]))
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

        holes = holes.add(cq.Workplane("XY").circle(self.holeD/2).extrude(self.pulley.getTotalThick()))
        segment = segment.cut(holes)

        return segment

    def getSegment(self, front=True):
        #if front segment (only applies to non-key version), the holes for screws/nuts will be different

        #end is the cap
        segment = self.getCap()

        #where the cord wraps
        segment = segment.faces(">Z").workplane().circle(self.diameter/2).extrude(self.thick)



        if self.useKey:
            #put the key on the top!

            #space for the cap

            # segment = segment.faces(">Z").workplane().moveTo(0, 0).circle(self.bearingInnerD / 2 + self.bearingLip).extrude(self.beforeBearingExtraHeight)
            segment = segment.faces(">Z").workplane().moveTo(0, 0).circle(self.bearing.innerD / 2 - self.bearingWiggleRoom).extrude(self.bearing.bearingHeight + self.beforeBearingExtraHeight + self.topCapThick)
            #using polygon rather than rect so it calcualtes the size to fit in teh circle, rotating 45deg so we have more room for the screw heads
            key = cq.Workplane("XY").polygon(4, self.bearing.innerD - self.bearingWiggleRoom*2).extrude(self.keySquareBitHeight)
            segment = segment.add(key.rotate((0,0,0),(0,0,1),45).translate((0,0,self.capThick + self.thick + self.bearing.bearingHeight + self.beforeBearingExtraHeight + self.topCapThick)))



            if self.topCapOverlap > 0 and not front:
                #overlapping slot
                overlap = cq.Workplane("XY").circle(self.diameter / 2).circle(self.diameter / 2 - self.overlapSlotWide).extrude(self.topCapOverlap)
                segment = segment.add(overlap.translate((0,0, self.capThick + self.thick)))

            countersink = self.getScrewCountersinkCutter(self.thick + self.capThick + self.topCapThick)
            segment = segment.cut(countersink)



        #hole for the rod
        segment = segment.faces(">Z").circle(self.holeD/2).cutThruAll()

        #holes for the screws that hold this together
        segment = segment.faces(">Z").pushPoints(self.fixingPoints).circle(self.screwThreadMetric/2).cutThruAll()

        if front:
            #base of this needs space for the nuts (for the non-key version)
            #current plan is to put the screw heads in the ratchet, as this side gives us more wiggle room for screws of varying length
            segment = segment.cut(self.getNutHoles())





        cordHoleR = 1.5*self.cordThick/2
        #weird things happenign without the +0.001 with a 1mm cord
        cordHoleZ = self.capThick + cordHoleR + 0.001

        cordHoleY = self.diameter*0.25

        #cut a hole so we can tie the cord
        cordHole = cq.Workplane("YZ").moveTo(cordHoleY,cordHoleZ).circle(cordHoleR).extrude(self.diameter*4).translate((-self.diameter*2,0,0))

        # #screw to tie the end of the cord to (NOTE - given the diameter of the hole, this is not feasible unless I buy some teeny tiny screws)
        # cordEndScrew = MachineScrew(metric_thread=2, countersunk=True)
        # cordHole = cordHole.add(cordEndScrew.getCutter(length=12).translate((self.diameter*0.25,cordHoleY,0)))

        segment = segment.cut(cordHole)

        return segment

    def getScrewCountersinkCutter(self, topOfScrewhead):
        '''
        countersink from top down
        '''

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
        capThick = self.topCapThick if top else self.capThick
        cap = cq.Workplane("XY").circle(self.capDiameter/2).extrude(capThick + extraThick)

        holeR = self.holeD / 2
        if self.useKey and top:
            holeR = self.bearing.innerD/2 + self.bearingWiggleRoom

            #add small ring to keep this further away from the bearing
            cap = cap.faces(">Z").workplane().circle(holeR).circle(self.bearing.innerD/2 + self.bearing.bearingHolderLip).extrude(self.beforeBearingExtraHeight)
            #add space for countersunk screw heads
            countersink = self.getScrewCountersinkCutter(capThick + extraThick)
            cap = cap.cut(countersink)

        if top and self.topCapOverlap > 0:
            #overlap slot
            cutter = cq.Workplane("XY").circle(self.diameter/2).circle(self.diameter/2 - self.overlapSlotWide - self.overlapSlotWiggle).extrude(self.topCapOverlap)
            cap = cap.cut(cutter)

        # hole for the rod
        cap = cap.cut(cq.Workplane("XY").circle(holeR).extrude(capThick*10))

        # holes for the screws that hold this together
        cap = cap.faces(">Z").pushPoints(self.fixingPoints).circle(self.screwThreadMetric / 2).cutThruAll()
        cap = Gear.cutStyle(cap, self.capDiameter/2-self.holeD*0.75, innerRadius=self.diameter / 2 + self.cordThick, style=self.style)
        return cap

    def getClickWheelForCord(self):
        clickwheel = self.ratchet.getInnerWheel()

        clickwheel = clickwheel.faces(">Z").workplane().circle(self.ratchet.clickInnerRadius*0.999).extrude(self.clickWheelExtra)

        # hole for the rod
        clickwheel = clickwheel.faces(">Z").circle(self.holeD / 2).cutThruAll()

        # holes for the screws that hold this together
        clickwheel = clickwheel.faces(">Z").pushPoints(self.fixingPoints).circle(self.screwThreadMetric / 2).cutThruAll()

        if self.useKey:
            #space for a nut
            cutter = cq.Workplane("XY")
            for fixingPoint in self.fixingPoints:
                cutter = cutter.add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, 0.2), self.ratchet.thick/2, sides=6).translate(fixingPoint))
        else:
            #cut out space for screwheads
            # cutter = cq.Workplane("XY").pushPoints(self.fixingPoints).circle(getScrewHeadDiameter(self.screwThreadMetric) / 2).extrude(getScrewHeadHeight(self.screwThreadMetric))
            countersunk = True

            if countersunk:
                cutter = cq.Workplane("XY")

                for fixingPoint in self.fixingPoints:
                    coneHeight = getScrewHeadHeight(self.screwThreadMetric, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE
                    bottomR = getScrewHeadDiameter(self.screwThreadMetric, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE
                    cutter = cutter.add(cq.Solid.makeCone(radius1=bottomR, radius2=self.screwThreadMetric / 2,
                                                                    height=coneHeight).translate((fixingPoint[0], fixingPoint[1],0)))
            else:
                cutter = cq.Workplane("XY").add(getHoleWithHole(self.screwThreadMetric, getScrewHeadDiameter(self.screwThreadMetric), getScrewHeadHeight(self.screwThreadMetric)+LAYER_THICK).translate(self.fixingPoints[0]))
                cutter = cutter.add(getHoleWithHole(self.screwThreadMetric, getScrewHeadDiameter(self.screwThreadMetric), getScrewHeadHeight(self.screwThreadMetric) + LAYER_THICK).translate(self.fixingPoints[1]))
        clickwheel = clickwheel.cut(cutter)



        return clickwheel

    def getWindingKey(self, withKnob=True):
        '''
        winding key! this is one with a little arm and handle

        Exact size of the key is based on the bearing and tolerance:
        key = cq.Workplane("XY").polygon(4, self.bearingInnerD - self.bearingWiggleRoom*2).extrude(self.keyKnobHeight)

        if withKnob, it's like an old longcase key with handle. If not, it's like a mantle key
        '''

        if withKnob:
            #base for handle
            key = cq.Workplane("XY").radiusArc((self.keyWidth,0),-self.keyWidth/2).lineTo(self.keyWidth, self.windingKeyHandleLength).radiusArc((0, self.windingKeyHandleLength), -self.keyWidth / 2).close().extrude(self.windingKeyHandleThick)
            # hole to screw in the knob (loose)
            key = key.faces(">Z").workplane().tag("top").moveTo(self.keyWidth / 2, self.windingKeyHandleLength).circle(self.screwThreadMetric / 2 + 0.2).cutThruAll()
        else:
            key = cq.Workplane("XY").tag("top")

            keyGripTall = min(self.windingKeyHeightFromPlate * 0.3, 15)
            keyGripWide = self.keyWidth*2.5

            # grippyBit = cq.Workplane("XZ").rect(keyGripWide,keyGripTall).extrude(self.keyWallThick)
            r=keyGripWide*0.1

            grippyBit = cq.Workplane("XZ").lineTo(keyGripWide/2,0).lineTo(keyGripWide/2,keyGripTall).tangentArcPoint((-r,r*1.25))\
                .tangentArcPoint((0,keyGripTall),relative=False).mirrorY().extrude(self.windingKeyHandleThick)
            # return grippyBit
            key = key.add(grippyBit.translate((self.keyWidth / 2, self.windingKeyHandleThick / 2, 0)))



        #key bit
        key = key.workplaneFromTagged("top").moveTo(self.keyWidth/2,0).circle(0.999*self.keyWidth/2).extrude(self.windingKeyHeightFromPlate)

        #5mm shorter than the key as a bodge to stand off from the front plate
        keyHole = cq.Workplane("XY").moveTo(self.keyWidth/2,0).polygon(4, self.bearing.innerD - self.bearingWiggleRoom*2 + self.keyWiggleRoom).extrude(self.keyHoleDeep).translate((0, 0, self.windingKeyHandleThick + self.windingKeyHeightFromPlate - self.keyHoleDeep))

        key = key.cut(keyHole)

        return key


    def getWindingKnob(self):
        r = self.bearing.innerD/2

        screwLength = 30 - self.windingKeyHandleThick

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
        (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.getCordTurningInfo(cordLength)

        print("layers of cord: {}, cord per hour: {:.1f}cm to {:.1f}cm min diameter: {:.1f}mm".format(layers, (cordPerRotationPerLayer[-1] / minuteRatio) / 10, (cordPerRotationPerLayer[0] / minuteRatio) / 10, self.diameter))
        print("Cord used per layer: {}".format(cordPerLayer))
        #minute hand rotates once per hour, so this answer will be in hours
        return (rotations * minuteRatio)

    def getCordTurningInfo(self, cordLength=-1):
        '''
        returns (rotations, layers, cordPerRotationPerLayer, cordPerLayer)
        '''

        if cordLength < 0:
            cordLength = self.cordLength

        lengthSoFar = 0
        rotationsSoFar = 0
        coilsPerLayer = floor(self.thick / self.cordThick)
        cordPerLayer=[]
        layer = 0
        cordPerRotationPerLayer = []
        while lengthSoFar < cordLength:

            circumference = math.pi * (self.diameter + 2 * (layer * self.cordThick + self.cordThick / 2))
            cordPerRotationPerLayer.append(circumference)
            if lengthSoFar + circumference * coilsPerLayer < cordLength:
                # assume this whole layer is used
                lengthSoFar += circumference * coilsPerLayer
                rotationsSoFar += coilsPerLayer
                cordPerLayer.append(circumference * coilsPerLayer)
            else:
                # not all of this layer
                lengthLeft = cordLength - lengthSoFar
                rotationsSoFar += lengthLeft / circumference
                cordPerLayer.append(lengthLeft)
                break

            layer += 1
        return (rotationsSoFar, layer + 1, cordPerRotationPerLayer, cordPerLayer)


    def getTurnsForDrop(self, cordLength):


        return self.getCordTurningInfo(cordLength)[0]


    def getAssembled(self):

        model = self.getClickWheelForCord()
        if self.useKey:
            model = model.add(self.getSegment(False).translate((0,0,self.ratchet.thick + self.clickWheelExtra)))
            model = model.add(self.getCap(top=True).translate((0, 0, self.ratchet.thick + self.clickWheelExtra + self.thick + self.capThick)))
        else:
            model = model.add(self.getCap().translate((0, 0, self.ratchet.thick + self.clickWheelExtra)))
            model = model.add(self.getSegment(False).mirror().translate((0,0,self.thick + self.capThick)).translate((0,0,self.ratchet.thick + self.capThick + self.clickWheelExtra)))
            model = model.add(self.getSegment(True).mirror().translate((0,0,self.thick + self.capThick)).translate((0,0,self.ratchet.thick + self.clickWheelExtra + self.capThick + self.thick + self.capThick)))



        return model

    def getHeight(self):
        '''
        total height, once assembled

        NOTE = includes height of a washer as part of the cordwheel (if not using key)
        '''

        if self.useKey:
            return self.ratchet.thick + self.clickWheelExtra + self.beforeBearingExtraHeight + self.capThick + self.topCapThick + self.thick

        return self.ratchet.thick + self.clickWheelExtra + self.capThick*2 + self.topCapThick + self.thick*2 + WASHER_THICK

    def outputSTLs(self, name="clock", path="../out"):

        out = os.path.join(path, "{}_cordwheel_bottom_segment.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getSegment(False), out)

        if self.useKey:
            out = os.path.join(path, "{}_cordwheel_top_cap.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getCap(top=True), out)

            out = os.path.join(path, "{}_cordwheel_winder.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getWindingKey(), out)

            out = os.path.join(path, "{}_cordwheel_key.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getWindingKey(withKnob=False), out)

            out = os.path.join(path, "{}_cordwheel_winder_knob.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getWindingKnob(), out)
        else:
            # extra bits where the other cord coils up
            out = os.path.join(path, "{}_cordwheel_cap.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getCap(), out)

            out = os.path.join(path, "{}_cordwheel_top_segment.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getSegment(True), out)

        out = os.path.join(path, "{}_cordwheel_click.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getClickWheelForCord(), out)



class ChainWheel:
    '''
    This is a pocket chain wheel, printed in two parts.

    Works well for lighter (<1kg) weights, doesn't work reliably for heavier weights.

    Note it's fiddly to get the tolerance right, you want a larger tolerance value ot make it more reliable, but then you get a little 'clunk'
    every time a link leaves.

    This needs a ratchet, but the ratchet is generated in the GonigTrain and then set with setRatchet until I feel like refactoring this
    This whole thing really could do with an overhaul, but I don't expect to be using chains much in the future so it'll probably not happen

    '''

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 22

    def __init__(self, ratchet_thick=4, max_circumference=75, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15, holeD=3.5, screw=None, screwThreadLength=10, power_clockwise=True):
        '''
        0.2 tolerance worked but could be tighter
        Going for a pocket-chain-wheel as this should be easiest to print in two parts

        default chain is for the spare hubert hurr chain I've got and probably don't need (wire_thick=1.25, inside_length=6.8, width=5)
        '''
        self.type = PowerType.CHAIN
        self.looseOnRod = False
        self.holeD=holeD
        #complete absolute bodge!
        # self.rodMetricSize=math.floor(holeD)
        self.screw = screw
        if self.screw is None:
            self.screw = MachineScrew(metric_thread=2, countersunk=True)
        self.screwThreadLength=screwThreadLength

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

        self.inner_width = width*1.2

        self.hole_distance = self.diameter*0.275#*0.25

        self.hole_positions = [(0,-self.hole_distance), (0, self.hole_distance)]

        self.power_clockwise = power_clockwise

        ratchetOuterD = self.diameter * 2.5
        self.ratchet = Ratchet(totalD=ratchetOuterD, innerRadius=self.outerDiameter / 2, thick=ratchet_thick, power_clockwise=power_clockwise)

    def getTurnsForDrop(self, maxChainDrop):
        return maxChainDrop / self.circumference

    def getChainHoleD(self):
        #diameter of the hole in the bottom of the plate for the chain to dangle through
        return self.chain_width + 2

    def getChainPositionsFromTop(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

        zOffset = - WASHER_THICK - self.wall_thick - self.inner_width/2

        return [ [(-self.diameter / 2, zOffset)], [(self.diameter / 2, zOffset)] ]

    def getTurnsForDrop(self, chainDrop):
        return chainDrop / self.circumference

    def getHeight(self):
        '''
        Returns total height of the chain wheel, once assembled, including the ratchet
        includes washer as this is considered part of the full assembly
        '''
        return self.inner_width + self.wall_thick*2 + self.ratchet.thick + WASHER_THICK

    def getRunTime(self,minuteRatio=1,chainLength=2000):
        #minute hand rotates once per hour, so this answer will be in hours
        return chainLength/((self.pockets*self.chain_inside_length*2)/minuteRatio)

    def getHalf(self, sideWithClicks=False):
        '''
        I'm hoping to be able to keep both halves identical - so long as there's space for the m3 screws and the m3 pinion then this should remain possible
        both halves are identical if we're not using bearings
        '''

        halfWheel = cq.Workplane("XY")

        halfWheel = halfWheel.circle(self.outerDiameter / 2).extrude(self.wall_thick).faces(">Z").workplane().tag("inside")

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
        if sideWithClicks:
            # halfWheel = halfWheel.faces(">Z").workplane().moveTo(0,self.hole_distance).circle(self.screwD / 2).cutThruAll()
            # halfWheel = halfWheel.faces(">Z").workplane().moveTo(0,-self.hole_distance).circle(self.screwD / 2).cutThruAll()
            for holePos in self.hole_positions:
                halfWheel = halfWheel.faces(">Z").workplane().moveTo(holePos[0],holePos[1]).circle(self.screw.metric_thread / 2).cutThruAll()
                #half the height for a nut so the screw length can vary
                # halfWheel = halfWheel.cut(self.screw.getNutCutter(withBridging=True, height=(self.ratchet.thick + self.inner_width/2 + self.wall_thick)/2).translate(holePos))

        else:
            #screw holes
            for holePos in self.hole_positions:
                # half the height for a nut so the screw length can vary
                halfWheel = halfWheel.cut(self.screw.getCutter(withBridging=True).translate(holePos))

        return halfWheel

    def getWithRatchet(self, ratchet):


        chain =self.getHalf(True).translate((0, 0, ratchet.thick))

        clickwheel = ratchet.getInnerWheel()
        combined = clickwheel.add(chain)

        #holes for screws
        # clickwheel = clickwheel.faces(">Z").workplane().circle(self.holeD / 2).moveTo(0, self.hole_distance).circle(self.screwD / 2).moveTo(0, -self.hole_distance).circle(self.screwD / 2).cutThruAll()
        for holePos in self.hole_positions:
            combined = combined.faces(">Z").workplane().moveTo(holePos[0], holePos[1]).circle(self.screw.metric_thread / 2).cutThruAll()
            # #to nearest 2mm
            #
            # heightForScrew = self.getHeight()
            # if not self.screw.countersunk:
            #     heightForScrew-=self.screw.getHeadHeight()
            #
            # nearestScrewLength = round(heightForScrew/2)*2
            #TODO - work out best screw length and make nut holes only just as deep as they need.


            # half the height for a nut so the screw length can vary
            combined = combined.cut(self.screw.getNutCutter(withBridging=True, height=(self.ratchet.thick + self.inner_width/2 + self.wall_thick)/2).translate(holePos))

        combined = combined.faces(">Z").workplane().circle(self.holeD / 2).cutThruAll()


        # totalHeight=self.inner_width + self.wall_thick*2 + ratchet.thick
        #
        #if I don't have screws long enough, sink them further into the click bit
        # headDepth = self.screwD*METRIC_HEAD_DEPTH_MULT
        # if self.screwThreadLength + headDepth < totalHeight:
        #     headDepth +=totalHeight - (self.screwThreadLength + headDepth)
        #     print("extra head depth: ", headDepth)
        # else:
        #     print("need M{} screw of length {}mm".format(self.screwD, totalHeight-headDepth))
        #
        # #space for the heads of the screws
        # #general assumption: screw heads are double the diameter of the screw and the same depth as the screw diameter
        # screwHeadSpace = getHoleWithHole(self.screwD,self.screwD*2,headDepth).translate((0,self.hole_distance,0))
        # screwHeadSpace =  screwHeadSpace.add(getHoleWithHole(self.screwD, self.screwD * 2, headDepth).translate((0, -self.hole_distance, 0)))
        # return screwHeadSpace
        # combined = combined.cut(screwHeadSpace)



        return combined

    def printScrewLength(self):

        minScrewLength = self.getHeight() - (self.ratchet.thick + self.inner_width/2 + self.wall_thick)/2 - self.screw.getNutHeight()
        print("Chain wheel screws: {} max length {}mm min length {}mm".format(self.screw.getString(), self.getHeight(), minScrewLength))


    def getAssembled(self):



        assembly = self.getWithRatchet(self.ratchet)

        chainWheelTop = self.getHalf().rotate((0,0,0),(1,0,0),180).translate((0, 0, self.getHeight() - WASHER_THICK))

        return assembly.add(chainWheelTop)

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

    def __init__(self, totalD=50, thick=5, power_clockwise=True, innerRadius=0, outer_thick=5):

        self.outsideDiameter=totalD

        self.outer_thick = outer_thick
        if self.outer_thick < 0:
            self.outer_thick = self.outsideDiameter*0.1



        self.clickInnerDiameter = self.outsideDiameter * 0.5
        if innerRadius == 0:
            self.clickInnerRadius = self.clickInnerDiameter / 2
        else:
            self.clickInnerRadius = innerRadius

        self.anticlockwise = -1 if power_clockwise else 1

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
        #since the clicks are at such an angle, this is a bodge to ensure they're actually that thick, rather than that thick at teh base
        #mostly affects ratchets with a larger inner radius and a not-so-large outer radius
        #TODO proper maffs
        innerThick=thick*2

        innerClickR = self.clickInnerRadius

        #arc aprox ratchetThick
        clickArcAngle = self.anticlockwise * thick / innerClickR
        clickInnerArcAngle = self.anticlockwise * innerThick / innerClickR
        clickOffsetAngle = -(math.pi*2/self.clicks)*1 * self.anticlockwise

        dA = -math.pi*2 / self.clicks * self.anticlockwise

        start = polar(clickOffsetAngle, innerClickR)
        wheel = wheel.moveTo(start[0], start[1])

        outerR = self.toothRadius
        innerR = self.toothRadius-thick


        for i in range(self.clicks):
            toothAngle = dA * i
            clickStartAngle = dA * i + clickOffsetAngle
            clickEndAngle = clickStartAngle - clickInnerArcAngle#clickArcAngle
            clickNextStartAngle = clickStartAngle + dA

            clickTip = polar(toothAngle, self.toothRadius)
            toothInner = polar(toothAngle-self.toothAngle, self.toothTipR)
            tipToInner = np.subtract(toothInner, clickTip)
            clickInner = tuple(np.add(clickTip, np.multiply(tipToInner, thick/np.linalg.norm(tipToInner))))

            clickStart = polar(clickStartAngle, innerClickR)
            clickEnd = polar(clickEndAngle, innerClickR)
            nextClickStart = polar(clickNextStartAngle, innerClickR)

            wheel = wheel.radiusArc(clickInner, -innerR * self.anticlockwise).lineTo(clickTip[0], clickTip[1]).radiusArc(clickEnd, outerR * self.anticlockwise).\
                radiusArc(nextClickStart, innerClickR * self.anticlockwise)


        wheel = wheel.close().extrude(self.thick)

        return wheel

    def getOuterWheel(self, extraThick=0, thick=0):
        '''
        contains the ratchet teeth, designed so it can be printed as part of the same object as a gear wheel
        extrathicnkess can be added (useful for embedding inside the chain wheel)
        if thick is provided this overrides the expected thickness
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

        totalThick = self.thick + extraThick
        if thick > 0:
            totalThick = thick

        wheel = wheel.close().extrude(totalThick)


        return wheel
