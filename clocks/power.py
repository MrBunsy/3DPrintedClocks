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



        screwHeight = r - self.bolt.get_head_diameter()

        screwSpace = self.bolt.get_cutter().rotate((0, 0, 0), (0, 1, 0), 90).translate((-r + self.bolt.get_head_height() / 2, 0, screwHeight + self.height))

        screwSpace = screwSpace.add(self.bolt.get_nut_cutter(height=1000).rotate((0, 0, 0), (0, 1, 0), 90).translate((r * 0.6, 0, screwHeight + self.height)))

        weight = weight.cut(screwSpace)


        #pretty shape

        topCutterToKeep = cq.Workplane("YZ").circle(r).extrude(self.diameter*2).translate((-self.diameter,0,0))
        topCutter = cq.Workplane("XY").rect(self.diameter*2, self.diameter*2).extrude(self.diameter)
        topCutter = topCutter.cut(topCutterToKeep).translate((0,0,self.height))

        weight = weight.cut(topCutter)

        return weight

    def output_STLs(self, name="clock", path="../out"):
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

    def output_STLs(self, name="clock", path="../out"):

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

    def __init__(self, diameter,rope_diameter=4, screws = None, use_steel_rod=True, style=None):
        self.diameter=diameter
        self.rope_diameter=rope_diameter
        self.screws = screws
        self.style = style

        if self.screws is None:
            self.screws = MachineScrew(3, countersunk=True)
        self.wall_thick=1
        self.slope_angle = math.pi / 3
        #just made up - might be nice to do some maths to check that the rope/chain will fit nicely with the chosen slope
        self.centre_wide = self.rope_diameter/2
        self.use_steel_rod = use_steel_rod

        self.hole_d = STEEL_TUBE_DIAMETER_CUTTER if self.use_steel_rod else self.screws.metric_thread + LOOSE_FIT_ON_ROD

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

        #adjust thickness for a screw length that exists
        screw_length = self.get_total_thickness()
        available_screw_length = get_nearest_machine_screw_length(screw_length, self.screws, allow_longer=True)
        extra_screw_length = available_screw_length - screw_length
        self.holder_thick += extra_screw_length/2



    def get_BOM(self):
        screw_length = self.get_total_thickness()

        instructions="""![Example lightweight pulley](./lightweight_pulley.jpg \"Example lightweight pulley\")
        
Push the two nyloc nuts into their slots in the back of the back holder.

Screw the bottom fixing screw partially into the front holder. Then slot the hook over the back before screwing the back holder to the front.

Screw the top fixing screw partially into the front holder, then slot over a washer. Screw the screw in slightly further, then slot over the pulley wheel. Screw it slightly further again and slot over the final washer. Then make sure that there's enough spacing for the pulley wheel to spin freely before screwing into the back holder.

When fully assembled the pulley wheel should be able to spin freely.
"""
        bom = BillOfMaterials("Lightweight pulley", instructions)

        bom.add_image("lightweight_pulley.jpg")

        bom.add_item(BillOfMaterials.Item("Cuckoo hook 1mm thick"))
        bom.add_item(BillOfMaterials.Item(f"{self.screws} {screw_length:.0f}mm", quantity=2, purpose="Fixing screws"))
        bom.add_item(BillOfMaterials.Item(f"M{self.screws.metric_thread} nyloc nut", quantity=2, purpose="Fixing nuts"))
        bom.add_item(BillOfMaterials.Item(f"M{self.screws.metric_thread} washer",quantity= 2, purpose="Padding washers"))

        if self.use_steel_rod:
            bom.add_item(BillOfMaterials.Item(f"Steel tube {STEEL_TUBE_DIAMETER}x{self.screws.metric_thread} {self.wheel_thick:.1f}mm", purpose="Tube insert for pulley wheel"))

        bom.add_printed_parts(self.get_printed_parts())
        bom.add_model(self.get_assembled())
        bom.add_model(self.get_assembled(), svg_preview_options=BillOfMaterials.SVG_OPTS_SIDE_PROJECTION)
        return bom

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

        wheel = Gear.cutStyle(wheel, outer_radius= self.diameter/2 - self.rope_diameter/2, inner_radius=self.hole_d, style=self.style, rim_thick=2)

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
            screw_cutter = self.screws.get_cutter(with_bridging=True)
            if upright:
                screw_cutter = screw_cutter.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, self.get_total_thickness()))
                screw_cutter = screw_cutter.add(self.screws.get_nut_cutter(nyloc=True, with_bridging=True))

            holder = holder.cut(screw_cutter.translate(pos))
            #used to alternate sides with nuts and screwheads, but I think I prefer just screwheads visible
            # upright = not upright

        return holder

    def get_total_thickness(self):
        return self.holder_thick*2 + self.gap_size*2 + self.wheel_thick

    def get_total_thick(self):
        return self.get_total_thickness()

    def get_assembled(self):

        wheel_base_z = self.holder_thick + self.gap_size

        wheel = self.get_wheel().translate((0,0,wheel_base_z))

        pulley = wheel.add(self.get_holder_half(True)).add(self.get_holder_half(False).rotate((0,0,0), (0,1,0), 180).translate((0,0,self.get_total_thickness())))

        return pulley

    def get_printed_parts(self):
        return [
            BillOfMaterials.PrintedPart("wheel", self.get_wheel(), printing_instructions="Print alone with small layer height for reliable overhang"),
            BillOfMaterials.PrintedPart("holder_back", self.get_holder_half(True)),
            BillOfMaterials.PrintedPart("holder_front", self.get_holder_half(False)),
        ]

    def output_STLs(self, name="clock", path="../out"):
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

    def __init__(self, diameter, cord_diameter=2.2, rod_metric_size=4, wheel_screws = None, hook_screws=None,
                 screw_count=4, v_shaped=False, style=None, bearing=None, bearing_holder_thick=0.8, hooks=1, hook_distance=55):

        #can hold multiple weights
        self.hooks = hooks
        #if hooks > 1, how far apart are they?
        self.hook_distance = hook_distance

        # TODO make this respect the actual style, at the moment it just does what it can to avoid the screws
        self.style = style

        self.diameter=diameter
        self.cord_diameter=cord_diameter
        self.v_shaped=v_shaped



        #if negative, don't punch holes
        self.rod_metric_size=rod_metric_size
        #only used if bearing is not provided
        self.rod_hole_d = rod_metric_size + LOOSE_FIT_ON_ROD
        #screws which hold the two halves of the pulley wheel together
        self.screws = wheel_screws
        if self.screws is None:
            self.screws = MachineScrew(2, countersunk=True, length=8)

        self.hook_screws = hook_screws
        if self.hook_screws is None:
            self.hook_screws = MachineScrew(4, countersunk=True)

        # self.hook_screws =

        self.edge_thick= cord_diameter * 0.5
        self.taper_thick = cord_diameter * 0.2
        #if not none, a BearingInfo for a bearing instead of a rod
        self.bearing=bearing
        self.bearing_holder_thick=bearing_holder_thick


        self.screw_positions=[polar(angle, diameter * 0.35) for angle in [i * math.pi * 2 / screw_count for i in range(screw_count)]]



        if bearing is not None:
            #see if we can adjust our total thickness to be the same as the bearing
            total_thick = self.get_total_thick()
            bearing_wiggle_height=0.4
            if total_thick < bearing.height + self.bearing_holder_thick*2 +bearing_wiggle_height:
                #too narrow
                extra_thick_needed = (bearing.height + self.bearing_holder_thick * 2 + bearing_wiggle_height) - total_thick
                self.edge_thick+= extra_thick_needed / 4
                self.taper_thick+= extra_thick_needed / 4
            else :
                print("Can't fit bearing neatly inside pulley")
        total_thick = self.get_total_thick()
        if total_thick < self.screws.get_total_length():
            print("Not thick ({}) enough to fit screw of length {}".format(total_thick, self.screws.get_total_length()))
            #make it thick enough to fit the screw in, with a little bit of spare
            extra_thick_needed = (self.screws.get_total_length() - total_thick) + 0.5
            self.edge_thick += extra_thick_needed / 2
            self.bearing_holder_thick += extra_thick_needed / 2

        self.hook_thick = 5.5
        self.hook_bottom_gap = 3
        self.hook_side_gap = 1

        self.hook_wide = 16
        #using a metal cuckoo chain hook to hold the weight, hoping it can stand up to 4kg (it can, last clock has been going for months) (now years)
        self.cuckoo_hook_outer_d=14#13.2
        self.cuckoo_hook_thick = 1.2#0.9

        hook_total_thick = self.get_hook_total_thick()
        hook_screws_length = get_nearest_machine_screw_length(hook_total_thick, self.hook_screws, prefer_longer=True)
        if hook_screws_length > hook_total_thick:
            #make ourselves thick enough to hold a sensible length of screw
            extra = hook_screws_length - hook_total_thick
            print(f"Making pulley extra {extra}mm thick to account for {hook_screws_length}mm screws")
            self.hook_thick += extra/2 + 0.1



    def get_total_thick(self):
        '''
        thickness of just the pulley wheel
        TODO rename this (but I think this might be harder as other things use this name so I can't use pycharm's refactor)
        '''
        return self.edge_thick * 2 + self.taper_thick * 2 + self.cord_diameter

    def get_max_radius(self):
        #needs to be kept consistent with bottomPos below
        return self.diameter/2 + self.cord_diameter

    def get_half(self, top=False):
        radius = self.diameter/2
        #from the side
        bottomPos = (radius + self.cord_diameter, 0)
        topOfEdgePos = (radius + self.cord_diameter, self.edge_thick)
        endOfTaperPos = (radius, self.edge_thick + self.taper_thick)
        topPos = (endOfTaperPos[0] - self.cord_diameter / 2, endOfTaperPos[1] + self.cord_diameter / 2)

        # edgeR = self.diameter/2 + self.cordDiameter/4
        # middleR = self.diameter/2 - self.cordDiameter/2

        circle = cq.Workplane("XY").circle(self.diameter/2)
        pulley = cq.Workplane("XZ").moveTo(bottomPos[0], bottomPos[1]).lineTo(topOfEdgePos[0], topOfEdgePos[1]).lineTo(endOfTaperPos[0], endOfTaperPos[1])#.\

        if self.v_shaped:
            pulley = pulley.lineTo(topPos[0], topPos[1])
        else:
            #pulley = pulley.tangentArcPoint(topPos, relative=False)
            pulley = pulley.radiusArc(topPos, self.cord_diameter / 2)

        pulley = pulley.lineTo(0,topPos[1]).lineTo(0,0).close().sweep(circle)

        holeD = self.rod_hole_d
        if self.bearing is not None:
            holeD = self.bearing.outer_d

        # TODO cut out rod hole and screwholes if needed
        # if self.rodMetricSize > 0:
        #     shape = shape.faces(">Z").workplane().circle((self.rodMetricSize+LOOSE_FIT_ON_ROD)/2).cutThruAll()


        if self.style is not None:
            #TODO but need to work out how to have arms in the right places for the screws
            # pulley = Gear.cutStyle(pulley, outer_radius=self.diameter / 2 - self.cord_diameter / 2, inner_radius=holeD / 2, style=self.style)
            #for now, avoid the screws
            extra_r = 2.5
            outer_radius = self.diameter / 2 - self.cord_diameter / 2 - extra_r
            inner_radius = holeD/2 + extra_r
            if outer_radius > inner_radius + 1:
                cutter = cq.Workplane("XY").circle(inner_radius).circle(outer_radius).extrude(self.get_total_thick())
                for pos in self.screw_positions:
                    line = Line((0,0), another_point=pos)

                    cutter = cutter.cut(get_stroke_line([(0,0), polar(line.get_angle(), outer_radius*2)], wide=self.screws.get_head_diameter() + extra_r, thick=self.get_total_thick()))
                cutter = cutter.edges("|Z").fillet(self.screws.get_head_diameter()*0.25)
                pulley = pulley.cut(cutter)




        # pulley = pulley.faces(">Z").workplane().circle(holeD/2).cutThroughAll()
        hole = cq.Workplane("XY").circle(holeD/2).extrude(1000)
        print("pulley, bearing", self.bearing)
        if self.bearing is not None:
            print("self.bearingHolderThick", self.bearing_holder_thick)
            hole = hole.translate((0,0,self.bearing_holder_thick))
            hole = hole.add(cq.Workplane("XY").circle(self.bearing.outer_safe_d / 2).extrude(1000))

        pulley = pulley.cut(hole)

        screwHoles = cq.Workplane("XY")

        for screwPos in self.screw_positions:


            if top:
               screwHoles = screwHoles.add(self.screws.get_cutter(with_bridging=True).translate(screwPos))
            else:
                screwHoles = screwHoles.add(self.screws.get_nut_cutter(with_bridging=True, with_screw_length=1000).translate(screwPos))

        pulley = pulley.cut(screwHoles)

        return pulley

    def get_hook_total_thick(self):
        return self.get_total_thick() + self.hook_side_gap*2 + self.hook_thick*2

    def get_hook_half(self, front=True):
        '''
        Get a way to attach a weight to a pulley wheel
        assumes we're using a bearing
        '''



        axle_height = self.get_max_radius() + self.hook_bottom_gap + self.hook_thick * 0.5

        extra_height = 0

        length = self.get_hook_total_thick()

        # hook = cq.Workplane("XY").lineTo(length/2,0).line(0,axleHeight+extraHeight).line(- thick,0).line(0,-(axleHeight + extraHeight - thick) ).lineTo(0,thick).mirrorY().extrude(wide)

        #make a large block of a nice shape and cut out space for a pulley wheel
        r = self.hook_wide / 2#*0.75
        # pulleyHoleWide = self.get_total_thick() + self.hook_side_gap * 2

        # hook = cq.Workplane("XY").lineTo(axle_height + extra_height, 0).radiusArc((axle_height + extra_height, self.hook_wide), -r).lineTo(0, self.hook_wide).radiusArc((0, 0), -r).close().extrude(length / 2)

        hook = get_stroke_line([(0,0), (axle_height + extra_height, 0)], wide=self.hook_wide, thick = length/2)

        hook = hook.edges("<Z").chamfer(r*0.1)

        hole_r = self.get_max_radius() + self.hook_bottom_gap

        #leave two sticky out bits on the hook that will press right up to the inside of the bearing
        pulley_hole = cq.Workplane("XY").circle(hole_r).extrude(self.get_total_thick() - self.bearing_holder_thick)\
             .faces("<Z").workplane().circle(hole_r).circle(self.bearing.inner_safe_d / 2).extrude(self.hook_side_gap + self.bearing_holder_thick)

        #            .faces(">Z").workplane().circle(holeR).circle(self.bearing.innerSafeD).extrude(self.hookSideGap)\

        #.translate((axleHeight, self.hookWide/2, self.hookThick))
        pulley_hole = pulley_hole.translate((axle_height, 0, self.hook_thick + self.hook_side_gap + self.bearing_holder_thick))

        # return pulleyHole
        hook = hook.cut(pulley_hole)

        fixing_positions = [(axle_height, 0), (0,0)]

        for pos in fixing_positions:
            hook = hook.cut(self.hook_screws.get_cutter(ignore_head=not front).translate(pos))

            if not front:
                hook = hook.cut(self.hook_screws.get_nut_cutter(with_bridging=True).translate(pos))

        # # cut out hole for m4 rod for the pulley axle
        # rod_hole = cq.Workplane("XY").circle(self.bearing.inner_d / 2).extrude(1000).translate((axle_height, 0, 0))
        #
        # hook = hook.cut(rod_hole)
        #
        #
        # #hole at the bottom for a screw to hold the pulley together and take the cuckoo hook to hold a weight
        #
        # screwhole = cq.Workplane("XY").circle(self.bearing.inner_d / 2).extrude(1000).translate((0, 0, 0))
        #
        # hook = hook.cut(screwhole)




        #translate so hole is at 0,0
        hook = hook.translate((-axle_height, 0, 0))

        cuckoo_hook_hole = cq.Workplane("XY").moveTo(0, self.cuckoo_hook_outer_d / 2).radiusArc((0, -self.cuckoo_hook_outer_d / 2), self.cuckoo_hook_outer_d / 2).line(-100, 0).line(0, self.cuckoo_hook_outer_d).close().extrude(self.cuckoo_hook_thick)

        hook = hook.cut(cuckoo_hook_hole.translate((0, 0, self.get_hook_total_thick() / 2 - self.cuckoo_hook_thick / 2)))

        return hook

    def get_assembled(self):
        pulley = self.get_half(top=False).add(self.get_half(top=True).rotate((0, 0, self.get_total_thick() / 2), (1, 0, self.get_total_thick() / 2), 180))

        if self.bearing is not None:
            # hook = self.getHookHalf()
            # pulley = hook.add(pulley.translate((0,0,-self.get_total_thick()/2)).rotate((0,0,0),(0,1,0),90))

            hook = self.get_hook_half(front=False).add(self.get_hook_half(front=True).rotate((0, 0, self.get_hook_total_thick() / 2), (1, 0, self.get_hook_total_thick() / 2), 180))
            pulley = hook.add(pulley.translate((0, 0, self.get_hook_total_thick() / 2 - self.get_total_thick() / 2)))

        pulley = pulley.rotate((0,0,0), (0,0,1), 90)

        return pulley

    def printInfo(self):


        def get_BOM(self):
            screw_length = self.get_total_thickness()

            instructions = """![Example lightweight pulley](./lightweight_pulley.jpg \"Example lightweight pulley\")

    Push the two nyloc nuts into their slots in the back of the back holder.

    Screw the bottom fixing screw partially into the front holder. Then slot the hook over the back before screwing the back holder to the front.

    Screw the top fixing screw partially into the front holder, then slot over a washer. Screw the screw in slightly further, then slot over the pulley wheel. Screw it slightly further again and slot over the final washer. Then make sure that there's enough spacing for the pulley wheel to spin freely before screwing into the back holder.

    When fully assembled the pulley wheel should be able to spin freely.
    """
            bom = BillOfMaterials("Lightweight pulley", instructions)

            bom.add_image("lightweight_pulley.jpg")

            bom.add_item(BillOfMaterials.Item("Cuckoo hook 1mm thick"))
            bom.add_item(BillOfMaterials.Item(f"{self.screws} {screw_length:.0f}mm", quantity=2, purpose="Fixing screws"))
            bom.add_item(BillOfMaterials.Item(f"M{self.screws.metric_thread} nyloc nut", quantity=2, purpose="Fixing nuts"))
            bom.add_item(BillOfMaterials.Item(f"M{self.screws.metric_thread} washer", quantity=2, purpose="Padding washers"))

            if self.use_steel_rod:
                bom.add_item(BillOfMaterials.Item(f"Steel tube {STEEL_TUBE_DIAMETER}x{self.screws.metric_thread} {self.wheel_thick:.1f}mm", purpose="Tube insert for pulley wheel"))

            bom.add_printed_parts(self.get_printed_parts())
            bom.add_model(self.get_assembled())
            bom.add_model(self.get_assembled(), svg_preview_options=BillOfMaterials.SVG_OPTS_SIDE_PROJECTION)
            return bom

    def get_BOM(self):

        bom = BillOfMaterials("Bearing Pulley")

        bom.add_model(self.get_assembled())
        bom.add_image("bearing_pulley.jpg")
        bom.add_image("bearing_pulley_wheel.jpg")

        bom.assembly_instructions += f"""![Example Bearing Pulley](./bearing_pulley.jpg \"Example Bearing Pulley\")

If the top surfaces (as printed) of the parts of the pulley wheel aren't completely flat it's worth sanding or filing them flat. Then when the two parts of the pulley are screwed together there won't be a gap.
        
Push the M{self.hook_screws.metric_thread} nuts into the back of the bottom hook and the M{self.screws.metric_thread} nuts into the back of the pulley wheel. Push the bearing into one half of the pulley wheel.

![Example Bearing Pulley Wheel](./bearing_pulley_wheel.jpg \"Example Bearing Pulley Wheel\")

Screw the two halves of the pulley wheel together with the M{self.screws.metric_thread} screws.

Use one of the M{self.hook_screws.metric_thread} screws to fix the top of the two hook halves together through the pulley wheel.

Finally screw the bottom half of the pulley hook together with the remaining M{self.hook_screws.metric_thread} screw, remembering to insert the cuckoo hook.
"""

        hook_screws_length = get_nearest_machine_screw_length(self.get_hook_total_thick(), self.hook_screws)

        bom.add_item(BillOfMaterials.Item(f"{self.screws} {self.screws.length}mm", quantity=2, purpose="Fix the pulley wheel together"))
        bom.add_item(BillOfMaterials.Item(f"M{self.screws.metric_thread} nut", quantity=2, purpose="Fix the pulley wheel together"))
        bom.add_item(BillOfMaterials.Item(f"{self.hook_screws} {hook_screws_length}mm", quantity=2, purpose="Fix whole pulley together"))
        bom.add_item(BillOfMaterials.Item(f"M{self.hook_screws.metric_thread} nut", quantity=2, purpose="Fix whole pulley together"))
        bom.add_item(BillOfMaterials.Item(f"Cuckoo hook {self.cuckoo_hook_thick}mm thick"))
        bom.add_item(BillOfMaterials.Item(f"{self.bearing}"))
        bom.add_printed_parts(self.get_printed_parts())

        return bom
    def get_printed_parts(self):
        parts = [
            BillOfMaterials.PrintedPart("pulley_wheel_top", self.get_half(top=True)),
            BillOfMaterials.PrintedPart("pulley_wheel_bottom", self.get_half(top=False))
        ]
        if self.bearing is not None:
            #I really can't remember what the use case was without the bearing?
            parts += [
                BillOfMaterials.PrintedPart("pulley_hook_half_top", self.get_hook_half(front=True)),
                BillOfMaterials.PrintedPart("pulley_hook_half_bottom", self.get_hook_half(front=False)),
            ]
        return parts

    def output_STLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_pulley_wheel_top.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_half(top=True), out)

        out = os.path.join(path, "{}_pulley_wheel_bottom.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_half(top=False), out)

        if self.bearing is not None:
            out = os.path.join(path, "{}_pulley_hook_half.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_hook_half(), out)

class MainSpring:
    '''
    Class to represent the dimensions of a mainspring
    '''



    def __init__(self, height=7.5, hook_height = -1, thick = 0.32, loop_end=True, barrel_diameter=50, arbor_d=9, turns=4.35, length=1100):
        '''
        height, thickness, barrel diameter (if not loop end) and length are all attributes of the actual spring itself

        arbor_d and turns have been measured by reverse engineering real clocks and may be best ignored once I can calculate how much energy we store in a spring
        '''
        self.height=height
        if hook_height < 0:
            hook_height = height / 3
        self.hook_height = hook_height
        self.thick=thick
        self.loop_end=loop_end
        #only the intended barrel diameter, we'll calculate our own later as we don't use the expected size of arbor
        self.barrel_diameter = barrel_diameter
        self.length = length
        #expected size of arbor, not actually used for any calculations
        self.arbor_d = arbor_d
        #rotation of barrel for expected duration (bit woolly, will define properly if and when needed)
        #DEPRECATED - we now calculate this. Previously was reverse engineered from examined clocks
        self.turns = turns

# 18 40 45
SMITHS_EIGHT_DAY_MAINSPRING = MainSpring(height=18, thick=0.4, barrel_diameter=45, arbor_d=9, length=1650)
MAINSPRING_183535 = MainSpring(height=18, thick=0.35, barrel_diameter=35, length=1400)
MAINSPRING_102525 = MainSpring(height=10, thick=0.25, barrel_diameter=25, length=950)
class SpringArbour:
    '''
    This was intended to work with a loop end mainspring like an alarm clock.
    not taking this design further, attempting springs with SpringBarrel
    and since the spring barrel has proven sucessful, I'm not sure this will ever be revisted
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
            bearing = get_bearing_info(10)
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
        self.bearingBitR = self.bearing.inner_d / 2 - self.bearingWiggleRoom

        self.bearingStandoffThick=0.6

        self.beforeBearingTaperHeight=0

        if self.diameter < self.bearingBitR*2:
            #need to taper up to the bearing, as it's bigger!
            r = self.bearing.inner_safe_d / 2 - self.diameter / 2
            angle=deg_to_rad(30)
            self.beforeBearingTaperHeight = r * math.sqrt(1/math.sin(angle) - 1)

        self.ratchet = None
        if self.ratchet_thick > 0:
            self.ratchet = Ratchet(totalD=self.diameter*4, thick=self.ratchet_thick, blocks_clockwise= self.power_clockwise)

    def getArbour(self):
        arbour = cq.Workplane("XY")

        if self.ratchet is not None:
            arbour = self.ratchet.get_inner_wheel().faces(">Z").workplane().circle(self.diameter / 2).extrude(self.spring_bit_height)

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
        point = polar(deg_to_rad(hook_angle), hook_r * 200)

        #cutting it flat
        # spring_hook = spring_hook.cut(cq.Workplane("XY").moveTo(0,self.hook_deep).rect(self.hook_deep*2,self.hook_deep*2).extrude(self.spring.hook_height))
        spring_hook = spring_hook.cut(cq.Workplane("XY").moveTo(0,0).lineTo(point[0],point[1]).lineTo(-point[0], point[1]).close().extrude(self.spring.hook_height))

        clockwise = 1 if self.power_clockwise else -1

        spring_hook = spring_hook.translate((clockwise*(self.hook_deep + (self.diameter/2 - hook_r)),0,self.spring_bit_height/2 - self.spring.hook_height/2 + self.ratchet_thick))
        #for some reason just adding results in a malformed STL, but cutting and then adding is much better?!
        spring_hook = spring_hook.cut(arbour)

        arbour = arbour.add(spring_hook)

        if self.beforeBearingTaperHeight > 0:
            arbour = arbour.add(cq.Solid.makeCone(radius1=self.diameter/2, radius2=self.bearing.inner_safe_d / 2, height = self.beforeBearingTaperHeight).translate((0, 0, self.spring_bit_height + self.ratchet_thick)))
            arbour = arbour.faces(">Z").workplane().moveTo(0, 0).circle(self.bearing.inner_safe_d / 2).extrude(self.bearingStandoffThick)

        arbour = arbour.faces(">Z").workplane().moveTo(0, 0).circle(self.bearing.inner_d / 2 - self.bearingWiggleRoom).extrude(self.bearing.height)
        # using polygon rather than rect so it calcualtes the size to fit in teh circle
        arbour = arbour.faces(">Z").workplane().polygon(4, self.bearing.inner_d - self.bearingWiggleRoom * 2).extrude(self.keySquareBitHeight)

        arbour = arbour.faces(">Z").workplane().circle(self.metric_rod_size/2).cutThruAll()



        return arbour


class SpringBarrel:
    '''
    Experiment! Can heavy duty 3D printed PETG hold up to an eight day spring? Let's find out!

    Plan: chunkier arbor than normal (and might need to make barrel diameter slightly larger as a result)
    Use M3 screws for the hooks on both the arbor and the barrel inside.
    Barrel will need a seriously thick wall - 5mm? 10mm?
    Arbor will be printed lying on its side, so the side the screw screws into will be the flat side Hopefully this will give it enough strength

    TODO determine how many turns the barrel should make - can easily count teeth on an old smiths.
    Worth making an experimental rig to see how much weight the spring can pull up? then I can estimate the power
    Current plan: work out how many turns are needed, then make a clock that runs for only 3 days using those turns

    In theory the going train already supports multiple chain wheels, time to shake out the bugs!

    TODO have the winding key on the back for the first mantel clock

    Observations:
     - The barrel is far chunkier than it needs to be - can be given much thinner walls, but will still want a chunky bit to take the m3 screw
     - M3 countersunk screws worked better than pan head
     - The chunky arbor was very hard to fit inside the spring, ended up mangling the spring a bit with pliers. Will want to reduce diameter to use a decent spring

     Ideas:
     Use bearings on the lid and base of barrel, since the barrel rotates in normal usage DONE
     Try 15mm bearings on lid and barrel, and 12mm in plates.
     Can round the edges of the key like on the anchor arbor to get as chunky a key as possible through a smaller diameter
     Since the barrel seems strong enough - try cutting a gear style?

     more ideas:
     12mm bearings on lid barrel and plates, and use collets to keep distances DONE
     maybe a hexagonal key instead of square? Could be stronger for the same diameter than the rounded square? DONE

    '''

    def __init__(self, spring = None, key_bearing=None, lid_bearing=None, barrel_bearing=None, clockwise = True, pawl_angle=math.pi/2, click_angle=-math.pi/2,
                 base_thick=5, ratchet_at_back=True, style=GearStyle.SOLID, fraction_of_max_turns=0.5, wall_thick=12, spring_hook_screws=None, extra_barrel_height=1.5,
                 ratchet_thick=8):
        '''

        '''
        self.type = PowerType.SPRING_BARREL

        self.style = style
        #comply with PoweredWheel interface
        self.loose_on_rod=True

        # we can calcualte the theoretical maximum rotations of the barrel, what fraction of this should be used over the runtime of the clock?
        # about half looks to match up with real smiths clocks I've analysed
        self.fraction_of_max_turns = fraction_of_max_turns

        #ratchet is out the back plate, rather than on the front plate?
        self.ratchet_at_back = ratchet_at_back
        self.ratchet_thick = ratchet_thick

        #how much more space to allow in the barrel to prevent the spring rubbing up against the base or lid?
        self.extra_barrel_height = extra_barrel_height

        self.spring = spring
        if self.spring is None:
            self.spring = SMITHS_EIGHT_DAY_MAINSPRING

        self.clockwise=clockwise

        #called key_bearing in Cordwheel, so stick with that, even though we'll use one bearing for everything now (except a flanged bearing in the lid?)
        self.key_bearing = key_bearing

        if self.key_bearing is None:
            self.key_bearing = BEARING_12x21x5

        self.lid_bearing = lid_bearing

        if self.lid_bearing is None:
            self.lid_bearing = BEARING_12x18x4_FLANGED

        self.barrel_bearing = barrel_bearing

        if self.barrel_bearing is None:
            self.barrel_bearing = BEARING_12x18x4_THIN

        self.barrel_height = self.spring.height + self.extra_barrel_height

        #10 from first experiment seemd like more than needed
        #8 did crack after the tooth failed - *probably* just because of the tooth failing, but let's go back up anyway
        self.wall_thick = wall_thick#12
        #6 seemed enough, can probably get away with less
        self.base_thick = base_thick
        #flanged bearing sitting entirely within the lid
        self.lid_thick= self.lid_bearing.height# - self.lid_bearing.flange_thick

        self.internal_endshake=0.5

        # copied from CordWheel (where it's added to radius)
        self.bearing_wiggle_room = 0.05*2

        #assuming a flanged bearing in the lid
        self.lid_hole_d = self.lid_bearing.outer_d

        self.arbor_d = self.key_bearing.inner_d - self.bearing_wiggle_room



        self.arbor_d_spring = self.arbor_d + 1
        print("arbor d inside spring: {}mm".format(self.arbor_d_spring))

        self.back_bearing_standoff = 0.5
        self.front_bearing_standoff = 1

        #trying a hex key instead of square
        self.key_containing_diameter = self.arbor_d

        # https://en.wikipedia.org/wiki/Sagitta_(geometry)
        #assuming hexagon, find how far the flat edge is from the containing diameter
        r = self.key_containing_diameter / 2
        l = r
        sagitta = r - math.sqrt(r ** 2 - (l ** 2) / 4)

        # print on its side and flat against the base of the key (get containing diameter is the full inside diameter of the bearing, but the arbor_d has bearing_wiggle_room subtracted)
        self.cutoff_height = sagitta
        # self.key_square_side_length = self.arbor_d_bearing*0.5*math.sqrt(2)
        # if self.arbor_d_bearing < 14:
        #     #make the key larger than would fit through the bearing, but we'll round the edges off later
        #     self.key_square_side_length = self.arbor_d_bearing*0.6 * math.sqrt(2)
        # self.key_max_r =



        self.collet_wiggle_room = 0.5 #0.5 only fitted with some filing, but when the arbor was pritned with a 0.6 nozzle 0.7 was a tiny bit loose

        self.lid_fixing_screws_count = 3
        # self.lid_fixing_screws = MachineScrew(2, countersunk=True, length=10)
        self.lid_fixing_screws = MachineScrew(2, countersunk=True, length=10)
        self.collet_screws = self.lid_fixing_screws

        self.spring_hook_screws = spring_hook_screws
        if self.spring_hook_screws is None:
            self.spring_hook_screws = MachineScrew(3, length=16, countersunk=True)

        # calculate this given we know the spring length+thickness and arbor diameter
        self.barrel_diameter = self.get_inner_diameter()

        self.spring_hook_space=2



        self.ratchet_collet_thick = self.lid_fixing_screws.get_head_diameter() + 1.5
        self.back_collet_thick = self.ratchet_collet_thick + self.back_bearing_standoff

        self.outer_radius_for_style = self.barrel_diameter / 2#-1
        self.inner_radius_for_style = self.key_bearing.outer_d / 2 + self.wall_thick / 2

        self.collet_diameter = self.arbor_d+8
        self.click_angle = click_angle
        self.pawl_angle = pawl_angle
        self.configure_ratchet()

    def configure_direction(self, power_clockwise=True):
        self.clockwise = power_clockwise
        #regenerate the ratchet
        self.configure_ratchet()

    def configure_ratchet(self):
        ratchet_blocks_clockwise = not self.clockwise
        if self.ratchet_at_back:
            ratchet_blocks_clockwise = self.clockwise
        ratchet_d = self.arbor_d * 2.5

        self.ratchet = TraditionalRatchet(gear_diameter=ratchet_d, thick=self.ratchet_thick, blocks_clockwise=ratchet_blocks_clockwise, click_fixing_angle=self.click_angle, pawl_angle=self.pawl_angle)

    def configure_ratchet_angles(self, click_angle, pawl_angle):
        self.click_angle = click_angle
        self.pawl_angle = pawl_angle
        self.configure_ratchet()

    def get_rod_radius(self):
        '''
        get space behind* the powered wheel space so the gear train can fit the minute wheel

        *TODO power at rear and ordering of gears etc etc, for now assume power at hte front and minute wheel behind
        '''
        return self.arbor_d/2

    def get_key_size(self):
        return self.key_containing_diameter

    def get_key_sides(self):
        return 6

    def is_clockwise(self):
        return self.clockwise

    def get_inner_diameter(self):
        '''
        Known: spring thickness, designed spring barrel internal diameter
        measured: "real" arbor diameter and barrel turns (for designed runtime)
        calculatable: key turns to wind up (for designed runtime)

        The Modern Clock, page 281 goes into some useful detail here.

        "This is conditioned by the fact that the volume which the spring occupies when it is down must
         not be greater nor less than the volume of the empty space around the arbor into which it is to
          be wound, so that the outermost coil of the spring when fully wound will occupy the same place
           which the innermost occupies when it is down"

        "A mainspring in the act of uncoiling in its barrel always gives a number of turns equal to the
         difference between the number of coils in the up and the down positions. Thus, if 17 be the number
          of coils when the spring is run down, and 25 the number when against the arbor, the number of
           turns in uncoiling will be 8, or the difference between 17 and 25"


        The inner diameter of the barrel is a function of the thickness of spring, length of spring and diameter of the centre arbor
        The maximum number of turns the barrel can perform is therefor calculated from the above
        I think it's then up to me to decide what the runtime should be over the maximum turns

        Trying the modern clock's rule of thumb doesn't result in the expected barrel diameter the smiths mainspring is sold for.
        I've read online about the 1/3 rule (but I think this was only for watches):
        #https://www.watchrepairtalk.com/topic/24127-estimating-the-mainspring-size-from-barrel-diameter/
        "Assuming that mainsprings are designed to follow the 1/3 area rule (that the unwound mainspring in the barrel
         should occupy 1/3 of the barrel width), then thickness and length must scale with the barrel diameter."

        #https://www.m-p.co.uk/formulae/sprlen.htm
        #Meadows & Passmore's Clock Mainspring Length Calculator
        Barrel diameter (D)
        Arbor diameter (d)
        Spring thickness (t)
        Length = ((((PI x (D/2)**2)-(PI x (d/2)**2)))/2) /t
        so I think this is: difference in the area of the barrel and area of the arbor, divided by twice teh thickness of the spring.
         Is this not another way of expressing The Modern Clock idea?
        then length should be between 80% and 100% of that calculated. The smiths spring is 86% of the length calcualted here, so this seems plausible

        My method of the modern clock results in a value that is 95% of the diameter of the smiths spring barrel (assuming 9mm arbor).
        So given I include partial coils, this sounds about the same?
        If I ignore partial coils I get a value 89% of the smiths barrel.

        Including partial coils and going the other way - mine calculates a barrel of 42.6, which results in the meadows and passmore saying the length should be 1702
        I think this is basically the same idea, but using area avoids the mess with partial coils.

        This agrees with the NAWCC:
        https://theindex.nawcc.org/CalcMainspringLength.php
        "A properly sized mainspring will fill half of the available area in the barrel."

        elsewhere I've read "The spring should occupy 1/3 to 1/2 of the free space inside a barrel" https://www.m-p.co.uk/muk/ryoc/doc_page27.shtml
        I think this is all variations on a theme, that the barrel needs to be slightly larger than calculated as from "half of the available area in the barrel"

        https://www.abbeyclock.com/usmsp.html
        Abbeyclock again says, about the maximum number of turns "This figure is theoretical: in practice, the net turns is one to two turns fewer,
         depending on the thickness and the condition of the spring" so I should bare that in mind with how many turns I get out of the barrel

        So, I'll use the area technique but scale up by 1/(90%) ~= 1.1
        Adjusted this scaling so that with a 9mm arbor, the diameter for a smiths barrel results in the same as its known real value

        '''


        arbor_d = self.arbor_d_spring
        # arbor_d = 9
        area_of_coiled_spring = self.spring.thick * self.spring.length
        #free area inside barrel needs to be twice this, plus some fudge factor chosen so that the calculations line up with the "known" smiths spring
        #thoughts - I'm using countersunk machine screw heads as hooks, they take up more space than proper hooks - should I take this into account?
        #or just leave the fudge factor as is?
        desired_free_area_of_inside_barrel = area_of_coiled_spring*2.325
        area_of_spring_arbor = math.pi*(arbor_d/2)**2
        total_area_of_inside_barrel = desired_free_area_of_inside_barrel + area_of_spring_arbor

        #A = pi * r**2
        #r**2 = A/pi
        #r = sqrt(A/pi)

        diameter_of_spring_barrel = 2*math.sqrt(total_area_of_inside_barrel/math.pi)

        print("diameter of spring barrel: {}".format(diameter_of_spring_barrel))

        #this also matches up with the rule of thumb that the mainspring thickness should be aproximately 1/100th of the barrel diameter

        #I think that my hooks are larger than "real" hooks and also it's a PITA to put the spring in without coning it. So, further bodge:
        #printed a few successful clocks with this, but trying dividing by two to see if I can get a tiny bit more runtime
        diameter_of_spring_barrel += self.spring_hook_screws.get_head_height()/2

        return diameter_of_spring_barrel

    def get_max_barrel_turns(self):
        '''
        Given we know the arbor and barrel diameter, thickness and length of the spring - what's the theoretical maximum number of rotations we can get out of it?

        uuh lots of copy paste from get_inner_diameter(), but that function really needs all its blurb about why it does the three lines of calculation, so I'm going to leave it for now
        '''

        arbor_radius = self.arbor_d_spring / 2
        area_of_coiled_spring = self.spring.thick * self.spring.length
        area_of_spring_arbor = math.pi * arbor_radius ** 2
        total_inner_area = area_of_spring_arbor + area_of_coiled_spring

        fully_wound_radius = math.sqrt(total_inner_area/math.pi)

        spring_wound_thickness = fully_wound_radius - arbor_radius
        spring_wound_coils = spring_wound_thickness / self.spring.thick

        #this does agree with the crude method of counting coils commented out in get_inner_diameter!


        area_of_barrel = math.pi*(self.barrel_diameter/2)**2
        #assume the spring is entirely on the outside of the barrel
        area_with_no_spring = area_of_barrel - area_of_coiled_spring

        inner_radius = math.sqrt(area_with_no_spring/math.pi)

        spring_unwound_thickness = self.barrel_diameter/2 - inner_radius
        spring_unwound_coils = spring_unwound_thickness / self.spring.thick


        total_barrel_turns = spring_wound_coils - spring_unwound_coils
        print("spring_wound_coils: {} spring unwound coils: {}, max theoretical barrel turns: {}".format(spring_wound_coils, spring_unwound_coils, total_barrel_turns))
        # given I calculated the smiths barrel to turn  4.3 turns during a week, maybe I should aim for half of this over the desired runtime?
        # This would work out at 4.4 turns over 7 days, which fits with Smiths
        return total_barrel_turns

    def get_key_turns_to_rewind_barrel_turns(self, barrel_turns):
        '''
        given a number of full rotations of the barrel, how many full key turns will be needed to wind back up fully?
        '''
        outer_r = self.barrel_diameter/2
        area_of_barrel = math.pi*outer_r**2

        inner_r = outer_r - barrel_turns * self.spring.thick

        area_of_inner = math.pi*inner_r**2

        area_of_spring_on_barrel_wall = area_of_barrel - area_of_inner

        length_of_used_spring = area_of_spring_on_barrel_wall / self.spring.thick

        area_of_used_spring = length_of_used_spring * self.spring.thick

        unused_spring_length = self.spring.length - length_of_used_spring
        area_of_unused_spring = unused_spring_length * self.spring.thick
        area_of_full_spring = self.spring.length * self.spring.thick
        arbor_radius = self.arbor_d_spring / 2
        area_of_spring_arbor = math.pi * arbor_radius ** 2

        radius_of_unused_spring_around_arbor = math.sqrt((area_of_unused_spring + area_of_spring_arbor)/math.pi)

        unused_spring_turns = (radius_of_unused_spring_around_arbor - arbor_radius) / self.spring.thick

        radius_of_fully_would_spring_around_arbor = math.sqrt((area_of_full_spring + area_of_spring_arbor)/math.pi)

        spring_wound_turns = (radius_of_fully_would_spring_around_arbor - arbor_radius) / self.spring.thick

        remaining_turns = spring_wound_turns - unused_spring_turns

        return remaining_turns


    def get_outer_diameter(self):
        return self.barrel_diameter + self.wall_thick*2

    def get_lid_fixing_screws_cutter(self, loose=False):
        cutter = cq.Workplane("XY")

        for i in range(self.lid_fixing_screws_count):
            #offset so it doesn't coincide with the spring hook
            pos = polar((i+0.25 )* math.pi * 2 / self.lid_fixing_screws_count, self.barrel_diameter / 2 + self.wall_thick / 2)

            cutter = cutter.add(self.lid_fixing_screws.get_cutter(self_tapping=True, loose=loose).rotate((0, 0, 0), (1, 0, 0), 180).translate(pos).translate((0, 0, self.base_thick + self.barrel_height + self.lid_thick)))

        return cutter

    def get_barrel_hole_d(self):
        return self.barrel_bearing.outer_d

    def get_front_bearing_standoff_washer(self):
        washer = cq.Workplane("XY").circle(self.lid_bearing.inner_safe_d_at_a_push/2).circle(self.arbor_d/2+0.2).extrude(self.front_bearing_standoff)

        return washer

    def get_inner_collet(self):
        '''
        if the ratchet is at the back (and barrely at front, still assumed), need a collet inside so the arbor can't just slip out backwards
        '''

        inner_r = self.arbor_d/2+self.collet_wiggle_room/2
        collet = cq.Workplane("XY").circle(self.collet_diameter / 2).extrude(self.back_collet_thick - self.back_bearing_standoff)
        collet = collet.faces(">Z").workplane().circle(self.key_bearing.inner_safe_d/2).extrude(self.back_bearing_standoff)

        cutoff_height = self.cutoff_height - self.collet_wiggle_room/2
        centre_cutout = cq.Workplane("XY").circle(inner_r).extrude(self.back_collet_thick).cut(cq.Workplane("XY").rect(self.collet_diameter, cutoff_height*2).extrude(self.back_collet_thick ).translate((0,-self.arbor_d/2)))

        collet =collet.cut(centre_cutout)

        screwshape = self.collet_screws.get_cutter(length=self.collet_diameter / 2).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, self.collet_diameter / 2, (self.back_collet_thick - self.back_bearing_standoff) / 2))

        collet = collet.cut(screwshape)

        return collet
    def get_barrel(self):
        barrel = cq.Workplane("XY").circle(self.barrel_diameter/2 + self.wall_thick).circle(self.key_bearing.outer_safe_d/2).extrude(self.base_thick)

        barrel = Gear.cutStyle(barrel, outer_radius=self.outer_radius_for_style, inner_radius=self.inner_radius_for_style, style=self.style,
                               clockwise_from_pinion_side=self.clockwise, rim_thick=0)

        barrel = barrel.faces(">Z").workplane().circle(self.barrel_diameter/2 + self.wall_thick).circle(self.barrel_diameter/2).extrude(self.barrel_height)

        barrel = barrel.cut(self.barrel_bearing.get_cutter().rotate((0,0,0),(1,0,0),180).translate((0,0,self.base_thick)))

        barrel = barrel.cut(self.get_lid_fixing_screws_cutter())
        #self.spring_hook_screws.getHeadHeight()
        #trying countersunk screw instead of pan head
        barrel = barrel.cut(self.spring_hook_screws.get_cutter(self_tapping=True, sideways=True, length=self.barrel_diameter).rotate((0,0,0),(0,0,1),-360/12).rotate((0, 0, 0), (0, 1, 0), 90).translate((0, 0, self.base_thick + self.barrel_height / 2)))



        return barrel




    def get_lid(self, for_printing = True):
        # lid = cq.Workplane("XY").circle(self.barrel_diameter/2 + self.wall_thick).circle(self.lid_hole_d/2).extrude(self.lid_thick)
        lid = cq.Workplane("XY").circle(self.barrel_diameter / 2 + self.wall_thick).extrude(self.lid_thick)
        lid = lid.cut(self.lid_bearing.get_cutter())
        # lid = lid.cut()
        lid = lid.cut(self.get_lid_fixing_screws_cutter(loose=True).translate((0,0,-self.base_thick - self.barrel_height)))

        lid = Gear.cutStyle(lid, outer_radius=self.outer_radius_for_style, inner_radius=self.inner_radius_for_style, style=self.style,
                            clockwise_from_pinion_side=self.clockwise, rim_thick=0)

        if for_printing:
            lid = lid.rotate((0,0,0),(1,0,0),180).translate((0,0,self.lid_thick))
        return lid

    def get_arbor(self, extra_at_back=0, extra_in_front=0, key_length=30, for_printing=True, ratchet_key_extra_length=0, back_collet_from_back=0):
        #standoff from rear bearing

        '''
        this needs to know almost everything about the plates - distance, endshake (to work out where to put the collets), thickness
        is it better off generating it in the ArborForPlate class?

        further thought - the collets could be made in the ArborForPlate class, leaving this a tiny bit at arm's reach?

        currently thinking it doesn't need bearings through the plates, it only rotates in the plates when winding.
        '''

        behind_spring_cylinder_length = self.internal_endshake / 2 + self.base_thick + extra_at_back

        in_front_spring_length = self.internal_endshake / 2 + self.lid_thick + self.front_bearing_standoff + extra_in_front

        arbor = cq.Workplane("XY").circle(self.arbor_d_spring / 2).extrude(self.barrel_height - self.internal_endshake)

        arbor = arbor.faces(">Z").workplane().circle(self.arbor_d/2).extrude(in_front_spring_length)

        # if self.ratchet_at_back:
        #     #instead of extending a cylinder all the way to the back of the back plate, we'll extend a polygon from the start of teh back collet
        #     arbor = arbor.faces("<Z").workplane().circle(self.arbor_d / 2).extrude(behind_spring_cylinder_length - (back_collet_from_back + self.ratchet_collet_thick))
        # else:
        arbor = arbor.faces("<Z").workplane().circle(self.arbor_d/2).extrude(behind_spring_cylinder_length)


        if self.ratchet_at_back:
            ratchet_key_length = ratchet_key_extra_length + self.ratchet_collet_thick + self.ratchet.thick
            arbor = arbor.faces("<Z").workplane().polygon(6, self.arbor_d).extrude(ratchet_key_length)
        arbor = arbor.faces(">Z").workplane().polygon(6, self.arbor_d).extrude(key_length)



        #line up with the base of the hexagon key
        arbor = arbor.rotate((0,0,0), (0,0,1),360/12)

        arbor = arbor.rotate((0,0,0),(0,1,0),90).translate((0,0,self.arbor_d/2 - self.cutoff_height))#.intersect(cq.Workplane("XY").rect(1000,1000).extrude(100))

        #chop off the bottom so this is printable horizontally
        arbor = arbor.cut(cq.Workplane("XY").rect(1000,1000).extrude(100).translate((0,0,-100)))



        #screwhole for spring hook
        screwhole_r = self.spring_hook_screws.get_diameter_for_die_cutting()/2
        #the die cutting never really worked, and printing with 0.6 nozzle not convinced it's helpful.
        screwhole_r = self.spring_hook_screws.get_rod_cutter_r()
        # screwhole = cq.Workplane("XY").circle(screwhole_r).extrude(self.spring_hook_screws.length - self.cutoff_height - self.spring_hook_space)
        # I think at one time I wanted this to not go all the way through. Now it just goes all the way through.
        screwhole = self.spring_hook_screws.get_cutter(self_tapping=True, ignore_head=True, length=self.spring_hook_screws.length - self.cutoff_height - self.spring_hook_space)
        screwhole = screwhole.translate(((self.barrel_height - self.internal_endshake)/2, 0, 0))
        arbor = arbor.cut(screwhole)

        #screwhole for ratchet collet
        top_z = self.key_containing_diameter - self.cutoff_height*2
        ratchet_screwhole_x = []
        if self.ratchet_at_back:
            ratchet_x = -behind_spring_cylinder_length - self.ratchet.thick - self.ratchet_collet_thick / 2
            back_collet_screwhole_x = -behind_spring_cylinder_length + back_collet_from_back + self.back_bearing_standoff + (self.back_collet_thick - self.back_bearing_standoff) / 2
            ratchet_screwhole_x = [ratchet_x, back_collet_screwhole_x]
        else:
            ratchet_screwhole_x = [self.barrel_height + self.internal_endshake + self.lid_thick + self.front_bearing_standoff + extra_in_front + self.ratchet.thick + self.ratchet_collet_thick / 2]
        collet_screwhole = cq.Workplane("XY")
        for x in ratchet_screwhole_x:
            collet_screwhole = collet_screwhole.add(cq.Workplane("XY").circle(self.lid_fixing_screws.metric_thread/2).extrude(self.arbor_d/2).translate((x,0,top_z/2 )))
        arbor = arbor.cut(collet_screwhole)

        #so it should line up better with the barrel
        arbor = arbor.translate((self.base_thick + self.internal_endshake/2,0,0))

        if not for_printing:
            arbor = arbor.rotate((0, 0, 0), (0, 1, 0), -90).translate((self.arbor_d/2, 0, 0))

        return arbor

    def get_encasing_radius(self):
        return self.barrel_diameter/2 + self.wall_thick

    def get_turns(self, cord_usage=0):
        '''
        we can ignore chain drop, this is just a fixed number of turns for the runtime
        '''
        return self.get_max_barrel_turns() * self.fraction_of_max_turns

    def get_height(self):
        #thought: should I be including the back standoff here? it's overriden when the plate distance is calculated
        #self.back_bearing_standoff +
        return self.base_thick + self.barrel_height + self.lid_thick + self.front_bearing_standoff

    def get_assembled(self):
        '''
        this is assembled such that it can be combined with the powered wheel, cord wheel conflates this a bit as it can't be combined
        '''
        return self.get_barrel()

    def get_model(self):
        model = self.get_barrel()

        model = model.add(self.get_lid(for_printing=False).translate((0,0,self.base_thick + self.barrel_height)))
        model = model.add(self.get_arbor(for_printing=False))

        return model

    def get_ratchet_gear_for_arbor(self):
        '''
        get the ratchet gear with a hole to slot over the key, and a space for a grub screw to fix it to the key
        '''
        gear = self.ratchet.get_gear()
        # if self.ratchet_at_back:
        outer_d = self.collet_diameter
        gear = gear.faces(">Z").workplane().circle(outer_d/2).extrude(self.ratchet_collet_thick)
        # means to hold screw that will hold this in place
        screwshape = self.collet_screws.get_cutter(length=outer_d/2).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -outer_d / 2, self.ratchet.thick + self.ratchet_collet_thick / 2))

        #TODO put a hole for a nut in the collet, instead of the arbor like it was previously

        # return screwshape
        gear = gear.cut(screwshape)
            # gear = gear.cut(self.collet_screws.getNutCutter(half=True).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -self.arbor_d / 2, self.ratchet.thick + self.ratchet_collet_thick/2)))
        gear = gear.faces(">Z").workplane().polygon(6, self.key_containing_diameter + self.collet_wiggle_room).cutThruAll()

        return gear

    def get_BOM(self):
        return None
        # instructions="""I recommend using a mainspring winder to put the mainspring in the barrel. It's possible by hand, but with a risk of harming yourself or the spring."""


    def get_printed_parts(self):
        return [
            # BillOfMaterials.PrintedPart("spring_barrel", self.get_barrel())
        ]

    def get_BOM_for_combining_with_arbor(self, wheel_thick=-1):
        instructions = """I recommend using a mainspring winder to put the mainspring in the barrel. It's possible by hand, but with a risk of harming yourself or the spring.
Screw the lid onto the barrel after putting the bearings, mainspring, and arbor into the barrel
"""
        bom = BillOfMaterials("Spring Barrel", assembly_instructions=instructions)

        bom.add_printed_part(BillOfMaterials.PrintedPart("lid", self.get_lid()))
        bom.add_item(BillOfMaterials.Item(f"{self.lid_fixing_screws} {self.lid_fixing_screws.length}mm", quantity=self.lid_fixing_screws_count))

        return bom

    def get_parts_for_arbor(self, wheel_thick=-1):
        '''
        The only part that's not combined with ArborForPlate is the lid
        TODO lid screws?
        '''
        return []


    def output_STLs(self, name="clock", path="../out"):
        out = os.path.join(path,"{}_spring_barrel.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_barrel(), out)

        out = os.path.join(path, "{}_spring_arbor.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_arbor(), out)

        out = os.path.join(path, "{}_spring_barrel_lid.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_lid(), out)

class WeightPoweredWheel:
    '''
    Base class with shared code for the weight power mechanisms like chain and cord
    '''

    @staticmethod
    def get_min_diameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 30

    def __init__(self, diameter=30, arbor_d=3, loose_on_rod=True, power_clockwise=True, use_key=False, ratchet_thick=5, ratchet_diameter=30):
        #diameter/circumference for the path the rope or chain takes. For the cord, this is the minimum diameter for the first layer of coils
        self.diameter=diameter
        self.circumference=math.pi * self.diameter
        self.ratchet = Ratchet()
        self.type = PowerType.NOT_CONFIGURED
        #if false, the powered wheel is fixed to the rod and the gear wheel is loose.
        self.loose_on_rod = loose_on_rod
        self.arbor_d = arbor_d
        self.power_clockwise = power_clockwise
        self.use_key = use_key
        self.ratchet_thick = ratchet_thick
        self.ratchet_diameter = ratchet_diameter
        self.pawl_thick = ratchet_thick - 0.6
        #TODO deprecated this and let it become the only type of ratchet
        self.traditional_ratchet = True
        self.pawl_screwed_from_front = False
        #TODO deprecate PowerType.is_weight and just use this instead on the base classes
        self.weight_powered = True
        self.configure_ratchet()

    def get_average_diameter(self):
        '''
        for the cord wheel the diameter can vary, hence "average", for most other types its consistent
        '''
        return self.diameter

    def get_model(self):
        '''
        get an assembled model that can be combined with the arbor for previews
        '''
        return None

    def get_encasing_radius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        return 30

    def configure_direction(self, power_clockwise=True):
        self.power_clockwise = power_clockwise
        # regenerate the ratchet
        self.configure_ratchet()

    def configure_ratchet(self):
        if self.ratchet_thick <=0:
            raise ValueError("Cannot make cord wheel without a ratchet")
        pawl_angle = 0
        if self.power_clockwise:
            click_angle = math.pi/2
        else:
            click_angle = -math.pi/2
        ratchet_diameter = self.ratchet_diameter
        if ratchet_diameter < 0:
            ratchet_diameter = self.diameter+6.5
        self.ratchet = TraditionalRatchet(gear_diameter=ratchet_diameter, thick=self.ratchet_thick, blocks_clockwise=self.power_clockwise,
                                          pawl_angle=pawl_angle, click_fixing_angle=click_angle, pawl_and_click_thick=self.pawl_thick,
                                          pawl_screwed_from_front=self.pawl_screwed_from_front)

    def get_chain_hole_diameter(self):
        '''
        Returns diameter of hole for the rope/chain/cord to pass through. It needs a hole to prevent winding the weight up too far
        '''
        raise NotImplementedError("TODO in child class")

    def is_clockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
        '''
        return self.power_clockwise

    def get_assembled(self):
        '''
        return 3D model of fully assembled wheel with ratchet (for the model, not printing)
        '''
        raise NotImplementedError("TODO in child class")

    def get_height(self):
        '''
        returns total thickness of the assembled wheel, with ratchet. If it needs a washer, this is included in the height
        '''
        raise NotImplementedError("TODO in child class")

    def get_BOM(self):
        '''
        return a BOM (or None) that will be added as a subcomponent to the arbor
        '''
        return None

    def get_BOM_for_combining_with_arbor(self, wheel_thick=-1):
        '''
         return a BOM (or None) that will have all its bits added to the parent BOM - useful for the parts only the power mechanism knows about but need to be included
        inthe arbor
        '''
        return None

    def get_chain_positions_from_top(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''
        raise NotImplementedError("TODO in child class")

    def get_screw_positions(self):
        '''
        return list of (x,y) positions, relative to the arbour, for screws that hold this wheel together.
        Only really relevant for ones in two halves, like chain and rope
        Used when we're not using a ratchet so the screwholes can line up with holes in the wheel
        '''
        raise NotImplementedError("TODO in child class")

    def get_turns(self, cord_usage=0):
        '''
        Given a chain drop, return number of rotations of this wheel.
        this is trivial for rope or chain, but not so much for the cord
        '''
        raise NotImplementedError("TODO in child class")

    def get_run_time(self, minuteRatio=1, cordLength=2000):
        '''
        print information about runtime based on the info provided
        '''
        raise NotImplementedError("TODO in child class")

    def get_encasing_radius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        return self.ratchet.get_max_radius()
    def get_rod_radius(self):
        '''
        get space behind* the powered wheel space so the gear train can fit the minute wheel

        *TODO power at rear and ordering of gears etc etc, for now assume power at hte front and minute wheel behind
        '''
        return self.arbor_d


class RopeWheel:
    '''
    Drop in replacement for chainwheel, but uses friction to hold a hemp rope

    first attempt tried using "teeth" to grip the rope. It worked, but added a lot of friction and chewed up teh rope.
    I've had a lot of success at retrofitting wheels with o-rings, so I want to try designing a wheel around using o-rings

    This is now based on the lightweight pully - printed in one peice with a hole for a steel tube in the centre
    '''

    @staticmethod
    def get_min_diameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 20

    def __init__(self, diameter, ratchet_thick, hole_d=STEEL_TUBE_DIAMETER_CUTTER, screw=None, rope_diameter=2.2, wall_thick=1, power_clockwise=True,
                 o_ring_diameter=3, arbor_d=3, use_o_rings=1, ratchet_outer_d=-1, ratchet_outer_thick=5, need_bearing_standoff=False):

        #diameter for the rope
        self.diameter=diameter
        self.circumference = math.pi*diameter

        #note, this actually has no effect on anything at the moment and is only for maintaining interface with other powered wheels
        self.loose_on_rod = True
        self.type = PowerType.ROPE

        self.need_bearing_standoff = need_bearing_standoff

        self.slope_angle = math.pi / 4
        self.rope_diameter = rope_diameter
        self.o_ring_diameter = o_ring_diameter
        self.use_o_rings = use_o_rings

        self.centre_wide = self.o_ring_diameter*self.use_o_rings

        self.wall_thick = wall_thick
        self.arbor_d = arbor_d

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
            self.ratchet = Ratchet(thick=ratchet_thick, totalD=ratchet_outer_d, innerRadius=self.outer_diameter/2, blocks_clockwise=power_clockwise, outer_thick=ratchet_outer_thick)
        else:
            self.ratchet = None

        print("rope wheel needs steel pipe of length {}mm".format(self.wheel_thick + self.bearing_standoff_thick))

    def get_rod_radius(self):
        '''
        get space behind* the powered wheel space so the gear train can fit the minute wheel

        *TODO power at rear and ordering of gears etc etc, for now assume power at hte front and minute wheel behind
        '''
        #TODO if there's ever an eight day version of this, it'll have the same winding mechanism as the cord wheel?
        return self.arbor_d

    def get_screw_positions(self):
        '''
        acn be printed in one peice, but still might want screw positions if we're being bolted to a wheel (eg huygen's)
        '''
        print("TODO screw positions for single-peice rope wheel")
        return []

    def is_clockwise(self):
        '''
        return true if this wheel is powered to rotate clockwise
        '''
        return self.power_clockwise

    def get_encasing_radius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        if self.ratchet is not None:
            return self.ratchet.outsideDiameter/2
        else:
            return self.outer_diameter/2

    def print_screw_length(self):
        if self.screw.countersunk:
            screwLength = self.get_height() - WASHER_THICK_M3
        else:
            screwLength = self.get_height() - WASHER_THICK_M3 - self.screw.get_head_height()
        #nut hole is extra deep by thickness of the ratchet
        print("RopeWheel needs: {} screw length {}-{}".format(self.screw.get_string(), screwLength, screwLength - self.ratchet_thick))

    def get_turns(self, cord_usage=0):
        return cord_usage/self.circumference

    def get_chain_hole_diameter(self):
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

        bearing_inner_safe_d = get_bearing_info(self.arbor_d).inner_safe_d

        if self.bearing_standoff_thick > 0 and bearing_inner_safe_d > self.hole_d:
            wheel = wheel.add(cq.Workplane("XY").circle(bearing_inner_safe_d/2).circle(self.hole_d/2).extrude(self.bearing_standoff_thick).translate((0,0,self.wheel_thick)))



        return wheel

    def get_wheel_with_ratchet(self):
        wheel = self.get_wheel().translate((0, 0, self.ratchet.thick)).add(self.ratchet.get_inner_wheel())

        wheel = wheel.cut(cq.Workplane("XY").circle(self.hole_d/2).extrude(self.get_height()))



        return wheel


    def get_assembled(self):
        if self.ratchet is not None:
            return self.get_wheel_with_ratchet()
        else:
            return self.get_wheel()

    def get_model(self):
        return self.get_assembled()

    def get_height(self):
        return self.wheel_thick + self.bearing_standoff_thick + self.ratchet_thick

    def output_STLs(self, name="clock", path="../out"):
        out = os.path.join(path,"{}_rope_wheel.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_assembled(), out)

    def get_chain_positions_from_top(self):
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

    def get_run_time(self,minuteRatio=1,chainLength=2000):
        #minute hand rotates once per hour, so this answer will be in hours
        return minuteRatio*chainLength/self.circumference

class WindingKeyBase:
    '''
    Base class for both the crank and spring winding key
    '''
    def __init__(self, key_containing_diameter, cylinder_length, key_hole_deep, key_sides=4, max_radius=-1, key_wiggle_room = 0.75,
                 wall_thick=2.5, handle_thick = 5):
        #the square bit the key slots over - what size is it?
        # self.square_side_length = square_side_length
        self.key_containing_diameter = key_containing_diameter
        #4 (square) or 6
        self.key_sides = key_sides
        #how long is the cylinder that will slot over the key? key_hole_deep needs to be less than this
        #increase this to ensure the key will be able to wind without crashing into the hands
        self.cylinder_length = cylinder_length
        #if the handle sticks out any more than this, it will crash into something
        self.max_radius = max_radius

        # how deep the hole that slots onto the square bit should be - keep shallow to ensure you can push the key all the way without crashing inot hte front plate or pushing the bearing out
        self.key_hole_deep = key_hole_deep


        self.wall_thick = wall_thick

        self.handle_thick = handle_thick

        #how much wider to make the hole than the square rod
        self.wiggle_room = key_wiggle_room

        self.cylinder_outer_diameter = self.key_containing_diameter + self.wall_thick * 2
        if self.key_hole_deep > self.cylinder_length:
            self.key_hole_deep = self.cylinder_length


    def get_key_hole_cutter(self):
        key_hole = cq.Workplane("XY").polygon(self.key_sides, self.key_containing_diameter + self.wiggle_room).extrude(self.key_hole_deep)
        key_hole = key_hole.translate((0,0,self.get_key_total_height() - self.key_hole_deep))
        return key_hole

    def get_key_outer_diameter(self):
        return self.cylinder_outer_diameter

    def get_handle(self, for_cutting=False, for_printing=False):
        raise NotImplementedError()

    def get_handle_z_length(self):
        raise NotImplementedError()

    def get_key_total_height(self):
        return self.cylinder_length + self.get_handle_z_length()

    def get_key(self, for_printing=True):
        raise NotImplementedError()

    def get_assembled(self):
        raise NotImplementedError()

    def output_STLs(self, name, path):
        out = os.path.join(path, "{}_winding_key.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_key(for_printing=True), out)

        out = os.path.join(path, "{}_winding_key_handle.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_handle(for_printing=True), out)

    def get_printed_parts(self):
        return [
            BillOfMaterials.PrintedPart("key", self.get_key(for_printing=True)),
            BillOfMaterials.PrintedPart("handle", self.get_handle(for_printing=True)),
        ]
class WindingKey(WindingKeyBase):
    '''
    A simple winding key with a grip, as usually used for winding a spring powered clock
    Printed sideways for strength
    '''


    def __init__(self, key_containing_diameter, cylinder_length, key_hole_deep, key_sides=4, max_radius=-1, key_wiggle_room=0.75,
                 wall_thick=2.5, handle_thick=5):
        if key_sides %2 !=0:
            raise ValueError("Polygon for key must have an even number of sides so screws can be used to secure handle")
        # adjust the wall thickness so that a screw can fit cleanly, with a small gap at the end, through the key. Assumes an even number of sides
        screw_length = get_incircle_for_regular_polygon(key_containing_diameter/2 + wall_thick, key_sides)*2
        #get_nearest_machine_screw_length() wasn't written when I did this. leaving it alone as it's fine though
        spare_space = (screw_length)%2
        # print(f"screws of length {screw_length - spare_space} needed, with a gap of {spare_space}")
        #gap between 0.3 and 0.6 should be fine
        #aiming for gap of 0.7 because this is not taking the actual algebra into account
        if spare_space < 0.3:
            #need tiny bit extra space
            need_extra = 0.7 - spare_space
            print(f"adding extra {need_extra}")
            wall_thick += need_extra/2
        elif spare_space > 0.6:
            need_extra = 2.7 - spare_space
            print(f"adding extra {need_extra}")
            wall_thick += need_extra / 2

        #the adjustment to wall_thick won't be exact as I don't want to work through that algebra. Should be close enough.

        self.screw_hole_length = get_incircle_for_regular_polygon(key_containing_diameter/2 + wall_thick, key_sides)*2
        spare_space = (self.screw_hole_length) % 2
        print(f"Winding Key: With a wall_thick of {wall_thick}, needs screws of length {self.screw_hole_length-spare_space}, which leaves a gap of {spare_space}")

        super().__init__(key_containing_diameter, cylinder_length, key_hole_deep, key_sides, max_radius, key_wiggle_room, wall_thick, handle_thick)

        self.key_grip_tall = max(self.cylinder_length * 0.4, 20)
        self.key_grip_wide = self.cylinder_outer_diameter * 2.5
        if self.max_radius >0 :
            if self.key_grip_wide/2 > self.max_radius:
                self.key_grip_wide = self.max_radius*2

        self.screw = MachineScrew(3, countersunk=True)

    def get_BOM(self):
        bom = BillOfMaterials("Winding key")
        bom.add_item(BillOfMaterials.Item(f"{self.screw} {get_nearest_machine_screw_length(self.screw_hole_length, self.screw)}mm", quantity=2, purpose="Handle fixing screws", object=self.screw))
        bom.add_item(BillOfMaterials.Item(f"M{self.screw.metric_thread} half nut", quantity=2, purpose="Handle fixing nuts"))

        bom.add_printed_parts(self.get_printed_parts())
        bom.add_model(self.get_assembled())
        return bom

    def get_let_down_adapter(self):

        adapter = cq.Workplane("XY").polygon(6, self.cylinder_outer_diameter).extrude(self.key_hole_deep + 10)
        adapter = adapter.cut(cq.Workplane("XY").polygon(self.key_sides, self.key_containing_diameter + self.wiggle_room).extrude(self.key_hole_deep))

        r = 11/(2 * math.cos(deg_to_rad(30)))
        adapter = adapter.faces(">Z").polygon(6,r*2).extrude(20)

        return adapter


    def get_handle(self, for_cutting=False, for_printing=False):

        r = self.key_grip_tall * 0.2
        thick = self.handle_thick
        if for_cutting:
            thick += 0.2
        small_r = 0.5
        grippy_bit = (cq.Workplane("XZ").moveTo(0, self.key_grip_tall / 2).rect(self.key_grip_wide, self.key_grip_tall).extrude(thick)
                      .edges("|Y").fillet(r).edges("|Z or |X").chamfer(small_r).translate((0,thick/2,0)))
        # if for_cutting:
        grippy_bit = grippy_bit.rotate((0,0,0),(0,0,1), 90)

        if not for_cutting:
            grippy_bit = grippy_bit.cut(self.get_screw_cutter())
        if for_printing:
            #put flat on the build plate
            grippy_bit = grippy_bit.rotate((0,0,0), (0,1,0), 90)

        return grippy_bit

    def get_handle_z_length(self):
        return self.key_grip_tall

    def get_key(self, for_printing=True):
        key = cq.Workplane("XY").polygon(6, self.cylinder_outer_diameter).extrude(self.cylinder_length + self.key_grip_tall)

        key = key.cut(self.get_key_hole_cutter())

        handle = self.get_handle(for_cutting=True)
        key = key.cut(handle)
        key = key.cut(self.get_screw_cutter())

        if for_printing:
            key = key.rotate((0,0,0), (1,0,0),90)

        return key

    def get_assembled(self, in_situ=True):
        key = self.get_key(for_printing=False)
        key = key.add(self.get_handle(for_cutting=False, for_printing=False))

        if in_situ:
            # for the model, standing on end lined up with the internal end of the key on the xy plane
            # so I can see where it would be if I was winding it up to check it won't clash with anything
            key = (key.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0, 0, 0), (0, 0, 1), 180)
                   .translate((0, 0, self.get_key_total_height() - self.key_hole_deep)))

        return key

    def get_screw_cutter(self):
        '''
        two screws will hold in the handle
        '''
        screw = self.screw.get_cutter(loose=True).rotate((0,0,0),(1,0,0), -90).translate((0,-self.screw_hole_length/2, 0))
        screw1 = screw.rotate((0,0,0), (0,0,1),rad_to_deg(math.pi*2/6)).translate((0,0, self.key_grip_tall/4))
        screw2 = screw.rotate((0, 0, 0), (0, 0, 1), -rad_to_deg(math.pi*2/6)).translate((0, 0, self.key_grip_tall * 3 / 4))

        nut = self.screw.get_nut_cutter(half=True).rotate((0,0,0),(1,0,0), -90).translate((0,-self.screw_hole_length/2, 0))
        nut1 = nut.rotate((0, 0, 0), (0, 0, 1), rad_to_deg(math.pi * 2 / 6 + math.pi)).translate((0, 0, self.key_grip_tall / 4))
        nut2 = nut.rotate((0, 0, 0), (0, 0, 1), -rad_to_deg(math.pi * 2 / 6 + math.pi)).translate((0, 0, self.key_grip_tall * 3 / 4))

        cutter = screw1.add(screw2).add(nut1).add(nut2)
        # cutter = cutter.add(cq.Workplane("XY").circle(self.screw_hole_length/2).extrude(3))

        return cutter


    def output_STLs(self, name, path):
        super().output_STLs(name, path)

        out = os.path.join(path, "{}_let_down_adapter.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_let_down_adapter(), out)


class WindingCrank(WindingKeyBase):
    '''
    winding crank with loose handle, printed upright as this appears to be strong enough
    '''
    def __init__(self,key_containing_diameter, cylinder_length, key_hole_deep, key_sides=4, max_radius=-1, key_wiggle_room = 0.75,
                 wall_thick=2.5, handle_thick = 5, knob_fixing_screw = None):
        super().__init__(key_containing_diameter, cylinder_length, key_hole_deep, key_sides, max_radius, key_wiggle_room, wall_thick, handle_thick)
        # screw for fixing the knob to the crank arm if this is a crank key, not needed otherwise
        self.knob_fixing_screw = knob_fixing_screw
        if self.knob_fixing_screw is None:
            self.knob_fixing_screw = MachineScrew(3, length=30)

        #only half the washer thick so the screw doesn't accidentally stick out the end
        self.knob_length = self.knob_fixing_screw.length - self.handle_thick - self.knob_fixing_screw.get_washer_thick()/2




    def get_handle(self, for_cutting=False, for_printing=False):
        #for_cutting not relevant in this case
        knob = cq.Workplane("XY").circle(self.cylinder_outer_diameter / 2).extrude(self.knob_length)


        nut_height_space = self.knob_fixing_screw.get_nut_height(nyloc=True)
        screw_hole = cq.Workplane("XY").circle(self.knob_fixing_screw.metric_thread/2).extrude(self.knob_length*1.5)
        screw_hole = screw_hole.add(self.knob_fixing_screw.get_nut_cutter(nyloc=True).translate((0, 0, self.knob_length - nut_height_space)))

        knob = knob.cut(screw_hole)

        return knob

    def get_BOM(self):

        instructions = """![Example Winding Crank](./winding_crank.jpg \"Example Winding Crank\")

Insert a nyloc nut into the base of the handle. Then screw the fixing screw through the crank, put a washer on the end and screw into the other end of the handle.

When assembled, the handle should be able to spin freely, but not wobble from side to side.
"""

        bom = BillOfMaterials("Winding Crank", instructions)
        bom.add_item(BillOfMaterials.Item(f"{self.knob_fixing_screw} {self.knob_fixing_screw.length}mm", purpose="Knob fixing screw"))
        bom.add_item(BillOfMaterials.Item(f"M{self.knob_fixing_screw.metric_thread} nyloc nut", purpose="Knob fixing nut"))
        bom.add_item(BillOfMaterials.Item(f"M{self.knob_fixing_screw.metric_thread} washer", purpose="Knob fixing washer"))
        bom.add_printed_parts(self.get_printed_parts())
        bom.add_model(self.get_assembled())

        bom.add_image("winding_crank.jpg")
        return bom

    def get_handle_z_length(self):
        return self.handle_thick

    def get_key(self, for_printing=True):
        '''
        winding key! this is one with a little arm and handle

        handle_length is to the end of the handle, not the middle of the knob (makes calculating the size of the key easier)

        Exact size of the key is based on the bearing and tolerance:
        key = cq.Workplane("XY").polygon(4, self.bearingInnerD - self.bearingWiggleRoom*2).extrude(self.keyKnobHeight)

        if withKnob, it's like an old longcase key with handle. If not, it's like a mantle key

        '''

        handle_tall = 0


        #base for handle
        key = cq.Workplane("XY").moveTo(-self.cylinder_outer_diameter / 2, 0).radiusArc((self.cylinder_outer_diameter / 2, 0), -self.cylinder_outer_diameter / 2).lineTo(self.cylinder_outer_diameter / 2, self.max_radius - self.cylinder_outer_diameter / 2).radiusArc((-self.cylinder_outer_diameter / 2, self.max_radius - self.cylinder_outer_diameter / 2), -self.cylinder_outer_diameter / 2).close().extrude(self.handle_thick)
        # hole to screw in the knob (loose)
        key = key.faces(">Z").workplane().tag("top").moveTo(0, self.max_radius - self.cylinder_outer_diameter / 2).circle(self.knob_fixing_screw.metric_thread / 2 + 0.2).cutThruAll()

        handle_tall = self.get_handle_z_length()

        #just a cylinder
        key = key.union(cq.Workplane("XY").circle(self.cylinder_outer_diameter / 2 + 0.0001).extrude(self.cylinder_length).translate((0, 0, handle_tall)))



        #5mm shorter than the key as a bodge to stand off from the front plate
        # key_hole = cq.Workplane("XY").polygon(self.key_sides, self.key_containing_diameter + self.wiggle_room).extrude(self.key_hole_deep).translate((0, 0, handle_tall + self.cylinder_length - self.key_hole_deep))

        key = key.cut(self.get_key_hole_cutter())

        if not for_printing:
            # for the model, standing on end lined up with the internal end of the key on the xy plane
            key = (key.rotate((0, 0, 0), (1, 0, 0), 180).rotate((0,0,0), (0,0,1),180)
                   .translate((0, 0, self.get_key_total_height() - self.key_hole_deep)))

        return key




    def get_assembled(self):
        key = self.get_key(for_printing=False)
        key = key.add(self.get_handle(for_cutting=False, for_printing=False).translate((0, self.max_radius - self.cylinder_outer_diameter / 2, self.get_key_total_height() - self.key_hole_deep  + self.knob_fixing_screw.get_washer_thick())))
        return key


class CordBarrel(WeightPoweredWheel):
    '''

    previous Cord Wheel, but I think barrel is more accurate and avoids confusion with the geared wheel itself

    This will be a replacement for the chainwheel, instead of using a chain this will be a coiled up clock cord.
    One end will be tied to the wheel and then the wheel wound up.

    Two options: use a key to wind it up, or have a double wheel and one half winds when the other unwinds, then you can tug the wound up side
    to wind up the weighted side.

    Made of two segments (one if using key) and a cap. Designed to be attached to the ratchet click wheel

    note - little cheap plastic bearings don't like being squashed, 24mm wasn't quite enough for the outer diameter.

    '''

    @staticmethod
    def get_min_diameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 21



    def __init__(self, diameter, ratchet_thick=4, power_clockwise=True, rod_metric_size=3, thick=10, use_key=False, screw_thread_metric=3,
                 cord_thick=2, bearing=None, key_square_bit_height=30,gear_thick=5, front_plate_thick=8, style=GearStyle.ARCS,
                 cord_length=2000, loose_on_rod=True, cap_diameter=-1, traditional_ratchet=True, ratchet_diameter=-1,
                 use_steel_tube=True, key_bearing_standoff = 1):
        '''
        loose_on_rod - if True (DEPRECATED) then the cord/chain/rope section of the wheel (this bit) is loose on the arbour .
         If false, then that is fixed and the actual gear wheel is loose on the arbour with a steel tube (PREFERRED)
        for now assume that is this is loose, it's just bare PETG on threaded rod, but if the wheel is loose it's a steel tube on the threaded rod. Also to consider are smaller diameter of bearings

        '''
        super().__init__(diameter=diameter, arbor_d=rod_metric_size, loose_on_rod=loose_on_rod, power_clockwise=power_clockwise, use_key=use_key,ratchet_thick=ratchet_thick, ratchet_diameter=ratchet_diameter)
        self.type = PowerType.CORD
        #if not loose_on_rod then we use a steel tube to slot over the threaded rod on teh wheel, leaving the cord barrel glued to the rod
        #however, to save on parts and faff, make the tube optional and allow plastic to just slide over the rod
        self.use_steel_tube =use_steel_tube
        # self.diameter=diameter
        #thickness of one segment (the bit where the cord coils up)
        self.thick=thick
        #if true, a key can be used to wind this cord wheel (if false, there are two cord winding segements)
        # self.use_key=use_key
        #1mm felt too flimsy
        #2mm was fine, but I'm trying to reduce depth as much as possible
        #note - if the clock is leaning forwards even slightly, then the cord can put a lot of weight on the top cap, bending it and forcing it against the front plate
        #beforeBearingExtraHeight helps compensate, but thicker caps do too
        self.cap_thick=1.6
        self.top_cap_thick = self.cap_thick

        # using as proxy for heavy
        self.heavy_duty = self.use_key
        self.fixing_screws = 2

        self.top_cap_overlap=0
        # even the 2mm cap got a bit wonky, so ensure lots of clearence from the front plate
        self.key_bearing_standoff = key_bearing_standoff

        if self.heavy_duty:
            #trying to prevent the end cap warping and rubbing against front plate
            #and there being a gap that the cord can get stuck down
            self.top_cap_thick = 3

            self.fixing_screws=4

            #I think I might be able get away with just using 3 screws and a thicker cap, and avoid this complication entirely
            #but it is implemented anyway, just might not print perfectly as the bridging hasn't been done
            # self.topCapOverlap = LAYER_THICK * 4
            self.top_cap_overlap = 0
            self.overlap_slot_wide= self.diameter * 0.075
            self.overlap_slot_wiggle=0.1

        #keeping large so there's space for the screws and screwheads
        if cap_diameter < 0:
            self.cap_diameter = diameter + 30#diameter*2#.5
        else:
            self.cap_diameter = cap_diameter
        self.rod_metric_size = rod_metric_size
        # self.arbor_d = rod_metric_size
        self.holeD = rod_metric_size
        #refers to the cord barrel, not the wheel
        self.loose_on_rod = loose_on_rod

        if self.loose_on_rod:
            self.holeD += LOOSE_FIT_ON_ROD

        self.screw_thread_metric=screw_thread_metric

        '''
        measurements for the 15mm inner diameter bearing, needs the extra outer d so it's not too tight a fit - since it's plastic I don't want it squashed in like the metal ones
        since I fear that might increase friction
        bearingInnerD=15, height=5, bearingLip=2.5, outer_d=24.2,
        '''

        if bearing is None:
            bearing = get_bearing_info(15)

        #only if useKey is true will this be used
        self.key_bearing = bearing
        print("cord wheel bearing:{}".format(self.key_bearing))
        # extra radius to subtract from the bit that goes through the large bearing for a key
        self.bearing_wiggle_room = 0.05
        #this is the square bit that sticks out the front of the clock. I suck at names
        self.key_square_bit_height=key_square_bit_height
        self.gear_thick = gear_thick
        self.front_plate_thick=front_plate_thick

        self.key_square_side_length = self.key_bearing.inner_d * 0.5 * math.sqrt(2)# self.key_bearing.innerD - self.bearingWiggleRoom * 2
        #TODO switch over to new WindingKey and containing diameter
        self.key_containing_diameter = self.key_bearing.inner_d - self.bearing_wiggle_room
        #default length, in mm
        self.cord_length_mm=cord_length
        #just for BOM
        self.weight_drop_mm = -1

        self.style = style
        # slowly switch over to using MachineScrews
        self.fixing_screw = MachineScrew(self.screw_thread_metric, countersunk=True)

        #how far from the centre are the screws that hold this together
        self.fixing_distance= self.diameter * 0.3

        if self.use_key:
            # self.fixing_distance= self.diameter / 2 - self.screw_thread_metric / 2 - 1.5
            self.fixing_distance = self.key_square_side_length / 2 + self.fixing_screw.get_head_diameter() / 2 + 0.5

        self.fixing_points = [polar(a * math.pi * 2 / self.fixing_screws, self.fixing_distance) for a in range(self.fixing_screws)]#[(self.fixingDistance,0), (-self.fixingDistance,0)]
        self.cord_thick=cord_thick

        self.ratchet_thick=ratchet_thick
        #so that the cord barrel base isn't rubbing up against the click and pawl (and they can move freely)
        #due to a (now fixed) but the original 0.6 had been doubled, but while I want to keep repoducing STLs for clock 40 as identical as i can I'll keep it
        #clocks 39 and 40 were printed with a pawl thick 1.2 thinner than the ratchet and seem to be fine. but going back to the original plan to see how that fares
        self.pawl_thick = ratchet_thick - 0.6
        self.ratchet_diameter = ratchet_diameter
        #TODO finish deprecating support for non-traditional ratchet
        self.traditional_ratchet=traditional_ratchet
        self.power_clockwise = power_clockwise
        self.configure_ratchet()


    def configure_weight_drop(self, weight_drop_mm, pulleys=1):
        self.cord_length_mm = weight_drop_mm * (pulleys + 1)
        self.weight_drop_mm = weight_drop_mm


    def get_screw_positions(self):
        return self.fixing_points

    def get_fixing_screw_length(self):
        if self.use_key:
            fixing_screw_length = self.ratchet.thick + self.cap_thick + self.thick + self.top_cap_thick
        else:
            raise NotImplementedError("TODO BOM screw length for non-key cord wheel")
        print(f"Cord wheel needs {self.fixing_screw} less than {fixing_screw_length:.1f}mm")
        fixing_screw_length = get_nearest_machine_screw_length(fixing_screw_length, self.fixing_screw)
        return fixing_screw_length

    def get_BOM(self):
        fixing_screw_length = self.get_fixing_screw_length()
        instructions =f"""
Insert the fixing nuts into the ratchet wheel, then slot the top cap over the cord barrel. Use the fixing screws through the top cap and barrel to fix the ratchet wheel onto the bottom of the barrel and hold the entire assembly together.

Thread the pivot rod through the centre of the cord barrel assembly, so the end of the rod ends up flush with the front of the key (the square bit). If the cord barrel is loose on the threaded rod I recommend a small amount of superglue to keep it in place. If the rod is able to rotate too easily then the barrel will come off the rod when winding the clock.# add rod item to the power mechanism sub component itself

Use the hole in the barrel to tie the cord, I recommend a [gnat hitch knot](https://www.animatedknots.com/gnat-hitch-knot) as it tightens itself after you tie it.

![Example cord barrel](./cord_barrel.jpg \"Example cord barrel\")
"""
        bom = BillOfMaterials("Cord barrel", assembly_instructions=instructions)
        bom.add_image("cord_barrel.jpg")
        model = self.get_assembled()
        bom.add_model(model)
        bom.add_model(model, svg_preview_options=BillOfMaterials.SVG_OPTS_SIDE_PROJECTION)
        bom.add_item(BillOfMaterials.Item( f"{self.fixing_screw} {fixing_screw_length:.0f}mm", quantity=self.fixing_screws, object=self.fixing_screw, purpose="Cord barrel fixing"))
        bom.add_item(BillOfMaterials.Item(f"M{self.fixing_screw.metric_thread} nut", quantity=4, purpose="Insert into ratchet gear to fix to bottom of cord barrel"))
        #keeping bearings with the plates as that makes more sense for assembling
        # bom.add_item(BillOfMaterials.Item(f"{self.key_bearing}", object=self.key_bearing, purpose="Bearing for key"))
        bom.add_item(BillOfMaterials.Item(f"Cord {self.cord_thick:.1f}mm thick", quantity=self.cord_length_mm + 150, purpose=f"Cord for weight. The weight needs to drop {self.weight_drop_mm / 1000:.2f}m so the cord length includes a little extra to account for the pulley and knots."))

        #moving to the arbor as that's where these are screwed in
        # if self.traditional_ratchet:
        #     #we know how thick the wheel is so we can calculate the lenght of screws needed to hold the pawl and click
        #     click_screw_length = get_nearest_machine_screw_length(wheel_thick + self.pawl_thick, self.ratchet.fixing_screws)
        #     pawl_screw_length = get_nearest_machine_screw_length(wheel_thick + self.ratchet_thick, self.ratchet.fixing_screws)
        #     bom.add_item(BillOfMaterials.Item(f"{self.ratchet.fixing_screws} {click_screw_length}mm", 2, object=self.ratchet.fixing_screws, purpose="Click screw"))
        #     bom.add_item(BillOfMaterials.Item(f"{self.ratchet.fixing_screws} {pawl_screw_length}mm", object=self.ratchet.fixing_screws, purpose="Pawl screw"))
        if not self.traditional_ratchet:
            raise NotImplementedError("TODO fixing screws for non-traditional ratchet")
        #steel tube dimensions only known in arbor for plate

        bom.add_printed_parts(self.get_printed_parts())

        return bom

    def get_BOM_for_combining_with_arbor(self, wheel_thick=0):
        '''
        get the bits which attach to the arbor rather than the cord barrel
        '''
        parts = []
        if self.traditional_ratchet:

            #we know how thick the wheel is so we can calculate the lenght of screws needed to hold the pawl and click
            click_screw_length = get_nearest_machine_screw_length(wheel_thick + self.pawl_thick, self.ratchet.fixing_screws)
            #want this as long as possible so it's loose and strong
            pawl_screw_length = get_nearest_machine_screw_length(wheel_thick + self.ratchet_thick, self.ratchet.fixing_screws)
            parts.append(BillOfMaterials.Item(f"{self.ratchet.fixing_screws} {click_screw_length}mm", 2, object=self.ratchet.fixing_screws, purpose="Click screw"))
            parts.append(BillOfMaterials.Item(f"{self.ratchet.fixing_screws} {pawl_screw_length}mm", object=self.ratchet.fixing_screws, purpose="Pawl screw"))

        assembly_instructions = f"""Attach the click to the front of the wheel with the two click screws. 

Screw the pawl screw into the wheel by itself, the pawl will sit loose on this screw and isn't held in until the clock is fully assembled and the cord barrel is in position.

![Example cord wheel](./cord_wheel.jpg \"Example cord wheel\")
"""

        bom = BillOfMaterials("Ratchet bits for arbor", assembly_instructions=assembly_instructions)
        bom.add_image("cord_wheel.jpg")
        bom.add_items(parts)
        return bom


    def get_chain_hole_diameter(self):
        (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.get_cord_turning_info()

        #assume that the cord is going to squish a bit, so don't need to make this too excessive
        return self.cord_thick * layers

    def get_average_diameter(self):
        '''
        for the cord wheel the diameter can vary, hence "average", for most other types its consistent
        '''
        (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.get_cord_turning_info(cordLength=self.cord_length_mm)

        return 2*(self.diameter / 2 + self.cord_thick * layers * 0.4)

    def get_chain_positions_from_top(self):
        '''
        Returns list of lists.  Each list is up to two coordinates. Only one coordinate if a round hole is needed
        but two coordinates [top, bottom] if the hole should be elongated.
        For example: chain would be just two round holes at the same z height [ [(-3,-5)], [(3,-5)]]
        Z coordinates are relative to the "front" of the chain wheel - the side furthest from the wheel
        (this is because the ratchet could be inset and the wheel could be different thicknesses)

         [ [(x,y),(x,y) ], [(x,y), (x,y)]  ]


        '''

        #not in the centre of hte layers, assuming that the cord will be fairly squashed, so offset slightly towards the wheel
        chainX = self.get_average_diameter()/2

        if self.use_key:
            #one hole only
            chainZTop = -self.key_bearing_standoff - self.top_cap_thick
            chainZBottom = chainZTop - self.thick

            side = 1 if self.ratchet.is_clockwise() else -1
            chainX *= side
            #don't worry about the pulley hole, the plates will do that if needed
            return [ [(chainX, chainZTop), (chainX, chainZBottom)] ]
        else:
            #make the weight segment the one nearer the wall to be consistent with old designs (idea was to ensure less flexing of plates, but as they've got closer this might
            #make the weight a bit close to teh wall?)
            weightSegmentBottomZ = - WASHER_THICK_M3 - self.top_cap_thick - self.thick - self.cap_thick - self.thick
            weightSegmentTopZ = - WASHER_THICK_M3 - self.top_cap_thick - self.thick - self.cap_thick
            windSegmentBottomZ = - WASHER_THICK_M3 - self.top_cap_thick - self.thick
            windSegmentTopZ = - WASHER_THICK_M3 - self.top_cap_thick

            if self.ratchet.is_clockwise():
                weightSide = 1
            else:
                weightSide = -1
            return [ [ (chainX*weightSide, weightSegmentTopZ), (chainX*weightSide, weightSegmentBottomZ) ], [(chainX*weightSide*(-1), windSegmentTopZ), (chainX*weightSide*(-1), windSegmentBottomZ)] ]


    def get_nut_holes(self):

        #rotate by 1/12th so there's a tiny bit more space near the main hole
        cutter = cq.Workplane("XY").add(get_hole_with_hole(self.screw_thread_metric, get_nut_containing_diameter(self.screw_thread_metric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).rotate((0, 0, 0), (0, 0, 1), 360 / 12).translate(self.fixing_points[0]))
        cutter = cutter.union(get_hole_with_hole(self.screw_thread_metric, get_nut_containing_diameter(self.screw_thread_metric, NUT_WIGGLE_ROOM), self.thick / 2, sides=6).rotate((0, 0, 0), (0, 0, 1), 360 / 12).translate(self.fixing_points[1]))
        return cutter

    def get_segment(self, front=True):
        #if front segment (only applies to non-key version), the holes for screws/nuts will be different

        #end is the cap
        segment = self.get_cap()

        #where the cord wraps
        segment = segment.faces(">Z").workplane().circle(self.diameter/2).extrude(self.thick)



        if self.use_key:
            #put the key on the top!

            #space for the cap

            # segment = segment.faces(">Z").workplane().moveTo(0, 0).circle(self.bearingInnerD / 2 + self.bearingLip).extrude(self.beforeBearingExtraHeight)
            segment = segment.faces(">Z").workplane().moveTo(0, 0).circle(self.key_bearing.inner_d / 2 - self.bearing_wiggle_room).extrude(self.key_bearing.height + self.key_bearing_standoff + self.top_cap_thick)
            #using polygon rather than rect so it calcualtes the size to fit in teh circle, rotating 45deg so we have more room for the screw heads
            #key = cq.Workplane("XY").polygon(4, self.key_bearing.innerD - self.bearingWiggleRoom * 2).extrude(self.keySquareBitHeight)
            key = cq.Workplane("XY").rect(self.key_square_side_length, self.key_square_side_length).extrude(self.key_square_bit_height)
            #.rotate((0,0,0),(0,0,1),45)
            segment = segment.union(key.translate((0, 0, self.cap_thick + self.thick + self.key_bearing.height + self.key_bearing_standoff + self.top_cap_thick)))



            if self.top_cap_overlap > 0 and not front:
                #overlapping slot
                overlap = cq.Workplane("XY").circle(self.diameter / 2).circle(self.diameter / 2 - self.overlap_slot_wide).extrude(self.top_cap_overlap)
                segment = segment.union(overlap.translate((0, 0, self.cap_thick + self.thick)))

            countersink = self.get_fixing_screws_cutter(self.thick + self.cap_thick + self.top_cap_thick)
            segment = segment.cut(countersink)



        #hole for the rod
        segment = segment.faces(">Z").circle(self.holeD/2).cutThruAll()

        #holes for the screws that hold this together
        #this can sometimes hang, not sure what conditions cause that.
        # segment = segment.faces(">Z").pushPoints(self.fixing_points).circle(self.screw_thread_metric / 2).cutThruAll()
        segment = segment.cut(cq.Workplane("XY").pushPoints(self.fixing_points).circle(self.screw_thread_metric / 2).extrude(self.thick*10))

        if front:
            #base of this needs space for the nuts (for the non-key version)
            #current plan is to put the screw heads in the ratchet, as this side gives us more wiggle room for screws of varying length
            segment = segment.cut(self.get_nut_holes())





        cord_hole_r = 1.5 * self.cord_thick / 2
        if cord_hole_r < 1.5:
            cord_hole_r = 1.5
        #weird things happenign without the +0.001 with a 1mm cord
        cord_hole_z = self.cap_thick + cord_hole_r + 0.001

        #TODO ensure this doesn't clash with the screws!
        cord_hole_y = self.diameter*0.25
        top_screw_y = max([pos[1] for pos in self.get_screw_positions()])
        if abs(cord_hole_y - top_screw_y) < self.fixing_screw.metric_thread/2 + cord_hole_r:
            #too close to screw hole
            cord_hole_y = top_screw_y - (self.fixing_screw.metric_thread/2 + cord_hole_r + 1)

        #cut a hole so we can tie the cord
        cord_hole = cq.Workplane("YZ").moveTo(cord_hole_y,cord_hole_z).circle(cord_hole_r).extrude(self.diameter*4).translate((-self.diameter*2,0,0))

        segment = segment.cut(cord_hole)

        return segment

    def get_fixing_screws_cutter(self, topOfScrewhead):
        '''
        countersink from top down
        '''

        countersink = cq.Workplane("XY")
        for fixingPoint in self.fixing_points:
            coneHeight = get_screw_head_height(self.screw_thread_metric, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE
            topR = get_screw_head_diameter(self.screw_thread_metric, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE
            countersink = countersink.add(cq.Solid.makeCone(radius2=topR, radius1=self.screw_thread_metric / 2,
                                                            height=coneHeight).translate((fixingPoint[0], fixingPoint[1], topOfScrewhead - coneHeight)))
            # punch thorugh the top circle so the screw can get in
            #self.beforeBearingExtraHeight
            top = cq.Workplane("XY").circle(topR).extrude(100).translate((fixingPoint[0], fixingPoint[1], topOfScrewhead))
            #this shuold be the same, but osmething is breaking the key section so leaving it alone for now
            # top = self.fixing_screw.get_cutter().rotate((0,0,0),(1,0,0),180).translate((fixingPoint[0], fixingPoint[1], topOfScrewhead))

            countersink = countersink.add(top)
        return countersink

    def get_cap(self, top=False, extraThick=0):
        capThick = self.top_cap_thick if top else self.cap_thick
        cap = cq.Workplane("XY").circle(self.cap_diameter / 2).extrude(capThick + extraThick)

        if top:
            #chamfer the inside edge - hoping this helps avoid the cord getting caught when winding on the round plates clock
            #where the tied end is in front of the barrel
            cap = cap.edges("<Z").chamfer((capThick + extraThick)*0.4)

        holeR = self.holeD / 2
        if self.use_key and top:
            holeR = self.key_bearing.inner_d / 2 + self.bearing_wiggle_room
            print("cord wheel cap holeR: {} innerSafe raduis:{}".format(holeR, self.key_bearing.inner_safe_d / 2))
            #add small ring to keep this further away from the bearing
            cap = cap.faces(">Z").workplane().circle(holeR).circle(self.key_bearing.inner_safe_d / 2).extrude(self.key_bearing_standoff)
            #add space for countersunk screw heads
            countersink = self.get_fixing_screws_cutter(capThick + extraThick)
            cap = cap.cut(countersink)

        if top and self.top_cap_overlap > 0:
            #overlap slot
            cutter = cq.Workplane("XY").circle(self.diameter/2).circle(self.diameter / 2 - self.overlap_slot_wide - self.overlap_slot_wiggle).extrude(self.top_cap_overlap)
            cap = cap.cut(cutter)

        # hole for the rod
        cap = cap.cut(cq.Workplane("XY").circle(holeR).extrude(capThick*10))

        # holes for the screws that hold this together
        cap = cap.faces(">Z").pushPoints(self.fixing_points).circle(self.screw_thread_metric / 2).cutThruAll()
        cap = Gear.cutStyle(cap, self.cap_diameter / 2 - self.holeD * 0.75, inner_radius=self.diameter / 2 + self.cord_thick, style=self.style, clockwise_from_pinion_side=self.power_clockwise)
        return cap

    def get_ratchet_wheel_for_cord(self, for_printing=True):

        '''
        Standalone clickwheel with holes for either screw heads or nuts.
        can't flip upside down for printing as there's a bit of extra height (clickWheelStandoffHeight) to keep the clicks away from the cap on top
        '''

        clickwheel = self.ratchet.get_inner_wheel()
        #can print upsidedown as we're increasing the thickness to stand off a bit from the base of the cord wheel
        bridging=False

        # hole for the rod
        clickwheel = clickwheel.cut(cq.Workplane("XY").circle(self.holeD / 2).extrude(self.thick*2))
        cutter = cq.Workplane("XY")
        if self.use_key:
            #space for a nut
            #screws can be slightly shorter than required, so might want to inset nuts slightly further
            extra_deep = (self.ratchet.thick + self.cap_thick + self.thick + self.top_cap_thick) - self.get_fixing_screw_length()
            for fixingPoint in self.fixing_points:
                cutter = cutter.add(self.fixing_screw.get_nut_cutter(height=self.fixing_screw.get_nut_height() + extra_deep,with_bridging=bridging, with_screw_length=1000).translate(fixingPoint))
        else:
            #cut out space for screwheads
            for fixingPoint in self.fixing_points:
                cutter = cutter.add(self.fixing_screw.get_cutter(with_bridging=True).translate(fixingPoint))
        clickwheel = clickwheel.cut(cutter)

        if self.traditional_ratchet and for_printing:
            clickwheel = clickwheel.rotate((0,0,0),(1,0,0),180).translate((0,0,self.ratchet.thick))

        return clickwheel


    def get_key_size(self):
        # return self.key_square_side_length
        return self.key_containing_diameter

    def get_key_sides(self):
        return 4

    def get_run_time(self, minuteRatio=1, cordLength=2000):
        '''
        minuteRatio is teeth of chain wheel divided by pinions of minute wheel, or just 1 if there aren't any chainwheels
        therefore the chain wheel rotates by 1/minuteRatio per hour

        assuming the cord coils perfectly, make a reasonable estimate at runtime
        '''
        (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.get_cord_turning_info(cordLength)

        print("layers of cord: {}, cord per hour: {:.1f}cm to {:.1f}cm min diameter: {:.1f}mm".format(layers, (cordPerRotationPerLayer[-1] / minuteRatio) / 10, (cordPerRotationPerLayer[0] / minuteRatio) / 10, self.diameter))
        print("Cord used per layer: {}".format(cordPerLayer))
        #minute hand rotates once per hour, so this answer will be in hours
        return (rotations * minuteRatio)

    def get_cord_turning_info(self, cordLength=-1):
        '''
        returns (rotations, layers, cordPerRotationPerLayer, cordPerLayer)
        '''

        if cordLength < 0:
            cordLength = self.cord_length_mm

        lengthSoFar = 0
        rotationsSoFar = 0
        coilsPerLayer = floor(self.thick / self.cord_thick)
        cordPerLayer=[]
        layer = 0
        cordPerRotationPerLayer = []
        while lengthSoFar < cordLength:

            circumference = math.pi * (self.diameter + 2 * (layer * self.cord_thick + self.cord_thick / 2))
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


    def get_turns(self, cord_usage):


        return self.get_cord_turning_info(cord_usage)[0]


    def get_assembled(self):
        '''
        for most of the other wheels this bit can be combined with the powered wheel - TODO tidy up
        '''
        model = self.get_ratchet_wheel_for_cord(for_printing=False)

        # if self.traditional_ratchet and not just_barrel:
        #     model = model.add(self.ratchet.get_pawl()).add(self.ratchet.get_click())

        if self.use_key:
            model = model.add(self.get_segment(False).translate((0, 0, self.ratchet.thick )))
            model = model.add(self.get_cap(top=True).translate((0, 0, self.ratchet.thick + self.thick + self.cap_thick)))
        else:
            model = model.add(self.get_cap().translate((0, 0, self.ratchet.thick)))
            model = model.add(self.get_segment(False).mirror().translate((0, 0, self.thick + self.cap_thick)).translate((0, 0, self.ratchet.thick + self.cap_thick )))
            model = model.add(self.get_segment(True).mirror().translate((0, 0, self.thick + self.cap_thick)).translate((0, 0, self.ratchet.thick + self.cap_thick + self.thick + self.cap_thick)))



        return model

    def get_model(self):
        return self.get_assembled()

    def get_height(self):
        '''
        total height, once assembled

        NOTE = includes height of a washer as part of the cordwheel (if not using key)
        '''

        if self.use_key:
            return self.ratchet.thick  + self.key_bearing_standoff + self.cap_thick + self.top_cap_thick + self.thick

        return self.ratchet.thick + self.cap_thick * 2 + self.top_cap_thick + self.thick * 2 + WASHER_THICK_M3

    def get_printed_parts(self):
        parts = [
            #previously "cordwheel_bottom_segment"
            BillOfMaterials.PrintedPart("barrel",self.get_segment(False), purpose="Cord wraps around this"),
            BillOfMaterials.PrintedPart("top_cap", self.get_cap(top=True), purpose="Top of cord barrel", printing_instructions="Print with extra elephant's foot to avoid lip on inside edge"),
            BillOfMaterials.PrintedPart("ratchet_wheel", self.get_ratchet_wheel_for_cord(), purpose="Fixed to base to form part of ratchet")
        ]
        if not self.use_key:
            # extra bits where the other cord coils up
            parts.append(BillOfMaterials.PrintedPart("centre_cap",self.get_cap(), purpose="Separates the two cord barrels"))

        return parts

    def output_STLs(self, name="clock", path="../out"):

        out = os.path.join(path, "{}_cordwheel_bottom_segment.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_segment(False), out)

        if self.use_key:
            out = os.path.join(path, "{}_cordwheel_top_cap.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_cap(top=True), out)
        else:
            # extra bits where the other cord coils up
            out = os.path.join(path, "{}_cordwheel_cap.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_cap(), out)

            out = os.path.join(path, "{}_cordwheel_top_segment.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_segment(True), out)

        out = os.path.join(path, "{}_cordwheel_click.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_ratchet_wheel_for_cord(), out)

class SprocketChainWheel(WeightPoweredWheel):
    '''
    I really want to be able to use heavier weights with a chain so I can do an eight grasshopper with simple maintaining power, so this is an attempt to make a
    stronger chainwheel using a sprocket sandwhiched between two large "washers"
    '''
    def __init__(self, ratchet_thick=0, chain=None, max_diameter=30, arbor_d=3, fixing_screws=None, fixings=3, power_clockwise=True, loose_on_rod=False, wall_thick=2):
        self.ratchet = ratchet

class PocketChainWheel2(WeightPoweredWheel):
    '''
    The PocketChainWheel was one of the first classes I wrote for the clocks, it's a mess and also the chain wheel doesn't cope well with heavy weights
    So this is an attempt to produce an improved pocket chain wheel and a tidier class

    still got a 'clunk' from this, which looked like it was due to teh chain twisting slightly so it ended up in the gap. Might try making that gap smaller.
    Also possible that the chainproducts chain is just not very high quality as it seems to hang twisted

    Works well with the heavy duty cousins chain (happy with 3kg). Looks like it might be occasionally slipping with the lighter regula 8 day chain. Need to investigate further.

    it does slip with the lighter Regula 8 day chain and a 1.25kg weight, however with a small counterweight of some M10 washers it doesn't slip anymore!
    So I think this is viable with old longcase style counterweights on the chains

    Worth trying on a 30 hour clock if I ever make one again?
    '''

    def __init__(self, ratchet_thick=0, chain=None, max_diameter=30, arbor_d=3, fixing_screws=None, fixings=3, power_clockwise=True, loose_on_rod=False, ratchet_outer_d=-1, ratchet_outer_thick=5, wall_thick=2):

        super().__init__(diameter=max_diameter, arbor_d=arbor_d, power_clockwise=power_clockwise, ratchet_thick=ratchet_thick, loose_on_rod=loose_on_rod)
        #no end cap on this one to stop the pawl escaping.
        self.pawl_screwed_from_front = True
        self.type = PowerType.CHAIN2
        # if false, the powered wheel is fixed to the rod and the gear wheel is loose.
        self.arbor_d = arbor_d

        self.chain = chain
        self.max_diameter = max_diameter
        self.hole_d  = arbor_d
        if self.loose_on_rod:
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

        self.pocket_cutter_cache = None
        self.chain_length = -1

    def get_BOM(self):
        return BillOfMaterials("Chain Pocket Wheel")

    def get_parts_for_arbor(self, wheel_thick):
        return []

    def configure_weight_drop(self, weight_drop_mm, pulleys=1):
        #we only really need to know this for the BOM
        self.chain_length = weight_drop_mm * (pulleys+1)

    def get_pocket_cutter(self):

        if self.pocket_cutter_cache is not None:
            return self.pocket_cutter_cache

        pocket_length = self.pocket_long#self.chain.inside_length + self.chain.wire_thick*2
        # print("pocket_length: {}, radius: {} {}".format(pocket_length, self.radius, 1 - (pocket_length**2)/(2*self.radius**2)))
        #from law of cosines
        pocket_angle = math.acos(1 - (pocket_length**2)/(2*self.radius**2))


        end_cylinder = cq.Workplane("XY").circle(self.pocket_wide/2).extrude(self.radius*2).translate((-self.pocket_wide/2,0,0)).rotate((0,0,0), (1,0,0),-90).rotate((0,0,0), (0,0,1), rad_to_deg(-pocket_angle / 2))
        start_cylinder = cq.Workplane("XY").circle(self.pocket_wide/2).extrude(self.radius*2).translate((self.pocket_wide/2,0,0)).rotate((0,0,0), (1,0,0),-90).rotate((0,0,0), (0,0,1), rad_to_deg(pocket_angle / 2))

        cutter = end_cylinder.union(start_cylinder)

        end_cylinder_centre_line = Line((math.cos(pocket_angle/2)*self.pocket_wide/2, math.sin(pocket_angle/2)*self.pocket_wide/2), angle=math.pi/2+pocket_angle/2)
        start_cylinder_centre_line = Line((-math.cos(pocket_angle / 2) * self.pocket_wide / 2, math.sin(pocket_angle / 2) * self.pocket_wide / 2), angle=math.pi / 2 - pocket_angle / 2)

        filler_centre = start_cylinder_centre_line.intersection(end_cylinder_centre_line)

        end_pos = np.add(end_cylinder_centre_line.start, polar(end_cylinder_centre_line.get_angle(), self.radius * 2))
        start_pos = np.add(start_cylinder_centre_line.start, polar(start_cylinder_centre_line.get_angle(), self.radius * 2))
        #
        filler = cq.Workplane("XY").moveTo(filler_centre[0], filler_centre[1]).lineTo(start_pos[0], start_pos[1]).lineTo(end_pos[0], end_pos[1]).close().extrude(self.pocket_wide).translate((0,0,-self.pocket_wide/2))
        cutter = cutter.union(filler)

        base_end = polar(end_cylinder_centre_line.get_angle(), self.radius - self.chain.wire_thick / 2)
        base_start = polar(start_cylinder_centre_line.get_angle(), self.radius - self.chain.wire_thick / 2)
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
            wheel = wheel.cut(self.get_pocket_cutter().rotate((0,0,0), (0,0,1), rad_to_deg(angle)))

        wheel = wheel.faces(">Z").workplane().circle(self.hole_d/2).cutThruAll()

        for pos in self.fixing_positions:
            wheel = wheel.cut(self.fixing_screws.get_cutter().rotate((0, 0, 0), (1, 0, 0), 180).translate(pos).translate((0, 0, self.wheel_thick / 2)))
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
            bottom = bottom.union(self.ratchet.get_inner_wheel())

            for pos in self.fixing_positions:
                bottom = bottom.cut(cq.Workplane("XY").circle(self.fixing_screws.metric_thread/2).extrude(self.get_height()).translate(pos))
                bottom = bottom.cut(self.fixing_screws.get_nut_cutter(height=self.ratchet.thick, with_bridging=True).rotate((0, 0, 0), (0, 0, 1), 360 / 12).translate(pos))
            bottom = bottom.faces(">Z").workplane().circle(self.hole_d / 2).cutThruAll()

        return bottom

    @staticmethod
    def get_min_diameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 22

    def get_encasing_radius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        we might not have a ratchet if hygens maintaining power is being used
        '''
        if self.ratchet is not None:
            return self.ratchet.get_max_radius()
        else:
            return self.outer_radius

    def get_chain_hole_diameter(self):
        '''
        Returns diameter of hole for the rope/chain/cord to pass through. It needs a hole to prevent winding the weight up too far
        '''
        return self.chain.width + 2

    def get_assembled(self):
        '''
        return 3D model of fully assembled wheel with ratchet (for the model, not printing)
        '''
        wheel = self.get_bottom_half()
        top = self.get_top_half().rotate((0,0,0),(1,0,0),180).translate((0,0,self.wheel_thick/2))
        bottom_thick = self.wheel_thick/2
        if self.ratchet is not None:
            bottom_thick += self.ratchet.thick
        model = wheel.add(top.translate((0,0,bottom_thick)))

        if self.traditional_ratchet:
            model = model.add(self.ratchet.get_pawl()).add(self.ratchet.get_click())

        return model

    def get_model(self):
        return self.get_assembled()

    def get_height(self):
        '''
        returns total thickness of the assembled wheel, with ratchet. If it needs a washer, this is included in the height
        '''
        height =  self.wheel_thick + SMALL_WASHER_THICK_M3
        if self.ratchet is not None:
            height += self.ratchet.thick
        return height

    def output_STLs(self, name="clock", path="../out"):
        '''
        save STL files to disc for all the objects required to print this wheel
        '''
        out = os.path.join(path, "{}_chain_wheel_bottom_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_bottom_half(), out)

        out = os.path.join(path, "{}_chain_wheel_top_half.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_top_half(), out)

    def get_chain_positions_from_top(self):
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

    def get_screw_positions(self):
        '''
        return list of (x,y) positions, relative to the arbour, for screws that hold this wheel together.
        Only really relevant for ones in two halves, like chain and rope
        Used when we're not using a ratchet so the screwholes can line up with holes in the wheel
        '''
        return self.fixing_positions

    def get_turns(self, cord_usage=0):
        '''
        Given a chain drop, return number of rotations of this wheel.
        this is trivial for rope or chain, but not so much for the cord
        '''
        return cord_usage / (self.pockets*self.chain.inside_length*2)

    def get_run_time(self, minuteRatio=1, cordLength=2000):
        '''
        print information about runtime based on the info provided
        '''
        return self.get_turns(cordLength)*minuteRatio

    def print_screw_length(self):
        '''
        print to console information on screws required to assemble
        '''
        if self.ratchet is None:
            print("No ratchet, can't estimate screw lenght")
            return
        minScrewLength = self.ratchet.thick + self.wheel_thick*0.75 + self.fixing_screws.get_nut_height()
        print("Chain wheel screws: {} max length {}mm min length {}mm".format(self.fixing_screws.get_string(), self.get_height(), minScrewLength))

    def get_rod_radius(self):
        '''
        get space behind* the powered wheel space so the gear train can fit the minute wheel

        *TODO power at rear and ordering of gears etc etc, for now assume power at hte front and minute wheel behind

        note - shared between most of the weight wheels, should really be in a base class
        '''

        return self.arbor_d
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
    def get_min_diameter():
        '''
        Return smallest sensible diameter, so the chain wheel ratio calculation can have something to work with
        '''
        return 22

    def is_clockwise(self):
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
        self.traditional_ratchet = False
        self.type = PowerType.CHAIN
        self.loose_on_rod = False
        self.holeD=holeD
        #complete absolute bodge!
        self.rodMetricSize=math.floor(holeD)
        self.arbor_d = self.rodMetricSize
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

        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference,self.get_run_time()))
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
            self.ratchet = Ratchet(totalD=ratchetOuterD, innerRadius=0.9999*self.outerDiameter / 2, thick=ratchet_thick, blocks_clockwise=power_clockwise, outer_thick=ratchetOuterThick)
        else:
            self.ratchet = None

    def get_encasing_radius(self):
        '''
        return the largest diameter of any part of this wheel - so other components can tell if they'll clash
        '''
        if self.ratchet is not None:
            return self.ratchet.outsideDiameter/2
        else:
            return self.outerRadius

    def get_turns(self, cord_usage=0):
        return cord_usage / self.circumference

    def get_chain_hole_diameter(self):
        #diameter of the hole in the bottom of the plate for the chain to dangle through
        return self.chain_width + 2

    def get_chain_positions_from_top(self):
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

    def get_turns(self, cord_usage=0):
        return cord_usage / (self.pockets*self.chain_inside_length*2)

    def get_height(self):
        '''
        Returns total height of the chain wheel, once assembled, including the ratchet
        includes washer as this is considered part of the full assembly
        '''
        thick = self.inner_width + self.wall_thick * 2 + WASHER_THICK_M3
        if self.ratchet is not None:
            thick += self.ratchet.thick
        return thick

    def get_run_time(self,minuteRatio=1,chainLength=2000):
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
                    halfWheel = halfWheel.cut(self.screw.get_cutter(with_bridging=True).translate(holePos))

            return halfWheel

    def get_screw_positions(self):
        return self.hole_positions

    def getWithRatchet(self, ratchet):


        chain =self.getHalf(True).translate((0, 0, ratchet.thick))

        clickwheel = ratchet.get_inner_wheel()
        combined = clickwheel.union(chain)

        #holes for screws
        # clickwheel = clickwheel.faces(">Z").workplane().circle(self.holeD / 2).moveTo(0, self.hole_distance).circle(self.screwD / 2).moveTo(0, -self.hole_distance).circle(self.screwD / 2).cutThruAll()
        for holePos in self.hole_positions:
            combined = combined.faces(">Z").workplane().moveTo(holePos[0], holePos[1]).circle(self.screw.metric_thread / 2).cutThruAll()
            # #to nearest 2mm
            #
            # heightForScrew = self.get_height()
            # if not self.screw.countersunk:
            #     heightForScrew-=self.screw.getHeadHeight()
            #
            # nearestScrewLength = round(heightForScrew/2)*2
            #TODO - work out best screw length and make nut holes only just as deep as they need.


            # half the height for a nut so the screw length can vary
            combined = combined.cut(self.screw.get_nut_cutter(with_bridging=True, height=(self.ratchet.thick + self.inner_width / 2 + self.wall_thick) / 2).translate(holePos))

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

    def print_screw_length(self):
        if self.ratchet is None:
            print("No ratchet, can't estimate screw lenght")
            return
        minScrewLength = self.get_height() - (self.ratchet.thick + self.inner_width/2 + self.wall_thick)/2 - self.screw.get_nut_height()
        print("Chain wheel screws: {} max length {}mm min length {}mm".format(self.screw.get_string(), self.get_height(), minScrewLength))


    def get_assembled(self):


        if self.ratchet is not None:
            assembly = self.getWithRatchet(self.ratchet)
        else:
            assembly = self.getHalf(sideWithClicks=True)

        chainWheelTop = self.getHalf().rotate((0,0,0),(1,0,0),180).translate((0, 0, self.get_height() - WASHER_THICK_M3))

        return assembly.add(chainWheelTop)

    def get_model(self):
        return self.get_assembled()

    def setRatchet(self, ratchet):
        self.ratchet=ratchet

    def get_rod_radius(self):
        '''
        get space behind* the powered wheel space so the gear train can fit the minute wheel

        *TODO power at rear and ordering of gears etc etc, for now assume power at hte front and minute wheel behind

        note - shared between most of the weight wheels, should really be in a base class
        '''

        return self.arbor_d

    def output_STLs(self, name="clock", path="../out"):

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

    def __init__(self, totalD=50, thick=5, blocks_clockwise=True, innerRadius=0, outer_thick=5, click_arms=-1, click_teeth=-1):
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
            self.click_inner_radius = self.clickInnerDiameter / 2
        else:
            self.click_inner_radius = innerRadius

        self.anticlockwise = -1 if blocks_clockwise else 1

        self.toothLength = max(self.outsideDiameter*0.025, 1)
        self.toothAngle = deg_to_rad(2) * self.anticlockwise

        self.toothRadius = self.outsideDiameter / 2 - self.outer_thick
        self.toothTipR = self.toothRadius - self.toothLength

        cicumference = math.pi*self.outsideDiameter

        #was originaly just 8. Then tried math.ceil(cicumference/10) to replicate it in a way that scales, but this produced slightly too many teeth.
        #even /15 seems excessive, trying /20 for reprinting bits of clock 19
        #allowing overrides since I keep messing with this logic and I need to retrofit a few ratchets
        click_multiplier = 4
        if click_arms < 0:
            if self.click_inner_radius/(self.outsideDiameter / 2) < 0.75:
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

    def is_clockwise(self):
        return self.anticlockwise == -1

    def get_inner_radius(self):
        #return radius of the solid bit in the centre
        return self.click_inner_radius

    def get_inner_wheel(self, extra_height = 0):
        '''
        Contains the ratchet clicks, hoping that PETG will be strong and springy enough, if not I'll have to go for screws as pinions and some spring wire (stainless steel wire might work?)
        Intended to be larger than the chain wheel so it can be printed as part of teh same object
        '''
        wheel = cq.Workplane("XY")

        thick = 1.25


        innerClickR = self.click_inner_radius

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

    def get_max_radius(self):
        return self.outsideDiameter/2

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

    note: no hole is provided in the ratchet gear, this class assumes it's adapted elsewhere (for spring barrel or cord wheel)

    '''

    def __init__(self, gear_diameter, thick=5, blocks_clockwise=True, fixing_screws=None, pawl_angle=math.pi / 2, click_fixing_angle =-math.pi /2, pawl_and_click_thick=-1, pawl_screwed_from_front=False):
        self.gear_diameter = gear_diameter
        self.thick = thick
        # for the cord wheel (and probably other weight driven wheels) it's useful to have the pawl and clickspring slightly less thick so they don't get wedged under the cord wheel base
        self.pawl_and_click_thick = pawl_and_click_thick
        if self.pawl_and_click_thick < 0:
            self.pawl_and_click_thick = self.thick
        self.blocks_clockwise = blocks_clockwise
        # by default set angle to pi/2 so the pawl is at the top of the ratchet - then if the spring fails gravity should help keep it locked in position
        #(only relevant to a spring barrel where the ratchet is on the plates, won't affect a cord movement)
        self.pawl_angle = pawl_angle

        self.click_fixing_angle = click_fixing_angle

        self.fixing_screws = fixing_screws
        if self.fixing_screws is None:
            self.fixing_screws = MachineScrew(3, countersunk=True)

        #if true then the head of the screw is in front of the pawl, so on a powered wheel it can't fall off
        self.pawl_screwed_from_front = pawl_screwed_from_front

        self.tooth_deep=3
        self.teeth = floor(self.gear_diameter / 2)

        self.tooth_angle = math.pi * 2 / self.teeth

        self.tooth_length = math.pi*self.gear_diameter/self.teeth

        self.pawl_diameter = self.fixing_screws.metric_thread*3

        self.spring_rest_length = self.pawl_diameter*2

        # self.gear_diameter = 2 * (self.max_diameter / 2 - self.pawl_diameter / 2 - self.tooth_deep * 2)

        # self.pawl_length = self.tooth_deep+self.pawl_diameter

        self.direction = -1 if self.blocks_clockwise else 1
        #TODO some way of ensuring it's "safe": it will stay locked without the spring
        #this should be a case of ensuring it's to the correct side of the line perpendicular to the tooth radial
        #I think this is also the same as ensuring it's on the "outside" of the tangent from the end of the tooth it locks against
        # self.pawl_fixing = polar(direction * self.tooth_angle*self.pawl_length, self.max_diameter/2 - self.pawl_diameter/2)

        #this should always be safe, pawl now spans aproximately two teeth
        self.pawl_fixing = (self.gear_diameter/2 + self.pawl_diameter/2, self.direction*self.tooth_length*2)

        self.pawl_fixing_angle = math.atan2(self.pawl_fixing[1], self.pawl_fixing[0])
        self.pawl_fixing_r = np.linalg.norm(self.pawl_fixing)

        if not self.is_pawl_position_safe():
            raise ValueError("Pawl is unsafe!")

        #pawl and gear and built in a position I could visualise, then rotated into requested position. the click is always built in the requested position
        self.rotate_by_deg = rad_to_deg(self.pawl_angle - math.atan2(self.pawl_fixing[1], self.pawl_fixing[0]))

        self.click_fixing_wide=self.fixing_screws.metric_thread*3
        # 0.9 works for a two-extrusion-wide click, but I think I want something stronger
        self.click_wide = 1.7  # 0.9
        # inside the little arm of the pawl
        self.click_end_pos = np_to_set(np.add(polar(self.pawl_fixing_angle, self.pawl_fixing_r + self.pawl_diameter / 3), polar(self.pawl_fixing_angle + self.direction * math.pi / 2, self.spring_rest_length * 0.5)))
        self.click_spring_r = np.linalg.norm(self.click_end_pos)
        self.click_fixings_r = self.click_spring_r - self.click_fixing_wide/2 + self.click_wide/2
        click_fixing_centre = polar(self.click_fixing_angle, self.click_fixings_r)
        self.click_fixings_distance = self.fixing_screws.metric_thread*3
        click_arc_angle = self.click_fixings_distance/self.click_fixings_r

        self.click_fixings = [
            # np_to_set(np.add(click_fixing_centre, polar(self.click_fixing_angle + math.pi / 2, self.click_fixings_distance / 2))),
            # np_to_set(np.add(click_fixing_centre, polar(self.click_fixing_angle - math.pi / 2, self.click_fixings_distance / 2)))
            polar(click_fixing_angle + click_arc_angle/2, self.click_fixings_r),
            polar(click_fixing_angle - click_arc_angle / 2, self.click_fixings_r)
        ]


    def get_inner_radius(self):
        '''
        get radius of a solid circle inside the gear wheel
        '''
        return self.gear_diameter/2 - self.tooth_deep

    def is_clockwise(self):
        return self.blocks_clockwise

    def get_pawl_screw_position(self):
        return rotate_vector(self.pawl_fixing, (0,0,1), deg_to_rad(self.rotate_by_deg))

    def get_screw_positions(self):
        return [self.get_pawl_screw_position()] + self.click_fixings

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


    def get_gear(self, extra_height = 0):
        gear = cq.Workplane("XY").moveTo(self.gear_diameter/2, 0)
        for tooth in range(self.teeth):
            start_angle = tooth * self.tooth_angle * self.direction
            end_angle = start_angle + self.tooth_angle * self.direction

            start_inner = polar(start_angle, self.gear_diameter/2 - self.tooth_deep)
            end = polar(end_angle, self.gear_diameter/2)

            gear = gear.lineTo(start_inner[0], start_inner[1]).radiusArc(end, -self.direction*self.gear_diameter/2)

        gear = gear.close()

        gear = gear.extrude(self.thick + extra_height)

        return gear.rotate((0,0,0),(0,0,1), self.rotate_by_deg)

    def get_inner_wheel(self, extra_height = 0):
        return self.get_gear(extra_height)

    def get_max_radius(self):
        #note: currently mainly used for teh cosmetic gear cutting on teh powered wheel
        return np.linalg.norm(self.pawl_fixing) + self.pawl_diameter/2

    def get_pawl(self):
        # pawl = cq.Workplane("XY").circle(3).translate(self.pawl_fixing)

        pawl_tip_pos = (self.gear_diameter/2 - self.tooth_angle, 0)
        pawl_direction = np.subtract(self.pawl_fixing, pawl_tip_pos)
        pawl_angle = math.atan2(pawl_direction[1], pawl_direction[0])
        pawl_from_centre_angle = math.atan2(self.pawl_fixing[1], self.pawl_fixing[0])

        tooth_inner = (self.gear_diameter/2-self.tooth_deep, 0)
        next_tooth_outer = polar(self.direction * self.tooth_angle, self.gear_diameter/2)

        pawl_inner = np_to_set(np.add(self.pawl_fixing, polar(pawl_angle + self.direction * math.pi / 2, self.pawl_diameter / 2)))
        pawl_outer = np_to_set(np.add(self.pawl_fixing, polar(pawl_angle - self.direction * math.pi / 2, self.pawl_diameter / 2)))
        pawl_base = np_to_set(np.add(self.pawl_fixing, polar(pawl_from_centre_angle + math.pi + -self.direction * self.tooth_angle, self.pawl_diameter / 2)))

        #contact with the tooth
        pawl = cq.Workplane("XY").moveTo(tooth_inner[0], tooth_inner[1]).lineTo(self.gear_diameter/2, 0)

        pawl = pawl.spline([pawl_outer], tangents=[None, polar(pawl_angle, 1)], includeCurrent=True)
        # #round the back of the fixing
        pawl = pawl.radiusArc(pawl_inner, -self.direction*(self.pawl_diameter/2+0.0001))
        #carry on round to near the base
        pawl = pawl.radiusArc(pawl_base, -self.direction*(self.pawl_diameter/2+0.0001) )
        #curve to the tip of the next tooth then along the tooth shape
        pawl = pawl.tangentArcPoint(next_tooth_outer, relative=False).radiusArc(tooth_inner, self.direction * self.gear_diameter / 2)

        pawl = pawl.close().extrude(self.pawl_and_click_thick)



        #bit for the spring to rest against
        # pawl = pawl.union(cq.Workplane("XY").rect(self.pawl_diameter/2, self.spring_rest_length).extrude(self.thick).translate(self.pawl_fixing).translate((self.pawl_diameter/4,-self.spring_rest_length/2)))
        spring_rest_top_start = polar(self.pawl_fixing_angle, self.pawl_fixing_r + self.pawl_diameter/2)
        spring_rest_top_end = np_to_set(np.add(spring_rest_top_start, polar(self.pawl_fixing_angle + self.direction * math.pi / 2, self.spring_rest_length)))
        spring_rest_bottom_end = np_to_set(np.add(spring_rest_top_end, polar(self.pawl_fixing_angle + math.pi, self.pawl_diameter / 2)))

        #
        pawl = pawl.union(cq.Workplane("XY").moveTo(spring_rest_top_start[0], spring_rest_top_start[1])
                          .lineTo(spring_rest_top_end[0], spring_rest_top_end[1])
                          .radiusArc(spring_rest_bottom_end, -self.direction *1.001* self.pawl_diameter/4)
                          .lineTo(self.pawl_fixing[0], self.pawl_fixing[1])
                          .close().extrude(self.pawl_and_click_thick))
        if self.pawl_screwed_from_front:
            pawl = pawl.cut(self.fixing_screws.get_cutter(loose=True).rotate((0,0,0),(1,0,0),180).translate((self.pawl_fixing[0], self.pawl_fixing[1], self.pawl_and_click_thick)))
        else:
            #plain hole for pawl
            pawl = pawl.faces(">Z").workplane().moveTo(self.pawl_fixing[0], self.pawl_fixing[1]).circle((self.fixing_screws.metric_thread + LOOSE_FIT_ON_ROD) / 2).cutThruAll()
        # return pawl

        return pawl.rotate((0,0,0),(0,0,1), self.rotate_by_deg)

    def get_little_plate_for_pawl_screw_positions(self):


        pawl_position = rotate_vector(self.pawl_fixing, (0,0,1), deg_to_rad(self.rotate_by_deg))
        pawl_distance = np.linalg.norm(pawl_position)

        distance_1 = pawl_distance + self.pawl_diameter*1.25 + self.fixing_screws.metric_thread
        distance_2 = distance_1 + self.fixing_screws.metric_thread*2 + self.thick


        screw_positions= [polar(self.pawl_angle, distance_1), polar(self.pawl_angle, distance_2)]


        return screw_positions

    def get_little_plate_for_pawl(self):
        '''
        If the pawl is attached to a front/back plate I fear that a screw through the plate will need some support to prevent bending part of the plate
        this is a little part designed to screw onto that plate and hold the pawl screw from both ends

        This may be better placed in the Plates class? not sure yet
        '''

        plate_width = self.fixing_screws.metric_thread*4
        #extra for washers
        body_thick = self.pawl_and_click_thick + WASHER_THICK_M3*2 + 0.5

        total_thick = body_thick + 5# max(self.thick, 5)

        plate_screw_positions = self.get_little_plate_for_pawl_screw_positions()
        pawl_screw_position = self.get_pawl_screw_position()

        plate = get_stroke_line([plate_screw_positions[1], pawl_screw_position], wide = plate_width, thick=total_thick)

        plate = plate.faces(">Z").workplane().pushPoints(plate_screw_positions + [pawl_screw_position]).circle(self.fixing_screws.metric_thread/2).cutThruAll()

        plate = plate.cut(cq.Workplane("XY").moveTo(pawl_screw_position[0], pawl_screw_position[1]).circle(self.pawl_diameter).extrude(body_thick))

        return plate




    def get_click(self):


        click_end_pos = self.click_end_pos

        click_end_pos = rotate_vector(click_end_pos, (0,0,1), deg_to_rad(self.rotate_by_deg))

        # click_fixing = cq.Workplane("XY").moveTo(self.click_fixings_r,0).rect(self.click_fixing_wide, self.click_fixings_distance + self.click_fixing_wide).extrude(self.thick).rotate((0,0,0), (0,0,1), rad_to_deg(self.click_fixing_angle))

        click_fixing = get_stroke_arc(self.click_fixings[1], self.click_fixings[0], self.click_fixings_r, wide=self.click_fixing_wide+0.0001, thick=self.pawl_and_click_thick)

        # click_fixing = click_fixing.edges("|Z").fillet(2)

        # click = click.union(cq.Workplane("XY").circle(self.click_fixings_r + self.click_wide/2).circle(self.click_fixings_r - self.click_wide/2).extrude(self.thick))

        line_to_click_end = Line((0,0), another_point=click_end_pos)

        click_end_inner_pos = np_to_set(np.subtract(click_end_pos, np.multiply(line_to_click_end.dir, self.click_wide / 2)))
        click_end_outer_pos = np_to_set(np.add(click_end_pos, np.multiply(line_to_click_end.dir, self.click_wide / 2)))

        click_spring_r = self.click_spring_r
        click_start_outer = polar(self.click_fixing_angle, self.click_fixings_r + self.click_wide / 2)
        click_start_inner = polar(self.click_fixing_angle, self.click_fixings_r - self.click_wide / 2)

        # clickspring = (cq.Workplane("XY").moveTo(click_start_outer[0], click_start_outer[1]).radiusArc(click_end_outer_pos, self.direction*(click_spring_r+self.click_wide/2)).
        #                lineTo(click_end_inner_pos[0], click_end_inner_pos[1]).radiusArc(click_start_inner, -self.direction*(click_spring_r - self.click_wide/2)).close().extrude(self.thick))

        # click_end_pos_angle = math.atan2(self.click_end_pos[1], self.click_end_pos[0])
        # pawl_angle = rationalise_angle(click_end_pos_angle)

        # click_angle = rationalise_angle(self.click_fixing_angle)

        # using unit vectors to make this easier
        pawl_dir = np_to_set(np.multiply(click_end_pos, 1/np.linalg.norm(click_end_pos)))
        click_dir = polar(self.click_fixing_angle)

        #I want the clockwise (if blocks_clockwise) or anticlockwise (if not blocks_clockwise) angle from the clock to the pawl
        #I think without headaches this is easier to do via dot or cross product

        from_dir = click_dir
        to_dir = pawl_dir
        # if self.blocks_clockwise:
        #     to_dir = click_dir
        #     from_dir = to_dir
        # work out if the angle we want to keep is >180deg, then either cut or include a segment of a circle
        dot_product = np.dot(from_dir, to_dir)
        small_angle = math.acos(dot_product)
        cross_product = np.cross(from_dir, to_dir)
        # if cross_product

        if self.blocks_clockwise:
            want_small_angle = cross_product > 0
        else:
            want_small_angle = cross_product < 0

        # print("want the SMALL ANGLE", want_small_angle)


        clickspring = cq.Workplane("XY").circle(click_spring_r + self.click_wide / 2).circle(click_spring_r - self.click_wide / 2).extrude(self.pawl_and_click_thick)
        wedge_r = click_spring_r * 5
        start = np_to_set(np.multiply(pawl_dir, wedge_r))
        end = np_to_set(np.multiply(click_dir, wedge_r))
        start_angle = math.atan2(pawl_dir[1], pawl_dir[0])
        #I'll be honest this was instinctive after playing about and I'm not sure I could tell you why it works
        dir = 1 if want_small_angle != self.blocks_clockwise else -1
        #making a funny shape rather than a wedge as I can't think through the clockwise logic needed for radiusarc
        mid_angle = start_angle + dir*small_angle*0.5
        mid = polar(mid_angle, wedge_r)

        # dir = -1 if self.blocks_clockwise else 1
        # small_angle_wedge = cq.Workplane("XY").lineTo(start[0], start[1]).radiusArc(end, wedge_r*dir).lineTo(0,0).close().extrude(self.thick)
        small_angle_wedge = cq.Workplane("XY").lineTo(start[0], start[1]).lineTo(mid[0], mid[1]).lineTo(end[0], end[1]).lineTo(0,0).close().extrude(self.pawl_and_click_thick)
        # return small_angle_wedge
        if want_small_angle:
            clickspring = clickspring.intersect(small_angle_wedge)
        else:
            clickspring = clickspring.cut(small_angle_wedge)

        clickspring = clickspring.union(cq.Workplane("XY").moveTo(click_end_pos[0], click_end_pos[1]).circle(self.click_wide / 2).extrude(self.pawl_and_click_thick))

        #this hangs forever sometimes... (added 0.0001 to click fixing radius above seems to fix)
        click = click_fixing.union(clickspring)
        # click = click_fixing

        for screwpos in self.click_fixings:
            if self.pawl_screwed_from_front:
                click = click.cut(self.fixing_screws.get_cutter().rotate((0,0,0),(1,0,0),180).translate((screwpos[0], screwpos[1], self.pawl_and_click_thick)))
            else:
                # click = click.cut(cq.Workplane("XY").circle(self.fixing_screws.get_rod_cutter_r()).extrude(self.pawl_and_click_thick).translate(screwpos))
                click = click.cut(self.fixing_screws.get_cutter(self_tapping=True, length=self.pawl_and_click_thick, ignore_head=True).translate(screwpos))

        return click

    def get_assembled(self):
        return self.get_gear().add(self.get_pawl()).add(self.get_click())