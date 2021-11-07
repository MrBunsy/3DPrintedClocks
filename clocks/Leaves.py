import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
import random
import numpy as np

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass

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

class CustomLeafPoint:
    def __init__(self, pos, bendInwards=False,bendyness=0.2):
        self.pos=pos
        self.bendInwards=bendInwards
        self.bendyness=bendyness

def customLeaf(length=70):
    '''
    Leaf with predefined points
    (0,0) is always the bit where the leaf would join a stem
    '''

    leftPoints = []

# leaf = maple2(55,withHoleD=2.5)
# leaf_small = maple2(45,withHoleD=3)
crown_leaf2 = maple2(60,2)

# exporters.export(leaf_small, "out/cuckoo_pendulum_leaf_fortoy_small.stl", tolerance=0.001, angularTolerance=0.01)

# if __name__ == "__main__":
#
#     leaf = maple2(55)
#
#     show_object(leaf)
#
#     exporters.export(leaf, "out/cuckoo_pendulum_leaf2.stl", tolerance=0.001, angularTolerance=0.01)