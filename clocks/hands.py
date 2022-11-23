from .utility import *
import cadquery as cq
import os
from cadquery import exporters
from enum import Enum
from .gearing import GearStyle,Gear

class HandStyle(Enum):
    SQUARE = "square"
    SIMPLE = "simple"
    SIMPLE_ROUND = "simple_rounded"
    CUCKOO = "cuckoo"
    SPADE = "spade"
    BREGUET = "breguet" # has a single circle on each hand
    SYRINGE="syringe"
    SWORD="sword"
    CIRCLES="circles" # very much inspired by the same clock on the horological journal that inspired the circle style gears
    XMAS_TREE="xmas_tree"
    #ARROWS


class Hands:
    def __init__(self, style=HandStyle.SIMPLE, minuteFixing="rectangle", hourFixing="circle", secondFixing="rod", minuteFixing_d1=1.5, minuteFixing_d2=2.5,
                 hourfixing_d=3, secondFixing_d=3, length=25, secondLength=30, thick=1.6, fixing_offset=0, outline=0, outlineSameAsBody=True, handNutMetricSize=3,
                 chunky = False):
        '''
        chunky applies to some styles that can be made more or less chunky - idea is that some defaults might look good with a dial, but look a bit odd without a dial
        '''
        self.thick=thick
        #usually I print multicolour stuff with two layers, but given it's entirely perimeter I think it will look okay with just one
        #one layer does work pretty well, but the elephant's foot is sometimes obvious and it's hard to keep the first layer of white perfect. So switching back to two
        self.outlineThick=LAYER_THICK*2
        #how much to rotate the minute fixing by
        self.fixing_offset=fixing_offset
        self.length = length
        self.style=style

        self.chunky = chunky

        #backwards compat, support old strings
        if isinstance(self.style, str):
            for handStyle in HandStyle:
                if self.style == handStyle.value:
                    self.style = handStyle

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
        #the round bit that attaches to the clock - this is just the default size for the cosmetics and various styles can override it
        # self.base_r = length * 0.12
        #
        # if self.style == HandStyle.SQUARE:
        #     self.base_r /= 2
        #
        # #ensure it's actually big enoguh to fit onto the fixing
        # if self.base_r < minuteFixing_d1 * 0.7:
        #     self.base_r = minuteFixing_d1 * 1.5 / 2
        #
        # if self.base_r < minuteFixing_d2 * 0.7:
        #     self.base_r = minuteFixing_d2 * 1.5 / 2
        #
        # if self.base_r < hourfixing_d * 0.7:
        #     self.base_r = hourfixing_d * 1.5 / 2

        # self.min_base_r = max(minuteFixing_d1 * 1.5 / 2,  minuteFixing_d2 * 1.5 / 2, hourfixing_d * 1.5 / 2)

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
            #second hand, assuming threaded onto a threaded rod, hole doesn't extend all the way through
            # hand = hand.moveTo(0, 0).circle(self.secondFixing_d / 2).cutThruAll()

            hand = hand.cut(cq.Workplane("XY").moveTo(0,0).circle(self.secondFixing_d / 2).extrude(self.thick/2).translate((0,0,self.thick/2)))
            try:
                hand = hand.workplaneFromTagged("base").moveTo(0,0).circle(self.secondFixing_d).circle(self.secondFixing_d / 2).extrude(self.secondFixing_thick + self.thick)
            except:
                hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.secondFixing_d * 0.99).circle(self.secondFixing_d / 2).extrude(self.secondFixing_thick + self.thick)
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
   
    def outLineIsSubtractive(self):
        '''
        If the outline is a negative shell from the outline provided by hand, return true
        if the outline is a positive shell, return false (for hands with thin bits where there isn't enough width)
        '''
        #sword is a bit too pointy, so trying to soften it
        #xmas tree just looks bettery
        #spade and cuckoo only work this way
        if self.style in [HandStyle.CUCKOO, HandStyle.SPADE, HandStyle.XMAS_TREE, HandStyle.SWORD]:
            return False

        return True

    def getExtraColours(self):
        #first colour is default
        if self.style == HandStyle.XMAS_TREE:
            #green leaves, red tinsel, brown trunk
            return ["brown", "green", "red", "gold"]

        return [None]

    def getHand(self, hour=False, minute=False, second=False, generate_outline=False, colour=None):
        '''
        #either hour, minute or second hand (for now?)
        if provide a colour, return the layer for just that colour (for novelty hands with lots of colours)
        '''

        #default is minute hand

        if not hour and not minute and not second:
            minute = True
        #draw a circle for the base of the hand
        need_base_r = True
        base_r = self.length * 0.12
        length = self.length
        thick = self.thick
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

        ignoreOutline = False

        hand = cq.Workplane("XY").tag("base")


        # if colour is None and len(self.getExtraColours()) > 0:
        #     colour = self.getExtraColours()[0]

        # if colour is not None:
        #     ignoreOutline = True

        if self.style == HandStyle.SIMPLE:

            width = self.length * 0.1
            if second:
                width = self.length * 0.05
                # don't let it be smaller than the rounded end!
                base_r = max(base_r, self.length * 0.1 / 2)


            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(width, length).extrude(thick)



        elif self.style == HandStyle.SIMPLE_ROUND:
            width = self.length * 0.1
            if second:
                width = self.length * 0.05
                # don't let it be smaller than the rounded end!
                base_r = max(base_r, self.length * 0.1 / 2)

            hand = hand.workplaneFromTagged("base").moveTo(width/2, 0).line(0,length).radiusArc((-width/2,length),-width/2).line(0,-length).close().extrude(thick)
        elif self.style == HandStyle.SQUARE:

            if not second:
                base_r = self.length * 0.08

            handWidth = base_r*2
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2 - base_r).rect(handWidth, length).extrude(thick)
        elif self.style == HandStyle.XMAS_TREE:
            trunkWidth = self.length * 0.075
            leafyWidth = length*0.5
            trunkEnd = length*0.4
            useTinsel = True
            if minute:
                leafyWidth*=0.6
            if hour:
                trunkEnd*=0.9

            #same as the spades
            base_r = self.length * 0.075

            leaves = cq.Workplane("XY").tag("base")
            tinsel = cq.Workplane("XY").tag("base")
            baubles = cq.Workplane("XY").tag("base")
            bauble_r = self.length*0.03
            tinsel_thick=length*0.02

            hand = hand.workplaneFromTagged("base").moveTo(0, trunkEnd/2).rect(trunkWidth, trunkEnd).extrude(thick)

            #rate of change of leaf width with respect to height from the start of the leaf bit
            dLeaf = 0.5*leafyWidth/(length - trunkEnd)

            spikes = 4
            spikeHeight = (length - trunkEnd)/spikes
            sag = spikeHeight*0.2
            ys = [trunkEnd + spikeHeight*spike for spike in range(spikes+1)]
            tinselHeight = spikeHeight*0.3

            for spike in range(spikes):
                width = leafyWidth - dLeaf*spikeHeight*spike
                left = (-width/2, ys[spike])
                right = (width/2, ys[spike])
                topLeft = (-width/4, ys[spike+1])
                topRight = (width / 4, ys[spike + 1])
                tinselTopLeft=(left[0], left[1] + tinselHeight)
                tinselTopRight=(right[0], right[1] + tinselHeight)
                if spike == spikes-1:
                    topLeft = topRight = (0, length)
                leaves = leaves.workplaneFromTagged("base").moveTo(topLeft[0], topLeft[1]).sagittaArc(endPoint=left, sag=sag/2).sagittaArc(endPoint=right, sag=-sag).\
                    sagittaArc(endPoint=topRight, sag=sag/2).close().extrude(thick)
                # tinsel = tinsel.workplaneFromTagged("base").moveTo(tinselTopLeft[0], tinselTopLeft[1]).lineTo(left[0], left[1]).sagittaArc(endPoint=right, sag=-sag). \
                #     lineTo(tinselTopRight[0], tinselTopRight[1]).sagittaArc(endPoint=tinselTopLeft, sag=sag).close().extrude(thick)

            tinsel_circle_centres = [(leafyWidth*0.6, length),(-leafyWidth*0.6, length*1.2),(leafyWidth*0.6, length*1.4)]

            for circle_centre in tinsel_circle_centres:
                circle_r = length-trunkEnd
                tinsel=tinsel.workplaneFromTagged("base").moveTo(circle_centre[0], circle_centre[1]).circle(circle_r).circle(circle_r - tinsel_thick).extrude(thick)

            bauble_positions = [(leafyWidth*0.1, length*0.5),(-leafyWidth*0.1, length*0.75)]

            for pos in bauble_positions:
                baubles =baubles.workplaneFromTagged("base").moveTo(pos[0], pos[1]).circle(bauble_r).extrude(thick)
                baubles = baubles.workplaneFromTagged("base").moveTo(pos[0], pos[1]+base_r*0.3).rect(bauble_r*0.3,bauble_r).extrude(thick)

            #
            tinsel = tinsel.intersect(leaves)
            if useTinsel:

                leaves = leaves.cut(tinsel)
                # baubles = baubles.cut(tinsel)
                tinsel = tinsel.cut(baubles)

            leaves = leaves.cut(baubles)

            if colour is None:
                hand = hand.add(leaves)
                hand = hand.add(baubles)
                if useTinsel:
                    hand = hand.add(tinsel)
            elif colour == "brown":
                hand = hand.cut(leaves)
                if useTinsel:
                    hand = hand.cut(tinsel)
            elif colour == "green":
                hand = leaves
                need_base_r=False
            elif colour == "red":
                hand = tinsel
                need_base_r = False
            elif colour == "gold":
                hand = baubles
                need_base_r = False



        elif self.style == HandStyle.SYRINGE:

            syringe_width = self.length*0.1
            if hour:
                syringe_width = self.length*0.15

            if second:
                syringe_width = length * 0.2

            syringe_length = length * 0.7

            syringe_startY = (length - syringe_length)/2

            syringe_end_length = syringe_width/2

            base_wide = syringe_width*0.25

            tip_wide = syringe_width*0.1
            base_r = base_r * 0.6
            if second:
                tip_wide = 1
                syringe_width=base_r*2



            if second:
                hand = hand.workplaneFromTagged("base").moveTo(0,0).lineTo(-syringe_width/2,0)
            else:
                hand = hand.workplaneFromTagged("base").moveTo(0,0).lineTo(-base_wide/2,0)

            hand = hand.lineTo(-syringe_width/2,syringe_startY).line(0,syringe_length-syringe_end_length)\
                .lineTo(-tip_wide/2,syringe_startY + syringe_length).lineTo(-tip_wide/2,length).lineTo(0,length+tip_wide/2).mirrorY().extrude(thick)
        elif self.style == HandStyle.CIRCLES:

            tip_r = self.length*0.05
            base_r = self.length*0.2
            border = self.length * 0.045
            if second:
                base_r = length*0.2
                tip_r = length * 0.05
                border = length * 0.045

            r_rate = (tip_r - base_r)/length

            overlap=border
            r = base_r
            y=0#-(base_r-overlap)

            while y < length:

                r=base_r + y*r_rate
                if y > 0:
                    y += r-overlap/2
                hand = hand.workplaneFromTagged("base").moveTo(0, y).circle(r)
                if not second and y > base_r:
                    hand = hand.circle(r-border)
                hand = hand.extrude(thick)
                y+=r-overlap/2

            #is this too much? # TODO line up cutter with hand!
            hand = Gear.cutStyle(hand,base_r*0.9,self.hourFixing_d*0.7, style=GearStyle.CIRCLES)
            base_r = self.hourFixing_d*0.6


            #circle on the other side (I'm sure there's a way to set up initial y to do this properly)
            #actually makes it quite hard to read the time!
            # y=-(base_r-overlap/2)
            # r = base_r + y * r_rate
            # y -= r - overlap / 2
            # hand = hand.workplaneFromTagged("base").moveTo(0, y).circle(r)
            # if not second:
            #     hand = hand.circle(r - border)
            # hand = hand.extrude(thick)

        elif self.style == HandStyle.SWORD:

            base_r = base_r*0.6

            base_width = base_r*2.5
            rear_length = length*0.3

            if rear_length < base_r*2:
                rear_length = base_r*2

            hand = hand.workplaneFromTagged("base").moveTo(-base_width/2,0).lineTo(0,length).lineTo(base_width/2,0).lineTo(0,-rear_length).close().extrude(thick)

        elif self.style == HandStyle.BREGUET:

            handWidth = self.length * 0.04
            tipWidth = self.length*0.01

            circleR = self.length * 0.08
            circleY = length*0.75

            if self.chunky:
                handWidth = self.length*0.06
                tipWidth = self.length*0.0125
                circleR = self.length*0.1
            else:
                base_r = self.length*0.075



            if hour:
                circleR = self.length*0.125
                circleY = length*0.65
            if second:
                handWidth=self.length*0.03
                circleR = self.length*0.04
                circleY = - self.length*0.04*2.5
                base_r = circleR
                # ignoreOutline=True

            hand = hand.workplaneFromTagged("base").moveTo(0, abs(circleY / 2)).rect(handWidth, abs(circleY)).extrude(thick)
            #some sizes are complaining the radius isn't long enough to complete the arc, so bodge it a bit
            hand = hand.workplaneFromTagged("base").moveTo(-handWidth/2, abs(circleY)).lineTo(-tipWidth/2,length).radiusArc((tipWidth/2,length),tipWidth/2+0.01).lineTo(handWidth/2, abs(circleY)).close().extrude(thick)
            if second:
                hand = hand.workplaneFromTagged("base").moveTo(0, circleY / 2).rect(handWidth, abs(circleY)).extrude(thick)
                hand = hand.workplaneFromTagged("base").moveTo(0,0).circle(base_r).extrude(thick)

            hand = hand.workplaneFromTagged("base").moveTo(0, circleY).circle(circleR).extrude(thick)
            hand = hand.faces(">Z").moveTo(0, circleY).circle(circleR-handWidth).cutThruAll()



        elif self.style == HandStyle.SPADE:
            base_r = self.length * 0.075
            handWidth = self.length*0.05
            if second:
                handWidth = self.length * 0.025
                base_r = self.length*0.02

            #for the bottom of the spade, not the usual baseR
            spadeBaseR = length*0.05*2

            if hour:
                spadeBaseR*=1.4

            spadeTopLength = length*0.4
            spadeTipWidth = handWidth*0.5
            tipLength = length*0.1

            # if second:
            #     spadeTipWidth*=0.9

            # length = length - tipLength - spadeTopLength

            armLength = length - tipLength - spadeTopLength

            midPoint = (spadeBaseR*0.75,armLength + spadeTopLength*0.3)
            tipBase = (spadeTipWidth/2,armLength + spadeTopLength)
            tipEndSide = (spadeTipWidth/2,armLength + spadeTopLength + tipLength)
            tip = (0,armLength + spadeTopLength + tipLength + spadeTipWidth/2)

            hand = hand.workplaneFromTagged("base").moveTo(0, armLength / 2).rect(handWidth, armLength).extrude(thick)

            hand = hand.workplaneFromTagged("base").moveTo(0, armLength-spadeBaseR).radiusArc((spadeBaseR, armLength), -spadeBaseR)\
                .tangentArcPoint(midPoint, relative=False)\
                .tangentArcPoint(tipBase, relative=False).tangentArcPoint(tipEndSide,relative=False).tangentArcPoint(tip, relative=False)\
                .mirrorY().extrude(thick)

        elif self.style == HandStyle.CUCKOO:

            end_d = self.length * 0.3 * 0.1
            centrehole_y = length * 0.6
            width = self.length * 0.3
            if second:
                width = length*0.3
                end_d = length * 0.3 * 0.1
                ignoreOutline = True
                base_r = self.secondLength * 0.12
            centrehole_r = width * 0.15

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).threePointArc((end_d *0.75, length/2),(end_d / 2, length)).radiusArc(
            #    (-end_d / 2, length), -end_d / 2).threePointArc((-end_d *0.75, length/2),(-width * 0.4, 0)).close().extrude(ratchetThick)

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.25, length*0.3).lineTo(end_d / 2, length).radiusArc(
            #     (-end_d / 2, length), -end_d / 2).lineTo(-width * 0.25, length*0.3).close().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(width * 0.2, length * 0.3).lineTo(end_d / 2, length).threePointArc((0, length + end_d / 2), (-end_d / 2, length)).lineTo(-width * 0.2, length * 0.3).close().extrude(thick)

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
            hand = stickyoutblobs.mirrorY().extrude(thick)

            # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y-centrehole_r).spline([(little_sticky_out_dist*1.6,centrehole_y-little_sticky_out_d*0.6),(little_sticky_out_dist*1.6,centrehole_y+little_sticky_out_d*0.2),(0,centrehole_y)],includeCurrent=True)\
            #     .mirrorY().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(0, little_sticky_out_y - little_sticky_out_d / 2 + little_sticky_out_d * 0.1).lineTo(little_sticky_out_dist, little_sticky_out_y - little_sticky_out_d / 2).threePointArc(
                (little_sticky_out_dist + little_sticky_out_d / 2, little_sticky_out_y), (little_sticky_out_dist, little_sticky_out_y + little_sticky_out_d / 2)).line(-little_sticky_out_dist, 0) \
                .mirrorY().extrude(thick)

            petalend = (width * 0.6, length * 0.45)

            # petal-like bits near the centre of the hand
            hand = hand.workplaneFromTagged("base").lineTo(width * 0.1, 0).spline([(petalend[0] * 0.3, petalend[1] * 0.1), (petalend[0] * 0.7, petalend[1] * 0.4), (petalend[0] * 0.6, petalend[1] * 0.75), petalend], includeCurrent=True) \
                .line(0, length * 0.005).spline([(petalend[0] * 0.5, petalend[1] * 0.95), (0, petalend[1] * 0.8)], includeCurrent=True).mirrorY()
            # return hand
            hand = hand.extrude(thick)

            # sticky out bottom bit for hour hand
            if hour:
                hand = hand.workplaneFromTagged("base").lineTo(width * 0.4, 0).lineTo(0, -width * 0.9).mirrorY().extrude(thick)
                # return hand
            # cut bits out
            # roudn bit in centre of knobbly bit
            hand = hand.moveTo(0, centrehole_y).circle(centrehole_r).cutThruAll()
            heartbase = base_r + length * 0.025  # length*0.175

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



        #check it's big enough for the fixing to fit inside!
        #note - currently assumes that minute and hour hands have the same size base circle, which is true of the current designs but may not be true of future designs.
        if (minute or hour) and base_r < self.minuteFixing_d1 * 0.7:
            base_r = self.minuteFixing_d1 * 1.5 / 2

        if (minute or hour)  and base_r < self.minuteFixing_d2 * 0.7:
            base_r = self.minuteFixing_d2 * 1.5 / 2

        if (minute or hour)  and base_r < self.hourFixing_d * 0.7:
            base_r = self.hourFixing_d * 1.5 / 2

        if second and base_r < self.secondFixing_d * 0.7:
            base_r = self.secondFixing_d* 1.5 / 2

        if need_base_r:
            hand = hand.workplaneFromTagged("base").circle(radius=base_r).extrude(thick)


        if self.fixing_offset != 0:
            hand = hand.workplaneFromTagged("base").transformed(rotate=(0, 0,self. fixing_offset))

        # if second:
        #     hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.secondFixing_d).extrude(self.secondFixing_thick + thick)

        if not generate_outline:
            try:
                hand = self.cutFixing(hand, hour, second)
            except:
                pass



        if self.outline > 0 and not ignoreOutline:
            if self.outLineIsSubtractive():
                #the outline cuts into the hand shape

                if generate_outline:
                    #we are generating the outline - hand is currently the default hand shape

                    #use a negative shell to get a thick line just inside the edge of the hand

                    #this doesn't work for fancier shapes - I think it can't cope if there isn't space to extrude the shell without it overlapping itself?
                    #works fine for simple hands, not for cuckoo hands
                    try:
                        shell = hand.shell(-self.outline).translate((0,0,-self.outline))
                    except:
                        print("Unable to give outline to hand")
                        return None

                    # hand_minus_shell = hand.cut(shell)

                    slab_thick = self.outlineThick

                    bigSlab = cq.Workplane("XY").rect(length*3, length*3).extrude(slab_thick)

                    outline = shell.intersect(bigSlab)

                    if self.outlineSameAsBody:
                        thin_not_outline = hand.intersect(bigSlab).cut(outline)
                        outline_with_back_of_hand = hand.cut(thin_not_outline)
                        try:
                            outline_with_back_of_hand = self.cutFixing(outline_with_back_of_hand, hour, second)
                        except:
                            pass
                        return outline_with_back_of_hand
                    else:
                        return outline
                else:
                    outlineShape = self.getHand(hour=hour, minute=minute, second=second, generate_outline=True)
                    #chop out the outline from the shape
                    if outlineShape is not None:
                        hand = hand.cut(outlineShape)
            else:#positive shell - outline is outside the shape
                #for things we can't use a negative shell on, we'll make the whole hand a bit bigger
                if generate_outline:
                    shell = hand.shell(self.outline)
                    slabThick = self.outlineThick
                    if self.outlineSameAsBody:
                        slabThick = self.thick
                    bigSlab = cq.Workplane("XY").rect(length * 3, length * 3).extrude(slabThick)

                    outline = shell.intersect(bigSlab)
                    outline = self.cutFixing(outline, hour, second)

                    if self.outlineSameAsBody:
                        #add the hand, minus a thin layer on the front
                        outline = outline.add(hand.cut(cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.outlineThick)))
                        outline = self.cutFixing(outline, hour, second)
                        return outline

                    return outline
                else:
                    #this is the hand, minus the outline
                    if self.outlineSameAsBody:
                        bigSlab = cq.Workplane("XY").rect(length * 3, length * 3).extrude(self.outlineThick)
                        hand = hand.intersect(bigSlab)
                    else:
                        #make the whole hand bigger by the outline amount
                        shell = hand.shell(self.outline).intersect(cq.Workplane("XY").rect(length * 3, length * 3).extrude(thick-self.outlineThick).translate((0,0,self.outlineThick)))

                        hand = hand.add(shell)
                        hand = self.cutFixing(hand, hour, second)
                        return hand


        return hand


    def outputSTLs(self, name="clock", path="../out"):

        colours = self.getExtraColours()

        for colour in colours:
            colour_string = "_"+colour if colour is not None else ""
            out = os.path.join(path, "{}_hour_hand{}.stl".format(name, colour_string))
            print("Outputting ", out)
            exporters.export(self.getHand(hour=True, colour=colour), out)

            out = os.path.join(path, "{}_minute_hand{}.stl".format(name, colour_string))
            print("Outputting ", out)
            exporters.export(self.getHand(minute=True, colour=colour), out)

            out = os.path.join(path, "{}_second_hand{}.stl".format(name, colour_string))
            print("Outputting ", out)
            exporters.export(self.getHand(second=True, colour=colour), out)

        out = os.path.join(path, "{}_hand_nut.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getHandNut(), out)

        if self.outline > 0:
            out = os.path.join(path, "{}_hour_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(hour=True, generate_outline=True), out)

            out = os.path.join(path, "{}_minute_hand_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getHand(minute=True, generate_outline=True), out)

            secondoutline = self.getHand(second=True, generate_outline=True)
            if secondoutline is not None:
                out = os.path.join(path, "{}_second_hand_outline.stl".format(name))
                print("Outputting ", out)
                exporters.export(secondoutline, out)
