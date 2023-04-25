from .utility import *
from .power import *
from .gearing import *
from .hands import *
from .escapements import *
from .cosmetics import *
from .leaves import *
from .dial import *
import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os
import datetime
from .cuckoo_bits import roman_numerals
from .cq_svg import exportSVG




'''
Long term plan: this will be a library of useful classes to generate all the components and bits of clock plates
But another script will generate specific clock plates and arbours (note - the GoingTrain class has become a bit of a jack of all trades generating most of the arbours)
(note - arbours have been spun out into their own class, but the goingtrain, arbours and plates are still fairly strongly coupled)

Note: naming conventions I can find for clock gears seem to assume you always have the same number of gears between the chain and the minute hand
this is blatantly false (I can see this just looking at the various clocks I have) so I originally adopted a different naming convention:

The minute hand arbour is arbour 0.
In the direction of the escapement is +=ve
in the direction of the chain/spring wheel is -ve

UPDATE - although I thought it would be useful to always have the minute wheel as 0, it has actually proven to be more of a bother
A lot of operations require looping through all the bearings, and it would have been much easier to stick with the convention
getArbourWithConventionalNaming has been added to address this, but be aware that both are in play (although it should be clear which is being used) 


So for a very simple clock where the minute arbour is also the chain wheel, there could be only three arbours: 0, 1 and 2 (the escape wheel itself)

This way I can add more gears in either direction without confusing things too much.

The gears that drive the hour hand are the motion work. The cannon pinion is attached to the minute hand arbour, this drives the minute wheel.
The minute wheel is on a mini arbour with the hour pinion, which drives the hour wheel. The hour wheel is on the hour shaft.
The hour shaft fits over the minute arbour (on the clock face side) and the hour hand is friction fitted onto the hour shaft

Current plan: the cannon pinion will be loose over the minute arbour, and have a little shaft for the minute hand.
A nyloc nut underneath it (or two nuts locked against each other) and a normal nut on top (found nyloc or two nuts locked works better, you can turn hands backwards) 
of the minute hand will provide friction from the minute arbour to the motion work.
I think this is similar to older cuckoos I've seen. It will result in a visible nut, but a more simple time train. Will try it
for the first clock and decide if I want to switch to something else later. 
update - it works really well, I'm planning to keep doing it until there's reason not to.


Plan: spin out GoingTrain to gearing and a new file for the plates. keep this just for the clock assembly (and maybe dial and any future cases?)
'''



class GoingTrain:

    def __init__(self, pendulum_period=-1, pendulum_length=-1, wheels=3, fourth_wheel=None, escapement_teeth=30, chainWheels=0, hours=30, chainAtBack=True, maxWeightDrop=1800,
                 escapement=None, escapeWheelPinionAtFront=None, usePulley=False, huygensMaintainingPower=False, minuteWheelRatio = 1):
        '''

        pendulum_period: desired period for the pendulum (full swing, there and back) in seconds
        fourth_wheel: if True there will be four wheels from minute hand to the escape wheel
        escapement_teeth: number of teeth on the escape wheel DEPRECATED, provide entire escapement instead
        chainWheels: if 0 the minute wheel is also the chain wheel, if >0, this many gears between the minute wheel and chain wheel (say for 8 day clocks)
        hours: intended hours to run for (dictates diameter of chain wheel)
        chainAtBack: Where the chain and ratchet mechanism should go relative to the minute wheel
        maxChainDrop: maximum length of chain drop to meet hours required, in mm
        max_chain_wheel_d: Desired diameter of the chain wheel, only used if chainWheels > 0. If chainWheels is 0 there is no flexibility here
        escapement: Escapement object. If not provided, falls back to defaults with esacpement_teeth
        usePulley: if true, changes calculations for runtime
        escapeWheelPinionAtFront:  bool, override default
        huygensMaintainingPower: bool, if true we're using a weight on a pulley with a single loop of chain/rope, going over a ratchet on the front of the clock and a counterweight on the other side from the main weight
        easiest to implement with a chain

        minuteWheelRatio: usually 1 - so the minute wheel (chain wheel as well on a 1-day clock) rotates once an hour. If less than one, this "minute wheel" rotates less than once per hour.
        this makes sense (at the moment) only on a centred-second-hand clock where we have another set of wheels linking the "minute wheel" and the motion works


        Grand plan: auto generate gear ratios.
        Naming convention seems to be powered (spring/weight) wheel is first wheel, then minute hand wheel is second, etc, until the escapement
        However, all the 8-day clocks I've got have an intermediate wheel between spring powered wheel and minute hand wheel
        And only the little tiny balance wheel clocks have a "fourth" wheel.
        Regula 1-day cuckoos have the minute hand driven directly from the chain wheel, but then also drive the wheels up the escapment from the chain wheel, effectively making the chain
        wheel part of the gearing from the escapement to the minute wheel

        So, the plan: generate gear ratios from escapement to the minute hand, then make a wild guess about how much weight is needed and the ratio from the weight and
         where it should enter the escapment->minute hand chain

         so sod the usual naming convention until otherwise. Minute hand wheel is gonig to be zero, +ve is towards escapment and -ve is towards the powered wheel
         I suspect regula are onto something, so I may end up just stealing their idea

         This is intended to be agnostic to how the gears are laid out - the options are manually provided for which ways round the gear and scape wheel should face

        '''

        #in seconds
        self.pendulum_period = pendulum_period
        #in metres
        self.pendulum_length = pendulum_length

        self.minuteWheelRatio = minuteWheelRatio

        self.huygensMaintainingPower = huygensMaintainingPower
        self.arbours = []

        if pendulum_length < 0 and pendulum_period > 0:
            #calulate length from period
            self.pendulum_length = getPendulumLength(pendulum_period)
        elif pendulum_period < 0 and pendulum_length > 0:
            self.pendulum_period = getPendulumPeriod(pendulum_length)
        else:
            raise ValueError("Must provide either pendulum length or perioud, not neither or both")

        #note - this has become assumed in many places and will require work to the plates and layout of gears to undo
        self.chainAtBack = chainAtBack
        #likewise, this has been assumed, but I'm trying to undo those assumptions to use this
        self.penulumAtFront = True
        #to ensure the anchor isn't pressed up against the back (or front) plate
        if escapeWheelPinionAtFront is None:
            self.escapeWheelPinionAtFront = chainAtBack
        else:
            self.escapeWheelPinionAtFront=escapeWheelPinionAtFront

        self.powered_by = PowerType.NOT_CONFIGURED

        #if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.chainWheels = chainWheels
        #to calculate sizes of the powered wheels and ratios later
        self.hours = hours
        self.maxWeightDrop = maxWeightDrop
        self.usePulley=usePulley

        if fourth_wheel is not None:
            #old deprecated interface
            self.wheels = 4 if fourth_wheel else 3
        else:
            self.wheels = wheels

        #calculate ratios from minute hand to escapement
        #the last wheel is the escapement

        self.escapement=escapement
        if escapement is None:
            self.escapement = AnchorEscapement(teeth=escapement_teeth)
        #
        self.escapement_time = self.pendulum_period * self.escapement.teeth

        self.trains=[]

    def has_seconds_hand(self):
        #not sure this should work with floating point, but it does...
        return self.escapement_time == 60

    def getCordUsage(self):
        '''
        how much rope or cord will actually be used, as opposed to how far the weight will drop
        '''
        if self.usePulley:
            return 2*self.maxWeightDrop
        return self.maxWeightDrop

    '''
    TODO make this generic and re-usable, I've got similar logic over in calculating chain wheel ratios and motion works
    '''
    def calculateRatios(self, moduleReduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth=20, wheel_min_teeth=50, max_error=0.1, loud=False):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        module reduction used to calculate smallest possible wheels - assumes each wheel has a smaller module than the last
        '''

        pinion_min = min_pinion_teeth
        pinion_max = pinion_max_teeth
        wheel_min = wheel_min_teeth
        wheel_max = max_wheel_teeth

        '''
        https://needhamia.com/clock-repair-101-making-sense-of-the-time-gears/
        “With an ‘integer ratio’, the same pairs of teeth (gear/pinion) always mesh on each revolution.
         With a non-integer ratio, each pass puts a different pair of teeth in mesh. (Some fractional 
         ratios are also called a ‘hunting ratio’ because a given tooth ‘hunts’ [walks around] the other gear.)”

         "So it seems clock designers prefer non-whole-number gear ratios to even out the wear of the gears’ teeth. "

         seems reasonable to me
        '''
        allGearPairCombos = []

        targetTime = 60 * 60 / self.minuteWheelRatio

        for p in range(pinion_min, pinion_max):
            for w in range(wheel_min, wheel_max):
                allGearPairCombos.append([w, p])
        if loud:
            print("allGearPairCombos", len(allGearPairCombos))
        # [ [[w,p],[w,p],[w,p]] ,  ]
        allTrains = []

        allTrainsLength = 1
        for i in range(self.wheels):
            allTrainsLength *= len(allGearPairCombos)

        # this can be made generic for self.wheels, but I can't think of it right now. A stack or recursion will do the job
        # one fewer pairs than wheels
        allcomboCount = len(allGearPairCombos)
        if self.wheels == 2:
            for pair_0 in range(allcomboCount):
                allTrains.append([allGearPairCombos[pair_0]])
        if self.wheels == 3:
            for pair_0 in range(allcomboCount):
                for pair_1 in range(allcomboCount):
                    allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
        elif self.wheels == 4:
            for pair_0 in range(allcomboCount):
                if loud and pair_0 % 10 == 0:
                    print("{:.1f}% of calculating trains".format(100 * pair_0 / allcomboCount))
                for pair_1 in range(allcomboCount):
                    for pair_2 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1], allGearPairCombos[pair_2]])
        if loud:
            print("allTrains", len(allTrains))
        allTimes = []
        totalTrains = len(allTrains)
        for c in range(totalTrains):
            if loud and c % 100 == 0:
                print("{:.1f}% of combos".format(100 * c / totalTrains))
            totalRatio = 1
            intRatio = False
            totalTeeth = 0
            # trying for small wheels and big pinions
            totalWheelTeeth = 0
            totalPinionTeeth = 0
            weighting = 0
            lastSize = 0
            fits = True
            for p in range(len(allTrains[c])):
                ratio = allTrains[c][p][0] / allTrains[c][p][1]
                if ratio == round(ratio):
                    intRatio = True
                    break
                totalRatio *= ratio
                totalTeeth += allTrains[c][p][0] + allTrains[c][p][1]
                totalWheelTeeth += allTrains[c][p][0]
                totalPinionTeeth += allTrains[c][p][1]
                # module * number of wheel teeth - proportional to diameter
                size = math.pow(moduleReduction, p) * allTrains[c][p][0]
                weighting += size
                if p > 0 and size > lastSize * 0.9:
                    # this wheel is unlikely to physically fit
                    fits = False
                    break
                lastSize = size
            totalTime = totalRatio * self.escapement_time
            error = targetTime - totalTime

            train = {"time": totalTime, "train": allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth, "weighting": weighting}
            if fits and abs(error) < max_error and not intRatio:
                allTimes.append(train)

        allTimes.sort(key=lambda x: x["weighting"])
        # print(allTimes)

        self.trains = allTimes

        if len(allTimes) == 0:
            raise RuntimeError("Unable to calculate valid going train")

        return allTimes

    # def calculateRatios(self,moduleReduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth = 20, wheel_min_teeth = 50, max_error=0.1, loud=False):
    #     '''
    #     Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
    #     module reduction used to calculate smallest possible wheels - assumes each wheel has a smaller module than the last
    #     '''
    #
    #     pinion_min=min_pinion_teeth
    #     pinion_max=pinion_max_teeth
    #     wheel_min=wheel_min_teeth
    #     wheel_max=max_wheel_teeth
    #
    #     '''
    #     https://needhamia.com/clock-repair-101-making-sense-of-the-time-gears/
    #     “With an ‘integer ratio’, the same pairs of teeth (gear/pinion) always mesh on each revolution.
    #      With a non-integer ratio, each pass puts a different pair of teeth in mesh. (Some fractional
    #      ratios are also called a ‘hunting ratio’ because a given tooth ‘hunts’ [walks around] the other gear.)”
    #
    #      "So it seems clock designers prefer non-whole-number gear ratios to even out the wear of the gears’ teeth. "
    #
    #      seems reasonable to me
    #     '''
    #     allGearPairCombos = []
    #
    #     targetTime = 60*60/self.minuteWheelRatio
    #
    #     for p in range(pinion_min,pinion_max):
    #         for w in range(wheel_min, wheel_max):
    #             allGearPairCombos.append([w,p])
    #     if loud:
    #         print("allGearPairCombos", len(allGearPairCombos))
    #     #[ [[w,p],[w,p],[w,p]] ,  ]
    #     allTrains = []
    #
    #     allTrainsLength = 1
    #     for i in range(self.wheels):
    #         allTrainsLength*=len(allGearPairCombos)
    #
    #     #this can be made generic for self.wheels, but I can't think of it right now. A stack or recursion will do the job
    #     #one fewer pairs than wheels
    #     allcomboCount=len(allGearPairCombos)
    #     if self.wheels == 2:
    #         for pair_0 in range(allcomboCount):
    #             allTrains.append([allGearPairCombos[pair_0]])
    #     if self.wheels == 3:
    #         for pair_0 in range(allcomboCount):
    #             for pair_1 in range(allcomboCount):
    #                     allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
    #     elif self.wheels == 4:
    #         for pair_0 in range(allcomboCount):
    #             if loud and pair_0 % 10 == 0:
    #                 print("{:.1f}% of calculating trains".format(100*pair_0/allcomboCount))
    #             for pair_1 in range(allcomboCount):
    #                 for pair_2 in range(allcomboCount):
    #                     allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1], allGearPairCombos[pair_2]])
    #     if loud:
    #         print("allTrains", len(allTrains))
    #     allTimes=[]
    #     totalTrains = len(allTrains)
    #     for c in range(totalTrains):
    #         if loud and c % 100 == 0:
    #             print("{:.1f}% of combos".format(100*c/totalTrains))
    #         totalRatio = 1
    #         intRatio = False
    #         totalTeeth = 0
    #         #trying for small wheels and big pinions
    #         totalWheelTeeth = 0
    #         totalPinionTeeth = 0
    #         weighting = 0
    #         lastSize=0
    #         fits=True
    #         for p in range(len(allTrains[c])):
    #             ratio = allTrains[c][p][0] / allTrains[c][p][1]
    #             if ratio == round(ratio):
    #                 intRatio=True
    #                 break
    #             totalRatio*=ratio
    #             totalTeeth +=  allTrains[c][p][0] + allTrains[c][p][1]
    #             totalWheelTeeth += allTrains[c][p][0]
    #             totalPinionTeeth += allTrains[c][p][1]
    #             #module * number of wheel teeth - proportional to diameter
    #             size =  math.pow(moduleReduction, p)*allTrains[c][p][0]
    #             weighting += size
    #             if p > 0 and size > lastSize*0.9:
    #                 #this wheel is unlikely to physically fit
    #                 fits=False
    #                 break
    #             lastSize = size
    #         totalTime = totalRatio*self.escapement_time
    #         error = targetTime-totalTime
    #
    #         train = {"time":totalTime, "train":allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth, "weighting": weighting }
    #         if fits and  abs(error) < max_error and not intRatio:
    #             allTimes.append(train)
    #
    #     allTimes.sort(key = lambda x: x["weighting"])
    #     # print(allTimes)
    #
    #     self.trains = allTimes
    #
    #     if len(allTimes) == 0:
    #         raise RuntimeError("Unable to calculate valid going train")
    #
    #     return allTimes

    def setRatios(self, gearPinionPairs):
        '''
        Instead of calculating the gear train from scratch, use a predetermined one. Useful when using 4 wheels as those take a very long time to calculate
        '''
        #keep in the format of the autoformat
        time={'train': gearPinionPairs}

        self.trains = [time]

    def calculatePoweredWheelRatios(self, pinion_min = 11, pinion_max = 20, wheel_min = 20, wheel_max = 160, prefer_small=False):
        '''
        Calcualte the ratio of the chain wheel based on the desired runtime and chain drop
        TODO currently this tries to choose the largest wheel possible so it can fit. ideally we want the smallest wheel that fits to reduce plate size
        '''
        if self.chainWheels == 0:
            '''
            nothing to do, the diameter is calculted in calculatePoweredWheelInfo
            '''
        elif self.chainWheels == 1:

            turns = self.poweredWheel.getTurnsForDrop(self.getCordUsage())

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / (self.hours * self.minuteWheelRatio)

            desiredRatio = 1 / turnsPerHour

            # print("Chain wheel turns per hour", turnsPerHour)
            # print("Chain wheel ratio to minute wheel", desiredRatio)

            allGearPairCombos = []



            for p in range(pinion_min, pinion_max):
                for w in range(wheel_min, wheel_max):
                    allGearPairCombos.append([w, p])
            # print("ChainWheel: allGearPairCombos", len(allGearPairCombos))

            allRatios = []
            for i in range(len(allGearPairCombos)):
                ratio = allGearPairCombos[i][0] / allGearPairCombos[i][1]
                if round(ratio) == ratio:
                    # integer ratio
                    continue
                totalTeeth = 0
                # trying for small wheels and big pinions
                totalWheelTeeth = allGearPairCombos[i][0]
                totalPinionTeeth = allGearPairCombos[i][1]

                error = desiredRatio - ratio
                # perfer_small false (old behaviour): want a fairly large wheel so it can actually fit next to the minute wheel (which is always going to be pretty big)
                train = {"ratio": ratio, "pair": allGearPairCombos[i], "error": abs(error), "teeth": totalWheelTeeth}
                if abs(error) < 0.1:
                    allRatios.append(train)
            if not prefer_small:
                allRatios.sort(key=lambda x: x["error"] - x["teeth"] / 1000)
            else:
                #aim for small wheels where possible
                allRatios.sort(key=lambda x: x["error"] + x["teeth"] / 100)

            print("power wheel ratios", allRatios)
            if len(allRatios) == 0 :
                raise ValueError("Unable to generate gear ratio for powered wheel")
            self.chainWheelRatio = allRatios[0]["pair"]
        else:
            raise ValueError("Unsupported number of chain wheels")

    def setChainWheelRatio(self, pinionPair):
        '''
        Note, shouldn't need to use this anymore, and I think it's overriden when generating powered wheels anyway!
        '''
        self.chainWheelRatio = pinionPair

    def isWeightOnTheRight(self):
        '''
        returns true if the weight dangles from the right side of the chain wheel (as seen from the front)
        '''

        clockwise = self.poweredWheel.isClockwise()
        chainAtFront = not self.chainAtBack

        #XNOR
        clockwiseFromFront = not (clockwise != chainAtFront)

        return clockwiseFromFront

    def calculatePoweredWheelInfo(self, default_powered_wheel_diameter=20):
        '''
        Calculate best diameter and direction of ratchet
        '''
        if self.chainWheels == 0:
            #no choice but to set diameter to what fits with the drop and hours
            self.powered_wheel_circumference = self.getCordUsage() / (self.hours * self.minuteWheelRatio)
            self.powered_wheel_diameter = self.powered_wheel_circumference / math.pi

        elif self.chainWheels == 1:
            #set the diameter to the minimum so the chain wheel gear ratio is as low as possible (TODO - do we always want this?)

            self.powered_wheel_diameter = default_powered_wheel_diameter

            self.powered_wheel_circumference = self.powered_wheel_diameter * math.pi

        # true for no chainwheels
        anticlockwise = self.chainAtBack

        for i in range(self.chainWheels):
            anticlockwise = not anticlockwise

        self.powered_wheel_clockwise = not anticlockwise

    def genChainWheels2(self, chain, ratchetThick=7.5, arbourD=3, looseOnRod=True, prefer_small=False, preferedDiameter=-1, fixing_screws=None):

        diameter = preferedDiameter
        if diameter < 0:
            diameter = PocketChainWheel2.getMinDiameter()
        self.calculatePoweredWheelInfo(diameter)

        if self.huygensMaintainingPower:
            # there is no ratchet with this setup
            ratchetThick = 0
            # TODO check holeD?

        self.poweredWheel = PocketChainWheel2(ratchet_thick=ratchetThick, arbour_d=arbourD, looseOnRod=looseOnRod,
                                              power_clockwise=self.powered_wheel_clockwise, chain=chain, max_diameter=self.powered_wheel_diameter, fixing_screws=fixing_screws)

        self.calculatePoweredWheelRatios(prefer_small=prefer_small)

    def genChainWheels(self, ratchetThick=7.5, holeD=3.4, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15,screwThreadLength=10, prefer_small=False):
        '''
        HoleD of 3.5 is nice and loose, but I think it's contributing to making the chain wheel wonky - the weight is pulling it over a bit
        Trying 3.3, wondering if I'm going to want to go back to the idea of a brass tube in the middle
        Gone back to 3.4 now that the arbour extension is part of the wheel, should be more stable and I don't want problems with the hands turning backwards when winding!
        don't want it to be too loose so it doesn't butt up against the front plate.
        TODO - provide metric thread and do this inside the chain wheel

        Generate the gear ratios for the wheels between chain and minute wheel
        again, I'd like to make this generic but the solution isn't immediately obvious and it would take
        longer to make it generic than just make it work
        '''

        self.calculatePoweredWheelInfo(PocketChainWheel.getMinDiameter())

        if self.huygensMaintainingPower:
            #there is no ratchet with this setup
            ratchetThick = 0
            #TODO check holeD?

        self.poweredWheel = PocketChainWheel(ratchet_thick=ratchetThick, power_clockwise=self.powered_wheel_clockwise, max_circumference=self.powered_wheel_circumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)

        self.calculatePoweredWheelRatios(prefer_small=prefer_small)

    def genCordWheels(self,ratchetThick=7.5, rodMetricThread=3, cordCoilThick=10, useKey=False, cordThick=2, style="HAC", preferedDiameter=-1, looseOnRod=True, prefer_small=False):
        '''
        If preferred diameter is provided, use that rather than the min diameter
        '''
        diameter = preferedDiameter
        if diameter < 0:
            diameter = CordWheel.getMinDiameter()

        if self.huygensMaintainingPower:
            raise ValueError("Cannot use cord wheel with huygens maintaining power")

        self.calculatePoweredWheelInfo(diameter)
        self.poweredWheel = CordWheel(self.powered_wheel_diameter, ratchet_thick=ratchetThick, power_clockwise=self.powered_wheel_clockwise,rodMetricSize=rodMetricThread, thick=cordCoilThick, useKey=useKey, cordThick=cordThick, style=style, looseOnRod=looseOnRod)
        self.calculatePoweredWheelRatios(prefer_small=prefer_small)

    def genRopeWheels(self, ratchetThick = 3, arbour_d=3, ropeThick=2.2, wallThick=1.2, preferedDiameter=-1, use_steel_tube=True, o_ring_diameter=2, prefer_small=False):

        diameter = preferedDiameter
        if diameter < 0:
            diameter = RopeWheel.getMinDiameter()

        self.calculatePoweredWheelInfo(diameter)

        if self.huygensMaintainingPower:
            #there is no ratchet with this setup
            ratchetThick = 0


        if use_steel_tube:
            hole_d = STEEL_TUBE_DIAMETER
        else:
            hole_d = arbour_d + LOOSE_FIT_ON_ROD

        self.poweredWheel = RopeWheel(diameter=self.powered_wheel_diameter, hole_d = hole_d, ratchet_thick=ratchetThick, arbour_d=arbour_d,
                                      rope_diameter=ropeThick, power_clockwise=self.powered_wheel_clockwise, wall_thick=wallThick, o_ring_diameter=o_ring_diameter, need_bearing_standoff=True)

        self.calculatePoweredWheelRatios(prefer_small=prefer_small)


    def setTrain(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]


    def printInfo(self, weight_kg=0.35):
        print(self.trains[0])

        print("pendulum length: {}m period: {}s".format(self.pendulum_length, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement.teeth))
        print("Powered wheel diameter: {}".format(self.powered_wheel_diameter))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.getRunTime()))
        chainRatio = self.minuteWheelRatio
        chainRatios=[1]
        if self.chainWheels > 0:
            #TODO if - for some reason - the minuteWheelRatio isn't 1, this logic needs checking
            print(self.chainWheelRatio)
            #how many turns per turn of the minute wheel
            chainRatio = self.chainWheelRatio[0]/self.chainWheelRatio[1]
            #the wheel/pinion tooth count
            chainRatios=self.chainWheelRatio

        runtime_hours = self.poweredWheel.getRunTime(chainRatio, self.getCordUsage())

        drop_m = self.maxWeightDrop/1000
        power = weight_kg * GRAVITY * drop_m / (runtime_hours*60*60)
        power_uW = power * math.pow(10, 6)
        #for reference, the hubert hurr eight day cuckoo is aproximately 34uW
        print("runtime: {:.1f}hours using {:.1f}m of cord/chain for a weight drop of {}. Chain wheel multiplier: {:.1f} ({})".format(runtime_hours, self.getCordUsage() / 1000,self.maxWeightDrop, chainRatio, chainRatios))
        print("With a weight of {}kg, this results in an average power usage of {:.1f}μW".format(weight_kg, power_uW))

        if len(self.arbours) > 0:
            self.getArbourWithConventionalNaming(0).printScrewLength()
            self.getArbourWithConventionalNaming(0).poweredWheel.printScrewLength()
        else:
            print("Generate gears to get screw information")

        if self.poweredWheel.type == PowerType.CORD:
            #because there are potentially multiple layers of cord on a cordwheel, power lever can vary enough for the clock to be viable when wound and not halfway through its run time!
            #seen this on clock 10!

            (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.poweredWheel.getCordTurningInfo(self.maxWeightDrop*(2 if self.usePulley else 1))
            #cord per rotation divided by chainRatio, gives speed in mm per hour, we want in m/s to calculate power
            effective_weight = weight_kg / (2 if self.usePulley else 1)
            min_weight_speed = (cordPerRotationPerLayer[0] / chainRatio) /(60*60*1000)
            min_power = effective_weight * GRAVITY * min_weight_speed* math.pow(10, 6)
            max_weight_speed = (cordPerRotationPerLayer[-1] / chainRatio) / (60 * 60 * 1000)
            max_power = effective_weight * GRAVITY * max_weight_speed* math.pow(10, 6)
            print("Cordwheel power varies from {:.1f}μW to {:.1f}μW".format(min_power, max_power))

    def genGears(self, module_size=1.5, holeD=3, moduleReduction=0.5, thick=6, chainWheelThick=-1, escapeWheelThick=-1, escapeWheelMaxD=-1, useNyloc=False,
                 chainModuleIncrease=None, pinionThickMultiplier = 2.5, style="HAC", chainWheelPinionThickMultiplier=2, ratchetInset=False, thicknessReduction=1,
                 ratchetScrews=None, pendulumFixing=PendulumFixing.FRICTION_ROD, module_sizes = None, stack_away_from_powered_wheel=False):
        '''
        escapeWheelMaxD - if <0 (default) escape wheel will be as big as can fit
        if > 1 escape wheel will be as big as can fit, or escapeWheelMaxD big, if that is smaller
        if > 0 and < 1, escape wheel will be this fraction of the previous wheel

        stack_away_from_powered_wheel - experimental, usually we interleave gears to minimise plate distance, but we might want to minimise height instead

        '''
        self.pendulumFixing = pendulumFixing
        arbours = []
        # ratchetThick = holeD*2
        #thickness of just the wheel
        self.gearWheelThick=thick
        #thickness of arbour assembly
        #wheel + pinion (3*wheel) + pinion top (0.5*wheel)

        if chainWheelThick < 0:
            chainWheelThick = thick

        if escapeWheelThick < 0:
            escapeWheelThick = thick * (thicknessReduction**(self.wheels-1))

        # self.gearPinionLength=thick*3
        # self.chainGearPinionLength = chainWheelThick*2.5


        self.gearPinionEndCapLength=max(thick*0.25, 0.8)
        # self.gearTotalThick = self.gearWheelThick + self.gearPinionLength + self.gearPinionEndCapLength
        # self.chainGearTotalThick


        if module_sizes is None:
            module_sizes = [module_size * math.pow(moduleReduction, i) for i in range(self.wheels)]

        #the module of each wheel is slightly smaller than the preceeding wheel
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_sizes[i]) for i,wheel in enumerate(self.trains[0]["train"])]




        # print(module_sizes)
        #make the escape wheel as large as possible, by default
        escapeWheelDiameter = (pairs[len(pairs)-1].centre_distance - pairs[len(pairs)-1].pinion.getMaxRadius() - 3)*2

        #we might choose to override this
        if escapeWheelMaxD > 1 and escapeWheelDiameter > escapeWheelMaxD:
            escapeWheelDiameter = escapeWheelMaxD
        elif escapeWheelMaxD >0 and escapeWheelMaxD < 1:
            #treat as fraction of previous wheel
            escapeWheelDiameter = pairs[len(pairs) - 1].wheel.getMaxRadius() * 2 * escapeWheelMaxD

        # chain wheel imaginary pinion (in relation to deciding which way the next wheel faces) is opposite to where teh chain is
        chainWheelImaginaryPinionAtFront = self.chainAtBack

        #this was an attempt to put the second wheel over the top of the powered wheel, if it fits, but now there are so many different setups I'm just disabling it
        secondWheelR = pairs[1].wheel.getMaxRadius()
        firstWheelR = pairs[0].wheel.getMaxRadius() + pairs[0].pinion.getMaxRadius()
        poweredWheelEncasingRadius = self.poweredWheel.getEncasingRadius()#.ratchet.outsideDiameter/2
        space = firstWheelR - poweredWheelEncasingRadius
        if secondWheelR < space - 3:
            #the second wheel can actually fit on the same side as the ratchet
            chainWheelImaginaryPinionAtFront = not chainWheelImaginaryPinionAtFront
            print("Space to fit minute wheel in front of chain wheel - should result in smaller plate distance. check to ensure it does not clash with power mechanism")

        #this is a bit messy. leaving it alone for now, but basically we manually choose which way to have the escape wheel but by default it's at front (if the chain is also at the front)
        escapeWheelPinionAtFront = self.escapeWheelPinionAtFront

        #only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escapeWheelClockwise = self.wheels %2 == 1

        escapeWheelClockwiseFromPinionSide = escapeWheelPinionAtFront == escapeWheelClockwise

        pinionAtFront = chainWheelImaginaryPinionAtFront

        # print("Escape wheel pinion at front: {}, clockwise (from front) {}, clockwise from pinion side: {} ".format(escapeWheelPinionAtFront, escapeWheelClockwise, escapeWheelClockwiseFromPinionSide))
        #escapment is now provided or configured in the constructor
        # self.escapement = Escapement(teeth=self.escapement_teeth, diameter=escapeWheelDiameter, type=self.escapement_type, lift=self.escapement_lift, lock=self.escapement_lock, drop=self.escapement_drop, anchorTeeth=None, clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide)
        # self.escapement.setDiameter(escapeWheelDiameter)
        # self.escapement.clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide
        # self.escapement.escapeWheelClockwise=escapeWheelClockwise
        self.escapement.setGearTrainInfo(escapeWheelDiameter, escapeWheelClockwiseFromPinionSide, escapeWheelClockwise)
        self.chainWheelArbours=[]
        if self.chainWheels > 0:
            # assuming one chain wheel for now
            if chainModuleIncrease is None:
                chainModuleIncrease = (1 / moduleReduction)

            chainModule = module_size * chainModuleIncrease
            chainDistance = chainModule * (self.chainWheelRatio[0] + self.chainWheelRatio[1]) / 2

            minuteWheelSpace = pairs[0].wheel.getMaxRadius() + holeD*2
            if not self.poweredWheel.looseOnRod:
                #need space for the steel rod as the wheel itself is loose on the threaded rod
                minuteWheelSpace += 2

            #check if the chain wheel will fit next to the minute wheel
            if chainDistance < minuteWheelSpace:
                # calculate module for the chain wheel based on teh space available
                chainModule = 2 * minuteWheelSpace / (self.chainWheelRatio[0] + self.chainWheelRatio[1])
                print("Chain wheel module increased to {} in order to fit next to minute wheel".format(chainModule))
            self.chainWheelPair = WheelPinionPair(self.chainWheelRatio[0], self.chainWheelRatio[1], chainModule)
            #only supporting one at the moment, but open to more in the future if needed
            self.chainWheelPairs=[self.chainWheelPair]
            power_at_front = not self.chainAtBack
            clockwise = self.chainWheels % 2 == 1
            clockwise_from_powered_side = clockwise and power_at_front
            self.chainWheelArbours=[Arbour(poweredWheel=self.poweredWheel, wheel = self.chainWheelPair.wheel, wheelThick=chainWheelThick, arbourD=self.poweredWheel.arbour_d,
                                           distanceToNextArbour=self.chainWheelPair.centre_distance, style=style, ratchetInset=ratchetInset, ratchetScrews=ratchetScrews,
                                           useRatchet=not self.huygensMaintainingPower, pinionAtFront=power_at_front, clockwise_from_pinion_side=clockwise_from_powered_side)]

            pinionAtFront = not pinionAtFront

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                if self.chainWheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbour(poweredWheel=self.poweredWheel, wheel = pairs[i].wheel, wheelThick=chainWheelThick, arbourD=self.poweredWheel.arbour_d, distanceToNextArbour=pairs[i].centre_distance,
                                    style=style, pinionAtFront=not self.chainAtBack, ratchetInset=ratchetInset, ratchetScrews=ratchetScrews, useRatchet=not self.huygensMaintainingPower,
                                    clockwise_from_pinion_side=not self.chainAtBack)
                else:
                    clockwise = i % 2 == 0
                    clockwise_from_pinion_side = clockwise and pinionAtFront
                    #just a normal gear
                    if self.chainWheels == 1:
                        pinionThick = self.chainWheelArbours[-1].wheelThick * chainWheelPinionThickMultiplier
                    else:
                        pinionThick = self.chainWheelArbours[-1].wheelThick * pinionThickMultiplier
                    arbour = Arbour(wheel = pairs[i].wheel, pinion=self.chainWheelPair.pinion, arbourD=holeD, wheelThick=thick, pinionThick=pinionThick, endCapThick=self.gearPinionEndCapLength,
                                    distanceToNextArbour= pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront, clockwise_from_pinion_side=clockwise_from_pinion_side)

                if useNyloc:
                    #regardless of chains, we need a nyloc nut to fix the wheel to the rod
                    arbour.setNutSpace(holeD)

                arbours.append(arbour)
                if stack_away_from_powered_wheel:
                    #only the minute wheel behind teh chain wheel
                    pinionAtFront = not pinionAtFront

            elif i < self.wheels-1:
                pinionThick = arbours[-1].wheelThick * pinionThickMultiplier

                if self.chainWheels == 0 and i == 1:
                    #this pinion is for the chain wheel
                    pinionThick = arbours[-1].wheelThick * chainWheelPinionThickMultiplier

                #intermediate wheels
                #no need to worry about front and back as they can just be turned around
                arbours.append(Arbour(wheel=pairs[i].wheel, pinion=pairs[i-1].pinion, arbourD=holeD, wheelThick=thick*(thicknessReduction**i), pinionThick=pinionThick, endCapThick=self.gearPinionEndCapLength,
                                distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront))
            else:
                #Using the manual override to try and ensure that the anchor doesn't end up against the back plate (or front plate)
                #automating would require knowing how far apart the plates are, which we don't at this point, so just do it manually
                pinionAtFront = self.escapeWheelPinionAtFront

                #last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                #escape wheel has its thickness controlled by the escapement, but we control the arbour diameter
                arbours.append(Arbour(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbourD=holeD, pinionThick=arbours[-1].wheelThick * pinionThickMultiplier, endCapThick=self.gearPinionEndCapLength,
                                      distanceToNextArbour=self.escapement.getDistanceBeteenArbours(), style=style, pinionAtFront=pinionAtFront))
            if not stack_away_from_powered_wheel:
                pinionAtFront = not pinionAtFront

        #anchor is the last arbour
        #"pinion" is the direction of the extended arbour for fixing to pendulum
        #this doesn't need arbourD or thickness as this is controlled by the escapement
        arbours.append(Arbour(escapement=self.escapement, pinionAtFront=self.penulumAtFront, pendulumFixing=pendulumFixing))

        self.wheelPinionPairs = pairs
        self.arbours = arbours




        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

    def getArbourWithConventionalNaming(self, i):
        '''
        Use the traditional naming of the chain wheel being zero
        if -ve, count from the anchor backwards (like array indexing in python, so -1 is the anchor, -2 is the escape wheel)
        '''
        if i < 0:
            i = i + len(self.arbours) + len(self.chainWheelArbours)
        return self.getArbour(i - self.chainWheels)

    def getArbour(self, i):
        '''
        +ve is in direction of the anchor
        0 is minute wheel
        -ve is in direction of power ( so last chain wheel is -1, first chain wheel is -chainWheels)
        '''

        if i >= 0:
            return self.arbours[i]
        else:
            return self.chainWheelArbours[self.chainWheels+i]


    # def getMinuteWheelPinionPair(self):
    #     return self.wheelPinionPairs[0]

    def outputSTLs(self, name="clock", path="../out"):
        '''
        Going train soon will no longer need to generates shapes - it provides only basic Arbours for the plates to turn into printable objects
        '''
        #wheels, chainwheels
        for i in range(self.wheels+self.chainWheels+1):
            arbour = self.getArbourWithConventionalNaming(i)
            out = os.path.join(path,"{}_wheel_{}.stl".format(name,i))
            print("Outputting ",out)
            exporters.export(arbour.getShape(), out)
            extras = arbour.getExtras()
            for extraName in extras:
                out = os.path.join(path, "{}_wheel_{}_{}.stl".format(name, i, extraName))
                print("Outputting ", out)
                exporters.export(extras[extraName], out)

        self.poweredWheel.outputSTLs(name, path)

        if self.escapement.type == EscapementType.GRASSHOPPER:
            self.escapement.outputSTLs(name, path)

        # if not self.huygensMaintainingPower:
            #undecided, but I think I'm going to keep the STLs generated here
            #if we are using huygens there powered wheel is permanently attached to a gear wheel, and is generated with the arbour


        # for i,arbour in enumerate(self.chainWheelArbours):
        #     out = os.path.join(path, "{}_chain_wheel_{}.stl".format(name, i))
        #     print("Outputting ", out)
        #     exporters.export(arbour.getShape(), out)


        # out = os.path.join(path, "{}_escapement_test_rig.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(self.escapement.getTestRig(), out)

        # out = os.path.join(path, "{}_anchor_spanner.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(getSpanner(thick=self.arbours[-1].spannerBitThick,size=self.arbours[-1].getAnchorSpannerSize()), out)


class SimpleClockPlates:
    '''
    This took a while to settle - clocks before v4 will be unlikely to work anymore.

    Given that the simple plate is the only working implementation, would it make more sense to turn this class into the SimpleClockPlates?

    Any future plates are likely to be be very different in terms out laying out gears, and anything that is needed can always be spun out

    '''
    def __init__(self, goingTrain, motionWorks, pendulum, style=ClockPlateStyle.VERTICAL, arbourD=3, pendulumAtTop=True, plateThick=5, backPlateThick=None,
                 pendulumSticksOut=20, name="", heavy=False, extraHeavy=False, motionWorksAbove=False, pendulumFixing = PendulumFixing.FRICTION_ROD,
                 pendulumAtFront=True, backPlateFromWall=0, fixingScrews=None, escapementOnFront=False, extraFrontPlate=False, chainThroughPillarRequired=True,
                 centred_second_hand=False, pillars_separate=False, dial=None, direct_arbour_d=DIRECT_ARBOUR_D, huygens_wheel_min_d=15, allow_bottom_pillar_height_reduction=False,
                 bottom_pillars=1, centre_weight=False):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!

        escapementOnFront: if true the escapement is mounted on the front of teh clock (helps with laying out a grasshopper) and if false, inside the plates like the rest of the train

        '''

        #how the pendulum is fixed to the anchor arbour. TODO centralise this
        self.pendulumFixing = pendulumFixing
        self.pendulumAtFront = pendulumAtFront

        #diameter of the cylinder that forms the arbour that physically links pendulum holder (or crutch in future) and anchor
        self.direct_arbour_d = direct_arbour_d

        self.dial = dial

        #are the main pillars attached to the back plate or independent? currently needs backPlateFromWall to create wall standoffs in order to screw to back plate
        self.pillars_separate = pillars_separate

        #try and put the weight central to the clock. Only currently affects the compact style when using two pillars
        self.centre_weight = centre_weight

        #second hand is centred on the motion works
        self.centred_second_hand = centred_second_hand

        #does the chain/rope/cord pass through the bottom pillar?
        self.chainThroughPillar = chainThroughPillarRequired




        anglesFromMinute = None
        anglesFromChain = None

        self.style=style

        #to print on the back
        self.name = name

        #is the motion works arbour above the cannon pinion? if centred_second_hand then this is not user-controllable
        self.motionWorksAbove=motionWorksAbove
        #escapement is on top of the front plate
        self.escapementOnFront = escapementOnFront
        #only valid if escapementOnFront. This adds an extra front plate that goes up to the escape wheel, to add stability for the large grasshopper esacpe wheel
        #not used yet, trying extending a bearing out the front to just behind the escape wheel first
        #DEPRECATED
        self.extraFrontPlate = extraFrontPlate

        #if true, mount the escapment on the front of the clock (to show it off or help the grasshopper fit easily)
        #if false, it's between the plates like the rest of the gear train
        #not sure much actually needs to change for the plates?
        # self.escapementOnFront = goingTrain.escapementOnFront
        #use the weight on a pulley with a single loop of chain/rope, going over a ratchet on the front of the clock and a counterweight on the other side from the main weight
        #easiest to implement with a chain
        self.huygensMaintainingPower = goingTrain.huygensMaintainingPower
        #for plates with very little distance (eg grasshopper) the bottom pillar will be small - but we still need a largeish wheel for the chain
        self.huygens_wheel_min_d = huygens_wheel_min_d

        #is the weight heavy enough that we want to chagne the plate design?
        #will result in wider plates up to the chain wheel
        self.heavy = heavy
        #beef up the pillars as well
        self.extraHeavy = extraHeavy

        if self.extraHeavy:
            self.heavy = True

        #2 or 1?
        self.bottom_pillars = bottom_pillars

        #make the bottom pillar long a thin rather than round?
        self.narrow_bottom_pillar = self.bottom_pillars > 1

        #is the weight danging from a pulley? (will affect screwhole and give space to tie other end of cord)
        self.usingPulley = goingTrain.usePulley

        #the hole for the key to slot through is big enough for the key to slot partially into the front plate
        #HACK this is calculated when generating the front plate
        self.front_plate_has_key_hole = False

        #how much space the crutch will need - used for work out where to put the bearing for the anchor
        self.crutch_space = 10


        #just for the first prototype (hahahahah, lasted a long time until PendulumFixing.SUSPENSION_SPRING)
        self.anchorHasNormalBushing=True
        self.motionWorks = motionWorks
        self.goingTrain = goingTrain
        self.pendulum=pendulum
        #up to and including the anchor
        self.anglesFromMinute = anglesFromMinute
        self.anglesFromChain=anglesFromChain
        self.plateThick=plateThick
        self.backPlateThick = backPlateThick
        if self.backPlateThick is None:
            self.backPlateThick = self.plateThick
        #default for anchor, overriden by most arbours
        self.arbourD=arbourD
        #how chunky to make the bearing holders
        self.bearingWallThick = 4

        #for fixing to teh wall
        self.wallFixingScrewHeadD = 11

        self.pendulumAtTop = pendulumAtTop
        #how far away from the relevant plate (front if pendulumAtFront) the pendulum should be
        self.pendulumSticksOut = pendulumSticksOut
        #if this is 0 then pendulumAtFront is going to be needed
        self.backPlateFromWall = backPlateFromWall
        self.fixingScrews = fixingScrews
        if self.fixingScrews is None:
            #PREVIOUSLY longest pozihead countersunk screws I can easily get are 25mm long. I have some 40mm flathead which could be deployed if really needed
            #now found supplies of pozihead countersunk screws up to 60mm, so planning to use two screws (each at top and bottom) to hold everything together
            self.fixingScrews = MachineScrew(metric_thread=3, countersunk=True)#, length=25)

        # how thick the bearing holder out the back or front should be
        # can't use bearing from ArborForPlate yet as they haven't been generated
        # bit thicker than the front bearing thick because this may have to be printed with supports
        if pendulumFixing == PendulumFixing.SUSPENSION_SPRING:
            self.rear_standoff_bearing_holder_thick = getBearingInfo(goingTrain.getArbourWithConventionalNaming(-1).arbourD).height + 2
        else:
            self.rear_standoff_bearing_holder_thick = self.plateThick

        # how much space to leave around the edge of the gears for safety
        self.gearGap = 3
        # if self.style == ClockPlateStyle.COMPACT:
        #     self.gearGap = 2
        self.smallGearGap = 2

        #if the bottom pillar radius is increased to allow space for the chains to fit through, do we permit the gear wheel to cut into that pillar?
        self.allow_bottom_pillar_height_reduction = allow_bottom_pillar_height_reduction

        if self.allow_bottom_pillar_height_reduction and self.bottom_pillars > 1:
            raise ValueError("Does not support pillar height reduction with more than one pillar")

        self.weightOnRightSide = self.goingTrain.isWeightOnTheRight()

        self.calc_bearing_positions()
        self.generate_arbours_for_plate()

        self.chainHoleD = self.goingTrain.poweredWheel.getChainHoleD()

        if self.chainHoleD < 4:
            self.chainHoleD = 4



        #absolute z position for the embedded nuts for the front plate to be held on (from before there was a wall standoff or an extra front plate)
        self.embeddedNutHeightForFrontPlateFixings = self.getPlateThick(back=True) + self.plateDistance + self.getPlateThick(back=False) - (self.fixingScrews.length - 7.5)

        self.chainWheelR = self.goingTrain.getArbour(-self.goingTrain.chainWheels).getMaxRadius() + self.gearGap

        self.calc_pillar_info()


        #fixing positions to plates and pillars together
        self.plate_top_fixings = [(self.topPillarPos[0] - self.topPillarR / 2, self.topPillarPos[1]), (self.topPillarPos[0] + self.topPillarR / 2, self.topPillarPos[1])]
        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottomPillarPositions:
            self.plate_bottom_fixings +=[
                (bottom_pillar_pos[0], bottom_pillar_pos[1] + self.bottomPillarR * 0.5 - self.reduce_bottom_pillar_height / 3),
                (bottom_pillar_pos[0], bottom_pillar_pos[1] - self.bottomPillarR * 0.5)
            ]
        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings

        self.extraFrontPlateDistance = 0
        #mounting position (that's not the bottom pillar)
        self.extraFrontPlateMountingPos = None
        self.extraFrontPlateFixings = []

        if self.escapementOnFront and self.extraFrontPlate:
            escapeWheelTopZFromFront = -self.goingTrain.escapement.getWheelBaseToAnchorBaseZ() + self.goingTrain.escapement.getWheelThick()

            self.extraFrontPlateDistance = escapeWheelTopZFromFront + self.endshake*2
            topSafe = self.bearingPositions[-2][1] - self.goingTrain.escapement.getWheelMaxR() - self.gearGap
            bottomSafe = self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorks.getHourHolderMaxRadius() + self.gearGap
            self.extraFrontPlateMountingPos = (self.bearingPositions[-2][0], (topSafe + bottomSafe)/2)
            self.extraFrontPlateMountingLength = topSafe - bottomSafe
            self.extraFrontPlateFixings =  [(self.extraFrontPlateMountingPos[0], self.extraFrontPlateMountingPos[1] - self.extraFrontPlateMountingLength / 2 + self.plateWidth / 4), (self.extraFrontPlateMountingPos[0], self.extraFrontPlateMountingPos[1] + self.extraFrontPlateMountingLength / 2 - self.plateWidth / 4)]

        self.huygensWheel = None
        #offset in y? This enables the plate to stay smaller (and fit on the print bed) while still offering a large huygens wheel
        self.huygens_wheel_y_offset = 0
        if self.huygensMaintainingPower:
            max_circumference = self.bottomPillarR * 1.25 * math.pi
            max_diameter = max_circumference/math.pi
            ratchetOuterD = self.bottomPillarR * 2

            if max_diameter < self.huygens_wheel_min_d:
                max_diameter = self.huygens_wheel_min_d
                max_circumference = max_diameter*math.pi
                ratchetOuterD = max_diameter+15
                if ratchetOuterD < self.bottomPillarR*2:
                    #have seen this happen, though I think it's rare
                    ratchetOuterD = self.bottomPillarR*2
                self.huygens_wheel_y_offset = ratchetOuterD / 2 - self.bottomPillarR

            ratchetOuterThick = 3
            ratchet_thick=5
            #need a powered wheel and ratchet on the front!
            if self.goingTrain.poweredWheel.type == PowerType.CHAIN:

                self.huygensWheel = PocketChainWheel(ratchet_thick=5, max_circumference=max_circumference, wire_thick=self.goingTrain.poweredWheel.chain_thick,
                                                     width=self.goingTrain.poweredWheel.chain_width, inside_length=self.goingTrain.poweredWheel.chain_inside_length,
                                                     tolerance=self.goingTrain.poweredWheel.tolerance, ratchetOuterD=self.bottomPillarR*2, ratchetOuterThick=ratchetOuterThick)
            elif self.goingTrain.poweredWheel.type == PowerType.CHAIN2:
                self.huygensWheel = PocketChainWheel2(ratchet_thick=5, max_diameter=max_diameter, chain=self.goingTrain.poweredWheel.chain, looseOnRod=True,
                                                      ratchetOuterD=ratchetOuterD, ratchetOuterThick=ratchetOuterThick, arbour_d=self.goingTrain.poweredWheel.arbour_d)
            elif self.goingTrain.poweredWheel.type == PowerType.ROPE:
                huygens_diameter = max_diameter*0.95
                print("Huygens wheel diameter",huygens_diameter)
                self.huygensWheel = RopeWheel(diameter=huygens_diameter, ratchet_thick=ratchet_thick, rope_diameter=self.goingTrain.poweredWheel.rope_diameter, o_ring_diameter=get_o_ring_thick(huygens_diameter - self.goingTrain.poweredWheel.rope_diameter*2),
                                              hole_d=self.goingTrain.poweredWheel.hole_d, ratchet_outer_d=self.bottomPillarR*2, ratchet_outer_thick=ratchetOuterThick)
            else:
                raise ValueError("Huygens maintaining power not currently supported with {}".format(self.goingTrain.poweredWheel.type.value))

        self.hands_position = self.bearingPositions[self.goingTrain.chainWheels][:2]

        if self.centred_second_hand:
            #adjust motion works size
            distance_between_minute_wheel_and_seconds_wheel = np.linalg.norm(np.subtract(self.bearingPositions[self.goingTrain.chainWheels][:2], self.bearingPositions[-2][:2]))
            self.motionWorks.calculateGears(arbourDistance= distance_between_minute_wheel_and_seconds_wheel/2)

            #override motion works position
            self.motionWorksAbove = not self.pendulumAtTop
            self.hands_position = [self.bearingPositions[-2][0],self.bearingPositions[-2][1]]

        motionWorksDistance = self.motionWorks.getArbourDistance()
        # get position of motion works relative to the minute wheel
        if style == ClockPlateStyle.ROUND:
            # place the motion works on the same circle as the rest of the bearings
            angle = self.hands_on_side*2 * math.asin(motionWorksDistance / (2 * self.compactRadius))
            compactCentre = (0, self.compactRadius)
            minuteAngle = math.atan2(self.bearingPositions[self.goingTrain.chainWheels][1] - compactCentre[1], self.bearingPositions[self.goingTrain.chainWheels][0] - compactCentre[0])
            motionWorksPos = polar(minuteAngle - angle, self.compactRadius)
            motionWorksPos = (motionWorksPos[0] + compactCentre[0], motionWorksPos[1] + compactCentre[1])
            self.motionWorksRelativePos = (motionWorksPos[0] - self.bearingPositions[self.goingTrain.chainWheels][0], motionWorksPos[1] - self.bearingPositions[self.goingTrain.chainWheels][1])
        else:
            # motion works is directly below the minute rod
            self.motionWorksRelativePos = [0, motionWorksDistance * (1 if self.motionWorksAbove else -1)]

        self.motionWorksPos = npToSet(np.add(self.hands_position, self.motionWorksRelativePos))

        #even if it's not used:

        #TODO calculate so it's always just big enough?
        self.motion_works_holder_length = 30
        self.motion_works_holder_wide = self.plateWidth
        self.motion_works_fixings_relative_pos = [(-self.plateWidth/4,self.motion_works_holder_length/2) ,
                                                  (self.plateWidth/4,-(self.motion_works_holder_length/2))]
        if self.dial is not None:
            #calculate dial height after motion works gears have been generated, in case the height changed with the bearing
            # height of dial from top of front plate
            # previously given 8mm of clearance, but this was more than enough, so reducing down to 4
            self.dial_z = self.bottom_of_hour_hand_z() - self.dial.thick - 3
            if self.goingTrain.has_seconds_hand() and not self.centred_second_hand:
                #mini second hand! give a smidge more clearance
                self.dial_z -= 2
            self.top_of_hands_z = self.motionWorks.get_cannon_pinion_effective_height() + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT
            print("dial z", self.dial_z)

            if self.goingTrain.has_seconds_hand():
                second_hand_relative_pos = npToSet(np.subtract(self.bearingPositions[-2], self.bearingPositions[self.goingTrain.chainWheels]))[0:2]

                if self.centred_second_hand:
                    second_hand_mini_dial_d = -1
                    second_hand_relative_pos = None
                else:
                    distance_to_seconds = np.linalg.norm(second_hand_relative_pos)
                    #just overlapping a tiny bit
                    second_hand_mini_dial_d = (self.dial.inner_r - distance_to_seconds + 2)*2
                    print("second_hand_mini_dial_d: {}".format(second_hand_mini_dial_d))

                self.dial.configure_dimensions(support_length=self.dial_z, support_d=self.plateWidth,second_hand_relative_pos=second_hand_relative_pos , second_hand_mini_dial_d=second_hand_mini_dial_d)
            else:
                self.dial.configure_dimensions(support_length=self.dial_z, support_d=self.plateWidth)

        # if this has a key (do after we've calculated the dial z)
        if self.goingTrain.poweredWheel.type == PowerType.CORD and self.goingTrain.poweredWheel.useKey:
            self.calc_winding_key_info()


        self.front_z = self.getPlateThick(back=True) + self.plateDistance + self.getPlateThick(back=False)

        #cache stuff that's needed multiple times to speed up generating clock
        self.fixing_screws_cutter = None
        self.need_motion_works_holder = self.calc_need_motion_works_holder()

    def generate_arbours_for_plate(self):

        self.arboursForPlate = []

        print("Plate distance", self.plateDistance)

        #configure stuff for the arbours, now we know their absolute positions
        # poweredWheel=self.goingTrain.getArbourWithConventionalNaming(0)
        # poweredWheelBracingR = poweredWheel.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(1).getMaxRadius() - self.gearGap
        #
        # #no need for it to be massive
        # poweredWheelBracingR = min(10,poweredWheelBracingR)
        # poweredWheel.setArbourExtensionInfo(rearSide=self.bearingPositions[0][2], maxR=poweredWheelBracingR)

        for i,bearingPos in enumerate(self.bearingPositions):
            arbour = self.goingTrain.getArbourWithConventionalNaming(i)
            if i < self.goingTrain.wheels + self.goingTrain.chainWheels - 2:
                maxR = arbour.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(i+1).getMaxRadius() - self.smallGearGap
            else:
                maxR = 0
            #hacky hack hack, I really think I should put escapementOnFront into GoingTrain
            arbour.escapementOnFront = self.escapementOnFront
            #deprecated way of doing it - passing loads of info to the Arbour class
            arbour.setPlateInfo(rearSideExtension=bearingPos[2], maxR=maxR, frontSideExtension=self.plateDistance - self.endshake - bearingPos[2] - arbour.getTotalThickness(),
                                frontPlateThick=self.getPlateThick(back=False), pendulumSticksOut=self.pendulumSticksOut, backPlateThick=self.getPlateThick(back=True), endshake=self.endshake,
                                plateDistance=self.plateDistance, escapementOnFront=self.escapementOnFront)

            bearing = getBearingInfo(arbour.arbourD)

            #new way of doing it, new class for combining all this logic in once place
            arbourForPlate = ArbourForPlate(arbour, self, bearing_position=bearingPos, arbour_extension_max_radius=maxR, pendulum_sticks_out=self.pendulumSticksOut,
                                            pendulum_at_front=self.pendulumAtFront, bearing=bearing, escapement_on_front=self.escapementOnFront, back_from_wall=self.backPlateFromWall,
                                            endshake=self.endshake, pendulum_fixing=self.pendulumFixing, direct_arbour_d=self.direct_arbour_d, crutch_space=self.crutch_space,
                                            previous_bearing_position=self.bearingPositions[i-1])
            self.arboursForPlate.append(arbourForPlate)




    def calc_bearing_positions(self):

        # if angles are not given, assume clock is entirely vertical, unless overriden by style below

        if self.anglesFromMinute is None:
            # assume simple pendulum at top
            angle = math.pi / 2 if self.pendulumAtTop else math.pi / 2

            # one extra for the anchor
            self.anglesFromMinute = [angle for i in range(self.goingTrain.wheels + 1)]
        if self.anglesFromChain is None:
            angle = math.pi / 2 if self.pendulumAtTop else -math.pi / 2

            self.anglesFromChain = [angle for i in range(self.goingTrain.chainWheels)]

        if self.style == ClockPlateStyle.COMPACT:
            '''
            idea: in a loop guess at the first angle, then do all the next angles such that it's as compact as possible without the wheels touching each other
            then see if it's possible to put the pendulum directly above the hands
            if it's not, tweak the first angle and try again
            
            second thoughts: would it be easier to force a line of gears and then every other gear is just off to one side?
            Not peak compactness but might keep the plate design easier
            '''
            # if self.goingTrain.chainWheels > 0:

            #thoughts: make which side the gears stick out adjustable?
            on_side = +1
            '''
            Have a line of gears vertical from hands to anchor, and any gears in between off to one side
            '''
            minute_wheel_to_second_wheel = self.goingTrain.getArbour(0).distanceToNextArbour
            second_wheel_to_third_wheel = self.goingTrain.getArbour(1).distanceToNextArbour
            minute_wheel_to_third_wheel = self.goingTrain.getArbour(0).getMaxRadius() + self.goingTrain.getArbour(2).pinion.getMaxRadius() + self.smallGearGap
            b = minute_wheel_to_second_wheel
            c = second_wheel_to_third_wheel
            a = minute_wheel_to_third_wheel
            # cosine law
            angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
            self.anglesFromMinute[0] = math.pi/2 + on_side*angle

            minute_wheel_pos = (0,0)
            third_wheel_pos = (0,minute_wheel_to_third_wheel)
            second_wheel_pos = polar(self.anglesFromMinute[0],minute_wheel_to_second_wheel)
            third_wheel_from_second_wheel = npToSet(np.subtract(third_wheel_pos, second_wheel_pos))
            self.anglesFromMinute[1] = math.atan2(third_wheel_from_second_wheel[1], third_wheel_from_second_wheel[0])
            #TODO if the second wheel would clash with the powered wheel, push the third wheel up higher
            #
            if self.goingTrain.wheels > 3:
                #stick the escape wheel out too
                third_wheel_to_escape_wheel = self.goingTrain.getArbour(2).distanceToNextArbour
                escape_wheel_to_anchor = self.goingTrain.getArbour(3).distanceToNextArbour
                #third_wheel_to_anchor is a bit tricky to calculate. going to try instead just choosing an angle
                #TODO could make anchor thinner and then it just needs to avoid the rod
                third_wheel_to_anchor = self.goingTrain.getArbourWithConventionalNaming(-1).getMaxRadius() + self.goingTrain.getArbour(2).getMaxRadius() + self.smallGearGap

                b = third_wheel_to_escape_wheel
                c = escape_wheel_to_anchor
                a = third_wheel_to_anchor
                # cosine law
                angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
                self.anglesFromMinute[2] = math.pi / 2 + on_side * angle

                # #choosing an angle manually:
                # self.anglesFromMinute[2] = math.pi/2 + on_side*self.goingTrain.escapement.escaping_arc*4

                escape_wheel_pos = polar( self.anglesFromMinute[2],third_wheel_to_escape_wheel)
                angle = math.acos(abs(escape_wheel_pos[0])/escape_wheel_to_anchor)
                #TODO make generic: only works if we're on the left side?
                self.anglesFromMinute[3] =  angle


            #aim: have pendulum directly above hands
            positions = [(0,0)]
            for i in range(1, self.goingTrain.wheels):
                positions.append(npToSet(np.add(positions[i-1], polar(self.anglesFromMinute[i-1], self.goingTrain.getArbour(i-1).distanceToNextArbour))))

            escape_wheel_to_anchor = self.goingTrain.getArbour(-2).distanceToNextArbour
            if escape_wheel_to_anchor < abs(positions[-1][0]):
                #need to re-think how this works
                raise ValueError("Cannot put anchor above hands without tweaking")

            if self.bottom_pillars > 1 and not self.usingPulley and self.goingTrain.chainWheels > 0 and self.centre_weight:
                #put chain in the centre. this works (although lots of things assume the bottom bearing is in the centre)
                #but I'm undecided if I actually want it - if we have two screwholes is that sufficient? the reduction in height is minimal
                x = self.goingTrain.poweredWheel.diameter/2
                r = self.goingTrain.getArbourWithConventionalNaming(0).distanceToNextArbour
                angle = math.acos(x/r)
                if self.weightOnRightSide:
                    self.anglesFromChain[0] = math.pi - angle
                else:
                    self.anglesFromChain[0] = angle



        if self.style == ClockPlateStyle.ROUND:

            # TODO decide if we want the train to go in different directions based on which side the weight is
            self.hands_on_side = 1 if self.goingTrain.isWeightOnTheRight() else -1
            arbours = [self.goingTrain.getArbourWithConventionalNaming(arbour) for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels)]
            distances = [arbour.distanceToNextArbour for arbour in arbours]
            maxRs = [arbour.getMaxRadius() for arbour in arbours]
            arcAngleDeg = 270

            foundSolution = False
            while (not foundSolution and arcAngleDeg > 180):
                arcRadius = getRadiusForPointsOnAnArc(distances, degToRad(arcAngleDeg))

                # minDistance = max(distances)

                if arcRadius > max(maxRs):
                    # if none of the gears cross the centre, they should all fit
                    # pretty sure there are other situations where they all fit
                    # and it might be possible for this to be true and they still don't all fit
                    # but a bit of playing around and it looks true enough
                    foundSolution = True
                    self.compactRadius = arcRadius
                else:
                    arcAngleDeg -= 1
            if not foundSolution:
                raise ValueError("Unable to calculate radius for gear ring, try a vertical clock instead")

            angleOnArc = -math.pi / 2
            lastPos = polar(angleOnArc, arcRadius)

            for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels):
                '''
                Calculate angle of the isololese triangle with the distance at the base and radius as the other two sides
                then work around the arc to get the positions
                then calculate the relative angles so the logic for finding bearing locations still works
                bit over complicated
                '''
                # print("angle on arc: {}deg".format(radToDeg(angleOnArc)))
                nextAngleOnArc = angleOnArc + 2 * math.asin(distances[i + self.goingTrain.chainWheels] / (2 * arcRadius)) * self.hands_on_side
                nextPos = polar(nextAngleOnArc, arcRadius)

                relativeAngle = math.atan2(nextPos[1] - lastPos[1], nextPos[0] - lastPos[0])
                if i < 0:
                    self.anglesFromChain[i + self.goingTrain.chainWheels] = relativeAngle
                else:
                    self.anglesFromMinute[i] = relativeAngle
                lastPos = nextPos
                angleOnArc = nextAngleOnArc

        # [[x,y,z],]
        # for everything, arbours and anchor
        self.bearingPositions = []
        # TODO consider putting the anchor on a bushing
        # self.bushingPositions=[]
        self.arbourThicknesses = []
        # how much the arbours can wobble back and forth. aka End-shake.
        # 2mm seemed a bit much
        self.endshake = 1
        # height of the centre of the wheel that will drive the next pinion
        drivingZ = 0
        for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels + 1):
            # print(str(i))
            if i == -self.goingTrain.chainWheels:
                # the wheel with chain wheel ratchet
                # assuming this is at the very back of the clock
                # note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearingPositions.append(pos)
                # note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.goingTrain.getArbour(i).getWheelCentreZ()
                self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())
                # print("pinionAtFront: {} wheel {} drivingZ: {}".format(self.goingTrain.getArbour(i).pinionAtFront, i, drivingZ), pos)
            else:
                r = self.goingTrain.getArbour(i - 1).distanceToNextArbour
                # print("r", r)
                # all the other going wheels up to and including the escape wheel
                if i == self.goingTrain.wheels:
                    # the anchor
                    if self.escapementOnFront:
                        # there is nothing between the plates for this
                        self.arbourThicknesses.append(0)
                        # don't do anything else
                    else:
                        escapement = self.goingTrain.getArbour(i).escapement
                        baseZ = drivingZ - self.goingTrain.getArbour(i - 1).wheelThick / 2 + escapement.getWheelBaseToAnchorBaseZ()
                        self.arbourThicknesses.append(escapement.getAnchorThick())
                    # print("is anchor")
                else:
                    # any of the other wheels
                    # pinionAtBack = not pinionAtBack
                    # print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(), self.goingTrain.getArbour(i).getPinionCentreZ()))
                    pinionToWheel = self.goingTrain.getArbour(i).getPinionToWheelZ()
                    pinionZ = self.goingTrain.getArbour(i).getPinionCentreZ()
                    baseZ = drivingZ - pinionZ

                    drivingZ = drivingZ + pinionToWheel
                    # massive bodge here, the arbour doesn't know about the escapement being on the front yet
                    self.goingTrain.getArbour(i).escapementOnFront = self.escapementOnFront
                    arbourThick = self.goingTrain.getArbour(i).getTotalThickness()

                    self.arbourThicknesses.append(arbourThick)

                if i <= 0:
                    angle = self.anglesFromChain[i - 1 + self.goingTrain.chainWheels]
                else:
                    angle = self.anglesFromMinute[i - 1]
                v = polar(angle, r)
                # v = [v[0], v[1], baseZ]
                lastPos = self.bearingPositions[-1]
                # pos = list(np.add(self.bearingPositions[i-1],v))
                pos = [lastPos[0] + v[0], lastPos[1] + v[1], baseZ]
                # if i < self.goingTrain.wheels:
                #     print("pinionAtFront: {} wheel {} r: {} angle: {}".format( self.goingTrain.getArbour(i).pinionAtFront, i, r, angle), pos)
                # print("baseZ: ",baseZ, "drivingZ ", drivingZ)

                self.bearingPositions.append(pos)

        # print(self.bearingPositions)

        topZs = [self.arbourThicknesses[i] + self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZs = [self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZ = min(bottomZs)
        if bottomZ < 0:
            # positions are relative (chain at front), so readjust everything
            topZs = [z - bottomZ for z in topZs]
            # bottomZs = [z - bottomZ for z in bottomZs]
            for i in range(len(self.bearingPositions)):
                self.bearingPositions[i][2] -= bottomZ

        '''
        something is always pressed up against both the front and back plate. If it's a powered wheel that's designed for that (the chain/rope wheel is designed to use a washer,
        and the key-wound cord wheel is specially shaped) then that's not a problem.

        However if it's just a pinion (or a wheel - somehow?), or and anchor (although this should be avoided now by choosing where it goes) then that's extra friction

        TODO - I assumed that the chainwheel was alays the frontmost or backmost, but that isn't necessarily true.
        '''
        needExtraFront = False
        needExtraBack = False

        preliminaryPlateDistance = max(topZs)
        for i in range(len(self.bearingPositions)):
            # check front plate
            canIgnoreFront = False
            canIgnoreBack = False
            if self.goingTrain.getArbourWithConventionalNaming(i).getType() == ArbourType.CHAIN_WHEEL:
                if self.goingTrain.chainAtBack:
                    canIgnoreBack = True
                else:
                    # this is the part of the chain wheel with a washer, can ignore
                    canIgnoreFront = True
            # topZ = self.goingTrain.getArbourWithConventionalNaming(i).getTotalThickness() + self.bearingPositions[i][2]
            if topZs[i] >= preliminaryPlateDistance - LAYER_THICK * 2 and not canIgnoreFront:
                # something that matters is pressed up against the top plate
                # could optimise to only add the minimum needed, but this feels like a really rare edgecase and will only gain at most 0.4mm
                needExtraFront = True

            if self.bearingPositions[i][2] == 0 and not canIgnoreBack:
                needExtraBack = True

        extraFront = 0
        extraBack = 0
        if needExtraFront:
            extraFront = LAYER_THICK * 2
        if needExtraBack:
            extraBack = LAYER_THICK * 2

        for i in range(len(self.bearingPositions)):
            self.bearingPositions[i][2] += extraBack

        # print(self.bearingPositions)
        self.plateDistance = max(topZs) + self.endshake + extraFront + extraBack

        if self.escapementOnFront:
            # little bodge to try and make things easier (not sure if it does)
            # the arbour for the anchor is just two arbourextensions, but one is prentending to be the main shape
            # so pretend it's placed exactly in the centre
            self.bearingPositions[-1][2] = self.plateDistance / 2 - self.endshake / 2

    def bottom_of_hour_hand_z(self):
        return self.motionWorks.getHandHolderHeight() + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motionWorks.inset_at_base

    def front_plate_has_flat_front(self):
        '''
        If there's nothing sticking out of the front plate it can be printed the other way up - better front surface and no hole-in-hole needed for bearings
        '''
        if self.pendulumAtFront and self.pendulumSticksOut > 0:
            #arm that holds the bearing (old designs)
            return False
        if self.huygensMaintainingPower:
            #ratchet is on the front
            return False
        return True

    def need_front_anchor_bearing_holder(self):
        #no longer supporting anything that doesn't (with the escapement on the front) - the large bearings have way too much friction so we have to hold the anchor arbour from both ends
        return self.escapementOnFront# and self.pendulumFixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

    def get_front_anchor_bearing_holder_total_length(self):
        '''
        full length (including bit that holds bearing) of the peice that sticks out the front of the clock to hold the bearing for a front mounted escapment
        '''
        if self.need_front_anchor_bearing_holder():
            holder_long = self.arboursForPlate[-1].front_anchor_from_plate + self.arboursForPlate[-1].arbour.escapement.getAnchorThick() \
                          + self.get_lone_anchor_bearing_holder_thick(self.arboursForPlate[-1].bearing) + WASHER_THICK_M3
        else:
            holder_long = 0
        return holder_long


    @staticmethod
    def get_lone_anchor_bearing_holder_thick(bearing = None):
        '''
        static so it can be used to adjust the thickness of the frame
        '''
        if bearing is None:
            bearing = getBearingInfo(3)
        return bearing.height + 1

    def get_front_anchor_bearing_holder(self, for_printing=True):

        holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arboursForPlate[-1].bearing)

        pillar_tall = self.get_front_anchor_bearing_holder_total_length() - holder_thick

        holder = cq.Workplane("XY").moveTo(-self.topPillarR, self.topPillarPos[1]).radiusArc((self.topPillarR, self.topPillarPos[1]), self.topPillarR)\
            .lineTo(self.topPillarR, self.bearingPositions[-1][1]).radiusArc((-self.topPillarR, self.bearingPositions[-1][1]), self.topPillarR).close().extrude(holder_thick)

        holder = holder.union(cq.Workplane("XY").moveTo(self.topPillarPos[0], self.topPillarPos[1]).circle(self.plateWidth / 2 + 0.0001).extrude(pillar_tall + holder_thick))


        holder = holder.cut(self.get_bearing_punch(holder_thick, bearing=getBearingInfo(self.arboursForPlate[-1].arbour.arbourD)).translate((self.bearingPositions[-1][0], self.bearingPositions[-1][1])))
        #rotate into position to cut fixing holes
        holder = holder.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, pillar_tall + holder_thick))
        holder= holder.cut(self.get_fixing_screws_cutter().translate((0,0,-self.front_z)))

        if for_printing:
            #rotate back
            holder = holder.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, pillar_tall + holder_thick))
            holder = holder.translate(npToSet(np.multiply(self.topPillarPos, -1)))
        else:
            holder = holder.translate((0,0, self.front_z))

        return holder


    def calc_need_motion_works_holder(self):
        '''
        If we've got a centred second hand then there's a chance that the motino works arbour lines up with another arbour, so there's no easy way to hold it in plnace
        in this case we have a separate peice that is given a long screw and itself screws onto the front of the front plate
        '''

        if self.style ==ClockPlateStyle.VERTICAL and self.goingTrain.has_seconds_hand() and self.centred_second_hand:
            #potentially

            motion_works_arbour_y = self.motionWorksPos[1]

            for i,bearing_pos in enumerate(self.bearingPositions):
                #just x,y
                bearing_pos_y = bearing_pos[1]
                bearing = getBearingInfo(self.goingTrain.getArbourWithConventionalNaming(i).arbourD)
                screw = MachineScrew(3, countersunk=True)
                if abs(bearing_pos_y - motion_works_arbour_y) < bearing.bearingOuterD/2 + screw.getHeadDiameter()/2:
                    print("motion works holder would clash with bearing holder for arbour", i)
                    return True

        return False

    def get_motion_works_holder(self):
        if not self.need_motion_works_holder:
            return None



        standoff_thick = 1
        holder_thick = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - WASHER_THICK_M3 - standoff_thick
        w = self.motion_works_holder_wide
        l = self.motion_works_holder_length
        #holder = cq.Workplane("XY").rect(self.motion_works_holder_wide, self.motion_works_holder_length).extrude(holder_thick)
        holder = cq.Workplane("XY").moveTo(w/2, l/2).radiusArc((-w/2,l/2), -w/2).line(0,-l).radiusArc((w/2, -l/2), -w/2).close().extrude(holder_thick)

        #small standoff for motion works arbour
        holder = holder.faces(">Z").workplane().circle(self.fixingScrews.metric_thread).extrude(standoff_thick)

        holder = holder.cut(self.fixingScrews.getCutter(withBridging=True,layerThick=LAYER_THICK_EXTRATHICK, for_tap_die=True))

        for pos in self.motion_works_fixings_relative_pos:
            holder = holder.cut(self.fixingScrews.getCutter().rotate((0,0,0),(0,1,0),180).translate((pos[0], pos[1], holder_thick)))

        return holder


    def getPlateThick(self, back=True, standoff=False):
        if standoff:
            #TODO separate value
            return self.plateThick
        if back:
            return self.backPlateThick
        return self.plateThick

    def getPlateDistance(self):
        '''
        how much space there is between the front and back plates
        '''
        return self.plateDistance

    def getScrewHolePositions(self):
        '''
        returns [(x,y, supported),]
        for where the holes to fix the clock to the wall will be

        This logic is a bit of a mess, it was pulled out of the tangle in clock plates and could do with tidying up
        '''
        if self.backPlateFromWall > 0:

            slotLength = 7

            # just above the pillar
            # TODO consider putting the screwhole INSIDE the pillar?
            topScrewHolePos = (self.topPillarPos[0], self.topPillarPos[1] + self.topPillarR + self.wallFixingScrewHeadD / 2 + slotLength)

            if self.bottom_pillars == 1:
                bottomScrewHolePos = (0, self.bottomPillarPositions[0][1] + self.bottomPillarR + self.wallFixingScrewHeadD / 2 + slotLength)
            else:
                bottomScrewHolePos = (0, self.bottomPillarPositions[0][1])

            if self.heavy:
                return [topScrewHolePos, bottomScrewHolePos]
            else:
                return [topScrewHolePos]


        else:
            #old messy logic

            bottomScrewHoleY = self.bearingPositions[0][1] + (self.bearingPositions[1][1] - self.bearingPositions[0][1]) * 0.6

            extraSupport = True
            if self.usingPulley and self.heavy:
                # the back plate is wide enough to accomodate
                extraSupport = False

            weightX = 0
            weightOnSide = 1 if self.weightOnRightSide else -1
            if self.heavy and not self.usingPulley:
                # line up the hole with the big heavy weight
                weightX = weightOnSide * self.goingTrain.poweredWheel.diameter / 2

            if self.style == ClockPlateStyle.ROUND:
                #screwHoleY = chainWheelR * 1.4
                raise NotImplementedError("Haven't fixed this for round clocks")

            elif self.style == ClockPlateStyle.VERTICAL:
                if self.extraHeavy:

                    # below anchor
                    topScrewHoleY = self.bearingPositions[-2][1] + (self.bearingPositions[-1][1] - self.bearingPositions[-2][1]) * 0.6
                    return [(weightX, bottomScrewHoleY, extraSupport), (weightX, topScrewHoleY, True)]
                else:
                    # just below anchor
                    screwHoleY = self.bearingPositions[-2][1] + (self.bearingPositions[-1][1] - self.bearingPositions[-2][1]) * 0.6

                    return [(weightX, screwHoleY, extraSupport)]

    def getDrillTemplate(self,drillHoleD=7):

        screwHoles = self.getScrewHolePositions()

        if len(screwHoles) <= 1:
            raise ValueError("Can't make template without at least two screwholes")
        #assumes aligned vertically
        ys = [hole[1] for hole in screwHoles]
        xs = [hole[0] for hole in screwHoles]
        maxY = max(ys)
        minY = min(ys)
        minX = min(xs)
        maxX = max(xs)

        minWidth = maxX - minX
        minHeight = maxY - minY

        print("screw hole distance", minHeight)

        border = drillHoleD*2
        thick = 2

        width = minWidth + border*2

        template = cq.Workplane("XY").moveTo(minX + minWidth/2, minY + minHeight/2).rect(width, minHeight + border*2).extrude(thick)

        for hole in screwHoles:
            template = template.faces(">Z").workplane().moveTo(hole[0], hole[1]).circle(drillHoleD/2).cutThruAll()
        print(self.name, width*0.5)
        # text = cq.Workplane("XY").text(txt=self.name, fontsize=int(minWidth*0.5), distance=LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotate((0,0,0), (0,0,1),90).translate((0,0,thick))
        text = cq.Workplane("XY").text("Wall 12", fontsize=width*0.5, distance=LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotate((0, 0, 0), (0, 0, 1), 90).translate(((minX + maxX)/2, (minY + maxY)/2, thick))
        template = template.add(text)

        return template

    def calc_pillar_info(self):
        '''
        Calculate (and set) topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide, reduce_bottom_pillar_height
        '''


        bearingInfo = getBearingInfo(self.arbourD)
        # width of thin bit
        self.plateWidth = bearingInfo.bearingOuterD + self.bearingWallThick * 2
        self.minPlateWidth = self.plateWidth
        if self.heavy or self.extraHeavy:
            self.plateWidth *= 1.2

        # original thinking was to make it the equivilant of a 45deg shelf bracket, but this is massive once cord wheels are used
        # so instead, make it just big enough to contain the holes for the chains/cord

        furthestX = max([abs(holePos[0][0]) for holePos in self.goingTrain.poweredWheel.getChainPositionsFromTop()])

        # juuust wide enough for the small bits on the edge of the bottom pillar to print cleanly
        minDistanceForChainHoles = (furthestX * 2 + self.chainHoleD + 5) / 2


        self.bottomPillarR = self.plateDistance / 2

        if self.bottomPillarR < self.plateWidth/2:
            #rare, but can happen
            self.bottomPillarR = self.plateWidth/2

        self.reduce_bottom_pillar_height = 0
        if self.bottomPillarR < minDistanceForChainHoles and self.chainThroughPillar:
            if self.allow_bottom_pillar_height_reduction:
                self.reduce_bottom_pillar_height = minDistanceForChainHoles - self.bottomPillarR
            self.bottomPillarR = minDistanceForChainHoles


        self.topPillarR = self.plateWidth / 2

        anchorSpace = bearingInfo.bearingOuterD / 2 + self.gearGap
        if self.pendulumFixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS:
            anchorSpace = self.direct_arbour_d*2 + self.gearGap

        # find the Y position of the bottom of the top pillar
        topY = self.bearingPositions[0][1]
        if self.style == ClockPlateStyle.ROUND:
            # find the highest point on the going train
            # TODO for potentially large gears this might be lower if they're spaced right
            for i in range(len(self.bearingPositions) - 1):
                y = self.bearingPositions[i][1] + self.goingTrain.getArbourWithConventionalNaming(i).getMaxRadius() + self.gearGap
                if y > topY:
                    topY = y
        else:

            topY = self.bearingPositions[-1][1] + max(self.arboursForPlate[-1].get_max_radius(), bearingInfo.bearingOuterD / 2) + self.gearGap

        if self.bottom_pillars > 1:
            #TODO optimal placement of pillars, for now let's just get them working
            # #take into account the chain wheel might not be directly below the minute wheel
            # from_lowest_wheel = self.arboursForPlate[0].arbour.getMaxRadius() + self.bottomPillarR + self.gearGap
            # from_next_wheel = self.arboursForPlate[1].arbour.getMaxRadius() + self.bottomPillarR + self.gearGap
            # between_wheels = np.linalg.norm(np.subtract(self.bearingPositions[0][:2], self.bearingPositions[1][:2]))
            chain_wheel_r = self.arboursForPlate[0].arbour.getMaxRadius() + self.gearGap
            self.bottomPillarPositions=[
                (self.bearingPositions[0][0] - (chain_wheel_r + self.bottomPillarR), self.bearingPositions[0][1]),
                (self.bearingPositions[0][0] + (chain_wheel_r + self.bottomPillarR), self.bearingPositions[0][1]),
            ]
        else:
            self.bottomPillarPositions = [[self.bearingPositions[0][0], self.bearingPositions[0][1] - self.chainWheelR - self.bottomPillarR + self.reduce_bottom_pillar_height]]
        self.topPillarPos = [self.bearingPositions[0][0], topY + self.topPillarR]

        if self.bottom_pillars > 1 and self.huygensMaintainingPower:
            raise ValueError("Don't currently support huygens with multiple bottom pillars")
        self.huygensWheelPos = self.bottomPillarPositions[0]


    def cut_anchor_bearing_in_standoff(self, standoff):
        bearingInfo = getBearingInfo(self.goingTrain.getArbourWithConventionalNaming(-1).getRodD())


        standoff = standoff.cut(self.getBearingPunchDeprecated(bearingOnTop=True, standoff=True, bearingInfo=bearingInfo).translate((0, self.bearingPositions[-1][1], 0)))

        return standoff

    def getWallStandoff(self, top=True, forPrinting=True):
        '''
        If the back plate isn't directly up against the wall, we need two more peices that attach to the top and bottom pillars on the back
        if the pendulum is at the back (likely given there's not much other reason to not be against the wall) the bottom peice will need
        a large gap or the hand-avoider

        this is in position with the xy plate at the TOP of the standoff

        I had considered linking the top and bottom standoffs together with another plate for strength, but an eight day clock (clock 12) has demonstrated that they're
        fine as two independant little pillars

        In the case of a suspension spring the top pillar standoff is only the bit that holds the bearing for the anchor arbor. There is (will be) a separate
        peice behind that to hold the suspension spring. This is because it's the same piece as the older standoff, just with a different length.
        SECOND THOUGHTS - could I just have a big round hole in the back plate and have the crutch extend through that?

        '''

        pillarPositions = [self.topPillarPos] if top else self.bottomPillarPositions
        pillarR = self.topPillarR if top else self.bottomPillarR

        pillarWallThick = 2
        pillarInnerR = pillarR-pillarWallThick

        standoff = cq.Workplane("XY").tag("base")

        back_thick = self.getPlateThick(standoff=True)
        screwhole_back_thick = back_thick - 2
        if top:
            #assuming 1 pillar fow now


            standoff = standoff.add(self.get_pillar(top=top, flat=True).extrude(self.backPlateFromWall).translate(pillarPositions[0]))
        else:
            if self.bottom_pillars > 1:
                # make back thinner, not needed for strength so much as stability
                back_thick = 4
                screwhole_back_thick = back_thick
                for pillarPos in pillarPositions:
                    standoff = standoff.union(cq.Workplane("XY").moveTo(pillarPos[0], pillarPos[1]).circle(pillarR).extrude(self.backPlateFromWall))
                standoff = standoff.union(get_stroke_line(pillarPositions, wide=pillarR, thick=back_thick))


            else:
                #round works fine, no need to copy the heavy duty lower pillar
                standoff = standoff.moveTo(pillarPositions[0][0], pillarPositions[0][1]).circle(pillarR).extrude( self.backPlateFromWall)


        if top or self.heavy or True:

            #screwholes to hang on wall
            #originally only at the top, but now I think put them everywhere
            # #TODO consider putting the screwhole INSIDE the pillar?

            if top:
                screwHolePos = self.getScrewHolePositions()[0]
            else:
                #bottom pillar, heavy
                screwHolePos = self.getScrewHolePositions()[1]

            screwHoleSupportR = self.topPillarR  # (self.wallFixingScrewHeadD + 6)/2

            addExtraSupport = False

            #extend a back plate out to the screwhole
            if len(pillarPositions) == 1:
                screwhole_support_start = pillarPositions[0]
                standoff = standoff.union(get_stroke_line([screwhole_support_start, screwHolePos], wide=self.plateWidth, thick=back_thick))
            else:
                #we have two pillars and the screwhole is in the link between them
                addExtraSupport = True

            #can't decide if to add backThick or not - it recesses the screw which looks nice in some situations but not convinced for teh standoff
            standoff = self.addScrewHole(standoff, screwHolePos, screwHeadD=self.wallFixingScrewHeadD, addExtraSupport=addExtraSupport, plate_thick=back_thick)#, backThick=screwhole_back_thick)

            if self.pendulumFixing in [PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING] and top:
                # extend a back plate out to the bearing holder and wall fixing

                bearingHolder = cq.Workplane("XY").tag("base").moveTo((screwHolePos[0] + self.topPillarPos[0]) / 2, (self.bearingPositions[-1][1] + self.topPillarPos[1]) / 2). \
                    rect(self.topPillarR * 2, self.topPillarPos[1] - self.bearingPositions[-1][1]).extrude(self.rear_standoff_bearing_holder_thick)
                bearingHolder = bearingHolder.workplaneFromTagged("base").moveTo(self.bearingPositions[-1][0], self.bearingPositions[-1][1]).circle(screwHoleSupportR).extrude(self.rear_standoff_bearing_holder_thick)
                bearingHolder = self.cut_anchor_bearing_in_standoff(bearingHolder)

                z = 0
                if self.pendulumFixing == PendulumFixing.SUSPENSION_SPRING:
                    #TODO
                    z = self.backPlateFromWall - self.crutch_space - self.rear_standoff_bearing_holder_thick - self.endshake
                standoff = standoff.union(bearingHolder.translate((0,0,z)))

        #we're currently not in the right z position
        standoff = standoff.cut(self.get_fixing_screws_cutter().translate((0,0,self.backPlateFromWall)))

        if forPrinting:
            if not top:
                standoff = standoff.rotate((0,0,0), (1,0,0), 180)
            standoff = standoff.translate((-pillarPos[0], -pillarPos[1]))
        else:
            standoff = standoff.translate((0,0,-self.backPlateFromWall))

        return standoff


    def getPlate(self, back=True, getText=False, for_printing=True):
        '''
        Two plates that are almost idential, with pillars at the very top and bottom to hold them together.
        Designed to be flat up against the wall, with everything offset to avoid the wall and picture rail

        styles: round or vertical
        round minimises total height by placing the gear train in a circle, so more complicated clocks can still fit on the print bed
        vertical just has everything directly above each other.

        The screwhole is placed directly above the weight to make the clock easier to hang straight

        '''
        topPillarPos, topPillarR, bottomPillarR, holderWide = (self.topPillarPos, self.topPillarR, self.bottomPillarR, self.plateWidth)

        thick = self.getPlateThick(back)

        #the bulk material that holds the bearings
        plate = cq.Workplane("XY").tag("base")
        if self.style==ClockPlateStyle.ROUND:
            radius = self.compactRadius + holderWide / 2
            #the ring that holds the gears
            plate = plate.moveTo(self.bearingPositions[0][0], self.bearingPositions[0][1] + self.compactRadius).circle(radius).circle(radius - holderWide).extrude(thick)
        elif self.style in [ClockPlateStyle.VERTICAL, ClockPlateStyle.COMPACT ]:
            #rectangle that just spans from the top bearing to the bottom pillar (so we can vary the width of the bottom section later)
            plate = plate.moveTo((self.bearingPositions[0][0]+self.bearingPositions[-1][0])/2, (self.bearingPositions[0][1]+self.bearingPositions[-1][1])/2).rect(holderWide,abs(self.bearingPositions[-1][1] - self.bearingPositions[0][1])).extrude(self.getPlateThick(back))

        if self.style == ClockPlateStyle.COMPACT:
            '''
            need some extra bits to hold the bearings that are off to one side
            '''
            #second wheel will be off to one side
            # side_shoots = 1 if self.goingTrain.wheels < 4 else 2
            # for i in range(side_shoots):
            #
            #     points = [self.bearingPositions[self.goingTrain.chainWheels+i*2],self.bearingPositions[self.goingTrain.chainWheels+1+i*2], self.bearingPositions[self.goingTrain.chainWheels+2+i*2]]
            #     points = [(x,y) for x,y,z in points]
            #     plate = plate.union(get_stroke_line(points,self.minPlateWidth, self.getPlateThick(back=back)))
            points = []
            if self.extraHeavy:
                #this looks okay but I think it's probably overkill
                if self.goingTrain.wheels == 4:
                    points = [self.bearingPositions[self.goingTrain.chainWheels], self.bearingPositions[self.goingTrain.chainWheels + 1 ], self.bearingPositions[self.goingTrain.chainWheels + 3], self.bearingPositions[self.goingTrain.chainWheels + 4 ]]
                else:
                    points = [self.bearingPositions[self.goingTrain.chainWheels], self.bearingPositions[self.goingTrain.chainWheels + 1], self.bearingPositions[self.goingTrain.chainWheels + 2]]
                points = [(x, y) for x, y, z in points]
                plate = plate.union(get_stroke_line(points, self.minPlateWidth, thick))
            else:
                #just stick a tiny arm out the side for each bearing
                arm_from_bearing = [0]
                if self.goingTrain.wheels == 4:
                    arm_from_bearing=[0,2]
                for i in arm_from_bearing:
                    bearing_pos = self.bearingPositions[self.goingTrain.chainWheels+1+i]
                    points = [(0, bearing_pos[1]), (bearing_pos[0], bearing_pos[1])]
                    plate = plate.union(get_stroke_line(points, self.minPlateWidth, thick))


        plate = plate.tag("top")

        bottom_pillar_joins_plate_pos = self.bearingPositions[0][:2]

        screwHolePositions = self.getScrewHolePositions()

        bottomScrewHoleY = min([hole[1] for hole in screwHolePositions])

        if self.heavy and self.usingPulley and back and self.backPlateFromWall == 0:
            #instead of an extra circle around the screwhole, make the plate wider extend all the way up
            #because the screwhole will be central when heavy and using a pulley
            #don't do this if we're offset from the wall
            bottom_pillar_joins_plate_pos = (0, bottomScrewHoleY)

        #supports all the combinations of round/vertical and chainwheels or not
        bottom_pillar_link_has_rounded_top = self.style in [ClockPlateStyle.VERTICAL, ClockPlateStyle.COMPACT]
        narrow = self.goingTrain.chainWheels == 0
        bottomBitWide = holderWide if narrow else bottomPillarR*2

        #link the bottom pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(bottom_pillar_joins_plate_pos[0] - bottomBitWide/2, bottom_pillar_joins_plate_pos[1])

        # if bottom_pillar_link_has_rounded_top:
        #     plate = plate.union(cq.Workplane("XY").moveTo(bottom_pillar_joins_plate_pos[0], bottom_pillar_joins_plate_pos[1]).circle(bottomBitWide/2).extrude(thick))

        for bottomPillarPos in self.bottomPillarPositions:
            #just square, will pop a round bit on after
            # plate = plate.lineTo(bottomPillarPos[0] + bottomBitWide/2, bottomPillarPos[1]).line(-bottomBitWide,0)
            #
            # plate = plate.close().extrude(self.getPlateThick(back))
            #
            # plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR).extrude(self.getPlateThick(back))
            plate = plate.union(get_stroke_line([bottomPillarPos, bottom_pillar_joins_plate_pos], wide=bottomBitWide, thick = thick))




        if self.style == ClockPlateStyle.ROUND:
            #centre of the top of the ring
            topOfPlate = (self.bearingPositions[0][0], self.bearingPositions[0][1] + self.compactRadius * 2)
        else:
            #topmost bearing
            topOfPlate = self.bearingPositions[-1]

        # link the top pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - topPillarR, topOfPlate[1]) \
            .lineTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR) \
            .lineTo(topOfPlate[0] + topPillarR, topOfPlate[1]).close().extrude(self.getPlateThick(back))


        plate = plate.tag("top")
        # #for the screwhole
        # screwHeadD = 9
        # screwBodyD = 6
        # slotLength = 7

        if back:
            #the hole for holding the clock to the wall - can inset the head of the screw if the plate is thick enough
            screwHolebackThick = max(self.getPlateThick(back)-5, 4)


            if self.backPlateFromWall == 0:
                for screwPos in screwHolePositions:
                    plate = self.addScrewHole(plate, (screwPos[0], screwPos[1]), backThick=screwHolebackThick, screwHeadD=self.wallFixingScrewHeadD, addExtraSupport=screwPos[2])

            #the pillars
            if not self.pillars_separate:
                for bottomPillarPos in self.bottomPillarPositions:
                    plate = plate.union(self.get_bottom_pillar().translate(bottomPillarPos).translate((0, 0, thick)))
                plate = plate.union(self.get_top_pillar().translate(self.topPillarPos).translate((0, 0, thick)))





            textMultiMaterial = cq.Workplane("XY")
            textSize = topPillarR * 0.9
            textY = (self.bearingPositions[0][1] + self.plate_fixings[2][1]) / 2
            if self.goingTrain.escapement.type == EscapementType.GRASSHOPPER:
                #TODO check all the gaps and choose the largest, so we don't have to care about which escapemetn it is?
                textY = (self.bearingPositions[-1][1] + self.bearingPositions[-2][1])/2
            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{} {:.1f}".format(self.name, self.goingTrain.pendulum_length * 100), (-textSize*0.4, textY), textSize)

            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{}".format(datetime.date.today().strftime('%Y-%m-%d')), (textSize*0.6, textY), textSize)
            #in case they overlapped with a bearing hole - crude fix rather than locating the text better
            textMultiMaterial = self.punchBearingHoles(textMultiMaterial, back=back)
            if getText:
                return textMultiMaterial

        plate = self.punchBearingHoles(plate, back)


        if not back:
            #front
            plate = self.frontAdditionsToPlate(plate)
            if self.extraFrontPlate:
                # plate = plate.add(cq.Workplane("XY").moveTo(self.extraFrontPlateMountingPos[0], self.extraFrontPlateMountingPos[1]).circle(self.plateWidth/2).extrude(self.extraFrontPlateDistance).translate((0,0,self.getPlateThick(back=False))))
                # self.extraFrontPlateMountingPos
                for pos in self.extraFrontPlateFixings:
                    plate = plate.cut(self.fixingScrews.getCutter(withBridging=True).translate(pos))


        #screws to fix the plates together, with embedded nuts in the pillars
        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())
        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0,0, -self.getPlateThick(back=True) - self.plateDistance)))


        if for_printing and not back and self.front_plate_has_flat_front():
            '''
            front plate is generated front-up, but we can flip it for printing
            '''
            plate = plate.rotate((0,0,0), (0,1,0),180).translate((0,0,self.getPlateThick(back=False)))


        return plate

    def get_fixing_screws_cutter(self):
        '''
        in position, assuming back of back plate is resting on the XY plane

        Previously used two sets of screws: one to attach the front plate and one to attach the rear standoffs, both with embedded nuts.
        Now assumes you've got screws long enough to attach everything. This should make it stronger
        especially as the pillars are now separate and the new suspension spring will result in two bits of standoff
        '''



        if self.fixing_screws_cutter is not None:
            #fetch from cache if possible
            return self.fixing_screws_cutter

        bottom_total_length = self.backPlateFromWall + self.getPlateThick(back=True) + self.plateDistance + self.getPlateThick(back=False)
        top_total_length = bottom_total_length + self.get_front_anchor_bearing_holder_total_length()

        top_screw_length = top_total_length - (top_total_length%10)
        bottom_screw_length = bottom_total_length - (bottom_total_length % 10)

        #top and bottom screws are different lengths if there is a front-mounted escapement

        print("Total length of front to back of clock is {}mm at top and {}mm at bottom. Assuming top screw length of {}mm and bottom screw length of {}mm".format(top_total_length, bottom_total_length, top_screw_length, bottom_screw_length))
        if top_screw_length > 60 and self.fixingScrews.metric_thread < 4:
            raise ValueError("WARNING may not be able to source screws long enough, try M4")
        cutter = cq.Workplane("XY")

        rear_nut_base_z = -self.backPlateFromWall
        top_nut_hole_height = self.fixingScrews.getNutHeight()
        bottom_nut_hole_height = top_nut_hole_height

        if self.backPlateFromWall > 0:
            #extra nut height just in case
            top_nut_hole_height = (top_total_length%10) + self.fixingScrews.getNutHeight()
            bottom_nut_hole_height = (bottom_total_length%10) + self.fixingScrews.getNutHeight()
        else:
            # unlikely I'll be printing any wall clocks without this standoff until I get to striking longcase-style clocks
            print("you may have to cut the fixing screws to length in the case of no back standoff")

        for fixingPos in self.plate_fixings:


            z = self.front_z
            if fixingPos in self.plate_top_fixings and self.need_front_anchor_bearing_holder():
                z += self.get_front_anchor_bearing_holder_total_length()
                cutter = cutter.union(self.fixingScrews.getNutCutter(height=top_nut_hole_height, withBridging=True).translate(fixingPos).translate((0, 0, rear_nut_base_z)))
            else:
                cutter = cutter.union(self.fixingScrews.getNutCutter(height=bottom_nut_hole_height, withBridging=True).translate(fixingPos).translate((0, 0, rear_nut_base_z)))
            # holes for the screws
            cutter = cutter.add(self.fixingScrews.getCutter(loose=True).rotate((0, 0, 0), (1, 0, 0), 180).translate(fixingPos).translate((0, 0, z)))




        if self.huygensMaintainingPower:
            #screw to hold the ratchetted chainwheel

            #hold a nyloc nut
            nyloc = True
            bridging = False
            base_z = 0
            nutZ = self.getPlateThick(back=True) + self.plateDistance - self.fixingScrews.getNutHeight(nyloc=True)

            if self.huygens_wheel_y_offset > self.bottomPillarR - self.fixingScrews.getNutContainingDiameter()/2:
                #nut is in the back of the front plate rather than the top of the bottom pillar, but don't make it as deep as we need the strength
                #making it normal nut deep but will probably still use nyloc
                # nutZ = self.getPlateThick(back=True) + self.plateDistance - (self.fixingScrews.getNutHeight(nyloc=True) - self.fixingScrews.getNutHeight(nyloc=False))

                if self.huygens_wheel_y_offset > self.bottomPillarR:
                    #just the front plate
                    bridging = True
                    base_z = self.getPlateThick(back=True) + self.plateDistance
                    nutZ = self.getPlateThick(back=True) + self.plateDistance - (self.fixingScrews.getNutHeight(nyloc=True) - self.fixingScrews.getNutHeight(nyloc=False))

            cutter = cutter.add(cq.Workplane("XY").moveTo(self.huygensWheelPos[0], self.huygensWheelPos[1] + self.huygens_wheel_y_offset).circle(self.fixingScrews.metric_thread / 2).extrude(1000).translate((0, 0, base_z)))
            cutter = cutter.add(self.fixingScrews.getNutCutter(nyloc=nyloc, withBridging=bridging).translate(self.huygensWheelPos).translate((0, self.huygens_wheel_y_offset, nutZ)))

        #cache to avoid re-calculating
        self.fixing_screws_cutter = cutter

        return cutter

    def get_bottom_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane
        '''

        #for chainholes and things which assume one pillar
        bottomPillarPos = self.bottomPillarPositions[0]
        if self.extraHeavy:
            '''
            beef up the bottom pillar
            bottomPillarR^2 + x^2 = chainWheelR^2
            x = sqrt(chainWheelR^2 - bottomPilarR^2)
            
            assumes only one bottom pillar, below the chain wheel
            '''

            pillarTopY = self.bearingPositions[0][1] - math.sqrt(self.chainWheelR ** 2 - self.bottomPillarR ** 2) - bottomPillarPos[1]

            bottom_pillar = cq.Workplane("XY").moveTo(0 - self.bottomPillarR, 0).radiusArc((0 + self.bottomPillarR, 0), -self.bottomPillarR). \
                lineTo(0 + self.bottomPillarR, pillarTopY).radiusArc((0 - self.bottomPillarR, pillarTopY), self.chainWheelR).close()

            if flat:
                return bottom_pillar

            bottom_pillar = bottom_pillar.extrude(self.plateDistance)



        else:

            bottom_pillar = cq.Workplane("XY").moveTo(0, 0).circle(self.bottomPillarR)

            if flat:
                return bottom_pillar

            bottom_pillar = bottom_pillar.extrude(self.plateDistance)

            if self.reduce_bottom_pillar_height > 0:
                #assumes one pillar
                #bottom pillar has been moved upwards a smidge, cut out a space for the chain wheel
                r = abs(self.bearingPositions[0][1] - (self.bottomPillarPositions[0][1] + self.bottomPillarR - self.reduce_bottom_pillar_height))
                bottom_pillar = bottom_pillar.cut(cq.Workplane("XY").moveTo(0, r-self.reduce_bottom_pillar_height + self.bottomPillarR).circle(r).extrude(self.plateDistance))

        if self.bottom_pillars == 1:
            chainHoles = self.get_chain_holes()
            bottom_pillar = bottom_pillar.cut(chainHoles.translate((-bottomPillarPos[0], -bottomPillarPos[1], self.endshake / 2)))

        #hack - assume screws are in the same place for both pillars for now
        bottom_pillar = bottom_pillar.cut(self.get_fixing_screws_cutter().translate((-bottomPillarPos[0], -bottomPillarPos[1], -self.getPlateThick(back=True))))
        return bottom_pillar

    def get_pillar(self, top=True, flat=False):
        if top:
            return self.get_top_pillar(flat=flat)
        else:
            return self.get_bottom_pillar(flat=flat)

    def get_top_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane

        if flat returns a 2D shape
        '''
        topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide = (self.topPillarPos, self.topPillarR, self.bottomPillarPositions, self.bottomPillarR, self.plateWidth)
        if self.extraHeavy:
            #sagitta looks nice, otherwise arbitrary at the moment, should really check it leaves enough space for the anchor
            sagitta = topPillarR * 0.25
            top_pillar = cq.Workplane("XY").moveTo(0 - topPillarR, 0).radiusArc((0 + topPillarR, 0), topPillarR)\
                .lineTo(0 + topPillarR, 0 - topPillarR - sagitta). \
                sagittaArc((0 - topPillarR, 0 - topPillarR - sagitta), -sagitta).close()#.extrude(self.plateDistance)
            if flat:
                return top_pillar

            top_pillar = top_pillar.extrude(self.plateDistance)
        else:
            top_pillar = cq.Workplane("XY").moveTo(0, 0).circle(topPillarR)
            if flat:
                return top_pillar
            top_pillar = top_pillar.extrude(self.plateDistance)

        top_pillar = top_pillar.cut(self.get_fixing_screws_cutter().translate((-topPillarPos[0], -topPillarPos[1], -self.getPlateThick(back=True))))

        return top_pillar

    def get_chain_holes(self):
        '''
        These chain holes are relative to the front of the back plate - they do NOT take plate thickness or wobble into account
        '''

        holePositions = self.goingTrain.poweredWheel.getChainPositionsFromTop()
        topZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness()

        chainHoles = cq.Workplane("XZ")

        for holePosition in holePositions:
            if len(holePosition) > 1:
                #elongated hole

                chainZTop = topZ + holePosition[0][1] + self.endshake / 2
                chainZBottom = topZ + holePosition[1][1] - self.endshake / 2
                #assuming we're only ever elongated along the z axis
                chainX = holePosition[0][0]

                # chainHole = cq.Workplane("XZ").moveTo(chainX - self.chainHoleD / 2, chainZTop - self.chainHoleD / 2).radiusArc((chainX + self.chainHoleD / 2, chainZTop - self.chainHoleD / 2), self.chainHoleD / 2) \
                #     .lineTo(chainX + self.chainHoleD / 2, chainZBottom + self.chainHoleD / 2).radiusArc((chainX - self.chainHoleD / 2, chainZBottom + self.chainHoleD / 2), self.chainHoleD / 2).close() \
                #     .extrude(1000)
                chainHole = cq.Workplane("XZ").moveTo(chainX, (chainZTop + chainZBottom)/2).rect(self.chainHoleD, abs(chainZTop - chainZBottom) ).extrude(1000)
                chainHoles.add(chainHole)
            else:
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + topZ).circle(self.chainHoleD / 2).extrude(1000)
                chainHoles.add(chainHole)

        if self.usingPulley and self.goingTrain.poweredWheel.type == PowerType.CORD:
            #hole for cord to be tied in

            chainX = holePositions[0][0][0]
            chainZTop = topZ + holePositions[0][0][1]
            pulleyX = -chainX
            # might want it as far back as possible?
            # for now, as far FORWARDS as possible, because the 4kg weight is really wide!
            pulleyZ = chainZTop - self.chainHoleD / 2  # chainZBottom + self.chainHoleD/2#(chainZTop + chainZBottom)/2
            if self.backPlateFromWall > 0:
                #centre it instead
                pulleyZ = topZ + (holePositions[0][0][1] + holePositions[0][1][1])/2
            # and one hole for the cord to be tied
            pulleyHole = cq.Workplane("XZ").moveTo(pulleyX, pulleyZ).circle(self.chainHoleD / 2).extrude(1000)
            chainHoles.add(pulleyHole)
            # print("chainZ min:", chainZBottom, "chainZ max:", chainZTop)

            # original plan was a screw in from the side, but I think this won't be particularly strong as it's in line with the layers
            # so instead, put a screw in from the front
            pulleyY = self.bottomPillarPositions[1] + self.bottomPillarR / 2
            if self.extraHeavy:
                #bring it nearer the top, making it easier to tie the cord around it
                pulleyY = self.bottomPillarPositions[1] + self.bottomPillarR - self.fixingScrews.metric_thread
            # this screw will provide something for the cord to be tied round
            pulleyScrewHole = self.fixingScrews.getCutter().rotate((0,0,0),(1,0,0),180).translate((pulleyX,pulleyY,self.plateDistance))

            #but it's fiddly so give it a hole and protect the screw
            max_extra_space = self.bottomPillarR - pulleyX - 1
            extra_space = cq.Workplane("XY").circle(max_extra_space).extrude(self.chainHoleD).translate((pulleyX,pulleyY,pulleyZ-self.chainHoleD/2))
            #make the space open to the top of the pillar
            extra_space = extra_space.union(cq.Workplane("XY").rect(max_extra_space*2, 1000).extrude(self.chainHoleD).translate((pulleyX,pulleyY + 500,pulleyZ-self.chainHoleD/2)))
            #and keep it printable
            extra_space = extra_space.union(getHoleWithHole(innerD=self.fixingScrews.metric_thread, outerD=max_extra_space*2, deep=self.chainHoleD,  layerThick=LAYER_THICK_EXTRATHICK)
                                            .rotate((0,0,0),(0,0,1),90).translate((pulleyX, pulleyY, pulleyZ-self.chainHoleD/2)))

            #I'm worried about the threads cutting the thinner cord, but there's not quite enough space to add a printed bit around the screw
            # I could instead file off the threads for this bit of the screw?

            chainHoles.add(extra_space)


            chainHoles.add(pulleyScrewHole)
        return chainHoles

    def getBearingHolder(self, height, addSupport=True, bearingInfo=None):
        #height from base (outside) of plate, so this is inclusive of base thickness, not in addition to
        if bearingInfo is None:
            bearingInfo = getBearingInfo(self.arbourD)
        wallThick = self.bearingWallThick
        # diameter = bearingInfo.bearingOuterD + wallThick*2
        outerR = bearingInfo.bearingOuterD/2 + wallThick
        innerInnerR = bearingInfo.outerSafeD/2
        innerR = bearingInfo.bearingOuterD/2
        holder = cq.Workplane("XY").circle(outerR).extrude(height)

        # holder = holder.faces(">Z").workplane().circle(diameter/2).circle(bearingInfo.bearingOuterD/2).extrude(bearingInfo.bearingHeight)
        # extra support?
        if addSupport:
            support = cq.Workplane("YZ").moveTo(0,0).lineTo(-height-outerR,0).lineTo(-outerR,height).lineTo(0,height).close().extrude(wallThick).translate((-wallThick/2,0,0))
            holder = holder.add(support)
        holder = holder.cut(cq.Workplane("XY").circle(innerInnerR).extrude(height))
        holder = holder.cut(cq.Workplane("XY").circle(innerR).extrude(bearingInfo.bearingHeight).translate((0,0,height - bearingInfo.bearingHeight)))

        return holder

    def get_bearing_punch(self, plate_thick, bearing, bearing_on_top=True , with_support=False):
        '''
        General purpose bearing punch
        '''
        if bearing.height >= plate_thick:
            raise ValueError("plate not thick enough to hold bearing: {}".format(bearing))

        if bearing_on_top:
            punch = cq.Workplane("XY").circle(bearing.outerSafeD/2).extrude(plate_thick - bearing.height)
            punch = punch.faces(">Z").workplane().circle(bearing.outerD/2).extrude(bearing.height)
        else:
            if with_support:
                punch = getHoleWithHole(bearing.outerSafeD, bearing.outerD, bearing.height, layerThick=LAYER_THICK_EXTRATHICK).faces(">Z").workplane().circle(bearing.outerSafeD / 2).extrude(
                    plate_thick - bearing.height)
            else:
                #no need for hole-in-hole!
                punch = cq.Workplane("XY").circle(bearing.outerD/2).extrude(bearing.height).faces(">Z").workplane().circle(bearing.outerSafeD/2).extrude(plate_thick - bearing.height)

        return punch



    def getBearingPunchDeprecated(self, bearingOnTop=True, bearingInfo=None, back=True, standoff=False):
        '''
        A shape that can be cut out of a clock plate to hold a bearing
        TODO use get_bearing_punch instead, the logic here is hard to follow as it's grown.
        '''



        if bearingInfo is None:
            bearingInfo = getBearingInfo(self.arbourD)

        height = self.getPlateThick(back)
        if standoff:
            height = self.rear_standoff_bearing_holder_thick#self.getPlateThick(standoff=True)

        if bearingInfo.height >= height:
            raise ValueError("{} plate not thick enough to hold bearing: {}".format("Back" if back else "Front",bearingInfo.get_string()))

        if bearingOnTop:
            punch = cq.Workplane("XY").circle(bearingInfo.outerSafeD/2).extrude(height - bearingInfo.bearingHeight)
            punch = punch.faces(">Z").workplane().circle(bearingInfo.bearingOuterD/2).extrude(bearingInfo.bearingHeight)
        else:
            if not back and self.front_plate_has_flat_front():
                #no need for hole-in-hole!
                punch = cq.Workplane("XY").circle(bearingInfo.bearingOuterD/2).extrude(bearingInfo.bearingHeight).faces(">Z").workplane().circle(bearingInfo.outerSafeD/2).extrude(height - bearingInfo.bearingHeight)
            else:
                punch = getHoleWithHole(bearingInfo.outerSafeD,bearingInfo.bearingOuterD, bearingInfo.bearingHeight, layerThick=LAYER_THICK_EXTRATHICK).faces(">Z").workplane().circle(bearingInfo.outerSafeD/2).extrude(height - bearingInfo.bearingHeight)

        return punch

    def punchBearingHoles(self, plate, back):
        for i, pos in enumerate(self.bearingPositions):
            bearingInfo = getBearingInfo(self.goingTrain.getArbourWithConventionalNaming(i).getRodD())
            bearingOnTop = back

            needs_plain_hole = False
            if self.pendulumFixing in [PendulumFixing.DIRECT_ARBOUR, PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING] and i == len(self.bearingPositions)-1:
                #if true we just need a hole for the direct arbour to fit through

                if self.escapementOnFront and not back:
                    '''
                    need the bearings to be on the back of front plate and back of the back plate
                    so endshake will be between back of back plate and front of the wall standoff bearing holder
                    this way there doesn't need to be a visible bearing on the front
                    '''
                    needs_plain_hole = True

                if not self.pendulumAtFront and back:
                    needs_plain_hole = True


            outer_d =  bearingInfo.bearingOuterD
            if needs_plain_hole:
                outer_d = self.direct_arbour_d + 3

            if outer_d > self.plateWidth - self.bearingWallThick*2:
                #this is a chunkier bearing, make the plate bigger
                try:
                    plate = plate.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(outer_d / 2 + self.bearingWallThick).extrude(self.getPlateThick(back=back)))
                except:
                    print("wasn't able to make plate bigger for bearing")

            if needs_plain_hole:
                plate = plate.cut(cq.Workplane("XY").circle(outer_d/2).extrude(self.getPlateThick(back=back)).translate((pos[0], pos[1], 0)))
            else:
                plate = plate.cut(self.getBearingPunchDeprecated(bearingOnTop=bearingOnTop, bearingInfo=bearingInfo, back=back).translate((pos[0], pos[1], 0)))
        return plate

    def addScrewHole(self, plate, screwholePos, screwHeadD = 9, screwBodyD = 6, slotLength = 7, backThick = -1, addExtraSupport=False, plate_thick=-1):
        '''
        screwholePos is the position the clock will hang from
        this is an upside-down-lollypop shape

        if backThick is default, this cuts through the whole plate
        if not, backthick is the thickness of the plastic around the screw


          /-\   circle of screwBodyD diameter (centre of the circle is the screwholePos)
          |  |  screwbodyD wide
          |  |  distance between teh two circle centres is slotLength
        /     \
        |     |  circle of screwHeadD diameter
        \_____/
        '''
        if plate_thick < 0:
            plate_thick = self.getPlateThick(back=True)

        if addExtraSupport:
            #a circle around the big hole to strengthen the plate
            #assumes plate has been tagged
            #removing all the old bodges and simplifying
            # extraSupportSize = screwHeadD*1.25
            extraSupportSize = self.plateWidth/2
            supportCentre=[screwholePos[0], screwholePos[1]- slotLength]

            # if self.heavy:
            #     extraSupportSize*=1.5
            #     supportCentre[1] += slotLength / 2
            #     #bodge if the screwhole is off to one side
            #     if screwholePos[0] != 0:
            #         #this can be a bit finnickity - I think if something lines up exactly wrong with the bearing holes?
            #         supportCentre[0] += (-1 if screwholePos[0] > 0 else 1) * extraSupportSize*0.5
            #
            plate = plate.workplaneFromTagged("base").moveTo(supportCentre[0], supportCentre[1] ).circle(extraSupportSize).extrude(plate_thick)

        #big hole
        plate = plate.faces(">Z").workplane().tag("top").moveTo(screwholePos[0], screwholePos[1] - slotLength).circle(screwHeadD / 2).cutThruAll()
        #slot
        plate = plate.workplaneFromTagged("top").moveTo(screwholePos[0], screwholePos[1] - slotLength/2).rect(screwBodyD, slotLength).cutThruAll()
        # small hole
        plate = plate.workplaneFromTagged("top").moveTo(screwholePos[0], screwholePos[1]).circle(screwBodyD / 2).cutThruAll()

        if backThick > 0 and backThick < plate_thick:
            extraY = screwBodyD*0.5
            cutter = cq.Workplane("XY").moveTo(screwholePos[0], screwholePos[1] + extraY).circle(screwHeadD/2).extrude(self.getPlateThick(back=True) - backThick).translate((0,0,backThick))
            cutter = cutter.add(cq.Workplane("XY").moveTo(screwholePos[0], screwholePos[1] - slotLength / 2 + extraY/2).rect(screwHeadD, slotLength+extraY).extrude(plate_thick - backThick).translate((0, 0, backThick)))
            plate = plate.cut(cutter)

        return plate

    def addText(self,plate, multimaterial, text, pos, textSize):
        # textSize =  width*0.25
        # textYOffset = width*0.025
        y = pos[1]
        textYOffset = 0  + pos[0]# width*0.1
        text = cq.Workplane("XY").moveTo(0, 0).text(text, textSize, LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotateAboutCenter((0, 0, 1), 90).rotateAboutCenter((1, 0, 0), 180).translate((textYOffset, y, 0))

        return plate.cut(text), multimaterial.add(text)

    def frontAdditionsToPlate(self, plate):
        '''
        stuff only needed to be added to the front plate
        '''
        plateThick = self.getPlateThick(back=False)
        # FRONT

        # note - works fine with the pendulum on the same rod as teh anchor, but I'm not sure about the long term use of ball bearings for just rocking back and forth
        # suspensionBaseThick=0.5
        # suspensionPoint = self.pendulum.getSuspension(False,suspensionBaseThick ).translate((self.bearingPositions[len(self.bearingPositions)-1][0], self.bearingPositions[len(self.bearingPositions)-1][1], plateThick-suspensionBaseThick))
        #         #
        #         # plate = plate.add(suspensionPoint)
        # new plan: just put the pendulum on the same rod as the anchor, and use nyloc nuts to keep both firmly on the rod.
        # no idea if it'll work without the rod bending!

        if self.pendulumAtFront and self.pendulumSticksOut > 0 and self.pendulumFixing == PendulumFixing.FRICTION_ROD:
            #a cylinder that sticks out the front and holds a bearing on the end
            extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, False).translate((self.bearingPositions[len(self.bearingPositions) - 1][0], self.bearingPositions[len(self.bearingPositions) - 1][1], plateThick))
            plate = plate.add(extraBearingHolder)




        motionWorksPos = npToSet(np.add(self.hands_position, self.motionWorksRelativePos))

        if self.need_motion_works_holder:
            #screw would be on top of a bearing, so there's a separate peice to hold it
            for pos in self.motion_works_fixings_relative_pos:
                screw_pos = npToSet(np.add(self.motionWorksPos, pos))
                plate = plate.cut(cq.Workplane("XY").circle(self.fixingScrews.get_diameter_for_die_cutting()/2).extrude(self.getPlateThick(back=False)).translate(screw_pos))
        else:
            #hole for screw to hold motion works arbour
            plate = plate.cut(self.fixingScrews.getCutter().translate(motionWorksPos))

        #embedded nut on the front so we can tighten this screw in
        #decided against this - I think it's might make the screw wonky as there's less plate for it to be going through.
        #if it's loose, use superglue.
        # nutDeep =  self.fixingScrews.getNutHeight(half=True)
        # nutSpace = self.fixingScrews.getNutCutter(half=True).translate(motionWorksPos).translate((0,0,self.getPlateThick(back=False) - nutDeep))
        #
        # plate = plate.cut(nutSpace)

        if self.dial is not None:


            dial_fixing_positions = [npToSet(np.add(pos, self.hands_position)) for pos in self.dial.get_fixing_positions()]

            need_top_extension = max([pos[1] for pos in dial_fixing_positions]) > self.topPillarPos[1]
            # need_bottom_extension = min([pos[1] for pos in dial_fixing_positions]) < self.bottomPillarPositions[1]


            if need_top_extension:
                # off the top of teh clock
                # TODO make this more robust

                dial_support_pos = (self.hands_position[0], self.hands_position[1] + self.dial.outside_d/2- self.dial.dial_width/2)
                plate = plate.union(cq.Workplane("XY").circle(self.plateWidth / 2).extrude(plateThick).translate(dial_support_pos))
                plate = plate.union(cq.Workplane("XY").rect(self.plateWidth, dial_support_pos[1] - self.topPillarPos[1]).extrude(plateThick).translate((self.topPillarPos[0], (self.topPillarPos[1] + dial_support_pos[1]) / 2)))

            #TODO bottom extension (am I ever going to want it?)


            for pos in dial_fixing_positions:
                plate = plate.cut(self.dial.fixing_screws.getCutter(loose=True,withBridging=True).translate(pos))


        # need an extra chunky hole for the big bearing that the key slots through
        if self.goingTrain.poweredWheel.type == PowerType.CORD and self.goingTrain.poweredWheel.useKey:
            cordWheel = self.goingTrain.poweredWheel
            front_hole_d = cordWheel.bearing.outerSafeD
            self.front_plate_has_key_hole = False
            key_hole_d = self.goingTrain.poweredWheel.keyWidth+1.5
            if key_hole_d > front_hole_d and key_hole_d < cordWheel.bearing.bearingOuterD - 1:
                #make the hole just big enough to fit the key into
                print("Making the front hole just big enough for the cord key")
                self.front_plate_has_key_hole = True
                front_hole_d = key_hole_d
            # cordBearingHole = cq.Workplane("XY").circle(cordWheel.bearingOuterD/2).extrude(cordWheel.bearingHeight)
            if self.front_plate_has_flat_front():
                #can print front-side on the build plate, so the bearing holes are printed on top
                cordBearingHole = cq.Workplane("XY").circle(cordWheel.bearing.bearingOuterD/2).extrude(cordWheel.bearing.bearingHeight)
                cordBearingHole = cordBearingHole.faces(">Z").workplane().circle(front_hole_d / 2).extrude(plateThick)
            else:
                cordBearingHole = getHoleWithHole(front_hole_d, cordWheel.bearing.bearingOuterD, cordWheel.bearing.bearingHeight, layerThick=LAYER_THICK_EXTRATHICK)
                cordBearingHole = cordBearingHole.faces(">Z").workplane().circle(front_hole_d / 2).extrude(plateThick)

            plate = plate.cut(cordBearingHole.translate((self.bearingPositions[0][0], self.bearingPositions[0][1],0)))

        if self.huygensMaintainingPower:

            #designed with a washer to be put under the chain wheel to reduce friction (hopefully)


            #add an extra bit at the bottom so the chain can't easily fall off
            chainholeD = self.huygensWheel.getChainHoleD()
            holePositions = self.huygensWheel.getChainPositionsFromTop()
            relevantChainHoles = [ pair[0] for pair in holePositions ]

            minThickAroundChainHole = 2
            #make a fancy bit that sticks out the bottom with holes for the chain - this makes it hard for the chain to detatch from the wheel

            extraHeight =relevantChainHoles[0][1] + self.huygensWheel.getHeight()-self.huygensWheel.ratchet.thick  + chainholeD/2 + minThickAroundChainHole
            ratchetD = self.huygensWheel.ratchet.outsideDiameter
            # ratchet for the chainwheel on the front of the clock
            ratchet = self.huygensWheel.ratchet.getOuterWheel(extraThick=WASHER_THICK_M3)

            ratchet = ratchet.faces(">Z").workplane().circle(ratchetD/2).circle(self.huygensWheel.ratchet.toothRadius).extrude(extraHeight)

            totalHeight = extraHeight + WASHER_THICK_M3 + self.huygensWheel.ratchet.thick


            cutter = cq.Workplane("YZ").moveTo(-ratchetD/2,totalHeight).spline(includeCurrent=True,listOfXYTuple=[(ratchetD/2, totalHeight-extraHeight)], tangents=[(1,0),(1,0)])\
                .lineTo(ratchetD/2,totalHeight).close().extrude(ratchetD).translate((-ratchetD/2,0,0))
            for holePosition in holePositions:
                #chainholes are relative to the assumed height of the chainwheel, which includes a washer
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + (self.huygensWheel.getHeight() + WASHER_THICK_M3)).circle(chainholeD / 2).extrude(1000)
                cutter.add(chainHole)


            ratchet = ratchet.cut(cutter)



            plate = plate.union(ratchet.translate(self.bottomPillarPositions).translate((0, self.huygens_wheel_y_offset, self.getPlateThick(back=False))))
            if ratchetD > self.bottomPillarR:
                plate = plate.union(cq.Workplane("XY").circle(ratchetD/2).extrude(self.getPlateThick(back=False)).translate(self.bottomPillarPositions).translate((0, self.huygens_wheel_y_offset)))

        if self.escapementOnFront and not self.extraFrontPlate and False:
            #this is a bearing extended out the front. I'm no longer convinced it's needed for the grasshopper
            plate = plate.add(self.getBearingHolder(-self.goingTrain.escapement.getWheelBaseToAnchorBaseZ()).translate((self.bearingPositions[-2][0], self.bearingPositions[-2][1], self.getPlateThick(back=False))))

        return plate

    def get_diameter_for_pulley(self):

        holePositions = self.goingTrain.poweredWheel.getChainPositionsFromTop()

        if self.huygensMaintainingPower:

            chainWheelTopZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() + self.getPlateThick(back=True) + self.endshake / 2
            chainWheelChainZ = chainWheelTopZ + holePositions[0][0][1]
            huygensChainPoses = self.huygensWheel.getChainPositionsFromTop()
            #washer is under the chain wheel
            huygensChainZ = self.getPlateThick(True) + self.getPlateThick(False) + self.plateDistance + self.huygensWheel.getHeight() + WASHER_THICK_M3 + huygensChainPoses[0][0][1]

            return huygensChainZ - chainWheelChainZ
        else:
            return abs(holePositions[0][0] - holePositions[1][0])

    def getAnchorWithDirectPendulumFixing(self):
        '''
        For the direct pendulum fixing (where you can't set the beat) the anchor is heavily modified to fit the plates
        so do this here where we have all the info

        Planning to move more over to the plates to do than overload teh already messy Arbour class
        '''

        anchor = self.goingTrain.escapement.g

    def calc_winding_key_info(self):
        '''
        set front_plate_has_key_hole and key_offset_from_front_plate

        hacky side effect: will set key length on cord wheel
        '''

        if self.goingTrain.poweredWheel.type != PowerType.CORD or not self.goingTrain.poweredWheel.useKey:
            raise ValueError("No winding key on this clock!")
        cordWheel = self.goingTrain.poweredWheel
        front_hole_d = cordWheel.bearing.outerSafeD
        self.front_plate_has_key_hole = False

        key_within_front_plate = self.getPlateThick(back=False) - self.goingTrain.poweredWheel.bearing.height

        self.key_hole_d = self.goingTrain.poweredWheel.keyWidth + 1.5
        if self.key_hole_d > front_hole_d and self.key_hole_d < cordWheel.bearing.bearingOuterD - 1:
            # make the hole just big enough to fit the key into
            print("Making the front hole just big enough for the cord key")
            self.front_plate_has_key_hole = True
            #offset *into* the front plate
            self.key_offset_from_front_plate = -key_within_front_plate
        else:
            self.key_offset_from_front_plate = 1

        #hack - set key size here
        # if self.dial is not None:
        #     self.goingTrain.poweredWheel.keySquareBitHeight = self.dial_z + self.dial.thick + key_within_front_plate
        # else:
        #this works out the same as above, but I'm trying to future proof at least slightly
        #note - do this relative to the hour hand, not the dial, because there may be more space for the hour hand to avoid the second hand
        self.goingTrain.poweredWheel.keySquareBitHeight = self.bottom_of_hour_hand_z() - 4 + key_within_front_plate


    def get_winding_key(self, for_printing=True):
        key_body = None

        if self.goingTrain.poweredWheel.type == PowerType.CORD and self.goingTrain.poweredWheel.useKey:
            #height of square bit above front plate, minus one so we're not scrapign the front plate
            square_bit_inside_front_plate_length = self.getPlateThick(back=False) - self.goingTrain.poweredWheel.bearing.height

            #key can only reach the front of the front plate if not front_plate_has_key_hole
            key_hole_deep =  self.goingTrain.poweredWheel.keySquareBitHeight  - ( square_bit_inside_front_plate_length + self.key_offset_from_front_plate) - self.endshake
            if self.dial is not None and self.centred_second_hand:
                # just so it doesn't clip the dial (the key is outside the dial)
                cylinder_length = self.dial_z + self.dial.thick + 6 - self.key_offset_from_front_plate
                # reach to the centre of the dial (just miss the hands)
                handle_length = self.hands_position[1] - (self.dial.outside_d / 2 - self.dial.dial_width / 2) - self.bearingPositions[0][1] - 5
            else:
                # above the hands (the key is inside the dial)
                cylinder_length = self.top_of_hands_z + 6 - self.key_offset_from_front_plate
                # avoid the centre of the hands
                handle_length = self.hands_position[1] - self.bearingPositions[0][1] - 10

            # print the key, with the right dimensions
            key_body = self.goingTrain.poweredWheel.getWindingKey(cylinder_length=cylinder_length, handle_length=handle_length, key_hole_deep = key_hole_deep, for_printing=for_printing)



        return key_body

    def outputSTLs(self, name="clock", path="../out"):

        if self.dial is not None:
            self.dial.outputSTLs(name, path)

        out = os.path.join(path, "{}_front_plate.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(False), out)

        out = os.path.join(path, "{}_back_plate_platecolour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True), out)

        out = os.path.join(path, "{}_back_plate_textcolour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True, True), out)

        if self.pillars_separate:
            out = os.path.join(path, "{}_bottom_pillar.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_bottom_pillar(), out)

            out = os.path.join(path, "{}_top_pillar.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_top_pillar(), out)


        if len(self.getScrewHolePositions()) > 1:
            #need a template to help drill the screwholes!
            out = os.path.join(path, "{}_drill_template_6mm.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getDrillTemplate(6), out)

        if self.backPlateFromWall > 0:
            # out = os.path.join(path, "{}_wall_standoff.stl".format(name))
            # print("Outputting ", out)
            # exporters.export(self.getCombinedWallStandOff(), out)

            out = os.path.join(path, "{}_wall_top_standoff.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getWallStandoff(top=True), out)

            out = os.path.join(path, "{}_wall_bottom_standoff.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getWallStandoff(top=False), out)

        if self.extraFrontPlate:
            out = os.path.join(path, "{}_extra_front_plate.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getExtraFrontPlate(), out)

        if self.huygensMaintainingPower:
            self.huygensWheel.outputSTLs(name+"_huygens", path)

        for i,arbourForPlate in enumerate(self.arboursForPlate):
            shapes = arbourForPlate.get_shapes()
            for shapeName in shapes.keys():
                out = os.path.join(path, "{}_arbour_{}_{}.stl".format(name, i, shapeName))
                print("Outputting ", out)
                if shapes[shapeName] is not None:
                    exporters.export(shapes[shapeName], out)
                else:
                    print("WARNING {} is None".format(shapeName))

        if self.need_motion_works_holder:
            out = os.path.join(path, "{}_motion_works_holder.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_motion_works_holder(), out)

        key_body = self.get_winding_key()
        if key_body is not None:
            out = os.path.join(path, "{}_winding_key_body.stl".format(name))
            print("Outputting ", out)
            exporters.export(key_body, out)

            out = os.path.join(path, "{}_winding_key_knob.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.goingTrain.poweredWheel.getWindingKnob(), out)

        if self.need_front_anchor_bearing_holder():
            out = os.path.join(path, "{}_front_anchor_bearing_holder.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_front_anchor_bearing_holder(), out)

        # for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels + 1):
        #     for top in [True, False]:
        #         extensionShape=self.getArbourExtension(arbour, top=top)
        #         if extensionShape is not None:
        #             out = os.path.join(path, "{}_arbour_{}_{}_extension.stl".format(name, arbour, "top" if top else "bottom"))
        #             print("Outputting ", out)
        #             exporters.export(extensionShape, out)



class Assembly:
    '''
    Produce a fully (or near fully) assembled clock
    likely to be fragile as it will need to delve into the detail of basically everything

    currently assumes pendulum and chain wheels are at front - doesn't listen to their values
    '''
    def __init__(self, plates, hands=None, timeMins=10, timeHours=10, timeSeconds=0, pulley=None, weights=None):
        self.plates = plates
        self.hands = hands
        self.dial= plates.dial
        self.goingTrain = plates.goingTrain
        #+1 for the anchor
        self.arbourCount = self.goingTrain.chainWheels + self.goingTrain.wheels + 1
        self.pendulum = self.plates.pendulum
        self.motionWorks = self.plates.motionWorks
        self.timeMins = timeMins
        self.timeHours = timeHours
        self.timeSeconds = timeSeconds
        self.pulley=pulley
        #weights is a list of weights, first in the list is the main weight and second is the counterweight (if needed)
        self.weights=weights
        if self.weights is None:
            self.weights = []

    def printInfo(self):

        for holeInfo in self.goingTrain.poweredWheel.getChainPositionsFromTop():
            #TODO improve this a bit for cordwheels which have a slot rather than just a hole
            z = self.plates.bearingPositions[0][2] + self.plates.getPlateThick(back=True) + self.goingTrain.poweredWheel.getHeight() + self.plates.endshake/2 + holeInfo[0][1]
            print("{} hole from wall = {}mm".format(self.goingTrain.poweredWheel.type.value, z))

    def get_arbour_rod_lengths(self):
        '''
        Calculate the lengths to cut the steel rods - stop me just guessing wrong all the time!
        '''

        total_plate_thick = self.plates.plateDistance + self.plates.getPlateThick(True) + self.plates.getPlateThick(False)
        plate_distance =self.plates.plateDistance
        front_plate_thick = self.plates.getPlateThick(back=False)
        back_plate_thick = self.plates.getPlateThick(back=True)

        #how much extra to extend out the bearing
        spare_rod_length_behind_bearing=3
        #extra length out the front of hands, or front-mounted escapements
        spare_rod_length_in_front=2
        rod_lengths = []
        rod_zs = []
        #for measuring where to put the arbour on the rod, how much empty rod should behind the back of the arbour?
        beyond_back_of_arbours = []

        for i in range(self.arbourCount):

            rod_length = -1

            arbourForPlate = self.plates.arboursForPlate[i]
            arbour = arbourForPlate.arbour
            bearing = getBearingInfo(arbour.arbourD)
            bearing_thick = bearing.bearingHeight

            length_up_to_inside_front_plate = spare_rod_length_behind_bearing + bearing_thick + plate_distance

            beyond_back_of_arbour = spare_rod_length_behind_bearing + bearing_thick + self.plates.endshake
            #true for nearly all of it
            rod_z = back_plate_thick - (bearing_thick + spare_rod_length_behind_bearing)

            #trying to arrange all the additions from back to front to make it easy to check
            if arbour.type == ArbourType.CHAIN_WHEEL:
                powered_wheel = arbour.poweredWheel
                if powered_wheel.type == PowerType.CORD:
                    if powered_wheel.useKey:
                        square_bit_out_front = powered_wheel.keySquareBitHeight - (front_plate_thick - powered_wheel.bearing.bearingHeight) - self.plates.endshake/2
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + square_bit_out_front



                else:
                    raise ValueError("TODO calculate rod lengths for powered wheel type: {}".format(arbour.type.value))
            elif arbour.type == ArbourType.WHEEL_AND_PINION:
                if i == self.goingTrain.chainWheels:
                    #minute wheel
                    if self.plates.centred_second_hand:
                        #only goes up to the canon pinion with hand turner
                        minimum_rod_length = length_up_to_inside_front_plate + front_plate_thick + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT + self.plates.motionWorks.getCannonPinionPinionThick() + WASHER_THICK_M3 + getNutHeight(arbour.arbourD, halfHeight=True) * 2
                        if self.plates.dial is not None:
                            #small as possible as it might need to fit behind the dial
                            rod_length = minimum_rod_length + 1.5
                        else:
                            rod_length = minimum_rod_length + spare_rod_length_in_front
                    else:
                        raise ValueError("TODO calculate rod lengths for normal hand holder")
                else:
                    # "normal" arbour
                    rod_length = length_up_to_inside_front_plate + bearing_thick + spare_rod_length_behind_bearing
            elif arbour.type == ArbourType.ESCAPE_WHEEL:
                if self.plates.escapementOnFront:
                    raise ValueError("TODO calculate rod lengths for escapement on front")
                elif self.plates.centred_second_hand:
                    #safe to assume mutually exclusive with escapement on front?
                    rod_length = length_up_to_inside_front_plate + front_plate_thick + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT + self.plates.motionWorks.get_cannon_pinion_effective_height() + self.hands.secondFixing_thick + self.hands.secondThick + getNutHeight(arbour.arbourD) * 2 + spare_rod_length_in_front
                elif self.goingTrain.has_seconds_hand():
                    #little seconds hand
                    rod_length = length_up_to_inside_front_plate + front_plate_thick + self.hands.secondFixing_thick + self.hands.secondThick
                else:
                    #"normal" arbour
                    rod_length = length_up_to_inside_front_plate + bearing_thick + spare_rod_length_behind_bearing
            elif arbour.type == ArbourType.ANCHOR:
                if self.plates.escapementOnFront:
                    raise ValueError("TODO calculate rod lengths for escapement on front")
                elif self.plates.backPlateFromWall > 0 and not self.plates.pendulumAtFront:
                    rod_length = spare_rod_length_behind_bearing + bearing_thick + (self.plates.backPlateFromWall - self.plates.getPlateThick(standoff=True)) + self.plates.getPlateThick(back=True) + plate_distance + bearing_thick + spare_rod_length_behind_bearing
                    rod_z = -self.plates.backPlateFromWall + (self.plates.getPlateThick(standoff=True) - bearing_thick - spare_rod_length_behind_bearing)

            rod_lengths.append(rod_length)
            rod_zs.append(rod_z)
            beyond_back_of_arbours.append(beyond_back_of_arbour)
            print("Arbour {} rod length: {}mm with {:.1f}mm beyond the arbour".format(i, round(rod_length), beyond_back_of_arbour))



        return rod_lengths, rod_zs

    def get_pendulum_rod_lengths(self):
        '''
        Calculate lengths of threaded rod needed to make the pendulum
        '''



    def getClock(self, with_rods=False, with_key=False, with_pendulum=False):
        '''
        Probably fairly intimately tied in with the specific clock plates, which is fine while there's only one used in anger
        '''

        bottomPlate = self.plates.getPlate(True, for_printing=False)
        topPlate  = self.plates.getPlate(False, for_printing=False)

        if self.plates.pillars_separate:
            for bottomPillarPos in self.plates.bottomPillarPositions:
                bottomPlate = bottomPlate.add(self.plates.get_bottom_pillar().translate(bottomPillarPos).translate((0, 0, self.plates.getPlateThick(back=True))))
            bottomPlate = bottomPlate.add(self.plates.get_top_pillar().translate(self.plates.topPillarPos).translate((0, 0, self.plates.getPlateThick(back=True))))

        frontOfClockZ = self.plates.getPlateThick(True) + self.plates.getPlateThick(False) + self.plates.plateDistance

        clock = bottomPlate.add(topPlate.translate((0,0,self.plates.plateDistance + self.plates.getPlateThick(back=True))))

        if self.plates.backPlateFromWall > 0:
            #need wall standoffs
            clock = clock.add(self.plates.getWallStandoff(top=True, forPrinting=False))
            clock = clock.add(self.plates.getWallStandoff(top=False, forPrinting=False))
            # clock = clock.add(self.plates.getWallStandOff())
            # clock = clock.add(self.plates.getDrillTemplate(6))

        if self.plates.need_front_anchor_bearing_holder():
            clock = clock.add(self.plates.get_front_anchor_bearing_holder(for_printing=False))

        #the wheels
        # arbours = self.goingTrain.wheels + self.goingTrain.chainWheels + 1
        # for a in range(arbours):
        #     arbour = self.goingTrain.getArbourWithConventionalNaming(a)
        #     clock = clock.add(arbour.getAssembled().translate(self.plates.bearingPositions[a]).translate((0,0,self.plates.getPlateThick(back=True) + self.plates.endshake/2)))
        for a,arbour in enumerate(self.plates.arboursForPlate):
            clock = clock.add(arbour.get_assembled())

        # if self.plates.escapementOnFront:
        #
        #     escapeWheelIndex = -2
        #     #double endshake on the extra front plate
        #     wheel = self.goingTrain.getArbourWithConventionalNaming(escapeWheelIndex).getEscapeWheel(forPrinting=False)
        #     #note getWheelBaseToAnchorBaseZ is negative
        #     clock = clock.add(wheel.translate((self.plates.bearingPositions[escapeWheelIndex][0], self.plates.bearingPositions[escapeWheelIndex][1], frontOfClockZ + self.plates.endshake -self.goingTrain.escapement.getWheelBaseToAnchorBaseZ())))
        #
        #     anchor = self.goingTrain.getArbourWithConventionalNaming(-1).getAnchor(forPrinting=False)#getExtras()["anchor"]
        #     clock = clock.add(anchor.translate((self.plates.bearingPositions[-1][0], self.plates.bearingPositions[-1][1], frontOfClockZ + self.plates.endshake)))


        #where the nylock nut and spring washer would be (6mm = two half size m3 nuts and a spring washer + some slack)
        motionWorksZOffset = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motionWorks.inset_at_base

        time_min = self.timeMins
        time_hour = self.timeHours


        minuteAngle = - 360 * (time_min / 60)
        hourAngle = - 360 * (time_hour + time_min / 60) / 12
        secondAngle = -360 * (self.timeSeconds / 60)

        motionWorksModel = self.motionWorks.getAssembled(motionWorksRelativePos=self.plates.motionWorksRelativePos,minuteAngle=minuteAngle)
        motionWorksZ = frontOfClockZ + motionWorksZOffset

        clock = clock.add(motionWorksModel.translate((self.plates.hands_position[0], self.plates.hands_position[1], motionWorksZ)))

        if self.plates.centred_second_hand:
            #the bit with a knob to set the time
            clock = clock.add(self.motionWorks.getCannonPinionPinion(standalone=True).translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0],self.plates.bearingPositions[self.goingTrain.chainWheels][1], motionWorksZ )))
        if self.plates.need_motion_works_holder:
            clock = clock.add(self.plates.get_motion_works_holder().translate((self.plates.motionWorksPos[0], self.plates.motionWorksPos[1], frontOfClockZ)))

        if self.dial is not None:
            dial = self.dial.get_assembled()#get_dial().rotate((0,0,0),(0,1,0),180)
            clock = clock.add(dial.translate((self.plates.hands_position[0], self.plates.hands_position[1], self.plates.dial_z + self.dial.thick + frontOfClockZ)))


        #hands on the motion work, showing the time
        #mirror them so the outline is visible (consistent with second hand)
        # minuteHand = self.hands.getHand(minute=True).mirror().translate((0,0,self.hands.thick)).rotate((0,0,0),(0,0,1), minuteAngle)
        # hourHand = self.hands.getHand(hour=True).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), hourAngle)
        hands = self.hands.getAssembled(time_minute = time_min, time_hour=time_hour, include_seconds=False ,gap_size = self.motionWorks.hourHandSlotHeight - self.hands.thick)
        #total, not effective, height because that's been taken into accounr with motionworksZOffset
        minuteHandZ = self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + motionWorksZOffset \
                      + self.motionWorks.get_cannon_pinion_total_height() - self.hands.thick

        # clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], minuteHandZ)))

        clock = clock.add(hands.translate((self.plates.hands_position[0], self.plates.hands_position[1],
                                              minuteHandZ - self.motionWorks.hourHandSlotHeight)))

        if self.goingTrain.has_seconds_hand():
            #second hand!! yay
            secondHand = self.hands.getHand(hand_type=HandType.SECOND).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), secondAngle)

            secondHandPos = self.plates.bearingPositions[-2][:2]
            secondHandPos.append(self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance+self.hands.secondFixing_thick)

            if self.plates.dial is not None:
                secondHandPos[2] = frontOfClockZ + self.plates.dial.support_length + self.plates.dial.thick

            if self.plates.centred_second_hand:
                secondHandPos = self.plates.hands_position[:]
                secondHandPos.append(minuteHandZ + self.hands.thick + self.hands.secondFixing_thick)

            clock = clock.add(secondHand.translate(secondHandPos))

        if with_key:
            key = self.plates.get_winding_key(for_printing=False)
            if key is not None:
                clock = clock.add(key.translate((self.plates.bearingPositions[0][0], self.plates.bearingPositions[0][1], frontOfClockZ + self.plates.key_offset_from_front_plate + self.plates.endshake/2)))

        pendulumRodExtraZ = 2

        pendulumRodFixing = self.pendulum.getPendulumForRod(forPrinting=False)

        pendulumHolderBaseZ = self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ

        if not self.plates.pendulumAtFront:
            pendulumHolderBaseZ = -self.plates.pendulumSticksOut - self.pendulum.pendulumTopThick/2

        # if self.plates.pendulumFixing == PendulumFixing.FRICTION_ROD:
        #     clock = clock.add(pendulumRodFixing.translate((self.plates.bearingPositions[-1][0], self.plates.bearingPositions[-1][1], pendulumHolderBaseZ)))

        pendulumRodCentreZ = pendulumHolderBaseZ + self.pendulum.pendulumTopThick / 2
        pendulumBobBaseZ = pendulumRodCentreZ - self.pendulum.bobThick / 2
        pendulumBobCentreY = self.plates.bearingPositions[-1][1] - self.goingTrain.pendulum_length * 1000

        if with_pendulum:


            clock = clock.add(self.pendulum.getBob(hollow=False).rotate((0,0,self.pendulum.bobThick / 2),(0,1,self.pendulum.bobThick / 2),180).translate((self.plates.bearingPositions[-1][0], pendulumBobCentreY, pendulumBobBaseZ)))

            clock = clock.add(self.pendulum.getBobNut().translate((0,0,-self.pendulum.bobNutThick/2)).rotate((0,0,0), (1,0,0),90).translate((self.plates.bearingPositions[-1][0], pendulumBobCentreY, pendulumBobBaseZ + self.pendulum.bobThick/2)))


        if len(self.weights) > 0:
            for i, weight in enumerate(self.weights):
                #line them up so I can see if they'll bump into each other
                weightTopY = pendulumBobCentreY

                holePositions = self.goingTrain.poweredWheel.getChainPositionsFromTop()

                #side the main weight is on
                side = 1 if self.goingTrain.isWeightOnTheRight() else -1

                if i == 1:
                    #counterweight
                    side*=-1

                #in X,Y,Z
                weightPos = None

                for holeInfo in holePositions:
                    if (holeInfo[0][0] > 0) == (side > 0):
                        #hole for the weight
                        weightPos = (holeInfo[0][0], weightTopY - weight.height, self.plates.bearingPositions[0][2] + self.plates.getPlateThick(back=True) + self.goingTrain.poweredWheel.getHeight() + holeInfo[0][1])

                if weightPos is not None:
                    weightShape = weight.getWeight().rotate((0,0,0), (1,0,0),-90)

                    clock = clock.add(weightShape.translate(weightPos))


        #vector from minute wheel to the pendulum
        minuteToPendulum = (self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[self.goingTrain.chainWheels][1])

        if abs(minuteToPendulum[0]) < 50:
            ring = self.pendulum.getHandAvoider()
            if self.plates.pendulumAtFront:
                #if the hands are directly below the pendulum pivot point (not necessarily true if this isn't a vertical clock)

                #centre around the hands by default
                ringY = self.plates.bearingPositions[self.goingTrain.chainWheels][1]
                if self.goingTrain.poweredWheel.type == PowerType.CORD and self.goingTrain.poweredWheel.useKey:
                    #centre between the hands and the winding key
                    ringY =  (self.plates.bearingPositions[self.goingTrain.chainWheels][1] + self.plates.bearingPositions[0][1])/2


                handAvoiderExtraZ = (self.pendulum.pendulumTopThick - self.pendulum.handAvoiderThick)/2
                #ring is over the minute wheel/hands
                clock = clock.add(ring.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], ringY, self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ + handAvoiderExtraZ)))
            else:
                #pendulum is at the back, hand avoider is around the bottom pillar (unless this proves too unstable)
                if len(self.plates.bottomPillarPositions) == 1:
                    ringCentre = self.plates.bottomPillarPositions[0]
                    clock = clock.add(ring.translate(ringCentre).translate((0,0,-self.plates.pendulumSticksOut - self.pendulum.handAvoiderThick/2)))


        if self.pulley is not None:

            chainWheelTopZ = self.plates.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() + self.plates.getPlateThick(back=True) + self.plates.endshake / 2

            chainZ = chainWheelTopZ + self.goingTrain.poweredWheel.getChainPositionsFromTop()[0][0][1]

            #TODO for two bottom pillars
            pulleyY = self.plates.bottomPillarPositions[0][1] - self.plates.bottomPillarR - self.pulley.diameter

            if self.plates.huygensMaintainingPower:
                pulley = self.pulley.getAssembled().translate((0,0,-self.pulley.getTotalThick()/2)).rotate((0,0,0), (0,1,0),90)
                clock = clock. add(pulley.translate((self.goingTrain.poweredWheel.diameter/2, pulleyY, chainZ + self.goingTrain.poweredWheel.diameter/2)))
                if self.goingTrain.poweredWheel.type == PowerType.ROPE:
                    #second pulley for the counterweight
                    clock = clock.add(pulley.translate((-self.goingTrain.poweredWheel.diameter / 2, pulleyY, chainZ + self.goingTrain.poweredWheel.diameter / 2)))
            else:

                clock = clock.add(self.pulley.getAssembled().rotate((0,0,0),(0,0,1),90).translate((0, pulleyY, chainZ - self.pulley.getTotalThick()/2)))

        if self.plates.huygensMaintainingPower:
            clock = clock.add(self.plates.huygensWheel.getAssembled().translate(self.plates.bottomPillarPositions).translate((0, self.plates.huygens_wheel_y_offset, self.plates.getPlateThick(True) + self.plates.getPlateThick(False) + self.plates.plateDistance + WASHER_THICK_M3)))

        #TODO pendulum bob and nut?

        #TODO weight?

        if with_rods:
            rod_lengths, rod_zs = self.get_arbour_rod_lengths()
            for i in range(len(rod_lengths)):
                rod = cq.Workplane("XY").circle(self.goingTrain.getArbourWithConventionalNaming(i).arbourD/2 - 0.2).extrude(rod_lengths[i]).translate((self.plates.bearingPositions[i][0], self.plates.bearingPositions[i][1], rod_zs[i]))
                clock = clock.add(rod)

        return clock

    def getSpanner(self, size, length=180):
        '''

        '''

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getClock(), out)

    def outputSVG(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.svg".format(name))
        print("Outputting ", out)
        exportSVG(self.getClock(), out, opts={"width":720,"height":1280})


def getHandDemo(justStyle=None, length = 120, perRow=3, assembled=False, time_min=10, time_hour=10, time_sec=0, chunky=False, outline=1, include_seconds=True):
    demo = cq.Workplane("XY")

    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)
    print("motion works r", motionWorks.get_widest_radius())

    space = length

    if assembled:
        space = length*2

    for i,style in enumerate(HandStyle):

        if justStyle is not None and style != justStyle:
            continue

        hands = Hands(style=style, chunky=chunky, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=length, thick=motionWorks.minuteHandSlotHeight, outline=outline,
                      outlineSameAsBody=False, secondLength=25)

        x = 0
        y = 0
        if justStyle is None:
            x = space*(i%perRow)
            y = (space)*math.floor(i/perRow)

        secondsHand = None
        try:
            secondsHand =hands.getHand(hand_type=HandType.SECOND)
        except:
            print("Unable to generate second hand for {}".format(style.value))

        if assembled:
            #showing a time
            # minuteAngle = - 360 * (time_min / 60)
            # hourAngle = - 360 * (time_hour + time_min / 60) / 12
            # secondAngle = -360 * (time_sec / 60)
            #
            # # hands on the motion work, showing the time
            # # mirror them so the outline is visible (consistent with second hand)
            # minuteHand = hands.getHand(minute=True).rotate((0, 0, 0), (0, 0, 1), minuteAngle)
            # hourHand = hands.getHand(hour=True).rotate((0, 0, 0), (0, 0, 1), hourAngle)

            # demo = demo.add(minuteHand.translate((x, y, hands.thick)))
            # demo = demo.add(hourHand.translate((x, y, 0)))
            demo = demo.add(hands.getAssembled(include_seconds=False, time_seconds=time_sec, time_minute=time_min, time_hour=time_hour).translate((x, y, 0)))

            if secondsHand is not None and include_seconds:
                demo = demo.add(secondsHand.translate((x, y + length * 0.3)))

        else:
            demo = demo.add(hands.getHand(hand_type=HandType.HOUR).translate((x, y)))
            demo = demo.add(hands.getHand(hand_type=HandType.MINUTE).translate((x+length*0.3, y)))
            if secondsHand is not None and include_seconds:
                demo = demo.add(secondsHand.translate((x - length * 0.3, y)))


    return demo

def getAnchorDemo(style=AnchorStyle.STRAIGHT):
    escapment = AnchorEscapement(style=style)
    return escapment.getAnchor()

def getGearDemo(module=1, justStyle=None, oneGear=False):
    demo = cq.Workplane("XY")

    train = GoingTrain(pendulum_period=2, fourth_wheel=False, maxWeightDrop=1200, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.5 * 24)

    moduleReduction = 0.9

    train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)
    # train.setChainWheelRatio([93, 10])

    train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1.5, cordCoilThick=14, style=None, useKey=True, preferedDiameter=25)
    # override default until it calculates an ideally sized wheel
    train.calculatePoweredWheelRatios(wheel_max=100)

    train.genGears(module_size=module, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, useNyloc=False, pinionThickMultiplier=3, style=None, chainModuleIncrease=1, chainWheelPinionThickMultiplier=2,
                   ratchetInset=False)

    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)

    demoArboursNums = [0, 1, 3]

    #get a chain wheel, a normal wheel, an escape wheel and part of the motion works for a good spread of sizes and inner radii
    demoArbours = [train.getArbourWithConventionalNaming(i) for i in demoArboursNums]
    demoArbours.append(motionWorks.getMotionArbour())

    gap = 5
    space = max([arbour.getMaxRadius()*2 for arbour in demoArbours]) + gap

    if oneGear and justStyle is not None:
        demoArbours[1].style = justStyle
        return demoArbours[1].getShape()

    x=0

    for i,style in enumerate(GearStyle):
        if justStyle is not None and style != justStyle:
            continue
        print(style.value)
        # try:
        y=0
        for arbour in demoArbours:
            arbour.style = style
            y += arbour.getMaxRadius() + gap
            demo = demo.add(arbour.getShape().translate((x,y,0)))
            y += arbour.getMaxRadius()

        x += space
        # except Exception as e:
        #     print("Failed to generate demo for {}: {}".format(style.value, e))

    return demo