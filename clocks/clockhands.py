import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math

'''
DEPRECATED - replaced with hands which wraps this up in a class

'''



if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass



def clockhand(style="simple",fixing="rectangle",fixing_d1=1.5,fixing_d2=2.5,length=25, thick=1.6, hour=False,fixing_offset=0):
    '''
    fixings: rectangle, square, circle
    '''
    #base_d = (minuteFixing_d2 if minuteFixing_d2 > minuteFixing_d1 else minuteFixing_d1)*3
    #nominal width of base and sticky out bits
    width = length*0.3
    end_d = width*0.1

    if hour:
        length = length*0.8
        if style == "simple":
            width = width*1.2
        if style == "square":
            width = width*1.75
    base_r = width/2
    if style == "square":
        base_r/=2

    if base_r < fixing_d1*0.9:
        base_r = fixing_d1*1.5/2

    hand = cq.Workplane("XY").tag("base").circle(radius=base_r).extrude(thick)
    #hand = hand.workplaneFromTagged("base").moveTo(0,length/2).rect(length*0.1,length).extrude(thick)

    if style == "simple":
        hand = hand.workplaneFromTagged("base").moveTo(width*0.4,0).lineTo(end_d/2, length).radiusArc((-end_d/2,length),-end_d/2).lineTo(-width*0.4,0).close().extrude(thick)
    elif style == "square":
        handWidth = width*0.25
        hand = hand.workplaneFromTagged("base").moveTo(0,length/2).rect(handWidth,length).extrude(thick)
    elif style == "cuckoo":

        centrehole_y = length * 0.6
        centrehole_r = width*0.15


        #hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).threePointArc((end_d *0.75, length/2),(end_d / 2, length)).radiusArc(
        #    (-end_d / 2, length), -end_d / 2).threePointArc((-end_d *0.75, length/2),(-width * 0.4, 0)).close().extrude(thick)

        # hand = hand.workplaneFromTagged("base").moveTo(width * 0.25, length*0.3).lineTo(end_d / 2, length).radiusArc(
        #     (-end_d / 2, length), -end_d / 2).lineTo(-width * 0.25, length*0.3).close().extrude(thick)
        hand = hand.workplaneFromTagged("base").moveTo(width * 0.2, length * 0.3).lineTo(end_d / 2, length).threePointArc((0,length+end_d/2),(-end_d/2,length)).lineTo(-width * 0.2, length * 0.3).close().extrude(thick)

        #extra round bits towards the end of the hand
        little_sticky_out_dist = width * 0.3
        little_sticky_out_d = width*0.35
        little_sticky_out_y = centrehole_y - centrehole_r*0.4
        little_sticky_out_d2 = width * 0.125
        little_sticky_out_dist2 = width * 0.2
        stickyoutblobs = hand.workplaneFromTagged("base")
        #the two smaller blobs, justcircles
        for angle_d in [45]:
            angle = math.pi*angle_d/180
            #just circle, works but needs more
            stickyoutblobs = stickyoutblobs.moveTo(0+math.cos(angle)*little_sticky_out_dist2, centrehole_y+little_sticky_out_d2*0.25+math.sin(angle)*little_sticky_out_dist2).circle(little_sticky_out_d2)
            #hand =  hand.workplaneFromTagged("base").moveTo(0+math.cos(angle+math.pi/2)*little_sticky_out_d/2,centrehole_y+math.sin(angle+math.pi/2)*little_sticky_out_d/2).lineTo()
            #hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y).rot
        hand = stickyoutblobs.mirrorY().extrude(thick)

        # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y-centrehole_r).spline([(little_sticky_out_dist*1.6,centrehole_y-little_sticky_out_d*0.6),(little_sticky_out_dist*1.6,centrehole_y+little_sticky_out_d*0.2),(0,centrehole_y)],includeCurrent=True)\
        #     .mirrorY().extrude(thick)
        hand = hand.workplaneFromTagged("base").moveTo(0, little_sticky_out_y-little_sticky_out_d/2 +little_sticky_out_d*0.1).lineTo(little_sticky_out_dist, little_sticky_out_y-little_sticky_out_d/2).threePointArc(
             (little_sticky_out_dist +little_sticky_out_d/2, little_sticky_out_y), (little_sticky_out_dist,little_sticky_out_y + little_sticky_out_d/2)).line(-little_sticky_out_dist,0)\
            .mirrorY().extrude(thick)

        petalend=(width*0.6,length*0.45)

        #petal-like bits near the centre of the hand
        hand = hand.workplaneFromTagged("base").lineTo(width*0.1,0).spline([(petalend[0]*0.3, petalend[1]*0.1),(petalend[0]*0.7, petalend[1]*0.4),(petalend[0]*0.6, petalend[1]*0.75),petalend],includeCurrent=True)\
            .line(0,length*0.005).spline([(petalend[0]*0.5,petalend[1]*0.95),(0,petalend[1]*0.8)], includeCurrent=True).mirrorY()
        # return hand
        hand = hand.extrude(thick)

        #sticky out bottom bit for hour hand
        if hour:
            hand=hand.workplaneFromTagged("base").lineTo(width*0.4,0).lineTo(0,-width*0.9).mirrorY().extrude(thick)
            # return hand
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
    if fixing_offset != 0:
        hand = hand.workplaneFromTagged("base").transformed(rotate=(0,0,fixing_offset))
    if fixing == "rectangle":
        hand = hand.moveTo(0,0).rect(fixing_d1,fixing_d2).cutThruAll()
    elif fixing == "circle":
        hand = hand.moveTo(0,0).circle(fixing_d1/2).cutThruAll()


    return hand
if False:
    minicuckoo_min=clockhand(style="cuckoo", thick=1)
    minicuckoo_hour=clockhand(style="cuckoo",hour=True, fixing="circle", fixing_d1=4.15, thick=1)

    smallcuckoo_min=clockhand(style="cuckoo", thick=1.2, length=33, fixing_d1=4.1, fixing_d2=4.1)
    smallcuckoo_hour=clockhand(style="cuckoo",hour=True, fixing="circle", fixing_d1=6.8, thick=1.2, length=33)

    minisimple_min=clockhand(style="simple", thick=1)
    minisimple_hour=clockhand(style="simple",hour=True, fixing="circle", fixing_d1=4.15, thick=1)


    greencuckoo_min=clockhand(style="cuckoo", thick=1.4, length=30, fixing_d1=2.6, fixing_d2=2.6, fixing_offset=45)
    greencuckoo_hour=clockhand(style="cuckoo",hour=True, fixing="circle", thick=1.4, length=30, fixing_d1=4.4, fixing_d2=4.4)
    exporters.export(greencuckoo_min, "out/greencuckoo_min.stl", tolerance=0.001, angularTolerance=0.01)
    exporters.export(greencuckoo_hour, "out/greencuckoo_hour.stl", tolerance=0.001, angularTolerance=0.01)

    #should be 1.6, but that was way too small. 2 was too big.
    smithsalarm_min = clockhand(style="square", thick = 2, fixing="circle", fixing_d1=1.8, length=35)
    #3.4 fits perfectly, but I need it to slide down a tiny bit further
    smithsalarm_hour = clockhand(style="square", hour=True, thick = 2, fixing="circle", fixing_d1=3.45, length=35)

    exporters.export(smithsalarm_min, "out/smithsalarm_min.stl", tolerance=0.001, angularTolerance=0.01)
    exporters.export(smithsalarm_hour, "out/smithsalarm_hour.stl", tolerance=0.001, angularTolerance=0.01)
#
#
# musiccuckoo_hour=clockhand(style="cuckoo",thick=1.3,hour=True, fixing="circle", minuteFixing_d1=4.55, length=32)#4.35
# musiccuckoo_min=clockhand(style="cuckoo",thick=1.4,hour=False, fixing="circle", minuteFixing_d1=5.3+0.15, length=32)#5.3+0.25 fits the collet, but too loose
# musiccuckoo_min2=clockhand(style="cuckoo",thick=1.4,hour=False, fixing="rectangle ", minuteFixing_d1=2.6, minuteFixing_d2=2.6, length=32)#5.3+0.25 fits the collet, but too loose
#
# exporters.export(musiccuckoo_min, "../out/musiccuckoo_min.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(musiccuckoo_hour, "../out/musiccuckoo_hour.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(musiccuckoo_min2, "../out/musiccuckoo_min2.stl", tolerance=0.001, angularTolerance=0.01)
#
# # show_object(minicuckoo_min)
# # show_object(minicuckoo_hour)
# #show_object(greencuckoo_min)
# # show_object(smallcuckoo_hour)
#
# #show_object(smithsalarm_min)
# #show_object(smithsalarm_hour)
#
#
# Path("out").mkdir(parents=True, exist_ok=True)
# # exporters.export(minicuckoo_min, "out/minicuckoo_min.stl", tolerance=0.001, angularTolerance=0.01)
# # exporters.export(minicuckoo_hour, "out/minicuckoo_hour.stl", tolerance=0.001, angularTolerance=0.01)
# # exporters.export(minisimple_min, "out/minisimple_min.stl", tolerance=0.001, angularTolerance=0.01)
# # exporters.export(minisimple_hour, "out/minisimple_hour.stl", tolerance=0.001, angularTolerance=0.01)
# # exporters.export(smallcuckoo_min, "out/smallcuckoo_min.stl", tolerance=0.001, angularTolerance=0.01)
# # exporters.export(smallcuckoo_hour, "out/smallcuckoo_hour.stl", tolerance=0.001, angularTolerance=0.01)
#
