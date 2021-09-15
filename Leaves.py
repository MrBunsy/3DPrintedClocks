import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
import random

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


leaf = maple()

show_object(leaf)