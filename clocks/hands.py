from .utility import *
import cadquery as cq
import os
from cadquery import exporters

class Hands:
    def __init__(self, style="simple", minuteFixing="rectangle", hourFixing="circle", secondFixing="rod", minuteFixing_d1=1.5, minuteFixing_d2=2.5, hourfixing_d=3, secondFixing_d=3, length=25, secondLength=30, thick=1.6, fixing_offset=0, outline=0, outlineSameAsBody=True, handNutMetricSize=3):
        '''

        '''
        self.thick=thick
        #usually I print multicolour stuff with two layers, but given it's entirely perimeter I think it will look okay with just one
        self.outlineThick=LAYER_THICK
        #how much to rotate the minute fixing by
        self.fixing_offset=fixing_offset
        self.length = length
        self.style=style
        self.minuteFixing=minuteFixing
        self.minuteFixing_d1 = minuteFixing_d1
        self.minuteFixing_d2 = minuteFixing_d2
        self.secondFixing=secondFixing
        self.secondFixing_d = secondFixing_d
        self.secondFixing_thick = self.thick
        self.secondLength= secondLength
        #Add a different coloured outline that is this many mm ratchetThick
        self.outline = outline
        #if true the outline will be part of the same STL as the main body, if false, it'll just be a small sliver
        self.outlineSameAsBody = outlineSameAsBody
        self.handNutMetricSize=handNutMetricSize

        if self.minuteFixing == "square":
            self.minuteFixing_d2 = self.minuteFixing_d1
            self.minuteFixing="rectangle"

        self.hourFixing=hourFixing
        self.hourFixing_d = hourfixing_d
        #the found bit that attaches to the clock
        self.base_r = length * 0.12

        if self.style == "square":
            self.base_r /= 2

        #ensure it's actually big enoguh to fit onto the fixing
        if self.base_r < minuteFixing_d1 * 0.7:
            self.base_r = minuteFixing_d1 * 1.5 / 2

        if self.base_r < minuteFixing_d2 * 0.7:
            self.base_r = minuteFixing_d2 * 1.5 / 2

        if self.base_r < hourfixing_d * 0.7:
            self.base_r = hourfixing_d * 1.5 / 2

    def getHandNut(self):
        #fancy bit to hide the actual nut
        r = self.handNutMetricSize*2.5
        height = r*0.75


        circle = cq.Workplane("XY").circle(r)
        nut = cq.Workplane("XZ").moveTo(self.handNutMetricSize/2,0).lineTo(r,0).line(0,height*0.25).lineTo(self.handNutMetricSize/2,height).close().sweep(circle)

        nutSpace = getHoleWithHole(innerD=self.handNutMetricSize,outerD=getNutContainingDiameter(self.handNutMetricSize),sides=6, deep=getNutHeight(self.handNutMetricSize))

        nut = nut.cut(nutSpace)

        return nut

    def cutFixing(self, hand, hour, second=False):
        if second and self.secondFixing == "rod":
            #second hand, assuming threaded onto a threaded rod
            hand = hand.workplaneFromTagged("base").moveTo(0,0).circle(self.secondFixing_d).extrude(self.secondFixing_thick + self.thick)
            hand = hand.moveTo(0, 0).circle(self.secondFixing_d/2).cutThruAll()
            return hand

        if not hour and self.minuteFixing == "rectangle":
            #minute hand, assuming square or rectangle
            hand = hand.moveTo(0, 0).rect(self.minuteFixing_d1, self.minuteFixing_d2).cutThruAll()
        elif hour and self.hourFixing == "circle":
            #hour hand, assuming circular friction fit
            hand = hand.moveTo(0, 0).circle(self.hourFixing_d / 2).cutThruAll()
        else:
            #major TODO would be a collet for the minute hand
            raise ValueError("Combination not supported yet")

        return hand

    def getHand(self, hour=True, outline=False, second=False):
        '''
        if hour is true this ist he hour hand
        if outline is true, this is just the bit of the shape that should be printed in a different colour
        if second is true, this overrides hour and this is the second hand
        '''
        base_r = self.base_r
        length = self.length
        # width = self.length * 0.3
        if hour:
            length = self.length * 0.8
            # if self.style == "simple":
            #     width = width * 1.2
            # if self.style == "square":
            #     width = width * 1.75
        if second:
            length = self.secondLength
            base_r = self.secondLength * 0.2

            if self.style == "cuckoo":
                base_r = self.secondLength * 0.12


        hand = cq.Workplane("XY").tag("base").circle(radius=base_r).extrude(self.thick)

        if self.style == "simple":
            width = self.length * 0.1
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(width, length).extrude(self.thick)
        elif self.style == "simple_rounded":
            width = self.length * 0.1
            # if second:
            #     width = length * 0.2
            hand = hand.workplaneFromTagged("base").moveTo(width/2, 0).line(0,length).radiusArc((-width/2,length),-width/2).line(0,-length).close().extrude(self.thick)
        elif self.style == "square":
            handWidth = self.length * 0.3 * 0.25
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(handWidth, length).extrude(self.thick)
        elif self.style == "cuckoo":

            end_d = self.length * 0.3 * 0.1
            centrehole_y = length * 0.6
            width = self.length * 0.3
            if second:
                width = length*0.3
                end_d = length * 0.3 * 0.1
            centrehole_r = width * 0.15

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).threePointArc((end_d *0.75, length/2),(end_d / 2, length)).radiusArc(
            #    (-end_d / 2, length), -end_d / 2).threePointArc((-end_d *0.75, length/2),(-width * 0.4, 0)).close().extrude(ratchetThick)

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.25, length*0.3).lineTo(end_d / 2, length).radiusArc(
            #     (-end_d / 2, length), -end_d / 2).lineTo(-width * 0.25, length*0.3).close().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(width * 0.2, length * 0.3).lineTo(end_d / 2, length).threePointArc((0, length + end_d / 2), (-end_d / 2, length)).lineTo(-width * 0.2, length * 0.3).close().extrude(self.thick)

            # extra round bits towards the end of the hand
            little_sticky_out_dist = width * 0.3
            little_sticky_out_d = width * 0.35
            little_sticky_out_y = centrehole_y - centrehole_r * 0.4
            little_sticky_out_d2 = width * 0.125
            little_sticky_out_dist2 = width * 0.2
            stickyoutblobs = hand.workplaneFromTagged("base")
            # the two smaller blobs, justcircles
            for angle_d in [45]:
                angle = math.pi * angle_d / 180
                # just circle, works but needs more
                stickyoutblobs = stickyoutblobs.moveTo(0 + math.cos(angle) * little_sticky_out_dist2, centrehole_y + little_sticky_out_d2 * 0.25 + math.sin(angle) * little_sticky_out_dist2).circle(little_sticky_out_d2)
                # hand =  hand.workplaneFromTagged("base").moveTo(0+math.cos(angle+math.pi/2)*little_sticky_out_d/2,centrehole_y+math.sin(angle+math.pi/2)*little_sticky_out_d/2).lineTo()
                # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y).rot
            hand = stickyoutblobs.mirrorY().extrude(self.thick)

            # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y-centrehole_r).spline([(little_sticky_out_dist*1.6,centrehole_y-little_sticky_out_d*0.6),(little_sticky_out_dist*1.6,centrehole_y+little_sticky_out_d*0.2),(0,centrehole_y)],includeCurrent=True)\
            #     .mirrorY().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(0, little_sticky_out_y - little_sticky_out_d / 2 + little_sticky_out_d * 0.1).lineTo(little_sticky_out_dist, little_sticky_out_y - little_sticky_out_d / 2).threePointArc(
                (little_sticky_out_dist + little_sticky_out_d / 2, little_sticky_out_y), (little_sticky_out_dist, little_sticky_out_y + little_sticky_out_d / 2)).line(-little_sticky_out_dist, 0) \
                .mirrorY().extrude(self.thick)

            petalend = (width * 0.6, length * 0.45)

            # petal-like bits near the centre of the hand
            hand = hand.workplaneFromTagged("base").lineTo(width * 0.1, 0).spline([(petalend[0] * 0.3, petalend[1] * 0.1), (petalend[0] * 0.7, petalend[1] * 0.4), (petalend[0] * 0.6, petalend[1] * 0.75), petalend], includeCurrent=True) \
                .line(0, length * 0.005).spline([(petalend[0] * 0.5, petalend[1] * 0.95), (0, petalend[1] * 0.8)], includeCurrent=True).mirrorY()
            # return hand
            hand = hand.extrude(self.thick)

            # sticky out bottom bit for hour hand
            if hour and not second:
                hand = hand.workplaneFromTagged("base").lineTo(width * 0.4, 0).lineTo(0, -width * 0.9).mirrorY().extrude(self.thick)
                # return hand
            # cut bits out
            # roudn bit in centre of knobbly bit
            hand = hand.moveTo(0, centrehole_y).circle(centrehole_r).cutThruAll()
            heartbase = self.base_r + length * 0.025  # length*0.175

            hearttop = length * 0.425
            heartheight = hearttop - heartbase
            heartwidth = length * 0.27 * 0.3  # width*0.3
            # heart shape (definitely not a dick)
            # hand = hand.moveTo(0, heartbase).spline([(heartwidth*0.6,heartbase*0.9),(heartwidth*0.8,heartbase+heartheight*0.15),(heartwidth*0.6,heartbase+heartheight*0.4),(heartwidth*0.3,heartbase + heartheight/2)],includeCurrent=True).lineTo(heartwidth*0.5,heartbase + heartheight*0.75).lineTo(0,hearttop).mirrorY().cutThruAll()
            hand = hand.moveTo(0, heartbase).spline(
                [(heartwidth * 0.6, heartbase * 0.9), (heartwidth * 0.8, heartbase + heartheight * 0.15),
                 (heartwidth * 0.6, heartbase + heartheight * 0.4), (heartwidth * 0.3, heartbase + heartheight / 2)],
                includeCurrent=True).lineTo(heartwidth * 0.5, heartbase + heartheight * 0.75).lineTo(0,
                                                                                                     hearttop).mirrorY()  # .cutThruAll()
            # return hand.extrude(ratchetThick*2)
            try:
                hand = hand.cutThruAll()
            except:
                print("Unable to cut detail in cuckoo hand")

        # fixing = self.hourFixing if hour else self.minuteFixing

        if self.fixing_offset != 0:
            hand = hand.workplaneFromTagged("base").transformed(rotate=(0, 0,self. fixing_offset))

        # if second:
        #     hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.secondFixing_d).extrude(self.secondFixing_thick + self.thick)

        hand = self.cutFixing(hand, hour, second)

        ignoreOutline = False
        if self.style == "cuckoo" and second:
            ignoreOutline = True

        if self.outline > 0 and not ignoreOutline:
            if self.style != "cuckoo":
                if outline:
                    #use a negative shell to get a thick line just inside the edge of the hand

                    #this doesn't work for fancier shapes - I think it can't cope if there isn't space to extrude the shell without it overlapping itself?
                    #works fine for simple hands, not for cuckoo hands
                    try:
                        shell = hand.shell(-self.outline).translate((0,0,-self.outline))
                    except:
                        print("Unable to give outline to hand")
                        return None

                    notOutline = hand.cut(shell)
                    # return notOutline
                    #chop off the mess above the first few layers that we want

                    bigSlab = cq.Workplane("XY").rect(length*3, length*3).extrude(self.thick*10).translate((0,0,self.outlineThick))



                    if self.outlineSameAsBody:
                        notOutline = notOutline.cut(bigSlab)
                    else:
                        notOutline = notOutline.add(bigSlab)

                    hand = hand.cut(notOutline)

                else:
                    outlineShape = self.getHand(hour, outline=True, second=second)
                    #chop out the outline from the shape
                    if outlineShape is not None:
                        hand = hand.cut(outlineShape)
            else:
                #for things we can't use a negative shell on, we'll make the whole hand a bit bigger
                if outline:
                    shell = hand.shell(self.outline)

                    bigSlab = cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.outlineThick)

                    outline = shell.intersect(bigSlab)
                    outline = self.cutFixing(outline, hour, second)
                    return outline
                else:
                    #make the whole hand bigger by the outline amount
                    shell = hand.shell(self.outline).intersect(cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.thick-self.outlineThick).translate((0,0,self.outlineThick)))



                    # shell2 = hand.shell(self.outline+0.1).intersect(cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.outlineThick))

                    # return shell2
                    # hand = shell
                    hand = hand.add(shell)
                    hand = self.cutFixing(hand, hour, second)
                    return hand
                    # shell2 = self.cutFixing(shell2, hour)
                    #
                    # hand = hand.cut(shell2)


        return hand


    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_hour_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(hour=True), out)

        out = os.path.join(path, "{}_minute_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(hour=False), out)

        out = os.path.join(path, "{}_second_hand.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHand(second=True), out)

        out = os.path.join(path, "{}_hand_nut.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHandNut(), out)

        if self.outline > 0:
            out = os.path.join(path, "{}_hour_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(True, outline=True), out)

            out = os.path.join(path, "{}_minute_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(False, outline=True), out)

            secondoutline = self.getHand(hour=False, second=True, outline=True)
            if secondoutline is not None:
                out = os.path.join(path, "{}_second_hand_outline.stl".format(name))
                print("Outputting ", out)
                exporters.export(secondoutline, out)
