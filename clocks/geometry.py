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
        print(i, centre)
        line = line.union(cq.Workplane("XY").rect(wide,length).extrude(thick).rotate((0,0,0), (0,0,1), radToDeg(angle)).translate(centre))
        if style == StrokeStyle.ROUND:
            line = line.union(cq.Workplane("XY").circle(wide/2).extrude(thick).translate(point))

    if style == StrokeStyle.ROUND:
        line = line.union(cq.Workplane("XY").circle(wide / 2).extrude(thick).translate(points[-1]))

    return line