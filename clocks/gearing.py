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

import random

from .geometry import *
from .utility import *

import cadquery as cq
import os
from cadquery import exporters
# from random import *

from .types import *

from clocks.cq_gears import BevelGearPair

class Gear:
    '''
    A gear represents a wheel or pinion, but holds no information about its thickness, it's largely for generating 2D representations that the Arbor class can turn into
    3D object.

    There is some blurring of lines with the lantern pinions, and I'm unsure what the best solution is, so for now it's a bit of a muddle
    '''

    @staticmethod
    def cutStyle(gear, outerRadius, innerRadius = -1, style=None, clockwise_from_pinion_side=True, rim_thick=-1):
        '''
        Could still do with a little more tidying up, outerRadius should be a few mm shy of the edge of teh gear to give a solid rim,
        but innerRadius should be at the edge of whatever can't be cut into

        I keep changing my mind whether or not to give the cutter the full size of the gear or just the area to cut.

        clockwise - assume this wheel is turning clockwise from the perspective of the side with the pinion
        '''
        #TODO - why did I used to pass this through to all the cutters?
        if innerRadius < 0:
            innerRadius = 3
        #thought - some things (caps for cord wheel?) don't need a thick rim
        #rimThick = max(outerRadius * 0.175, 3)
        if rim_thick < 0:
            rim_thick = max(outerRadius * 0.15, 2.5)
        outerRadius -= rim_thick
        # lots of old designs used a literal string "HAC"
        if style == GearStyle.ARCS or style == GearStyle.ARCS.value:
            if innerRadius < outerRadius*0.5:
                innerRadius=outerRadius*0.5
            return Gear.cutHACStyle(gear, outer_r=outerRadius, inner_r=innerRadius)
        if style == GearStyle.ARCS2:
            return Gear.cutArcsStyle(gear, outer_r=outerRadius, inner_r=innerRadius+2)
        if style == GearStyle.CIRCLES:
            return Gear.cut_circles_style(gear, outer_radius=outerRadius, inner_radius=innerRadius, hollow=False)
        if style == GearStyle.MOONS:
            return Gear.cut_circles_style(gear, outer_radius=outerRadius, inner_radius=innerRadius, moons=True)
        if style == GearStyle.CIRCLES_HOLLOW:
            return Gear.cut_circles_style(gear, outer_radius=outerRadius, inner_radius=innerRadius + 2, hollow=True)
        if style == GearStyle.SIMPLE4:
            return Gear.cutSimpleStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius+2, arms=4)
        if style == GearStyle.SIMPLE5:
            return Gear.cutSimpleStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius+2, arms=5)
        if style == GearStyle.SPOKES:
            return Gear.cutSpokesStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius+2)
        if style == GearStyle.STEAMTRAIN:
            return Gear.cutSteamTrainStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius+2)
        if style == GearStyle.CARTWHEEL:
            return Gear.cutSteamTrainStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius+2, withWeight=False)
        if style == GearStyle.FLOWER:
            return Gear.cutFlowerStyle2(gear, outerRadius=outerRadius, innerRadius=innerRadius)
        if style == GearStyle.HONEYCOMB:
            return Gear.cutHoneycombStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius + 2)
        if style == GearStyle.HONEYCOMB_SMALL:
            return Gear.cutHoneycombStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius + 2, big=False)
        if style == GearStyle.HONEYCOMB_CHUNKY:
            return Gear.cutHoneycombStyle(gear, outerRadius=outerRadius, innerRadius=innerRadius + 2, big=False, chunky=True)
        if style == GearStyle.SNOWFLAKE:
            return Gear.cutSnowflakeStyle(gear, outerRadius= outerRadius, innerRadius = innerRadius + 2)

        if style == GearStyle.CURVES:
            return Gear.cutCurvesStyle(gear, outerRadius=outerRadius, innerRadius=max(innerRadius*1.05, innerRadius+1), clockwise=clockwise_from_pinion_side)
        if style == GearStyle.DIAMONDS:
            return Gear.cut_diamonds_style(gear, outerRadius=outerRadius, innerRadius=max(innerRadius * 1.05, innerRadius + 1))
        return gear

    @staticmethod
    def get_thin_arm_thickness(outer_radius, inner_radius):
        arm_thick = max(outer_radius * 0.1, 1.8)  # 1.8 is the size of the honeycomb walls
        # print("arm_thick", arm_thick)
        if arm_thick < 2.7:
            # arms that were slightly bigger ended up with a gap. probably need to ensure we're a multiple of 0.45?
            return 1.75
        if arm_thick < 3:
            return 2.7

        return arm_thick

    @staticmethod
    def get_thick_arm_thickness(outer_radius, inner_radius):
        arm_thick = max(outer_radius * 0.1, 1.8)  # 1.8 is the size of the honeycomb walls
        # print("arm_thick", arm_thick)
        if arm_thick < 3:
            return 2.7

        return arm_thick

    @staticmethod
    def cut_diamonds_style(gear, outerRadius, innerRadius):
        arm_thick = Gear.get_thick_arm_thickness(outerRadius, innerRadius)
        # arm_thick=2.7
        diamonds = 7

        centre_r = (outerRadius + innerRadius)/2

        centre_gap = outerRadius - innerRadius
        ratio = innerRadius/outerRadius

        narrow_gap = False

        if ratio > 0.6:
            narrow_gap = True
            #if the gap is narrow just cut out shapes of diamonds and increase the number of diamonds to reduce their width
            diamonds = floor(ratio*12)
            # arm_thick*=0.5
            # if arm_thick < 3:
            #     arm_thick = 1.9
            # diamond_width*=0.5
        # if innerRadius/outerRadius < 0.

        diamond_width = math.pi * centre_r * 2 / diamonds

        cutter_thick = 100

        if narrow_gap:
            cutter = cq.Workplane("XY")
        else:
            cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutter_thick)



        for d in range(diamonds):

            other_shapes_angle = (d + 0.5) * math.pi * 2 / diamonds

            next_diamond_angle = (d + 1) * math.pi * 2 / diamonds
            diamond_angle = d * math.pi * 2 / diamonds
            diamond_wide_angle = diamond_width / centre_r

            left_point = polar(diamond_angle - diamond_wide_angle / 2, centre_r)
            right_point = polar(diamond_angle + diamond_wide_angle / 2, centre_r)
            top_point = polar(diamond_angle, outerRadius)
            bottom_point = polar(diamond_angle, innerRadius)


            if narrow_gap:
                arm_angle = arm_thick / ((outerRadius + innerRadius)/2)
                # top_point = polar(diamond_angle, outerRadius + arm_thick)
                # bottom_point = polar(diamond_angle, innerRadius - arm_thick)
                left_point = polar(diamond_angle - diamond_wide_angle / 2 + arm_angle/2, centre_r)
                right_point = polar(diamond_angle + diamond_wide_angle / 2 - arm_angle/2, centre_r)


                diamond = cq.Workplane("XY").moveTo(left_point[0], left_point[1]).lineTo(top_point[0], top_point[1]).lineTo(right_point[0], right_point[1]).lineTo(bottom_point[0],bottom_point[1]).close().extrude(cutter_thick)
                cutter = cutter.add(diamond)
                # cutter = cutter.cut(get_stroke_line([top_point, right_point, bottom_point, left_point], wide=arm_thick, thick=cutter_thick, loop=True))
            else:




                diamond = get_stroke_line([top_point, right_point, bottom_point, left_point], wide=arm_thick, thick=cutter_thick, loop=True)

                cutter = cutter.cut(diamond)

            # diamond = cq.Workplane("XY").moveTo(left_point[0], left_point[1]).lineTo(top_point[0], top_point[1]).lineTo(right_point[0], right_point[1]).lineTo(bottom_point[0],bottom_point[1]).close().extrude(cutter_thick)
            #
            # arm_thick_angle_inner_r = arm_thick/innerRadius
            # inner_shape_right = polar(next_diamond_angle - arm_thick_angle_inner_r, innerRadius)
            # inner_shape_left = polar(diamond_angle + arm_thick_angle_inner_r, innerRadius)
            # # inner_shape_top =
            # # inner_shape =
            #
            # arm_thick_angle_outer_r = arm_thick/outerRadius
            #
            # upper_shape_right = polar(next_diamond_angle - arm_thick_angle_outer_r, outerRadius)
            # upper_shape_left = polar(diamond_angle + arm_thick_angle_outer_r, outerRadius)
            # upper_shape_bottom = polar((diamond_angle + next_diamond_angle)/2, centre_r)
            #
            # upper_shape = cq.Workplane("XY").moveTo(upper_shape_left[0], upper_shape_left[1]).radiusArc(upper_shape_right, -outerRadius).lineTo(upper_shape_bottom[0], upper_shape_bottom[1]).close().extrude(cutter_thick)
            # cutter = cutter.add(upper_shape)
            # cutter = cutter.add(diamond)
            # return cutter


        return gear.cut(cutter)

    @staticmethod
    def cutCurvesStyle(gear, outerRadius, innerRadius, clockwise=True):

        gap_size = outerRadius - innerRadius

        arm_thick = outerRadius*0.15
        #thin arms can result in the wheel warping to be non-circular. I don't fancy taking my chances!
        if arm_thick < 3:
            arm_thick = 3
        cutter_thick = 100

        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutter_thick)
        # cutter = cq.Workplane("XY")
        arms = 6

        for arm in range(arms):
            outer_r = (gap_size + arm_thick*2)/2
            if outer_r < arm_thick:#*1.5:
                print("curved style: not enough space. outer_r: {}, arm_thick:{}".format(outer_r, arm_thick))
                #not enough space to cut this gear
                return gear
            clockwise_modifier = -1 if clockwise else 1

            angle = arm * math.pi*2 / arms

            arm = cq.Workplane("XY").circle(outer_r).circle(outer_r - arm_thick).extrude(cutter_thick)
            # return arm
            square = cq.Workplane("XY").rect(outer_r*2, outer_r*2).extrude(cutter_thick).translate((clockwise_modifier* outer_r,0))
            # return square
            arm = arm.cut(square)
            # return arm
            arm = arm.translate((0,innerRadius + gap_size/2 )).rotate((0,0,0), (0,0,1), radToDeg(angle))
            # return arm
            cutter = cutter.cut(arm)
            # cutter = cutter.add(arm)

        # return cutter

        gear = gear.cut(cutter)

        return gear


    @staticmethod
    def cutSnowflakeStyle(gear, outerRadius, innerRadius):
        '''
        Just random branching arms until I can think of something better
        '''
        middleOfGapR = (outerRadius + innerRadius)/2
        gapSize = outerRadius - innerRadius

        armThick = 4

        branchThick = 2.4

        branchDepth=2

        if gapSize < 20:
            branchThick = 1.65
            armThick=2.4

        if gapSize < 40:
            branchDepth = 1

        cutterThick = 1000
        snowflake=cq.Workplane("XY")

        branchesPerArm = random.randrange(3,6)
        possibleBranchYs = [(branch+0.5) * gapSize/branchesPerArm + innerRadius + random.randrange(-1,1)*gapSize/(branchesPerArm*2) for branch in range(branchesPerArm)]

        branchYs = [possibleBranchYs[0]]

        lastY = possibleBranchYs[0]
        for y in possibleBranchYs[1:]:
            if y - lastY > branchThick*2:
                branchYs.append(y)
                lastY = y

        midBranch0 = polar(0,middleOfGapR)
        midBranch1 = polar(math.pi/3,middleOfGapR)



        branchlength = distance_between_two_points(midBranch0, midBranch1) / 2

        branchLengths = [branchlength for branch in branchYs]
        branchAngle = math.pi/3
        branchesPerArm = len(branchLengths)

        branchLengthMultiplier =  0.2 + random.random()*0.3

        def addBranches(shape, branchStart, branchLength, armAngle, branchThick, depth=0):
            '''
            from a point on an arm or branch, add a pair of branches
            '''
            shape = shape.workplaneFromTagged("base").moveTo(branchStart[0], branchStart[1]).circle(branchThick/2).extrude(cutterThick)
            for i in [-1, 1]:
                thisBranchAbsAngle=armAngle + i * branchAngle
                branchEnd = np.add(branchStart, polar(thisBranchAbsAngle, branchLength))
                branchCentre = average_of_two_points(branchStart, branchEnd)
                branchShape = cq.Workplane("XY").rect(branchLength, branchThick).extrude(cutterThick).rotate((0, 0, 0), (0, 0, 1), radToDeg(thisBranchAbsAngle)).translate(branchCentre)
                shape = shape.add(branchShape)
                if depth < branchDepth-1:
                    #find angle from centre
                    endAngle = math.atan2(branchEnd[1], branchEnd[0])
                    if abs(endAngle - armAngle) < branchAngle/2:
                        nextBranchStart = branchCentre
                        #only if the end of this branch isn't giong to be chopped off by the pizza slice
                        shape = addBranches(shape, nextBranchStart, branchLength*branchLengthMultiplier, armAngle + i * branchAngle, branchThick, depth+1)

            return shape

        for arm in range(6):
            #arm from centre to edge, building from centre to top and rotating into place afterwards
            armShape = cq.Workplane("XY").tag("base").moveTo(0, middleOfGapR).rect(armThick,gapSize*2).extrude(cutterThick)

            for branch in range(branchesPerArm):
                branchStart = (0, branchYs[branch])
                armAngle = math.pi/2

                armShape = addBranches(armShape, branchStart, branchLengths[branch], armAngle, branchThick)
                # #armShape = armShape.workplaneFromTagged("base").moveTo().circle(armThick*2).extrude(cutterThick)
                # # return armShape
                # branchEnd = np.add(branchStart, polar(math.pi/2 - branchAngle, branchLengths[branch]))
                # branchCentre = averageOfTwoPoints(branchStart, branchEnd)
                #
                # branchShape = cq.Workplane("XY").rect(branchThick, branchLengths[branch]).extrude(cutterThick).rotate((0,0,0), (0,0,1),-radToDeg(branchAngle)).translate(branchCentre)
                # branchShape = branchShape.add(cq.Workplane("XY").rect(branchThick, branchLengths[branch]).extrude(cutterThick).rotate((0, 0, 0), (0, 0, 1), radToDeg(branchAngle)).translate((-branchCentre[0], branchCentre[1])))
                # armShape = armShape.add(branchShape)

                left = polar(math.pi/2 + branchAngle/2, outerRadius*2)
                pizzaSlice = cq.Workplane("XY").lineTo(left[0], left[1]).lineTo(-left[0], left[1]).close().extrude(cutterThick)
                # return pizzaSlice
                armShape = armShape.intersect(pizzaSlice)

                # if branchDepth > 1:
                #     #TODO make this recursive? Or am I never going to go above 2?



            snowflake = snowflake.add(armShape.rotate((0,0,0), (0,0,1),arm * 360/6))


        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutterThick)

        cutter = cutter.cut(snowflake)

        return gear.cut(cutter)

    @staticmethod
    def cutHoneycombStyle(gear, outerRadius, innerRadius, big=True, chunky=False):
        hexagonDiameter = 10
        if big:
            hexagonDiameter = outerRadius / 3
            if hexagonDiameter < innerRadius*2 and innerRadius*2 < outerRadius*0.75:
                # keep hexagon larger than the inner radius (looks better), unless that would result in a hexagon too big
                hexagonDiameter = innerRadius*2
            if hexagonDiameter > 25:
                #too big looks like it's just spokes
                hexagonDiameter = 25

        if hexagonDiameter < 10:
            hexagonDiameter = 10

        # if hexagonDiameter < 6:
        #     hexagonDiameter = 6


        # padding = outerRadius*0.075
        padding = outerRadius * 0.1
        if padding < 1.5:
            padding=1.5
        #1.9 nearly seems to result in no gaps and no fiddly bits with classic slicer and 0.4 nozzle
        #1.8 seems better
        padding=1.8#2

        if big or chunky:
            #experimental, not printed yet
            padding=2.7

        #experimenting to reduce the tiny bits teh slicer likes to make
        # padding = padding - (padding % EXTRUSION_WIDTH) - 0.2

        hexagonDiameter+=padding

        hexagonSideLength = hexagonDiameter * math.sin(math.pi / 6)
        hexagonHeight = hexagonDiameter*0.5*math.sin(math.pi*2/6)*2

        cutterThick = 100

        honeycomb = cq.Workplane("XY")#.circle(outerRadius).extrude(cutterThick)

        count = math.ceil(outerRadius/hexagonDiameter) + 2

        for i in range(-count, count):
            for j in range(-count*2, count*2):
                offset = 0
                if j % 2 != 0:
                    offset = 0.5
                x = (i-offset)*(hexagonDiameter + hexagonSideLength)
                y = j*(hexagonHeight)/2

                #undecided if it looks better or worse with the slivers of hexagons on the edges
                centreDistance = math.sqrt(x*x + y*y)
                if centreDistance > outerRadius + padding*1.2:
                    #we're more than half outside

                    #skip if it's a small sliver that would be left behind
                    if hexagonDiameter - (centreDistance - outerRadius) < 15:
                        continue
                if x == 0 and y ==0:
                    #always skip the center hexagon
                    continue

                honeycomb = honeycomb.add(cq.Workplane("XY").polygon(nSides=6,diameter=hexagonDiameter-padding).extrude(cutterThick).translate((x, y)))
        try:
            honeycomb = honeycomb.cut(cq.Workplane("XY").circle(innerRadius).extrude(cutterThick))
        except:
            '''
            *shrug*
            '''
            print("failed to cut honeycomb")

        outerRing = cq.Workplane("XY").circle(outerRadius*2).circle(outerRadius).extrude(cutterThick)

        honeycomb = honeycomb.cut(outerRing)

        return gear.cut(honeycomb)

    @staticmethod
    def cutFlowerStyle2(gear, outerRadius, innerRadius):
        '''
        same idea as cutFlowerStyle but with the arm width consistent
        '''
        petals = 5

        armToHoleRatio = 0.5

        innerCircumference = math.pi * 2 * innerRadius

        # width at inner radius
        pairWidth = innerCircumference / petals
        armWidth = armToHoleRatio * pairWidth
        petalWidth = pairWidth * (1 - armToHoleRatio)
        petal_inner_radius = (outerRadius - innerRadius) * 0.75
        if petal_inner_radius < 6:
            print("petal inner radius: ", petal_inner_radius)
            petal_inner_radius = 6

        min_arm_width=1.8

        if petal_inner_radius < 0:
            return gear
        #if this is a wheel with a relatively large inner radius (like a cord wheel), increase the number of petals
        while petal_inner_radius < petalWidth*1.5 and armWidth > min_arm_width:
            petals+=1
            pairWidth = innerCircumference / petals
            armWidth = armToHoleRatio * pairWidth
            petalWidth = pairWidth * (1 - armToHoleRatio)
            armToHoleRatio*=0.975#0.975
            # petal_inner_radius*=1.01

        if armWidth < min_arm_width:
            armWidth = min_arm_width
            petals-=1

        cutter_thick = 1000

        #calculate centre of the circle based on sagitta (again)
        angle_per_flower = math.pi*2/petals
        angle_over_arm = armWidth/innerRadius
        angle_for_sagitta = angle_per_flower*2 - angle_over_arm
        angle_for_sagitta_deg = radToDeg(angle_for_sagitta)
        l_old = np.linalg.norm(np.subtract(polar(0, innerRadius), polar(angle_for_sagitta, innerRadius)))
        l = 2*innerRadius*math.sin(angle_for_sagitta/2)
        r = petal_inner_radius
        try:
            sagitta = r - math.sqrt(r**2 - (l/2)**2)
        except:
            print("unable to cut flower gear. innerR:{} outerR:{}, petals:{}".format(innerRadius, outerRadius, petals))
            # return Gear.cutFlowerStyle(gear, innerRadius, outerRadius)
            # return Gear.cutSimpleStyle(gear, innerRadius, outerRadius,15)
            return Gear.cutSemicirclesStyle(gear, outerRadius, innerRadius)
        circle_centre_distance = r - sagitta + innerRadius*math.cos(angle_for_sagitta/2)
        # circle_centre_distance = math.sqrt(innerRadius**2 - (l/2)**2) + math.sin(petal_inner_radius**2 - (l/2)**2)

        def get_circle(petal, hollow=True, inner_only=False):
            r = petal_inner_radius + armWidth
            if inner_only:
                hollow=False
                r = petal_inner_radius
            circle_cutter = cq.Workplane("XY").circle(r)
            if hollow:
                circle_cutter = circle_cutter.circle(petal_inner_radius)
            circle_cutter = circle_cutter.extrude(cutter_thick)

            circle_cutter = circle_cutter.translate(polar(petal * math.pi * 2 / petals, circle_centre_distance))
            return circle_cutter

        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutter_thick)
        # debug = cq.Workplane("XY")
        for p in range(petals):
            # circle_cutter = cq.Workplane("XY").circle(petal_inner_radius + armWidth).circle(petal_inner_radius).extrude(cutter_thick)
            # circle_cutter = circle_cutter.translate(polar(p*math.pi*2/petals, circle_centre_distance))
            # debug = debug.add(circle_cutter)

            circle_cutter = get_circle(p)
            #only keep the 'inner' bits of the circles, so that for more than 5ish petals we don't have small circles eating into the outer ring. hard to explain, easy to see
            circle_cutter = circle_cutter.intersect(get_circle(p-1, hollow=False).union(get_circle(p+1, hollow=False)))
            #don't let the arms bulge into the inner petal bit
            circle_cutter = circle_cutter.cut(get_circle(p-2, inner_only=True).union(get_circle(p+2, inner_only=True)))

            cutter = cutter.cut(circle_cutter)
        # return debug
        return gear.cut(cutter)

    @staticmethod
    def cutFlowerStyle(gear, outerRadius, innerRadius):

        petals = 5

        armToHoleRatio = 0.5

        innerCircumference=math.pi*2*innerRadius

        #width at inner radius
        pairWidth = innerCircumference/petals
        armWidth = armToHoleRatio*pairWidth
        petalWidth = pairWidth*(1-armToHoleRatio)
        #
        petalRadius = (outerRadius - innerRadius)*0.75

        if petalRadius < 0:
            return gear
        #if this is a wheel with a relatively large inner radius (like a cord wheel), increase the number of petals
        while petalRadius < petalWidth*1.5:
            petals+=1
            pairWidth = innerCircumference / petals
            armWidth = armToHoleRatio * pairWidth
            petalWidth = pairWidth * (1 - armToHoleRatio)

        armOuterAngle=armWidth/outerRadius

        cutter = cq.Workplane("XY")

        cutterThick = 1000

        outerTipR = innerRadius + (outerRadius - innerRadius)*0.4

        for p in range(petals):

            startAngle = p*math.pi*2/petals
            endAngle = startAngle + (1-armToHoleRatio)*math.pi*2/petals

            tipAngle = (startAngle + endAngle)/2

            startPos = polar(startAngle,innerRadius)
            tipPos = polar(tipAngle, outerRadius)
            endPos = polar(endAngle, innerRadius)
            try:
                #cut out the hole in the middle
                cutter = cutter.add(cq.Workplane("XY").moveTo(startPos[0], startPos[1]).radiusArc(tipPos, -petalRadius).radiusArc(endPos, -petalRadius).radiusArc(startPos,innerRadius).close().extrude(cutterThick))
            except:
                print("unable to produce flower cutter:", innerRadius, outerRadius)

            if petalWidth < 4 and petals > 10:
                #the extra cut out bits will look messy, so don't bother with them
                continue
            outerStartAngle=tipAngle+armOuterAngle
            outerEndAngle = tipAngle + math.pi*2/petals - armOuterAngle
            outerTipAngle = (outerStartAngle + outerEndAngle)/2

            outerStartPos = polar(outerStartAngle, outerRadius)
            outerEndPos = polar(outerEndAngle, outerRadius)
            outerTipPos = polar(outerTipAngle, outerTipR)

            outercutter = cq.Workplane("XY").moveTo(outerStartPos[0], outerStartPos[1]).radiusArc(outerEndPos, -outerRadius - 0.1)
            # outercutter = outercutter.lineTo(outerTipPos[0], outerTipPos[1])
            # outercutter = outercutter.lineTo(outerStartPos[0], outerStartPos[1])
            outercutter = outercutter.radiusArc(outerTipPos, petalRadius + armWidth)
            outercutter = outercutter.radiusArc(outerStartPos, petalRadius + armWidth)
            outercutter = outercutter.close().extrude(cutterThick)

            cutter = cutter.add(outercutter)


        return gear.cut(cutter)

    @staticmethod
    def cutSteamTrainStyle(gear, outerRadius, innerRadius, spokes=20, withWeight=True):
        '''
        Without the weight this could be a cartwheel
        '''
        armThick = outerRadius * 0.05
        # weightR = (outerRadius + innerRadius)*0.8
        weightWide = outerRadius*0.3
        spokesShape = cq.Workplane("XY")
        cutterThick = 100

        for i in range(spokes):
            spoke = cq.Workplane("XY").moveTo(0, outerRadius / 2).rect(armThick, outerRadius).extrude(cutterThick)
            spokesShape = spokesShape.add(spoke.rotate((0, 0, 0), (0, 0, 1), i * 360 / spokes))

        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutterThick)

        if withWeight and outerRadius/innerRadius > 2:
            #infilled bit off to the left (in reality a counterweight to the bit that holds the rod)
            spokesShape = spokesShape.add(cq.Workplane("XY").moveTo(-outerRadius,0).rect(weightWide*2, outerRadius*2).extrude(cutterThick))
            # angle = degToRad(10)
            smallCircleR = innerRadius*0.75
            smallCircleDistance = (innerRadius + outerRadius)*0.3
            # spokesShape = spokesShape.add(cq.Sketch()..circle(innerRadius).located())

            # start = polar(math.pi/2 - angle, innerRadius)
            # middleRelative = polar(math.pi/2 - angle, smallCircleR)
            # #circularish bit that would hold a rod!
            # spokesShape = spokesShape.add(cq.Workplane("XY").mo)
            #I really don't understand CQ sketches it turns out, but from copy-pasting and bodging an example I can hull two circles by magic:
            spokesShape = spokesShape.add(cq.Workplane("XY").sketch()
            .arc((0, 0), innerRadius, 0., 360.)
            .arc((smallCircleDistance, 0), smallCircleR, 0., 360.)
            .hull().finalize().extrude(cutterThick))

        cutter = cutter.cut(spokesShape)

        gear = gear.cut(cutter)

        # gear = gear.faces(">Z").workplane().moveTo(0,0)

        return gear

    @staticmethod
    def cutSpokesStyle(gear, outerRadius, innerRadius, pairs = 11):
        armThick = outerRadius * 0.05

        spokes = cq.Workplane("XY")
        cutterThick = 100

        for i in range(pairs):
            pair = cq.Workplane("XY").moveTo(-innerRadius, outerRadius/2).rect(armThick, outerRadius).mirrorY().extrude(cutterThick)
            spokes = spokes.add(pair.rotate((0,0,0), (0,0,1),i*360/pairs))

        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutterThick)

        cutter = cutter.cut(spokes)

        gear = gear.cut(cutter)

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
    def cutArcsStyle(gear, outer_r, inner_r):
        #more wibbly than the HAC style ARCS
        #unlike HAC style, which uses semicircles, this uses non-semicircles so can cut away more gear
        armThick = max(4, outer_r*0.1)
        armAngle = armThick / outer_r
        # print("outer_r: {} inner_r:{} outer_r/inner_r:{} inner_r/outer_r:{}".format(outer_r, inner_r, outer_r/inner_r, (inner_r-armThick)/outer_r))
        # arms = math.ceil(25 * (inner_r-armThick)/outer_r)
        arms = max(5,math.ceil(10 * (inner_r) / outer_r))


        # sagitta*=1.2
        # if sagitta > outer_r - inner_r:
        #     sagitta = outer_r - inner_r

        # line it up so there's a nice arm a the bottom
        offsetAngle = -math.pi / 2 + armAngle / 2
        cutter = cq.Workplane("XY")

        for i in range(arms):
            startAngle = i * math.pi * 2 / arms + offsetAngle
            endAngle = (i + 1) * math.pi * 2 / arms - armAngle + offsetAngle

            midAngle = (startAngle + endAngle)/2

            startPos = polar(startAngle, outer_r)
            midPos = polar(midAngle, inner_r)
            endPos = polar(endAngle, outer_r)

            startDir = polar(startAngle , 1)
            endDir = polar(endAngle + math.pi, 1)
            midDir = polar(midAngle - math.pi/2, 1)



            # gear = gear.faces(">Z").workplane()
            # gear = gear.moveTo(startPos[0], startPos[1]).radiusArc(endPos, -outer_r).spline([midPos, startPos], tangents=[endDir, midDir, startDir], includeCurrent=True).close().cutThruAll()
            cutter = cutter.add(cq.Workplane("XY").moveTo(startPos[0], startPos[1]).radiusArc(endPos, -outer_r).spline([midPos, startPos], tangents=[endDir, midDir, startDir], includeCurrent=True).close().extrude(100))
            # gear = gear.moveTo(startPos[0], startPos[1]).spline([startPos, endPos], tangents=[npToSet(np.multiply(startPos, -1)), endPos]).radiusArc(startPos, outer_r).close().cutThruAll()
            # .radiusArc(startPos,-innerRadius)\
            # .close().cutThruAll()

        # return cutter
        return gear.cut(cutter)

    @staticmethod
    def cutHACStyle(gear,outer_r, inner_r):
        # vaguely styled after some HAC gears I've got, with nice arcing shapes cut out
        #same as ARCS2
        armThick = max(4, outer_r * 0.125)
        armAngle = armThick / outer_r
        arms = 5



        def get_sagitta(arms):
            # distance between inner arches of cutout
            angle_between_arches = math.pi * 2 / arms - armAngle
            # l = 2 * outer_r * math.sin(angle_between_arches / 2)
            sagitta = outer_r * math.cos(angle_between_arches / 2) - inner_r
            return sagitta

        gap_size = outer_r - inner_r

        sagitta = get_sagitta(arms)
        i=0
        while sagitta < gap_size/2 and arms < 20:
            #on narrow gaps they can end up just a straight lines!
            arms+=1
            sagitta = get_sagitta(arms)


        # sagitta*=1.2
        # if sagitta > outer_r - inner_r:
        #     sagitta = outer_r - inner_r

        #line it up so there's a nice arm a the bottom
        offsetAngle = -math.pi/2 + armAngle/2
        for i in range(arms):
            startAngle = i * math.pi * 2 / arms + offsetAngle
            endAngle = (i + 1) * math.pi * 2 / arms - armAngle + offsetAngle

            startPos = polar(startAngle, outer_r)
            endPos = polar(endAngle, outer_r)

            gear = gear.faces(">Z").workplane()
            gear = gear.moveTo(startPos[0], startPos[1]).radiusArc(endPos, -outer_r).sagittaArc(startPos, -sagitta).close().cutThruAll()
            # gear = gear.moveTo(startPos[0], startPos[1]).spline([startPos, endPos], tangents=[npToSet(np.multiply(startPos, -1)), endPos]).radiusArc(startPos, outer_r).close().cutThruAll()
            # .radiusArc(startPos,-innerRadius)\
            # .close().cutThruAll()
        return gear

    @staticmethod
    def crescent_moon_2D(radius, fraction):
        '''
        moon, from no moon (fraction 0) to full moon (fraction 0.5) back to no moon (fraction 1)
        '''
        if fraction < 0 or fraction > 1:
            raise ValueError("fraction can only go from 0 to 1")

        if fraction == 0 or fraction == 1:
            return None
            return cq.Workplane("XY")

        sagitta = -radius + (fraction*2 % 1)*2*radius
        radius_for_shape = radius if fraction < 0.5 else -radius

        moon = cq.Workplane("XY").moveTo(0, radius).radiusArc((0, -radius), radius_for_shape)

        if sagitta != 0:
            moon = moon.sagittaArc((0,radius),sagitta)

        moon = moon.close()


        return moon

    @staticmethod
    def cut_circles_style(gear, outer_radius, inner_radius = 3, min_gap = 3, hollow=False, moons=False):
        '''inspired (shamelessly stolen) by the clock on teh cover of the horological journal dated March 2022'''
        #TODO split out the hollow into its own method, I think it's going to be a little different, especially around calculating positions

        if inner_radius < 0:
            inner_radius = 3



        # #TEMP
        # gear = gear.faces(">Z").workplane().circle(innerRadius).cutThruAll()
        # return gear

        #sopme slight fudging occurs with minGap as using the diameter (gapSize) as a measure of how much circumference the circle takes up isn't accurate

        ring_size = (outer_radius - inner_radius)
        big_circle_r = ring_size*0.425
        #want to ensure the "arm" thickness between the circles is enough for a rigid gear
        big_circle_space = ring_size*1.15
        # smallCircleR = bigCircleR*0.3

        circle_size_ratio = big_circle_space/((inner_radius + outer_radius)/2)

        if circle_size_ratio < 0.5:
            big_circle_space += min_gap

        cutter_thick = 1000
        cutter = cq.Workplane("XY")

        if hollow:
            cutter = cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(cutter_thick)

        big_circlescircumference = 2 * math.pi * (inner_radius + ring_size / 2)

        cutmoons = moons

        #this is only aproximate, but seems to work
        big_circle_count = math.floor(big_circlescircumference / big_circle_space)

        # big_circle_angle_max = math.pi * 2 / big_circle_count
        # big_circle_angle = get_angle_of_chord(inner_radius + ring_size/2, big_circle_r*2)
        # print("big_circle_angle/big_circle_angle_max",big_circle_angle/big_circle_angle_max, " big_circle_count ", big_circle_count, " circle_size_ratio ",circle_size_ratio)
        # if big_circle_angle/big_circle_angle_max > 0.8:
        #     big_circle_count = math.floor(big_circle_count*0.8)

        if big_circle_count <6:
            cutmoons = False

        if big_circle_count > 0 :
            big_circle_angle = math.pi*2/big_circle_count

            smallCircleRingR = inner_radius + ring_size * 0.75

            bigCirclePos = polar(0, inner_radius + ring_size / 2)
            smallCirclePos = polar(big_circle_angle / 2, smallCircleRingR)
            distance = math.sqrt((bigCirclePos[0] - smallCirclePos[0])**2 + (bigCirclePos[1] - smallCirclePos[1])**2)
            smallCircleR = distance - big_circle_r - min_gap
            #don't want the small circles eating into the edges of the gear
            if smallCircleR + smallCircleRingR > outer_radius:
                smallCircleR = outer_radius - smallCircleRingR

            hasSmallCircles = smallCircleR > 2

            for circle in range(big_circle_count):
                angle = big_circle_angle*circle - big_circle_angle/4
                pos = polar(angle, inner_radius + ring_size / 2)

                if hollow:
                    cutter = cutter.cut(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(big_circle_r+2).circle(big_circle_r).extrude(cutter_thick))
                elif cutmoons:
                    moon = Gear.crescent_moon_2D(big_circle_r,((circle)/big_circle_count))
                    if moon is not None:
                        cutter = cutter.add(moon.extrude(cutter_thick).rotate((0,0,0),(0,0,1),radToDeg(angle-math.pi/2)).translate(pos))
                else:
                    cutter = cutter.add(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(big_circle_r).extrude(cutter_thick))

                if hasSmallCircles:
                    smallCirclePos = polar(angle + big_circle_angle / 2, inner_radius + ring_size * 0.75)
                    cutter = cutter.add(cq.Workplane("XY").moveTo(smallCirclePos[0], smallCirclePos[1]).circle(smallCircleR).extrude(cutter_thick))


        gear = gear.cut(cutter)

        return gear

    @staticmethod
    def cutSemicirclesStyle(gear, outerRadius, innerRadius):
        '''
        used when the gap is too narrow for flowers to work - cut a series of circles that are larger than the gap
        '''

        circle_r = (outerRadius - innerRadius)#*0.6
        arm_wide=3

        r = (innerRadius + outerRadius)/2

        # circle_r = outerRadius - innerRadius

        circles = floor(math.pi*2*innerRadius / (circle_r*2 + arm_wide))

        cutter_thick = 1000
        cutter = cq.Workplane("XY")

        for c in range(circles):
            angle = c*math.pi*2/circles

            cutter = cutter.add(cq.Workplane("XY").circle(circle_r).extrude(cutter_thick).translate(polar(angle,innerRadius)))

        cutter = cutter.intersect(cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutter_thick))

        return gear.cut(cutter)



    def __init__(self, isWheel, teeth, module, addendum_factor, addendum_radius_factor, dedendum_factor, toothFactor=math.pi/2, is_crown=False, lantern=False):
        self.iswheel = isWheel
        self.teeth = teeth
        self.module=module
        self.addendum_factor=addendum_factor
        # # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl
        # self.addendum_radius_factor=addendum_factor * 1.4
        self.addendum_radius_factor=addendum_radius_factor
        self.dedendum_factor=dedendum_factor

        self.toothFactor = toothFactor

        self.tooth_angle = self.toothFactor / (self.teeth / 2)
        self.gap_angle = (math.pi - self.toothFactor) / (self.teeth / 2)

        self.pitch_diameter = self.module * self.teeth

        self.outer_r = self.pitch_diameter/2 + self.addendum_factor*self.module

        dedendum_height = self.dedendum_factor * self.module
        self.inner_r = self.pitch_diameter / 2 - dedendum_height


        self.lantern = lantern
        if self.lantern:
            tooth_angle = self.tooth_angle
            self.trundle_r = math.sin(tooth_angle/2)* self.pitch_diameter/2
            print("need trundles of diameter {}mm".format(self.trundle_r*2))
            self.outer_r = self.outer_r + self.trundle_r*3
            self.inner_r_for_lantern_fixing_slot = self.inner_r + 0.175
            self.slot_sides = 6
            # https://en.wikipedia.org/wiki/Sagitta_(geometry)
            # assuming hexagon, find how far the flat edge is from the containing diameter
            r = self.inner_r
            l = r
            sagitta = r - math.sqrt(r ** 2 - (l ** 2) / 4)
            self.cutoff_height = sagitta

        '''
        is this a crown gear (may be called a face gear) - a special case of bevel gear that can mesh with a normal spur gear at 90deg
        experimental, no idea if this will work with cycloidal gears or with my rudementary understanding of gear design.
        my idea is that this will be easier to work with then bevel gears as they wouldn't need to be perfectly lined up - one could be slightly offset from the other without issue
        
        further thought - even if I can design this - will it be printable? bevel gears look printable so it's probably worth experimenting with them first
        '''
        self.is_crown = is_crown

        #purely for the fancy styling, is there anyhting in the centre (like a pinion or ratchet) to avoid?
        # self.innerRadiusForStyle=innerRadiusForStyle

        # # via practical addendum factor
        # self.addendum_height = 0.95 * addendum_factor * module

    def get_max_radius(self):
        '''
        radius that encompasses the outermost parts of the teeth
        '''
        return self.outer_r
        # return self.pitch_diameter/2 + self.addendum_factor*self.module

    def get_min_radius(self):
        '''
        you could cut a hole through the gear of this radius without touchign the teeth
        '''
        return self.inner_r
        # dedendum_height = self.dedendum_factor * self.module
        # return self.pitch_diameter/2 - dedendum_height

    def get3D(self, holeD=0, thick=0, style=GearStyle.ARCS, innerRadiusForStyle=-1, clockwise_from_pinion_side=True):
        gear = self.get2D()

        if thick == 0:
            thick = round(self.pitch_diameter*0.05)
        gear = gear.extrude(thick)

        if holeD > 0:
            gear = gear.faces(">Z").workplane().moveTo(0,0).circle(holeD/2).cutThruAll()

        if self.iswheel:
            # rimThick = max(self.pitch_diameter * 0.035, 3)
            # rimRadius = self.pitch_diameter / 2 - self.dedendum_factor * self.module - rimThick

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
            gear = Gear.cutStyle(gear, outerRadius=self.pitch_diameter / 2 - self.dedendum_factor * self.module, innerRadius=innerRadiusForStyle, style=style, clockwise_from_pinion_side=clockwise_from_pinion_side)

        return gear

    def get_STL_modifier_shape(self, thick, offset_z=0, min_inner_r=1.5):
        '''
        return a shape that covers just the teeth to help apply tweaks to the slicing settings
        '''

        # inner_r = self.getMinRadius() - 1.8
        # if inner_r < min_inner_r:
        #     inner_r = min_inner_r

        #two 0.45 traces extra
        inner_r = self.get_min_radius() - 0.9

        return cq.Workplane("XY").circle(self.get_max_radius()).circle(inner_r).extrude(thick).translate((0, 0, offset_z))

    def get_lantern_cutter(self, offset = 1, trundle_length=100):
        '''
        get a cutter that will provide slots for the lantern trundles to rest in

        just provides a series of rods offset in z by height provided

        TODO plan is to have a separate vertical hexagonal peice printed sideways (like the key) for strength

        '''



        cutter = cq.Workplane("XY").polygon(self.slot_sides, self.inner_r_for_lantern_fixing_slot * 2).extrude(trundle_length)

        angle_change = math.pi*2 / self.teeth

        for angle in [angle_change*i for i in range(self.teeth)]:
            #0.1 extra is enough to squeeze in, but I broke the wheel first time trying to assemble.
            cutter = cutter.add(cq.Workplane("XY").circle(self.trundle_r+0.2).extrude(trundle_length).translate(polar(angle, self.pitch_diameter/2)).translate((0,0,offset)))

        return cutter


    def get_lantern_inner_fixing(self, base_thick=5, pinion_height=10, top_thick=5, for_printing=True, hole_d=3):
        holder_together = cq.Workplane("XY").polygon(self.slot_sides, self.inner_r*2).circle(hole_d/2).extrude(base_thick)

        holder_together = holder_together.faces(">Z").workplane().circle(self.inner_r).circle(hole_d/2).extrude(pinion_height)

        holder_together = holder_together.faces(">Z").workplane().polygon(self.slot_sides, self.inner_r*2).circle(hole_d/2).extrude(top_thick)
        # line up with the base of the hexagon
        holder_together = holder_together.rotate((0, 0, 0), (0, 0, 1), 360 / 12)
        holder_together = holder_together.rotate((0, 0, 0), (0, 1, 0), 90).translate((0, 0, self.inner_r - self.cutoff_height))

        # chop off the bottom so this is printable horizontally
        holder_together = holder_together.cut(cq.Workplane("XY").rect(1000, 1000).extrude(100).translate((0, 0, -100)))

        if not for_printing:
            holder_together = (holder_together.rotate((0, 0, 0), (0, 1, 0), -90)
                               .translate((self.inner_r - self.cutoff_height, 0, 0)).rotate((0, 0, 0), (0, 0, 1), 360 / 12))

        return holder_together

    def get_lantern_cap(self, offset = 1, cap_thick=5):
        cap = cq.Workplane("XY").circle(self.outer_r).polygon(self.slot_sides, self.inner_r_for_lantern_fixing_slot * 2).extrude(cap_thick)

        cap = cap.cut(self.get_lantern_cutter(0, cap_thick-offset))



        return cap

    def add_to_wheel(self, wheel, hole_d=0, thick=4, style=GearStyle.ARCS, pinion_thick=8, cap_thick=2, clockwise_from_pinion_side=True, pinion_extension=0):
        '''
        Intended to add a pinion (self) to a wheel (provided)
        if front is true ,added onto the top (+ve Z) of the wheel, else to -ve Z. Only really affects the escape wheel
        pinionthicker is a multiplier to thickness of the week for thickness of the pinion
        clockwise_from_pinion_side is purely for cutting a style
        '''
        base = wheel.get3D(thick=thick, holeD=hole_d, style=style, innerRadiusForStyle=self.get_max_radius() + 1, clockwise_from_pinion_side=clockwise_from_pinion_side)

        if self.lantern:
            base = base.cut(self.get_lantern_cutter())
            # base = base.union(cq.Workplane("XY").circle(self.inner_r).circle(hole_d/2).extrude(thick + pinion_thick).faces(">Z").workplane().polygon(self.slot_sides, self.inner_r*2).circle(hole_d/2).extrude(cap_thick))
            return base

        # pinionThick = thick * pinionthicker



        if pinion_extension > 0:
            base = base.union(cq.Workplane("XY").circle(self.get_max_radius()).extrude(pinion_extension).translate((0, 0, thick)))

        top = self.get3D(thick=pinion_thick, holeD=hole_d, style=style).translate((0, 0, thick + pinion_extension))

        arbour = base.union(top)

        if cap_thick > 0:
            arbour = arbour.union(cq.Workplane("XY").circle(self.get_max_radius()).extrude(cap_thick).translate((0, 0, thick + pinion_thick + pinion_extension)))

        # arbour = arbour.faces(topFace).workplane().moveTo(0,0).circle(holeD / 2).cutThruAll()
        arbour = arbour.cut(cq.Workplane("XY").moveTo(0,0).circle(hole_d / 2).extrude(1000).translate((0, 0, -500)))

        return arbour

    def get2D(self):
        '''
        Return a 2D cadquery profile of a single gear

        note - might need somethign different for pinions?
        '''

        # return cq.Workplane("XY").circle(self.pitch_diameter/2)

        if self.lantern:
            raise ValueError("This is a lantern pinion, the 2D shape will not work for this")

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

        tooth_angle = self.tooth_angle
        gap_angle = self.gap_angle

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

    #MODULE_FOR_LANTERN_PINION_DIAMETER[lantern_pinion_trundle_d] = module_size
    #assumes ten leaves
    MODULE_FOR_LANTERN_PINION_DIAMETER={
        1.5: 1.4312,
        # 1.6:
    }

    @staticmethod
    def module_size_for_lantern_pinion_trundle_diameter(desired_trundle_d, leaves=10):
        tooth_factor = 1.25
        if leaves == 10:
            tooth_factor = 1.05

        module = desired_trundle_d / (math.sin(tooth_factor/leaves) * leaves)

        return module

        # trundle_r = math.sin((self.toothFactor / (self.teeth / 2)) / 2) * (self.module * self.teeth) / 2


    errorLimit=0.000001
    def __init__(self, wheelTeeth, pinionTeeth, module=1.5, looseArbours=False, lantern=False):
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

        if pinionTeeth > 20 and self.gear_ratio < 3:
            # print("Reducing wheel addendum factor wheel teeth: {}, pinion teeth: {}".format(wheelTeeth, pinionTeeth))
            #bodge - got a clock with a really large pinion on the escape wheel and it keeps binding with the previous wheel
            #TODO investigate this further - it might affect the motion works jamming I had on clock 19 and would be good to understand properly
            wheel_addendum_factor *= 0.7

        # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl says addendum radius factor is 1.4*addendum factor
        #(this is aproximating the real curve, i think?)
        wheel_addendum_radius_factor=wheel_addendum_factor*1.4
        #TODO consider custom slop, this is from http://hessmer.org/gears/CycloidalGearBuilder.html
        wheel_dedendum_factor = math.pi/2
        self.wheel = Gear(True, wheelTeeth, module, wheel_addendum_factor, wheel_addendum_radius_factor, wheel_dedendum_factor)
        # print("wheel teeth: {}, pinion teeth: {}, wheel_addendum_factor: {}, wheel_addendum_radius_factor: {}, wheel_dedendum_factor:{}".format(wheelTeeth, pinionTeeth,
        #                                                                                                                                         wheel_addendum_factor,
        #                                                                                                                                         wheel_addendum_radius_factor,
        #                                                                                                                                         wheel_dedendum_factor))
        #based on the practical wheel addendum factor
        pinion_dedendum_factor = wheel_addendum_factor*0.95 + 0.4

        if module < 0.9:
            # another bodge
            pinion_dedendum_factor*=1.1

        pinion_tooth_factor = 1.25
        if pinionTeeth <= 10:
            pinion_tooth_factor = 1.05
        #https://www.csparks.com/watchmaking/CycloidalGears/index.jxl
        if pinionTeeth == 6 or pinionTeeth == 7 or looseArbours:
            # High ogival
            pinion_addendum_factor=0.855
            pinion_addendum_radius_factor = 1.05
        elif pinionTeeth == 8 or pinionTeeth == 9:
            # Medium ogival
            pinion_addendum_factor = 0.67
            pinion_addendum_radius_factor = 0.7
        elif pinionTeeth == 10:
            #round top
            #this was missing until clock 30, not sure what difference, if any, it will make?
            pinion_addendum_factor=0.525
            pinion_addendum_radius_factor=0.525
        else:
            # round top (11+ leaves)
            pinion_addendum_factor = 0.625
            pinion_addendum_radius_factor = 0.625

        # print("pinion_addendum_factor: {}, pinion_addendum_radius_factor: {}, pinion_dedendum_factor:{}".format(pinion_addendum_factor, pinion_addendum_radius_factor, pinion_dedendum_factor))
        self.pinion=Gear(False, pinionTeeth, module, pinion_addendum_factor, pinion_addendum_radius_factor, pinion_dedendum_factor, toothFactor=pinion_tooth_factor, lantern=lantern)


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
        # print("addendum Factor", addendumFactor)
        return addendumFactor

    def get_model(self, thick=2, offset_angle_deg=0):
        pinion = self.pinion.get3D(3,thick=thick)
        wheel = self.wheel.get3D(3, thick=thick).rotate((0,0,0), (0,0,1), offset_angle_deg)
        model = wheel.add(pinion.translate((self.centre_distance,0,0)))
        return model


class WheelPinionBeveledPair:
    '''
    90degree beveled set of involute gears. Uses cq_gears with some bodges to make them easier to print

    wheel driving pinion to keep consistent even though main usecase is probably the moon dial where it's a pinion driving a wheel
    '''
    def __init__(self, wheel_teeth, pinion_teeth, module=1):
        self.wheel_teeth = wheel_teeth
        self.pinion_teeth = pinion_teeth
        self.module = module

        self.face_width = module*8

        #I've manually overridden trim_bottom in my fork TODO work out how to use the build_params
        self.bevel_gear_pair = BevelGearPair(module=module, gear_teeth=wheel_teeth, pinion_teeth=pinion_teeth, face_width=self.face_width, build_params={"trim_bottom":False})

        #chop off the top bits that cq_gears generates - they'll just produce stringy mess when printing
        self.wheel =  cq.Workplane("XY").add(self.bevel_gear_pair.gear.build()).intersect(cq.Workplane("XY").rect(100, 100).extrude(self.face_width * math.sin(self.bevel_gear_pair.pinion_cone_angle)))
        self.pinion = cq.Workplane("XY").add(self.bevel_gear_pair.pinion.build()).intersect(cq.Workplane("XY").rect(100, 100).extrude(self.face_width * math.sin(self.bevel_gear_pair.gear_cone_angle)))

        #chop off edge bits - I've disabled trim_bottom but I won't want them to stick out sideways. This limits them to a cylinder - bit ugly but should print cleanly without overhang
        #note - I'm uncertain about this - will this cause the gears to bind? am I better off with the overhang?
        # self.wheel = self.wheel.intersect(cq.Workplane("XY").circle(self.bevel_gear_pair.pinion.cone_h).extrude(self.bevel_gear_pair.pinion.cone_h))
        # self.pinion = self.pinion.intersect(cq.Workplane("XY").circle(self.bevel_gear_pair.gear.cone_h).extrude(self.bevel_gear_pair.gear.cone_h))

        #this is doable but I'm too fuzzy - I'll just leave it with overhang
        # self.wheel = self.wheel.cut(cq.Workplane("XY").rect(self.bevel_gear_pair.gear.gs_r*2,self.bevel_gear_pair.gear.gs_r*2).extrude(self.bevel_gear_pair.gear.gs_r*(1-math.cos(self.bevel_gear_pair.gear_cone_angle/2))))
        # self.pinion = self.pinion.cut(cq.Workplane("XY").rect(self.bevel_gear_pair.pinion.gs_r * 2, self.bevel_gear_pair.pinion.gs_r * 2).extrude(self.bevel_gear_pair.pinion.gs_r * (1 - math.cos(self.bevel_gear_pair.pinion_cone_angle / 2))))

    def get_centre_of_wheel_to_back_of_pinion(self):
        return self.bevel_gear_pair.pinion.cone_h

    def get_centre_of_pinion_to_back_of_wheel(self):
        return self.bevel_gear_pair.gear.cone_h

    def get_pinion_max_radius(self):
        #TODO properly - from great circle and cone height?
        return (self.module * self.pinion_teeth)/2 + self.module

    def get_wheel_max_radius(self):
        return (self.module * self.wheel_teeth)/2 + self.module


    def get_assembled(self):
        pinion_in_situ = self.pinion.rotate((0,0,0),(1,0,0),90).translate((0,self.get_centre_of_wheel_to_back_of_pinion(),self.get_centre_of_pinion_to_back_of_wheel()))
        assembly = self.wheel.add(pinion_in_situ)

        return assembly

class FrictionFitPendulumBits:
    '''
    Pendulum holder that attaches to a threaded rod by friction, can be manually adjusted to set in beat
    Do not use for new designs - was a pain to set the beat and easy to knock out of beat
    '''

    def __init__(self, arbor_d=3):
        self.pendulumTopThick = 15
        self.arbor_d = arbor_d

    def get_pendulum_holder(self, holeD=3, for_printing=True):
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
        holeStartY=-get_nut_containing_diameter(self.arbor_d)*0.5-0.4#-5#-8#-height*0.2
        holeHeight = get_nut_height(self.arbor_d, nyloc=True) + get_nut_height(self.arbor_d) + 1

        nutD = get_nut_containing_diameter(holeD)

        wall_thick = (width - (nutD + 1))/2

        pendulum = pendulum.moveTo(-width/2,0).radiusArc((width/2,0), width/2).line(0,-height).radiusArc((-width/2,-height), width/2).close().extrude(self.pendulumTopThick)

        pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()

        #nut to hold to anchor rod
        nutThick = get_nut_height(holeD, nyloc=True)
        nutSpace = cq.Workplane("XY").polygon(6,nutD).extrude(nutThick).translate((0,0,self.pendulumTopThick-nutThick))
        pendulum = pendulum.cut(nutSpace)


        # pendulum = pendulum.faces(">Z").moveTo(0,-height*3/4).rect(width-wall_thick*2,height/2).cutThruAll()
        space = cq.Workplane("XY").moveTo(0,holeStartY-holeHeight/2).rect(width-wall_thick*2,holeHeight).extrude(self.pendulumTopThick).translate((0,0,LAYER_THICK*3))
        pendulum = pendulum.cut(space)

        extraSpaceForRod = 0.1
        extraSpaceForNut = 0.2
        #
        rod = cq.Workplane("XZ").tag("base").moveTo(0, self.pendulumTopThick / 2 - extraRodSpace).circle(self.arbor_d/2 + extraSpaceForRod/2).extrude(100)
        # add slot for rod to come in and out
        rod = rod.workplaneFromTagged("base").moveTo(0,self.pendulumTopThick - extraRodSpace).rect(self.arbor_d + extraSpaceForRod, self.pendulumTopThick).extrude(100)

        rod = rod.translate((0,holeStartY,0))




        pendulum = pendulum.cut(rod)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(6, nutD+extraSpaceForNut).extrude(nutThick).translate((0,holeStartY-holeHeight,0))
        pendulum = pendulum.cut(nutSpace2)


        if not for_printing:
            pendulum = pendulum.mirror().translate((0, 0, self.pendulumTopThick))

        return pendulum

class SuspensionSpringPendulumBits:
    '''
    Crutch and pendulum holder for a suspension spring, contained here to avoid making ArborForPlate far too large
    '''

    def __init__(self, crutch_length=40, square_side_length=6, crutch_thick=7.5, collet_screws=None, crutch_screw=None, printed_suspension=True):

        self.collet_screws = collet_screws

        #experiment: try a 3D printed suspension spring
        self.printed_suspension = printed_suspension

        if self.collet_screws is None:
            self.collet_screws = MachineScrew(2, countersunk=True)

        self.crutch_screw =crutch_screw
        if self.crutch_screw is None:
            self.crutch_screw = MachineScrew(3, countersunk=True)

        self.crutch_length = crutch_length
        #size of the square that will slot onto the anchor arbor
        self.square_side_length = square_side_length
        self.crutch_thick=crutch_thick

        self.radius = self.square_side_length*0.5/math.sqrt(2) + 4
        self.crutch_wide = 10

    def get_crutch(self):
        crutch = cq.Workplane("XY").circle(self.radius).extrude(self.crutch_thick)
        # means to hold screw that will hold this in place
        crutch = crutch.cut(self.collet_screws.get_cutter(length=self.radius, head_space_length=5).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, self.radius, self.crutch_thick / 2)))
        #rotating so bridging shouldn't be needed to print
        crutch = crutch.cut(self.collet_screws.get_nut_cutter(half=True).rotate((0, 0, 0), (0, 0, 1), 360 / 12).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, self.square_side_length / 2, self.crutch_thick / 2)))

        #arm down to the screw that will link with the pendulum
        crutch = crutch.union(cq.Workplane("XY").moveTo(0, -self.crutch_length/2).rect(self.crutch_wide, self.crutch_length).extrude(self.crutch_thick))
        crutch = crutch.union(cq.Workplane("XY").moveTo(0, -self.crutch_length).circle(self.crutch_wide/2).extrude(self.crutch_thick))

        #screw to link with pendulum
        crutch = crutch.cut(self.crutch_screw.get_cutter(with_bridging=True).translate((0, -self.crutch_length)))

        crutch = crutch.faces(">Z").workplane().rect(self.square_side_length, self.square_side_length).cutThruAll()

        return crutch
    def get_pendulum_holder(self):
        holder = cq.Workplane("XY")


        return holder

class ArborForPlate:

    def __init__(self, arbour, plates, arbour_extension_max_radius, pendulum_sticks_out=0, pendulum_at_front=True, bearing=None, escapement_on_front=False,
                back_from_wall=0, endshake = 1, pendulum_fixing = PendulumFixing.DIRECT_ARBOUR, bearing_position=None, direct_arbor_d = DIRECT_ARBOUR_D, crutch_space=10,
                 previous_bearing_position=None, front_anchor_from_plate=-1):
        '''
        Given a basic Arbour and a specific plate class do the following:

        Add arbour extensions where needed
        Produce tweaks to escape wheel and anchor for escapements on front
        Produce the finished arbor for the anchor (with whichever form of pendulum fixing is being used)


        distance_from_back: how far from the back plate is the bottom of this arbour (the rearSideExtension as was in the old Arbour)
        arbour_extension_max_radius: how much space around the arbour (not the bit with a wheel or pinion) there is, to calculate how thick the arbour extension could be

        Note - there is only one plate type at the moment, but the aim is that this should be applicable to others in the future
        as such, I'm trying not to tie it to the internals of SimpleClockPlates (this may be a fool's errand)
        '''
        self.arbor = arbour
        self.plates = plates

        self.arbor_d = self.arbor.arbor_d

        self.plate_distance = self.plates.get_plate_distance()
        self.front_plate_thick = self.plates.get_plate_thick(back=False)
        self.back_plate_thick = self.plates.get_plate_thick(back=True)
        self.standoff_plate_thick = self.plates.get_plate_thick(standoff=True)

        self.arbour_extension_max_radius = arbour_extension_max_radius
        self.pendulum_sticks_out = pendulum_sticks_out
        self.pendulum_at_front = pendulum_at_front
        self.back_plate_from_wall = back_from_wall
        self.endshake = endshake
        self.bearing = bearing
        if self.bearing is None:
            self.bearing = get_bearing_info(self.arbor_d)
        #(x,y,z) from the clock plate. z is the base of the arbour, ignoring arbour extensions (this is from the days when the bearings were raised on little pillars, but is still useful for
        #calculating where the arbour should be)
        self.bearing_position = bearing_position
        #only used for the anchor, to get the angle correct for non-vertical layouts
        self.previous_bearing_position = previous_bearing_position
        #from the top of the back plate to the bottom of the wheel/anchor
        self.distance_from_back = bearing_position[2]

        self.total_thickness = self.arbor.get_total_thickness(just_pinion =escapement_on_front and self.arbor.get_type() == ArborType.ESCAPE_WHEEL)

        self.distance_from_front = (self.plate_distance - self.endshake) - self.total_thickness - self.distance_from_back

        self.pendulum_fixing = pendulum_fixing
        self.escapement_on_front = escapement_on_front

        self.type = self.arbor.get_type()

        #for an escapement on the front, how far from the front plate is the anchor?
        #want space for a washer to act as a standoff against the bearing and a bit of wobble to account for the top wall standoff to flex a bit
        # - I think I'm completely wrong including teh washer thick here, but I do want it extended anyway
        self.front_anchor_from_plate = front_anchor_from_plate
        if self.front_anchor_from_plate < 0:
            self.front_anchor_from_plate = self.endshake# + 2 - IS THIS WHY THE ANCHOR ARBOR WAS ALWAYS TOO SHORT??
        # ============ anchor bits ===============
        #for direct pendulum arbour with esacpement on the front there's a collet to hold it in place for endshape
        self.collet_thick = 6
        self.collet_screws = MachineScrew(2,countersunk=True)
        self.pendulum_holder_thick = 15
        self.pendulum_fixing_extra_space = 0.2
        #diameter of the bit taht links anchor and pendulum holder
        self.direct_arbor_d = direct_arbor_d
        #for the collet
        self.outer_d = (self.bearing.inner_safe_d + self.bearing.outer_d) / 2

        self.cylinder_r = self.direct_arbor_d / 2
        self.square_side_length = math.sqrt(2) * self.cylinder_r

        if self.cylinder_r < 5:
            self.square_side_length = math.sqrt(2) * self.cylinder_r * 1.2

        self.crutch_holder_slack_space = 2
        self.crutch_thick = crutch_space - self.crutch_holder_slack_space

        self.suspension_spring_bits = SuspensionSpringPendulumBits(crutch_thick=self.crutch_thick, square_side_length=self.square_side_length + self.pendulum_fixing_extra_space)
        self.friction_fit_bits = FrictionFitPendulumBits(arbor_d=self.arbor.arbor_d)

        #distance between back of back plate and front of front plate (plate_distance is the literal plate distance, including endshake)
        self.total_plate_thickness = self.plate_distance + (self.front_plate_thick + self.back_plate_thick)

        # so that we don't have the arbour pressing up against hte bit of the bearing that doesn't move, adding friction
        self.arbour_bearing_standoff_length = LAYER_THICK * 2
        self.lantern_pinion_wheel_holder_thick = 2

        if self.type == ArborType.POWERED_WHEEL and self.arbor.powered_wheel.type == PowerType.SPRING_BARREL:
            self.bearing = self.arbor.powered_wheel.key_bearing

        #for powered wheels with keys, the plates calculates this
        self.key_length = 0


    def get_max_radius(self, above=False):
        if self.arbor.type == ArborType.ANCHOR:
            #too much of the anchor is dependant on the plate, even though a method exists to use the base arbor
            if above:
                return self.outer_d / 2
            else:
                return self.arbor.escapement.largest_anchor_r

        else:
            return self.arbor.get_max_radius()

    def get_anchor_collet(self):
        '''
        get a collet that fits on the direct arbour anchor to prevent it sliding out and holds the pendulum
        '''

        outer_d = self.outer_d
        height = self.collet_thick - LAYER_THICK*2

        square_size = self.square_side_length+self.pendulum_fixing_extra_space


        collet = cq.Workplane("XY").circle(outer_d/2).rect(square_size, square_size).extrude(height)
        collet = collet.faces(">Z").workplane().circle(self.bearing.inner_safe_d / 2).rect(square_size, square_size).extrude(self.collet_thick - height)

        collet = collet.cut(self.collet_screws.get_cutter(length=outer_d / 2).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -outer_d / 2, self.collet_thick / 2)))
        collet = collet.cut(self.collet_screws.get_nut_cutter(half=True).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -square_size / 2, self.collet_thick / 2)))

        return collet

    def get_pendulum_crutch(self):

        if self.pendulum_fixing not in [PendulumFixing.SUSPENSION_SPRING, PendulumFixing.SUSPENSION_SPRING_WITH_PLATE_HOLE]:
            return None
        return self.suspension_spring_bits.get_crutch()

    def get_pendulum_holder_collet(self):
        '''
        will slot over square bit of anchor arbour and screw in place
        for the direct arbours without suspension spring
        '''
        outer_d = self.outer_d
        if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS:
            outer_d = self.cylinder_r*4#DIRECT_ARBOUR_D*2

        square_size = self.square_side_length + self.pendulum_fixing_extra_space

        extra_distance_from_bearing = + 5
        #plus extra so it's easier to slot the pendulum out when it's near the bearing holder on the top wall standoff
        gap_between_square_and_pendulum_hole = self.collet_screws.get_nut_height(half=True) + 1 + self.collet_screws.get_head_height() + extra_distance_from_bearing

        height = outer_d*2.5 + extra_distance_from_bearing
        print("gap_between_square_and_pendulum_hole (and m2 screw) = ",gap_between_square_and_pendulum_hole)
        r = outer_d/2

        collet = cq.Workplane("XY").tag("base").circle(r).extrude(self.pendulum_holder_thick)
        collet = collet.workplaneFromTagged("base").moveTo(0,r - height/2).rect(outer_d, height - outer_d).extrude(self.pendulum_holder_thick)
        collet = collet.workplaneFromTagged("base").moveTo(0, outer_d - height).circle(r).extrude(self.pendulum_holder_thick)

        #square bit that slots over arbour
        collet = collet.cut(cq.Workplane("XY").rect(square_size, square_size).extrude(self.pendulum_holder_thick))

        #means to hold end of pendulum made of threaded rod
        collet = collet.cut(get_pendulum_holder_cutter(z=self.pendulum_holder_thick/2).translate((0,-self.square_side_length/2-gap_between_square_and_pendulum_hole)))

        #means to hold screw that will hold this in place
        collet = collet.cut(self.collet_screws.get_cutter(length=outer_d / 2, head_space_length=5).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -outer_d / 2, self.pendulum_holder_thick / 2)))
        collet = collet.cut(self.collet_screws.get_nut_cutter(half=True).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -square_size / 2, self.pendulum_holder_thick / 2)))


        return collet

    def get_standalone_pinion_with_arbor_extension(self, for_printing=True):
        standalone_pinion = self.arbor.get_standalone_pinion()
        # include the shortest arbor extension (since the short one could be a pain to thread onto the rod by itself)
        including_front_arbor_extension = self.distance_from_front < self.distance_from_back
        arbour_extension = self.get_arbour_extension(front=including_front_arbor_extension)

        thick = self.arbor.end_cap_thick * 2 + self.arbor.pinion_thick
        if arbour_extension is not None:
            standalone_pinion = standalone_pinion.add(arbour_extension.translate((0, 0, thick)))

        if not for_printing and not including_front_arbor_extension:
            standalone_pinion = standalone_pinion.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, thick))

        return standalone_pinion

    def get_escape_wheel(self, for_printing=True):
        '''
        if escapement_on_front this is a standalone escape wheel, otherwise it's a fairly standard abor
        '''
        if self.escapement_on_front:
            #it's just teh wheel for now, but extended a bit to make it more sturdy
            #TODO extend back towards the front plate by the distance dictacted by the escapement

            extra_arbour_length = self.front_anchor_from_plate - self.arbor.escapement.get_wheel_base_to_anchor_base_z() - self.endshake - 1
            if extra_arbour_length > 10:
                extra_arbour_length = 10
            extend_out_front = self.plates.extra_support_for_escape_wheel
            arbourThreadedRod = MachineScrew(metric_thread=self.arbor_d)

            #using a half height nut so we get more rigidity on the rod, and we're clamping this in with a nut on the front anyway
            nut_height = arbourThreadedRod.get_nut_height(half=True)

            #if there's a bearing support out the front, extend out the front of the escape wheel, otherwise extend behind
            if extend_out_front:
                face = ">Z"
                nut_base_z = self.arbor.wheel_thick + extra_arbour_length - nut_height
            else:
                face = "<Z"
                nut_base_z = -extra_arbour_length

            wheel = self.arbor.get_escape_wheel(standalone=True).faces(">Z").circle(self.arbor_d/2).cutThruAll()

            wheel = wheel.faces(face).workplane().moveTo(0,0).circle(self.arbor_d*2).circle(self.arbor_d/2).extrude(extra_arbour_length)


            #Clamping this both sides - plannign to use a dome nut on the front
            wheel = wheel.cut(arbourThreadedRod.get_nut_cutter(half=True).translate((0, 0, nut_base_z)))

            if for_printing and not extend_out_front:
                wheel = wheel.rotate((0,0,0),(1,0,0),180).translate((0,0,self.arbor.wheel_thick))


        else:

            wheel = self.arbor.get_escape_wheel()

            if self.need_arbor_extension(front=self.arbor.pinion_at_front):
                #need arbor extension on the pinion
                wheel = wheel.union(self.get_arbour_extension(front=self.arbor.pinion_at_front).translate((0, 0, self.total_thickness)))

        return wheel

    def get_escape_wheel_shapes(self):

        shapes = {}

        if self.escapement_on_front:

            shapes["pinion"] = self.get_standalone_pinion_with_arbor_extension()
        shapes["wheel"] = self.get_escape_wheel()


        return shapes



    def get_anchor_shapes(self):
        shapes = {}
        previous_bearing_to_here = np_to_set(np.subtract(self.bearing_position, self.previous_bearing_position))
        anchor_angle = math.atan2(previous_bearing_to_here[1], previous_bearing_to_here[0]) - math.pi/2
        #the Arbor will flip the anchor to the correct clockwiseness
        anchor = self.arbor.get_anchor().rotate((0, 0, 0), (0, 0, 1), radToDeg(anchor_angle))
        anchor_thick = self.arbor.escapement.get_anchor_thick()
        # flip over so the front is on the print bed
        anchor = anchor.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, anchor_thick))
        if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOUR, PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING_WITH_PLATE_HOLE, PendulumFixing.SUSPENSION_SPRING]:


            #direct arbour pendulum fixing - a cylinder that extends from the anchor until it reaches where the pendulum should be and becomes a square rod
            #if the anchor is between the plates then the end-shake is controlled by the extensions out each side of the anchor.
            #if the anchor is on the front plate (assumed pendulum is at back), then the cylinder extends all the way through the plates and the square rod is at the back
            #the end of the square rod controls one bit of end shake and there will be a collect that slots onto the rod to control the other

            #suspension spring is the same shape of arbour, just with less distance between the anchor and the square bit

            #no need to support direct arbour with large bearings


            if self.pendulum_fixing not in [PendulumFixing.SUSPENSION_SPRING_WITH_PLATE_HOLE, PendulumFixing.SUSPENSION_SPRING]:
                shapes["pendulum_holder"]=self.get_pendulum_holder_collet()
                #else TODO suspension spring holder

            if not self.pendulum_at_front:
                rear_bearing_standoff_height = LAYER_THICK * 2
                if self.pendulum_fixing == PendulumFixing.SUSPENSION_SPRING_WITH_PLATE_HOLE:
                    #square bit just up to the top back plate
                    square_rod_length = self.distance_from_back - rear_bearing_standoff_height
                elif self.pendulum_fixing == PendulumFixing.SUSPENSION_SPRING:
                    #round up to the back of the back plate then square out the back
                    #some extra so the crutch doesn't have to be perfectly aligned
                    square_rod_length = self.crutch_thick + self.crutch_holder_slack_space - rear_bearing_standoff_height
                else:
                    #bits out the back

                    square_rod_length = self.back_plate_from_wall - self.standoff_plate_thick - self.endshake - rear_bearing_standoff_height


                '''
                Esacpement on teh front and pendulum at the back (like grasshopper)
                '''
                if self.escapement_on_front:
                    #cylinder passes through plates and out the front
                    cylinder_length = self.front_anchor_from_plate + self.total_plate_thickness

                else:
                    #cylinder passes only through the back plate and up to the anchor
                    #no need for collet - still contained within two bearings like a normal arbour

                    if self.pendulum_fixing == PendulumFixing.SUSPENSION_SPRING_WITH_PLATE_HOLE:
                        #we put the square section right on the back of the anchor
                        cylinder_length = 0
                    else:
                        #cylinder up to the back of the back plate
                        cylinder_length = self.back_plate_thick + self.endshake + self.bearing_position[2]
                    shapes["arbour_extension"] = self.get_arbour_extension(front=True)





                wall_bearing = get_bearing_info(self.arbor.arbor_d)


                #circular bit
                anchor = anchor.union(cq.Workplane("XY").circle(self.cylinder_r).extrude(cylinder_length + anchor_thick))
                #square bit
                anchor = anchor.union(cq.Workplane("XY").rect(self.square_side_length, self.square_side_length).extrude(square_rod_length).intersect(cq.Workplane("XY").circle(self.cylinder_r).extrude(square_rod_length)).translate((0,0, anchor_thick + cylinder_length)))
                #bearing standoff
                anchor = anchor.union(cq.Workplane("XY").circle(wall_bearing.inner_safe_d / 2).circle(self.arbor.arbor_d / 2).extrude(rear_bearing_standoff_height).translate((0, 0, anchor_thick + cylinder_length + square_rod_length)))
                #cut hole through the middle
                anchor = anchor.cut(cq.Workplane("XY").circle(self.arbor.arbor_d / 2 + ARBOUR_WIGGLE_ROOM/2).extrude(anchor_thick + cylinder_length + square_rod_length + rear_bearing_standoff_height))

            else:
                '''
                I don't think I'm going to design many more with the pendulum on the front, so I'm not going to bother supporting that with a direct arbour unless I have to
                TODO - would be useful to have old designs working again (done, supported with old friction fitting)
                UPDATE: several people have remarked that they like the style of the old pendulum on front clocks, so I might ressurect it free of the friction fitting, using something like
                the escapement on front mechanism
                '''
                raise NotImplementedError("Unsuported escapement and pendulum combination!")
        else:
            #friction fitting pendulum
            shapes["pendulum_holder"] = self.friction_fit_bits.get_pendulum_holder()
            shapes["arbour_extension"] = self.get_arbour_extension(front=True)
            anchor = anchor.union(self.get_arbour_extension(front=False).translate((0,0,anchor_thick)))
            # print("Only direct arbour pendulum fixing supported currently")
        shapes["anchor"] = anchor

        crutch = self.get_pendulum_crutch()
        if crutch is not None:
            shapes["crutch"] = crutch

        return shapes

    def get_assembled(self):
        '''
        Get a model that is relative to the back of the back plate of the clock and already in position (so you should just be able to add it straight to the model)

        This is slowly refactoring the complex logic from the Arbour class to here. the ultimate aim is for the arbour class to be unaware of the plates
        and this class be the only one with interactions with the plates
        '''

        assembly = cq.Workplane("XY")
        shapes = self.get_shapes()
        if self.type == ArborType.ANCHOR:
            assembly = assembly.add(shapes["anchor"].rotate((0, 0, 0), (1, 0, 0), 180))
            if self.arbor.escapement.type == EscapementType.GRASSHOPPER:
                # move 'down' by frame thick because we've just rotated the frame above
                assembly = assembly.add(self.arbor.escapement.get_assembled(leave_out_wheel_and_frame=True, centre_on_anchor=True, mid_pendulum_swing=True).translate((0, 0, -self.arbor.escapement.frame_thick)))


            if self.escapement_on_front:
                #minus half the endshake is very much deliberate, because otherwise with total_plate_thickness included we're putting the arbor as far forwards as it can go. We want it to be modelled in the centre
                anchor_assembly_end_z = self.total_plate_thickness + self.front_anchor_from_plate + self.arbor.escapement.get_anchor_thick() - self.endshake / 2
            else:
                anchor_assembly_end_z = self.back_plate_thick + self.bearing_position[2] + self.endshake/2 + self.arbor.escapement.get_anchor_thick()
                if "arbour_extension" in shapes and shapes["arbour_extension"] is not None:
                    #can be none if the anchor is pressed up against a plate
                    assembly = assembly.add(shapes["arbour_extension"])
            assembly = assembly.translate((0,0,anchor_assembly_end_z))
            if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOUR and self.escapement_on_front and not self.pendulum_at_front:
                collet = shapes["collet"]
                assembly = assembly.add(collet.translate((0, 0, -self.collet_thick - self.endshake/2)))
            if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS, PendulumFixing.FRICTION_ROD]:
                pendulum_z = -self.pendulum_sticks_out

                if self.pendulum_at_front:
                    pendulum_z = self.total_plate_thickness + self.pendulum_sticks_out

                assembly = assembly.add(shapes["pendulum_holder"].rotate((0,0,0),(0,1,0),180).translate((0,0,pendulum_z + self.pendulum_holder_thick/2)))
            if self.pendulum_fixing == PendulumFixing.SUSPENSION_SPRING:
                assembly = assembly.add(shapes["crutch"].rotate((0,0,0),(0,1,0),180).translate((0,0, - self.endshake/2 - self.crutch_holder_slack_space/2 - self.arbour_bearing_standoff_length/2)))
            assembly = assembly.translate((self.bearing_position[0], self.bearing_position[1]))
        elif self.type == ArborType.ESCAPE_WHEEL and self.escapement_on_front:
            pinion = self.get_standalone_pinion_with_arbor_extension(for_printing=False)
            pinion = pinion.translate(self.bearing_position).translate((0, 0, self.back_plate_thick + self.endshake / 2))
            assembly = assembly.add(pinion)

            wheel = self.get_escape_wheel(for_printing=False)
            #same as anchor, pulling back by half the endshake
            wheel = wheel.translate((self.bearing_position[0], self.bearing_position[1], self.total_plate_thickness + self.front_anchor_from_plate - self.arbor.escapement.get_wheel_base_to_anchor_base_z() - self.endshake / 2))
            assembly = assembly.add(wheel)
        elif self.type == ArborType.POWERED_WHEEL:

            if "ratchet" in shapes:
                # already in the right place
                assembly = assembly.add(shapes["ratchet"])

            if not self.arbor.combine_with_powered_wheel:
                assembly = assembly.add(self.arbor.powered_wheel.get_model().translate((0, 0, self.arbor.wheel_thick)))

            wheel = shapes["wheel"]
            if self.arbor.weight_driven:
                #it's been flipped on its back to make it printable, turn it back
                wheel = wheel.rotate((0,0,0),(1,0,0),180).translate((0,0, self.arbor.wheel_thick))

            assembly = assembly.add(wheel)
            if self.arbor.powered_wheel.type == PowerType.SPRING_BARREL:
                spring_barrel = self.arbor.powered_wheel
                #deliberately not including back bearing standoff as that's taken out of the distance_from_back
                arbor = shapes["spring_arbor"].rotate((0, 0, 0), (0, 1, 0), -90).translate((spring_barrel.arbor_d/2 - spring_barrel.cutoff_height, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -90)
                assembly = assembly.add(arbor)
                assembly = assembly.add(spring_barrel.get_lid(for_printing=False).translate((0,0,spring_barrel.base_thick + spring_barrel.barrel_height)))
                assembly = assembly.add(spring_barrel.get_front_bearing_standoff_washer().translate((0,0,spring_barrel.get_height() - spring_barrel.front_bearing_standoff)))

            assembly = assembly.translate(self.bearing_position).translate((0,0, self.back_plate_thick + self.endshake/2))
        else:
            #"normal" wheel-pinion pair (or escape wheel if not on the front)
            arbor = shapes["wheel"]
            if "lantern_pinion_cap" in shapes:
                arbor = arbor.add(shapes["lantern_pinion_cap"].translate((0,0,self.arbor.wheel_thick + self.arbor.pinion_thick)))

            if not self.arbor.pinion_at_front:
                arbor = arbor.rotate((0,0,0),(1,0,0),180).translate((0,0,self.total_thickness))

            assembly = assembly.add(arbor.translate(self.bearing_position).translate((0,0, self.back_plate_thick + self.endshake/2)))


        if self.need_separate_arbor_extension(front=True):
            assembly = assembly.add(self.get_arbour_extension(front = True).translate(self.bearing_position).translate((0,0, self.endshake/2 + self.total_thickness + self.back_plate_thick)))
        if self.need_separate_arbor_extension(front = False):
            assembly = assembly.add(self.get_arbour_extension(front = False).rotate((0,0,0),(1,0,0),180).translate(self.bearing_position).translate((0,0,self.endshake/2 + self.back_plate_thick)))

        return assembly


    def get_shapes(self):
        '''
        return a dict of name:shape for all the components needed for this arbour
        always for printing, they will be arranged for the model in get_assembled()
        '''
        shapes = {}

        extras = self.arbor.get_extras(rear_side_extension=self.distance_from_back + self.endshake + self.back_plate_thick,
                                       front_side_extension=self.endshake / 2 + self.front_plate_thick, key_length=self.key_length,
                                       ratchet_key_extra_length=0)
        for extraName in extras:
            shapes[extraName] = extras[extraName]

        if self.arbor.get_type() == ArborType.ANCHOR:
            shapes = self.get_anchor_shapes()
        elif self.arbor.get_type() == ArborType.ESCAPE_WHEEL:
            shapes = self.get_escape_wheel_shapes()
            shapes["pinion_STL_modifier"] = self.arbor.get_STL_modifier_pinion_shape()
        elif self.arbor.get_type() == ArborType.WHEEL_AND_PINION:

            wheel = self.arbor.get_shape()

            if self.need_arbor_extension(front=self.arbor.pinion_at_front) and not self.need_separate_arbor_extension(front=self.arbor.pinion_at_front):
                #need arbor extension on the pinion
                wheel = wheel.union(self.get_arbour_extension(front=self.arbor.pinion_at_front).translate((0, 0, self.total_thickness)))

            shapes["wheel"] = wheel


            shapes["pinion_STL_modifier"]=self.arbor.get_STL_modifier_pinion_shape()
        elif self.arbor.get_type() == ArborType.POWERED_WHEEL:
            #TODO support chain at front?
            wheel = self.arbor.get_powered_wheel(rear_side_extension = self.distance_from_back, arbour_extension_max_radius=self.arbour_extension_max_radius)
            shapes["wheel"] = wheel
            #rear side extended full endshake so we could go plain bushing if needed




        if self.need_separate_arbor_extension(front=False):
            shapes['arbour_extension_rear'] = self.get_arbour_extension(front=False)
        if self.need_separate_arbor_extension(front=True):
            shapes['arbour_extension_front'] = self.get_arbour_extension(front=True)

        return shapes

    def add_arbor_extension(self, shape):
        '''
        Given a lone wheel/pinion pair (or equivalent) in the printing position (pinion up) add the relevant arbor extension on top
        '''

        # note, the included extension is always on the pinion side (unprintable otherwise)
        if self.need_arbor_extension(front=True) and self.arbor.pinion_at_front:
            # need arbour extension on the front
            extendo = self.get_arbour_extension(front=True).translate((0, 0, self.total_thickness))
            shape = shape.union(extendo)

        if self.need_arbor_extension(front=False) and not self.arbor.pinion_at_front:
            # need arbour extension on the rear
            extendo = self.get_arbour_extension(front=False).translate((0, 0, self.total_thickness))
            shape = shape.union(extendo)

        return shape

    def need_separate_arbor_extension(self, front=True):
        '''
        Need a separate component for teh arbor extension on thsi side
        '''

        if self.arbor.get_type() == ArborType.POWERED_WHEEL:
            return False

        if self.arbor.get_type() == ArborType.ANCHOR and self.pendulum_fixing != PendulumFixing.FRICTION_ROD:
            if self.escapement_on_front:
                return False
            return self.pendulum_at_front != front

        if self.arbor.get_type() == ArborType.ESCAPE_WHEEL and self.escapement_on_front:
            #the longest is the one separate
            if self.distance_from_back > self.distance_from_front:
                #back one is longest
                return not front
            else:
                #front one is longest
                return front

        if self.arbor.get_type() in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL] and self.arbor.pinion.lantern:
            return True

        if not front and self.arbor.pinion_at_front and self.need_arbor_extension(front=False):
            #need a rear arbor extension
            return True
        if front and not self.arbor.pinion_at_front and self.need_arbor_extension(front=True):
            #need a front arbor extension
            return True
        return False

    def need_arbor_extension(self, front=True):
        '''
        Need an arbor extension on this side of the arbor. May or may not end up being combined with the arbor
        '''
        #not enough to print
        if front and self.distance_from_front < self.arbour_bearing_standoff_length:
            return False
        if (not front) and self.distance_from_back < self.arbour_bearing_standoff_length:
            return False

        if self.arbor.get_type() == ArborType.POWERED_WHEEL:
            #assuming chain is at front
            if front == self.arbor.pinion_at_front:
                return False
            else:
                # the rope wheel is printed in one peice, print the standoff (the arbor extension) on the front
                return self.arbor.combine_with_powered_wheel
            #the extension out the back is always needed and calculated elsewhere TODO

        return self.get_arbour_extension(front=front) is not None

    def get_arbour_extension(self, front=True):
        '''
        Get little cylinders we can use as spacers to keep the gears in the right place on the rod

        Simple logic here, it may produce some which aren't needed
        '''

        length = self.distance_from_front if front else self.distance_from_back
        bearing = get_bearing_info(self.arbor.get_rod_d())

        outer_r = self.arbor.get_arbor_extension_r()
        inner_r = self.arbor.get_arbor_extension_r() / 2 + ARBOUR_WIGGLE_ROOM / 2
        tip_r = bearing.inner_safe_d / 2
        if tip_r > outer_r:
            tip_r = outer_r


        if length - self.arbour_bearing_standoff_length >= 0:
            # 0.1 to avoid trying to extude a 0.0000x long cylinder which causes CQ to throw a wobbly
            if length - self.arbour_bearing_standoff_length > 0.1:
                extendo_arbour = cq.Workplane("XY").tag("base").circle(outer_r).circle(inner_r).extrude(length-self.arbour_bearing_standoff_length).faces(">Z").workplane()
            else:
                extendo_arbour=cq.Workplane("XY")
            extendo_arbour = extendo_arbour.circle(tip_r).circle(inner_r).extrude(self.arbour_bearing_standoff_length)

            if (length-self.arbour_bearing_standoff_length > self.lantern_pinion_wheel_holder_thick and self.arbor.pinion is not None
                    and self.arbor.pinion.lantern):# and front is not self.arbor.pinion_at_front):
                #extra wide flange to help the wheel remain perpendicular
                #first just did this to help the wheel remain perpendicular, but now doing it for front and back as it makes it much easier to glue everything together.
                #will work out if it ends up clashing with other wheels if it becomes a problem in the future
                extendo_arbour = extendo_arbour.union(cq.Workplane("XY").circle(self.arbor.pinion.get_max_radius()).circle(inner_r).extrude(self.lantern_pinion_wheel_holder_thick))

            return extendo_arbour
        return None




class Arbor:
    def __init__(self, arbor_d=None, wheel=None, wheel_thick=None, pinion=None, pinion_thick=None, pinion_extension=0, powered_wheel=None, escapement=None, end_cap_thick=1, style=GearStyle.ARCS,
                 distance_to_next_arbour=-1, pinion_at_front=True, ratchet_screws=None, use_ratchet=True, clockwise_from_pinion_side=True):
        '''
        This represents a combination of wheel and pinion. But with special versions:
        - chain wheel is wheel + ratchet (pinionThick is used for ratchet thickness)
        - escape wheel is pinion + escape wheel
        - anchor is just the escapement anchor

        This is purely theoretical and you need the ArbourForPlate to produce an STL that can be printed

        its primary purpose is to help perform the layout of a gear train.


        NOTE currently assumes chain/cord is at the front - needs to be controlled by something like pinionAtFront
        '''
        #diameter of the threaded rod. Usually assumed to also be the size of the hole
        self.arbor_d=arbor_d
        self.wheel=wheel
        self.wheel_thick=wheel_thick
        self.pinion=pinion
        self.pinion_thick=pinion_thick
        #where the pinion is extended (probably to ensure the wheel avoids something) but don't want to treat it just as an extra-thick pinion
        self.pinion_extension = pinion_extension
        self.escapement=escapement
        self.end_cap_thick=end_cap_thick
        #the pocket chain wheel or cord wheel (needed to calculate full height and a few tweaks)
        self.powered_wheel=powered_wheel
        self.style=style
        self.distance_to_next_arbour=distance_to_next_arbour
        #for the anchor, this is the side with the pendulum
        #for the powered wheel, this is the side with the chain/rope/cord
        self.pinion_at_front=pinion_at_front
        #used for cutting the gear style and getting teh escapement the right way around. Mild bodge: for the Anchor this means clockwise from front
        self.clockwise_from_pinion_side = clockwise_from_pinion_side
        #if using hyugens maintaining power then the chain wheel is directly fixed to the wheel, without a ratchet.
        self.use_ratchet=use_ratchet
        #is this screwed (and optionally glued) to the threaded rod?
        self.loose_on_rod = False

        self.ratchet = None
        if self.powered_wheel is not None:
            self.ratchet=self.powered_wheel.ratchet

        if self.get_type() == ArborType.POWERED_WHEEL:
            # currently this can only be used with the cord wheel
            self.loose_on_rod = (not self.powered_wheel.loose_on_rod) and use_ratchet

        self.hole_d = arbor_d
        if self.loose_on_rod:
            if self.arbor_d == 4:
                # assume steel pipe (currently only have pipe with a 4mm internal diameter)
                #6.2 squeezes on and holds tight!
                self.hole_d = STEEL_TUBE_DIAMETER
            else:
                self.hole_d = self.arbor_d + LOOSE_FIT_ON_ROD

        if self.get_type() == ArborType.UNKNOWN:
            raise ValueError("Not a valid arbour")

        #just to help debugging
        self.type = self.get_type()

        self.combine_with_powered_wheel = False

        if self.get_type() == ArborType.POWERED_WHEEL:
            #chain/cord wheel specific bits:
            self.weight_driven = PowerType.is_weight(self.powered_wheel.type)
            #remove support for not bolt on ratchet and inset ratchet as they're never used anymore - the bolt on ratchet has proven to be a good design
            if self.weight_driven:
                self.ratchet_screws = ratchet_screws
                if self.ratchet_screws is None:
                    self.ratchet_screws = MachineScrew(2, countersunk=True)

                if self.use_ratchet:
                    #could do with not having to care about the innards of the ratchet here
                    if self.powered_wheel.traditional_ratchet:
                        self.bolt_positions = self.powered_wheel.ratchet.get_screw_positions()
                        self.ratchet_screws = self.powered_wheel.ratchet.fixing_screws
                    else:
                        bolts = 4
                        outer_r = self.ratchet.outsideDiameter / 2
                        inner_r = self.ratchet.toothRadius
                        bolt_distance = (outer_r + inner_r) / 2

                        #offsetting so it's in the middle of a click (where it's slightly wider)
                        self.bolt_positions=[polar(i * math.pi * 2 / bolts + math.pi / self.ratchet.ratchetTeeth, bolt_distance) for i in range(bolts)]
                else:
                    #bolting powered wheel on without a ratchet
                    self.bolt_positions = self.powered_wheel.get_screw_positions()



                if not self.use_ratchet and self.powered_wheel.type == PowerType.ROPE:
                    #this can be printed in one peice, so combine with the wheel and use a standard arbour extension
                    self.combine_with_powered_wheel = True
            else:
                #spring type
                self.combine_with_powered_wheel = True
                if self.powered_wheel.type == PowerType.SPRING_BARREL:
                    self.hole_d = self.powered_wheel.get_barrel_hole_d()
                    self.use_ratchet = False

        if self.get_type() == ArborType.ANCHOR:
            #the anchor now controls its own thickness and arbour thickness, so get dimensions from that
            self.arbor_d = self.escapement.get_anchor_arbor_d()
            self.hole_d = self.arbor_d
            self.wheel_thick = self.escapement.get_anchor_thick()
        if self.get_type() == ArborType.ESCAPE_WHEEL:
            self.wheel_thick = self.escapement.get_wheel_thick()


    def get_type(self):
        if self.wheel is not None and self.pinion is not None:
            return ArborType.WHEEL_AND_PINION
        if self.wheel is not None and self.powered_wheel is not None:
            return ArborType.POWERED_WHEEL
        if self.wheel is None and self.escapement is not None and self.pinion is not None:
            return ArborType.ESCAPE_WHEEL
        if self.escapement is not None:
            return ArborType.ANCHOR
        return ArborType.UNKNOWN

    def get_rod_d(self):
        return self.arbor_d
    def get_arbor_extension_r(self):
        return self.arbor_d

    def get_total_thickness(self, just_pinion=False):
        '''
        return total thickness of everything that will be on the rod (between the plates!)
        '''
        if self.get_type() in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL]:

            if just_pinion:
                #just the pinion is within the plates
                return self.pinion_thick + self.pinion_extension + self.end_cap_thick * 2

            return self.wheel_thick + self.pinion_thick + self.pinion_extension + self.end_cap_thick
        if self.get_type() == ArborType.POWERED_WHEEL:
            #the chainwheel (or cordwheel) now includes the ratceht thickness
            if self.powered_wheel.type == PowerType.SPRING_BARREL:
                #spring barrel is incorporated into the wheel rather than stuck on the front
                return self.powered_wheel.get_height()
            return self.wheel_thick + self.powered_wheel.get_height()
        if self.get_type() == ArborType.ANCHOR:
            # wheel thick being used for anchor thick
            return self.wheel_thick

    def get_wheel_centre_z(self):
        '''
        Get the centre of the height of the wheel - which drives the next arbour
        '''
        if self.pinion_at_front:
            return self.wheel_thick / 2
        else:
            return self.get_total_thickness() - self.wheel_thick / 2

    def get_pinion_centre_z(self):
        if self.get_type() not in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL]:
            raise ValueError("This arbour (type {}) does not have a pinion".format(self.get_type()))
        if self.pinion_at_front:
            return self.get_total_thickness() - self.end_cap_thick - self.pinion_thick / 2
        else:
            return self.end_cap_thick + self.pinion_thick / 2

    def get_pinion_to_wheel_z(self):
        '''
        Useful for calculating the height of the next part of the power train
        '''
        return self.get_wheel_centre_z() - self.get_pinion_centre_z()

    def get_max_radius(self):
        if self.wheel is not None:
            #chain wheel, WheelAndPinion
            return self.wheel.get_max_radius()
        if self.get_type() == ArborType.ESCAPE_WHEEL:
            return self.escapement.get_wheel_max_r()
        if self.get_type() == ArborType.ANCHOR:
            return self.escapement.get_anchor_max_r()
        raise NotImplementedError("Max Radius not yet implemented for arbour type {}".format(self.get_type()))

    def get_escape_wheel(self, standalone=False):
        '''
        if standalone returns a clockwise wheel for teh ArborForPlate class to sort out
        if not it returns a wheel pinion pair
        '''
        arbour_or_pivot_r = self.pinion.get_max_radius()
        if standalone:
            arbour_or_pivot_r = self.arbor_d * 2
        wheel = self.escapement.get_wheel_2d()

        clockwise = True if standalone else self.clockwise_from_pinion_side


        wheel = wheel.extrude(self.wheel_thick)
        wheel = Gear.cutStyle(wheel, outerRadius=self.escapement.get_wheel_inner_r(), innerRadius=arbour_or_pivot_r, style = self.style, clockwise_from_pinion_side=clockwise)

        if standalone:
            return wheel

        if not self.clockwise_from_pinion_side:
            wheel = wheel.mirror("YZ", (0, 0, 0))



        # if self.escapement.type == EscapementType.GRASSHOPPER and not self.escapement.clockwiseFromPinionSide:
        #     # bodge, should try and tidy up how the escapements do this, but generally the anchor will be inside the plates (attached to a pinion) and the grasshopper won't be
        #     # so this here is probably an edge case
        #     wheel = wheel.mirror("YZ", (0, 0, 0))

        # pinion is on top of the wheel
        pinion = self.pinion.get3D(thick=self.pinion_thick, holeD=self.hole_d, style=self.style).translate([0, 0, self.wheel_thick])

        arbour = wheel.union(pinion)
        if self.end_cap_thick > 0:
            arbour = arbour.union(cq.Workplane("XY").circle(self.pinion.get_max_radius()).extrude(self.end_cap_thick).translate((0, 0, self.wheel_thick + self.pinion_thick)))

        arbour = arbour.cut(cq.Workplane("XY").circle(self.hole_d / 2).extrude(self.wheel_thick + self.pinion_thick + self.end_cap_thick))

        return arbour

    def get_STL_modifier_pinion_shape(self):
        '''
        return a shape that covers the teeth of the pinions for apply tweaks to the slicing settings
        '''

        if self.get_type() in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL]:
            return self.pinion.get_STL_modifier_shape(thick=self.pinion_thick, offset_z=self.wheel_thick + self.pinion_extension, min_inner_r=self.arbor_d / 2)

        return None

    def get_STL_modifier_wheel_shape(self):
        '''
        return a shape that covers the teeth of the pinions for apply tweaks to the slicing settings
        '''

        if self.get_type() == ArborType.WHEEL_AND_PINION:
            return self.wheel.get_STL_modifier_shape(thick=self.pinion_thick, offset_z=self.wheel_thick, min_inner_r=self.arbor_d / 2)

        return None

    def get_shape(self, for_printing=True):
        '''
        return a shape that can be exported to STL
        if for printing, wheel is on the bottom, if false, this is in the orientation required for the final clock
        '''
        if self.get_type() == ArborType.WHEEL_AND_PINION:

            shape = self.pinion.add_to_wheel(self.wheel, hole_d=self.hole_d, thick=self.wheel_thick, style=self.style, pinion_thick=self.pinion_thick,
                                             pinion_extension=self.pinion_extension, cap_thick=self.end_cap_thick, clockwise_from_pinion_side=self.clockwise_from_pinion_side)

            # shape = self.pinion.get3D

        elif self.get_type() == ArborType.ESCAPE_WHEEL:
            #will be completely override by ArborForPlate
            shape = self.get_escape_wheel()
        elif self.get_type() == ArborType.POWERED_WHEEL:
            shape = self.get_powered_wheel(for_printing=for_printing)
        elif self.get_type() == ArborType.ANCHOR:
            # will be completely override by ArborForPlate
            shape = self.get_anchor(for_printing=for_printing)
        else:
            raise ValueError("Cannot produce 3D model for type: {}".format(self.get_type().value))

        if not for_printing and not self.pinion_at_front and (self.get_type() in [ArborType.WHEEL_AND_PINION]):
            #make it the right way around for placing in a model
            #rotate not mirror! otherwise the escape wheels end up backwards
            # shape = shape.rotate((0,0,0),(1,0,0),180).translate((0,0,self.getTotalThickness()))
            shape = shape.mirror("YZ", (0, 0, 0))


        return shape


    def get_anchor(self, for_printing=True):

        #just the anchor/frame shape, with nothing else that might be needed
        anchor = self.escapement.get_anchor()

        if not self.clockwise_from_pinion_side:
            #clockwise_from_pinion_side is being abused to mean clockwise from front
            anchor = anchor.mirror("YZ", (0, 0, 0))

        return anchor


    def get_assembled(self):
        '''
        return this arbour fully assembled for debugging. The model is built from using ArborForPlates
        (0,0,0) should be in the centre of the arbour, at the back of the wheel or pinion
        '''

        #get the main bit, the right way round
        shape = self.get_shape(for_printing=False)

        if self.get_type() == ArborType.POWERED_WHEEL:
            # should work for both chain and cord

            bolt_on_ratchet = self.get_extra_ratchet(for_printing=False)
            if bolt_on_ratchet is not None:
                #already in the right place
                shape = shape.add(bolt_on_ratchet)

            if not self.combine_with_powered_wheel:
                shape = shape.add(self.powered_wheel.get_assembled().translate((0, 0, self.wheel_thick)))

        if self.pinion.lantern:
            shape = shape.add(self.pinion.get_lantern_cap(self.end_cap_thick).translate((0,0, self.wheel_thick + self.pinion_thick)))
            shape = shape.add(self.pinion.get_lantern_inner_fixing(base_thick=self.wheel_thick, pinion_height=self.pinion_thick, top_thick=self.end_cap_thick, for_printing=False))

        return shape



    def get_standalone_pinion(self):
        '''
        For an escape wheel out the front of the clock there's just a pinion on the arbour inside the clock

        '''

        pinion = self.pinion.get3D(thick=self.pinion_thick, holeD=self.hole_d).translate((0, 0, self.end_cap_thick))
        cap = cq.Workplane("XY").circle(self.pinion.get_max_radius()).circle(self.hole_d / 2).extrude(self.end_cap_thick)
        pinion = pinion.add(cap).add(cap.translate((0, 0, self.end_cap_thick + self.pinion_thick)))

        return pinion

    def get_extras(self, rear_side_extension = 0, front_side_extension = 0, key_length = 0, front_plate_thick=0, ratchet_key_extra_length=0):
        '''
        are there any extra bits taht need printing for this arbour?
        returns {'name': shape,}
        '''
        extras = {}
        #messy logic needs tidying up with different powered wheels and ratchets more unified
        traditional_ratchet = False
        if self.get_type() == ArborType.POWERED_WHEEL and self.get_extra_ratchet() is not None:
            extras['ratchet']= self.get_extra_ratchet()

        if self.get_type() in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL] and self.pinion.lantern:
            extras["lantern_pinion_cap"] = self.pinion.get_lantern_cap(cap_thick=self.end_cap_thick)
            extras["lantern_pinion_fixing"] = self.pinion.get_lantern_inner_fixing(base_thick=self.wheel_thick, pinion_height=self.pinion_thick, top_thick=self.end_cap_thick, hole_d=self.hole_d)

        if self.get_type() == ArborType.POWERED_WHEEL and self.weight_driven and self.powered_wheel.traditional_ratchet:
            traditional_ratchet = True
            extras['ratchet_gear'] = self.powered_wheel.get_ratchet_wheel_for_cord()

        if self.get_type() == ArborType.POWERED_WHEEL and self.powered_wheel.type == PowerType.SPRING_BARREL:
            extras['spring_arbor']=self.powered_wheel.get_arbor(extra_at_back=rear_side_extension, extra_in_front=front_side_extension,
                                                                key_length=key_length, ratchet_key_extra_length=ratchet_key_extra_length)
            extras['lid'] = self.powered_wheel.get_lid()
            extras['ratchet_gear'] = self.powered_wheel.get_ratchet_gear_for_arbor()
            extras['front_washer'] = self.powered_wheel.get_front_bearing_standoff_washer()
            traditional_ratchet = True

        if traditional_ratchet:
            extras['ratchet_pawl'] = self.powered_wheel.ratchet.get_pawl()
            extras['ratchet_click'] = self.powered_wheel.ratchet.get_click()
            extras['ratchet_pawl_supporter'] = self.powered_wheel.ratchet.get_little_plate_for_pawl()

        return extras
    def get_extra_ratchet(self, for_printing=True):
        '''
        returns None if the ratchet is fully embedded in teh wheel
        otherwise returns a shape that can either be adapted to be bolted, or combined with the wheel

        Note: shape is returned translated into the position relative to the chain wheel

        '''
        if not self.use_ratchet or self.powered_wheel.traditional_ratchet:
            return None

        if self.ratchet.thick <= 0:
            return None

        ratchet_wheel = self.ratchet.getOuterWheel()

        #add holes
        for hole_pos in self.bolt_positions:
            cutter = self.ratchet_screws.get_cutter(with_bridging=False).rotate((0, 0, 0), (0, 1, 0), 180).translate((hole_pos[0], hole_pos[1], self.ratchet.thick))
            # return cutter
            ratchet_wheel = ratchet_wheel.cut(cutter)

        ratchet_wheel = ratchet_wheel.translate((0, 0, self.wheel_thick))

        # if not for_printing:
        #     ratchetWheel = ratchetWheel.rotate((0,0,0),(1,0,0),180)

        return ratchet_wheel

    def print_screw_length(self):
        if self.get_extra_ratchet() is not None:
            length = self.wheel_thick + self.ratchet.thick
            if not self.ratchet_screws.countersunk:
                length -= self.ratchet_screws.get_head_height()
            print("Ratchet needs {} screws of length {}mm".format(self.ratchet_screws.get_string(), length))

    def get_powered_wheel(self, for_printing=True, rear_side_extension=0, arbour_extension_max_radius=0):
        '''
        The Arbor class no longer knows about the placement of the arbors in teh plates, so if we want to generate a complete wheel rear_side_extension and arbour_extension_max_r must be provided
        This will gracefully fall back to still producing a chain wheel if they're not
        '''
        style = self.style
        if PowerType.is_weight(self.powered_wheel.type):

            if self.use_ratchet:
                inner_radius_for_style=self.ratchet.get_max_radius()
            else:
                inner_radius_for_style = self.powered_wheel.diameter * 1.1 / 2
        else:
            inner_radius_for_style = self.powered_wheel.get_outer_diameter()
            #TODO
            style = None
        #the "pinion" is used for the side of the powered wheel
        #TODO review logic if I ever get chain at back working again
        gear_wheel = self.wheel.get3D(holeD=self.hole_d, thick=self.wheel_thick, style=style, innerRadiusForStyle=inner_radius_for_style,
                                      clockwise_from_pinion_side=self.clockwise_from_pinion_side)

        if self.combine_with_powered_wheel:
            z_offset = self.wheel_thick

            if self.powered_wheel.type == PowerType.SPRING_BARREL:

                # cut a hole in teh gear wheel so the style in the back of the barrel works
                gear_wheel = gear_wheel.faces(">Z").workplane().circle(self.powered_wheel.radius_for_style + 1).cutThruAll()

                z_offset = 0
                barrel_r = self.powered_wheel.get_outer_diameter()/2
                wheel_r = self.wheel.get_min_radius()

                if barrel_r < wheel_r - 10:
                    gear_wheel = Gear.cutStyle(gear_wheel, wheel_r, barrel_r, self.style)
                
                
            gear_wheel = gear_wheel.union(self.powered_wheel.get_assembled().translate((0, 0, z_offset)))

        if rear_side_extension > 0 and not self.combine_with_powered_wheel:
            #rear side extension - chunky bit out the back to help provide stability on the threaded rod
            #limit to r of 1cm
            max_r = 10
            if self.loose_on_rod:
                max_r = 12.5

            extension_r = min(max_r, arbour_extension_max_radius)


            if len(self.bolt_positions) > 0:
                boltR = np.linalg.norm(self.bolt_positions[0])
                #make sure it's possible to screw the ratchet or wheel on
                if extension_r > boltR - self.ratchet_screws.get_nut_containing_diameter()/2:
                    extension_r = boltR - self.ratchet_screws.get_nut_containing_diameter() / 2

            bearing_standoff_height = LAYER_THICK * 2
            bearing_standoff_r = get_bearing_info(self.arbor_d).inner_safe_d / 2
            if bearing_standoff_r > extension_r:
                bearing_standoff_r = extension_r

            if extension_r < self.arbor_d:
                #this *shouldn't* be possible anymore as the module size of teh chain wheel is recalcualted to ensure there is space
                raise ValueError("Wheel next to powered wheel is too large for powered wheel arbour extension to fit. Try making module reduction smaller for gear generation. extension_r:{}".format(extension_r))
            extended_arbour = cq.Workplane("XY").circle(extension_r).extrude(rear_side_extension - bearing_standoff_height).faces(">Z").workplane().circle(bearing_standoff_r).extrude(bearing_standoff_height)
            #add hole for rod!
            extended_arbour = extended_arbour.faces(">Z").circle(self.arbor_d / 2).cutThruAll()

            gear_wheel = gear_wheel.add(extended_arbour.rotate((0,0,0),(1,0,0),180))

        if self.get_extra_ratchet() is not None or not self.use_ratchet and self.weight_driven:
            #need screwholes to attach the rest of the ratchet or the chain wheel (the boltPositions have alreayd been adjusted accordingly)
            # either to hold on the outer part of the ratchet or the powered wheel itself
            for hole_pos in self.bolt_positions:
                cutter = cq.Workplane("XY").moveTo(hole_pos[0], hole_pos[1]).circle(self.ratchet_screws.metric_thread / 2).extrude(self.wheel_thick)
                gear_wheel = gear_wheel.cut(cutter)
                if self.wheel_thick - self.ratchet_screws.get_nut_height(half=True) > 1:
                    cutter = self.ratchet_screws.get_nut_cutter(with_bridging=False, half=True).translate(hole_pos)
                # else screwing straight into the wheel seemed surprisingly secure, and if the wheel is that thin it probably isn't holding much weight anyway
                gear_wheel = gear_wheel.cut(cutter)
        if self.use_ratchet and self.powered_wheel.traditional_ratchet:
            for hole_pos in self.bolt_positions:
                gear_wheel = gear_wheel.cut(self.ratchet_screws.get_cutter(for_tap_die=True).translate(hole_pos))


        if for_printing and not self.combine_with_powered_wheel:
            #put flat side down
            gear_wheel = gear_wheel.rotate((0,0,0),(1,0,0),180).translate((0,0, self.wheel_thick))

        if self.loose_on_rod:
            #cut a hole through the arbour extension too (until the arbour extension takes this into account, but it doesn't since this currently only applies to the cord wheel)
            cutter = cq.Workplane("XY").circle(self.hole_d / 2).extrude(10000).translate((0, 0, -5000))
            gear_wheel = gear_wheel.cut(cutter)
            print("Need steel tube of length {}mm".format(self.wheel_thick + rear_side_extension))

        if not self.pinion_at_front:
            #chain is at the back
            #I'm losing track of how many times we flip this now
            gear_wheel = gear_wheel.rotate((0,0,0),(1,0,0),180).translate((0,0,self.get_total_thickness()))

        return gear_wheel

class MotionWorks:

    #enough for two half height nuts, a washer and a slightly compressed spring washer to be contained in the base of the cannon pinion
    STANDARD_INSET_DEPTH = 4.5

    def __init__(self, arbor_d=3, thick=3, pinion_thick=-1, module=1, minute_hand_thick=3, extra_height=0,
                 style=GearStyle.ARCS, compensate_loose_arbour=True, snail=None, strike_trigger=None, strike_hour_angle_deg=45, compact=False, bearing=None, inset_at_base=0,
                 moon_complication=None, cannon_pinion_friction_ring=False, lone_pinion_inset_at_base=0):
        '''

        inset_at_base - if >0 (usually going to want just less than TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT) then inset the bearing or create a space large enoguh
        for the two locked nuts, washer and spring washer. this way the motion works can be closer to the clock plate

        lone_pinion_inset_at_base - for centred second hands there's an extra pinion used as a time setting knob, do the inset at base thing for this instead of the main cannon pinion
        primarily because it can struggle to fit behind the dial

        thick is thickness of the wheels
        pinionthick is double thick by default, can be overriden
        minuteHolderTotalHeight - extra height above the minimum

        the the minute wheel is fixed to the arbour, and the motion works must only be friction-connected to the minute arbour.

        if bearing is not none, it expects a BearingInfo object. This will provide space at the top and bottom of the cannon pinion for such a bearing
        in order for a seconds hand to pass through the centre of the motion works.

        NOTE hour hand is very loose when motion works arbour is mounted above the cannon pinion.
         compensateLooseArbour attempts to compensate for this

        If snail and strikeTrigger are provided, this motion works will be for a striking clock

        The modern clock:
        'The meshing of the minute wheel and cannon pinion should be as deep as is consistent with perfect freedom, as should also that of the hour wheel
         and minute pinion in order to prevent the hour hand from having too much shake, as the minute wheel and pinion are loose on the stud and the hour
         wheel is loose on the cannon, so that a shallow depthing here will give considerable back lash, which is especially noticeable when winding.'


         Note - bits of this get overriden by the plates (for the centred seconds hands). this is a bit of a hack

         moon_complication - the hour wheel will drive the moon phase complication and needs a pinion at the base of the holder


        '''
        self.arbor_d = arbor_d
        self.hole_d= arbor_d + 0.4
        #thickness of gears
        self.thick = thick
        self.pinion_thick = pinion_thick
        if self.pinion_thick < 0:
            self.pinion_thick = self.thick * 2
        self.style=style
        self.compact = compact

        #experimental, have an extra round bit at the bottom that can have a small amount of friction applied to remove the slack on centred-seconds-hands clocks
        self.cannon_pinion_friction_ring = cannon_pinion_friction_ring
        self.friction_ring_thick = self.thick * 2
        self.friction_ring_wall_thick=2

        #hole in the bottom so the bearing or double nut + split washer can be inside the cannon pinion
        self.inset_at_base = inset_at_base
        self.lone_pinion_inset_at_base = lone_pinion_inset_at_base

        self.moon_complication = moon_complication

        self.strike_trigger=strike_trigger
        #angle the hour strike should be at
        self.strike_hour_angle_deg=strike_hour_angle_deg
        self.snail=snail

        self.pinion_cap_thick = thick / 2
        if self.compact:
            self.pinion_cap_thick = 0

        self.module = module
        self.compensate_loose_arbour = compensate_loose_arbour

        self.bearing = bearing

        self.inset_at_base_r = (get_washer_diameter(self.arbor_d) + 1) / 2

        self.cannon_pinion_pinion_thick = self.pinion_thick
        self.calculate_size()



        self.wallThick = 1.5
        #for centred seconds hands, the bit you can twist to set the time
        self.knob_thick = 1.5


        # self.pairs = [WheelPinionPair(36, 12, module), WheelPinionPair(40, 10, secondModule)]


        #minuteHandHolderSize=5,
        #length of the edge of the square that holds the minute hand
        #(if minuteHandHolderIsSquare is false, then it's round and this is a diameter)
        self.minute_hand_holder_size= self.arbor_d + 2

        #if no bearing this has no second hand in the centre, so is a "normal" motion works

        self.minute_hand_holder_is_square = True


        self.minute_hand_holder_d = self.minute_hand_holder_size * math.sqrt(2) + 0.5

        if self.bearing is not None:
            self.minute_hand_holder_d = self.bearing.outer_d + 4
            self.inset_at_base_r = self.bearing.outer_d / 2
            self.hole_d = self.bearing.outer_safe_d
            self.minute_hand_holder_size = self.bearing.outer_d + 3
            # if there is a bearing then there's a rod through the centre for the second hand and the minute hand is friction fit like the hour hand
            self.minute_hand_holder_is_square = False
        #assume bearing == centred second hand.
        self.centred_second_hand = self.bearing is not None

        # print("minute hand holder D: {}".format(self.minuteHandHolderD))

        self.distance_between_hands = minute_hand_thick
        self.minute_hand_slot_height = minute_hand_thick
        self.hour_hand_slot_height = minute_hand_thick + self.distance_between_hands

        self.bearing_holder_thick = 0

        self.calc_bearing_holder_thick()
        print("bearingHolderThick", self.bearing_holder_thick)

        #done in calc_bearing_holder_thick
        # self.cannonPinionBaseHeight = self.cannonPinionPinionThick + self.pinionCapThick * 2 + self.bearingHolderThick
        self.space = 0.5
        #old size of space so I can reprint without reprinting the hands (for the non-bearing version)
        self.hour_hand_holder_d = self.minute_hand_holder_d + 1 + self.wallThick * 2

        if self.bearing is not None:
            #remove the backwards compatible bodge, we don't want this any bigger than it needs to be
            self.hour_hand_holder_d -= 1

        if extra_height < self.thick*2:
            #to ensure hour hand can't hit the top of the arbour
            extra_height = self.thick*2

        #thick for thickness of hour holder wheel
        self.cannon_pinion_total_height_above_base = extra_height + self.minute_hand_slot_height + self.space + self.hour_hand_slot_height + self.thick# + self.cannonPinionBaseHeight


    def get_hour_wheel_teeth(self):
        return self.pairs[1].wheel.teeth

    def get_cannon_pinion_teeth(self):
        return self.pairs[0].pinion.teeth

    def get_cannon_pinion_max_r(self):
        return self.pairs[0].pinion.get_max_radius()

    def get_cannon_pinion_total_height(self):
        return self.cannon_pinion_total_height_above_base + self.cannon_pinion_base_height

    def get_cannon_pinion_effective_height(self):
        #because the inset at the base means the locking nuts and spring washer sit inside the motion works
        return self.get_cannon_pinion_total_height() - self.inset_at_base

    def get_top_of_hour_holder_wheel_z(self):
        '''
        get distance in z from bottom of cannon pinion to top of the wheel on the hour holder
        '''
        return self.cannon_pinion_base_height

    def calc_bearing_holder_thick(self):

        if self.bearing is not None:
            if self.bearing.outer_d > self.pairs[0].pinion.get_min_radius()*2 - 1:
                #this bearing won't fit inside the cannon pinion
                self.bearing_holder_thick = self.bearing.height
                if self.compact:
                    self.bearing_holder_thick += 1
            else:
                self.bearing_holder_thick = 0
            #we're big enough with the bearings, try to reduce size where we can
            self.wallThick = 1.2
        else:
            self.bearing_holder_thick = 0
        self.cannon_pinion_base_height = self.cannon_pinion_pinion_thick + self.pinion_cap_thick * 2 + self.bearing_holder_thick

    def calculate_size(self, arbor_distance=-1):
        '''
        If no arbour distance, use module size to calculate arbour distance, and set it.
        If arbour distance provided, use it to calculate module size and set that
        changes properties of this object
        '''

        #experiment, if true aim to keep module size aproximately same as self.module by adjusting number of teeth
        aim_for_module_size = True

        wheel0_teeth = 36
        pinion0_teeth = 12
        wheel1_teeth = 40
        pinion1_teeth = 10

        # pinching ratios from The Modern Clock
        # adjust the module so the diameters work properly
        if arbor_distance < 0:
            self.arbor_distance = self.module * (wheel0_teeth + pinion0_teeth) / 2
        else:
            if aim_for_module_size:
                pinion_min = 10
                pinion_max = 30
                wheel_min = 20
                wheel_max = 200

                options = []

                for p0 in range(pinion_min, pinion_max):
                    print("\r{:.1f}% calculating motion works gears".format(100*(p0 - pinion_min)/(pinion_max-pinion_min)), end='')
                    for w0 in range(wheel_min, wheel_max):
                        for p1 in range(pinion_min, pinion_max):
                            for w1 in range(wheel_min, wheel_max):

                                ratio = (w1/p1) * (w0/p0)#1/((p0/w0)*(p1/w1))

                                if (w1 * w0) % (p1 * p0) != 0:
                                    continue
                                if ratio != 12:
                                    continue




                                module0 = arbor_distance / ((w0 + p0) / 2)
                                module1 = arbor_distance / ((w1 + p1) / 2)

                                min_cannon_pinion_r = 0

                                if self.bearing is not None:
                                    min_cannon_pinion_r = self.bearing.outer_d / 2
                                if self.inset_at_base > 0:
                                    min_cannon_pinion_r = self.inset_at_base_r

                                #v.slow
                                potential_pair = WheelPinionPair(w0, p0, module0, looseArbours=self.compensate_loose_arbour)
                                if min_cannon_pinion_r > potential_pair.pinion.get_min_radius() - 0.9:
                                    #not enough space to slot in the bearing
                                    # print("pinion_min_r",pinion_min_r)
                                    continue

                                option = {'ratio':ratio, 'module0': module0, 'module1':module1, 'teeth':[w0,p0,w1,p1]}
                                options.append(option)

                #one with the modules closest to requested
                options.sort(key=lambda x: abs(x["module0"] - x["module1"])*0 + abs(x["module0"] - self.module) + abs(x["module1"] - self.module))
                # options.sort(key=lambda x:abs((x["module0"] + x["module1"])/2 - self.module))

                if len(options) == 0:
                    raise ValueError("Unable to calculate gears for motion works")
                self.module = options[0]["module0"]
                self.arbor_distance = arbor_distance
                wheel0_teeth, pinion0_teeth, wheel1_teeth, pinion1_teeth = options[0]["teeth"]

                # if self.bearing is not None and pinion0_teeth < pinion1_teeth:
                #     #try and ensure enough space for the bearing
                #     old0 = pinion0_teeth
                #     pinion0_teeth = pinion1_teeth
                #     pinion1_teeth = old0


            else:
                self.module = arbor_distance / ((wheel0_teeth + pinion0_teeth) / 2)
                self.arbor_distance = arbor_distance
        secondModule = 2 * self.arbor_distance / (wheel1_teeth + pinion1_teeth)
        print("Motion works module0: {}, module1: {}. wheel0_teeth {}, pinion0_teeth {}, wheel1_teeth {}, pinion1_teeth {}".format(self.module, secondModule,wheel0_teeth, pinion0_teeth, wheel1_teeth, pinion1_teeth))
        self.pairs = [WheelPinionPair(wheel0_teeth, pinion0_teeth, self.module, looseArbours=self.compensate_loose_arbour), WheelPinionPair(wheel1_teeth, pinion1_teeth, secondModule, looseArbours=self.compensate_loose_arbour)]


        self.calc_bearing_holder_thick()

        self.friction_ring_r = self.pairs[0].pinion.get_max_radius()


    def get_assembled(self, motionWorksRelativePos=None,minuteAngle=10):

        parts = self.get_parts_in_situ(motionWorksRelativePos, minuteAngle)

        model = cq.Workplane("XY")

        for part in parts:
            model = model.add(parts[part])

        return model

    def get_parts_in_situ(self, motionWorksRelativePos=None,minuteAngle=10):
        if motionWorksRelativePos is None:
            motionWorksRelativePos = [0, -self.get_arbor_distance()]
        parts = {}
        parts["cannon_pinion"] = self.get_cannon_pinion().rotate((0, 0, 0), (0, 0, 1), minuteAngle)
        parts["hour_holder"] = self.getHourHolder().translate((0, 0, self.get_cannon_pinion_base_thick()))
        parts["arbor"] = self.get_motion_arbour_shape().translate((motionWorksRelativePos[0], motionWorksRelativePos[1], (self.get_cannon_pinion_base_thick() - self.bearing_holder_thick) / 2 + self.bearing_holder_thick - self.thick / 2))

        if self.centred_second_hand:
            # relative_pos = npToSet(np.multiply(motionWorksRelativePos, 2))
            #is this general purpose?
            relative_pos = np_to_set(np.add(motionWorksRelativePos, (-motionWorksRelativePos[0], motionWorksRelativePos[1])))
            parts["time_setter_pinion"] = self.get_cannon_pinion_pinion(standalone=True).translate(relative_pos)

        return parts

    def get_hour_hand_hole_d(self):
        '''
        get the size of the hole needed for the hand to slot onto the hour hand holder
        '''
        return self.hour_hand_holder_d

    def get_minute_hand_square_size(self):
        '''
        Get the size of the square needed for the hand to slot onto the cannon pinion
        '''
        return self.minute_hand_holder_size + 0.2

    def get_arbor_distance(self):
        return self.arbor_distance

    def get_hour_holder_max_radius(self):
        return self.pairs[1].wheel.get_max_radius()

    def get_arbour_max_radius(self):
        return self.pairs[0].wheel.get_max_radius()

    def get_hand_holder_height(self):
        '''
        get distance from base of the cannon pinion to the beginning of the hand holders (base of hour hand)
        '''
        return self.get_cannon_pinion_total_height() - (self.minute_hand_slot_height + self.space + self.hour_hand_slot_height)

    def get_wheels_thick(self):
        '''
        get maximum thickness from bottom of cannon pinion to the front of the motion works arbor
        '''

        return self.cannon_pinion_pinion_thick + self.pinion_thick + self.pinion_cap_thick*2

    def get_cannon_pinion_base_thick(self):
        '''
        get the thickness of the pinion + caps at the bottom of the cannon pinion ( and bearing holder)

        '''

        thick = self.pinion_cap_thick * 2 + self.cannon_pinion_pinion_thick + self.bearing_holder_thick


        return thick

    def get_cannon_pinion_pinion_thick(self):
        return self.get_cannon_pinion_base_thick() + self.knob_thick

    def get_cannon_pinion_pinion(self, with_snail=False, standalone=False, for_printing=True):
        '''
        For the centred seconds hands I'm driving the motion works arbour from the minute arbour. To keep the gearing correct, use the same pinion as the cannon pinion!
        if standalone, this is for the centred seconds hands where we're driving the motion works arbour from the minute wheel
        '''

        pinion_max_r = self.pairs[0].pinion.get_max_radius()

        base = cq.Workplane("XY")

        if self.strike_trigger is not None:
            base = self.strike_trigger.get2D().extrude(self.pinion_cap_thick).rotate((0, 0, 0), (0, 0, 1), self.strike_hour_angle_deg).faces(">Z").workplane()

        if self.pinion_cap_thick > 0:
            base = base.circle(pinion_max_r).extrude(self.pinion_cap_thick)

        base = base.union(self.pairs[0].pinion.get2D().extrude(self.cannon_pinion_pinion_thick).translate((0, 0, self.pinion_cap_thick)))

        if self.pinion_cap_thick > 0:
            base = base.union(cq.Workplane("XY").circle(pinion_max_r).extrude(self.pinion_cap_thick).translate((0, 0, self.pinion_cap_thick + self.cannon_pinion_pinion_thick)))

        pinion = base

        if standalone:

            #add hand-grippy thing to allow setting the time easily
            inner_r = pinion_max_r
            outer_r = inner_r*1.5

            knob = get_smooth_knob_2d(inner_r, outer_r, knobs=6).extrude(self.knob_thick)

            pinion = pinion.union(knob.translate((0, 0, self.pinion_cap_thick + self.cannon_pinion_pinion_thick)))

            # cut hole to slot onto arbour
            pinion = pinion.cut(cq.Workplane("XY").circle((self.arbor_d + LOOSE_FIT_ON_ROD) / 2).extrude(10000))

            if self.lone_pinion_inset_at_base > 0:
                #hack, copy-pasted from initial setting of inset_at_base_r before that was hijacked for the bearing slot
                inner_r = (get_washer_diameter(self.arbor_d) + 1) / 2
                pinion = pinion.cut(cq.Workplane("XY").circle(inner_r).extrude(self.lone_pinion_inset_at_base))



        return pinion

    def get_cannon_pinion_pinion_stl_modifier(self):

        return self.pairs[0].pinion.get_STL_modifier_shape(thick=self.cannon_pinion_pinion_thick, offset_z=self.pinion_cap_thick)


    def get_cannon_pinion(self, hand_holder_radius_adjustment=1.0):

        pinion_max_r = self.pairs[0].pinion.get_max_radius()

        # base = cq.Workplane("XY")
        #
        #
        # if self.strikeTrigger is not None:
        #     base = self.strikeTrigger.get2D().extrude(self.pinionCapThick).rotate((0,0,0),(0,0,1),self.strikeHourAngleDeg).faces(">Z").workplane()
        #
        # if self.pinionCapThick > 0:
        #     base = base.circle(pinion_max_r).extrude(self.pinionCapThick)
        #
        # base = base.union(self.pairs[0].pinion.get2D().extrude(self.cannonPinionPinionThick).translate((0, 0, self.pinionCapThick)))
        #
        #
        #
        #
        #
        # if self.pinionCapThick > 0:
        #     base = base.union(cq.Workplane("XY").circle(self.pairs[0].pinion.getMaxRadius()).extrude(self.pinionCapThick).translate((0,0,self.pinionCapThick+self.cannonPinionPinionThick)))

        pinion = self.get_cannon_pinion_pinion(with_snail=True)

        if self.bearing is not None and self.bearing_holder_thick > 0:
            # extend out the bottom for space for a slot on the bottom
            pinion = pinion.translate((0, 0, self.bearing_holder_thick))
            pinion = pinion.union(cq.Workplane("XY").circle(pinion_max_r).extrude(self.bearing_holder_thick))
            if self.cannon_pinion_friction_ring:
                raise ValueError("TODO calculate friction_ring_r for this case")
        elif self.cannon_pinion_friction_ring and self.bearing is not None:
            #need a round bit at the base, but there isn't one from the bearing
            #note this isn't taken into account for geometry deliberately - it should slot over any nuts on the rod
            pinion = pinion.faces("<Z").workplane().circle(self.friction_ring_r).circle(self.bearing.outer_d/2).extrude(self.friction_ring_thick)
            #cut a cone in the bottom to make it easier to slot in the bearing
            #not using wall thick as intended because I want this to be easier to print with more in contact with the plate
            pinion = pinion.cut(cq.Solid.makeCone(radius2=self.bearing.outer_d/2, radius1=self.bearing.outer_d/2 + self.friction_ring_wall_thick, height=self.friction_ring_thick).translate((0,0,-self.friction_ring_thick)))

        # has an arm to hold the minute hand
        pinion = pinion.union(cq.Workplane("XY").circle(self.minute_hand_holder_d / 2).extrude(self.cannon_pinion_total_height_above_base - self.minute_hand_slot_height).translate((0, 0, self.cannon_pinion_base_height)))


        if self.minute_hand_holder_is_square:
            pinion = pinion.union(cq.Workplane("XY").rect(self.minute_hand_holder_size, self.minute_hand_holder_size).extrude(self.minute_hand_slot_height).translate((0, 0, self.get_cannon_pinion_total_height() - self.minute_hand_slot_height)))
        else:

            holder_r = self.minute_hand_holder_size / 2
            # minute holder is -0.2 and is pretty snug, but this needs to be really snug
            # -0.1 almost works but is still a tiny tiny bit loose (with amazon blue PETG, wonder if that makes a difference?)
            # NEW IDEA - keep the tapered shape, but make it more subtle and also keep the new hard stop at the end
            #INFO - HANDS ADD 0.2 TO THIS for the hole in the hand
            holderR_base = (self.minute_hand_holder_size / 2 + 0.05) * hand_holder_radius_adjustment
            holderR_top = (self.minute_hand_holder_size / 2 - 0.15) * hand_holder_radius_adjustment

            circle = cq.Workplane("XY").circle(holder_r)
            holder = cq.Workplane("XZ").lineTo(holderR_base, 0).lineTo(holderR_top, self.minute_hand_slot_height).lineTo(0, self.minute_hand_slot_height).close().sweep(circle)#.translate((0, 0, self.thick))
            holder = holder.translate((0, 0, self.get_cannon_pinion_total_height() - self.minute_hand_slot_height))

            pinion = pinion.union(holder)

        pinion = pinion.cut(cq.Workplane("XY").circle(self.hole_d / 2).extrude(self.get_cannon_pinion_total_height()))


        if self.bearing is not None:
            #slot for bearing on top
            pinion = pinion.cut(cq.Workplane("XY").circle(self.bearing.outer_d / 2).extrude(self.bearing.height).translate((0, 0, self.get_cannon_pinion_total_height() - self.bearing.height)))


            pinion = pinion.cut(get_hole_with_hole(innerD=self.hole_d, outerD=self.bearing.outer_d, deep=self.bearing.height + self.inset_at_base))

        elif self.inset_at_base > 0:
            # cut out space for the nuts/bearing to go further into the cannon pinion, so it can be closer to the front plate
            # pinion = pinion.cut(cq.Workplane("XY").circle(self.inset_at_base_r).extrude(self.inset_at_base))
            pinion = pinion.cut(get_hole_with_hole(innerD=self.hole_d, outerD=self.inset_at_base_r * 2, deep=self.inset_at_base))

        return pinion

    def get_motion_arbour(self):
        # mini arbour that sits between the cannon pinion and the hour wheel
        #this is an actual Arbour object
        wheel = self.pairs[0].wheel
        pinion = self.pairs[1].pinion

        #add pinioncap thick so that both wheels are roughly centred on both pinion (look at the assembled preview)
        return Arbor(wheel=wheel, pinion=pinion, arbor_d=self.arbor_d + LOOSE_FIT_ON_ROD_MOTION_WORKS, wheel_thick=self.thick, pinion_thick=self.pinion_thick + self.pinion_cap_thick, end_cap_thick=self.pinion_cap_thick, style=self.style, clockwise_from_pinion_side=False)

    def get_motion_arbout_pinion_stl_modifier(self):
        return self.pairs[1].pinion.get_STL_modifier_shape(thick=self.pinion_thick + self.pinion_cap_thick, offset_z=self.thick)

    def get_motion_arbour_shape(self):
        #mini arbour that sits between the cannon pinion and the hour wheel
        return self.get_motion_arbour().get_shape()

    def get_widest_radius(self):
        '''
        a hole in the dial must be at least this wide (plus some more for working in the real world)
        bottomR for the hand holder
        '''

        # fiddled the numbers so that fill isn't required to print
        return self.hour_hand_holder_d / 2 + 0.7

    def getHourHolder(self):
        #the final wheel and arm that friction holds the hour hand
        #this used to be excessively tapered, but now a lightly tapered friction fit slot.
        style=self.style
        # if self.snail is not None:
        #     style = None

        #fiddled the numbers so that fill isn't required to print
        # bottomR = self.hourHandHolderD / 2 + 0.7
        bottomR = self.get_widest_radius()

        bottom_r_for_style = bottomR
        if self.moon_complication is not None:
            bottom_r_for_style = self.moon_complication.get_pinion_for_motion_works_max_radius()

        #minute holder is -0.2 and is pretty snug, but this needs to be really snug
        #-0.1 almost works but is still a tiny tiny bit loose (with amazon blue PETG, wonder if that makes a difference?)
        # NEW IDEA - keep the tapered shape, but make it more subtle and also keep the new hard stop at the end
        holderR_base = self.hour_hand_holder_d / 2 + 0.1
        holderR_top = self.hour_hand_holder_d / 2 - 0.2

        hour = self.pairs[1].wheel.get3D(holeD=self.hole_d, thick=self.thick, style=style, innerRadiusForStyle=bottom_r_for_style, clockwise_from_pinion_side=True)

        if self.snail is not None:
            hour = hour.union(self.snail.get3D(self.thick))



        top_z = self.get_cannon_pinion_total_height() - self.space - self.minute_hand_slot_height - self.cannon_pinion_base_height

        # hour = hour.faces(">Z").workplane().circle(self.hourHandHolderD/2).extrude(height)

        handHolderStartZ = top_z - self.hour_hand_slot_height

        if handHolderStartZ < 0.0001:
            #because CQ won't let you make shapes of zero height
            handHolderStartZ = 0.0001

        holeR = self.minute_hand_holder_d / 2 + self.space / 2

        # return hour
        circle = cq.Workplane("XY").circle(bottomR)
        shape = cq.Workplane("XZ").moveTo(bottomR,self.thick).lineTo(bottomR,handHolderStartZ).lineTo(holderR_base,handHolderStartZ).lineTo(holderR_top,top_z).lineTo(holeR,top_z).lineTo(holeR,self.thick).close().sweep(circle)

        hour = hour.add(shape)

        if self.moon_complication is not None:
            # experiment, cut out a chunk
            hour = hour.cut(cq.Workplane("XY").circle(bottom_r_for_style).extrude(self.moon_complication.hour_hand_pinion_thick).translate((0, 0, self.thick)))
            hour = hour.union(self.moon_complication.get_pinion_for_motion_works_shape().translate((0, 0, self.thick)))

        hole = cq.Workplane("XY").circle(holeR).extrude(self.get_cannon_pinion_total_height())
        hour = hour.cut(hole)

        #seems like we can't cut through all when we've added shapes? I'm sure this has worked elsewhere!
        # hour = hour.faces(">Z").workplane().circle(self.minuteHandHolderD/2 + self.space/2).cutThruAll()



        return hour

    def output_STLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_motion_cannon_pinion.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_cannon_pinion(), out)

        out = os.path.join(path, "{}_motion_cannon_pinion_x1.015.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_cannon_pinion(hand_holder_radius_adjustment=1.015), out)

        out = os.path.join(path, "{}_motion_arbour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_motion_arbour_shape(), out)

        out = os.path.join(path, "{}_motion_arbour_pinion_modifier.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_motion_arbour().get_STL_modifier_pinion_shape(), out)

        #only needed for prototype with centred seconds hand
        out = os.path.join(path, "{}_motion_cannon_pinion_pinion_standalone.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_cannon_pinion_pinion(standalone=True), out)

        out = os.path.join(path, "{}_motion_cannon_pinion_modifier.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_cannon_pinion_pinion_stl_modifier(), out)

        out = os.path.join(path, "{}_motion_arbour_pinion_modifier.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_motion_arbout_pinion_stl_modifier(), out)

        out = os.path.join(path, "{}_motion_hour_holder.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHourHolder(), out)
