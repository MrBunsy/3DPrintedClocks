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
import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
import random
import numpy as np

from .utility import *

# if 'show_object' not in globals():
#     def show_object(*args, **kwargs):
#         pass

'''
Plan is for a procedularily generated maple leaf, for use on pendulums or decoration of cuckoo clocks!
'''
def length(v1,v2=None):
    if v2 is None:
        return math.sqrt(math.pow(v1[0],2) + math.pow(v1[1],2))
    return math.sqrt(math.pow(v1[0] - v2[0], 2) + math.pow(v1[1] - v2[1], 2))

def maple(size=40, seed=5):
    random.seed(seed)
    points = random.randint(3,5)
    leaf = cq.Workplane("XY").tag("base")
    print("points: {}".format(points))

    #(xPos, yPos, centreX for the angle that created this point, angle)
    tips = []
    inners = []

    angleOffset = 2

    #generate points for tips of leaves and inner bits of leaves
    for i in range(points):
        tipAngle = (i+1 + angleOffset)*2*math.pi/((points+angleOffset)*2)
        innerAngle = (i + angleOffset)*2*math.pi/((points+angleOffset)*2)

        tipR = size*tipAngle/math.pi
        innerR = size*(innerAngle)/math.pi*(points-i+10)/(points+10)*0.85
        tipR*=random.uniform(0.8,1)
        innerR*=random.uniform(0.7,1)
        innerR = tipR*random.uniform(0.5,0.7)

        centreX = -i*0.3*size/points
        centreY = 0

        tipPos = (math.cos(tipAngle)*tipR + centreX, math.sin(tipAngle)*tipR + centreY, centreX, tipAngle)

        tips.append(tipPos)

        innerPos = (math.cos(innerAngle)*innerR + centreX, math.sin(innerAngle)*innerR + centreY, centreX, innerAngle)

        inners.append(innerPos)

    leaf.moveTo(inners[0][0], inners[0][1])

    for i, tip in enumerate(tips):
        if i > 0:
            if False:
                leaf = leaf.lineTo(inners[i][0],inners[i][1])
            else:
                centreX = (inners[i-1][2]+tip[2])/2
                avgR = (length(inners[i-1], (centreX,0)) + length(tip, (tip[2], 0)))/2
                avgAngle = (inners[i-1][3] + tip[3])/2 - (math.pi/points)*0.1

                mid = (math.cos(avgAngle)*avgR + centreX, math.sin(avgAngle)*avgR)
                leaf = leaf.spline([mid, (inners[i][0], inners[i][1])], includeCurrent=True)


        if False:
            leaf = leaf.lineTo(tip[0], tip[1])
        else:
            centreX = (inners[i][2] + tip[2]) / 2
            avgR = (length(inners[i], (centreX, 0)) + length(tip, (tip[2], 0))) / 2

            sign = 1 if i >0 else 0

            avgAngle = (inners[i][3] + tip[3]) / 2 + sign*(math.pi / points) * 0.1

            mid = (math.cos(avgAngle) * avgR + centreX, math.sin(avgAngle) * avgR)
            leaf = leaf.spline([mid, (tip[0], tip[1])], includeCurrent=True)


    leaf = leaf.mirrorX()
    # return leaf
    leaf = leaf.extrude(10)


    centreX = (tips[0][0] + tips[-1][0])/2

    bowl = cq.Workplane("XY").sphere(size*2).translate((centreX,0,-size*1.8))
    cube = cq.Workplane("XY").rect(size*3,size*3).extrude(size*2)
    mould = cube.cut(bowl)

    #cut the top of the leaf into a rounded shape
    return leaf.cut(mould)

class LeafPoint():

    def __init__(self, r, angle, inwardness=0.2, centre=None, bendinessOut=0.2,bendinessIn=0.025):
        '''
        represents a point on the outisde of a leaf
        :param r: radius from centre
        :param angle: angle from centre
        :param inwardness: how far (as proportion of distance from this outer point to hte next) to put the 'inner point' towards to centre
        :param centre: [x,y]
        :param bendinessOut: how bendy the line should be from the new inner point to the next outer point
        :param bendinessIn: how bendy the line should be from this outer point to the new inner point
        '''
        self.centre=[0,0] if centre is None else centre
        self.r=r
        self.angle=angle
        self.inwardness=inwardness
        self.bendinessOut=bendinessOut
        self.bendinessIn=bendinessIn

    def getPos(self):
        return [self.centre[0] + math.cos(self.angle)*self.r, self.centre[1] + math.sin(self.angle)*self.r]

    def __str__(self):
        return "centre: {}, r:{}, angle:{}".format(self.centre, self.r,round(180*self.angle/math.pi))

def bendyLineBetween(shape,a,b,centre,bendTowardsCentre=True, bendMultiplier=0.2, nearerA=0.5, heightStart=0, heightMid=0, heightEnd=0):
    # shape = shape.lineTo(b[0],b[1])
    shape.moveTo(a[0], a[1])



    line = np.subtract(b,a)
    line_length = np.linalg.norm(line)

    line_unit = np.divide(line, line_length)

    # mid = np.divide(np.add(a, b), 2)
    mid = np.add(a, np.multiply(line_unit, line_length*nearerA))
    midToCentre = np.subtract(centre, mid)

    length = np.linalg.norm(line)

    n = np.cross(line, [0,0,1])
    n = [n[0], n[1]]
    dot = np.dot(midToCentre, n)
    if dot < 0 and bendTowardsCentre:
        n = np.multiply(n, -1)

    #make unit vector
    n = np.divide(n, np.linalg.norm(n))

    bendPoint = np.add(mid, np.multiply(n, length*bendMultiplier))

    shape = shape.spline([(a[0], a[1], heightStart),(bendPoint[0], bendPoint[1],heightMid), (b[0], b[1], heightEnd)])

    return shape

def maple2(length = 70, shape=1, cuts=2, withHoleD=0):
    '''
    [0,0] = bit of leaf that would attach to a stalk, tip pointing upwards (+ve y)
    currently symetric around y axis
    :return:
    '''
    points = []
    symetric=True

    if shape == 1:
        #intended to go on a pendulum - loosely styled off a small green pendulum I have
        points = [LeafPoint(length*0.1,-math.pi/2,0.2,[0,length*0.1])]

        widePoints = 3
        tipPoints = 0
        wideCentre = [0,length*(6/16)]

        points.append(LeafPoint(length*0.5, -math.pi*0.25, 0.25, wideCentre, 0.2))
        points.append(LeafPoint(length * 0.5, 0, 0.4, wideCentre,0.1))
        points.append(LeafPoint(length * (5.5/16), math.pi*0.1, 0.2, wideCentre, 0.1))
        points.append(LeafPoint(length * (5.5 / 16), math.pi *0.25, 0.25, [0,length*(8/16)],0.1))
        # currently at the tip so we can be symmetrical, but doesn't need to be if we stop symmetry
        points.append(LeafPoint(length * 0.1, math.pi / 2, 0.2, [0, length * 0.9]))
    elif shape == 2:
        topCentre=[0,length*3/14]
        midCentre = [0, length * 4 / 14]
        bottomCentre=[0,length*0.45]
        '''intended to go on a top crown'''
        points.append(LeafPoint(length*0.1,-math.pi/2,0.2,[0,length*0.1], 0.05))
        points.append(LeafPoint(length*(6/14), -math.pi*0.25,0.3, topCentre,0.11,-0.1))
        points.append(LeafPoint(length * (6 / 14), 0, 0.2, topCentre,0.15))
        points.append(LeafPoint(length * (7 / 14), math.pi*0.1, 0.4, midCentre,0.1,-0.1))
        points.append(LeafPoint(length * (4.5 / 14), 0, 0.2, bottomCentre,0.1))
        points.append(LeafPoint(length * 0.25, math.pi * 0.1, 0.3, [0,length*0.65],0.1))
        points.append(LeafPoint(length*0.5, math.pi * 0.5, 0.2, bottomCentre))

    # #points at the wide bit of the leaf
    # for i in range(widePoints):
    #     r=length*0.5
    #     fromA = -math.pi*0.3
    #     toA = math.pi*0.3
    #
    #     a = fromA +  i*(toA - fromA)/(widePoints-1)
    #
    #     points.append(LeafPoint(r,a, wideCentre))

    # tipCentre = [0, length*0.75]
    # #points at the narrow bit of the leaf
    # for i in range(tipPoints):
    #     r=length*0.3
    #     fromA = -math.pi * 0.1
    #     toA = math.pi * 0.2
    #     a = fromA +  i*(toA - fromA)/(max(tipPoints-1,1))
    #
    #     points.append(LeafPoint(r,a, 0.2, tipCentre))



    for point in points:
        print(point)

    leaf = cq.Workplane("XY").tag("base")
    # leaf = leaf.lineTo(points[1].getPos()[0], points[1].getPos()[1])
    leaf = bendyLineBetween(leaf, points[0].getPos(), points[1].getPos(), [0,length*0.5], False, points[0].bendinessOut)

    leafCentre = [0,length/2]

    for i in range(1,len(points)-1):
        print(i)
        if False:
            leaf = leaf.lineTo(points[i+1].getPos()[0],points[i+1].getPos()[1])
        else:
            start = points[i]
            startPos = start.getPos()
            end = points[i+1]

            pointToCentre = np.subtract(start.centre, startPos)

            innerPoint = np.add(startPos, np.multiply(pointToCentre, start.inwardness))

            leaf = bendyLineBetween(leaf, startPos, innerPoint, start.centre, True, start.bendinessIn)
            leaf = bendyLineBetween(leaf, innerPoint, end.getPos(), start.centre, False, start.bendinessOut)


    thick=(13/70)*length

    #thick = thick*0.75

    leaf = leaf.mirrorY()
    # return leaf
    leaf = leaf.extrude(thick)

    # return leaf

    #the cutters need work - they currently only function on a leaf of length 70
    cutters=[]

    cutter = cq.Workplane("XZ").tag("base")

    if cuts == 1:
        angle = 0
        for a in [40,60,80]:
            cutter = cq.Workplane("XZ").moveTo(-thick*2,0).lineTo(0,-thick*2).lineTo(thick*2,0).close().twistExtrude(-length,a).rotate((0,0,0),(0,0,1),angle).translate([0,0,thick*2 + thick*0.5])
            cutters.append(cutter)
            angle+=15
    elif cuts == 2:

        startHeight=thick*0.55
        midHeight=thick*0.6
        endHeight=thick*0.675

        startPos=[0,length*0]

        for point in points:
            # if point == points[-1]:
            #     startPos=[0,length*0.1]
            print(point.getPos())
            cutter = cq.Workplane("XZ").transformed(offset=[0,0,-startPos[1]]).move(-thick * 1, thick * 2.5).lineTo(0, startHeight).lineTo(thick * 1, thick * 2.5).close()
            # cutter = cutter.workplaneFromTagged("base").moveTo(-thick * 2, thick * 2.5).lineTo(0, startHeight).lineTo(thick * 2, thick * 2.5).close()

            # path = cq.Workplane("XY").moveTo(startPos[0],startPos[1]).spline([(startPos[0],startPos[1],startHeight),(length*0.1,length*0.5,midHeight), (length,length,endHeight)])

            bend=0.05
            if point == points[-1]:
                bend=0
            path = bendyLineBetween(cq.Workplane("XY"), startPos, point.getPos(), [0,length], True, bend, heightStart=startHeight, heightMid=midHeight, heightEnd=endHeight)
            # return path
            cutter = cutter.sweep(path)
            cutters.append(cutter)
            if point != points[-1]:
                cutters.append(cutter.mirror("ZY"))
        # return cutter

    # return cutters
    # return cutter
    # return allCutters


    size = length
    centreX = leafCentre[0]

    bowl = cq.Workplane("XY").sphere(size * 2).translate((0, leafCentre[1], -length*1.85))
    # return bowl
    cube = cq.Workplane("XY").rect(size * 3, size * 3).extrude(size * 2)
    mould = cube.cut(bowl)

    # cut the top of the leaf into a rounded shape
    leaf = leaf.cut(mould)

    #cut some patterns out as well
    # if len(cutters) > 1:
    #     allCutters = cutters[0]
    #     for a in range(1, len(cutters)):
    #         allCutters = allCutters.union(cutters[a])
    #
    #     # allCutters = allCutters.union(allCutters.mirror(mirrorPlane="YZ"))
    # elif len(cutters) == 1:
    #     allCutters=cutters[0]

    #for some reason the cutter isn't a shape, so fetch the shape from teh shape. Wish I understnd wtf was going on here
    allCutters = cq.Compound.makeCompound([c.objects[0] for c in cutters])

    # return allCutters
    # return cutters
    # for cutter in cutters:
    #     leaf = leaf.cut(cutter)

    leaf = leaf.cut(allCutters)
    # leaf = leaf.union(allCutters)
    # leaf = leaf.add(allCutters)

    if withHoleD > 0:
        #punch a hole down the centre (lengthways)
        z = withHoleD
        if withHoleD > 2.5:
            z = withHoleD*0.75
        hole = cq.Workplane("XZ").circle(withHoleD/2).extrude(length*4).translate([0,length*2,z])
        leaf = leaf.cut(hole)

    return leaf

def bendyLineBetween2(shape,a,b,bendMultiplier=0.2, nearerA=0.5, startZ=0, midZ = 0, endZ = 0):
    '''
    if bendMultiplier +ve, bend will be towards a point clockwise from first point
    '''

    # shape = shape.lineTo(b[0],b[1])
    shape.moveTo(a[0], a[1])

    line = np.subtract(b,a)
    line_length = np.linalg.norm(line)
    line_unit = np.divide(line, line_length)

    # mid = np.divide(np.add(a, b), 2)
    mid = np.add(a, np.multiply(line_unit, line_length*nearerA))

    length = np.linalg.norm(line)

    n = np.cross(line_unit, [0,0,1])
    n = [n[0], n[1]]
    # dot = np.dot(midToCentre, n)
    # if dot < 0 and bendTowardsCentre:
    #     n = np.multiply(n, -1)

    #make unit vector
    # n = np.divide(n, np.linalg.norm(n))

    bendPoint = np.add(mid, np.multiply(n, length*bendMultiplier))

    shape = shape.spline([(a[0], a[1], startZ),(bendPoint[0], bendPoint[1], midZ), (b[0], b[1], endZ)])

    return shape

class CustomLeafPoint:
    def __init__(self, pos,bendyness=0.2):
        #as fraction of length
        self.pos=pos
        # self.bendInwards=bendInwards# bendInwards=False,
        #from the previous point, +ve is bending outwards, -ve bending inwards
        self.bendyness=bendyness

def customLeaf(length=70, thick=10, shape="bowl", cut=True):
    '''
    shape wobble or bowl

    Leaf with predefined points
    (0,0) is always the bit where the leaf would join a stem
    (0,length) is aproximately the tip of the leaf
    '''

    #this is for decoration on a cuckoo case, for one of the two small broken cuckoos
    tipPos = [-0.75/14,1]
    rightPoints = [
        #RHS
        CustomLeafPoint([4 / 14, -2.25 / 14], -0.03),
        CustomLeafPoint([3.5 / 14, 0.5 / 14], 0.1),
        CustomLeafPoint([6.5 / 14, 2.75 / 14], 0.075),
        CustomLeafPoint([5.25 / 14, 3 / 14], -0.025),
        CustomLeafPoint([7 / 14, 6.5 / 14], 0.1),
        CustomLeafPoint([4 / 14, 6 / 14], -0.075),
        CustomLeafPoint([4.75 / 14, 7.5 / 14], 0.1),
        CustomLeafPoint([3.2 / 14, 7.25 / 14], -0.01),
        CustomLeafPoint([3.5 / 14, 9.8 / 14], 0.05),
        CustomLeafPoint([2.5 / 14, 9.5 / 14], -0.025),
        #Tip
        CustomLeafPoint(tipPos,0.1)
    ]

    #temp, mirror
    # leftPoints= [CustomLeafPoint([-p.pos[0],p.pos[1],p.bendyness]) for i,p in enumerate(reversed(points[:-1])]

    mirror = True
    lastBendiness=0
    leftPoints = []
    if mirror:
        for i,point in enumerate(reversed(rightPoints)):
            if i > 0:
                leftPoints.append(CustomLeafPoint([-point.pos[0], point.pos[1]], lastBendiness))

            lastBendiness = point.bendyness

    if mirror and tipPos[0] != 0:
        leftPoints[0].bendyness*=-0.5

    leftPoints.append(CustomLeafPoint([0,0], lastBendiness))

    points = rightPoints + leftPoints
    # leftPoints.append(CustomLeafPoint(tipPos,-0.1))

    leaf = cq.Workplane("XY")

    leaf = leaf.moveTo(0,0)
    lastPos = [0,0]
    for point in points:

        currentPos = [point.pos[0]*length, point.pos[1]*length]
        print("from {} to {}".format(lastPos, currentPos))
        leaf = bendyLineBetween2(leaf, lastPos, currentPos , point.bendyness)
        # leaf = leaf.lineTo(currentPos[0], currentPos[1])
        lastPos = currentPos

    leaf = leaf.close().extrude(thick)


    bowl = cq.Workplane("XY").sphere(length * 2).translate((0, length*0.4, -length * (1 +  (1- (thick/length))  )))
    cube = cq.Workplane("XY").rect(length * 3, length * 3).extrude(length * 2)
    mould = cube.cut(bowl)

    # cut the top of the leaf into a rounded shape
    leaf = leaf.cut(mould)

    startHeight = thick * 0.85
    midHeight = thick * 0.7
    endHeight = thick * 1
    if cut:
        startPos = [0, length * 0.1]
        cutters=[]

        skip = 2
        # offset = 1

        for i in range(0,len(points[:]),skip):
            point = points[i]
            cutter = cq.Workplane("XZ").transformed(offset=(0, 0, -startPos[1])).move(-thick * 0.5, thick * 2.5).lineTo(0, startHeight).lineTo(thick * 0.5, thick * 2.5).close()
            # return cutter
            bend = 0.05
            if  i < (len(points)/2) -1:#/skip:
                bend = -0.05

            # bend = 0
            try:
                # path = cq.Workplane("XY").moveTo(startPos[0],startPos[1]).lineTo(point.pos[0]*length, point.pos[1]*length)
                endPoint = np.multiply(point.pos, length)
                #
                # halfPoint = np.add(startPos, np.multiply(np.subtract(endPoint, startPos),0.5))
                # path = cq.Workplane("XY").spline([(startPos[0],startPos[1], startHeight), (halfPoint[0],halfPoint[1], midHeight), (endPoint[0], endPoint[1], endHeight)])
                path = bendyLineBetween2(cq.Workplane("XY"),startPos, endPoint, bendMultiplier=bend, startZ=startHeight, midZ=midHeight, endZ=endHeight)

                # path = bendyLineBetween(cq.Workplane("XY"), startPos, [point.pos[0]*length, points.pos[1]*length], [0, length], True, bend, heightStart=startHeight, heightMid=midHeight, heightEnd=endHeight)
                # # return path
                cutter = cutter.sweep(path)
                # return cutter
                cutters.append(cutter)
                # if point != points[-1]:
                #     cutters.append(cutter.mirror("ZY"))
                # return cutter
            except:
                '''
                '''
                print("failed")

        # for some reason the cutter isn't a shape, so fetch the shape from teh shape. Wish I understnd wtf was going on here
        # allCutters = cq.Compound.makeCompound([c.objects[0] for c in cutters])
        allCutters=cutters[0]

        for c in cutters[1:]:
            allCutters.add(c)

        # return allCutters
        # return cutters
        # for cutter in cutters:
        #     leaf = leaf.cut(cutter)

        leaf = leaf.cut(allCutters)
        # leaf = leaf.cut(cutters[0])


    return leaf


def toyPendulumBob(diameter=30, thick=7.5, withHoleD=2):
    '''
    a leaf on a circle
    '''

    inner_thick=thick*0.75
    thick_diff = thick-inner_thick

    # bob=cq.Workplane("XY")
    # bob=bob.circle(diameter/2).extrude(inner_thick)
    r = diameter/2
    circle = cq.Workplane("XY").circle(r)
    bob = cq.Workplane("XZ").moveTo(0, 0).lineTo(r, 0).line(0, inner_thick).tangentArcPoint((r - thick_diff, thick), relative=False).\
        tangentArcPoint((r - thick_diff*2, inner_thick), relative=False).lineTo(0,inner_thick).close().sweep(circle)

    leafLength=diameter*0.5

    leaf = customLeaf(length=leafLength, thick=3, cut=False).translate([0,-leafLength*0.4,inner_thick])

    bob = bob.add(leaf)


    if withHoleD > 0:
        #punch a hole down the centre (lengthways)
        z = thick/2
        if z < withHoleD:
            z = withHoleD*0.75
        hole = cq.Workplane("XZ").circle(withHoleD/2).extrude(diameter*4).translate([0,diameter*2,z])
        bob = bob.cut(hole)

    return bob


class HollyLeaf:
    '''
    A randomly generated holly leaf. currently only a 2D outline
    '''
    def __init__(self, length=40, seed=-1):
        if seed >=0:
            random.seed(seed)
        self.length = length
        self.width = length*random.uniform(0.6, 0.7)
        self.spikes = random.randint(4,6)

        #if we imagine the spikes of the leaf as being on a circle centred off to one side
        #this is a circle of radius r, calculated by a sagitta of our choosing, s.
        #the centre of the circle is therefore off to one side by r-s
        #with the help of wiki:
        s = self.width*random.uniform(0.4, 0.6)
        l = self.length
        self.edge_circle_r = s/2 + (l**2)/(8*s)
        self.edge_circle_offset = self.edge_circle_r - s
        self.edge_arc_angle = 2 * math.asin(l/(2*self.edge_circle_r))
        self.spike_angle = self.edge_arc_angle / (self.spikes + 1)
        self.spike_sagitta = 0.15* self.length / self.spikes

    def get_2d(self):
        leaf = cq.Workplane("XY")


        # cq.Workplane("XZ").circle(withHoleD / 2).sagittaArc()


        top_angle = math.pi/2 - (math.pi - self.edge_arc_angle)/2
        angle = top_angle
        leaf = leaf.moveTo(0,self.length)

        centre = (0, self.length/2)
        circle_centre = (centre[0] - self.edge_circle_offset, centre[1])
        spike_points_RHS = []
        for i in range(self.spikes):
            #RHS
            angle = top_angle - i * self.spike_angle
            next_angle = top_angle - (i+1) * self.spike_angle
            spike_pos = np_to_set(np.add(circle_centre, polar(next_angle, self.edge_circle_r)))
            spike_points = spike_points_RHS.append(spike_pos)


        spike_points = spike_points_RHS[:]
        spike_points.append((0,0))

        for point in reversed(spike_points_RHS):
            spike_points.append((-point[0], point[1]))

        spike_points.append((0, self.length))

        for point in spike_points:
            # print(spike_pos)
            leaf = leaf.sagittaArc(endPoint=point, sag=-self.spike_sagitta)
            # leaf = leaf.add(cq.Workplane("XY").moveTo(circle_centre[0], circle_centre[1]).lineTo(spike_pos[0], spike_pos[1]))
            # leaf = leaf.lineTo(spike_pos[0], spike_pos[1])

        leaf = leaf.close()
        # leaf = leaf.add(cq.Workplane("XY").moveTo(-self.edge_circle_offset, self.length/2).circle(self.edge_circle_r))
        # leaf = leaf.extrude(10)
        return leaf

class HollySprig:
    '''
    a 2D pair of holly leaves with a small bunch of berries, intended to be added to the top of a decorative christmas pud
    centred around the bunch of berries

    Randomly generated at object creation time, getting leaves and berries after that will always result in the same shapes
    '''
    def __init__(self, leaf_length=50, berry_diameter=8, thick=3):
        self.leaf_length = leaf_length
        self.berry_diameter = berry_diameter
        self.thick = thick
        self.leaves = self.gen_leaves()
        self.berries = self.gen_berries()

        self.leaves = self.leaves.cut(self.berries)

    def get_leaves(self):
        return self.leaves

    def get_berries(self):
        return self.berries

    def gen_leaves(self):
        leaves = cq.Workplane("XY")

        leaves = leaves.add(HollyLeaf(length=self.leaf_length).get_2d().extrude(self.thick).rotate((0,0,0), (0,0,1),-50))
        leaves = leaves.add(HollyLeaf(length=self.leaf_length).get_2d().extrude(self.thick).rotate((0, 0, 0), (0, 0, 1), 50))

        return leaves

    def gen_berries(self):
        berries = cq.Workplane("XY").tag("base")

        total_berries = 3
        berry_angle = math.pi*2/total_berries

        for berry in range(total_berries):
            angle = math.pi/2 + berry_angle*berry

            pos = polar(angle, self.berry_diameter*0.55)

            berries = berries.workplaneFromTagged("base").moveTo(pos[0], pos[1]).circle(self.berry_diameter*random.uniform(0.45,0.55)).extrude(self.thick)

        return berries



class Wreath:
    '''
    a 2D holly wreath intended to be a cosmetic addition to the hand avoider

    Randomly generated at object creation time, getting leaves and berries after that will always result in the same shapes
    '''

    def __init__(self, diameter=120, thick=5, berry_diameter=8):
        self.diameter = diameter
        self.thick = thick
        self.leaf_length = diameter*0.2
        self.leaves = [HollyLeaf(length=self.leaf_length*random.uniform(0.9, 1.1)) for i in range(30)]
        self.berry_diameter = berry_diameter
        self.leaves_shape = self.gen_leaves()
        self.berries_shape = self.gen_berries()
        self.leaves_shape = self.leaves_shape.cut(self.berries_shape)

    def get_leaves(self):
        return self.leaves_shape

    def get_berries(self):
        return self.berries_shape

    def gen_leaves(self):
        wreath = cq.Workplane("XY")

        angle = 0

        for leaf in self.leaves:
            angle += math.pi*2 / len(self.leaves)
            leaf_angle = angle + random.uniform(-math.pi*0.05, math.pi*0.05)
            pos = polar(angle, self.diameter/2)
            wreath = wreath.add(leaf.get_2d().extrude(self.thick).rotate((0,0,0), (0,0,1), radToDeg(-math.pi/2 + leaf_angle)).translate((pos[0], pos[1])))

        return wreath

    def gen_berries(self):
        angle = math.pi/2# 0.5 * math.pi * 2 / len(self.leaves)

        berries = cq.Workplane("XY")
        berry_bunches = round(len(self.leaves)/3)
        berry_arc_angle = self.berry_diameter/(self.diameter/2)
        for bunch in range(berry_bunches):
            angle += math.pi * 2 / berry_bunches
            angle_0 = angle - berry_arc_angle*random.uniform(0.4,0.5)
            angle_1 = angle + berry_arc_angle*random.uniform(0.4,0.5)

            pos_0 = polar(angle_0, self.diameter / 2 + self.berry_diameter * random.uniform(0.5, 0.6))
            pos_1 = polar(angle_1, self.diameter / 2 + self.berry_diameter * random.uniform(0.5, 0.6))
            pos_2 = polar(angle, self.diameter / 2 + self.berry_diameter * random.uniform(0.5, 0.6) + self.berry_diameter*0.75)
            positions = [pos_0, pos_1, pos_2]

            berries_in_bunch = round(random.uniform(2,3))
            for berry in range(berries_in_bunch):
                berries = berries.moveTo(positions[berry][0], positions[berry][1]).circle(self.berry_diameter*random.uniform(0.45,0.55)).extrude(self.thick)

        return berries

# leaf = maple2(55,withHoleD=2.5)
# leaf_small = maple2(45,withHoleD=3)
# crown_leaf2 = maple2(60,2)

# leaf2 = customLeaf(length=30-0.75, thick=3,cut=False)
# show_object(leaf2)

# bob=toyPendulumBob()
# show_object(bob)
# exporters.export(bob, "../out/toy_bob_with_leaf.stl")

#exporters.export(leaf2, "../out/leaftest.stl")

# exporters.export(leaf_small, "out/cuckoo_pendulum_leaf_fortoy_small.stl", tolerance=0.001, angularTolerance=0.01)

# if __name__ == "__main__":
#
#     leaf = maple2(55)
#
#     show_object(leaf)
#
#     exporters.export(leaf, "out/cuckoo_pendulum_leaf2.stl", tolerance=0.001, angularTolerance=0.01)



class MistletoeLeaf:
    '''
    A randomly generated mistletow leaf. currently only a 2D outline
    (0,0) is at the base of the leaf, which is pointing along the y axis
    '''
    def __init__(self, length=40, seed=-1, stalk_width=-1):
        self.length = length
        if seed >=0:
            random.seed(seed)
        self.width = length * random.uniform(0.25, 0.4)
        self.stalk_width = stalk_width
        if self.stalk_width < 0:
            self.stalk_width = length* random.uniform(0.075, 0.1)
        self.tip_offset = length*0.1 * random.uniform(-0.15,0.15)
        self.stalk_length = length * random.uniform(0.075,0.1)

    def get_2d(self):
        leaf = cq.Workplane("XY")

        leaf = leaf.lineTo(self.stalk_width/2,0).line(0,self.stalk_length).spline([(self.width/2, self.length/2+self.stalk_length), (self.tip_offset, self.length)], includeCurrent=True).\
            spline([(-self.width/2, self.length/2+self.stalk_length), (-self.stalk_width/2, self.stalk_length)], includeCurrent=True).line(0,-self.stalk_length).radiusArc((self.stalk_width/2,0), -self.stalk_width/2).close()

        return leaf

class MistletoeLeafPair:
    '''
    just two leaves at the end of a short branch

    starting at 0,0, facing along y axis
    '''
    def __init__(self, branch_length=50, leaf_length=50, seed=-1, thick=3):
        self.thick = thick
        if seed >=0:
            random.seed(seed)
        self.branch_length = branch_length
        self.branch_wonky = self.branch_length*random.uniform(-0.1, 0.1)
        self.leaf_length = leaf_length
        self.branch_thick = self.branch_length*random.uniform(0.075, 0.1)
        self.leaves = [MistletoeLeaf(length= self.leaf_length*random.uniform(0.9, 1.1), seed=random.random(), stalk_width=self.branch_thick*random.uniform(0.5,1)) for l in range(2)]
        angle = random.uniform(0.9,1.1)*math.pi/4
        spread = math.pi/10
        self.leaf_angles = [angle + random.uniform(-0.5, 0.5)*spread, (angle + random.uniform(-0.5, 0.5)*spread) - math.pi/2]

        self.branch = self.gen_branch()
        self.leaves_shape = self.gen_leaves().cut(self.branch)

    def get_branch(self):
        return self.branch

    def get_leaves(self):
        return self.leaves_shape

    def gen_branch(self):
        # branch = cq.Workplane("XY").moveTo(0, self.branch_length/2).rect(self.branch_thick, self.branch_length).extrude(self.thick)
        # branch = branch.union(cq.Workplane("XY").circle(self.branch_thick/2).extrude(self.thick))
        # branch = branch.union(cq.Workplane("XY").moveTo(0, self.branch_length).circle(self.branch_thick / 2).extrude(self.thick))


        branch = cq.Workplane("XY").moveTo(-self.branch_thick/2, 0).sagittaArc((-self.branch_thick/2, self.branch_length), self.branch_wonky)\
            .radiusArc((self.branch_thick/2, self.branch_length), 1.001*self.branch_thick/2).sagittaArc((self.branch_thick/2, 0), -self.branch_wonky).radiusArc((-self.branch_thick/2, 0), 1.001*self.branch_thick/2).close().extrude(self.thick)



        return branch

    def gen_leaves(self):
        leaves = cq.Workplane("XY")
        for i, leaf in enumerate(self.leaves):
            leaves = leaves.union(leaf.get_2d().extrude(self.thick).rotate((0,0,0), (0,0,1), radToDeg(self.leaf_angles[i])).translate((0,self.branch_length)))
            # return leaf.get_2d().extrude(self.thick)

        return leaves


class MistletoeSprig:
    def __init__(self, leaf_length=35, branch_length=50, berry_diameter=8, thick=3, seed=-1):
        self.leaf_length = leaf_length
        self.branch_length = branch_length
        self.berry_diameter = berry_diameter
        self.thick = thick

        if seed >=0:
            random.seed(seed)

        self.leaves = self.gen_leaves()
        self.berries = self.gen_berries()

        self.leaves = self.leaves.cut(self.berries)

    def get_leaves(self):
        return self.leaves

    def get_berries(self):
        return self.berries

    def gen_leaves(self):
        leaves = cq.Workplane("XY")
        self.mistletoe_leaf_pairs =[MistletoeLeafPair(branch_length=self.branch_length, leaf_length= self.leaf_length, seed=random.random(), thick=self.thick) for x in range(2)]
        angles = [-random.uniform(10,30), random.uniform(10,30)]

        for i,leaf in enumerate(self.mistletoe_leaf_pairs):
            angle = angles[i]

            leaves = leaves.union(leaf.get_leaves().rotate((0,0,0), (0,0,1), angle))
            leaves = leaves.union(leaf.get_branch().rotate((0, 0, 0), (0, 0, 1), angle))


        return leaves

    def gen_berries(self):
        berries = cq.Workplane("XY").tag("base")

        total_berries = 3
        berry_angle = math.pi*2/total_berries

        for berry in range(total_berries):
            angle = math.pi/2 + berry_angle*berry

            pos = polar(angle, self.berry_diameter*0.55)

            berries = berries.workplaneFromTagged("base").moveTo(pos[0], pos[1]).circle(self.berry_diameter*random.uniform(0.45,0.55)).extrude(self.thick)

        return berries