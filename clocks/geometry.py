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
from math import sin, cos, pi, floor
import cadquery as cq
from .utility import *
from .types import *

def get_smooth_knob_2d(inner_r, outer_r, knobs=5):
    def shape_func(t):
        angle = t * math.pi * 2
        distance = math.pi * 2 * knobs
        r_diff = outer_r - inner_r
        return polar(angle, inner_r + r_diff/2 + math.sin(t * distance) * r_diff/2)

    return cq.Workplane('XY').parametricCurve(lambda t: shape_func(t), maxDeg=12)


# def get_stroke_semicircle(centre, r, angle0, angle1, line_width, thick):
#     '''
#     partial circle with rounded ends, clockwise from angle0 to angle1
#     difference in angle has to be less than pi
#     '''
#
#     start_outer = polar(angle0, r + line_width/2)
#     start_inner = polar(angle0, r - line_width/2)
#     mid_angle = angle0 - abs(angle0 - angle1)/2
#     mid_outer = polar(mid_angle, r + line_width/2)
#     mid_inner = polar(mid_angle, r - line_width / 2)
#     end_outer = polar(angle1, r + line_width/2)
#     end_inner = polar(angle1, r - line_width / 2)
#     circle = cq.Workplane("XY").moveTo(start_outer[0], start_outer[1]).radiusArc(mid_outer, r+line_width/2).radiusArc(end_outer, r+line_width/2).radiusArc(end_inner, line_width/2).\
#         radiusArc(start_inner, -(r-line_width/2)).radiusArc(start_outer, line_width/2).close().extrude(thick).translate(centre)
#
#     return circle

def get_stroke_arc(from_pos, to_pos, radius, wide, thick, style=StrokeStyle.ROUND, fill_in=False):
    '''
    if fill_in then it's more of a rounded semicircle

    negative radius seems to be broken in some cases? workaround is to adjust order of from and to pos
    '''

    #temp hack
    if radius < 0:
        radius *= -1
        from_pos, to_pos = to_pos, from_pos

    line = Line(from_pos, another_point=to_pos)
    midpoint = average_of_two_points(from_pos, to_pos)
    nighty_deg = math.pi/2 * (1 if radius > 0 else -1)
    from_midpoint_to_centre_angle = line.get_angle() + nighty_deg

    wide_radius = wide / 2 * (1 if radius > 0 else -1)


    #sagitta to work out where the centre should be
    l = get_distance_between_two_points(from_pos, to_pos)
    # if radius**2 - 0.25*l**2 < 0:
    #     #assume aproximately zero and that this is a quarter of a circle (bold assumption)
    #     s = radius
    # else:
    s = radius - math.sqrt(radius**2 - 0.25*l**2)
    
    centre = np_to_set(np.add(midpoint, polar(from_midpoint_to_centre_angle, radius-s)))

    from_line = Line(centre, another_point=from_pos)
    to_line = Line(centre, another_point=to_pos)

    inner_from = np_to_set(np.add(centre, polar(from_line.get_angle(), radius - wide / 2)))
    outer_from = np_to_set(np.add(centre, polar(from_line.get_angle(), radius + wide / 2)))
    inner_to = np_to_set(np.add(centre, polar(to_line.get_angle(), radius - wide / 2)))
    outer_to = np_to_set(np.add(centre, polar(to_line.get_angle(), radius + wide / 2)))

    if fill_in:
        if style == StrokeStyle.ROUND:
            base_from = np_to_set(np.add(from_pos, polar(from_midpoint_to_centre_angle, wide/2)))
            base_to = np_to_set(np.add(to_pos, polar(from_midpoint_to_centre_angle, wide / 2)))
            arc = cq.Workplane("XY").moveTo(base_from[0], base_from[1]).lineTo(base_to[0], base_to[1])
            # arc = arc.radiusArc(inner_to, wide_radius+0.00001)
        else:
            #direct line
            arc = cq.Workplane("XY").moveTo(inner_from[0], inner_from[1]).lineTo(inner_to[0], inner_to[1])
    else:
        #the inner curve
        arc = cq.Workplane("XY").moveTo(inner_from[0], inner_from[1]).radiusArc(inner_to, -(radius-wide/2))

    if style == StrokeStyle.ROUND:
        arc = arc.radiusArc(outer_to, wide_radius+0.00001)
    else:
        arc = arc.lineTo(outer_to[0], outer_to[1])

    arc = arc.radiusArc(outer_from, radius + wide/2)

    if style == StrokeStyle.ROUND:
        if fill_in:
            arc = arc.radiusArc(base_from, wide_radius + 0.00001)
        else:
            arc = arc.radiusArc(inner_from, wide_radius+0.00001)
    else:
        arc = arc.lineTo(inner_from[0], inner_from[1])

    arc = arc.close().extrude(thick)

    return arc

        # for pos in [from_pos, to_pos]:
        #     arc = arc.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(wide/2).extrude(thick))

class ArithmeticSpiral:
    def __init__(self, r, start_pos=None, x_scale=1, y_scale=1, start_angle=0, power=1, clockwise=False):
        '''
        if clockwise then starting angle must be -ve
        '''
        self.r = r
        self.start_pos = start_pos
        if self.start_pos is None:
            self.start_pos = (0,0)
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.start_angle = start_angle
        self.power = power
        self.clockwise = clockwise
    def get_pos(self, angle):

        dir = 1
        if self.clockwise:
            dir = -1

        r = self.r * (dir*angle + self.start_angle)/(math.pi*2)
        r = r ** self.power
        pos = polar(angle, r)

        return (pos[0]*self.x_scale + self.start_pos[0], pos[1] * self.y_scale + self.start_pos[1])

    def get_tangent(self, angle):
        if self.clockwise:
            pre_pos = self.get_pos(angle + 0.01)
            post_pos = self.get_pos(angle - 0.01)
        else:
            pre_pos = self.get_pos(angle - 0.01)
            post_pos = self.get_pos(angle + 0.01)
        line = Line(pre_pos, another_point=post_pos)
        return line.dir

    def get_draw_info(self, from_angle, to_angle, points_per_spiral=15):
        spiral_points = []
        spiral_directions = []

        spirals = abs(from_angle - to_angle)/(math.pi*2)

        clockwise = 1 if from_angle < to_angle else -1

        for i in range(math.ceil(points_per_spiral*spirals) + 1):
            angle =from_angle + clockwise*i*math.pi*2/points_per_spiral
            pos = self.get_pos(angle)
            dir = self.get_tangent(angle)
            spiral_points.append(pos)
            spiral_directions.append(dir)

        return {
            "points": spiral_points,
            "tangents": spiral_directions
        }

    def draw(self, from_angle, to_angle, wide, thick, points_per_spiral=15):
        info = self.get_draw_info(from_angle, to_angle, points_per_spiral)
        spiral_points = info["points"]
        spiral_directions = info["tangents"]

        twirly = cq.Workplane("XY")

        for i in range(len(spiral_points)-1):
            from_pos = spiral_points[i]
            from_dir = spiral_directions[i ]
            to_pos = spiral_points[i + 1]
            to_dir = spiral_directions[(i+1)]
            twirly = twirly.union(get_stroke_curve(from_pos, to_pos, from_dir, to_dir, wide, thick))

        return twirly


def get_stroke_curve(start, end, start_dir, end_dir, wide, thick, style=StrokeStyle.SQUARE):
    '''
    this doesn't actually work in many cases :(
    '''

    start_line = Line(start, direction=start_dir)
    
    start_clockwise_dir = start_line.get_perpendicular_direction(clockwise=True)
    start_anticlockwise_dir = start_line.get_perpendicular_direction(clockwise=False)
    
    start_clockwise_pos = np_to_set(np.add(start, np.multiply(start_clockwise_dir, wide/2)))
    start_anticlockwise_pos = np_to_set(np.add(start, np.multiply(start_anticlockwise_dir, wide / 2)))

    end_line = Line(end, direction=end_dir)

    end_clockwise_dir = end_line.get_perpendicular_direction(clockwise=True)
    end_anticlockwise_dir = end_line.get_perpendicular_direction(clockwise=False)

    end_clockwise_pos = np_to_set(np.add(end, np.multiply(end_clockwise_dir, wide / 2)))
    end_anticlockwise_pos = np_to_set(np.add(end, np.multiply(end_anticlockwise_dir, wide / 2)))

    curve = cq.Workplane("XY").spline([start_clockwise_pos, end_clockwise_pos], tangents=[start_dir, end_dir]).lineTo(end_anticlockwise_pos[0], end_anticlockwise_pos[1]).spline([end_anticlockwise_pos, start_anticlockwise_pos], tangents=[backwards_vector(end_dir), backwards_vector(start_dir)]).close().extrude(thick)

    if style == StrokeStyle.ROUND:
        for pos in [start, end]:
            curve = curve.union(cq.Workplane("XY").circle(wide/2).extrude(thick).translate(pos))

    return curve
    

def get_stroke_line(original_points, wide, thick, style=StrokeStyle.ROUND, loop=False):

    points = original_points.copy()

    if loop:
        points.append(original_points[0])

    line = cq.Workplane("XY")

    for i, point in enumerate(points):
        if i > len(points) - 2:
            break
        next_point = points[i+1]

        angle = math.atan2(next_point[1] - point[1], next_point[0] - point[0]) + math.pi/2
        centre = ((point[0] + next_point[0])/2, (point[1] + next_point[1])/2)
        length = np.linalg.norm(np.subtract(next_point, point))
        line = line.union(cq.Workplane("XY").rect(wide,length).extrude(thick).rotate((0,0,0), (0,0,1), rad_to_deg(angle)).translate(centre))
        if style == StrokeStyle.ROUND:
            try:
                line = line.union(cq.Workplane("XY").circle(wide/2).extrude(thick).translate(point))
            except:
                print(f"Failed to add circle on stroke line at {point}")

    if style == StrokeStyle.ROUND:
        #cap off the end
        line = line.union(cq.Workplane("XY").circle(wide / 2).extrude(thick).translate(points[-1]))

    return line

def get_angle_of_chord(radius, chord_length):
    '''
    In many places I've assumed that the arc length ~= chord length and just run with it, but occasionally I need accuracy


    the chord will form an isosceles triangle, but I don't know the length of the triangle yet.

    I know the length of the chord (width of triangle) and the radius (hypotenuse of triangle) so I can find the height by finding the sagitta of the arc
    '''

    # #for sagitta
    # l = chord_length
    # r = radius
    # sagitta = r - math.sqrt(r**2 - 0.25*l**2)
    #
    # triangle_height = radius - sagitta
    #
    # #split the isosceles triangle into two right angled triangles

    #r*sin(theta) = half the chord

    half_angle = math.asin((chord_length/2) / radius)

    return half_angle*2

def rationalise_angle(angle_radians):
    '''
    there's probably a proper term for this - ensure 0 <= angle < math.pi*2
    '''
    angle = angle_radians % (math.pi * 2)

    while angle < 0:
        angle += math.pi * 2
    return angle


def get_quadrant(angle_radians):
    '''
    return which quadrant an angle is in in the form of (x,y)
    '''
    angle = rationalise_angle(angle_radians)


    if angle <= math.pi/2:
        return (1, 1)
    if angle <= math.pi:
        return (-1, 1)
    if angle <= math.pi*1.5:
        return (-1, -1)
    return (1, -1)

#https://stackoverflow.com/a/6802723
def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])

def rotate_vector(vector, axis, angle_rad):
    rotate_vector = list(vector)
    if len(rotate_vector) < 3:
        rotate_vector += [0]
    return np_to_set(np.dot(rotation_matrix(axis, angle_rad), rotate_vector))

def backwards_vector(vector):
    '''
    get 2D vector pointing in opposite direction
    '''
    return (-vector[0], -vector[1])

def get_point_two_circles_intersect(pos0, distance0, pos1, distance1, anticlockwise_from_0=True, in_direction=None):
    '''
    Since there are always two points where overlapping circles overlap, we need a way to distinguish.
    if in_direction is a vector, will find point relative to average circle position which is +ve along in_direction, otherwise we'll use anticlockwise_from_0

    needs a better name. (done? I've realised it's basically the intersection of two circles)
    Given two positions, a and b, find the position of another point when you know all the distances, using cosine law
    I've done this all over the place in calculating gear train placement in plates, but let's finally abstract it out so I can re-use it cleanly
    '''
    #putting into standard form for cosine rule
    c = distance1
    a = distance0
    b = get_distance_between_two_points(pos0, pos1)

    #cosine rule
    angle = math.acos((a**2 + b**2 - c**2)/(2*a*b))

    a_to_b = np_to_set(np.subtract(pos1, pos0))
    a_to_b_angle = math.atan2(a_to_b[1], a_to_b[0])
    if in_direction is not None:
        point_angles = [a_to_b_angle + dir*angle for dir in [-1,1]]
        test_points = [np_to_set(np.add(pos0, polar(point_angle, distance0))) for point_angle in point_angles]
        average_centre = average_of_two_points(pos0, pos1)

        for point in test_points:
            relative_point = np.subtract(point, average_centre)
            if np.dot(relative_point, in_direction) >= 0:
                return point
        #shouldn't be able to reach here?
        raise ValueError("unable to find point circles intersect")

    else:
        dir = 1 if anticlockwise_from_0 else -1
        point_angle = a_to_b_angle + dir*angle

        return np_to_set(np.add(pos0, polar(point_angle, distance0)))

def get_incircle_for_regular_polygon(outer_radius, sides):
    polygon_side_length = 2 * outer_radius * math.sin(math.pi / sides)
    incircle_radius = polygon_side_length / (2 * math.tan(math.pi/sides))
    return incircle_radius