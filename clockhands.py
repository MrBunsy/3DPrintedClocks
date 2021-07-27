import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass



def clockhand(style="simple",fixing="rectangle",fixing_d1=1.5,fixing_d2=2.5,length=25, thick=1.6, hour=False):
    '''
    fixings: rectangle, square, circle
    '''
    #base_d = (fixing_d2 if fixing_d2 > fixing_d1 else fixing_d1)*3
    #nominal width of base and sticky out bits
    width = length*0.3
    end_d = width*0.1

    if hour:
        length = length*0.8
        if style is "simple":
            width = width*1.2
    base_r = width/2

    if base_r < fixing_d1*0.9:
        base_r = fixing_d1*1.5/2

    hand = cq.Workplane("XY").tag("base").circle(radius=base_r).extrude(thick)
    #hand = hand.workplaneFromTagged("base").moveTo(0,length/2).rect(length*0.1,length).extrude(thick)

    if style is "simple":
        hand = hand.workplaneFromTagged("base").moveTo(width*0.4,0).lineTo(end_d/2, length).radiusArc((-end_d/2,length),-end_d/2).lineTo(-width*0.4,0).close().extrude(thick)
    elif style is "cuckoo":

        centrehole_y = length * 0.6
        centrehole_r = width*0.2


        #hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).threePointArc((end_d *0.75, length/2),(end_d / 2, length)).radiusArc(
        #    (-end_d / 2, length), -end_d / 2).threePointArc((-end_d *0.75, length/2),(-width * 0.4, 0)).close().extrude(thick)

        # hand = hand.workplaneFromTagged("base").moveTo(width * 0.25, length*0.3).lineTo(end_d / 2, length).radiusArc(
        #     (-end_d / 2, length), -end_d / 2).lineTo(-width * 0.25, length*0.3).close().extrude(thick)
        hand = hand.workplaneFromTagged("base").moveTo(width * 0.2, length * 0.3).lineTo(end_d / 2, length).threePointArc((0,length+end_d/2),(-end_d/2,length)).lineTo(-width * 0.2, length * 0.3).close().extrude(thick)

        #extra round bits towards the end of the hand
        little_sticky_out_dist = width * 0.3
        little_sticky_out_d = width*0.2
        little_sticky_out_d2 = width * 0.2
        little_sticky_out_dist2 = width * 0.2
        stickyoutblobs = hand.workplaneFromTagged("base")
        for angle_d in [45]:
            angle = math.pi*angle_d/180
            #just circle, works but needs more
            stickyoutblobs = stickyoutblobs.moveTo(0+math.cos(angle)*little_sticky_out_dist2, centrehole_y+little_sticky_out_d2*0.25+math.sin(angle)*little_sticky_out_dist2).circle(little_sticky_out_d2)
            #hand =  hand.workplaneFromTagged("base").moveTo(0+math.cos(angle+math.pi/2)*little_sticky_out_d/2,centrehole_y+math.sin(angle+math.pi/2)*little_sticky_out_d/2).lineTo()
            #hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y).rot
        hand = stickyoutblobs.mirrorY().extrude(thick)

        hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y-centrehole_r).spline([(little_sticky_out_dist*1.6,centrehole_y-little_sticky_out_d*0.6),(little_sticky_out_dist*1.6,centrehole_y+little_sticky_out_d*0.2),(0,centrehole_y)],includeCurrent=True)\
            .mirrorY().extrude(thick)

        petalend=(width*0.6,length*0.45)

        #petal-like bits near the centre of the hand
        hand = hand.workplaneFromTagged("base").lineTo(width*0.1,0).spline([(petalend[0]*0.3, petalend[1]*0.1),(petalend[0]*0.7, petalend[1]*0.4),(petalend[0]*0.6, petalend[1]*0.75),petalend],includeCurrent=True)\
            .line(0,length*0.005).spline([(petalend[0]*0.5,petalend[1]*0.95),(0,petalend[1]*0.8)], includeCurrent=True).mirrorY()
        # return hand
        hand = hand.extrude(thick)
        #cut bits out
        #roudn bit in centre of knobbly bit
        hand = hand.moveTo(0,centrehole_y).circle(centrehole_r).cutThruAll()
        heartbase = base_r + length*0.025#length*0.175

        hearttop = length*0.425
        heartheight = hearttop-heartbase
        heartwidth=length*0.27*0.3#width*0.3
        #heart shape (definitely not a dick)
        #hand = hand.moveTo(0, heartbase).spline([(heartwidth*0.6,heartbase*0.9),(heartwidth*0.8,heartbase+heartheight*0.15),(heartwidth*0.6,heartbase+heartheight*0.4),(heartwidth*0.3,heartbase + heartheight/2)],includeCurrent=True).lineTo(heartwidth*0.5,heartbase + heartheight*0.75).lineTo(0,hearttop).mirrorY().cutThruAll()
        hand = hand.moveTo(0, heartbase).spline(
            [(heartwidth * 0.6, heartbase * 0.9), (heartwidth * 0.8, heartbase + heartheight * 0.15),
             (heartwidth * 0.6, heartbase + heartheight * 0.4), (heartwidth * 0.3, heartbase + heartheight / 2)],
            includeCurrent=True).lineTo(heartwidth * 0.5, heartbase + heartheight * 0.75).lineTo(0,
                                                                                                hearttop).mirrorY()#.cutThruAll()
        # return hand.extrude(thick*2)
        hand = hand.cutThruAll()
    if fixing is "rectangle":
        hand = hand.moveTo(0,0).rect(fixing_d1,fixing_d2).cutThruAll()
    elif fixing is "circle":
        hand = hand.moveTo(0,0).circle(fixing_d1/2).cutThruAll()


    return hand

minicuckoo_min=clockhand(style="cuckoo", thick=1)
minicuckoo_hour=clockhand(style="cuckoo",hour=True, fixing="circle", fixing_d1=4.15, thick=1)

smallcuckoo_min=clockhand(style="cuckoo", thick=1.2, length=33, fixing_d1=4.1, fixing_d2=4.1)
smallcuckoo_hour=clockhand(style="cuckoo",hour=True, fixing="circle", fixing_d1=6.8, thick=1.2, length=33)

minisimple_min=clockhand(style="simple", thick=1)
minisimple_hour=clockhand(style="simple",hour=True, fixing="circle", fixing_d1=4.15, thick=1)

# show_object(minicuckoo_min)
# show_object(minicuckoo_hour)
show_object(smallcuckoo_min)
# show_object(smallcuckoo_hour)

Path("out").mkdir(parents=True, exist_ok=True)
# exporters.export(minicuckoo_min, "out/minicuckoo_min.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(minicuckoo_hour, "out/minicuckoo_hour.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(minisimple_min, "out/minisimple_min.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(minisimple_hour, "out/minisimple_hour.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(smallcuckoo_min, "out/smallcuckoo_min.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(smallcuckoo_hour, "out/smallcuckoo_hour.stl", tolerance=0.001, angularTolerance=0.01)