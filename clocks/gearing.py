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



class Gear:


    @staticmethod
    def cutStyle(gear, outerRadius, innerRadius = -1, style=None, clockwise_from_pinion_side=True):
        '''
        Could still do with a little more tidying up, outerRadius should be a few mm shy of the edge of teh gear to give a solid rim,
        but innerRadius should be at the edge of whatever can't be cut into

        I keep changing my mind whether or not to give the cutter the full size of the gear or just the area to cut.

        clockwise - assume this wheel is turning clockwise from the perspective of the side with the pinion
        '''
        #lots of old designs used a literal string "HAC"
        if style == GearStyle.ARCS or style == GearStyle.ARCS.value:
            if innerRadius < outerRadius*0.5:
                innerRadius=outerRadius*0.5
            return Gear.cutHACStyle(gear, armThick=outerRadius*0.1, outer_r=outerRadius - 2, inner_r=innerRadius)
        if style == GearStyle.CIRCLES:
            if innerRadius < 0:
                innerRadius = 3
            return Gear.cutCirclesStyle(gear,outerRadius=outerRadius, innerRadius=innerRadius, hollow=False)
        if style == GearStyle.CIRCLES_HOLLOW:
            return Gear.cutCirclesStyle(gear,outerRadius=outerRadius, innerRadius=innerRadius+2, hollow=True)
        if style == GearStyle.SIMPLE4:
            return Gear.cutSimpleStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2, arms=4)
        if style == GearStyle.SIMPLE5:
            return Gear.cutSimpleStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2, arms=5)
        if style == GearStyle.SPOKES:
            return Gear.cutSpokesStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2)
        if style == GearStyle.STEAMTRAIN:
            return Gear.cutSteamTrainStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2)
        if style == GearStyle.CARTWHEEL:
            return Gear.cutSteamTrainStyle(gear, outerRadius=outerRadius*0.9, innerRadius=innerRadius+2, withWeight=False)
        if style == GearStyle.FLOWER:
            return Gear.cutFlowerStyle2(gear, outerRadius=outerRadius-2.8, innerRadius=innerRadius)
        if style == GearStyle.HONEYCOMB:
            return Gear.cutHoneycombStyle(gear, outerRadius=outerRadius * 0.9, innerRadius=innerRadius + 2)
        if style == GearStyle.HONEYCOMB_SMALL:
            return Gear.cutHoneycombStyle(gear, outerRadius=outerRadius * 0.9, innerRadius=innerRadius + 2, big=False)
        if style == GearStyle.SNOWFLAKE:
            return Gear.cutSnowflakeStyle(gear, outerRadius= outerRadius * 0.9, innerRadius = innerRadius + 2)

        if style == GearStyle.CURVES:
            return Gear.cutCurvesStyle(gear, outerRadius=min(outerRadius*0.9, outerRadius-2.4), innerRadius=max(innerRadius*1.05, innerRadius+1), clockwise=clockwise_from_pinion_side)
        if style == GearStyle.DIAMONDS:
            return Gear.cutDiamondsStyle(gear, outerRadius=min(outerRadius*0.9, outerRadius-2.4), innerRadius=max(innerRadius*1.05, innerRadius+1))
        return gear

    @staticmethod
    def getThinArmThickness(outerRadius, innerRadius):
        arm_thick = max(outerRadius * 0.1, 1.8)  # 1.8 is the size of the honeycomb walls
        # print("arm_thick", arm_thick)
        if arm_thick < 2.7:
            # arms that were slightly bigger ended up with a gap. probably need to ensure we're a multiple of 0.45?
            return 1.75
        if arm_thick < 3:
            return 2.7

        return arm_thick


    @staticmethod
    def cutDiamondsStyle(gear, outerRadius, innerRadius):
        arm_thick = Gear.getThinArmThickness(outerRadius, innerRadius)

        diamonds = 7

        centre_r = (outerRadius + innerRadius)/2

        centre_gap = outerRadius - innerRadius

        if innerRadius/outerRadius > 0.5:
            #better idea - instead of cutting fewer diamonds, why don't I leave in arms that are solid diamond shaped? with space between?
            diamonds = 5

        diamond_width = math.pi*centre_r*2 / diamonds

        cutter_thick = 100

        cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutter_thick)

        for d in range(diamonds):
            diamond_angle = d*math.pi*2/diamonds

            other_shapes_angle = (d+0.5)*math.pi*2/diamonds

            next_diamond_angle = (d+1)*math.pi*2/diamonds

            diamond_wide_angle = diamond_width/centre_r

            left_point = polar(diamond_angle - diamond_wide_angle/2, centre_r)
            right_point = polar(diamond_angle + diamond_wide_angle/2, centre_r)
            top_point = polar(diamond_angle, outerRadius)
            bottom_point = polar(diamond_angle, innerRadius)

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

        arm_thick = Gear.getThinArmThickness(outerRadius, innerRadius)
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



        branchlength = distanceBetweenTwoPoints(midBranch0, midBranch1)/2

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
                branchCentre = averageOfTwoPoints(branchStart, branchEnd)
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
    def cutHoneycombStyle(gear, outerRadius, innerRadius, big=True):
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
    def cutHACStyle(gear, armThick, outer_r, inner_r):
        # vaguely styled after some HAC gears I've got, with nice arcing shapes cut out
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
        while sagitta < gap_size/2 and i <1000:
            #on narrow gaps they can end up just a straight lines!
            arms+=1
            sagitta = get_sagitta(arms)
            i+=1


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
    def cutCirclesStyle(gear, outerRadius, innerRadius = 3, minGap = 2.4, hollow=False):
        '''inspired (shamelessly stolen) by the clock on teh cover of the horological journal dated March 2022'''
        #TODO split out the hollow into its own method, I think it's going to be a little different, especially around calculating positions

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

        cutter_thick = 1000
        cutter = cq.Workplane("XY")

        if hollow:
            cutter = cq.Workplane("XY").circle(outerRadius).circle(innerRadius).extrude(cutter_thick)

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
                angle = bigCircleAngle*circle - bigCircleAngle/4
                pos = polar(angle, innerRadius + ringSize/2)

                if hollow:
                    cutter = cutter.cut(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(bigCircleR+2).circle(bigCircleR).extrude(cutter_thick))
                else:
                    cutter = cutter.add(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(bigCircleR).extrude(cutter_thick))

                if hasSmallCircles:
                    smallCirclePos = polar(angle + bigCircleAngle / 2, innerRadius + ringSize * 0.75)
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



    def __init__(self, isWheel, teeth, module, addendum_factor, addendum_radius_factor, dedendum_factor, toothFactor=math.pi/2, innerRadiusForStyle=-1, is_crown=False):
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

    def getMaxRadius(self):
        '''
        radius that encompasses the outermost parts of the teeth
        '''
        return self.pitch_diameter/2 + self.addendum_factor*self.module

    def getMinRadius(self):
        '''
        you could cut a hole through the gear of this radius without touchign the teeth
        '''
        dedendum_height = self.dedendum_factor * self.module

        return self.pitch_diameter/2 - dedendum_height

    def get3D(self, holeD=0, thick=0, style="HAC", innerRadiusForStyle=-1, clockwise_from_pinion_side=True):
        gear = self.get2D()

        if thick == 0:
            thick = round(self.pitch_diameter*0.05)
        gear = gear.extrude(thick)

        if holeD > 0:
            gear = gear.faces(">Z").workplane().moveTo(0,0).circle(holeD/2).cutThruAll()

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
            gear = Gear.cutStyle(gear, outerRadius=self.pitch_diameter / 2 - rimThick, innerRadius=innerRadiusForStyle, style=style, clockwise_from_pinion_side=clockwise_from_pinion_side)

        return gear

    def getSTLModifierShape(self, thick, offset_z=0, min_inner_r=1.5):
        '''
        return a shape that covers just the teeth to help apply tweaks to the slicing settings
        '''

        inner_r = self.getMinRadius() - 1.8
        if inner_r < min_inner_r:
            inner_r = min_inner_r

        return cq.Workplane("XY").circle(self.getMaxRadius()).circle(inner_r).extrude(thick).translate((0, 0, offset_z))

    def addToWheel(self,wheel, holeD=0, thick=4, front=True, style="HAC", pinionThick=8, capThick=2, clockwise_from_pinion_side=True):
        '''
        Intended to add a pinion (self) to a wheel (provided)
        if front is true ,added onto the top (+ve Z) of the wheel, else to -ve Z. Only really affects the escape wheel
        pinionthicker is a multiplier to thickness of the week for thickness of the pinion
        clockwise_from_pinion_side is purely for cutting a style
        '''

        # pinionThick = thick * pinionthicker

        base = wheel.get3D(thick=thick, holeD=holeD, style=style, innerRadiusForStyle=self.getMaxRadius()+1,clockwise_from_pinion_side = clockwise_from_pinion_side)

        if front:
            #pinion is on top of the wheel
            distance = thick
            topFace = ">Z"
        else:
            distance = -pinionThick
            topFace = "<Z"

        top = self.get3D(thick=pinionThick, holeD=holeD, style=style).translate([0, 0, distance])

        arbour = base.union(top)

        if capThick > 0:
            arbour = arbour.faces(topFace).workplane().moveTo(0,0).circle(self.getMaxRadius()).extrude(capThick)

        # arbour = arbour.faces(topFace).workplane().moveTo(0,0).circle(holeD / 2).cutThruAll()
        arbour = arbour.cut(cq.Workplane("XY").moveTo(0,0).circle(holeD / 2).extrude(1000).translate((0,0,-500)))

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
        # print("addendum Factor", addendumFactor)
        return addendumFactor


class ArbourForPlate:

    def __init__(self, arbour, plates, arbour_extension_max_radius, pendulum_sticks_out=0, pendulum_at_front=True, bearing=None, escapement_on_front=False,
                back_from_wall=0, endshake = 1, pendulum_fixing = PendulumFixing.DIRECT_ARBOUR, bearing_position=None, direct_arbour_d = DIRECT_ARBOUR_D):
        '''
        Given a basic Arbour and a specific plate class do the following:

        Add arbour extensions where needed
        Produce special pinion-only arbours for escapements on front
        produce special extended arbours for escapement anchors which are using the direct arbour fixing


        distance_from_back: how far from the back plate is the bottom of this arbour (the rearSideExtension as was in the old Arbour)
        arbour_extension_max_radius: how much space around the arbour (not the bit with a wheel or pinion) there is, to calculate how thick the arbour extension could be

        Note - there is only one plate type at the moment, but the aim is that this should be applicable to others in the future
        as such, I'm trying not to tie it to the internals of SimpleClockPlates
        '''
        self.arbour = arbour
        self.plates = plates

        self.plate_distance = self.plates.getPlateDistance()
        self.front_plate_thick = self.plates.getPlateThick(back=False)
        self.back_plate_thick = self.plates.getPlateThick(back=True)
        self.standoff_plate_thick = self.plates.getPlateThick(standoff=True)

        self.arbour_extension_max_radius = arbour_extension_max_radius
        self.pendulum_sticks_out = pendulum_sticks_out
        self.pendulum_at_front = pendulum_at_front
        self.back_from_wall = back_from_wall
        self.endshake = endshake
        self.bearing = bearing
        if self.bearing is None:
            self.bearing = getBearingInfo(self.arbour.arbourD)
        #(x,y,z) from the clock plate. z is the base of the arbour, ignoring arbour extensions (this is from the days when the bearings were raised on little pillars, but is still useful for
        #calculating where the arbour should be)
        self.bearing_position = bearing_position
        self.distance_from_back = bearing_position[2]
        self.distance_from_front = (self.plate_distance - self.endshake) - self.arbour.getTotalThickness() - self.distance_from_back

        self.pendulum_fixing = pendulum_fixing
        if self.bearing is None:
            self.bearing = getBearingInfo(3)
        self.escapement_on_front = escapement_on_front

        self.type = self.arbour.getType()

        #for an escapement on the front, how far from the front plate is the anchor?
        self.front_anchor_from_plate = 1 + self.endshake
        #for direct pendulum arbour with esacpement on the front there's a collet to hold it in place for endshape
        self.collet_thick = 6
        self.collet_screws = MachineScrew(2,countersunk=True)
        self.pendulum_holder_thick = 15
        self.pendulum_fixing_extra_space = 0.2
        self.direct_arbour_d = direct_arbour_d

        #distance between back of back plate and front of front plate (plate_distance is the literal plate distance, including endshake)
        self.total_plate_thickness = self.plate_distance + (self.front_plate_thick + self.back_plate_thick)

        # so that we don't have the arbour pressing up against hte bit of the bearing that doesn't move, adding friction
        self.arbour_bearing_standoff_length = LAYER_THICK * 2

    def get_anchor_collet(self, square_side_length):
        '''
        get a collet that fits on the direct arbour anchor to prevent it sliding out and holds the pendulum
        '''

        outer_d = (self.bearing.innerSafeD + self.bearing.bearingOuterD)/2
        height = self.collet_thick - LAYER_THICK*2

        square_size = square_side_length+self.pendulum_fixing_extra_space


        collet = cq.Workplane("XY").circle(outer_d/2).rect(square_size, square_size).extrude(height)
        collet = collet.faces(">Z").workplane().circle(self.bearing.innerSafeD/2).rect(square_size, square_size).extrude(self.collet_thick - height)

        collet = collet.cut(self.collet_screws.getCutter(length=outer_d/2).rotate((0,0,0),(1,0,0),-90).translate((0,-outer_d/2,self.collet_thick/2)))
        collet = collet.cut(self.collet_screws.getNutCutter(half=True).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -square_size / 2, self.collet_thick / 2)))

        return collet

    def get_pendulum_holder_collet(self, square_side_length, cylinder_r):
        '''
        will slot over square bit of anchor arbour and screw in place
        for the direct arbours without suspension spring
        '''
        #to be consistent with the endshake collet
        outer_d = (self.bearing.innerSafeD + self.bearing.bearingOuterD) / 2
        if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS:
            outer_d = cylinder_r*4#DIRECT_ARBOUR_D*2

        square_size = square_side_length + self.pendulum_fixing_extra_space

        gap_between_square_and_pendulum_hole = self.collet_screws.getNutHeight(half=True) + 1 + self.collet_screws.getHeadHeight()

        height = outer_d*2.5

        r = outer_d/2

        collet = cq.Workplane("XY").tag("base").circle(r).extrude(self.pendulum_holder_thick)
        collet = collet.workplaneFromTagged("base").moveTo(0,r - height/2).rect(outer_d, height - outer_d).extrude(self.pendulum_holder_thick)
        collet = collet.workplaneFromTagged("base").moveTo(0, outer_d - height).circle(r).extrude(self.pendulum_holder_thick)

        #square bit that slots over arbour
        collet = collet.cut(cq.Workplane("XY").rect(square_size, square_size).extrude(self.pendulum_holder_thick))

        #means to hold end of pendulum made of threaded rod
        collet = collet.cut(get_pendulum_holder_cutter(z=self.pendulum_holder_thick/2).translate((0,-square_side_length/2-gap_between_square_and_pendulum_hole)))

        #means to hold screw that will hold this in place
        collet = collet.cut(self.collet_screws.getCutter(length=outer_d / 2, headSpaceLength=5).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -outer_d / 2, self.pendulum_holder_thick / 2)))
        collet = collet.cut(self.collet_screws.getNutCutter(half=True).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -square_size / 2, self.pendulum_holder_thick / 2)))


        return collet

    def get_anchor_shapes(self):
        shapes = {}
        anchor = self.arbour.escapement.getAnchor()
        if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOUR,PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS]:


            #direct arbour pendulum fixing - a cylinder that extends from the anchor until it reaches where the pendulum should be and becomes a square rod
            #if the anchor is between the plates then the end-shake is controlled by the extensions out each side of the anchor.
            #if the anchor is on the front plate (assumed pendulum is at back), then the cylinder extends all the way through the plates and the square rod is at the back
            #the end of the square rod controls one bit of end shake and there will be a collect that slots onto the rod to control the other

            cylinder_r = self.bearing.innerD / 2
            if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS:
                cylinder_r = self.direct_arbour_d/2
            square_side_length = math.sqrt(2) * cylinder_r

            if cylinder_r < 5:
                square_side_length = math.sqrt(2) * cylinder_r * 1.2


            shapes["pendulum_holder"]=self.get_pendulum_holder_collet(square_side_length, cylinder_r)

            if not self.pendulum_at_front:

                #bits out the back
                rear_bearing_standoff_height = LAYER_THICK*2
                rod_length = self.back_from_wall - self.standoff_plate_thick - self.endshake - rear_bearing_standoff_height


                '''
                Esacpement on teh front and pendulum at the back (like grasshopper)
                '''
                if self.escapement_on_front:
                    #cylinder passes through plates and out the front
                    cylinder_length = self.front_anchor_from_plate + self.total_plate_thickness
                    # if self.arbour.escapement.type == EscapementType.GRASSHOPPER:
                    #     #anchor is split into two parts, the back part has to be printed front-side down because of the link to the pendulum,
                    #     #but we need a gap for the bearing-holder on teh front , otherwise it'll crash into the composers
                    #     bearing_standoff_thick = LAYER_THICK*2
                    #     front_thick = bearing_standoff_thick + 1.5
                    #     back_thick = self.arbour.escapement.getAnchorThick() - front_thick - self.plates.get_front_anchor_bearing_holder_thick()
                    #
                    #     anchor = self.arbour.escapement.getFrame(leave_in_situ=False, thick=back_thick)

                else:
                    #cylinder passes only through the back plate and up to the anchor
                    #no need for collet - still contained within two bearings like a normal arbour
                    cylinder_length = self.back_plate_thick + self.endshake + self.bearing_position[2]
                    shapes["arbour_extension"] = self.get_arbour_extension(front=True)

                anchor_thick = self.arbour.escapement.getAnchorThick()



                wall_bearing = getBearingInfo(self.arbour.arbourD)

                # flip over so the front is on the print bed
                anchor = anchor.rotate((0, 0, 0), (1, 0, 0), 180).translate((0,0,anchor_thick))
                anchor = anchor.union(cq.Workplane("XY").circle(cylinder_r).extrude(cylinder_length + anchor_thick))
                anchor = anchor.union(cq.Workplane("XY").rect(square_side_length,square_side_length).extrude(rod_length).intersect(cq.Workplane("XY").circle(cylinder_r).extrude(rod_length)).translate((0,0, anchor_thick + cylinder_length)))
                anchor = anchor.union(cq.Workplane("XY").circle(wall_bearing.innerSafeD/2).circle(self.arbour.arbourD/2).extrude(rear_bearing_standoff_height).translate((0,0, anchor_thick + cylinder_length + rod_length)))

                anchor = anchor.cut(cq.Workplane("XY").circle(self.arbour.arbourD/2+ARBOUR_WIGGLE_ROOM).extrude(anchor_thick + cylinder_length + rod_length + rear_bearing_standoff_height))
                #anchor is between the plates, make 'base' of cylinder thicker so it can't go through the bearing
                anchor = anchor.union(cq.Workplane("XY").circle(self.bearing.innerSafeD/2).circle(self.arbour.arbourD/2+ARBOUR_WIGGLE_ROOM).extrude(self.distance_from_back + self.arbour.escapement.getAnchorThick()))

            else:
                '''
                I don't think I'm going to design many more with the pendulum on the front, so I'm not going to bother supporting that with a direct arbour unless I have to
                TODO - would be useful to have old designs working again
                '''
                raise NotImplementedError("Unsuported escapement and pendulum combination!")
        else:
            #friction fitting pendulum
            raise ValueError("Only direct arbour pendulum fixing supported currently")
            # print("Only direct arbour pendulum fixing supported currently")
        shapes["anchor"] = anchor
        return shapes

    def get_assembled(self):
        '''
        Get a model that is relative to the back of the back plate of the clock and already in position (so you should just be able to add it straight to the model)

        This is slowly refactoring the complex logic from the Arbour class to here. the ultimate aim is for the arbour class to be unaware of the plates
        and this class be the only one with interactions with the plates
        (might be an edge case for the escape wheel on the front?)
        '''

        assembly = cq.Workplane("XY")
        shapes = self.get_shapes()
        if self.type == ArbourType.ANCHOR:
            assembly = assembly.add(shapes["anchor"].rotate((0, 0, 0), (1, 0, 0), 180))
            if self.arbour.escapement.type == EscapementType.GRASSHOPPER:
                # move 'down' by frame thick because we've just rotated the frame above
                assembly = assembly.add(self.arbour.escapement.getAssembled(leave_out_wheel_and_frame=True, centre_on_anchor=True, mid_pendulum_swing=True).translate((0, 0, -self.arbour.escapement.frame_thick)))


            if self.escapement_on_front:
                anchor_assembly_end_z = self.total_plate_thickness + self.front_anchor_from_plate + self.arbour.escapement.getAnchorThick() - self.endshake/2
            else:
                anchor_assembly_end_z = self.back_plate_thick + self.bearing_position[2] + self.endshake/2 + self.arbour.escapement.getAnchorThick()
                assembly = assembly.add(shapes["arbour_extension"])
            assembly = assembly.translate((0,0,anchor_assembly_end_z))
            if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOUR and self.escapement_on_front and not self.pendulum_at_front:
                collet = shapes["collet"]
                assembly = assembly.add(collet.translate((0, 0, -self.collet_thick - self.endshake/2)))

            pendulum_z = -self.pendulum_sticks_out

            if self.pendulum_at_front:
                pendulum_z = self.total_plate_thickness + self.pendulum_sticks_out

            assembly = assembly.add(shapes["pendulum_holder"].rotate((0,0,0),(0,1,0),180).translate((0,0,pendulum_z + self.pendulum_holder_thick/2)))

            assembly = assembly.translate((self.bearing_position[0], self.bearing_position[1]))
        elif self.type == ArbourType.ESCAPE_WHEEL:
            assembly = assembly.add(self.arbour.getAssembled())
            assembly = assembly.translate(self.bearing_position).translate((0, 0, self.back_plate_thick + self.endshake / 2))

            if self.escapement_on_front:
                assembly = assembly.add(self.arbour.getEscapeWheel(forPrinting=False).translate((self.bearing_position[0], self.bearing_position[1],self.total_plate_thickness + self.front_anchor_from_plate - self.arbour.escapement.getWheelBaseToAnchorBaseZ())))
        else:
            assembly = assembly.add(self.arbour.getAssembled())

            assembly = assembly.translate(self.bearing_position).translate((0,0, self.back_plate_thick + self.endshake/2))

        return assembly

    def get_shapes(self):
        '''
        return a dict of name:shape for all the components needed for this arbour
        always for printing, they will be arranged for the model in get_assembled()
        '''
        shapes = {}

        if self.arbour.getType() == ArbourType.ANCHOR:
            return self.get_anchor_shapes()

        if self.arbour.getType() in [ArbourType.WHEEL_AND_PINION, ArbourType.ESCAPE_WHEEL]:

            #TODO refactor everything into this class
            shapes["wheel"]=self.arbour.getShape()
            extras = self.arbour.getExtras()
            for extraName in extras:
                shapes[extraName]=extras[extraName]

            shapes["pinion_STL_modifier"]=self.arbour.getSTLModifierPinionShape()

        return shapes


    def get_arbour_extension(self, front=True):
        '''
        Get little cylinders we can use as spacers to keep the gears in the right place on the rod

        Simple logic here, it may produce some which aren't needed
        '''

        length = self.distance_from_front if front else self.distance_from_back
        bearing = getBearingInfo(self.arbour.getRodD())

        outer_r = self.arbour.getRodD()
        inner_r = self.arbour.getRodD() / 2 + ARBOUR_WIGGLE_ROOM/2
        tip_r = bearing.innerSafeD/2
        if tip_r > outer_r:
            tip_r = outer_r

        if length - self.arbour_bearing_standoff_length >= 0:
            if length > self.arbour_bearing_standoff_length:
                extendo_arbour = cq.Workplane("XY").tag("base").circle(outer_r).circle(inner_r).extrude(length-self.arbour_bearing_standoff_length).faces(">Z").workplane()
            else:
                extendo_arbour=cq.Workplane("XY")
            extendo_arbour = extendo_arbour.circle(tip_r).circle(inner_r).extrude(self.arbour_bearing_standoff_length)

            return extendo_arbour
        return None

class Arbour:
    def __init__(self, arbourD=None, wheel=None, wheelThick=None, pinion=None, pinionThick=None, poweredWheel=None, escapement=None, endCapThick=1, style=GearStyle.ARCS,
                 distanceToNextArbour=-1, pinionAtFront=True, ratchetInset=True, ratchetScrews=None, pendulumFixing = PendulumFixing.FRICTION_ROD, useRatchet=True, clockwise_from_pinion_side=True):
        '''
        This represents a combination of wheel and pinion. But with special versions:
        - chain wheel is wheel + ratchet (pinionThick is used for ratchet thickness)
        - escape wheel is pinion + escape wheel
        - anchor is just the escapement anchor

        This is being slowly refactored so it's purely theoretical and you need the ArbourForPlate to produce an STL that can be printed

        its primary purpose is to help perform the layout of a gear train. Originally it was trying to store all the special logic for thicknesses and radii in one place


        NOTE currently assumes chain/cord is at the front - needs to be controlled by something like pinionAtFront



        Note - this is becoming a bit bloated with the inclusion of escapementOnFront. Would it be worth trimming this class down, and getting the plates
        to produce the final shapes for all arbours/wheels? then lots of the special cases don't need to be dealt with here
        Planning to do this, I think everythign that depends on setPlateInfo should be removed from this class
        Then it can be given more options for getShape() - like option for pinion_only
        the direct arbour anchor will be the first thing to be done in the plates instead of here, and the rest should be moved over slowly

        Or maybe a new ArbourForPlate class? the input would be this Arbour and plate info, then it's explicit that this arbour is a theorical arbour used for calculating
        the layout of the gear train, and ArbourForPlate is responsible for

        , looseOnRod=False
        '''
        #diameter of the threaded rod. Usually assumed to also be the size of the hole
        self.arbourD=arbourD
        self.wheel=wheel
        self.wheelThick=wheelThick
        self.pinion=pinion
        self.pinionThick=pinionThick
        self.escapement=escapement
        self.endCapThick=endCapThick
        #the pocket chain wheel or cord wheel (needed to calculate full height and a few tweaks)
        self.poweredWheel=poweredWheel
        self.style=style
        self.distanceToNextArbour=distanceToNextArbour
        self.nutSpaceMetric=None
        #for the anchor, this is the side with the pendulum
        #for the powered wheel, this is the side with the chain/rope/cord
        self.pinionAtFront=pinionAtFront
        #only used for cutting the gear style
        self.clockwise_from_pinion_side = clockwise_from_pinion_side
        #if using hyugens maintaining power then the chain wheel is directly fixed to the wheel, without a ratchet.
        self.useRatchet=useRatchet
        #is this screwed (and optionally glued) to the threaded rod?
        self.looseOnRod = False

        #TODO remove from this class and move to ArbourForPlate
        self.pendulumFixing = pendulumFixing

        self.ratchet = None
        if self.poweredWheel is not None:
            self.ratchet=self.poweredWheel.ratchet

        if self.getType() == ArbourType.CHAIN_WHEEL:
            # currently this can only be used with the cord wheel
            self.looseOnRod = (not self.poweredWheel.looseOnRod) and useRatchet

        self.holeD = arbourD
        if self.looseOnRod:
            if self.arbourD == 4:
                # assume steel pipe (currently only have pipe with a 4mm internal diameter)
                #6.2 squeezes on and holds tight!
                self.holeD = STEEL_TUBE_DIAMETER
            else:
                self.holeD = self.arbourD + LOOSE_FIT_ON_ROD

        #bits set by setPlateInfo - this isn't known until the plates are generated
        self.frontSideExtension=0
        self.rearSideExtension=0
        self.arbourExtensionMaxR=self.arbourD
        self.useArbourExtenders=False
        self.frontPlateThick = 0
        self.pendulumSticksOut = 0
        self.escapementOnFront = False
        #so that we don't have the arbour pressing up against hte bit of the bearing that doesn't move, adding friction
        self.arbourBearingStandoff=LAYER_THICK*2

        if self.getType() == ArbourType.UNKNOWN:
            raise ValueError("Not a valid arbour")

        #just to help debugging
        self.type = self.getType()

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


            if self.useRatchet:
                bolts = 4
                outerR = self.ratchet.outsideDiameter / 2
                innerR = self.ratchet.toothRadius
                boltDistance = (outerR + innerR) / 2

                #offsetting so it's in the middle of a click (where it's slightly wider)
                self.boltPositions=[polar(i*math.pi*2/bolts + math.pi/self.ratchet.ratchetTeeth, boltDistance) for i in range(bolts)]
            else:
                #bolting powered wheel on without a ratchet
                self.boltPositions = self.poweredWheel.getScrewPositions()

            self.ratchetScrews = ratchetScrews
            if self.ratchetScrews is None:
                self.ratchetScrews = MachineScrew(2, countersunk=True)

            self.combine_with_powered_wheel = False
            if not self.useRatchet and self.poweredWheel.type == PowerType.ROPE:
                #this can be printed in one peice, so combine with the wheel and use a standard arbour extension
                self.combine_with_powered_wheel = True

        if self.getType() == ArbourType.ANCHOR:
            #the anchor now controls its own thickness and arbour thickness, so get dimensions from that
            self.arbourD = self.escapement.getAnchorArbourD()
            self.holeD = self.arbourD
            self.wheelThick = self.escapement.getAnchorThick()
        if self.getType() == ArbourType.ESCAPE_WHEEL:
            self.wheelThick = self.escapement.getWheelThick()

        #anchor specific, will be refined once arbour extension info is provided
        # want a square bit so we can use custom long spanners to set the beat
        self.spannerBitThick = 4
        self.spannerBitOnFront=False
        #turning off this for now, it wasn't useful
        self.useSpanner=False


    def setPlateInfo(self, frontSideExtension=0, rearSideExtension=0, maxR=0, frontPlateThick=0, backPlateThick=0, pendulumSticksOut=0,
                     pendulumAtFront=True, endshake=1, pendulumFixingBearing=None, escapementOnFront=False, plateDistance=0):
        '''
        front/rear side extensions: how far from the front or back of this arbour to the front or back plate (excluding end shake aka "wobble")

        maxR - how fat teh arbour can be while avoiding any other gears or parts of teh clock

        This info is only known after the plates are configured, so retrospectively add it to the arbour.

        Added the to pinion side (or the 'back' of the chainwheel if the ratchet is bolt-on)
        '''
        self.frontSideExtension=frontSideExtension
        self.rearSideExtension=rearSideExtension
        self.arbourExtensionMaxR=maxR
        #the motion works never has this set, so if we're setting plate info we know we need it
        self.useArbourExtenders = True

        self.frontPlateThick=frontPlateThick
        self.pendulumSticksOut=pendulumSticksOut
        self.pendulumAtFront=pendulumAtFront
        self.backPlateThick=backPlateThick
        self.endshake=endshake
        self.pendulumFixingBearing = pendulumFixingBearing
        self.escapementOnFront = escapementOnFront
        self.plateDistance = plateDistance

        #can now calculate the location and size of the spanner nut for the anchor
        if self.getType() == ArbourType.ANCHOR and self.pendulumFixing == PendulumFixing.FRICTION_ROD and self.useSpanner:
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
        if self.escapementOnFront and self.getType() == ArbourType.ESCAPE_WHEEL:
            #bodge, this is the pinion only arbour, we want the included arbour extension to be the shorted, so set pinionside to the shorted extension
            self.pinionAtFront = self.frontSideExtension < self.rearSideExtension


    def setNutSpace(self, nutMetricSize=3):
        '''
        This arbour is fixed firmly to the rod using a nyloc nut
        '''
        self.nutSpaceMetric=nutMetricSize

    def getType(self):
        if self.wheel is not None and self.pinion is not None:
            return ArbourType.WHEEL_AND_PINION
        if self.wheel is not None and self.poweredWheel is not None:
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
        if not self.useRatchet:
            return 0

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
        return total thickness of everything that will be on the rod (between the plates!)
        '''
        if self.getType() in [ArbourType.WHEEL_AND_PINION, ArbourType.ESCAPE_WHEEL]:

            if self.escapementOnFront and self.getType() == ArbourType.ESCAPE_WHEEL:
                #just the pinion is within the plates
                return self.pinionThick + self.endCapThick*2

            return self.wheelThick + self.pinionThick + self.endCapThick
        if self.getType() == ArbourType.CHAIN_WHEEL:
            #the chainwheel (or cordwheel) now includes the ratceht thickness
            return self.wheelThick + self.poweredWheel.getHeight() - self.getRatchetInsetness(toCarve=False)
        if self.getType() == ArbourType.ANCHOR:
            if self.escapementOnFront:
                #no main shape, just two arbour extensions
                return 0
            else:
                # wheel thick being used for anchor thick
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

    def getEscapeWheel(self, forPrinting=True):
        #escapement controls wheel thickness
        arbour_or_pivot_r = self.pinion.getMaxRadius()
        if self.escapementOnFront:
            arbour_or_pivot_r = self.arbourD*2
        wheel = self.escapement.getWheel(style = self.style, arbour_or_pivot_r=arbour_or_pivot_r, holeD=self.holeD)





        if self.escapementOnFront:
            #it's just teh wheel for now, but extended a bit to make it more sturdy
            #TODO extend back towards the front plate by the distance dictacted by the escapement
            # arbour = wheel.add(cq.Workplane("XY").circle(self.arbourD*2).circle(self.arbourD/2).extrude(15))

            extraArbourLength =10
            arbour = wheel.faces(">Z").workplane().moveTo(0,0).circle(self.arbourD*2).circle(self.arbourD/2).extrude(extraArbourLength)
            arbourThreadedRod = MachineScrew(metric_thread=self.arbourD)
            #going to see if a nyloc nut is enough to secure the wheel to the arbour. Nyloc wasn't enough for the chainwheel, but this doesn't have a chain being dragged over it once a day
            arbour = arbour.cut(arbourThreadedRod.getNutCutter(nyloc=True).translate((0,0,self.wheelThick+extraArbourLength - arbourThreadedRod.getNutHeight(nyloc=True))))
            #original plan had been to extend the arbour to the front plate. Now the plan is to put an extra bearing on the front plate that sticks out,
            # so this extension is just for stability and is out the front of the clock
            # extension = -self.escapement.getWheelBaseToAnchorBaseZ()
            # arbour = wheel.translate((0,0,extension))
            # arbour = arbour.add(cq.Workplane("XY").circle(self.arbourD * 2).circle(self.arbourD / 2).extrude(extension))
            #
            # if forPrinting:
            #     arbour = arbour.rotate((0,0,0),(1,0,0),180)

            # if not forPrinting:
            #     #move into position that's correct relative to the frame
            #     arbour = arbour.translate((0,0,-self.escapement.getWheelBaseToAnchorBaseZ()))

        else:

            if self.escapement.type == EscapementType.GRASSHOPPER and not self.escapement.clockwiseFromPinionSide:
                # bodge, should try and tidy up how the escapements do this, but generally the anchor will be inside the plates (attached to a pinion) and the grasshopper won't be
                # so this here is probably an edge case
                wheel = wheel.mirror("YZ", (0, 0, 0))

            # pinion is on top of the wheel
            pinion = self.pinion.get3D(thick=self.pinionThick, holeD=self.holeD, style=self.style).translate([0, 0, self.wheelThick])

            arbour = wheel.union(pinion)
            if self.endCapThick > 0:
                arbour = arbour.union(cq.Workplane("XY").circle(self.pinion.getMaxRadius()).extrude(self.endCapThick).translate((0,0,self.wheelThick + self.pinionThick)))

            arbour = arbour.cut(cq.Workplane("XY").circle(self.holeD / 2).extrude(self.wheelThick + self.pinionThick + self.endCapThick))

        return arbour

    def getSTLModifierPinionShape(self):
        '''
        return a shape that covers the teeth of the pinions for apply tweaks to the slicing settings
        '''

        if self.getType() == ArbourType.WHEEL_AND_PINION:
            return self.pinion.getSTLModifierShape(thick=self.pinionThick, offset_z=self.wheelThick, min_inner_r=self.arbourD/2)

        return None

    def getSTLModifierWheelShape(self):
        '''
        return a shape that covers the teeth of the pinions for apply tweaks to the slicing settings
        '''

        if self.getType() == ArbourType.WHEEL_AND_PINION:
            return self.pinion.getSTLModifierShape(thick=self.pinionThick, offset_z=self.wheelThick, min_inner_r=self.arbourD/2)

        return None

    def getShape(self, forPrinting=True):
        '''
        return a shape that can be exported to STL
        if for printing, wheel is on the bottom, if false, this is in the orientation required for the final clock
        '''
        if self.getType() == ArbourType.WHEEL_AND_PINION:
            shape = self.pinion.addToWheel(self.wheel, holeD=self.holeD, thick=self.wheelThick, style=self.style, pinionThick=self.pinionThick, capThick=self.endCapThick, clockwise_from_pinion_side=self.clockwise_from_pinion_side)
        elif self.getType() == ArbourType.ESCAPE_WHEEL:
            if self.escapementOnFront:
                shape = self.getPinionArbour(forPrinting=forPrinting)
            else:
                shape = self.getEscapeWheel()
        elif self.getType() == ArbourType.CHAIN_WHEEL:
            shape = self.getPoweredWheel(forPrinting=forPrinting)
        elif self.getType() == ArbourType.ANCHOR:
            # NOTE - this should now be driven from ArbourForPlate
            if self.escapementOnFront:
                #there's just a spacer, made up of two arbour extensions (so the bearing standoffs are always printed on top)
                # shape = self.getArbourExtension(front=self.pinionAtFront).rotate((0,0,0),(1,0,0),180)
                #the extension will be added below
                shape = cq.Workplane("XY")
            else:
                shape = self.getAnchor(forPrinting=forPrinting)
        else:
            raise ValueError("Cannot produce 3D model for type: {}".format(self.getType().value))

        # note, the included extension is always on the pinion side (unprintable otherwise)
        if self.needArbourExtension(front=True) and self.pinionAtFront:
            #need arbour extension on the front
            extendo = self.getArbourExtension(front=True).translate((0, 0, self.getTotalThickness()))
            shape = shape.add(extendo)

        if self.needArbourExtension(front=False) and not self.pinionAtFront:
            # need arbour extension on the rear
            extendo = self.getArbourExtension(front=False).translate((0, 0, self.getTotalThickness()))
            shape = shape.add(extendo)


        if not forPrinting and not self.pinionAtFront and (self.getType() in [ArbourType.WHEEL_AND_PINION, ArbourType.ESCAPE_WHEEL]):
            #make it the right way around for placing in a model
            #rotate not mirror! otherwise the escape wheels end up backwards
            shape = shape.rotate((0,0,0),(1,0,0),180).translate((0,0,self.getTotalThickness()))


        return shape

    def getAnchorSpannerSize(self):
        return self.getRodD() * 2

    def getAnchor(self, forPrinting=True):

        remainingExtension = (self.frontSideExtension if self.spannerBitOnFront else self.rearSideExtension) - self.spannerBitThick

        #just the anchor/frame shape, with nothing else that might be needed
        anchor = self.escapement.getAnchor()

        if self.escapementOnFront:
            if self.pendulumFixing == PendulumFixing.FRICTION_ROD:
                #cut out a nut space, planning to clamp it between a nut included at the back and a nut on teh front
                anchor = anchor.cut(MachineScrew(self.arbourD).getNutCutter(half=True))

            #not much else to do
            if not forPrinting and self.escapement.type == EscapementType.GRASSHOPPER:
                #if for the model, include all the other bits
                anchor = anchor.add(self.escapement.getAssembled(leave_out_wheel_and_frame=True, centre_on_anchor=True))
            else:
                #if for printing, flip over so the front is on the print bed
                anchor = anchor.rotate((0,0,0), (1,0,0), 180)
            return anchor

        if self.pendulumFixing == PendulumFixing.FRICTION_ROD:

            #undecided here, textured sheet looks good on teh front, put supergluing the anchor's arbour extension on (which helps setting the beat as only one side can move) makes it a bit ugly
            #no spanner, just a normal arbour extension, on the back, so the front is printed on the plate (looks better with the textured PETG)
            arbourExtension = self.getArbourExtension(front=True)
            arbourExtension = arbourExtension.translate((0, 0, self.wheelThick))
            anchor = anchor.add(arbourExtension)

        elif self.pendulumFixing == PendulumFixing.DIRECT_ARBOUR:
            '''
            Extend the arbour out through a larger bearing and end in a square (like the cannon pinion) that the pendulum end can slot over
            '''
            #note - copied and modified from the unfinished spring arbour
            bearingWiggleRoom = 0.05
            bearingStandoffThick = 0.6

            # radius for that bit that slots inside the bearing
            bearingBitR = self.pendulumFixingBearing.innerD / 2 - bearingWiggleRoom
            diameter = self.arbourD*2
            beforeBearingTaperHeight = 0
            if diameter < bearingBitR * 2:
                # need to taper up to the bearing, as it's bigger!
                r = self.pendulumFixingBearing.innerSafeD / 2 - diameter / 2
                angle = degToRad(30)
                beforeBearingTaperHeight = r * math.sqrt(1 / math.sin(angle) - 1)

            normalExtensionLength = self.frontSideExtension-beforeBearingTaperHeight-bearingStandoffThick
            if normalExtensionLength <=0 :
                # raise ValueError("TODO work to enable really short anchor arbours")
                print("TODO work to enable really short anchor arbours")
                normalExtensionLength=0.1

            arbour = cq.Workplane("XY").circle(diameter/2).extrude(normalExtensionLength)

            if beforeBearingTaperHeight > 0:
                arbour = arbour.add(cq.Solid.makeCone(radius1=diameter / 2, radius2=self.pendulumFixingBearing.innerSafeD / 2, height=beforeBearingTaperHeight).translate((0, 0, normalExtensionLength)))
                arbour = arbour.faces(">Z").workplane().moveTo(0, 0).circle(self.pendulumFixingBearing.innerSafeD / 2).extrude(bearingStandoffThick)

            roundBitThick = self.frontPlateThick + self.endshake/2

            arbour = arbour.faces(">Z").workplane().moveTo(0, 0).circle(self.pendulumFixingBearing.innerD / 2 - bearingWiggleRoom).extrude(roundBitThick)
            # using polygon rather than rect so it calcualtes the size to fit in teh circle
            arbour = arbour.faces(">Z").workplane().polygon(4, self.pendulumFixingBearing.innerD - bearingWiggleRoom * 2).extrude(self.pendulumSticksOut+20)

            arbour = arbour.rotate((0,0,0), (0,0,1), 45)

            arbour = arbour.faces(">Z").workplane().circle(self.arbourD / 2).cutThruAll()

            anchor = anchor.add(arbour.translate((0,0,self.wheelThick)))

        return anchor

    def getArbourExtension(self, front=True):
        '''
        Get little cylinders we can use as spacers to keep the gears in the right place on the rod

        returns None if no extension is needed
        '''

        length = self.frontSideExtension if front else self.rearSideExtension
        bearing = getBearingInfo(self.arbourD)

        if self.getType() == ArbourType.ANCHOR and self.escapementOnFront:
            #this is just a spacer split into two
            length = self.plateDistance/2 - self.endshake/2

        if bearing is None:
            #i think this can only happen for the motion works arbour at the moment, where we don't need standoffs anyway, so bodge for now
            return None

        if length == 0 and front == self.pinionAtFront:
            #bodge to always have a bearing standoff
            length = self.arbourBearingStandoff

        outerR = self.getRodD()
        innerR = self.getRodD() / 2 + ARBOUR_WIGGLE_ROOM/2
        tipR = bearing.innerSafeD/2
        if tipR > outerR:
            tipR = outerR

        if length - self.arbourBearingStandoff >= 0:
            if length > self.arbourBearingStandoff:
                extendoArbour = cq.Workplane("XY").tag("base").circle(outerR).circle(innerR).extrude(length-self.arbourBearingStandoff).faces(">Z").workplane()
            else:
                extendoArbour=cq.Workplane("XY")
            extendoArbour = extendoArbour.circle(tipR).circle(innerR).extrude(self.arbourBearingStandoff)

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
            shape = shape.add(self.getArbourExtension(front=False).rotate((0,0,0),(1,0,0),180))

        if self.getType() == ArbourType.CHAIN_WHEEL:
            # should work for both chain and cord

            boltOnRatchet = self.getExtraRatchet(forPrinting=False)
            if boltOnRatchet is not None:
                #already in the right place
                shape = shape.add(boltOnRatchet)

            if not self.combine_with_powered_wheel:
                shape = shape.add(self.poweredWheel.getAssembled().translate((0, 0, self.wheelThick - self.getRatchetInsetness())))

        # if self.getType() == ArbourType.ESCAPE_WHEEL and self.escapement.type == EscapementType.GRASSHOPPER:
        #
        #     z = self.escapement.getWheelBaseToAnchorBaseZ()
        #     if not self.pinionAtFront:
        #         z += self.pinionThick + self.endCapThick
        #
        #     shape = shape.add(self.escapement.getAssembled(leave_out_wheel_and_frame=True).translate((0,0,z)))

        return shape

    def needArbourExtension(self, front=True):
        if not self.useArbourExtenders:
            return False



        #not enough to print
        if front and self.frontSideExtension < self.arbourBearingStandoff:
            return False
        if (not front) and self.rearSideExtension < self.arbourBearingStandoff:
            return False

        if self.getType() == ArbourType.ANCHOR and self.useSpanner:
            return not (front == self.spannerBitOnFront)

        # if self.getType() == ArbourType.ANCHOR and self.escapementOnFront:
        #     #the extension on the front
        #     return not front == self.pinionAtFront

        if self.getType() == ArbourType.CHAIN_WHEEL:
            #assuming chain is at front
            if front:
                return False
            else:
                if self.combine_with_powered_wheel:
                    return True
                return not self.boltOnRatchet

        return True

    def getPinionArbour(self, forPrinting=True):
        '''
        For an escape wheel out the front of the clock there's just a pinion on the arbour inside the clock

        we've already calculated which extension to include in setPlateInfo (we're including teh shortest) so use pinionAtFront for which extension we're using here
        '''
        # longestExtensionIsFront = self.frontSideExtension > self.rearSideExtension
        #we want to print the smallest extension as part of the pinion, because it's likely pressed up against the plate and so too small to thread on by itself

        pinion = self.pinion.get3D(thick=self.pinionThick, holeD=self.holeD).translate((0,0,self.endCapThick))
        cap = cq.Workplane("XY").circle(self.pinion.getMaxRadius()).circle(self.holeD/2).extrude(self.endCapThick)
        pinion = pinion.add(cap).add(cap.translate((0,0,self.endCapThick + self.pinionThick)))

        arbourExtension = self.getArbourExtension(front= self.pinionAtFront)

        thick = self.endCapThick*2 + self.pinionThick
        if arbourExtension is not None:
            pinion = pinion.add(arbourExtension.translate((0,0,thick)))

        if not forPrinting and not self.pinionAtFront:
                pinion = pinion.rotate((0,0,0),(1,0,0),180).translate((0,0,thick))

        return pinion



    def getExtras(self):
        '''
        are there any extra bits taht need printing for this arbour?
        returns {'name': shape,}
        '''
        extras = {}

        if self.getType() == ArbourType.CHAIN_WHEEL and self.getExtraRatchet() is not None:
            extras['ratchet']= self.getExtraRatchet()

        if self.escapementOnFront and self.getType() in [ArbourType.ANCHOR, ArbourType.ESCAPE_WHEEL]:
            '''
            quite different logic for the bits that stick out the front.
            Treating the arbour as the escape wheel and frame, and the "extras" as the bit between the plates
            '''
            if self.getType() == ArbourType.ANCHOR:
                #the main shape is two arbour extenders, so this is the real frame
                extras['anchor'] = self.getAnchor()
                #bail out before the extensions
                return extras
            elif self.getType() == ArbourType.ESCAPE_WHEEL:
                #main shape is the bit between the plates
                extras['escape_wheel'] = self.getEscapeWheel()

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
        if not self.useRatchet:
            return None

        ratchetOutsideWheelRequired = self.ratchet.thick - self.getRatchetInsetness(toCarve=False)

        if ratchetOutsideWheelRequired <= 0:
            return None

        ratchetWheel = self.ratchet.getOuterWheel(thick=ratchetOutsideWheelRequired)

        if self.boltOnRatchet:
            #add holes
            for holePos in self.boltPositions:
                # countersunk = not self.ratchetScrewsPanHead
                # ratchetWheel = ratchetWheel.faces(">Z").moveTo(holePos[0], holePos[1]).circle(self.screwSize/2).cutThruAll()
                # headHeight = getScrewHeadHeight(self.screwSize, countersunk=countersunk)
                # # if not countersunk:
                # #
                # #     cutter = cq.Workplane("XY").circle(getScrewHeadDiameter(self.screwSize,countersunk=countersunk)/2+0.1).extrude(headHeight).translate((holePos[0], holePos[1],ratchetOutsideWheelRequired-headHeight))
                # # else:
                # #     coneHeight = getScrewHeadHeight(self.screwSize, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE_SMALL
                # #     topR = getScrewHeadDiameter(self.screwSize, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE_SMALL
                #     cutter = cq.Workplane("XY").add(cq.Solid.makeCone(radius2=topR, radius1=self.screwSize / 2, height=coneHeight).translate((holePos[0], holePos[1],ratchetOutsideWheelRequired-coneHeight)))

                cutter = self.ratchetScrews.getCutter(withBridging=False).rotate((0,0,0),(0,1,0),180).translate((holePos[0], holePos[1],ratchetOutsideWheelRequired))
                # return cutter
                ratchetWheel = ratchetWheel.cut(cutter)

        ratchetWheel = ratchetWheel.translate((0, 0, self.wheelThick))

        # if not forPrinting:
        #     ratchetWheel = ratchetWheel.rotate((0,0,0),(1,0,0),180)

        return ratchetWheel

    def printScrewLength(self):
        if self.getExtraRatchet() is not None:
            length = self.wheelThick-self.getRatchetInsetness(toCarve=False) + self.ratchet.thick
            if not self.ratchetScrews.countersunk:
                length -= self.ratchetScrews.getHeadHeight()
            print("Ratchet needs {} screws of length {}mm".format(self.ratchetScrews.getString(),length))

    def getPoweredWheel(self, forPrinting=True):

        if self.useRatchet:
            innerRadiusForStyle=self.ratchet.outsideDiameter * 0.5
        else:
            innerRadiusForStyle = self.poweredWheel.diameter*1.1/2
        #invert clockwise from pinion side as the "pinion" is used for the side of the powered wheel, which is wrong
        #TODO review logic if I ever get chain at back working again
        gearWheel = self.wheel.get3D(holeD=self.holeD, thick=self.wheelThick, style=self.style, innerRadiusForStyle=innerRadiusForStyle, clockwise_from_pinion_side=not self.clockwise_from_pinion_side)

        holeDeep = self.getRatchetInsetness(toCarve=True)
        if holeDeep > 0:
            #ratchet is inset (only used once and decided against it since)

            #note, if the ratchet is inset the wheel will need some other mechanism to keep it at right angles on the rod, like the wheelSideExtension set

            #bare in mind this wheel is now upside down in the case of an inset ratchet
            ratchetHole = getHoleWithHole(self.arbourD,self.ratchet.outsideDiameter,holeDeep).rotate((0,0,0),(1,0,0),180).translate((0,0,self.wheelThick))
            gearWheel = gearWheel.cut(ratchetHole)
            ratchetZ = self.wheelThick - holeDeep
            #extra layer thick so the hole-in-a-hole doesn't print with gaps at the edges
            ratchetWheel = self.ratchet.getOuterWheel(thick=holeDeep+LAYER_THICK).translate((0, 0, ratchetZ-LAYER_THICK))
            gearWheel = gearWheel.add(ratchetWheel)


        needScrewHoles = False

        if self.boltOnRatchet or not self.useRatchet:
            #only extend out this way if the ratchet is inset (or there is not ratchet!) - otherwise this is unprintable
            #have it stand off from the bearing slightly

            use_rear_side_extension = True

            if self.combine_with_powered_wheel:
                #currently only rope wheel can do this for huygens, which is also a combination I'm unlikely to ever print again as splicing cord is a faff
                gearWheel = gearWheel.union(self.poweredWheel.getAssembled().translate((0,0,self.wheelThick)))

            if self.rearSideExtension > 0 and not self.combine_with_powered_wheel:
                #rear side extension
                #limit to r of 1cm
                maxR = 10
                if self.looseOnRod:
                    maxR = 15

                extensionR = min(maxR,self.arbourExtensionMaxR)

                # if extensionR > 10:
                #    extensionR = 10

                if len(self.boltPositions) > 0:
                    boltR = np.linalg.norm(self.boltPositions[0])
                    #make sure it's possible to screw the ratchet or wheel on
                    if extensionR > boltR - self.ratchetScrews.getNutContainingDiameter()/2:
                        extensionR = boltR - self.ratchetScrews.getNutContainingDiameter()/2

                bearingStandoffHeight = LAYER_THICK * 2
                bearingStandoffR = getBearingInfo(self.arbourD).innerSafeD/2
                if bearingStandoffR > extensionR:
                    bearingStandoffR = extensionR

                if extensionR < self.arbourD:
                    raise ValueError("Wheel next to powered wheel is too large for powered wheel arbour extension to fit. Try making module reduction smaller for gear generation")
                extendedArbour = cq.Workplane("XY").circle(extensionR).extrude(self.rearSideExtension - bearingStandoffHeight).faces(">Z").workplane().circle(bearingStandoffR).extrude(bearingStandoffHeight)
                #add hole for rod!
                extendedArbour = extendedArbour.faces(">Z").circle(self.arbourD/2).cutThruAll()

                gearWheel = gearWheel.add(extendedArbour.rotate((0,0,0),(1,0,0),180))

            if self.getExtraRatchet() is not None or not self.useRatchet:
                #need screwholes to attach the rest of the ratchet or the chain wheel (the boltPositions have alreayd been adjusted accordingly)
                # either to hold on the outer part of the ratchet or the powered wheel itself
                for holePos in self.boltPositions:
                    cutter = cq.Workplane("XY").moveTo(holePos[0], holePos[1]).circle(self.ratchetScrews.metric_thread / 2).extrude(self.wheelThick)
                    gearWheel = gearWheel.cut(cutter)
                    # cutter = cq.Workplane("XY").moveTo(holePos[0],holePos[1]).polygon(nSides=6,diameter=getNutContainingDiameter(self.screwSize)+NUT_WIGGLE_ROOM).extrude(getNutHeight(self.screwSize))
                    # gearWheel=gearWheel.cut(cutter)
                    if self.wheelThick - self.ratchetScrews.getNutHeight(half=True) > 1:
                        cutter = self.ratchetScrews.getNutCutter(withBridging=False, half=True).translate(holePos)
                    # else screwing straight into the wheel seemed surprisingly secure, and if the wheel is that thin it probably isn't holding much weight anyway
                    gearWheel = gearWheel.cut(cutter)

        else: # not bolt on ratchet
            gearWheel = gearWheel.union(self.getExtraRatchet().translate((0,0,self.wheelThick)))

        if (self.boltOnRatchet or not self.useRatchet) and forPrinting:
            #put flat side down
            gearWheel = gearWheel.rotate((0,0,0),(1,0,0),180)

        if self.looseOnRod:
            #cut a hole through the arbour extension too (until the arbour extension takes this into account, but it doesn't since this currently only applies to the cord wheel)
            cutter = cq.Workplane("XY").circle(self.holeD/2).extrude(10000).translate((0,0,-5000))
            gearWheel = gearWheel.cut(cutter)
            print("Need steel tube of length {}mm".format(self.wheelThick + self.rearSideExtension))

        # if not self.ratchetInset and self.wheelSideExtension > 0:
        #     print("UNPRINTABLE CHAIN WHEEL, cannot have bits sticking out both sides")

        if not self.pinionAtFront:
            #chain is at the back
            #I'm losing track of how many times we flip this now
            gearWheel = gearWheel.rotate((0,0,0),(1,0,0),180).translate((0,0,self.getTotalThickness()))

        return gearWheel

class MotionWorks:

    #enough for two half height nuts, a washer and a slightly compressed spring washer to be contained in the base of the cannon pinion
    STANDARD_INSET_DEPTH = 4.5

    def __init__(self, arbourD=3, thick=3, pinionThick=-1, module=1, minuteHandThick=3, extra_height=0,
                 style=GearStyle.ARCS, compensateLooseArbour=True, snail=None, strikeTrigger=None, strikeHourAngleDeg=45, compact=False, bearing=None, inset_at_base=-1):
        '''

        inset_at_base - if >0 (usually going to want just less than TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT) then inset the bearing or create a space large enoguh
        for the two locked nuts, washer and spring washer. this way the motion works can be closer to the clock plate

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

        '''
        self.arbourD = arbourD
        self.holeD=arbourD + 0.4
        #thickness of gears
        self.thick = thick
        self.pinionThick = pinionThick
        if self.pinionThick < 0:
            self.pinionThick = self.thick*2
        self.style=style
        self.compact = compact

        self.inset_at_base = inset_at_base

        self.strikeTrigger=strikeTrigger
        #angle the hour strike should be at
        self.strikeHourAngleDeg=strikeHourAngleDeg
        self.snail=snail

        self.pinionCapThick = thick/2
        if self.compact:
            self.pinionCapThick = 0

        self.module = module
        self.compensateLooseArbour = compensateLooseArbour

        self.bearing = bearing

        self.inset_at_base_r = (get_washer_diameter(self.arbourD) + 1)/2

        self.cannonPinionPinionThick = self.pinionThick
        self.calculateGears()



        self.wallThick = 1.5
        #for centred seconds hands, the bit you can twist to set the time
        self.knob_thick = 1.5


        # self.pairs = [WheelPinionPair(36, 12, module), WheelPinionPair(40, 10, secondModule)]


        #minuteHandHolderSize=5,
        #length of the edge of the square that holds the minute hand
        #(if minuteHandHolderIsSquare is false, then it's round and this is a diameter)
        self.minuteHandHolderSize=self.arbourD + 2

        #if no bearing this has no second hand in the centre, so is a "normal" motion works

        self.minuteHandHolderIsSquare = True


        self.minuteHandHolderD = self.minuteHandHolderSize*math.sqrt(2)+0.5

        if self.bearing is not None:
            self.minuteHandHolderD = self.bearing.outerD + 4
            self.inset_at_base_r = self.bearing.outerD/2
            self.holeD = self.bearing.outerSafeD
            self.minuteHandHolderSize = self.bearing.outerD + 3
            # if there is a bearing then there's a rod through the centre for the second hand and the minute hand is friction fit like the hour hand
            self.minuteHandHolderIsSquare = False
        #assume bearing == centred second hand.
        self.centred_second_hand = self.bearing is not None

        # print("minute hand holder D: {}".format(self.minuteHandHolderD))

        self.distanceBetweenHands = minuteHandThick
        self.minuteHandSlotHeight = minuteHandThick
        self.hourHandSlotHeight = minuteHandThick + self.distanceBetweenHands

        self.bearingHolderThick = 0

        self.calc_bearing_holder_thick()
        print("bearingHolderThick",self.bearingHolderThick)

        #done in calc_bearing_holder_thick
        # self.cannonPinionBaseHeight = self.cannonPinionPinionThick + self.pinionCapThick * 2 + self.bearingHolderThick
        self.space = 0.5
        #old size of space so I can reprint without reprinting the hands (for the non-bearing version)
        self.hourHandHolderD = self.minuteHandHolderD + 1 + self.wallThick*2

        if self.bearing is not None:
            #remove the backwards compatible bodge, we don't want this any bigger than it needs to be
            self.hourHandHolderD -= 1

        if extra_height < self.thick*2:
            #to ensure hour hand can't hit the top of the arbour
            extra_height = self.thick*2

        #thick for thickness of hour holder wheel
        self.cannonPinionTotalHeightAboveBase = extra_height + self.minuteHandSlotHeight + self.space + self.hourHandSlotHeight + self.thick# + self.cannonPinionBaseHeight


    def get_hour_wheel_teeth(self):
        return self.pairs[1].wheel.teeth

    def get_cannon_pinion_teeth(self):
        return self.pairs[0].pinion.teeth

    def get_cannon_pinion_total_height(self):
        return self.cannonPinionTotalHeightAboveBase + self.cannonPinionBaseHeight

    def get_cannon_pinion_effective_height(self):
        #because the inset at the base means the locking nuts and spring washer sit inside the motion works
        return self.get_cannon_pinion_total_height() - self.inset_at_base

    def calc_bearing_holder_thick(self):

        if self.bearing is not None:
            if self.bearing.outerD > self.pairs[0].pinion.getMinRadius()*2 - 1:
                #this bearing won't fit inside the cannon pinion
                self.bearingHolderThick = self.bearing.height
                if self.compact:
                    self.bearingHolderThick += 1
            else:
                self.bearingHolderThick = 0
            #we're big enough with the bearings, try to reduce size where we can
            self.wallThick = 1.2
        else:
            self.bearingHolderThick = 0
        self.cannonPinionBaseHeight = self.cannonPinionPinionThick + self.pinionCapThick * 2 + self.bearingHolderThick

    def calculateGears(self, arbourDistance=-1):
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
        if arbourDistance < 0:
            self.arbourDistance = self.module * (wheel0_teeth + pinion0_teeth) / 2
        else:
            if aim_for_module_size:
                pinion_min = 10
                pinion_max = 30
                wheel_min = 20
                wheel_max = 200

                options = []

                for p0 in range(pinion_min, pinion_max):
                    print("{:.1f}% calculating motion works gears".format(100*(p0 - pinion_min)/(pinion_max-pinion_min)))
                    for w0 in range(wheel_min, wheel_max):
                        for p1 in range(pinion_min, pinion_max):
                            for w1 in range(wheel_min, wheel_max):

                                ratio = (w1/p1) * (w0/p0)#1/((p0/w0)*(p1/w1))

                                if (w1 * w0) % (p1 * p0) != 0:
                                    continue
                                if ratio != 12:
                                    continue




                                module0 = arbourDistance / ((w0 + p0) / 2)
                                module1 = arbourDistance / ((w1 + p1) / 2)

                                min_cannon_pinion_r = 0

                                if self.bearing is not None:
                                    min_cannon_pinion_r = self.bearing.outerD/2
                                if self.inset_at_base > 0:
                                    min_cannon_pinion_r = self.inset_at_base_r

                                #v.slow
                                potential_pair = WheelPinionPair(w0, p0, module0, looseArbours=self.compensateLooseArbour)
                                if min_cannon_pinion_r > potential_pair.pinion.getMinRadius() - 0.9:
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
                self.arbourDistance = arbourDistance
                wheel0_teeth, pinion0_teeth, wheel1_teeth, pinion1_teeth = options[0]["teeth"]

                # if self.bearing is not None and pinion0_teeth < pinion1_teeth:
                #     #try and ensure enough space for the bearing
                #     old0 = pinion0_teeth
                #     pinion0_teeth = pinion1_teeth
                #     pinion1_teeth = old0


            else:
                self.module = arbourDistance / ((wheel0_teeth + pinion0_teeth) / 2)
                self.arbourDistance = arbourDistance
        secondModule = 2 * self.arbourDistance / (wheel1_teeth + pinion1_teeth)
        print("Motion works module0: {}, module1: {}. wheel0_teeth {}, pinion0_teeth {}, wheel1_teeth {}, pinion1_teeth {}".format(self.module, secondModule,wheel0_teeth, pinion0_teeth, wheel1_teeth, pinion1_teeth))
        self.pairs = [WheelPinionPair(wheel0_teeth, pinion0_teeth, self.module, looseArbours=self.compensateLooseArbour), WheelPinionPair(wheel1_teeth, pinion1_teeth, secondModule, looseArbours=self.compensateLooseArbour)]


        self.calc_bearing_holder_thick()

    def getAssembled(self, motionWorksRelativePos=None,minuteAngle=10):
        if motionWorksRelativePos is None:
            motionWorksRelativePos = [0, self.getArbourDistance()]

        motionWorksModel = self.getCannonPinion().rotate((0, 0, 0), (0, 0, 1), minuteAngle)
        motionWorksModel = motionWorksModel.add(self.getHourHolder().translate((0, 0, self.getCannonPinionBaseThick())))
        motionWorksModel = motionWorksModel.add(self.getMotionArbourShape().translate((motionWorksRelativePos[0], motionWorksRelativePos[1], (self.getCannonPinionBaseThick()-self.bearingHolderThick) / 2 +self.bearingHolderThick- self.thick/2)))

        if self.centred_second_hand:
            relative_pos = npToSet(np.multiply(motionWorksRelativePos,2))
            motionWorksModel = motionWorksModel.add(self.getCannonPinionPinion(standalone=True).translate(relative_pos))

        return motionWorksModel

    def getHourHandHoleD(self):
        '''
        get the size of the hole needed for the hand to slot onto the hour hand holder
        '''
        return self.hourHandHolderD

    def getMinuteHandSquareSize(self):
        '''
        Get the size of the square needed for the hand to slot onto the cannon pinion
        '''
        return self.minuteHandHolderSize + 0.2

    def getArbourDistance(self):
        return self.arbourDistance

    def getHourHolderMaxRadius(self):
        return self.pairs[1].wheel.getMaxRadius()

    def getArbourMaxRadius(self):
        return self.pairs[0].wheel.getMaxRadius()

    def getHandHolderHeight(self):
        '''
        get distance from base of the cannon pinion to the beginning of the hand holders (base of hour hand)
        '''
        return self.get_cannon_pinion_total_height() - (self.minuteHandSlotHeight + self.space + self.hourHandSlotHeight)

    def getCannonPinionBaseThick(self):
        '''
        get the thickness of the pinion + caps at the bottom of the cannon pinion ( and bearing holder)

        '''

        thick = self.pinionCapThick * 2 + self.cannonPinionPinionThick + self.bearingHolderThick


        return thick

    def getCannonPinionPinionThick(self):
        return self.getCannonPinionBaseThick() + self.knob_thick

    def getCannonPinionPinion(self, with_snail=False, standalone=False, for_printing=True):
        '''
        For the centred seconds hands I'm driving the motion works arbour from the minute arbour. To keep the gearing correct, use the same pinion as the cannon pinion!
        if standalone, this is for the centred seconds hands where we're driving the motion works arbour from the minute wheel
        '''

        pinion_max_r = self.pairs[0].pinion.getMaxRadius()

        base = cq.Workplane("XY")

        if self.strikeTrigger is not None:
            base = self.strikeTrigger.get2D().extrude(self.pinionCapThick).rotate((0, 0, 0), (0, 0, 1), self.strikeHourAngleDeg).faces(">Z").workplane()

        if self.pinionCapThick > 0:
            base = base.circle(pinion_max_r).extrude(self.pinionCapThick)

        base = base.union(self.pairs[0].pinion.get2D().extrude(self.cannonPinionPinionThick).translate((0, 0, self.pinionCapThick)))

        if self.pinionCapThick > 0:
            base = base.union(cq.Workplane("XY").circle(pinion_max_r).extrude(self.pinionCapThick).translate((0, 0, self.pinionCapThick + self.cannonPinionPinionThick)))

        pinion = base

        if standalone:

            #add hand-grippy thing to allow setting the time easily
            inner_r = pinion_max_r
            outer_r = inner_r*1.5

            knob = get_smooth_knob_2d(inner_r, outer_r, knobs=6).extrude(self.knob_thick)

            pinion = pinion.union(knob.translate((0,0,self.pinionCapThick + self.cannonPinionPinionThick)))

            # cut hole to slot onto arbour
            pinion = pinion.cut(cq.Workplane("XY").circle((self.arbourD + LOOSE_FIT_ON_ROD) / 2).extrude(10000))



        return pinion

    def getCannonPinionPinionSTLModifier(self):

        return self.pairs[0].pinion.getSTLModifierShape(thick=self.cannonPinionPinionThick, offset_z=self.pinionCapThick)


    def getCannonPinion(self):

        pinion_max_r = self.pairs[0].pinion.getMaxRadius()

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

        pinion = self.getCannonPinionPinion(with_snail=True)

        if self.bearing is not None and self.bearingHolderThick > 0:
            # extend out the bottom for space for a slot on the bottom
            pinion = pinion.translate((0, 0, self.bearingHolderThick))
            pinion = pinion.union(cq.Workplane("XY").circle(pinion_max_r).extrude(self.bearingHolderThick))

        # has an arm to hold the minute hand
        pinion = pinion.union(cq.Workplane("XY").circle(self.minuteHandHolderD / 2).extrude(self.cannonPinionTotalHeightAboveBase - self.minuteHandSlotHeight).translate((0, 0, self.cannonPinionBaseHeight)))


        if self.minuteHandHolderIsSquare:
            pinion = pinion.union(cq.Workplane("XY").rect(self.minuteHandHolderSize,self.minuteHandHolderSize).extrude(self.minuteHandSlotHeight).translate((0, 0, self.get_cannon_pinion_total_height() - self.minuteHandSlotHeight)))
        else:

            holder_r = self.minuteHandHolderSize / 2
            # minute holder is -0.2 and is pretty snug, but this needs to be really snug
            # -0.1 almost works but is still a tiny tiny bit loose (with amazon blue PETG, wonder if that makes a difference?)
            # NEW IDEA - keep the tapered shape, but make it more subtle and also keep the new hard stop at the end
            #INFO - HANDS ADD 0.2 TO THIS for the hole in the hand
            holderR_base = self.minuteHandHolderSize / 2 + 0.05
            holderR_top = self.minuteHandHolderSize / 2 - 0.15

            circle = cq.Workplane("XY").circle(holder_r)
            holder = cq.Workplane("XZ").lineTo(holderR_base, 0).lineTo(holderR_top, self.minuteHandSlotHeight).lineTo(0, self.minuteHandSlotHeight).close().sweep(circle)#.translate((0, 0, self.thick))
            holder = holder.translate((0, 0, self.get_cannon_pinion_total_height() - self.minuteHandSlotHeight))

            pinion = pinion.union(holder)

        pinion = pinion.cut(cq.Workplane("XY").circle(self.holeD/2).extrude(self.get_cannon_pinion_total_height()))


        if self.bearing is not None:
            #slot for bearing on top
            pinion = pinion.cut(cq.Workplane("XY").circle(self.bearing.outerD / 2).extrude(self.bearing.height).translate((0, 0, self.get_cannon_pinion_total_height() - self.bearing.height)))


            pinion = pinion.cut(getHoleWithHole(innerD=self.holeD, outerD=self.bearing.outerD, deep=self.bearing.height + self.inset_at_base))

        elif self.inset_at_base > 0:
            # cut out space for the nuts/bearing to go further into the cannon pinion, so it can be closer to the front plate
            # pinion = pinion.cut(cq.Workplane("XY").circle(self.inset_at_base_r).extrude(self.inset_at_base))
            pinion = pinion.cut(getHoleWithHole(innerD=self.holeD, outerD=self.inset_at_base_r*2, deep=self.inset_at_base))

        return pinion

    def getMotionArbour(self):
        # mini arbour that sits between the cannon pinion and the hour wheel
        #this is an actual Arbour object
        wheel = self.pairs[0].wheel
        pinion = self.pairs[1].pinion

        #add pinioncap thick so that both wheels are roughly centred on both pinion (look at the assembled preview)
        return Arbour(wheel=wheel, pinion=pinion, arbourD=self.arbourD + LOOSE_FIT_ON_ROD_MOTION_WORKS, wheelThick=self.thick, pinionThick=self.pinionThick + self.pinionCapThick, endCapThick=self.pinionCapThick, style=self.style, clockwise_from_pinion_side=False)

    def getMotionArboutPinionSTLModifier(self):
        return self.pairs[1].pinion.getSTLModifierShape(thick=self.pinionThick + self.pinionCapThick, offset_z=self.thick)

    def getMotionArbourShape(self):
        #mini arbour that sits between the cannon pinion and the hour wheel
        return self.getMotionArbour().getShape()
    def getHourHolder(self):
        #the final wheel and arm that friction holds the hour hand
        #this used to be excessively tapered, but now a lightly tapered friction fit slot.
        style=self.style
        # if self.snail is not None:
        #     style = None

        #fiddled the numbers so that fill isn't required to print
        bottomR = self.hourHandHolderD / 2 + 0.7

        #minute holder is -0.2 and is pretty snug, but this needs to be really snug
        #-0.1 almost works but is still a tiny tiny bit loose (with amazon blue PETG, wonder if that makes a difference?)
        # NEW IDEA - keep the tapered shape, but make it more subtle and also keep the new hard stop at the end
        holderR_base = self.hourHandHolderD / 2 + 0.1
        holderR_top = self.hourHandHolderD / 2 - 0.2

        hour = self.pairs[1].wheel.get3D(holeD=self.holeD,thick=self.thick,style=style, innerRadiusForStyle=bottomR, clockwise_from_pinion_side=True)

        if self.snail is not None:
            hour = hour.add(self.snail.get3D(self.thick))

        top_z = self.get_cannon_pinion_total_height() - self.space - self.minuteHandSlotHeight - self.cannonPinionBaseHeight

        # hour = hour.faces(">Z").workplane().circle(self.hourHandHolderD/2).extrude(height)

        handHolderStartZ = top_z - self.hourHandSlotHeight

        if handHolderStartZ < 0.0001:
            #because CQ won't let you make shapes of zero height
            handHolderStartZ = 0.0001

        holeR = self.minuteHandHolderD / 2 + self.space / 2

        # return hour
        circle = cq.Workplane("XY").circle(bottomR)
        shape = cq.Workplane("XZ").moveTo(bottomR,self.thick).lineTo(bottomR,handHolderStartZ).lineTo(holderR_base,handHolderStartZ).lineTo(holderR_top,top_z).lineTo(holeR,top_z).lineTo(holeR,self.thick).close().sweep(circle)

        hour = hour.add(shape)

        hole = cq.Workplane("XY").circle(holeR).extrude(self.get_cannon_pinion_total_height())
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
        exporters.export(self.getMotionArbourShape(), out)

        out = os.path.join(path, "{}_motion_arbour_pinion_modifier.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getMotionArbour().getSTLModifierPinionShape(), out)

        #only needed for prototype with centred seconds hand
        out = os.path.join(path, "{}_motion_cannon_pinion_pinion_standalone.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getCannonPinionPinion(standalone=True), out)

        out = os.path.join(path, "{}_motion_cannon_pinion_modifier.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getCannonPinionPinionSTLModifier(), out)

        out = os.path.join(path, "{}_motion_arbour_pinion_modifier.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getMotionArboutPinionSTLModifier(), out)

        out = os.path.join(path, "{}_motion_hour_holder.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHourHolder(), out)
