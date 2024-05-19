from .types import *
from .geometry import *
from .utility import *
import cadquery as cq

#not sure where to put the pillars, maybe their own file?
def fancy_pillar(r, length, clockwise=True, style=PillarStyle.BARLEY_TWIST):
    if style == PillarStyle.BARLEY_TWIST:
        return fancy_pillar_barley_twist(r, length, clockwise)
    elif style == PillarStyle.BLOBS:
        return fancy_pillar_blobs(r, length, clockwise)
    elif style == PillarStyle.COLUMN:
        return fancy_pillar_column(r, length, clockwise)
    elif style == PillarStyle.TWISTY:
        return fancy_pillar_twisty(r, length, clockwise)
    elif style == PillarStyle.CLASSIC:
        return fancy_pillar_classic(r, length, clockwise)
    else:
        raise NotImplementedError("Pillar style {} not yet implemented".format(style))
def fancy_pillar_twisty(r, length, clockwise=True):

    dir = 1 if clockwise else -1
    # outline = get_smooth_knob_2d(inner_r=r*0.8, outer_r=r, knobs=3)
    outline = cq.Workplane("XY").moveTo(dir*r*0.1,0).circle(r*0.8)
    twists_per_mm = 4 / 100
    twists = twists_per_mm * length
    angle = 360 * twists
    if not clockwise:
        angle *= -1

    pillar = outline.twistExtrude(length, angleDegrees=angle)

    return pillar


def fancy_pillar_classic(r, length, clockwise=True):
    '''
    the top and bottom bit copy-pasted from barley twist, could probably consider abstracting out
    '''

    circle = cq.Workplane("XY").circle(r)
    curve_end_gap = min(2, r * 0.07)

    curve_r = r * 0.25 - curve_end_gap

    inner_r = r * 0.85
    base_thick = curve_r * 1.5
    next_bulge_thick = curve_r * 2
    base_outline = (cq.Workplane("XZ").moveTo(0, 0).lineTo(r, 0).spline(includeCurrent=True, listOfXYTuple=[(inner_r, base_thick)], tangents=[(0, 1), (-0.5, 0.5)])
                    .spline(includeCurrent=True, listOfXYTuple=[(inner_r, base_thick + next_bulge_thick)], tangents=[(1, 1), (-1, 1)]).lineTo(0, base_thick + next_bulge_thick).close())
    base = base_outline.sweep(circle)
    centre_length = length - 2*(base_thick + next_bulge_thick)

    central_ring_r = r*0.75
    central_ring_thick = base_thick + next_bulge_thick
    central_ring_curve_r = central_ring_thick

    central_ring = (cq.Workplane("XZ").moveTo(0, -central_ring_thick/2).lineTo(central_ring_r,-central_ring_thick/2).radiusArc((central_ring_r, central_ring_thick/2),-central_ring_curve_r)
                    .lineTo(0, central_ring_thick/2).close()).sweep(circle)



    cone = cq.Solid.makeCone(inner_r,central_ring_r, length/2 - central_ring_thick/2 - base_thick - next_bulge_thick)
    centre = central_ring.translate((0,0,length/2)).union(cone.translate((0,0, base_thick + next_bulge_thick))).union(cone.rotate((0,0,0),(1,0,0),180).translate((0,0,length-base_thick - next_bulge_thick)))


    pillar = base.union(centre).union(base.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, length)))

    return pillar


def fancy_pillar_blobs(r, length, clockwise=True):

    blob_desired_height = r*1.6

    blobs = math.ceil(length/blob_desired_height)
    blob_height = length/blobs

    pillar = cq.Workplane("XY")

    for blob in range(blobs):
        pillar = pillar.union(cq.Workplane("XY").sphere(r).translate((0,0,blob*blob_height + blob_height/2)))
        # pillar = pillar.union(cq.Workplane("XY").add(cq.Solid.makeSphere(radius=r)).rotate((0,0,0),(1,0,0),180).translate((0, 0, blob * blob_height + blob_height / 2)))

    pillar = pillar.union(cq.Workplane("XY").circle(r).extrude(blob_height/2))
    pillar = pillar.union(cq.Workplane("XY").circle(r).extrude(blob_height / 2).translate((0,0,length - blob_height/2)))

    pillar = pillar.intersect(cq.Workplane("XY").circle(r*2).extrude(length))

    return pillar



def fancy_pillar_barley_twist(r, length, clockwise=True):
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