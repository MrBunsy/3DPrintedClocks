import cadquery as cq
from cadquery import exporters
from .utility import *

def get_star(star_thick=3, star_size = 75):


    star_arm_wide = star_size * 0.2
    secondary_star_arm_length = star_size * 0.3
    secondary_star_arm_wide = star_arm_wide*0.9

    star = cq.Workplane("XY").tag("base").moveTo(-star_size/2,0).lineTo(0, star_arm_wide/2).lineTo(star_size/2, 0).lineTo(0, -star_arm_wide/2).close().extrude(star_thick)
    star = star.workplaneFromTagged("base").moveTo(-star_arm_wide / 2, 0).lineTo(0, star_size / 2).lineTo(star_arm_wide / 2, 0).lineTo(0, -star_size/2).close().extrude(star_thick)

    secondary_top_left = polar(math.pi*3/4,secondary_star_arm_length)
    secondary_top = (0, secondary_star_arm_wide/2)
    star = star.workplaneFromTagged("base").moveTo(secondary_top_left[0], secondary_top_left[1]).lineTo(secondary_top[0], secondary_top[1]).lineTo(-secondary_top_left[0], -secondary_top_left[1])\
        .lineTo(-secondary_top[0], -secondary_top[1]).close().extrude(star_thick)

    star = star.workplaneFromTagged("base").moveTo(-secondary_top_left[0], secondary_top_left[1]).lineTo(-secondary_top[0], secondary_top[1]).lineTo(secondary_top_left[0], -secondary_top_left[1]) \
        .lineTo(secondary_top[0], -secondary_top[1]).close().extrude(star_thick)

    return star