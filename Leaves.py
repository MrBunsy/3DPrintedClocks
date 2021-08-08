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

def maple(size=40, seed=1):
    random.seed(seed)
    points = random.randint(4,7)
    leaf = cq.Workplane("XY").tag("base")

    startAngle = 0
    currentPos = (size*0.5,0)
    #leaf = leaf.moveTo(currentPos[0], currentPos[1])

    #(xPos, yPos, centreX for the angle that created this point, angle)
    tips = []
    inners = []

    #generate points for tips of leaves and inner bits of leaves
    for i in range(points):
        tipAngle = (i+1)*2*math.pi/(points*2)
        innerAngle = i*2*math.pi/(points*2)



        tipR = size*tipAngle/math.pi
        innerR = size*(innerAngle)/math.pi*0.5
        tipR*=random.uniform(0.8,1)
        innerR*=random.uniform(0.7,1.1)

        centreX = -i*0.5*size/points
        centreY = 0

        tipPos = (math.cos(tipAngle)*tipR + centreX, math.sin(tipAngle)*tipR + centreY, centreX, tipAngle)

        tips.append(tipPos)

        innerPos = (math.cos(innerAngle)*innerR + centreX, math.sin(innerAngle)*innerR + centreY, centreX, innerAngle)

        inners.append(innerPos)

    leaf.moveTo(inners[0][0], inners[0][1])

    previousTip = None
    # print("points:"+str(points))
    for i, tip in enumerate(tips):

        # if previousTip is not None:
        # print("i"+str(i))
        if i > 0:
            if False:
                leaf = leaf.lineTo(inners[i][0],inners[i][1])
            else:
                centreX = (inners[i-1][2]+tip[2])/2
                avgR = (length(inners[i-1], (centreX,0)) + length(tip, (tip[2], 0)))/2
                avgAngle = (inners[i-1][3] + tip[3])/2 - (math.pi/points)*0.1

                # mid = (math.cos(inners[i][3] + angleDiff)*avgR + centreX, math.sin(inners[i][3] + angleDiff)*avgR)
                mid = (math.cos(avgAngle)*avgR + centreX, math.sin(avgAngle)*avgR)
                # mid = ((inners[i][0] + tips[i-1][0])/2, (inners[i][1] + tips[i-1][1])/2)
                leaf = leaf.spline([mid, (inners[i][0], inners[i][1])], includeCurrent=True)


        if False:
            leaf = leaf.lineTo(tip[0], tip[1])

        else:
            centreX = (inners[i][2] + tip[2]) / 2
            avgR = (length(inners[i], (centreX, 0)) + length(tip, (tip[2], 0))) / 2
            avgAngle = (inners[i][3] + tip[3]) / 2 + (math.pi / points) * 0.1

            # mid = (math.cos(inners[i][3] + angleDiff)*avgR + centreX, math.sin(inners[i][3] + angleDiff)*avgR)
            mid = (math.cos(avgAngle) * avgR + centreX, math.sin(avgAngle) * avgR)
            # mid = ((inners[i][0] + tips[i-1][0])/2, (inners[i][1] + tips[i-1][1])/2)
            leaf = leaf.spline([mid, (tip[0], tip[1])], includeCurrent=True)


        # previousTip = tip

        # outDiff = math.pow(currentPos[0] - tipPos[0], 2) + math.pow(currentPos[1] - tipPos[1], 2)
        # inDiff = math.pow(endPos[0] - tipPos[0], 2) + math.pow(endPos[1] - tipPos[1], 2)
        # variation = 0.01
        # outOffset = random.uniform(-variation,variation)*outDiff
        # inOffset = random.uniform(-variation, variation) * inDiff
        #
        # # midOutPos = ((currentPos[0] + tipPos[0])/2 + outOffset, (currentPos[1] + tipPos[1])/2 + outOffset)
        # # midInPos = ((endPos[0] + tipPos[0]) / 2 + inOffset, (tipPos[1] + endPos[1]) / 2 + inOffset)
        #
        # midR = (tipR + endR)/2
        # offsetAngle = random.uniform(0,0.2)*(endAngle - tipAngle)
        # midOutPos = (math.cos(tipAngle-offsetAngle)*midR, math.sin(tipAngle-offsetAngle)*midR)
        # midInPos = (math.cos(tipAngle + offsetAngle) * midR, math.sin(tipAngle + offsetAngle) * midR)
        #
        # # leaf = leaf.lineTo(tipPos[0],tipPos[1])
        # # leaf = leaf.lineTo(endPos[0], endPos[1])
        #
        # leaf = leaf.spline([midOutPos, tipPos], includeCurrent=True)
        # leaf = leaf.spline([midInPos, endPos], includeCurrent=True)
        #
        # currentPos = endPos

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