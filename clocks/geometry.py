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
    line = Line(from_pos, anotherPoint=to_pos)
    midpoint = average_of_two_points(from_pos, to_pos)
    nighty_deg = math.pi/2 * (1 if radius > 0 else -1)
    from_midpoint_to_centre_angle = line.get_angle() + nighty_deg

    wide_radius = wide / 2 * (1 if radius > 0 else -1)


    #sagitta to work out where the centre should be
    l = distance_between_two_points(from_pos, to_pos)
    s = radius - math.sqrt(radius**2 - 0.25*l**2)
    
    centre = np_to_set(np.add(midpoint, polar(from_midpoint_to_centre_angle, radius-s)))

    from_line = Line(centre, anotherPoint=from_pos)
    to_line = Line(centre, anotherPoint=to_pos)

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
        line = line.union(cq.Workplane("XY").rect(wide,length).extrude(thick).rotate((0,0,0), (0,0,1), radToDeg(angle)).translate(centre))
        if style == StrokeStyle.ROUND:
            line = line.union(cq.Workplane("XY").circle(wide/2).extrude(thick).translate(point))

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

#not sure where to put this
def fancy_pillar(r, length, clockwise=True, style=PillarStyle.BARLEY_TWIST):
    '''
    produce a fancy turned-wood style pillar
    '''
    circle = cq.Workplane("XY").circle(r)

    ridge_length = min(3, length*0.1)
    curve_end_gap = min(2, r*0.07)
    inner_r = r*0.75
    curve_r = r - inner_r - curve_end_gap

    #can't figure out how to use mirror properly, so building whole pillar despite being same on both ends
    #actually I need this as the pillar needs to be printable, so I can remove overhangs on the second half
    if False:
        pillar_outline = (cq.Workplane("XZ").moveTo(0, 0).lineTo(r, 0).line(0, ridge_length).radiusArc((inner_r + curve_end_gap, ridge_length + curve_r), curve_r).line(-curve_end_gap, 0).lineTo(inner_r,length - ridge_length - curve_r)
                      .line(curve_end_gap, curve_end_gap*0.75).radiusArc((r, length - (ridge_length)), curve_r*1.5).line(0, ridge_length).lineTo(0, length)).close()
        pillar = pillar_outline.sweep(circle)
    else:
        ridge_length = min(10, length*0.1)
        inner_r = r * 0.85
        base_thick = curve_r*1.5
        next_bulge_thick = curve_r*2
        base_outline = (cq.Workplane("XZ").moveTo(0, 0).lineTo(r, 0).spline(includeCurrent=True, listOfXYTuple=[(inner_r, base_thick)], tangents=[(0,1),(-0.5,0.5)])
                          .spline(includeCurrent=True, listOfXYTuple=[(inner_r, base_thick + next_bulge_thick)], tangents=[(1,1),(-1,1)]).lineTo(0,base_thick + next_bulge_thick).close())
        base = base_outline.sweep(circle)

        twists_per_mm = 1/100

        twists = twists_per_mm * (length - base_thick*2 - next_bulge_thick*2)#math.ceil(length/100)/2
        angle = 360*twists
        if not clockwise:
            angle *= -1
        barley_twist = cq.Workplane("XY").polygon(8,inner_r*2).twistExtrude(length - 2*(base_thick + next_bulge_thick), angle).translate((0,0,base_thick + next_bulge_thick))

        pillar = base.union(barley_twist).union(base.rotate((0,0,0),(1,0,0),180).translate((0,0,length)))


    return pillar#.union(pillar.mirrorX().translate((0,0,length/2)))