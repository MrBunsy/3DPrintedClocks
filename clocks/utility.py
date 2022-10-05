import math
import numpy as np
from math import sin, cos, pi, floor
import cadquery as cq


# INKSCAPE_PATH="C:\Program Files\Inkscape\inkscape.exe"
IMAGEMAGICK_CONVERT_PATH="C:\\Users\\Luke\\Documents\\Clocks\\3DPrintedClocks\\ImageMagick-7.1.0-portable-Q16-x64\\convert.exe"


#aprox 1.13kg per 200ml for number 9 steel shot (2.25mm diameter)
#this must be a bit low, my height=100, diameter=38 wallThick=2.7 could fit nearly 350g of shot (and weighed 50g itself)
#STEEL_SHOT_DENSITY=1.13/0.2
STEEL_SHOT_DENSITY=0.35/0.055
#"Steel shot has a density of 7.8 g/cc" "For equal spheres in three dimensions, the densest packing uses approximately 74% of the volume. A random packing of equal spheres generally has a density around 64%."
#and 70% of 7.8 is 5.46, which is lower than my lowest measured :/

#TODO - pass around metric thread size rather than diameter and have a set of helper methods spit these values out for certain thread sizes
LAYER_THICK=0.2
LAYER_THICK_EXTRATHICK=0.3
#default extrusion width, for the odd thing where it matters
EXTRUSION_WIDTH = 0.45
GRAVITY = 9.81

#extra diameter to add to something that should be free to rotate over a rod
LOOSE_FIT_ON_ROD = 0.3

WASHER_THICK = 0.5

#extra diameter to add to the nut space if you want to be able to drop one in rather than force it in
NUT_WIGGLE_ROOM = 0.2
#extra diameter to add to the arbour extension to make them easier to screw onto the threaded rod
ARBOUR_WIGGLE_ROOM = 0.1

#assuming m2 screw has a head 2*m2, etc
#note, pretty sure this is often wrong.
METRIC_HEAD_D_MULT=1.9
#assuming an m2 screw has a head of depth 1.5
METRIC_HEAD_DEPTH_MULT=0.75
#metric nut width is double the thread size
METRIC_NUT_WIDTH_MULT=2

#depth of a nut, right for m3, might be right for others
METRIC_NUT_DEPTH_MULT=0.77
METRIC_HALF_NUT_DEPTH_MULT=0.57

COUNTERSUNK_HEAD_WIGGLE = 0.2
COUNTERSUNK_HEAD_WIGGLE_SMALL = 0.1



def getNutContainingDiameter(metric_thread, wiggleRoom=0):
    '''
    Given a metric thread size we can safely assume the side-to-side size of the nut is 2*metric thread size
    but the poly() in cq requires:
    "the size of the circle the polygon is inscribed into"

    so this calculates that

    '''

    nutWidth = metric_thread * METRIC_NUT_WIDTH_MULT

    if metric_thread == 3:
        nutWidth = 5.4

    nutWidth += wiggleRoom

    return nutWidth / math.cos(math.pi / 6)

def getNutHeight(metric_thread, nyloc=False, halfHeight=False):
    if metric_thread > 2 and halfHeight:
        return metric_thread * METRIC_HALF_NUT_DEPTH_MULT

    if metric_thread == 2 and halfHeight:
        return 1.2

    if metric_thread == 3:
        if nyloc:
            return 3.9

    return metric_thread * METRIC_NUT_DEPTH_MULT

def getScrewHeadHeight(metric_thread, countersunk=False):
    if metric_thread == 3:
        if countersunk:
            return 1.86
        return 2.6
    if metric_thread == 2:
        #TODO countersunk (1.2?)
        return 1.7

    return metric_thread

def getScrewHeadDiameter(metric_thread, countersunk=False):
    if metric_thread == 3:
        return 6
    if metric_thread == 2:
        return 3.9
    return METRIC_HEAD_D_MULT * metric_thread

class MachineScrew:
    '''
    Instead of a myriad of different ways of passing information about screwholes around, have a real screw class that can produce a cutting shape
    for screwholes
    '''

    def __init__(self, metric_thread=3, countersunk=False):
        self.metric_thread=metric_thread
        self.countersunk=countersunk

    def getCutter(self, length=1000, withBridging=False, layerThick=LAYER_THICK):
        '''
        Returns a (very long) model of a screw designed for cutting a hole in a shape
        Centred on (0,0,0), with the head flat on the xy plane and the threaded rod pointing 'up' (if facing up) along +ve z
        if facingDown, then still in exactly the same shape and orentation, but using hole-in-hole for printing with bridging
        '''

        screw = cq.Workplane("XY")#.circle(self.metric_thread/2).extrude(length)

        if self.countersunk:
            screw.add(cq.Solid.makeCone(radius1=self.getHeadDiameter() / 2 + COUNTERSUNK_HEAD_WIGGLE_SMALL, radius2=self.metric_thread / 2,
                                        height=self.getHeadHeight() + COUNTERSUNK_HEAD_WIGGLE_SMALL))
            #countersunk screw lengths seem to include the head
            screw= screw.faces(">Z").workplane().circle(self.metric_thread/2).extrude(length - self.getHeadHeight())
        else:
            if not withBridging:
                screw = screw.circle(self.getHeadDiameter() / 2 + NUT_WIGGLE_ROOM/2).extrude(self.getHeadHeight())
            else:
                screw = screw.add(getHoleWithHole(innerD=self.metric_thread, outerD=self.getHeadDiameter()+NUT_WIGGLE_ROOM, deep=self.getHeadHeight() ,layerThick=layerThick))
            #pan head screw lengths do not include the head
            screw = screw.faces(">Z").workplane().circle(self.metric_thread / 2).extrude(length)

        #extend out from the headbackwards too
        screw = screw.faces("<Z").workplane().circle(self.getHeadDiameter() / 2 + NUT_WIGGLE_ROOM/2).extrude(length)

        return screw

    def getNutHeight(self, nyloc=False, half=False):
        return getNutHeight(self.metric_thread, nyloc=nyloc, halfHeight=half)

    def getNutCutter(self,height=-1, nyloc=False, half=False, withScrewLength=0, withBridging=False, layerThick=LAYER_THICK):
        '''
        if height is provided, use that, otherwise use the default height of a nut
        '''
        nutHeight = getNutHeight(self.metric_thread, nyloc=nyloc, halfHeight=half)
        if height < 0:
            height = nutHeight
        nutD = getNutContainingDiameter(self.metric_thread, NUT_WIGGLE_ROOM)
        if withBridging:
            nut = getHoleWithHole(innerD=self.metric_thread, outerD=nutD,deep = height, sides=6, layerThick=layerThick)
        else:
            nut = cq.Workplane("XY").polygon(nSides=6,diameter=nutD).extrude(height)
        if withScrewLength > 0:
            nut = nut.faces(">Z").workplane().circle(self.metric_thread/2).extrude(withScrewLength-height)
        return nut

    def getString(self):
        return "M{} ({})".format(self.metric_thread, "CS" if self.countersunk else "pan")

    def getHeadHeight(self,):
        return getScrewHeadHeight(self.metric_thread)

    def getHeadDiameter(self):
        return getScrewHeadDiameter(self.metric_thread, countersunk=self.countersunk)

def averageOfTwoPoints(a,b):
    if len(a) != len(b):
        raise ValueError("Points not same number of dimensions")

    avg = []
    points = len(a)
    for i in points:
        avg.append((a[i] + b[i])/2)
    return avg

class Line:
    def __init__(self, start, angle=None, direction=None, anotherPoint=None):
        '''
        start = (x,y)
        Then one of:
        angle in radians
        direction (x,y) vector - will be made unit
        anotherPoint (x,y) - somewhere this line passes through as well as start
        '''

        self.start = start

        if direction is not None:
            self.dir = direction

        elif angle is not None:
            self.dir = (math.cos(angle), math.sin(angle))
        elif anotherPoint is not None:
            self.dir = (anotherPoint[0] - start[0], anotherPoint[1] - start[1])
        else:
            raise ValueError("Need one of angle, direction or anotherPoint")
        # make unit vector
        self.dir = np.divide(self.dir, np.linalg.norm(self.dir))
    def get2D(self, length=100):
        return cq.Workplane("XY").moveTo(self.start[0], self.start[1]).line(self.dir[0]*length, self.dir[1]*length)
    # def getGradient(self):
    #     return self.dir[1] / self.dir[0]

    def get_perpendicular_direction(self, clockwise=True):
        '''
        return a line which is perpendicular to this line
        '''

        z = 1 if clockwise else -1

        return  np.cross(self.dir, [0,0,z])


    def intersection(self, b):
        '''
        https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection#Given_two_points_on_each_line
        I used to be able to do this stuff off the top of my head :(

        First we consider the intersection of two lines {\displaystyle L_{1}}L_{1} and {\displaystyle L_{2}}L_{2} in 2-dimensional space, with line {\displaystyle L_{1}}L_{1} being defined by two distinct points {\displaystyle (x_{1},y_{1})}(x_{1},y_{1}) and {\displaystyle (x_{2},y_{2})}(x_{2},y_{2}), and line {\displaystyle L_{2}}L_{2} being defined by two distinct points {\displaystyle (x_{3},y_{3})}(x_3,y_3) and {\displaystyle (x_{4},y_{4})}{\displaystyle (x_{4},y_{4})}

        '''

        x1 = self.start[0]
        x2 = self.start[0] + self.dir[0]
        y1 = self.start[1]
        y2 = self.start[1] + self.dir[1]

        x3 = b.start[0]
        x4 = b.start[0] + b.dir[0]
        y3 = b.start[1]
        y4 = b.start[1] + b.dir[1]

        D = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 - x4)

        if D == 0:
            raise ValueError("Lines do not intersect")

        Px = ((x1*y2 - y1*x2) * (x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / D
        Py = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4))/D

        return (Px, Py)

def degToRad(deg):
    return math.pi*deg/180

def radToDeg(rad):
    return rad*180/math.pi

def polar(angle, radius):
    return (math.cos(angle) * radius, math.sin(angle) * radius)

def toPolar(x,y):
    r= math.sqrt(x*x + y*y)
    angle = math.atan2(y,x)
    return (angle, r)


def getHoleWithHole(innerD,outerD,deep, sides=1, layerThick=LAYER_THICK):
    '''
    Generate the shape of a hole ( to be used to cut out of another shape)
    that can be printed with bridging

      |  | inner D
    __|  |__
    |       | outer D       | deep

    if sides is 1 it's a circle, else it's a polygone with that number of sides
    funnily enough zero and 2 are invalid values

    '''

    if sides <= 0 or sides == 2:
        raise ValueError("Impossible polygon, can't have {} sides".format(sides))

    hole = cq.Workplane("XY")
    if sides == 1:
        hole = hole.circle(outerD/2)
    else:
        hole = hole.polygon(sides,outerD)
    hole = hole.extrude(deep+layerThick*2)

    #the shape we want the bridging to end up
    bridgeCutterCutter= cq.Workplane("XY").rect(innerD, outerD).extrude(layerThick).faces(">Z").workplane().rect(innerD,innerD).extrude(layerThick)#

    bridgeCutter = cq.Workplane("XY")
    if sides == 1:
        bridgeCutter = bridgeCutter.circle(outerD/2)
    else:
        bridgeCutter = bridgeCutter.polygon(sides,outerD)

    bridgeCutter = bridgeCutter.extrude(layerThick*2).cut(bridgeCutterCutter).translate((0,0,deep))

    hole = hole.cut(bridgeCutter)

    return hole


def getAngleCovered(distances,r):
    totalAngle = 0

    for dist in distances:
        totalAngle += math.asin(dist/(2*r))

    totalAngle*=2

    return totalAngle

def getRadiusForPointsOnAnArc(distances, arcAngle=math.pi, iterations=100):
    '''
    given a list of distances between points, place them on the edge of a circle at those distances apart (to cover circleangle of the circle)
    find the radius of a circle where this is possible
    circleAngle is in radians
    '''



    #treat as circumference
    aproxR = sum(distances) / arcAngle

    minR = aproxR
    maxR = aproxR*1.2
    lastTestR = 0
    # errorMin = circleAngle - getAngleCovered(distances, minR)
    # errorMax = circleAngle - getAngleCovered(distances, maxR)
    testR = aproxR
    errorTest = arcAngle - getAngleCovered(distances, testR)

    for i in range(iterations):
        # print("Iteration {}, testR: {}, errorTest: {}".format(i,testR, errorTest))
        if errorTest < 0:
            #r is too small
            minR = testR

        if errorTest > 0:
            maxR = testR

        if errorTest == 0 or testR == lastTestR:
            #turns out errorTest == 0 can happen. hurrah for floating point! Sometimes however we don't get to zero, but we can't refine testR anymore
            print("Iteration {}, testR: {}, errorTest: {}".format(i, testR, errorTest))
            # print("found after {} iterations".format(i))
            break
        lastTestR = testR
        testR = (minR + maxR)/2
        errorTest = arcAngle - getAngleCovered(distances, testR)

    return testR


class BearingInfo():
    '''
    Like MachineScrew this is designed to be in place of passing around loads of info, just one object that represents different sizes of bearings

    TODO - add and use safeouterD (where we can come into contact with the outside of the bearing without grating on the inner bit which will rotate)
    '''
    def __init__(self, bearingOuterD=10, bearingHolderLip=1.5, bearingHeight=4, innerD=3, innerSafeD=4.25):
        self.bearingOuterD = bearingOuterD
        # how much space we need to support the bearing (and how much space to leave for the arbour + screw0)
        #so a circle of radius outerD/2 - bearingHolderLip will safely rest on the outside sectino of the pulley
        #should probably refactor to outerSafeD, this is how many mm in from the outer radius the bearing holder can be without fouling the moving part of the bearing
        self.bearingHolderLip = bearingHolderLip
        self.bearingHeight = bearingHeight
        self.innerD=innerD
        #how large can something that comes into contact with the bearing (from the rod) be
        self.innerSafeD = innerSafeD



def getBearingInfo(innerD):
    '''
    Get some stock bearings
    '''
    if innerD == 3:
        return BearingInfo()
    if innerD == 4:
        return BearingInfo(bearingOuterD=13, bearingHolderLip=2, bearingHeight=5, innerD=innerD, innerSafeD=5.4)
    if innerD == 10:
        return BearingInfo(bearingOuterD=19, bearingHolderLip=2, bearingHeight=5, innerD=innerD, innerSafeD=12.5)
    if innerD == 15:
        return BearingInfo(bearingOuterD=24.2,  bearingHolderLip=2.5, bearingHeight=5, innerD=innerD)


def getPendulumLength(pendulum_period):
    pendulum_length = GRAVITY * pendulum_period * pendulum_period / (4 * math.pi * math.pi)
    return pendulum_length

def getPendulumPeriod(pendulum_length):
    pendulum_period = 2 * math.pi * math.sqrt(pendulum_length / GRAVITY)
    return pendulum_period