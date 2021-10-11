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
        represents a centre vector and a point in vector coordinates from it
        :param centre:
        :param r:
        :param angle:
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

def bendyLineBetween(shape,a,b,centre,bendTowardsCentre=True, bendMultiplier=0.2, nearerA=0.5):
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

    shape = shape.spline([bendPoint, b], includeCurrent=True)

    return shape

def maple2(length = 70):
    '''
    [0,0] = bit of leaf that would attach to a stalk, tip pointing upwards (+ve y)
    currently symetric around y axis
    :return:
    '''

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

    # #points at the wide bit of the leaf
    # for i in range(widePoints):
    #     r=length*0.5
    #     fromA = -math.pi*0.3
    #     toA = math.pi*0.3
    #
    #     a = fromA +  i*(toA - fromA)/(widePoints-1)
    #
    #     points.append(LeafPoint(r,a, wideCentre))

    tipCentre = [0, length*0.75]
    #points at the narrow bit of the leaf
    for i in range(tipPoints):
        r=length*0.3
        fromA = -math.pi * 0.1
        toA = math.pi * 0.2
        a = fromA +  i*(toA - fromA)/(max(tipPoints-1,1))

        points.append(LeafPoint(r,a, 0.2, tipCentre))



    for point in points:
        print(point)

    leaf = cq.Workplane("XY").tag("base")
    # leaf = leaf.lineTo(points[1].getPos()[0], points[1].getPos()[1])
    leaf = bendyLineBetween(leaf, points[0].getPos(), points[1].getPos(), [0,length*0.5], False)

    leafCentre = [0,length/2]

    for i in range(1,len(points)-1):
        print(i)
        if False:
            leaf = leaf.lineTo(points[i+1].getPos()[0],points[i+1].getPos()[1])
        else:
            start = points[i]
            startPos = start.getPos()
            end = points[i+1]
            endPos = end.getPos()

            midPos = np.divide(np.add(startPos, endPos),2)

            line = np.subtract(endPos, startPos)
            dist = np.linalg.norm(line)
            np.append(line, 0)
            #better than cross product and guessing clockwise/anticlockwise, go from midVec in the direction of centre
            # cross = np.cross(line, [0,0,1])
            # crossVec = [cross[0], cross[1]]
            #
            # offsetPoint = np.add(midVec,np.multiply(crossVec,-0.1))

            midToCentre = np.subtract(start.centre, midPos)
            #make unit vector
            midToCentre = np.divide(midToCentre, np.linalg.norm(midToCentre))

            #innerpoint try instead be on a straightline from the first point to the centre of the leaf
            #innerPoint = np.add(midPos,np.multiply(midToCentre, start.r*start.inwardness))

            pointToCentre = np.subtract(start.centre, startPos)

            innerPoint = np.add(startPos, np.multiply(pointToCentre, start.inwardness))

            leaf = bendyLineBetween(leaf, start.getPos(), innerPoint, start.centre, True, start.bendinessIn)
            leaf = bendyLineBetween(leaf, innerPoint, end.getPos(), start.centre, False, start.bendinessOut)

            # leaf = leaf.moveTo(start.getPos()[0],start.getPos()[1]).lineTo(end.getPos()[0],end.getPos()[1])
            # leaf = leaf.moveTo(start.getPos()[0],start.getPos()[1]).lineTo(innerPoint[0], innerPoint[1]).lineTo(end.getPos()[0],end.getPos()[1])

    # leaf = leaf.lineTo(0,length)

    leaf = leaf.mirrorY()
    # return leaf
    leaf = leaf.extrude(13)



    size = length
    centreX = leafCentre[0]

    bowl = cq.Workplane("XY").sphere(size * 2).translate((0, leafCentre[1], -length*1.85))
    # return bowl
    cube = cq.Workplane("XY").rect(size * 3, size * 3).extrude(size * 2)
    mould = cube.cut(bowl)

    # cut the top of the leaf into a rounded shape
    return leaf.cut(mould)

leaf = maple2()

show_object(leaf)