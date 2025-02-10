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
import os
import re
import pathlib
import json

import numpy as np
from math import sin, cos, pi, floor
import cadquery as cq
from cadquery import exporters
from .cq_svg import exportSVG
import shutil
try:
    from markdown_pdf import MarkdownPdf, Section
except:
    pass

from string import Template

# INKSCAPE_PATH="C:\Program Files\Inkscape\inkscape.exe"
IMAGEMAGICK_CONVERT_PATH = "C:\\Users\\Luke\\Documents\\Clocks\\3DPrintedClocks\\ImageMagick-7.1.0-portable-Q16-x64\\convert.exe"

# aprox 1.13kg per 200ml for number 9 steel shot (2.25mm diameter)
# this must be a bit low, my height=100, diameter=38 wallThick=2.7 could fit nearly 350g of shot (and weighed 50g itself)
# STEEL_SHOT_DENSITY=1.13/0.2
STEEL_SHOT_DENSITY = 0.35 / 0.055
# "Steel shot has a density of 7.8 g/cc" "For equal spheres in three dimensions, the densest packing uses approximately 74% of the volume. A random packing of equal spheres generally has a density around 64%."
# and 70% of 7.8 is 5.46, which is lower than my lowest measured :/

# TODO - pass around metric thread size rather than diameter and have a set of helper methods spit these values out for certain thread sizes
LAYER_THICK = 0.2
LINE_WIDTH = 0.45
LAYER_THICK_EXTRATHICK = 0.3
# default extrusion width, for the odd thing where it matters
EXTRUSION_WIDTH = 0.45
GRAVITY = 9.81

# extra diameter to add to something that should be free to rotate over a rod
LOOSE_FIT_ON_ROD = 0.3
# where not wobbling is more important
LOOSE_FIT_ON_ROD_MOTION_WORKS = 0.25

LOOSE_SCREW = 0.2

WASHER_THICK_M3 = 0.5
# the spring washer flattened - useful because it can butt up against a bearing without rubbing on anything.
SMALL_WASHER_THICK_M3 = 1.1

# external diameter for 3 and 4mm internal diameter
#size used to make hole to slot it into
STEEL_TUBE_DIAMETER_CUTTER = 6.2
#actual size
STEEL_TUBE_DIAMETER = 6

# extra diameter to add to the nut space if you want to be able to drop one in rather than force it in
NUT_WIGGLE_ROOM = 0.2
# extra diameter to add to the arbour extension to make them easier to screw onto the threaded rod
ARBOUR_WIGGLE_ROOM = 0.1

# six actually prints pretty well, but feels a bit small! contemplating bumping up to 7.5
DIRECT_ARBOR_D = 7  # 7.5

# for calculating height of motion works - two half height m3 nuts are locked against each other and a spring washer is used to friction-fit the motion works to the minute wheel
# includes a bit of slack
TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT = 6
#M3 half nut + flattened spring washer + wiggle room
CENTRED_SECOND_HAND_BOTTOM_FIXING_HEIGHT = 1.75+1.1 + 1

# actually nearer 3.6, but this leaves wiggle room
M3_DOMED_NUT_THREAD_DEPTH = 3.5

# assuming m2 screw has a head 2*m2, etc
# note, pretty sure this is often wrong.
METRIC_HEAD_D_MULT = 1.9
# assuming an m2 screw has a head of depth 1.5
METRIC_HEAD_DEPTH_MULT = 0.75
# metric nut width is double the thread size
METRIC_NUT_WIDTH_MULT = 2
#true for M3 onwards
METRIC_NUT_THUMB_WIDTH_MULT = 4

# depth of a nut, right for m3, might be right for others
METRIC_NUT_DEPTH_MULT = 0.77
METRIC_HALF_NUT_DEPTH_MULT = 0.57

#TODO remove all usages of this - still lurking in places which don't use the MachineScrew class
COUNTERSUNK_HEAD_WIGGLE = 0.2
#then once that's done, rename this
#0.5 was excessive for M3
COUNTERSUNK_HEAD_WIGGLE_SMALL = 0.3


def get_washer_diameter(metric_thread):
    if metric_thread == 3:
        return 6.8
    raise ValueError("TODO measure more washers")

def get_washer_thick(metric_thread):
    if metric_thread == 3:
        return WASHER_THICK_M3
    raise NotImplementedError("TODO add more washer dimensions")

def get_nut_containing_diameter(metric_thread, wiggleRoom=0, thumb=False):
    '''
    Given a metric thread size we can safely assume the side-to-side size of the nut is 2*metric thread size
    but the poly() in cq requires:
    "the size of the circle the polygon is inscribed into"

    so this calculates that

    '''

    nutWidth = metric_thread * METRIC_NUT_WIDTH_MULT

    if metric_thread == 3:
        nutWidth = 5.4
    if metric_thread == 4:
        nutWidth = 6.85

    if thumb:
        nutWidth = metric_thread * METRIC_NUT_THUMB_WIDTH_MULT

    nutWidth += wiggleRoom

    return nutWidth / math.cos(math.pi / 6)


def get_nut_height(metric_thread, nyloc=False, half_height=False, thumb=False):
    if metric_thread > 2 and half_height:
        return metric_thread * METRIC_HALF_NUT_DEPTH_MULT

    if metric_thread == 2 and half_height:
        return 1.2

    if metric_thread == 3:
        if nyloc:
            return 3.9
        if thumb:
            return 3.05#2.85#3.0

    if metric_thread == 4:
        if nyloc:
            return 5

    return metric_thread * METRIC_NUT_DEPTH_MULT


def get_screw_head_height(metric_thread, countersunk=False):
    if metric_thread == 3:
        if countersunk:
            return 1.86
        return 2.6
    if metric_thread == 2:
        # TODO countersunk (1.2?)
        return 1.7
    if metric_thread == 4:
        if countersunk:
            return 2.1 + 0.4

    return metric_thread * 0.85


def get_screw_head_diameter(metric_thread, countersunk=False):

    #from https://engineersbible.com/countersunk-machine-ansi-metric/
    # #this looks far too big...
    # if countersunk:
    #     if metric_thread == 2:
    #         return 4.4
    #     if metric_thread == 3:
    #         return 6.3
    #     if metric_thread == 4:
    #         return 9.4

    if metric_thread == 3:
        # if countersunk:
        #want a bit more slack for the countersink holes
        #     return 5.6
        return 6
    if metric_thread == 2:
        return 3.9
    if metric_thread == 4:
        return 7.5 + 0.5
    return METRIC_HEAD_D_MULT * metric_thread


SCREW_LENGTH_EXTRA = 2


def get_diameter_for_die_cutting(M, sideways=False):
    '''
    with a bodge that circles printed sideways aren't very round
    '''
    if M == 2:
        return 1.6
    if M == 3:
        if sideways:
            return 2.75
        return 2.5
    if M == 4:
        return 3.3
    raise ValueError("Hole size not known for M{}".format(M))



class CountersunkWoodScrew:

    @staticmethod
    def get_wood_screw(imperial_size=4):
        if imperial_size == 4:
            return CountersunkWoodScrew(imperial_size = imperial_size, metric_size=3, head_diameter=6, head_depth=1.95)
        if imperial_size == 6:
            return CountersunkWoodScrew(imperial_size=imperial_size, metric_size=3.5, head_diameter=7, head_depth=2.3)
        if imperial_size == 8:
            return CountersunkWoodScrew(imperial_size=imperial_size, metric_size=4, head_diameter=8, head_depth=2.6)

        raise ValueError("Wood screw size #{} not known".format(imperial_size))

    def __init__(self, imperial_size=4, metric_size=3.0, head_diameter=6, head_depth=1.95, pilot_diameter=1.5, length=-1):
        self.imperial_size = imperial_size
        self.metric_size = metric_size
        self.diameter = metric_size
        self.head_diameter = head_diameter
        self.head_depth = head_depth
        self.pilot_diameter = pilot_diameter
        self.length = length

    def get_head_diameter(self):
        return self.head_diameter

    def get_rod_cutter_r(self, layer_thick=LAYER_THICK, loose=False, for_tap_die=False, sideways=False):
        return self.diameter/2


    def get_cutter(self, length=-1, with_bridging=False, layer_thick=LAYER_THICK, head_space_length=1000, loose=False, for_tap_die=False, sideways=False):
        if length < 0:
            if self.length < 0:
                # default to something really long
                length = 1000
            else:
                # use the length that this screw represents, plus some wiggle
                length = self.length + SCREW_LENGTH_EXTRA

        r = self.get_rod_cutter_r()
        if loose:
            r+=LOOSE_SCREW
        if for_tap_die:
            r = self.pilot_diameter/2

        screw = cq.Workplane("XY")  # .circle(self.metric_thread/2).extrude(length)

        screw = screw.add(cq.Solid.makeCone(radius1=self.head_diameter / 2 + COUNTERSUNK_HEAD_WIGGLE_SMALL, radius2=self.diameter/2,
                                            height=self.head_depth + COUNTERSUNK_HEAD_WIGGLE_SMALL))

        screw = screw.union(cq.Workplane("XY").circle(r).extrude(length))

        # extend out from the headbackwards too
        if head_space_length > 0:
            screw = screw.faces("<Z").workplane().circle(self.head_diameter / 2 + NUT_WIGGLE_ROOM / 2).extrude(head_space_length)

        return screw

'''
M3 thumb nuts:
Thread Diameter - M3
Thread Pitch - 0.5mm
Head Diameter - 12mm
Knurled Head Length - 2.5mm
Shoulder Diameter - 6mm
Shoulder Length (High Type) - 5mm
Shoulder Length (Thin Type) - 0.5mm
'''


class MachineScrew:
    '''
    Instead of a myriad of different ways of passing information about screwholes around, have a real screw class that can produce a cutting shape
    for screwholes

    TODO include layer thickness as part of screw or keep it as input to the cutters?
    '''

    def __init__(self, metric_thread=3, countersunk=False, length=-1):
        self.metric_thread = metric_thread
        self.countersunk = countersunk
        # if length is provided, this represents a specific screw
        self.length = length


    def get_nut_for_die_cutting(self):
        '''
        Not sure I ever really need this, just curious
        '''
        return cq.Workplane("XY").polygon(nSides=6, diameter=self.get_nut_containing_diameter()).circle(self.get_diameter_for_die_cutting() / 2).extrude(self.get_nut_height())

    def get_screw_for_thread_cutting(self):
        '''
        Pretty sure I won't need this either
        '''
        length = self.length
        if length < 0:
            length = 30
        screw = cq.Workplane("XY").polygon(nSides=6, diameter=self.get_nut_containing_diameter()).extrude(self.get_head_height()).circle(self.metric_thread / 2).extrude(length)
        return screw

    def get_diameter_for_die_cutting(self, sideways=False):
        return get_diameter_for_die_cutting(self.metric_thread, sideways=sideways)

    def get_washer_diameter(self):
        return get_washer_diameter(self.metric_thread)

    def get_washer_thick(self):
        return get_washer_thick(self.metric_thread)

    def get_rod_cutter_r(self, layer_thick=LAYER_THICK, loose=False, for_tap_die=False, sideways=False):
        r = self.metric_thread / 2

        if loose:
            r += LOOSE_SCREW / 2 + max(layer_thick - LAYER_THICK_EXTRATHICK, 0)
        if for_tap_die:
            r = self.get_diameter_for_die_cutting(sideways=sideways) / 2

        return r

    def get_cutter(self, length=-1, with_bridging=False, layer_thick=LAYER_THICK, head_space_length=1000, loose=False, self_tapping=False, sideways=False, space_for_pan_head=False):
        '''
        Returns a (very long) model of a screw designed for cutting a hole in a shape
        Centred on (0,0,0), with the head flat on the xy plane and the threaded rod pointing 'up' (if facing up) along +ve z
        if withBridging, then still in exactly the same shape and orentation, but using hole-in-hole for printing with bridging

        previously pan heads provided a cutter to fit the head into. but I don't think I ever actually used this and now this does not happen
        only countersunk screws have a space for the head included in the cutter
        for_tap_die - DEPRECATED - intended to be able to cut a thread with a real tap die. didn't really work at m3
        self_tapping: using an idea from a youtube video, add three nubs so the thread has something to bite and form a strong join without being too hard to screw
        '''

        if length < 0:
            if self.length < 0:
                # default to something really long
                length = 1000
            else:
                # use the length that this screw represents, plus some wiggle
                length = self.length + SCREW_LENGTH_EXTRA

        r = self.get_rod_cutter_r(layer_thick=layer_thick, loose=loose, for_tap_die=False, sideways=sideways)

        screw = cq.Workplane("XY").circle(r).extrude(length)

        if self_tapping:
            #cut out three nubs from teh cutter so the hole has three bits for the screw to bite into
            inner_r = self.get_rod_cutter_r(for_tap_die=True)
            nubs = 3
            angles = [-math.pi/2 + nub*(math.pi*2/nubs) for nub in range(nubs)]
            overlap = r - inner_r
            for angle in angles:
                pos = polar(angle, r + inner_r - overlap)
                screw = screw.cut(cq.Workplane("XY").circle(inner_r).extrude(length).translate(pos))

        if self.countersunk:
            #countersink angle for ANSI metric machine screws is 90deg, so this means edges sloping at 45deg. Therefore cut a code of height same as radius
            screw = screw.add(cq.Solid.makeCone(radius1=self.get_head_diameter() / 2 + COUNTERSUNK_HEAD_WIGGLE_SMALL, radius2=0,
                                        height=self.get_head_diameter() / 2 + COUNTERSUNK_HEAD_WIGGLE_SMALL))
            # # countersunk screw lengths seem to include the head
            # screw = screw.union(cq.Workplane("XY").circle(r).extrude(length))
        else:
            if space_for_pan_head:
                length += self.get_head_height()
                # pan head screw lengths do not include the head
                if not with_bridging:
                    screw = screw.union(cq.Workplane("XY").circle(self.get_head_diameter() / 2 + NUT_WIGGLE_ROOM / 2).extrude(self.get_head_height()))
                else:
                    screw = screw.union(get_hole_with_hole(inner_d=r * 2, outer_d=self.get_head_diameter() + NUT_WIGGLE_ROOM, deep=self.get_head_height(), layer_thick=layer_thick))
        # extend out from the headbackwards too
        if head_space_length > 0:
            screw = screw.faces("<Z").workplane().circle(self.get_head_diameter() / 2 + NUT_WIGGLE_ROOM / 2).extrude(head_space_length)

        return screw

    def get_nut_height(self, nyloc=False, half=False, thumb=False):
        return get_nut_height(self.metric_thread, nyloc=nyloc, half_height=half, thumb=thumb)

    def get_nut_cutter(self, height=-1, nyloc=False, half=False, with_screw_length=0, with_bridging=False, layer_thick=LAYER_THICK, wiggle=-1, rod_loose=False):
        '''
        if height is provided, use that, otherwise use the default height of a nut
        '''

        inner_r = self.get_rod_cutter_r(layer_thick=layer_thick, loose=rod_loose)

        if wiggle < 0:
            wiggle = layer_thick-0.2

        nutHeight = get_nut_height(self.metric_thread, nyloc=nyloc, half_height=half)
        if height < 0:
            height = nutHeight
        nutD = self.get_nut_containing_diameter() + wiggle
        if with_bridging:
            nut = get_hole_with_hole(inner_d=inner_r * 2, outer_d=nutD, deep=height, sides=6, layer_thick=layer_thick)
        else:
            nut = cq.Workplane("XY").polygon(nSides=6, diameter=nutD).extrude(height)
        if with_screw_length > 0:
            nut = nut.faces(">Z").workplane().circle(inner_r).extrude(with_screw_length - height)
        return nut

    def get_string(self):
        return "Machine screw M{} ({})".format(self.metric_thread, "CS" if self.countersunk else "pan")

    def __str__(self):
        return self.get_string()

    def get_head_height(self, ):
        return get_screw_head_height(self.metric_thread, countersunk=self.countersunk)

    def get_total_length(self):
        '''
        get the total length from tip to end
        '''
        if self.length < 0:
            return -1

        if self.countersunk:
            return self.length
        else:
            return self.length + self.get_head_height()

    def get_nut_containing_diameter(self, wiggle=NUT_WIGGLE_ROOM, thumb=False):
        return get_nut_containing_diameter(self.metric_thread, wiggle, thumb=thumb)

    def get_head_diameter(self):
        return get_screw_head_diameter(self.metric_thread, countersunk=self.countersunk)


def np_to_set(npVector):
    return (npVector[0], npVector[1])

def np_to_set3(npVector):
    return (npVector[0], npVector[1], npVector[2])

#TODO all of this should be moved to geometry?


def get_average_of_points(pointslist):
    if len(pointslist) < 2:
        raise ValueError("Cannot generate average of list shorter than 2")
    dimensions = len(pointslist[0])
    totals = [ 0 for i in range(dimensions)]


    for point in pointslist:
        for i, axis in enumerate(point):
            totals[i] += axis

    average = [axis/len(pointslist) for axis in totals]

    return tuple(average)


def average_of_two_points(a, b):
    if len(a) != len(b):
        raise ValueError("Points not same number of dimensions")

    avg = []
    points = len(a)
    for i in range(points):
        avg.append((a[i] + b[i]) / 2)
    return avg


# def differenceOfTwoPoints(a,b):
#     '''
#     returns a vector AB, from A to B (B - A)
#     '''
#     return

def distance_between_two_points(a, b):
    return math.sqrt(math.pow(a[0] - b[0], 2) + math.pow(a[1] - b[1], 2))


def get_preferred_tangent_through_point(circle_centre, circle_r, point, clockwise=True):
    '''
    Get the tangent which is in the clockwise of anticlockwise direction from the point (relative to the circle)
    '''
    tangents = get_tangents_through_point(circle_centre, circle_r, point)

    direct_line = Line(circle_centre, anotherPoint=point)

    perpendicular = direct_line.get_perpendicular_direction(clockwise=clockwise)

    centre_to_tangent = Line(circle_centre, anotherPoint=tangents[0].anotherPoint)

    if centre_to_tangent.dir.dot(perpendicular) >= 0:
        return tangents[0]
    else:
        return tangents[1]

    # for tangent in tangents:
    #     matches = True
    #     if positiveX is not None:
    #         if positiveX and tangent.anotherPoint[0] - circle_centre[0] <= 0:
    #             matches = False
    #     if positiveY is not None:
    #         if positiveY and tangent.anotherPoint[1] - circle_centre[1] <= 0:
    #             matches = False
    #     if matches:
    #         return tangent


# def getCircleIntersectionPoints(a_centre, a_r, b_centre, b_r):
#     '''
#     circle a centred at a_centre, radius a_r
#     circle b centred at b_centre, radius b_r
#     '''
#
#     dist = distanceBetweenTwoPoints(a_centre, b_centre)
#
#     if dist <= a_r + b_r and dist >= abs(a_r - b_r):
#         #circles will intersect, not too far apart and not inside each other
def get_circle_intersections(circle0_centre, r0, circle1_centre, r1):
    '''
    dervived from #https: // stackoverflow.com / a / 55817881 with little alteration
    returns array of points
    '''

    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1
    x0, y0 = circle0_centre
    x1, y1 = circle1_centre
    d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

    # non intersecting
    if d > r0 + r1:
        return []
    # One circle within other
    if d < abs(r0 - r1):
        return []
    # coincident circles
    if d == 0 and r0 == r1:
        return []
    else:
        a = (r0 ** 2 - r1 ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(r0 ** 2 - a ** 2)
        x2 = x0 + a * (x1 - x0) / d
        y2 = y0 + a * (y1 - y0) / d
        x3 = x2 + h * (y1 - y0) / d
        y3 = y2 - h * (x1 - x0) / d

        x4 = x2 - h * (y1 - y0) / d
        y4 = y2 + h * (x1 - x0) / d

        return [(x3, y3), (x4, y4)]


def get_tangents_through_point(circle_centre, circle_r, point):
    '''
    Given a circle centred at circle_centre, radius_r and a point outside the circle, return a Line which passes through the point and is a tangent to thecircle

    https://math.stackexchange.com/a/3190374
    '''
    Cx, Cy = circle_centre
    r = circle_r
    Px, Py = point
    # ################################ #
    dx, dy = Px - Cx, Py - Cy
    dxr, dyr = -dy, dx
    d = math.sqrt(dx ** 2 + dy ** 2)
    if d >= r:
        rho = r / d
        ad = rho ** 2
        bd = rho * math.sqrt(1 - rho ** 2)
        T1x = Cx + ad * dx + bd * dxr
        T1y = Cy + ad * dy + bd * dyr
        T2x = Cx + ad * dx - bd * dxr
        T2y = Cy + ad * dy - bd * dyr

        # print('The tangent points:')
        # print('\tT1≡(%g,%g),  T2≡(%g,%g).' % (T1x, T1y, T2x, T2y))
        if (d / r - 1) < 1E-8:
            raise ValueError('P is on the circumference')
        else:
            # print('The equations of the lines P-T1 and P-T2:')
            # print('\t%+g·y%+g·x%+g = 0' % (T1x - Px, Py - T1y, T1y * Px - T1x * Py))
            # print('\t%+g·y%+g·x%+g = 0' % (T2x - Px, Py - T2y, T2y * Px - T2x * Py))
            return [Line(point, anotherPoint=(T1x, T1y)), Line(point, anotherPoint=(T2x, T2y))]
    else:
        raise ValueError('''\
    Point P≡(%g,%g) is inside the circle with centre C≡(%g,%g) and radius r=%g.
    No tangent is possible...''' % (Px, Py, Cx, Cy, r))


class Colour:
    '''
    for use in show_object(...,options:{"color": colour})
    '''
    WHITE = "white"
    PINK = (255, 182, 193)
    GOLD = (153, 102, 0)
    BRASS = (71, 65, 26)
    RED = "red"
    ORANGE = (255, 102, 0)
    BRIGHT_ORANGE = (255, 120, 0)
    YELLOW = "yellow"
    GREEN = "green"
    LIME_GREEN = (100, 255, 0)
    DARK_GREEN = (0, 25, 13)
    LIGHTBLUE = (0, 153, 255)
    BLUE = "blue"
    BLUE_PASTLE = (	167, 199, 231)
    DARKBLUE = (0, 0, 55)
    PURPLE = (138, 43, 226)  # (148,0,211)
    LILAC = (210, 175, 255)
    LIGHTGREY = (200,200,200)#(211, 211, 211)
    SILVER = (169,169,169)#(192, 192, 192)
    DARKGREY = (50, 50, 50)
    DARKER_GREY = (30, 30, 30)
    BLACK = "black"
    BROWN = (66, 40, 14)  # (139,69,19)

    RAINBOW = [RED,
               ORANGE,
               YELLOW,
               GREEN,
               LIGHTBLUE,
               BLUE,
               PURPLE]

    @staticmethod
    def colour_tidier(string):
        '''
        given a colour name (from, for example, cosmetics or hands) return something that cq_editor will display
        '''
        return string


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

        self.anotherPoint = None
        if direction is not None:
            self.dir = direction

        elif angle is not None:
            self.dir = (math.cos(angle), math.sin(angle))
        elif anotherPoint is not None:
            self.dir = (anotherPoint[0] - start[0], anotherPoint[1] - start[1])
            # store for hackery
            self.anotherPoint = anotherPoint
        else:
            raise ValueError("Need one of angle, direction or anotherPoint")
        # make unit vector
        self.dir = np.divide(self.dir, np.linalg.norm(self.dir))

    def get2D(self, length=100, both_directions=False):
        line = cq.Workplane("XY").moveTo(self.start[0], self.start[1]).line(self.dir[0] * length, self.dir[1] * length)
        if both_directions:
            line = line.add(cq.Workplane("XY").moveTo(self.start[0], self.start[1]).line(-self.dir[0] * length, -self.dir[1] * length))
        return line

    def get_direction(self, negative=False):
        if negative:
            return (-self.dir[0], -self.dir[1])
        else:
            return self.dir

    def get_direction_towards(self, b):
        '''
        get direction, positive towards the point
        '''
        if self.dot_product(b) > 0:
            return self.dir
        else:
            return self.get_direction(negative=True)

    # def getGradient(self):
    #     return self.dir[1] / self.dir[0]

    def get_perpendicular_direction(self, clockwise=True):
        '''
        return a line which is perpendicular to this line
        '''

        z = 1 if clockwise else -1

        return np.cross(self.dir, [0, 0, z])[:-1]

    def dot_product(self, b):
        return np.dot(self.dir, b.dir)

    def intersection_with_circle(self, circle_centre, circle_r, line_length=-1):
        '''
        assumes line is from start pos to anotherPoint, or if this line doesn't have anotherPoint (was created with angle or dir)
        then assumes the line is line_length long. if line_length is provided, that overrides anotherPoint
        only finds intersections along the length of that bit of the line.

        ported from my old javascript physics engine

        //does a circle intersect a line?
        //returns points where circle intersects.
        '''
        x1, y1 = self.start

        if self.anotherPoint is None or line_length > 0:
            if line_length < 0:
                line_length = 10000
            x2 = self.start[0] + self.dir[0] * line_length
            y2 = self.start[1] + self.dir[1] * line_length
        else:
            x2, y2 = self.anotherPoint
        a = circle_centre[0]
        b = circle_centre[1]
        r = circle_r
        '''//r=radius
		//a=circle centre x
		//b=circle centre y
		//(x1,y1), (x2,y2) points line travels between
		'''

        if x1 < x2:
            testx1 = x1
            testx2 = x2
        else:
            testx1 = x2
            testx2 = x1

        if y1 < y2:
            testy1 = y1
            testy2 = y2
        else:
            testy1 = y2
            testy2 = y1

        # treat both as squares first, if they collide, look in more detail
        # if not (testx2 > (a-r) and testx1 < (a+r) and testy1 < (b+r) and testy2 > (b-r)):
        #     #nowhere near,
        #     return []

        distance = self.get_shortest_distance_to_point(circle_centre)
        if distance > circle_r:
            return []

        dy = y2 - y1
        dx = x2 - x1

        if dx == 0:
            m = float('inf')
        else:
            # //gradient of line
            m = dy / dx
        # //fixes odd problem with not detecting collision point correctly on a nearly vertical line - needs looking into?
        if m > 1000000:
            m = float('inf')

        if m == float('inf') or m == float('-inf'):
            # //vertical line - we know x, but have potentially two possible Ys
            x = x1
            # //b^2 - 4ac
            discrim = math.pow((-2 * b), 2) - 4 * (b * b + (x - a) * (x - a) - r * r)
            if discrim >= 0:
                points = []
                # //minus
                y = (-(-2 * b) - math.sqrt(discrim)) / 2
                if testx1 <= x and x <= testx2 and testy1 <= y and y <= testy2:
                    points.append((x, y))
                # //plus
                y = (-(-2 * b) + math.sqrt(discrim)) / 2
                if testx1 <= x and x <= testx2 and testy1 <= y and y <= testy2:
                    points.append((x, y))
                return points

        elif m == 0:
            # //horizontal line, two potential Xs
            y = y1
            discrim = math.pow((-2 * a), 2) - 4 * (a * a + (y - b) * (y - b) - r * r)
            if discrim >= 0:
                points = []
                # //minus
                x = (-(-2 * a) - math.sqrt(discrim)) / 2
                if testx1 <= x and x <= testx2 and testy1 <= y and y <= testy2:
                    points.append((x, y))
                # //plus
                x = (-(-2 * a) + math.sqrt(discrim)) / 2
                if testx1 <= x and x <= testx2 and testy1 <= y and y <= testy2:
                    points.append((x, y))
                return points
        else:
            # //re-arrangement of the equation of a circle and the equation of a straight line to find the x co-ordinate of an intersection
            discrim = math.pow((-2 * a - 2 * m * m * x1 + 2 * y1 * m - 2 * b * m), 2) - 4 * (1 + m * m) * (-2 * m * x1 * y1 + 2 * m * x1 * b + m * m * x1 * x1 - r * r + a * a + (y1 - b) * (y1 - b))
            # //if discriminant is less than zero then there are no real roots and :. no interesction
            if discrim >= 0:
                points = []
                # //circle intersects line, but where?
                # //minus first
                x = (-(-2 * a - 2 * m * m * x1 + 2 * y1 * m - 2 * b * m) - math.sqrt(discrim)) / (2 * (1 + m * m))
                y = m * (x - x1) + y1
                if testx1 <= x and x <= testx2 and testy1 <= y and y <= testy2:
                    points.append((x, y))
                # //then plus
                x = (-(-2 * a - 2 * m * m * x1 + 2 * y1 * m - 2 * b * m) + math.sqrt(discrim)) / (2 * (1 + m * m))
                y = m * (x - x1) + y1

                if testx1 <= x and x <= testx2 and testy1 <= y and y <= testy2:
                    points.append((x, y))

                return points
            # //end of discrim if

        # //end of m switch
        return []

    # def intersection_with_circle(self, circle_centre, circle_r):
    #     distance = self.get_shortest_distance_to_point(circle_centre)
    # 
    #     if distance > circle_r:
    #         return []

    # '''
    # not perfect, I haven't bothered to understand Shapely properly
    # '''
    # circle_centre_point = Point(circle_centre[0], circle_centre[1])
    #
    # if self.anotherPoint is None:
    #     #could easily fix this to make properly generic
    #     raise ValueError("Need anotherPoint to test intersection with circle (for now)")
    #
    # line = LineString([self.start, self.anotherPoint])
    # circle = circle_centre_point.buffer(circle_r)
    #
    # intersections = circle.intersection(line)
    #
    # points = []
    #
    # for end in range(floor(len(intersections.bounds)/2)):
    #     point = (intersections.bounds[end*2], intersections.bounds[end*2+1])
    #     if distance_between_two_points(point, circle_centre) >= circle_r*0.99:
    #         #point on the edge of the circle
    #         points.append(point)
    #
    #
    #
    # return points

    def get_angle(self):
        return math.atan2(self.dir[1], self.dir[0])

    def get_angle_between_lines(self, b, acute=True):
        aAngle = self.get_angle()
        bAngle = b.get_angle()
        angle = abs(aAngle - bAngle)
        while angle > math.pi:
            angle -= math.pi
        if angle > math.pi / 2:
            angle = math.pi - angle

        if acute:
            return angle
        else:
            return math.pi - angle

    def get_shortest_distance_to_point(self, point):
        '''
        https://stackoverflow.com/a/39840218
        '''
        p1 = np.asarray(self.start)
        p2 = np.asarray((self.start[0] + self.dir[0], self.start[1] + self.dir[1]))
        p3 = np.asarray(point)
        d = np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)

        return d

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

        D = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if D == 0:
            raise ValueError("Lines do not intersect")

        Px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / D
        Py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / D

        return (Px, Py)


def deg_to_rad(deg):
    return math.pi * deg / 180


def rad_to_deg(rad):
    return rad * 180 / math.pi


def polar(angle, radius=1):
    return (math.cos(angle) * radius, math.sin(angle) * radius)


def to_polar(x, y):
    r = math.sqrt(x * x + y * y)
    angle = math.atan2(y, x)
    return (angle, r)


def get_hole_with_hole(inner_d, outer_d, deep, sides=1, layer_thick=LAYER_THICK):
    '''
    Generate the shape of a hole ( to be used to cut out of another shape)
    that can be printed with bridging

      |  | inner D
    __|  |__
    |       | outer D       | deep

    if sides is 1 it's a circle, else it's a polygone with that number of sides
    funnily enough zero and 2 are invalid values

    TODO if the radii are too similar (only a thin ring around the edge) we don't need the two layers
    '''

    if sides <= 0 or sides == 2:
        raise ValueError("Impossible polygon, can't have {} sides".format(sides))

    layers = 2
    square_r = (inner_d / 2) / math.cos(math.pi / 4)
    if square_r > outer_d/2:
        #can do this in one layer
        layers = 1
    hole = cq.Workplane("XY")
    if sides == 1:
        hole = hole.circle(outer_d / 2)
    else:
        hole = hole.polygon(sides, outer_d)
    hole = hole.extrude(deep + layer_thick * layers)

    # the shape we want the bridging to end up


    if layers == 1:
        bridgeCutterCutter = cq.Workplane("XY").rect(inner_d, inner_d).extrude(layer_thick)
    else:
        bridgeCutterCutter = cq.Workplane("XY").rect(inner_d, outer_d).extrude(layer_thick).faces(">Z").workplane().rect(inner_d, inner_d).extrude(layer_thick)  #
    bridgeCutter = cq.Workplane("XY")
    if sides == 1:
        bridgeCutter = bridgeCutter.circle(outer_d / 2)
    else:
        bridgeCutter = bridgeCutter.polygon(sides, outer_d)

    bridgeCutter = bridgeCutter.extrude(layer_thick * layers).cut(bridgeCutterCutter).translate((0, 0, deep))

    hole = hole.cut(bridgeCutter)

    return hole


def getAngleCovered(distances, r):
    totalAngle = 0

    for dist in distances:
        totalAngle += math.asin(dist / (2 * r))

    totalAngle *= 2

    return totalAngle


def getRadiusForPointsOnAnArc(distances, arcAngle=math.pi, iterations=100):
    '''
    given a list of distances between points, place them on the edge of a circle at those distances apart (to cover circleangle of the circle)
    find the radius of a circle where this is possible
    circleAngle is in radians
    '''

    # treat as circumference
    aproxR = sum(distances) / arcAngle

    minR = aproxR
    maxR = aproxR * 1.2
    lastTestR = 0
    # errorMin = circleAngle - getAngleCovered(distances, minR)
    # errorMax = circleAngle - getAngleCovered(distances, maxR)
    testR = aproxR
    errorTest = arcAngle - getAngleCovered(distances, testR)

    for i in range(iterations):
        # print("Iteration {}, testR: {}, errorTest: {}".format(i,testR, errorTest))
        if errorTest < 0:
            # r is too small
            minR = testR

        if errorTest > 0:
            maxR = testR

        if errorTest == 0 or testR == lastTestR:
            # turns out errorTest == 0 can happen. hurrah for floating point! Sometimes however we don't get to zero, but we can't refine testR anymore
            print("Iteration {}, testR: {}, errorTest: {}".format(i, testR, errorTest))
            # print("found after {} iterations".format(i))
            break
        lastTestR = testR
        testR = (minR + maxR) / 2
        errorTest = arcAngle - getAngleCovered(distances, testR)

    return testR


class ChainInfo:
    '''
    Hold info to describe a chain
    regula 30 hour chain:
    train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)

    Undecided on if to include tolerance with the chain or with the wheel, going to try with the wheel for now as I hope the improved pocket wheel won't need it as much
    '''

    def __init__(self, wire_thick=0.85, width=3.6, outside_length=6.65, inside_length=-1):
        self.wire_thick = wire_thick
        self.width = width
        self.outside_length = outside_length
        self.inside_length = inside_length
        if self.inside_length < 0:
            self.inside_length = self.outside_length - self.wire_thick * 2
        if self.outside_length < 0:
            self.outside_length = self.inside_length + self.wire_thick * 2

        self.pitch = self.inside_length*2

    def __str__(self):
        return f"Chain_{self.wire_thick}x{self.width}_pitch_{self.pitch}"


# consistently reliable results have been obtained by laying out and pulling tight) a stretch of chain against a ruler to calculate inside_length (half chain pitch)

REGULA_30_HOUR_CHAIN = ChainInfo(wire_thick=0.85, width=3.6, outside_length=6.65)
# claims a max load of 5kg, looks promising for an eight day
# 129 links in 1m = 7.75 inside length
# 38.5 in 30cm = 7.79 inside length
# re-measuring 7.75 inside seems more accurate and wire I think is 1.45 not 1.4 thick
# some lengths of this stuff are completely different, triple checked this and got one with much shorter links:
# 82 links over 597mm
# looks like that one chain is just different! I might not use this one after all...
# 74 links 593mm
# different again!!! That's three different sizes from one purchase. I think I need to stick to ones that come on a reel
CHAIN_PRODUCTS_1_4MM_CHAIN = ChainInfo(wire_thick=1.45, width=5.5, inside_length=1000 / 129)  # , outside_length=10.8)

# https://www.cousinsuk.com/product/chains-steel?code=C34656
# looks to be as good value as the reels of chain I got, but smaller
# the values on the website don't match up to the stated chain pitch, I'll have to wait until it arrives
# 597.5/83
COUSINS_1_5MM_CHAIN = ChainInfo(wire_thick=1.5, width=6.5, inside_length=597.5 / 83.0)  # outside_length=12)

# bought one, probably not going to buy any more but might use it for a prototype
# undecided - on further inspection it's not a great chain, many wonky links
COUSINS_1_2_BRASS_CHAIN = ChainInfo(wire_thick=1.2, width=5.5, inside_length=597 / 76)

# TODO measure a long stretch, 10.15 is just a rough estimate
FAITHFULL_1_6MM_CHAIN = ChainInfo(wire_thick=1.6, width=6.35, inside_length=10.15)

# 595.5/94
REGULA_8_DAY_1_05MM_CHAIN = ChainInfo(wire_thick=1.05, width=4.4, inside_length=595.5 / 94)  # , outside_length=8.4)


class BearingInfo:
    '''
    Like MachineScrew this is designed to be in place of passing around loads of info, just one object that represents different sizes of bearings

    TODO - remove holder lip and use entirely safe outer and safe inner diameters
    '''

    def __init__(self, outer_d=10, height=4, inner_d=3, inner_safe_d=4.25, inner_d_wiggle_room=0.05, outer_safe_d=-1, inner_safe_d_at_a_push=-1,
                 flange_thick=0, flange_diameter=0, cutter_wiggle_room=0.1):
        self.outer_d = outer_d
        self.height = height
        self.inner_d = inner_d
        self.cutter_wiggle_room = cutter_wiggle_room
        # how large can something that comes into contact with the bearing (from the rod) be
        self.inner_safe_d = inner_safe_d
        # for times when I really need to push the limits rather than play it safe
        self.inner_safe_d_at_a_push = inner_safe_d_at_a_push
        if self.inner_safe_d_at_a_push < 0:
            self.inner_safe_d_at_a_push = self.inner_safe_d
        # something that can touch the outside of the bearing can also touch the front/back of the bearing up to this diameter without fouling on anything that moves when it rotates
        self.outer_safe_d = outer_safe_d
        # subtract this from innerD for something taht can easily slot inside (0.05 tested only for 15 and 10mm inner diameter plastic bearings)
        self.inner_d_wiggle_room = inner_d_wiggle_room

        self.flange_thick = flange_thick
        self.flange_diameter = flange_diameter

    def get_cutter(self, with_bridging=False, layer_thick = LAYER_THICK, rod_long=20):
        '''
        flange side down
        '''

        outer_d = self.outer_d + self.cutter_wiggle_room
        inner_d = self.outer_safe_d

        if self.flange_diameter > 0:
            flange_outer_d = self.flange_diameter + self.cutter_wiggle_room
            if with_bridging:
                cutter = get_hole_with_hole(inner_d=outer_d, outer_d=flange_outer_d, deep=self.flange_thick, layer_thick=layer_thick)
                cutter = cutter.union(get_hole_with_hole(inner_d=inner_d, outer_d=outer_d, deep=self.height - self.flange_thick, layer_thick=layer_thick).translate((0,0,self.flange_thick)))
            else:
                cutter = cq.Workplane("XY").circle(flange_outer_d/2).extrude(self.flange_thick).faces(">Z").workplane().circle(self.outer_d / 2).extrude(self.height - self.flange_thick)
        else:
            if with_bridging:
                cutter = get_hole_with_hole(inner_d=inner_d, outer_d=outer_d, deep=self.height, layer_thick=layer_thick)
            else:
                cutter = cq.Workplane("XY").circle(outer_d / 2).extrude(self.height)

        if rod_long > 0:
            cutter = cutter.union(cq.Workplane("XY").circle(inner_d/2).extrude(rod_long*2).translate((0,0,-rod_long/2)))
        return cutter

    def get_string(self):
        flange_string = ""
        if self.flange_diameter > 0:
            flange_string = " (flange {}x{})".format(self.flange_diameter, self.flange_thick)
        return "Bearing {inner}x{outer}x{thick}{flange_string}".format(inner=self.inner_d, outer=self.outer_d, thick=self.height, flange_string=flange_string)

    def __str__(self):
        return self.get_string()

BEARING_12x18x4_FLANGED = BearingInfo(outer_d=18, inner_d=12, height=4, flange_thick=0.8, flange_diameter=19.5, outer_safe_d=15, inner_safe_d=13.5, inner_safe_d_at_a_push=14)
BEARING_12x18x4_THIN = BearingInfo(outer_d=18, inner_d=12, height=4, outer_safe_d=15, inner_safe_d=13, inner_safe_d_at_a_push=14)
BEARING_12x21x5 = BearingInfo(outer_d=21, height=5, inner_d=12, outer_safe_d=16.5, inner_safe_d=14)
BEARING_3x8x4 = BearingInfo(outer_d=8, inner_d=3, height=4, inner_safe_d=4, outer_safe_d=6)
#can't remember why I gave this one more space
BEARING_2x6x3 = BearingInfo(outer_d=6, inner_d=2, height=3, inner_safe_d=2.9, outer_safe_d=3.8, cutter_wiggle_room=0.2)

#guess on safe d
BEARING_8x16x5 = BearingInfo(outer_d = 16, inner_d=8, height=5, outer_safe_d=13, inner_safe_d=10)
#guess on safe d
BEARING_7x14x5 = BearingInfo(outer_d = 14, inner_d=7, height=5, outer_safe_d=11, inner_safe_d=9)

BEARING_3x10x4 = BearingInfo(outer_d=10, outer_safe_d=10 - 3, height=4, inner_d=3, inner_safe_d=4.25, inner_safe_d_at_a_push=5.2)
def get_bearing_info(innerD):
    '''
    Get some stock bearings, although now I have a much larger selection and more use cases, consider phasing this out
    '''
    if innerD == 2:
        #2x6x3
        return BEARING_2x6x3
    if innerD == 3:
        # 3x10x4
        # most arbors
        return BEARING_3x10x4
    if innerD == 4:
        # 4x13x5
        # used for power arbor on eight day clocks
        # was outer 13.2 but the bearing fell out of the latest print using light grey fibreology easy-PETG!
        return BearingInfo(outer_d=13, outer_safe_d=13 - 4, height=5, inner_d=innerD, inner_safe_d=5.4)
    if innerD == 6:
        # these are really chunky, might need to get some which are less chunky. Not actually used in a print yet
        return BearingInfo(outer_d=19, outer_safe_d=12, height=6, inner_d=6, inner_safe_d=8, cutter_wiggle_room=0.2)
    if innerD == 12:
        # 12x21x5
        return BEARING_12x21x5
    # if innerD == 10:
    #     # not used much since direct-arbor with small bearings (this had too much friction)
    #     # 19.2 works well for plastic and metal bearings - I think I should actually make the 3 and 4mm bearing holders bigger too
    #     return BearingInfo(outer_d=19.2, outer_safe_d=19.4, height=5, inner_d=innerD, inner_safe_d=12.5)
    if innerD == 15:
        # 15x24x5
        # (used for the winding key)
        # nominally 24mm OD, but we can't squash it in like the metal bearings. 24.2 seems a tight fit without squashing (and presumably increasing friction?)
        # printed in light grey 24.2 was a tiny bit too loose! not sure why the dark and light grey are so different, both fibreology easy-PETG
        # with 24.15 light grey again latest print fell out again, wondering if tolerences are better since the new nozzle?
        return BearingInfo(outer_d=24, outer_safe_d=24 - 5, height=5, inner_d=innerD, inner_safe_d=17.5)
    raise ValueError("Bearing not found")
    return None


def get_o_ring_thick(total_diameter):
    # #hack
    # return 2.2
    return 2
    # TODO when I build up a selection of o-rings tinker with this
    if total_diameter > 20:
        return 3
    return 2


def getPendulumLength(pendulum_period):
    '''
    in metres!
    '''
    pendulum_length = GRAVITY * pendulum_period * pendulum_period / (4 * math.pi * math.pi)
    return pendulum_length


def getPendulumPeriod(pendulum_length):
    pendulum_period = 2 * math.pi * math.sqrt(pendulum_length / GRAVITY)
    return pendulum_period


def get_pendulum_holder_cutter(pendulum_rod_d=3, z=7.5, extra_nut_space=0.2, extra_space_for_rod=0.1):
    '''
    a square hole with rod space below it that can hold the top of a pendulum, top of holder is at 0,0
    z is height above xy plane for the rod centre
    extra_space_for_rod - how much wider to make the hole for the rod to slot into
    extra_nut_space - how much larger than the nut should the hole the nut slots into
    '''

    shape = cq.Workplane("XY")

    # a square hole that can fit the end of the pendulum rod with two nuts on it
    hole_start_y = 0
    hole_height = get_nut_height(pendulum_rod_d, nyloc=True) + get_nut_height(pendulum_rod_d) + 1

    nut_d = get_nut_containing_diameter(pendulum_rod_d)

    width = nut_d * 1.5

    space = cq.Workplane("XY").moveTo(0, hole_start_y - hole_height / 2).rect(width, hole_height).extrude(1000).translate((0, 0, z - nut_d))
    shape = shape.add(space)

    # I've noticed that the pendulum doesn't always hang vertical, so give more room for the rod than the minimum so it can hang forwards relative to the holder
    extra_rod_space_z = 1

    rod = cq.Workplane("XZ").tag("base").moveTo(0, z - extra_rod_space_z).circle(pendulum_rod_d / 2 + extra_space_for_rod / 2).extrude(100)
    # add slot for rod to come in and out
    rod = rod.workplaneFromTagged("base").moveTo(0, z - extra_rod_space_z + 500).rect(pendulum_rod_d + extra_space_for_rod, 1000).extrude(100)

    rod = rod.translate((0, hole_start_y, 0))

    shape = shape.add(rod)

    nut_thick = get_nut_height(pendulum_rod_d, nyloc=True)

    nut_space2 = cq.Workplane("XZ").moveTo(0, z).polygon(6, nut_d + extra_nut_space).extrude(nut_thick).translate((0, hole_start_y - hole_height, 0))
    shape = shape.add(nut_space2)

    return shape

class Font:
    '''
    found myself starting to pass more and more info about rather than just the name of the font - so wrap it all up in a single object.
    TODO move everything over to this
    '''
    def __init__(self, name="Arial", kind="bold", filepath=None, dial_scale=1.0):
        self.name = name
        self.kind = kind
        self.filepath = filepath
        self.dial_scale = dial_scale

#I don't think I have the rights to distribute these, so anyone checking out the repo will have to source them themselves.
FANCY_WATCH_FONT = Font(name="Eurostile Extended #2", dial_scale=1.5, filepath="../fonts/Eurostile_Extended_2_Bold.otf")
FANCY_WATCH_TEXT_FONT = Font(name = "EB Garamond", filepath = "../fonts/EBGaramond-Bold.ttf")
SANS_GILL_FONT = Font(name="Gill Sans Medium", dial_scale=0.9, filepath="../fonts/GillSans/Gill Sans Medium.otf")
SANS_GILL_HEAVY_FONT = Font(name="Gill Sans Heavy", dial_scale=0.9, filepath="../fonts/GillSans/Gill Sans Heavy.otf")
SANS_GILL_BOLD_FONT = Font(name="Gill Sans Bold", dial_scale=0.9, filepath="../fonts/GillSans/Gill Sans Bold.otf")
ARIAL_FONT = Font(name="Arial")
DEFAULT_FONT = SANS_GILL_FONT

class TextSpace:
    def __init__(self, x, y, width, height, horizontal=None, inverted=True, text=None, thick=LAYER_THICK, font="Arial", angle_rad=0, font_path = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # deprecated, use angle_rad for more control. If this is a boolean it will override angle_rad to math.pi/2 or 0
        self.horizontal = horizontal
        self.text = text
        self.text_size = 10
        self.inverted = inverted
        self.thick = thick
        #backwards compatibility
        if isinstance(font, str):
            font = Font(name=font, filepath=font_path)
        if font is None:
            font = DEFAULT_FONT
        self.font = font
        #deprecated, use the Font object instead
        # self.font_path = font_path
        self.angle_rad = angle_rad

        if self.horizontal is not None:
            if self.horizontal == False:
                self.angle_rad = math.pi / 2
            else:
                self.angle_rad = 0

    def set_text(self, text):
        self.text = text

    def set_size(self, size):
        self.text_size = size

    def get_text_shape(self):
        '''
        get the text centred properly
        '''
        shape = cq.Workplane("XY").text(self.text, self.text_size, self.thick, kind=self.font.kind, font=self.font.name, fontPath=self.font.filepath)  # , font="Comic Sans MS")
        bb = shape.val().BoundingBox()

        # actually centre it, the align feature of text does...something else
        shape = shape.translate((-bb.center.x, -bb.center.y))

        if self.inverted:
            shape = shape.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, self.thick))

        shape = shape.rotate((0, 0, 0), (0, 0, 1), rad_to_deg(self.angle_rad))

        shape = shape.translate((self.x, self.y))

        return shape

    def get_text_width(self):
        shape = self.get_text_shape()
        bb = shape.val().BoundingBox()
        return bb.xlen

    def get_text_height(self):
        shape = self.get_text_shape()
        bb = shape.val().BoundingBox()
        return bb.ylen

    def get_text_max_size(self):
        shape = self.get_text_shape()
        bb = shape.val().BoundingBox()
        width_ratio = self.width / bb.xlen
        height_ratio = self.height / bb.ylen

        return self.text_size * min(width_ratio, height_ratio)

def export_STL(object, object_name, clock_name="clock", path="../out", tolerance=0.1):
    if object is None:
        print("Not exporting {} as object is None".format(object_name))
        return
    out = os.path.join(path, "{}_{}.stl".format(clock_name, object_name))
    print(f"Exporting STL {out}")
    exporters.export(object, out, tolerance=tolerance, angularTolerance=tolerance)



machine_screw_lengths={
    3: [x for x in range(4,22+2,2)] + [x for x in range(25,40+5,5)] + [50, 60],
    2: [x for x in range(4, 10, 2) ]
}

def get_nearest_machine_screw_length(length, machine_screw, allow_longer=False, prefer_longer=False):
    '''
    Given a size, find the nearest machine screw that is easily purchasable
    '''

    if not allow_longer and prefer_longer:
        #shortcut, allow just specifying prefer_longer
        allow_longer = True

    available_lengths = machine_screw_lengths[machine_screw.metric_thread]

    just_below = -1

    for test_length in available_lengths:
        if test_length <= length:
            just_below = test_length

    if not allow_longer:
        return just_below

    #if we can be bigger as well
    below_index = available_lengths.index(just_below)
    if below_index < len(available_lengths)-1:
        just_above = available_lengths[below_index+1]

    if prefer_longer:
        return just_above

    if abs(length - just_below) < abs(length - just_above):
        return just_below
    else:
        return just_above


class BillOfMaterials:

    MODEL_PATH = "models"
    PRINTABLES_PATH = "STL"
    IMAGES_PATH = "images"

    SVG_OPTS_SIDE_PROJECTION = {"projectionDir": (-1, 0, 0), "xDirection": (0, 0, 1)}
    SVG_OPTS_BACK_PROJECTION = {"projectionDir": (0, 0, -1)}
    #as if lying on a table looking down at them
    SVG_OPTS_TABLE_FRONT_PROJECTION = {"width":500, "height":500, "projectionDir": (0, -1, 1), "xDirection":(1, 0, 0), "yDirection":(0, 0, 1), "showHidden":False}
    SVG_OPTS_TABLE_BACK_PROJECTION = {"width":500, "height":500, "projectionDir": (0, 1, 1), "xDirection": (1, 0, 0), "yDirection": (0, 0, 1), "showHidden": False}
    SVG_OPTS_ISOMETRIC_SOLID = {"width":400, "height":400, "projectionDir": (1, -1, 1), "xDirection": (-1, -1, 0), "yDirection": (0, 0, 1), "showHidden": False}
    SVG_OPTS_ISOMETRIC_HIDDEN = {"width":400, "height":400, "projectionDir": (1, -1, 1), "xDirection": (-1, -1, 0), "yDirection": (0, 0, 1), "showHidden": True}


    class Item:
        def __init__(self,  name, quantity=1, object=None, purpose=""):#, printed=False, printing_instructions="", tolerance=0.1):
            self.name = name
            self.quantity = quantity
            # if there is an object which represents this item (like MachineScrew)
            self.object = object
            #human readable description of what this is for
            self.purpose = purpose
            self.parent_BOM = None
        def __str__(self):
            return f"{self.quantity} x {self.name} ({self.purpose})"


    class PrintedPart:
        def __init__(self, name, object, tolerance=0.1, printing_instructions="", quantity=1, purpose="", modifier_objects=None, svg_options=None, is_model=False):
            self.name = name
            #CQ object
            self.object = object
            self.tolerance = tolerance
            #TODO how to store specific info about printing?
            self.printing_instructions = printing_instructions
            # human readable description of what this is for
            self.purpose = purpose
            self.quantity = quantity
            self.parent_BOM = None
            #if a modifier is useful for slicing, these are it
            self.modifier_objects = modifier_objects
            if self.modifier_objects is None:
                #dict of ["name": object]
                self.modifier_objects = {}

            #not a part that actually needs to be printed, just rendered (question to self - so why is it a PrintedPart?)
            self.is_model = is_model

            #bit crude, dict passed straight into the exportSVG function
            self.svg_options = svg_options
            if self.svg_options is None:
                self.svg_options = {}

        def get_root_name(self):
            '''
            get the name of just the top of the BOM
            '''
            return self.parent_BOM.get_root_name()

        def get_full_name(self):
            '''
            get the full path name of this item (eg clock_x_arbor_y)
            '''
            return self.parent_BOM.get_full_name()

        def get_filename(self):
            return f"{self.get_full_name()}_{self.name}.stl"

        def get_preview_filename(self):
            return f"{self.get_full_name()}_{self.name}.svg"
        #TODO decide how to get hold of the clock name properly
        def to_json(self):
            return {
                "file": self.get_filename(),
                "quantity": self.quantity,
                # "blurb": self.blurb
            }
        def __str__(self):
            blurb_string = ""
            inner_strings = []
            if len(self.purpose):
                inner_strings.append(self.purpose)
            if len(self.printing_instructions):
                inner_strings.append(self.printing_instructions)

            if len(inner_strings) > 0:
                blurb_string = f" ({': '.join(inner_strings)})"

            return f"{self.quantity} x {self.get_filename()}{blurb_string}"

        def export(self, path):
            self.export_STL(os.path.join(path,BillOfMaterials.PRINTABLES_PATH))
            self.export_SVG(os.path.join(path,BillOfMaterials.IMAGES_PATH))

        def export_STL(self, path):
            export_STL(object=self.object,object_name=self.name, clock_name=self.get_full_name(), path=path, tolerance=self.tolerance)
            for modifier_name in self.modifier_objects:
                export_STL(object=self.modifier_objects[modifier_name], object_name=self.name+f"_modifier_{modifier_name}", clock_name=self.get_full_name(), path=path, tolerance=self.tolerance)

        def export_SVG(self, path):
            if self.object is None:
                print(f"Cannot export {self.get_full_name()}_{self.name}.svg as object is None")
                return
            exportSVG(self.object,os.path.join(path,f"{self.get_full_name()}_{self.name}.svg"), opts=self.svg_options)


    def __init__(self, name, assembly_instructions="", template_path='docs/templates'):
        self.name = name
        self.parent = None
        self.items = []
        self.subcomponents = []
        self.printed_parts=[]
        self.assembly_instructions=assembly_instructions
        # list of PrintedParts automatically rendered and put before the assembly instructions
        self.assembled_models = []
        # list of PrintedParts available to place wherever wanted inside the assembly instructions using {render_[int]}
        self.renders = []
        # images to copy from the images dir into the clock output for including in markdown and pdf
        self.images = []
        self.template_path = template_path

    def add_image(self, image):
        self.images.append(image)

    def add_images(self, images):
        for image in images:
            self.add_image(image)

    def set_parent(self, parent_bom):
        self.parent = parent_bom

    def add_model(self, model_object, svg_preview_options = None):
        model = BillOfMaterials.PrintedPart(f"model_{len(self.assembled_models)}", model_object, printing_instructions="Assembled model, not for printing", svg_options=svg_preview_options)
        model.parent_BOM = self
        self.assembled_models.append(model)

    def add_render(self, render_object, svg_preview_options = None):
        render = BillOfMaterials.PrintedPart(f"render_{len(self.renders)}", render_object, printing_instructions="Model to be rendered to provide image for instructions", svg_options=svg_preview_options)
        render.parent_BOM = self
        self.renders.append(render)
        return len(self.renders) - 1

    def add_subcomponent(self, bom):
        '''
        add a whole BOM for a sub component
        '''
        if bom is None:
            return
        bom.set_parent(self)
        self.subcomponents.append(bom)

    def add_subcomponents(self, boms):
        for bom in boms:
            self.add_subcomponent(bom)

    def combine(self, bom):
        '''
        instead of adding a BOM as a subcomponent, take it and combine it with us
        '''
        if bom is None:
            return
        self.add_printed_parts(bom.printed_parts)
        self.add_items(bom.items)
        self.assembly_instructions += "\n\n"+bom.assembly_instructions
        self.add_subcomponents(bom.subcomponents)
        self.add_images(bom.images)
        self.renders += bom.renders
        self.assembled_models += bom.assembled_models
    def get_root_name(self):
        if self.parent is None:
            return self.name
        return self.parent.get_root_name()

    def tidy_name(self):
        #https://stackoverflow.com/a/71199182 adding in stripping for ( and )
        return re.sub(r"[/\\?%*\(*\)*#:|\"<>\x7F\x00-\x1F]", "", self.name.replace(" ", "_").lower().replace("#",'.'))
        # return self.name.replace(" ", "_").replace(")","").replace("(","").lower()

    def get_full_name(self):
        if self.parent is None:
            return self.tidy_name()
        return f"{self.parent.get_full_name()}_{self.tidy_name()}"
    def add_thing(self, thing, list):
        found = False
        thing.parent_BOM = self
        for i, lookup_item in enumerate(list):
            # unlikely to hit this often
            if thing.name == lookup_item.name and thing.purpose == lookup_item.purpose:
                found = True
                list[i].quantity += thing.quantity
        if not found:
            list.append(thing)

    def add_item(self, item):
        '''
        add an item to this BOM
        '''
        self.add_thing(item, self.items)

    def add_printed_part(self, part):
        self.add_thing(part, self.printed_parts)

    def add_printed_parts(self, printed_parts):
        for part in printed_parts:
            self.add_printed_part(part)
    def add_items(self, items):
        for item in items:
            self.add_item(item)

#     def __str__(self):
#         items_string = "\n".join([str(item) for item in self.items])
#         subcomponents_string = "\n".join([str(subcomponent) for subcomponent in self.subcomponents])
#         return f'''{self.name} BOM:
# {items_string}
# Subcomponents:
# {subcomponents_string}
# '''
    def to_json(self):
        '''
        Using the json stringify as a crude way of formatting the entire BOM neatly
        '''
        json = {
            "name": self.name,
        }
        if len(self.assembly_instructions) > 0:
            json["assembly_instructions"] = self.assembly_instructions
        if len(self.items) > 0:
            json["items"]= [str(item) for item in self.items]
        if len(self.printed_parts) > 0:
            json["printed_parts"] = [str(printed_part) for printed_part in self.printed_parts]
        if len(self.subcomponents) > 0:
            json["subcomponents"]= [component.to_json() for component in self.subcomponents]

        if self.parent is None:
            json["full_item_list"] = self.get_consolidated_items()
        return json


    def get_items(self, include_subcomponents=False):
        items = self.items.copy()
        if include_subcomponents:
            for subcomponent in self.subcomponents:
                items += subcomponent.get_items(include_subcomponents=include_subcomponents)
        return items

    def get_consolidated_items(self):
        '''
        Get a single list of items for all subcomponents
        '''
        unique_items = {}
        for item in self.get_items(include_subcomponents=True):
            if item.name in unique_items:
                unique_items[item.name] += item.quantity
            else:
                unique_items[item.name] = item.quantity
        # return unique_items
        #https://stackoverflow.com/questions/9001509/how-do-i-sort-a-dictionary-by-key#comment89671526_9001529
        sorted_unique_items = dict(sorted(unique_items.items()))
        return sorted_unique_items

    def get_instructions(self, heading_level=1):
        '''
        get text for a markdown set of instructions

        TODO more generic instructions - but I think this will need to be done from Assembly. This will just output a pretty summary of the BOM
        '''

        # duration = "an eight day"
        #
        # subs = {"title": self.name,
        #         "duration": duration,
        #         }
        # with open(os.path.join(self.template_path, "pendulum_clock_intro.md"),'r', encoding="utf8") as f:
        #     intro_src = Template(f.read())
        #     intro = intro_src.substitute(subs)
        #
        # instructions = f"""
        # {intro}
        # """
        heading = "".join(["#" for i in range(heading_level)])
        #supposardly meant to be 4 spaces, but everything i've used (VS code + github) wants 2
        #only need this for sublists, not lists in sub-headings!
        list_spacing = "  "#"".join([" " for i in range(heading_level*2)])
        preview = ""
        assembly_instructions = self.assembly_instructions
        if len(self.renders) > 0:
            render_subs = {}
            for i, render_part in enumerate(self.renders):
                render_subs[f"render{i}"] =f"![{self.name} Render](./{os.path.join(BillOfMaterials.MODEL_PATH, BillOfMaterials.IMAGES_PATH, render_part.get_preview_filename())} \"{self.name} Render\")"
            assembly_instructions = Template(assembly_instructions).substitute(render_subs)


        for model in self.assembled_models:
            preview += f"![{self.name} Render](./{os.path.join(BillOfMaterials.MODEL_PATH, BillOfMaterials.IMAGES_PATH, model.get_preview_filename())} \"{self.name}\")"
        instructions = f"""{heading} {self.name}
{preview}

{assembly_instructions}
"""
        if self.parent is None:
            consolidated_items = self.get_consolidated_items()
            parts_strings = [f"{list_spacing}- {consolidated_items[item]} x {item}" for item in consolidated_items]
            if len(parts_strings) > 0:
                parts = "\n".join(parts_strings)
                instructions+= f"""{heading}# Full (non-printed) Parts List
{parts}
"""
        else:
            if len(self.items) > 0:
                items = self.get_items()
                items.sort(key = lambda x: x.name)
                parts_strings = []
                for item in items:
                    parts_string = f"{list_spacing}- {item.quantity} x {item.name}"
                    if len(item.purpose) > 0:
                        parts_string += f": {item.purpose}"
                    parts_strings.append(parts_string)
                parts = "\n".join(parts_strings)
                instructions += f"""{heading}# Parts
{parts}
"""

        if len(self.printed_parts) > 0:
            printed_parts = self.printed_parts
            printed_parts.sort(key = lambda x : x.get_filename())
            printed_parts_string = ""
            for part in printed_parts:
                stl_string = f"{part.quantity} x {part.get_filename()}"
                printed_parts_string +=f"\n{list_spacing} - {stl_string}"
                sublist = []
                if len(part.purpose) > 0:
                    sublist.append(part.purpose)
                if len(part.printing_instructions) > 0:
                    sublist.append(part.printing_instructions)
                if len(sublist) > 0:
                    for subitem in sublist:
                        printed_parts_string+=f"\n{list_spacing}{list_spacing} - {subitem}"
            # printed_parts_strings = [f"{list_spacing}- {part.quantity} x {part.get_filename()}" for part in self.printed_parts]
            # printed_parts_string = '\n'.join(printed_parts_strings)
            instructions += f"""{heading}# Printed Parts
{printed_parts_string}
"""

        for component in self.subcomponents:
            # instructions+="\n<div style=\"page-break-after: always;\"></div>\n"
            instructions+= f"{component.get_instructions(heading_level+1)}"

        return instructions

    def export(self, out_path="out", image_path="images/"):

        if self.parent is None:
            out_path = os.path.join(out_path, self.tidy_name())

        # make if it doesn't exist
        pathlib.Path(out_path).mkdir(parents=True, exist_ok=True)
        if self.parent is None:
            pathlib.Path(os.path.join(out_path, BillOfMaterials.IMAGES_PATH)).mkdir(parents=True, exist_ok=True)
            pathlib.Path(os.path.join(out_path, BillOfMaterials.PRINTABLES_PATH)).mkdir(parents=True, exist_ok=True)
            pathlib.Path(os.path.join(out_path, BillOfMaterials.MODEL_PATH)).mkdir(parents=True, exist_ok=True)
            pathlib.Path(os.path.join(out_path, BillOfMaterials.MODEL_PATH, BillOfMaterials.IMAGES_PATH)).mkdir(parents=True, exist_ok=True)
            pathlib.Path(os.path.join(out_path, BillOfMaterials.MODEL_PATH, BillOfMaterials.PRINTABLES_PATH)).mkdir(parents=True, exist_ok=True)

        for printable in self.printed_parts:
            printable.export(out_path)

        for component in self.subcomponents:
            component.export(out_path)

        for image in self.images:
            shutil.copyfile(os.path.join(image_path, image), os.path.join(out_path, image))

        for model in self.assembled_models + self.renders:
            model.export(os.path.join(out_path, BillOfMaterials.MODEL_PATH))

        #export all the subcomponents and models first so the SVG files exist for the PDF generation below
        if self.parent is None:
            with open(os.path.join(out_path,'bom.json'), 'w', encoding='utf-8') as f:
                json.dump(self.to_json(), f, ensure_ascii=False, indent=4)

            markdown_instructions = self.get_instructions()
            with open(os.path.join(out_path,f'{self.tidy_name()}.md'), 'w', encoding='utf-8') as f:
                f.write(markdown_instructions)

            # import typing
            # import fitz
            # def override_save_func(self, file_name: typing.Union[str, pathlib.Path]) -> None:
            #     """Save pdf to file."""
            #     self.writer.close()
            #     doc = fitz.open("pdf", self.out_file)
            #     doc.set_metadata(self.meta)
            #     if self.toc_level > 0:
            #         doc.set_toc(self.toc)
            #     #see if clean prevents SVGs being rasterised (didn't work)
            #     doc.save(file_name, clean=1, pretty=1)
            #     doc.close()
            # setattr(MarkdownPdf, 'save2', override_save_func)

            setting_up_instructions = ""
            with open(os.path.join("docs", "Setup.md"), 'r') as setupdocfile:
                setting_up_instructions = setupdocfile.read()

            pdf = MarkdownPdf()
            pdf.add_section(Section(markdown_instructions, root=out_path))
            pdf.add_section(Section(setting_up_instructions, root='docs'))

            # pdf.save2(os.path.join(out_path,f'{self.tidy_name()}.pdf'))
            pdf.save(os.path.join(out_path, f'{self.tidy_name()}.pdf'))
