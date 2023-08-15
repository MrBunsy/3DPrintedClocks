'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
import math
import numpy as np

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
    def __init__(self, diameter, height, twoParts=True, holeD=5, solidBottom=False):
        #internal diameter
        self.diameter=diameter
        self.height = height
        self.wallThick=0.875#0.45
        #if True then (probably because it's too tall...) print in two sections that slot over top and bottom
        self.twoParts=twoParts
        self.holeD=holeD
        #if false, the bottom also has a hole to screw into the bottom of the weight
        self.solidBottom=solidBottom

        self.outerR = self.diameter / 2 + self.wallThick

    def getShell(self, top=True):
        shell = cq.Workplane("XY")

        height = self.height
        overlap = 3
        if self.twoParts:
            height=height/2 - overlap/2

        shell = shell.circle(self.outerR).circle(self.holeD/2).extrude(self.wallThick)
        shell = shell.faces(">Z").workplane().circle(self.outerR).circle(self.diameter/2).extrude(height+self.wallThick)

        if self.twoParts:
            if top:
                shell = shell.faces(">Z").workplane().circle(self.outerR).circle(self.outerR - self.wallThick/2).extrude(overlap)
            else:
                shell = shell.faces(">Z").workplane().circle(self.outerR - self.wallThick / 2).circle(self.outerR - self.wallThick).extrude(overlap)

        return shell

    def getLid(self):
        lid = cq.Workplane("XY").circle(self.outerR)

        if self.solidBottom:
            lid =  cq.Workplane("XY").circle(self.outerR-self.wallThick/2 - 0.2)
        else:
            lid = lid.circle(self.holeD / 2)
        lid = lid.extrude(self.wallThick)

        return lid

    def outputSTLs(self, name="clock", path="../out"):

        out = os.path.join(path, "{}_weight_shell_top.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getShell(True), out)
        if self.twoParts:
            out = os.path.join(path, "{}_weight_shell_bottom.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getShell(False), out)
        else:
            out = os.path.join(path, "{}_weight_lid.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getLid(), out)



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


class LightweightPulley:
    '''
    This uses steel pipe or just plastic straight onto a threaded rod.
    Intended to have the pulley print in one peice and be usable by chain or rope

    By sheer fluke the first design fits with 25mm countersunk M3 screws
    TODO deliberately match up design with screw lengths
    '''

    def __init__(self, diameter,rope_diameter=4, screws = None, use_steel_rod=True):
        self.diameter=diameter
        self.rope_diameter=rope_diameter
        self.screws = screws

        if self.screws is None:
            self.screws = MachineScrew(3, countersunk=True)
        self.wall_thick=1
        self.slope_angle = math.pi / 3
        #just made up - might be nice to do some maths to check that the rope/chain will fit nicely with the chosen slope
        self.centre_wide = self.rope_diameter/2
        self.use_steel_rod = use_steel_rod

        self.hole_d = STEEL_TUBE_DIAMETER if self.use_steel_rod else self.screws.metric_thread + LOOSE_FIT_ON_ROD

        self.gap_size = WASHER_THICK_M3 + 0.5

        self.holder_thick=5
        self.holder_wide = self.screws.metric_thread*2.5

        self.axle_holder_r = self.screws.metric_thread*2

        '''
        wall_thick at edges
        rope_diameter/4 in centre (just a wild guess to see what it looks like)
        __     __
        | \___/ |   rope_diameter tall gap, 45deg slopes
        |       |
        
        
        |\
        | \  length of the slope = self.rope_diameter/sin(slope_angle)  
        |  \
        '''
        self.slope_length = self.rope_diameter / math.sin(self.slope_angle)


        self.wheel_thick = self.wall_thick*2 + math.cos(self.slope_angle)*self.slope_length*2 + self.centre_wide

        #using a cuckoo hook
        self.hook_inner_r = 9/2
        self.hook_thick = 1
        print(self)

    def get_wheel(self):
        circle = cq.Workplane("XY").circle(self.diameter / 2 + self.rope_diameter/2)
        '''
        _____
            |
           /
          /
        |
        |
        \
         \
          \
        ___|
        '''
        wheel_outline = cq.Workplane("XZ").moveTo(0,0).lineTo(self.diameter/2 + self.rope_diameter/2, 0).line(0, self.wall_thick).lineTo(self.diameter/2 - self.rope_diameter/2, self.wall_thick + math.cos(self.slope_angle)*self.slope_length)\
            .line(0, self.centre_wide).lineTo(self.diameter/2 + self.rope_diameter/2, self.wheel_thick - self.wall_thick).line(0, self.wall_thick).lineTo(0, self.wheel_thick).close()

        wheel = wheel_outline.sweep(circle)

        wheel = wheel.cut(cq.Workplane("XY").circle(self.hole_d/2).extrude(self.wheel_thick))

        return wheel

    def get_holder_half(self, left=True):
        holder = cq.Workplane("XY").tag("base")

        centre_to_centre = self.diameter/2 + self.rope_diameter + self.holder_wide/2

        holder = holder.moveTo(0,-centre_to_centre/2).rect(self.holder_wide,centre_to_centre).extrude(self.holder_thick)
        holder = holder.workplaneFromTagged("base").moveTo(0,0).circle(self.axle_holder_r).extrude(self.holder_thick)
        holder = holder.workplaneFromTagged("base").moveTo(0, -centre_to_centre).circle(self.axle_holder_r).extrude(self.holder_thick)
        holder = holder.workplaneFromTagged("base").moveTo(0, -centre_to_centre).circle(self.holder_wide/2).extrude(self.get_total_thickness()/2)#-self.hook_thick/2)
        # holder = holder.workplaneFromTagged("base").moveTo(0, -centre_to_centre).circle(self.hook_inner_r).extrude(self.get_total_thickness()/2)

        #add a notch for the cuckoo hook to rest in
        hook_cutter = cq.Workplane("XY").circle(100).circle(self.hook_inner_r).extrude(self.hook_thick).translate((0,-centre_to_centre - self.hook_inner_r + self.screws.metric_thread/2,self.get_total_thickness()/2 - self.hook_thick/2))

        holder = holder.cut(hook_cutter)

        screw_positions = [(0,0), (0, -centre_to_centre)]
        upright = left
        for pos in screw_positions:
            screw_cutter = self.screws.getCutter(withBridging=True)
            if upright:
                screw_cutter = screw_cutter.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, self.get_total_thickness()))
                screw_cutter = screw_cutter.add(self.screws.getNutCutter(nyloc=True, withBridging=True))

            holder = holder.cut(screw_cutter.translate(pos))

            upright = not upright

        return holder

    def get_total_thickness(self):
        return self.holder_thick*2 + self.gap_size*2 + self.wheel_thick

    def getTotalThick(self):
        return self.get_total_thickness()

    def getAssembled(self):

        wheel_base_z = self.holder_thick + self.gap_size

        wheel = self.get_wheel().translate((0,0,wheel_base_z))

        pulley = wheel.add(self.get_holder_half(True)).add(self.get_holder_half(False).rotate((0,0,0), (0,1,0), 180).translate((0,0,self.get_total_thickness())))

        return pulley

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_lightweight_pulley_wheel.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_wheel(), out)

        out = os.path.join(path, "{}_lightweight_pulley_holder_a.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_holder_half(True), out)

        out = os.path.join(path, "{}_lightweight_pulley_holder_b.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_holder_half(False), out)

class BearingPulley:
    '''
    Pulley wheel that can be re-used by all sorts of other things
    This is pretty heavy duty and uses a bearing to avoid friction
    '''

    def __init__(self, diameter, cordDiameter=2.2, rodMetricSize=4, wheel_screws = None, hook_screws=None, screw_count=4, vShaped=False, style=None, bearing=None, bearingHolderThick=0.8):
        self.diameter=diameter
        self.cordDiameter=cordDiameter
        self.vShaped=vShaped

        self.style=style

        #if negative, don't punch holes
        self.rodMetricSize=rodMetricSize
        #only used if bearing is not provided
        self.rodHoleD = rodMetricSize + LOOSE_FIT_ON_ROD
        #screws which hold the two halves of the pulley wheel together
        self.screws = wheel_screws
        if self.screws is None:
            self.screws = MachineScrew(2, countersunk=True)

        self.hook_screws = hook_screws
        if self.hook_screws is None:
            self.hook_screws = MachineScrew(4, countersunk=True)

        # self.hook_screws =

        self.edgeThick=cordDiameter*0.5
        self.taperThick = cordDiameter * 0.2
        #if not none, a BearingInfo for a bearing instead of a rod
        self.bearing=bearing
        self.bearingHolderThick=bearingHolderThick


        self.screwPositions=[polar(angle,diameter*0.35) for angle in [i*math.pi*2/screw_count for i in range(screw_count)]]



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
        totalThick = self.getTotalThick()
        if totalThick < self.screws.getTotalLength():
            print("Not thick ({}) enough to fit screw of length {}".format(totalThick, self.screws.getTotalLength()))
            #make it thick enough to fit the screw in, with a little bit of spare
            extra_thick_needed = (self.screws.getTotalLength() - totalThick) + 0.5
            self.edgeThick += extra_thick_needed/2
            self.bearingHolderThick += extra_thick_needed/2

        self.hookThick = 6
        self.hookBottomGap = 3
        self.hookSideGap = 1

        self.hookWide = 16
        #using a metal cuckoo chain hook to hold the weight, hoping it can stand up to 4kg (it can, last clock has been going for months)
        self.cuckooHookOuterD=14#13.2
        self.cuckooHookThick = 1.2#0.9

    def getTotalThick(self):
        '''
        thickness of just the pulley wheel
        '''
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
        print("pulley, bearing", self.bearing)
        if self.bearing is not None:
            print("self.bearingHolderThick",self.bearingHolderThick)
            hole = hole.translate((0,0,self.bearingHolderThick))
            hole = hole.add(cq.Workplane("XY").circle(self.bearing.outerSafeD/2).extrude(1000))

        pulley = pulley.cut(hole)

        screwHoles = cq.Workplane("XY")

        for screwPos in self.screwPositions:


            if top:
               screwHoles = screwHoles.add(self.screws.getCutter(withBridging=True).translate(screwPos))
            else:
                screwHoles = screwHoles.add(self.screws.getNutCutter(withBridging=True, withScrewLength=1000).translate(screwPos))

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

        length = self.getHookTotalThick()

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

    def printInfo(self):
        print("pulley needs screws {} {}mm and {} {}mm".format(self.screws, self.getTotalThick(), self.hook_screws, self.getHookTotalThick()))

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
    def __init__(self, height=7.5, hook_height = -1, thick = 0.32, loop_end=True, barrel_diameter=50):
        self.height=height
        if hook_height < 0:
            hook_height = height / 3
        self.hook_height = hook_height
        self.thick=thick
        self.loop_end=loop_end
        self.barrel_diameter = barrel_diameter


class SpringArbour:
    '''
    not taking this design further, attempting springs with SpringBarrel
    '''

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

    def getEncasingRadius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        return 30

    def __init__(self):
        #diameter/circumference for the path the rope or chain takes. For the cord, this is the minimum diameter for the first layer of coils
        self.diameter=30
        self.circumference=math.pi * self.diameter
        self.ratchet = Ratchet()
        self.type = PowerType.NOT_CONFIGURED
        #if false, the powered wheel is fixed to the rod and the gear wheel is loose.
        self.looseOnRod = False
        self.arbour_d = 3

    def getChainHoleD(self):
        '''
        Returns diameter of hole for the rope/chain/cord to pass through. It needs a hole to prevent winding the weight up too far
        '''

    def isClockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
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

    def getScrewPositions(self):
        '''
        return list of (x,y) positions, relative to the arbour, for screws that hold this wheel together.
        Only really relevant for ones in two halves, like chain and rope
        Used when we're not using a ratchet so the screwholes can line up with holes in the wheel
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

    first attempt tried using "teeth" to grip the rope. It worked, but added a lot of friction and chewed up teh rope.
    I've had a lot of success at retrofitting wheels with o-rings, so I want to try designing a wheel around using o-rings

    This is now based on the lightweight pully - printed in one peice with a hole for a steel tube in the centre
    '''

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 20

    def __init__(self, diameter, ratchet_thick, hole_d=STEEL_TUBE_DIAMETER, screw=None, rope_diameter=2.2, wall_thick=1, power_clockwise=True,
                 o_ring_diameter=3, arbour_d=3, use_o_rings=1, ratchet_outer_d=-1, ratchet_outer_thick=5, need_bearing_standoff=False):

        #diameter for the rope
        self.diameter=diameter
        self.circumference = math.pi*diameter

        #note, this actually has no effect on anything at the moment and is only for maintaining interface with other powered wheels
        self.looseOnRod = True
        self.type = PowerType.ROPE

        self.need_bearing_standoff = need_bearing_standoff

        self.slope_angle = math.pi / 4
        self.rope_diameter = rope_diameter
        self.o_ring_diameter = o_ring_diameter
        self.use_o_rings = use_o_rings

        self.centre_wide = self.o_ring_diameter*self.use_o_rings

        self.wall_thick = wall_thick
        self.arbour_d = arbour_d

        '''
        |\
        | \  length of the slope (the hypotenuse) = self.rope_diameter/sin(slope_angle)  
        |  \
        
        height of rope_diameter
        '''
        self.outer_diameter = self.diameter + rope_diameter
        self.slope_length = self.rope_diameter / math.sin(self.slope_angle)

        #standoff from bearing
        self.bearing_standoff_thick = 0.5
        if not self.need_bearing_standoff:
            self.bearing_standoff_thick = 0

        self.wheel_thick = self.wall_thick*2 + math.cos(self.slope_angle)*self.slope_length*2 + self.centre_wide


        perpendicular_distance_from_centre_of_rope_to_centre_of_o_rings = math.sqrt((o_ring_diameter + rope_diameter) ** 2 - o_ring_diameter ** 2)

        #nominal diameter of the centre of the o-rings
        self.inner_diameter = diameter - perpendicular_distance_from_centre_of_rope_to_centre_of_o_rings

        self.power_clockwise = power_clockwise
        self.hole_d = hole_d
        self.screw = screw
        if self.screw is None:
            self.screw = MachineScrew(2)


        if ratchet_outer_d < 0:
            ratchet_outer_d = self.outer_diameter+Ratchet.APROX_EXTRA_RADIUS_NEEDED*2
        self.ratchet_thick = ratchet_thick
        if ratchet_thick > 0:
            self.ratchet = Ratchet(thick=ratchet_thick, totalD=ratchet_outer_d, innerRadius=self.outer_diameter/2, power_clockwise=power_clockwise, outer_thick=ratchet_outer_thick)
        else:
            self.ratchet = None

        print("rope wheel needs steel pipe of length {}mm".format(self.wheel_thick + self.bearing_standoff_thick))

    def getScrewPositions(self):
        '''
        acn be printed in one peice, but still might want screw positions if we're being bolted to a wheel (eg huygen's)
        '''
        print("TODO screw positions for single-peice rope wheel")
        return []

    def isClockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
        '''
        return self.power_clockwise

    def getEncasingRadius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        if self.ratchet is not None:
            return self.ratchet.outsideDiameter/2
        else:
            return self.outer_diameter/2

    def printScrewLength(self):
        if self.screw.countersunk:
            screwLength = self.getHeight() - WASHER_THICK_M3
        else:
            screwLength = self.getHeight() - WASHER_THICK_M3 - self.screw.getHeadHeight()
        #nut hole is extra deep by thickness of the ratchet
        print("RopeWheel needs: {} screw length {}-{}".format(self.screw.getString(), screwLength, screwLength-self.ratchet_thick))

    def getTurnsForDrop(self, maxChainDrop):
        return maxChainDrop/self.circumference

    def getChainHoleD(self):
        return self.rope_diameter + 4
    #
    # def getHalf(self, top=False):
    #     radius = self.inner_diameter / 2 - self.rope_thick / 2
    #
    #
    #
    #     # from the side
    #     bottomPos = (radius + self.extra_rim, 0)
    #     topOfEdgePos = (radius + self.extra_rim, self.wall_thick)
    #     middlePos = (radius, self.wall_thick + self.gulley_wide / 2)
    #
    #     circle = cq.Workplane("XY").circle(self.inner_diameter / 2)
    #     ropeWheel = cq.Workplane("XZ").moveTo(bottomPos[0], bottomPos[1]).lineTo(topOfEdgePos[0], topOfEdgePos[1]).lineTo(middlePos[0], middlePos[1])
    #
    #
    #     ropeWheel = ropeWheel.lineTo(0, middlePos[1]).lineTo(0, 0).close().sweep(circle)
    #
    #     offset = 0 if top else 0.5*math.pi*2/self.nibs
    #     nibOuterOuterX = radius + self.extra_rim * 0.95
    #     nibOuterX= radius + self.extra_rim * 0.9
    #     nibInnerX = radius + self.extra_rim * 0.4
    #     nibStart = radius*0.9
    #     nibEdgeHeight = self.wall_thick + self.gulley_wide * 0.25
    #     nibMiddleHeight = self.wall_thick + self.gulley_wide * 0.5
    #     for i in range(self.nibs):
    #         angle = i*math.pi*2/self.nibs + offset
    #
    #         nib = cq.Workplane("XZ").moveTo(nibStart, self.wall_thick).lineTo(nibOuterOuterX, self.wall_thick).lineTo(nibOuterX, nibEdgeHeight).lineTo(nibInnerX, nibMiddleHeight).lineTo(nibStart, nibMiddleHeight).close().extrude(self.nibThick).translate((0, self.nibThick / 2, 0))
    #         # return nib
    #         ropeWheel = ropeWheel.add(nib.rotate((0,0,0), (0,0,1), radToDeg(angle)))
    #
    #
    #
    #
    #     if not top:
    #         ropeWheel = ropeWheel.translate((0,0,self.ratchet.thick)).add(self.ratchet.getInnerWheel())
    #
    #     holeD = self.rodD
    #     # pulley = pulley.faces(">Z").workplane().circle(holeD/2).cutThroughAll()
    #     hole = cq.Workplane("XY").circle(holeD / 2).extrude(1000)
    #
    #     ropeWheel = ropeWheel.cut(hole)
    #
    #
    #
    #     for pos in self.screw_positions:
    #         if not top:
    #             #have a bigger hole than needed for the nut in the ratchet side, so we can get away with shorter screws
    #             cutter = self.screw.getNutCutter(withScrewLength=100, withBridging=True, height=self.ratchet.thick + self.screw.getNutHeight()).rotate((0,0,0),(0,0,1),360/12)
    #         else:
    #             cutter = self.screw.getCutter(withBridging=True)
    #
    #         ropeWheel = ropeWheel.cut(cutter.translate(pos))
    #
    #     return ropeWheel

    def get_wheel(self):
        '''
        get the wheel (without ratchet)
        This is based on the lightweight pulley, but with two slots to hold o-rings
        '''

        circle = cq.Workplane("XY").circle(self.diameter / 2)
        '''
        ____
           |
          /
         /
        (
        (
         \
          \
           \
        ___|
        '''

        slope_width = math.cos(self.slope_angle) * self.slope_length

        wheel_outline = cq.Workplane("XZ").moveTo(0, 0).lineTo(self.outer_diameter/2, 0).line(0, self.wall_thick).lineTo(self.inner_diameter/2, self.wall_thick + slope_width)


        for o in range(self.use_o_rings):
            end_point = (self.inner_diameter/2, self.wall_thick + slope_width + self.o_ring_diameter * (o+1))
            # wheel_outline = wheel_outline.radiusArc(end_point, self.o_ring_diameter/2)
            #expecting o-ring to be slightly squashed, and this will hopefully help it print better
            wheel_outline = wheel_outline.sagittaArc(end_point, self.o_ring_diameter*0.4)
            # wheel_outline = wheel_outline.lineTo(end_point[0], end_point[1])

        wheel_outline = wheel_outline.lineTo(self.outer_diameter / 2, self.wheel_thick - self.wall_thick).line(0, self.wall_thick).lineTo(0, self.wheel_thick).close()

        wheel = wheel_outline.sweep(circle)

        wheel = wheel.cut(cq.Workplane("XY").circle(self.hole_d / 2).extrude(self.wheel_thick))

        bearing_inner_safe_d = getBearingInfo(self.arbour_d).innerSafeD

        if self.bearing_standoff_thick > 0 and bearing_inner_safe_d > self.hole_d:
            wheel = wheel.add(cq.Workplane("XY").circle(bearing_inner_safe_d/2).circle(self.hole_d/2).extrude(self.bearing_standoff_thick).translate((0,0,self.wheel_thick)))



        return wheel

    def get_wheel_with_ratchet(self):
        wheel = self.get_wheel().translate((0, 0, self.ratchet.thick)).add(self.ratchet.getInnerWheel())

        wheel = wheel.cut(cq.Workplane("XY").circle(self.hole_d/2).extrude(self.getHeight()))



        return wheel


    def getAssembled(self):
        if self.ratchet is not None:
            return self.get_wheel_with_ratchet()
        else:
            return self.get_wheel()

    def getHeight(self):
        return self.wheel_thick + self.bearing_standoff_thick + self.ratchet_thick

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path,"{}_rope_wheel.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getAssembled(), out)

    def getChainPositionsFromTop(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

        zOffset = -(self.wheel_thick)/2 - self.bearing_standoff_thick
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

    def __init__(self,  diameter, ratchet_thick=4, power_clockwise=True, rodMetricSize=3, thick=10, useKey=False, screwThreadMetric=3, cordThick=2, bearing=None, keySquareBitHeight=30,
                 gearThick=5, frontPlateThick=8, style="HAC", cordLength=2000, looseOnRod=True, cap_diameter=-1):
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
        if cap_diameter < 0:
            self.cap_diameter = diameter + 30#diameter*2#.5
        else:
            self.cap_diameter = cap_diameter
        self.rodMetricSize = rodMetricSize
        self.arbour_d = rodMetricSize
        self.holeD = rodMetricSize
        self.looseOnRod = looseOnRod

        if self.looseOnRod:
            self.holeD += LOOSE_FIT_ON_ROD

        self.screwThreadMetric=screwThreadMetric

        '''
        measurements for the 15mm inner diameter bearing, needs the extra outer d so it's not too tight a fit - since it's plastic I don't want it squashed in like the metal ones
        since I fear that might increase friction
        bearingInnerD=15, bearingHeight=5, bearingLip=2.5, bearingOuterD=24.2,
        '''

        if bearing is None:
            bearing = getBearingInfo(15)

        #only if useKey is true will this be used
        self.bearing = bearing
        print("cord wheel bearing:{}".format(self.bearing))
        # extra radius to subtract from the bit that goes through the large bearing for a key
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
        self.clickWheelStandoffHeight=LAYER_THICK

        if ratchet_thick <=0:
            raise ValueError("Cannot make cord wheel without a ratchet")

        #inner radius slightly larger than cord diameter so there's space for nuts
        self.ratchet = Ratchet(totalD=self.cap_diameter, thick=ratchet_thick, power_clockwise=power_clockwise, innerRadius=self.diameter / 2 + 2)
        self.keyScrewHoleD = self.screwThreadMetric
        self.power_clockwise = power_clockwise
        self.keyWiggleRoom = 0.75

        #slowly switch over to using this
        self.fixingScrew = MachineScrew(self.screwThreadMetric, countersunk=True)

        if self.useKey:
            self.keyWallThick = 2.5
            # enough to cut out the key itself
            self.keyWidth = self.keyWallThick * 2 + self.bearing.innerD
            #this is the length of the handle of the key if it's knob-type (needs to be short enough that it won't bump into the motion works, or else windingKeyHeightFromPlate needs to be
            #long enough that we're above the motion works)
            self.defaultWindingKeyHandleLength = 30,
            #this is how far from the front of the clock the winding handle of the key will be
            self.defaultWindingKeyHeightFromPlate = 70,
            #thickness of the handle
            self.windingKeyHandleThick = 5
            self.keyHoleDeep = self.keySquareBitHeight - 5

    def isClockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
        '''
        return self.power_clockwise

    def getEncasingRadius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        return self.ratchet.outsideDiameter/2

    def getScrewPositions(self):
        return self.fixingPoints

    def printScrewLength(self):
        if self.useKey:
            minScrewLength = self.ratchet.thick/2 + self.capThick + self.topCapThick + self.thick
            print("cord wheel screw (m{}) length between".format(self.screwThreadMetric), minScrewLength, minScrewLength + self.ratchet.thick/2)
        else:
            # two sections, one for winding up while the other winds down
            minScrewLength = self.ratchet.thick - (getScrewHeadHeight(self.screwThreadMetric) + LAYER_THICK) + self.clickWheelStandoffHeight + self.capThick + self.topCapThick + self.thick * 1.5
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
            weightSegmentBottomZ = - WASHER_THICK_M3 - self.topCapThick - self.thick - self.capThick - self.thick
            weightSegmentTopZ = - WASHER_THICK_M3 - self.topCapThick - self.thick - self.capThick
            windSegmentBottomZ = - WASHER_THICK_M3 - self.topCapThick - self.thick
            windSegmentTopZ = - WASHER_THICK_M3 - self.topCapThick

            if self.ratchet.isClockwise():
                weightSide = 1
            else:
                weightSide = -1
            return [ [ (chainX*weightSide, weightSegmentTopZ), (chainX*weightSide, weightSegmentBottomZ) ], [(chainX*weightSide*(-1), windSegmentTopZ), (chainX*weightSide*(-1), windSegmentBottomZ)] ]


    def getNutHoles(self):

        #rotate by 1/12th so there's a tiny bit more space near the main hole
        cutter = cq.Workplane("XY").add(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).rotate((0,0,0),(0,0,1),360/12).translate(self.fixingPoints[0]))
        cutter = cutter.union(getHoleWithHole(self.screwThreadMetric, getNutContainingDiameter(self.screwThreadMetric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).rotate((0,0,0),(0,0,1),360/12).translate(self.fixingPoints[1]))
        return cutter

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
            segment = segment.union(key.rotate((0,0,0),(0,0,1),45).translate((0,0,self.capThick + self.thick + self.bearing.bearingHeight + self.beforeBearingExtraHeight + self.topCapThick)))



            if self.topCapOverlap > 0 and not front:
                #overlapping slot
                overlap = cq.Workplane("XY").circle(self.diameter / 2).circle(self.diameter / 2 - self.overlapSlotWide).extrude(self.topCapOverlap)
                segment = segment.union(overlap.translate((0,0, self.capThick + self.thick)))

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
        if cordHoleR < 1.5:
            cordHoleR = 1.5
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
        cap = cq.Workplane("XY").circle(self.cap_diameter / 2).extrude(capThick + extraThick)

        holeR = self.holeD / 2
        if self.useKey and top:
            holeR = self.bearing.innerD/2 + self.bearingWiggleRoom
            print("cord wheel cap holeR: {} innerSafe raduis:{}".format(holeR,self.bearing.innerSafeD/2))
            #add small ring to keep this further away from the bearing
            cap = cap.faces(">Z").workplane().circle(holeR).circle(self.bearing.innerSafeD/2).extrude(self.beforeBearingExtraHeight)
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
        cap = Gear.cutStyle(cap, self.cap_diameter / 2 - self.holeD * 0.75, innerRadius=self.diameter / 2 + self.cordThick, style=self.style, clockwise_from_pinion_side=self.power_clockwise)
        return cap

    def getClickWheelForCord(self, for_printing=True):

        '''
        Standalone clickwheel with holes for either screw heads or nuts.
        can't flip upside down for printing as there's a bit of extra height (clickWheelStandoffHeight) to keep the clicks away from the cap on top
        '''

        clickwheel = self.ratchet.getInnerWheel()

        clickwheel = clickwheel.faces(">Z").workplane().circle(self.ratchet.clickInnerRadius*0.999).extrude(self.clickWheelStandoffHeight)

        # hole for the rod
        clickwheel = clickwheel.cut(cq.Workplane("XY").circle(self.holeD / 2).extrude(self.thick*2))
        cutter = cq.Workplane("XY")
        if self.useKey:
            #space for a nut
            for fixingPoint in self.fixingPoints:
                cutter = cutter.add(self.fixingScrew.getNutCutter(height=self.ratchet.thick/2, withBridging=True, withScrewLength=1000).translate(fixingPoint))
        else:
            #cut out space for screwheads
            for fixingPoint in self.fixingPoints:
                cutter = cutter.add(self.fixingScrew.getCutter(withBridging=True).translate(fixingPoint))
        clickwheel = clickwheel.cut(cutter)

        return clickwheel

    def getWindingKey(self, withKnob=True, cylinder_length=-1, handle_length=-1, for_printing=True, key_hole_deep=-1):
        '''
        winding key! this is one with a little arm and handle

        handle_length is to the end of the handle, not the middle of the knob (makes calculating the size of the key easier)

        Exact size of the key is based on the bearing and tolerance:
        key = cq.Workplane("XY").polygon(4, self.bearingInnerD - self.bearingWiggleRoom*2).extrude(self.keyKnobHeight)

        if withKnob, it's like an old longcase key with handle. If not, it's like a mantle key

        TODO - make Key a separate class and then it can have the cordwheel fed into it, controlled by something else
        '''

        if cylinder_length < 0:
            cylinder_length = self.defaultWindingKeyHeightFromPlate

        if handle_length < 0:
            handle_length = self.defaultWindingKeyHandleLength
        if key_hole_deep < 0:
            key_hole_deep = self.keyHoleDeep

        if withKnob:
            #base for handle
            key = cq.Workplane("XY").radiusArc((self.keyWidth,0),-self.keyWidth/2).lineTo(self.keyWidth, handle_length -self.keyWidth/2).radiusArc((0, handle_length-self.keyWidth/2), -self.keyWidth / 2).close().extrude(self.windingKeyHandleThick)
            # hole to screw in the knob (loose)
            key = key.faces(">Z").workplane().tag("top").moveTo(self.keyWidth / 2, handle_length-self.keyWidth/2).circle(self.screwThreadMetric / 2 + 0.2).cutThruAll()
        else:
            key = cq.Workplane("XY").tag("top")

            keyGripTall = min(cylinder_length * 0.3, 15)
            keyGripWide = self.keyWidth*2.5

            # grippyBit = cq.Workplane("XZ").rect(keyGripWide,keyGripTall).extrude(self.keyWallThick)
            r=keyGripWide*0.1

            grippyBit = cq.Workplane("XZ").lineTo(keyGripWide/2,0).lineTo(keyGripWide/2,keyGripTall).tangentArcPoint((-r,r*1.25))\
                .tangentArcPoint((0,keyGripTall),relative=False).mirrorY().extrude(self.windingKeyHandleThick)
            # return grippyBit
            key = key.union(grippyBit.translate((self.keyWidth / 2, self.windingKeyHandleThick / 2, 0)))



        #key bit
        key = key.workplaneFromTagged("top").moveTo(self.keyWidth/2,0).circle(0.999*self.keyWidth/2).extrude(cylinder_length)

        if key_hole_deep > cylinder_length:
            key_hole_deep = cylinder_length

        #5mm shorter than the key as a bodge to stand off from the front plate
        keyHole = cq.Workplane("XY").moveTo(self.keyWidth/2,0).polygon(4, self.bearing.innerD - self.bearingWiggleRoom*2 + self.keyWiggleRoom).extrude(key_hole_deep).translate((0, 0, self.windingKeyHandleThick + cylinder_length - key_hole_deep))

        key = key.cut(keyHole)

        if not for_printing:
            # for the model
            key = key.translate((-self.keyWidth/2,0))
            key = key.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0,0,0), (0,0,1),180).translate((0, 0, cylinder_length + self.windingKeyHandleThick))
            key = key.add(self.getWindingKnob().translate((0,handle_length - self.keyWidth/2,cylinder_length + self.windingKeyHandleThick)))

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

        model = self.getClickWheelForCord(for_printing=False)
        if self.useKey:
            model = model.add(self.getSegment(False).translate((0,0,self.ratchet.thick + self.clickWheelStandoffHeight)))
            model = model.add(self.getCap(top=True).translate((0, 0, self.ratchet.thick + self.clickWheelStandoffHeight + self.thick + self.capThick)))
        else:
            model = model.add(self.getCap().translate((0, 0, self.ratchet.thick + self.clickWheelStandoffHeight)))
            model = model.add(self.getSegment(False).mirror().translate((0,0,self.thick + self.capThick)).translate((0,0,self.ratchet.thick + self.capThick + self.clickWheelStandoffHeight)))
            model = model.add(self.getSegment(True).mirror().translate((0,0,self.thick + self.capThick)).translate((0, 0, self.ratchet.thick + self.clickWheelStandoffHeight + self.capThick + self.thick + self.capThick)))



        return model

    def getHeight(self):
        '''
        total height, once assembled

        NOTE = includes height of a washer as part of the cordwheel (if not using key)
        '''

        if self.useKey:
            return self.ratchet.thick + self.clickWheelStandoffHeight + self.beforeBearingExtraHeight + self.capThick + self.topCapThick + self.thick

        return self.ratchet.thick + self.clickWheelStandoffHeight + self.capThick * 2 + self.topCapThick + self.thick * 2 + WASHER_THICK_M3

    def outputSTLs(self, name="clock", path="../out"):

        out = os.path.join(path, "{}_cordwheel_bottom_segment.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getSegment(False), out)

        if self.useKey:
            out = os.path.join(path, "{}_cordwheel_top_cap.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getCap(top=True), out)

            #exported by plates once it knows what size the key should be
            # out = os.path.join(path, "{}_cordwheel_winder.stl".format(name))
            # print("Outputting ", out)
            # exporters.export(self.getWindingKey(), out)
            #
            # out = os.path.join(path, "{}_cordwheel_key.stl".format(name))
            # print("Outputting ", out)
            # exporters.export(self.getWindingKey(withKnob=False), out)
            #
            # out = os.path.join(path, "{}_cordwheel_winder_knob.stl".format(name))
            # print("Outputting ", out)
            # exporters.export(self.getWindingKnob(), out)
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

class SprocketChainWheel:
    '''
    I really want to be able to use heavier weights with a chain so I can do an eight grasshopper with simple maintaining power, so this is an attempt to make a
    stronger chainwheel using a sprocket sandwhiched between two large "washers"
    '''
    def __init__(self, ratchet=None):
        self.ratchet = ratchet

class PocketChainWheel2:
    '''
    The PocketChainWheel was one of the first classes I wrote for the clocks, it's a mess and also the chain wheel doesn't cope well with heavy weights
    So this is an attempt to produce an improved pocket chain wheel and a tidier class

    still got a 'clunk' from this, which looked like it was due to teh chain twisting slightly so it ended up in the gap. Might try making that gap smaller.
    Also possible that the chainproducts chain is just not very high quality as it seems to hang twisted

    Works well with the heavy duty cousins chain (happy with 3kg). Looks like it might be occasionally slipping with the lighter regula 8 day chain. Need to investigate further.
    '''

    def __init__(self, ratchet_thick=0, chain=None, max_diameter=30,arbour_d=3, fixing_screws=None, fixings=3, power_clockwise=True, looseOnRod=False, ratchetOuterD=-1, ratchetOuterThick=5, wall_thick=2):

        self.type = PowerType.CHAIN2
        # if false, the powered wheel is fixed to the rod and the gear wheel is loose.
        self.looseOnRod = looseOnRod
        self.arbour_d = arbour_d



        self.chain = chain
        self.max_diameter = max_diameter
        self.hole_d  = arbour_d
        if self.looseOnRod:
            self.hole_d += LOOSE_FIT_ON_ROD
        self.fixing_screws = fixing_screws
        self.power_clockwise = power_clockwise

        if self.fixing_screws is None:
            self.fixing_screws = MachineScrew(2, countersunk=True)

        if self.chain is None:
            self.chain = REGULA_30_HOUR_CHAIN

        max_circumference = math.pi * max_diameter
        #two chain segments is what I'm calling a link, as that's the repeating bit
        link_length = self.chain.inside_length * 2
        self.pockets = floor(max_circumference /link_length)
        self.pocket_wide = self.chain.width+0.5
        #extra wire thick just so they're a smidge bigger than they need to be
        self.pocket_long =  self.chain.inside_length + self.chain.wire_thick*2 + self.chain.wire_thick

        n = self.pockets * 2
        #https://keisan.casio.com/exec/system/1223432608
        #radius of a circle that fits a polygon with n sides of length a
        a = self.chain.inside_length
        #for the centre of the chain width
        self.radius = a / (2*math.sin(math.pi/n))
        if self.radius < self.pocket_long*0.5:
            #a ratio of pocket length to radius of less than one will fail to generate a pocket angle
            print("Radius too small to generate chain wheel for this chain")
            self.radius = self.pocket_long*0.5
            # raise ValueError("Radius too small to generate chain wheel for this chain")
        self.fixing_positions = [polar(f*math.pi*2/fixings, self.radius*0.475) for f in range(fixings)]
        self.outer_radius = self.radius+self.chain.wire_thick

        self.diameter = self.radius*2
        self.circumference = math.pi * self.diameter

        self.wall_thick=wall_thick
        self.wheel_thick = self.pocket_wide + self.wall_thick*2

        if ratchetOuterD < 0:
            ratchetOuterD = self.diameter * 1.6 + ratchetOuterThick

        if ratchet_thick > 0:
            self.ratchet = Ratchet(totalD=ratchetOuterD, innerRadius=self.outer_radius*0.9999, thick=ratchet_thick, power_clockwise=power_clockwise, outer_thick=ratchetOuterThick)
        else:
            self.ratchet = None

        self.pocket_cutter_cache = None

    def get_pocket_cutter(self):

        if self.pocket_cutter_cache is not None:
            return self.pocket_cutter_cache

        pocket_length = self.pocket_long#self.chain.inside_length + self.chain.wire_thick*2
        # print("pocket_length: {}, radius: {} {}".format(pocket_length, self.radius, 1 - (pocket_length**2)/(2*self.radius**2)))
        #from law of cosines
        pocket_angle = math.acos(1 - (pocket_length**2)/(2*self.radius**2))


        end_cylinder = cq.Workplane("XY").circle(self.pocket_wide/2).extrude(self.radius*2).translate((-self.pocket_wide/2,0,0)).rotate((0,0,0), (1,0,0),-90).rotate((0,0,0),(0,0,1), radToDeg(-pocket_angle/2))
        start_cylinder = cq.Workplane("XY").circle(self.pocket_wide/2).extrude(self.radius*2).translate((self.pocket_wide/2,0,0)).rotate((0,0,0), (1,0,0),-90).rotate((0,0,0),(0,0,1), radToDeg(pocket_angle/2))

        cutter = end_cylinder.union(start_cylinder)

        end_cylinder_centre_line = Line((math.cos(pocket_angle/2)*self.pocket_wide/2, math.sin(pocket_angle/2)*self.pocket_wide/2), angle=math.pi/2+pocket_angle/2)
        start_cylinder_centre_line = Line((-math.cos(pocket_angle / 2) * self.pocket_wide / 2, math.sin(pocket_angle / 2) * self.pocket_wide / 2), angle=math.pi / 2 - pocket_angle / 2)

        filler_centre = start_cylinder_centre_line.intersection(end_cylinder_centre_line)

        end_pos = np.add(end_cylinder_centre_line.start, polar(end_cylinder_centre_line.getAngle(), self.radius * 2))
        start_pos = np.add(start_cylinder_centre_line.start, polar(start_cylinder_centre_line.getAngle(), self.radius * 2))
        #
        filler = cq.Workplane("XY").moveTo(filler_centre[0], filler_centre[1]).lineTo(start_pos[0], start_pos[1]).lineTo(end_pos[0], end_pos[1]).close().extrude(self.pocket_wide).translate((0,0,-self.pocket_wide/2))
        cutter = cutter.union(filler)

        base_end = polar(end_cylinder_centre_line.getAngle(), self.radius - self.chain.wire_thick/2)
        base_start = polar(start_cylinder_centre_line.getAngle(), self.radius - self.chain.wire_thick / 2)
        #chop the bottom off so we only cut a pocket with a flat base
        base_cutter = cq.Workplane("XY").rect(self.radius*2, base_end[1]*2).extrude(self.pocket_wide).translate((0,0,-self.pocket_wide/2))
        cutter = cutter.cut(base_cutter)

        #gap for the vertical chainlinks
        gap_thick = self.chain.wire_thick * 1.5 # twice the wire thick seemed to result in chains still being able to clunk and ended up partly sideways on the way out the wheel

        hole_centre_y = (self.radius - self.chain.wire_thick/2)* math.cos(pocket_angle/2)

        circle_centres_distance = self.chain.inside_length + self.chain.wire_thick - self.pocket_wide

        chain_segment_hole = cq.Workplane("XY").moveTo(circle_centres_distance / 2, 0).circle(self.pocket_wide / 2).extrude(gap_thick)

        chain_segment_hole = chain_segment_hole.union(cq.Workplane("XY").moveTo(-circle_centres_distance / 2, 0).circle(self.pocket_wide / 2).extrude(gap_thick))
        chain_segment_hole = chain_segment_hole.union(cq.Workplane("XY").rect(circle_centres_distance, self.pocket_wide).extrude(gap_thick))
        chain_segment_hole = chain_segment_hole.union(cq.Workplane("XY").moveTo(0,self.pocket_wide/2).rect(circle_centres_distance + self.pocket_wide, self.pocket_wide).extrude(gap_thick))

        chain_segment_hole = chain_segment_hole.translate((0, hole_centre_y, -gap_thick / 2)).rotate((0,0,0), (0,0,1), 360/(self.pockets*2))

        cutter = cutter.union(chain_segment_hole)
        self.pocket_cutter_cache = cutter
        return cutter

    def get_whole_wheel(self):
        #just the chain wheel, no ratchet, centred on (0,0,0)

        wheel = cq.Workplane("XY").circle(self.outer_radius).extrude(self.wheel_thick).translate((0, 0, -self.wheel_thick / 2))

        for p in range(self.pockets):
            angle = p*math.pi*2/self.pockets
            wheel = wheel.cut(self.get_pocket_cutter().rotate((0,0,0), (0,0,1), radToDeg(angle)))

        wheel = wheel.faces(">Z").workplane().circle(self.hole_d/2).cutThruAll()

        for pos in self.fixing_positions:
            wheel = wheel.cut(self.fixing_screws.getCutter().rotate((0,0,0), (1,0,0),180).translate(pos).translate((0,0,self.wheel_thick/2)))
            #no bottom fixing nut space, this is always being bolted to something, be it a ratchet or wheel
            # if self.ratchet is None:
            #     wheel = wheel.cut(self.fixing_screws.getNutCutter(height=self.wheel_thick/4, withBridging=True).translate(pos).translate((0,0,-self.wheel_thick/2)))

        return wheel

    def get_top_half(self):
        top = self.get_whole_wheel().intersect(cq.Workplane("XY").rect(self.radius*4, self.radius*4).extrude(self.wheel_thick))



        top =top.rotate((0,0,0), (1,0,0),180).translate((0,0,self.wheel_thick/2))

        return top

    def get_bottom_half(self):
        bottom = self.get_whole_wheel().intersect(cq.Workplane("XY").rect(self.radius*4, self.radius*4).extrude(self.wheel_thick).translate((0,0,-self.wheel_thick))).translate((0,0,self.wheel_thick/2))

        if self.ratchet is not None:
            bottom = bottom.translate((0,0,self.ratchet.thick))
            bottom = bottom.union(self.ratchet.getInnerWheel())

            for pos in self.fixing_positions:
                bottom = bottom.cut(cq.Workplane("XY").circle(self.fixing_screws.metric_thread/2).extrude(self.getHeight()).translate(pos))
                bottom = bottom.cut(self.fixing_screws.getNutCutter(height=self.ratchet.thick, withBridging=True).rotate((0,0,0),(0,0,1), 360/12).translate(pos))
            bottom = bottom.faces(">Z").workplane().circle(self.hole_d / 2).cutThruAll()

        return bottom

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 22

    def getEncasingRadius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        if self.ratchet is not None:
            return self.ratchet.outsideDiameter / 2
        else:
            return self.outer_radius

    def getChainHoleD(self):
        '''
        Returns diameter of hole for the rope/chain/cord to pass through. It needs a hole to prevent winding the weight up too far
        '''
        return self.chain.width + 2

    def isClockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
        '''
        return self.power_clockwise

    def getAssembled(self):
        '''
        return 3D model of fully assembled wheel with ratchet (for the model, not printing)
        '''
        wheel = self.get_bottom_half()
        top = self.get_top_half().rotate((0,0,0),(1,0,0),180).translate((0,0,self.wheel_thick/2))
        bottom_thick = self.wheel_thick/2
        if self.ratchet is not None:
            bottom_thick += self.ratchet.thick
        wheel = wheel.add(top.translate((0,0,bottom_thick)))
        return wheel

    def getHeight(self):
        '''
        returns total thickness of the assembled wheel, with ratchet. If it needs a washer, this is included in the height
        '''
        height =  self.wheel_thick + SMALL_WASHER_THICK_M3
        if self.ratchet is not None:
            height += self.ratchet.thick
        return height

    def outputSTLs(self, name="clock", path="../out"):
        '''
        save STL files to disc for all the objects required to print this wheel
        '''
        out = os.path.join(path, "{}_chain_wheel_bottom_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_bottom_half(), out)

        out = os.path.join(path, "{}_chain_wheel_top_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_top_half(), out)

    def getChainPositionsFromTop(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

        zOffset = - SMALL_WASHER_THICK_M3 - self.wheel_thick/2

        return [[(-self.radius, zOffset)], [(self.radius, zOffset)]]

    def getScrewPositions(self):
        '''
        return list of (x,y) positions, relative to the arbour, for screws that hold this wheel together.
        Only really relevant for ones in two halves, like chain and rope
        Used when we're not using a ratchet so the screwholes can line up with holes in the wheel
        '''
        return self.fixing_positions

    def getTurnsForDrop(self, maxChainDrop):
        '''
        Given a chain drop, return number of rotations of this wheel.
        this is trivial for rope or chain, but not so much for the cord
        '''
        return maxChainDrop / (self.pockets*self.chain.inside_length*2)

    def getRunTime(self, minuteRatio=1, cordLength=2000):
        '''
        print information about runtime based on the info provided
        '''
        return self.getTurnsForDrop(cordLength)*minuteRatio

    def printScrewLength(self):
        '''
        print to console information on screws required to assemble
        '''
        if self.ratchet is None:
            print("No ratchet, can't estimate screw lenght")
            return
        minScrewLength = self.ratchet.thick + self.wheel_thick*0.75 + self.fixing_screws.getNutHeight()
        print("Chain wheel screws: {} max length {}mm min length {}mm".format(self.fixing_screws.getString(), self.getHeight(), minScrewLength))

class PocketChainWheel:
    '''
    This is a pocket chain wheel, printed in two parts.

    Works well for lighter (<1kg) weights, doesn't work reliably for heavier weights.

    Note it's fiddly to get the tolerance right, you want a larger tolerance value ot make it more reliable, but then you get a little 'clunk'
    every time a link leaves.

    This needs a ratchet, but the ratchet is generated in the GonigTrain and then set with setRatchet until I feel like refactoring this
    This whole thing really could do with an overhaul, but I don't expect to be using chains much in the future so it'll probably not happen

    Hubert Hurr eight day chain works: wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15 (the default since it was my first clock)
    Regula 1 day chain (61 LPF) works:  wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075
    Regula 8 day chain (47 LPF 1.20mm diameter): wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075 - worked, but the chain stretch and the wheel failed with 2.5kg

    Regular 8? day chain (47 LPF 1.05mm diameter) UNTESTED: wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075

    TODO wrap all these up in a class like the screws and bearings, if I'm actually going to be using chains again

    '''

    @staticmethod
    def getMinDiameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 22

    def isClockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
        '''
        return self.power_clockwise

    def __init__(self, ratchet_thick=4, max_circumference=75, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15, holeD=3.5, screw=None, screwThreadLength=10,
                 power_clockwise=True, ratchetOuterD=-1, ratchetOuterThick=5):
        '''
        0.2 tolerance worked but could be tighter
        Going for a pocket-chain-wheel as this should be easiest to print in two parts

        default chain is for the spare hubert hurr chain I've got and probably don't need (wire_thick=1.25, inside_length=6.8, width=5)
        '''
        self.type = PowerType.CHAIN
        self.looseOnRod = False
        self.holeD=holeD
        #complete absolute bodge!
        self.rodMetricSize=math.floor(holeD)
        self.arbour_d = self.rodMetricSize
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
        #was  inside_length - wire_thick*4, which is fine for weights < 500g, but starts to get damanged beyond that, completely failing somewhere before 2.5kg
        self.pocket_wall_thick = inside_length - wire_thick*2.5

        self.inner_width = width*1.2

        self.hole_distance = self.diameter*0.275#*0.25

        self.hole_positions = [(0,-self.hole_distance), (0, self.hole_distance)]

        self.power_clockwise = power_clockwise

        if ratchetOuterD < 0:
            ratchetOuterD = self.diameter * 2.2

        if ratchet_thick > 0:
            self.ratchet = Ratchet(totalD=ratchetOuterD, innerRadius=0.9999*self.outerDiameter / 2, thick=ratchet_thick, power_clockwise=power_clockwise, outer_thick=ratchetOuterThick)
        else:
            self.ratchet = None

    def getEncasingRadius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        if self.ratchet is not None:
            return self.ratchet.outsideDiameter/2
        else:
            return self.outerRadius

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

        zOffset = - WASHER_THICK_M3 - self.wall_thick - self.inner_width / 2

        return [ [(-self.diameter / 2, zOffset)], [(self.diameter / 2, zOffset)] ]

    def getTurnsForDrop(self, chainDrop):
        return chainDrop / (self.pockets*self.chain_inside_length*2)

    def getHeight(self):
        '''
        Returns total height of the chain wheel, once assembled, including the ratchet
        includes washer as this is considered part of the full assembly
        '''
        thick = self.inner_width + self.wall_thick * 2 + WASHER_THICK_M3
        if self.ratchet is not None:
            thick += self.ratchet.thick
        return thick

    def getRunTime(self,minuteRatio=1,chainLength=2000):
        #minute hand rotates once per hour, so this answer will be in hours
        return chainLength/((self.pockets*self.chain_inside_length*2)/minuteRatio)

    def getHalf(self, sideWithClicks=False, noScrewHoles=False):
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

        if not noScrewHoles:
            if sideWithClicks:
                #just plain holes through the middle for the screws
                for holePos in self.hole_positions:
                    halfWheel = halfWheel.faces(">Z").workplane().moveTo(holePos[0],holePos[1]).circle(self.screw.metric_thread / 2).cutThruAll()
            else:
                #screw holes and nut space
                for holePos in self.hole_positions:
                    # half the height for a nut so the screw length can vary
                    halfWheel = halfWheel.cut(self.screw.getCutter(withBridging=True).translate(holePos))

            return halfWheel

    def getScrewPositions(self):
        return self.hole_positions

    def getWithRatchet(self, ratchet):


        chain =self.getHalf(True).translate((0, 0, ratchet.thick))

        clickwheel = ratchet.getInnerWheel()
        combined = clickwheel.union(chain)

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
        if self.ratchet is None:
            print("No ratchet, can't estimate screw lenght")
            return
        minScrewLength = self.getHeight() - (self.ratchet.thick + self.inner_width/2 + self.wall_thick)/2 - self.screw.getNutHeight()
        print("Chain wheel screws: {} max length {}mm min length {}mm".format(self.screw.getString(), self.getHeight(), minScrewLength))


    def getAssembled(self):


        if self.ratchet is not None:
            assembly = self.getWithRatchet(self.ratchet)
        else:
            assembly = self.getHalf(sideWithClicks=True)

        chainWheelTop = self.getHalf().rotate((0,0,0),(1,0,0),180).translate((0, 0, self.getHeight() - WASHER_THICK_M3))

        return assembly.add(chainWheelTop)

    def setRatchet(self, ratchet):
        self.ratchet=ratchet

    def outputSTLs(self, name="clock", path="../out"):

        if self.ratchet is None:
            out = os.path.join(path, "{}_chain_wheel_bottom_half.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHalf(True), out)
        else:
            out = os.path.join(path,"{}_chain_wheel_with_click.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getWithRatchet(self.ratchet), out)
        out = os.path.join(path, "{}_chain_wheel_top_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHalf(False), out)


class Ratchet:

    '''
    This is backwards from a traditional ratchet, the 'clicks' are attached to the chain wheel and the teeth are on the
    gear-wheel. The entire thing is 3D printed and relies on the springyness of PETG

    This means that they can be printed as only two parts with minimal screws to keep everything together
    '''

    APROX_EXTRA_RADIUS_NEEDED=12

    def __init__(self, totalD=50, thick=5, power_clockwise=True, innerRadius=0, outer_thick=5, click_arms=-1, click_teeth=-1):
        '''
        innerRadius is the radius of the round bit of the click wheel
        '''
        self.outsideDiameter=totalD

        #how wide the outer click wheel is
        self.outer_thick = outer_thick
        if self.outer_thick < 0:
            self.outer_thick = self.outsideDiameter*0.1



        self.clickInnerDiameter = self.outsideDiameter * 0.5
        if innerRadius == 0:
            self.clickInnerRadius = self.clickInnerDiameter / 2
        else:
            self.clickInnerRadius = innerRadius

        self.anticlockwise = -1 if power_clockwise else 1

        self.toothLength = max(self.outsideDiameter*0.025, 1)
        self.toothAngle = degToRad(2)* self.anticlockwise

        self.toothRadius = self.outsideDiameter / 2 - self.outer_thick
        self.toothTipR = self.toothRadius - self.toothLength

        cicumference = math.pi*self.outsideDiameter

        #was originaly just 8. Then tried math.ceil(cicumference/10) to replicate it in a way that scales, but this produced slightly too many teeth.
        #even /15 seems excessive, trying /20 for reprinting bits of clock 19
        #allowing overrides since I keep messing with this logic and I need to retrofit a few ratchets
        click_multiplier = 4
        if click_arms < 0:
            if self.clickInnerRadius/(self.outsideDiameter/2) < 0.75:
                #not much space for the clicks, go for more and smaller arms
                self.clicks = math.ceil(cicumference / 15)  # 8
                click_multiplier=2
            else:
                self.clicks = math.ceil(cicumference/20)#8
        else:
            self.clicks = click_arms

        if click_teeth < 0:
            #ratchetTeet must be a multiple of clicks
            self.ratchetTeeth = self.clicks*click_multiplier
        else:
            self.ratchetTeeth = click_teeth


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

        #makes for a strong ratchet, but it's harder to wind the ratchet than pull the weight!
        #clickOffsetAngle = -(math.pi*2/(self.clicks))*0.9 * self.anticlockwise
        clickOffsetAngle = -(math.pi*2/(self.clicks))*1.2 * self.anticlockwise

        # since the clicks are at such an angle, this is a bodge to ensure they're actually that thick, rather than that thick at teh base
        # mostly affects ratchets with a larger inner radius and a not-so-large outer radius
        # note - since adjusting number of clicks to the circumference, this isn't so exagerated
        #TODO proper maffs. can't use clickoffsetangle - need angle from edge of the circle
        # innerThick = 1.2*thick/math.sin(clickOffsetAngle)
        #el bodgeo for now
        innerThick = 1.4*thick

        clickInnerArcAngle = self.anticlockwise * innerThick / innerClickR

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

class TraditionalRatchet:
    '''
    For the spring barrel I need to be able to let down the mainspring, so this is a more traditional ratchet where I can release the pawl manually

    made up of a gear (with teeth), a pawl (which goes click) and a spring (which keeps the pawl in position)

    undecided on 3D printed spring or steel spring

    '''

    def __init__(self, gear_diameter, thick=5, power_clockwise=True, fixing_screws=None, pawl_angle=math.pi/2):
        self.gear_diameter = gear_diameter
        self.thick = thick
        self.power_clockwise = power_clockwise
        # by default set angle to pi/2 so the pawl is at the top of the ratchet - then if the spring fails gravity should help keep it locked in position
        #(only relevant to a spring barrel where the ratchet is on the plates, won't affect a cord movement)
        self.pawl_angle = pawl_angle

        self.fixing_screws = fixing_screws

        if self.fixing_screws is None:
            #pan headed M3 by default
            self.fixing_screws = MachineScrew(3)



        self.tooth_deep=3
        self.teeth = floor(self.gear_diameter / 5)

        self.tooth_angle = math.pi * 2 / self.teeth

        self.pawl_diameter = self.fixing_screws.metric_thread*3

        # self.gear_diameter = 2 * (self.max_diameter / 2 - self.pawl_diameter / 2 - self.tooth_deep * 2)

        self.pawl_length = self.gear_diameter*0.5

        direction = -1 if self.power_clockwise else 1
        #TODO some way of ensuring it's "safe": it will stay locked without the spring
        #this should be a case of ensuring it's to the correct side of the line perpendicular to the tooth radial
        #I think this is also the same as ensuring it's on the "outside" of the tangent from the end of the tooth it locks against
        # self.pawl_fixing = polar(direction * self.tooth_angle*self.pawl_length, self.max_diameter/2 - self.pawl_diameter/2)

        #this should always be safe, it's half a tooth depth further outside the tangent than needed to be safe, so even if it just
        #catches the tip of the tooth it should be forced into a safer position
        self.pawl_fixing = (self.gear_diameter/2 + self.tooth_deep/2, direction*self.pawl_length)

        if not self.is_pawl_position_safe():
            raise ValueError("Pawl is unsafe!")

        self.rotate_by_deg = radToDeg(self.pawl_angle - math.atan2(self.pawl_fixing[1], self.pawl_fixing[0]))



    def get_max_diameter(self):
        return np.linalg.norm(self.pawl_fixing) + self.pawl_diameter/2

    def is_pawl_position_safe(self):
        '''
        assume pawl engages with the "first" tooth, which is on the +ve x axis

        take the tangent of the gear at the tip of the first tooth

        if the pawl fixing (the point it pivots around) is on the other side of this tangent than the gear centre, it's safe
        it will lock against the tooth under pressure even without the spring holding it there

        '''
        tooth_tip_pos = (self.gear_diameter/2, 0)
        tooth_to_pawl = np.subtract(self.pawl_fixing, tooth_tip_pos)

        dot_product = np.dot(tooth_tip_pos, tooth_to_pawl)
        return dot_product > 0


    def get_gear(self):
        gear = cq.Workplane("XY").moveTo(self.gear_diameter/2, 0)

        direction = -1 if self.power_clockwise else 1

        for tooth in range(self.teeth):
            start_angle = tooth * self.tooth_angle * direction
            end_angle = start_angle + self.tooth_angle * direction

            start_inner = polar(start_angle, self.gear_diameter/2 - self.tooth_deep)
            end = polar(end_angle, self.gear_diameter/2)

            gear = gear.lineTo(start_inner[0], start_inner[1]).radiusArc(end, -direction*self.gear_diameter/2)

        gear = gear.close()

        gear = gear.extrude(self.thick)

        return gear.rotate((0,0,0),(0,0,1), self.rotate_by_deg)

    def get_pawl(self):
        # pawl = cq.Workplane("XY").circle(3).translate(self.pawl_fixing)

        direction = -1 if self.power_clockwise else 1

        tooth_inner = (self.gear_diameter/2-self.tooth_deep, 0)
        next_tooth_outer = polar(direction * self.tooth_angle, self.gear_diameter/2)

        pawl_inner = (self.pawl_fixing[0] - self.pawl_diameter / 2, self.pawl_fixing[1])
        pawl_outer = (self.pawl_fixing[0] + self.pawl_diameter / 2, self.pawl_fixing[1])

        #contact with the tooth
        pawl = cq.Workplane("XY").moveTo(tooth_inner[0], tooth_inner[1]).lineTo(self.gear_diameter/2, 0)

        pawl = pawl.lineTo(pawl_outer[0], pawl_outer[1])
        # #round the back of the fixing
        pawl = pawl.radiusArc(pawl_inner, -direction*self.pawl_diameter/2)
        # pawl = pawl.tangentArcPoint(pawl_inner)
        pawl = pawl.lineTo(next_tooth_outer[0],next_tooth_outer[1]).radiusArc(tooth_inner, direction*self.gear_diameter/2)
        # pawl = pawl.radiusArc(tooth_inner, direction * self.gear_diameter*0.75)

        # pawl = pawl.spline([pawl_outer, pawl_inner, next_tooth_outer] ,includeCurrent=True, tangents=[(0,direction), (0,direction), (0,-direction), None]).radiusArc(tooth_inner, direction*self.gear_diameter/2)



        pawl = pawl.close().extrude(self.thick)

        pawl = pawl.faces(">Z").workplane().moveTo(self.pawl_fixing[0], self.pawl_fixing[1]).circle((self.fixing_screws.metric_thread + LOOSE_FIT_ON_ROD) / 2).cutThruAll()


        return pawl.rotate((0,0,0),(0,0,1), self.rotate_by_deg)
