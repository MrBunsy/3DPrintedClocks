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
    return npToSet(np.dot(rotation_matrix(axis, angle_rad), rotate_vector))