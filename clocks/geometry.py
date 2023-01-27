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
        line = line.union(cq.Workplane("XY").circle(wide / 2).extrude(thick).translate(points[-1]))

    return line