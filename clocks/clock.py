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
import numpy.linalg.linalg

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

# if 'show_object' not in globals():
#     #don't output STL when we're in cadquery editor
#     outputSTL = True
#     def show_object(*args, **kwargs):
#         pass



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
    '''
    This sets which direction the gears are facing and does some work about setting the size of the escape wheel, which is getting increasingly messy
    and makes some assumptions that are no longer true, now there's a variety of power sources and train layouts.

    I propose instead moving this logic over to the plates and therefore out of Arbor and into ArborForPlate.
    Maybe even going as far as this class not generating any actual geometry? just being ratios?
    '''

    def __init__(self, pendulum_period=-1, pendulum_length_m=-1, wheels=3, fourth_wheel=None, escapement_teeth=30, chain_wheels=0, runtime_hours=30, chain_at_back=True, max_weight_drop=1800,
                 escapement=None, escape_wheel_pinion_at_front=None, use_pulley=False, huygens_maintaining_power=False, minute_wheel_ratio = 1, support_second_hand=False):
        '''

        pendulum_period: desired period for the pendulum (full swing, there and back) in seconds
        fourth_wheel: if True there will be four wheels from minute hand to the escape wheel
        escapement_teeth: number of teeth on the escape wheel DEPRECATED, provide entire escapement instead
        chain_wheels: if 0 the minute wheel is also the chain wheel, if >0, this many gears between the minute wheel and chain wheel (say for 8 day clocks)
        hours: intended hours to run for (dictates diameter of chain wheel)
        chain_at_back: Where the chain and ratchet mechanism should go relative to the minute wheel
        max_weight_drop: maximum length of chain drop to meet hours required, in mm
        max_chain_wheel_d: Desired diameter of the chain wheel, only used if chainWheels > 0. If chainWheels is 0 there is no flexibility here
        escapement: Escapement object. If not provided, falls back to defaults with esacpement_teeth
        use_pulley: if true, changes calculations for runtime
        escape_wheel_pinion_at_front:  bool, override default
        huygens_maintaining_power: bool, if true we're using a weight on a pulley with a single loop of chain/rope, going over a ratchet on the front of the clock and a counterweight on the other side from the main weight
        easiest to implement with a chain

        minute_wheel_ratio: usually 1 - so the minute wheel (chain wheel as well on a 1-day clock) rotates once an hour. If less than one, this "minute wheel" rotates less than once per hour.
        this makes sense (at the moment) only on a centred-second-hand clock where we have another set of wheels linking the "minute wheel" and the motion works

        support_second_hand: if the period and number of teeth on the escape wheel don't result in it rotating once a minute, try and get the next gear down the train to rotate once a minute


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
        self.pendulum_length = pendulum_length_m

        #was experimenting with having the minute wheel outside the powered wheel to escapement train - but I think it's a dead
        #end as it will end up with some slop if it's not in the train
        self.minute_wheel_ratio = minute_wheel_ratio

        self.support_second_hand = support_second_hand

        self.huygens_maintaining_power = huygens_maintaining_power
        self.arbors = []

        if pendulum_length_m < 0 and pendulum_period > 0:
            #calulate length from period
            self.pendulum_length = getPendulumLength(pendulum_period)
        elif pendulum_period < 0 and pendulum_length_m > 0:
            self.pendulum_period = getPendulumPeriod(pendulum_length_m)
        else:
            raise ValueError("Must provide either pendulum length or perioud, not neither or both")
        print("Pendulum length {}cm and period {}s".format(self.pendulum_length*100, self.pendulum_period))
        #note - this has become assumed in many places and will require work to the plates and layout of gears to undo
        self.chain_at_back = chain_at_back
        #likewise, this has been assumed, but I'm trying to undo those assumptions to use this
        self.penulum_at_front = True
        #to ensure the anchor isn't pressed up against the back (or front) plate
        if escape_wheel_pinion_at_front is None:
            self.escape_wheel_pinion_at_front = chain_at_back
        else:
            self.escape_wheel_pinion_at_front=escape_wheel_pinion_at_front

        self.powered_by = PowerType.NOT_CONFIGURED

        #if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.powered_wheels = chain_wheels
        #to calculate sizes of the powered wheels and ratios later
        self.runtime_hours = runtime_hours
        self.max_weight_drop = max_weight_drop
        self.use_pulley=use_pulley

        if fourth_wheel is not None:
            #old deprecated interface, use "wheels" instead
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

    def has_seconds_hand_on_escape_wheel(self):
        #not sure this should work with floating point, but it does...
        return self.escapement_time == 60

    def has_second_hand_on_last_wheel(self):

        last_pair = self.trains[0]["train"][-1]
        return self.escapement_time / (last_pair[1]/last_pair[0]) == 60

    def get_cord_usage(self):
        '''
        how much rope or cord will actually be used, as opposed to how far the weight will drop
        '''
        if self.use_pulley:
            return 2*self.max_weight_drop
        return self.max_weight_drop

    '''
    TODO make this generic and re-usable, I've got similar logic over in calculating chain wheel ratios and motion works
    '''
    def calculate_ratios(self, module_reduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth=20, wheel_min_teeth=50,
                         max_error=0.1, loud=False, penultimate_wheel_min_ratio=0, favour_smallest=True, allow_integer_ratio=False):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        module reduction used to calculate smallest possible wheels - assumes each wheel has a smaller module than the last
        penultimate_wheel_min_ratio - check that the ratio of teeth on the last wheel is greater than the previous wheel's teeth * penultimate_wheel_min_ratio (mainly for trains
        where the second hand is on the penultimate wheel rather than the escape wheel - since we prioritise smaller trains we can end up with a teeny tiny escape wheel)

        now favours a low standard deviation of number of teeth on the wheels - this should stop situations where we get a giant first wheel and tiny final wheels (and tiny escape wheel)
        This is slow, but seems to work well
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
        all_gear_pair_combos = []
        all_seconds_wheel_combos = []

        target_time = 60 * 60 / self.minute_wheel_ratio

        for p in range(pinion_min, pinion_max):
            for w in range(wheel_min, wheel_max):
                all_gear_pair_combos.append([w, p])


        #use a much wider range
        if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel():
            for p in range(pinion_min, pinion_max*3):
                for w in range(pinion_max, wheel_max*4):
                    # print(p, w, self.escapement_time / (p/w))
                    if self.escapement_time / (p/w) == 60:
                        all_seconds_wheel_combos.append([w,p])
        if loud:
            print("allGearPairCombos", len(all_gear_pair_combos))
        # [ [[w,p],[w,p],[w,p]] ,  ]
        all_trains = []

        print(all_seconds_wheel_combos)

        all_trains_length = 1
        for i in range(self.wheels):
            all_trains_length *= len(all_gear_pair_combos)
        allcombo_count = len(all_gear_pair_combos)

        def add_combos(pair_index=0, previous_pairs=None):
            if previous_pairs is None:
                previous_pairs = []
            # one fewer pair than wheels, and if we're the last pair then add the combos, else recurse
            final_pair = pair_index == self.wheels - 2
            valid_combos = all_gear_pair_combos
            if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel() and final_pair:
                #using a different set of combinations that will force the penultimate wheel to rotate at 1 rpm
                valid_combos = all_seconds_wheel_combos
            for pair in range(len(valid_combos)):
                if loud and pair % 10 == 0 and pair_index == 0:
                    print("\r{:.1f}% of calculating train options".format(100 * pair / allcombo_count), end='')


                all_pairs = previous_pairs + [valid_combos[pair]]
                if final_pair:
                    all_trains.append(all_pairs)
                else:
                    add_combos(pair_index+1, all_pairs)

        #recursively create an array of all gear trains to test - should work with any number of wheels >= 2
        add_combos()

        if loud:
            print("\nallTrains", len(all_trains))
        all_times = []
        total_trains = len(all_trains)
        for c in range(total_trains):
            if loud and c % 100 == 0:
                print("\r{:.1f}% of trains evaluated".format(100 * c / total_trains), end='')
            total_ratio = 1
            int_ratio = False
            total_teeth = 0
            # trying for small wheels and big pinions
            total_wheel_teeth = 0
            total_pinion_teeth = 0
            weighting = 0
            last_size = 0
            fits = True
            for p in range(len(all_trains[c])):
                ratio = all_trains[c][p][0] / all_trains[c][p][1]
                if ratio == round(ratio):
                    int_ratio = True
                    if not allow_integer_ratio:
                        break
                total_ratio *= ratio
                total_teeth += all_trains[c][p][0] + all_trains[c][p][1]
                total_wheel_teeth += all_trains[c][p][0]
                total_pinion_teeth += all_trains[c][p][1]
                # module * number of wheel teeth - proportional to diameter
                size = math.pow(module_reduction, p) * all_trains[c][p][0]
                if favour_smallest:
                    weighting += size
                else:
                    #still don't want to just choose largest by mistake
                    weighting += size*0.3
                if p > 0 and size > last_size * 0.9:
                    # this wheel is unlikely to physically fit
                    fits = False
                    break
                last_size = size
            #favour evenly sized wheels
            wheel_tooth_counts = [pair[0] for pair in all_trains[c]]
            weighting += np.std(wheel_tooth_counts)
            if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel():
                #want to check last wheel won't be too tiny (would rather add more teeth than increase the module size for asthetics)
                if all_trains[c][-1][0] < all_trains[c][-2][0]*penultimate_wheel_min_ratio:
                    #only continue if the penultimate wheel has more than half the number of teeth of the wheel before that
                    continue


            total_time = total_ratio * self.escapement_time
            error = target_time - total_time
            if int_ratio:
                #avoid if we can
                weighting+=100

            train = {"time": total_time, "train": all_trains[c], "error": abs(error), "ratio": total_ratio, "teeth": total_wheel_teeth, "weighting": weighting}
            if fits and abs(error) < max_error:# and not int_ratio:
                all_times.append(train)

        if loud:
            print("")

        all_times.sort(key=lambda x: x["error"])
        # print(allTimes)

        self.trains = all_times

        if len(all_times) == 0:
            raise RuntimeError("Unable to calculate valid going train")
        print(all_times[0])
        return all_times

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

    def set_ratios(self, gear_pinion_pairs):
        '''
        Instead of calculating the gear train from scratch, use a predetermined one. Useful when using 4 wheels as those take a very long time to calculate
        '''
        #keep in the format of the autoformat
        time={'train': gear_pinion_pairs}

        self.trains = [time]

    def calculate_powered_wheel_ratios(self, pinion_min = 10, pinion_max = 20, wheel_min = 20, wheel_max = 160, prefer_small=False, inaccurate=False, big_pinion=False,
                                       prefer_large_second_wheel=True):
        '''
        Calcualte the ratio of the chain wheel based on the desired runtime and chain drop
        used to prefer largest wheel, now is hard coded to prefer smallest.

        experiment for springs, if inaccurate then allow a large variation of the final ratio if it helps keep the size down

        big_pinion if true prefer a larger first pinion (easier to print with multiple perimeters)


        prefer_large_second_wheel is usually true because this helps with spring barrels
        '''
        if self.powered_wheels == 0:
            '''
            nothing to do, the diameter is calculted in calculatePoweredWheelInfo
            '''
        else:
            #this should be made to scale down to 1 and then I can reduce the logic here

            max_error = 0.1
            if inaccurate:
                max_error=1

            turns = self.powered_wheel.get_turns(cord_usage=self.get_cord_usage())

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / (self.runtime_hours * self.minute_wheel_ratio)

            desiredRatio = 1 / turnsPerHour

            #consider tweaking this in future
            moduleReduction = 1.1
            #copy-pasted from calculateRatios and tweaked
            allGearPairCombos = []

            for p in range(pinion_min, pinion_max):
                for w in range(wheel_min, wheel_max):
                    allGearPairCombos.append([w, p])
            # [ [[w,p],[w,p],[w,p]] ,  ]
            allTrains = []

            allTrainsLength = 1
            for i in range(self.powered_wheels):
                allTrainsLength *= len(allGearPairCombos)

            allcomboCount = len(allGearPairCombos)
            if self.powered_wheels == 1:
                for pair_0 in range(allcomboCount):
                    allTrains.append([allGearPairCombos[pair_0]])
            elif self.powered_wheels == 2:
                for pair_0 in range(allcomboCount):
                    for pair_1 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
            else:
                raise ValueError("Unsupported number of chain wheels")
            all_ratios = []
            totalTrains = len(allTrains)
            for c in range(totalTrains):
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
                    #loop through each wheel/pinion pair
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
                    #prefer smaller wheels
                    weighting += size
                    #allow more space between the wheels than with the normal wheels ebcause of the chunky bit out the back of the chain wheel
                    # if p > 0 and size > lastSize * 0.875:
                    # # if p > 0 and size > lastSize * 0.9:
                    #     # this wheel is unlikely to physically fit
                    #     fits = False
                    #     break
                    #TODO does it fit next to the minute wheel?
                    # if p > 0 and size > self.trains[0][0][0]
                    lastSize = size
                    #TODO is the first wheel big enough to take the powered wheel?

                error = desiredRatio - totalRatio
                # weighting = totalWheelTeeth
                if self.powered_wheels == 2:
                    #prefer similar sizes
                    # weighting+=abs(allTrains[c][0][0] - allTrains[c][1][0])*0.5

                    if prefer_large_second_wheel:
                        #prefer second wheel more teeth (but not so much that it makes it huge)
                        weighting += (allTrains[c][0][0] - allTrains[c][1][0])*0.5#*0.5
                    else:
                        #similar sized if possible
                        weighting += abs(allTrains[c][0][0] - allTrains[c][1][0])
                    '''
                    Want large first pinion (for strength) and a smaller second wheel (so it will fit)
                    '''
                    # first_pinion_teeth = allTrains[c][0][1]
                    # weighting -= (first_pinion_teeth*8)# + allTrains[c][0][0] - allTrains[c][1][0]

                train = {"ratio": totalRatio, "train": allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth, "weighting": weighting}
                if fits and abs(error) < max_error and not intRatio:
                    all_ratios.append(train)

            all_ratios.sort(key=lambda x: x["weighting"])
            # print(all_ratios[0])
            # if not prefer_small:
            #     all_ratios.sort(key=lambda x: x["error"] - x["teeth"] / 1000)
            # else:
            #     # aim for small wheels where possible
            #     all_ratios.sort(key=lambda x: x["error"] + x["teeth"] / 100)
            if len(all_ratios) == 0 :
                raise ValueError("Unable to generate gear ratio for powered wheel")
            self.chain_wheel_ratios = all_ratios[0]["train"]
            print("chosen powered wheels: ", self.chain_wheel_ratios)
            print("")


    def set_chain_wheel_ratio(self, pinionPairs):
        '''
        Note, shouldn't need to use this anymore, and I think it's overriden when generating powered wheels anyway!
        '''
        if type(pinionPairs[0]) == int:
            #backwards compatibility with old clocks that assumed only one chain wheel was supported
            self.chain_wheel_ratios = [pinionPairs]
        else:
            self.chain_wheel_ratios = pinionPairs

    def is_weight_on_the_right(self):
        '''
        returns true if the weight dangles from the right side of the chain wheel (as seen from the front)
        '''

        clockwise = self.powered_wheel.is_clockwise()
        chainAtFront = not self.chain_at_back

        #XNOR
        clockwiseFromFront = not (clockwise != chainAtFront)

        return clockwiseFromFront

    def calculate_powered_wheel_info(self, default_powered_wheel_diameter=20):
        '''
        Calculate best diameter and direction of ratchet
        '''
        if self.powered_wheels == 0:
            #no choice but to set diameter to what fits with the drop and hours
            self.powered_wheel_circumference = self.get_cord_usage() / (self.runtime_hours * self.minute_wheel_ratio)
            self.powered_wheel_diameter = self.powered_wheel_circumference / math.pi

        else:
            #set the diameter to the minimum so the chain wheel gear ratio is as low as possible (TODO - do we always want this?)

            self.powered_wheel_diameter = default_powered_wheel_diameter

            self.powered_wheel_circumference = self.powered_wheel_diameter * math.pi

        # true for no chainwheels
        anticlockwise = self.chain_at_back

        for i in range(self.powered_wheels):
            anticlockwise = not anticlockwise

        self.powered_wheel_clockwise = not anticlockwise

    def gen_chain_wheels2(self, chain, ratchetThick=7.5, arbourD=3, loose_on_rod=True, prefer_small=False, preferedDiameter=-1, fixing_screws=None, ratchetOuterThick=5):

        diameter = preferedDiameter
        if diameter < 0:
            diameter = PocketChainWheel2.getMinDiameter()
        self.calculate_powered_wheel_info(diameter)

        if self.huygens_maintaining_power:
            # there is no ratchet with this setup
            ratchetThick = 0
            # TODO check holeD?

        self.powered_wheel = PocketChainWheel2(ratchet_thick=ratchetThick, arbor_d=arbourD, loose_on_rod=loose_on_rod,
                                               power_clockwise=self.powered_wheel_clockwise, chain=chain, max_diameter=self.powered_wheel_diameter, fixing_screws=fixing_screws, ratchetOuterThick=ratchetOuterThick)

        self.calculate_powered_wheel_ratios(prefer_small=prefer_small)

    def gen_chain_wheels(self, ratchetThick=7.5, holeD=3.4, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15, screwThreadLength=10, prefer_small=False):
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

        self.calculate_powered_wheel_info(PocketChainWheel.getMinDiameter())

        if self.huygens_maintaining_power:
            #there is no ratchet with this setup
            ratchetThick = 0
            #TODO check holeD?

        self.powered_wheel = PocketChainWheel(ratchet_thick=ratchetThick, power_clockwise=self.powered_wheel_clockwise, max_circumference=self.powered_wheel_circumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)

        self.calculate_powered_wheel_ratios(prefer_small=prefer_small)

    def gen_cord_wheels(self, ratchet_thick=7.5, rod_metric_thread=3, cord_coil_thick=10, use_key=False, cord_thick=2, style=GearStyle.ARCS, prefered_diameter=-1, loose_on_rod=True, prefer_small=False,
                        ratchet_diameter=-1, traditional_ratchet=False, min_wheel_teeth=20):
        '''
        If preferred diameter is provided, use that rather than the min diameter
        '''
        diameter = prefered_diameter
        if diameter < 0:
            diameter = CordWheel.getMinDiameter()

        if self.huygens_maintaining_power:
            raise ValueError("Cannot use cord wheel with huygens maintaining power")

        self.calculate_powered_wheel_info(diameter)
        self.powered_wheel = CordWheel(self.powered_wheel_diameter, ratchet_thick=ratchet_thick, power_clockwise=self.powered_wheel_clockwise,
                                       rod_metric_size=rod_metric_thread, thick=cord_coil_thick, use_key=use_key, cord_thick=cord_thick, style=style, loose_on_rod=loose_on_rod,
                                       cap_diameter=ratchet_diameter, traditional_ratchet=traditional_ratchet)
        self.calculate_powered_wheel_ratios(prefer_small=prefer_small, wheel_min=min_wheel_teeth)#prefer_large_second_wheel=False,

    def gen_rope_wheels(self, ratchetThick = 3, arbor_d=3, ropeThick=2.2, wallThick=1.2, preferedDiameter=-1, use_steel_tube=True, o_ring_diameter=2, prefer_small=False):

        diameter = preferedDiameter
        if diameter < 0:
            diameter = RopeWheel.getMinDiameter()

        self.calculate_powered_wheel_info(diameter)

        if self.huygens_maintaining_power:
            #there is no ratchet with this setup
            ratchetThick = 0


        if use_steel_tube:
            hole_d = STEEL_TUBE_DIAMETER
        else:
            hole_d = arbor_d + LOOSE_FIT_ON_ROD

        self.powered_wheel = RopeWheel(diameter=self.powered_wheel_diameter, hole_d = hole_d, ratchet_thick=ratchetThick, arbor_d=arbor_d,
                                       rope_diameter=ropeThick, power_clockwise=self.powered_wheel_clockwise, wall_thick=wallThick, o_ring_diameter=o_ring_diameter, need_bearing_standoff=True)

        self.calculate_powered_wheel_ratios(prefer_small=prefer_small)

    def gen_spring_barrel(self, spring = None, key_bearing=None, rod_d=4, pawl_angle=math.pi/2, click_angle=-math.pi/2, ratchet_at_back=True,
                          style=GearStyle.ARCS, chain_wheel_ratios=None, base_thick=8, fraction_of_max_turns=0.5, wheel_min_teeth=60, wall_thick=12):

        self.powered_wheel = SpringBarrel(spring=spring, key_bearing=key_bearing, rod_d=rod_d, clockwise=self.powered_wheels % 2 == 0,
                                          pawl_angle = pawl_angle, click_angle = click_angle, ratchet_at_back=ratchet_at_back, style=style, base_thick=base_thick,
                                          fraction_of_max_turns=fraction_of_max_turns, wall_thick=wall_thick)
        '''
        smiths: 66 teeth on barrel, 10 on next pinion
        76 teeth on next wheel, 13 on next pinion
        
        barrel rotates 4.35 times a week (168hours)
        '''
        if chain_wheel_ratios is None:
            self.calculate_powered_wheel_ratios(wheel_min=wheel_min_teeth, inaccurate = True)
        else:
            self.chain_wheel_ratios=chain_wheel_ratios

    def set_train(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]


    def print_info(self, weight_kg=0.35, for_runtime_hours=168):
        print(self.trains[0])




        print("pendulum length: {}m period: {}s".format(self.pendulum_length, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement.teeth))
        if PowerType.is_weight(self.powered_wheel.type):
            print("Powered wheel diameter: {}".format(self.powered_wheel_diameter))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.getRunTime()))
        power_ratio = self.minute_wheel_ratio
        power_wheel_ratios=[1]
        if self.powered_wheels > 0:
            #TODO if - for some reason - the minuteWheelRatio isn't 1, this logic needs checking
            print(self.chain_wheel_ratios)
            #how many turns per turn of the minute wheel
            power_ratio = 1
            for pair in self.chain_wheel_ratios:
                power_ratio *= pair[0] / pair[1]
            #the wheel/pinion tooth count
            power_wheel_ratios=self.chain_wheel_ratios

        if self.powered_wheel.type == PowerType.SPRING_BARREL:
            max_barrel_turns = self.powered_wheel.get_max_barrel_turns()

            turns = for_runtime_hours / power_ratio

            rewinding_turns = self.powered_wheel.get_key_turns_to_rewind_barrel_turns(turns)
            print("Over a runtime of {:.1f}hours the spring barrel will make {:.1f} full rotations which is {:.1f}% of the maximum number of turns ({:.1f}) and will take {:.1f} key turns to wind back up"
                  .format(for_runtime_hours, turns, 100.0*turns/max_barrel_turns, max_barrel_turns, rewinding_turns))
            return

        runtime_hours = self.powered_wheel.getRunTime(power_ratio, self.get_cord_usage())

        drop_m = self.max_weight_drop / 1000
        power = weight_kg * GRAVITY * drop_m / (runtime_hours*60*60)
        power_uW = power * math.pow(10, 6)
        #for reference, the hubert hurr eight day cuckoo is aproximately 34uW
        print("runtime: {:.1f}hours using {:.1f}m of cord/chain for a weight drop of {}. Chain wheel multiplier: {:.1f} ({})".format(runtime_hours, self.get_cord_usage() / 1000, self.max_weight_drop, power_ratio, power_wheel_ratios))
        print("With a weight of {}kg, this results in an average power usage of {:.1f}uW".format(weight_kg, power_uW))

        if len(self.arbors) > 0:
            self.get_arbour_with_conventional_naming(0).print_screw_length()
            self.get_arbour_with_conventional_naming(0).powered_wheel.print_screw_length()
        else:
            print("Generate gears to get screw information")

        if self.powered_wheel.type == PowerType.CORD:
            #because there are potentially multiple layers of cord on a cordwheel, power lever can vary enough for the clock to be viable when wound and not halfway through its run time!
            #seen this on clock 10!

            (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.powered_wheel.getCordTurningInfo(self.max_weight_drop * (2 if self.use_pulley else 1))
            #cord per rotation divided by chainRatio, gives speed in mm per hour, we want in m/s to calculate power
            effective_weight = weight_kg / (2 if self.use_pulley else 1)
            min_weight_speed = (cordPerRotationPerLayer[0] / power_ratio) /(60*60*1000)
            min_power = effective_weight * GRAVITY * min_weight_speed* math.pow(10, 6)
            max_weight_speed = (cordPerRotationPerLayer[-1] / power_ratio) / (60 * 60 * 1000)
            max_power = effective_weight * GRAVITY * max_weight_speed* math.pow(10, 6)
            print("Cordwheel power varies from {:.1f}uW to {:.1f}uW".format(min_power, max_power))

    def gen_gears(self, module_size=1.5, rod_diameters=None, module_reduction=0.5, thick=6, chain_wheel_thick=-1, escape_wheel_max_d=-1,
                  powered_wheel_module_increase=None, pinion_thick_multiplier = 2.5, style="HAC", chain_wheel_pinion_thick_multiplier=2, thickness_reduction=1,
                  ratchet_screws=None, pendulum_fixing=PendulumFixing.FRICTION_ROD, module_sizes = None, stack_away_from_powered_wheel=False, pinion_extensions=None,
                  powered_wheel_module_sizes = None, lanterns=None, pinion_thick_extra=-1, override_powered_wheel_distance=-1):
        '''
        What's provided to teh constructor and what's provided here is a bit scatty and needs tidying up.
        Also this assumes a *lot* about the layout, which really should be in the control of the plates
        Might even be worth making it entirely user-configurable which way the gears stack as layouts get more complicated, rather than assume we can calculate the best


        escapeWheelMaxD - if <0 (default) escape wheel will be as big as can fit
        if > 1 escape wheel will be as big as can fit, or escapeWheelMaxD big, if that is smaller
        if > 0 and < 1, escape wheel will be this fraction of the previous wheel

        stack_away_from_powered_wheel - experimental, put each wheel in "front" of the previous, usually we interleave gears to minimise plate distance,
         but we might want to minimise height instead. Required for compact plates with 4 wheels
        
        chain_module_increase - increase module size from the minute wheel down to the chainwheel by this multiplier
        
        alernatively can specify chain wheel modules directly:
        powered_wheel_module_sizes = [powered_wheel_0_module, powered_wheel_1_module...]
        
        lanterns, array of WHEEL-pinion pair indexes, anything in this list is a lantern pinion (eg if [0] the first pinion is a lantern pinion)

        pinion_thick_extra: newer idea, override pinion_thick_multiplier and chain_wheel_pinion_thick_multiplier.
         Just add this value to the thickness of the previous wheel for each pinion thickness

         bodge: chain_wheel_pinion_thick_multiplier will override pinion_thick_extra if chain_wheel_pinion_thick_multiplier is positive
        '''

        if rod_diameters is None:
            rod_diameters = [3 for i in range(self.powered_wheels + self.wheels + 1)]

        if lanterns is None:
            lanterns = []

        # lantern_indexed = [l in lanterns for l in range(self.powered_wheels + self.wheels)]

        if powered_wheel_module_increase is None:
            powered_wheel_module_increase = (1 / module_reduction)
            
        if powered_wheel_module_sizes is None:
            powered_wheel_module_sizes = []
            for i in range(self.powered_wheels):
                powered_wheel_module_sizes.append(module_size * powered_wheel_module_increase ** (self.powered_wheels - i))

        #can manually override the pinion extensions on a per arbor basis - used for some of the compact designs. Ideally I should automate this, but it feels like
        #a bit problem so solve so I'm offering the option to do it manually for now
        if pinion_extensions is None:
            pinion_extensions = {}

        self.pendulum_fixing = pendulum_fixing
        arbours = []
        # ratchetThick = holeD*2
        #thickness of just the wheel
        self.gear_wheel_thick=thick
        #thickness of arbour assembly
        #wheel + pinion (3*wheel) + pinion top (0.5*wheel)

        if chain_wheel_thick < 0:
            chain_wheel_thick = thick

        # self.gearPinionLength=thick*3
        # self.chainGearPinionLength = chainWheelThick*2.5


        #thought - should all this be part of the Gear or WheelAndPinion class?
        gear_pinion_end_cap_thick=max(thick * 0.25, 0.8)
        #on the assumption that we're using lantern pinions for strenght, make them chunky
        lantern_pinion_end_cap_thick = thick
        # self.gearTotalThick = self.gearWheelThick + self.gearPinionLength + self.gearPinionEndCapLength
        # self.chainGearTotalThick


        if module_sizes is None:
            module_sizes = [module_size * math.pow(module_reduction, i) for i in range(self.wheels)]

        print("module_sizes: {}".format(module_sizes))
        #the module of each wheel is slightly smaller than the preceeding wheel
        # pairs = [WheelPinionPair(wheel[0],wheel[1],module_sizes[i]) for i,wheel in enumerate(self.trains[0]["train"])]
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_sizes[i], lantern=(i+self.powered_wheels) in lanterns) for i,wheel in enumerate(self.trains[0]["train"])]




        # print(module_sizes)
        #make the escape wheel as large as possible, by default
        if (stack_away_from_powered_wheel or self.wheels == 3) and self.escape_wheel_pinion_at_front == self.chain_at_back:
            #avoid previous arbour extension (BODGE - this has no knowledge of how thick that is)
            escape_wheel_diameter = (pairs[len(pairs) - 1].centre_distance - rod_diameters[-2] - 2) * 2
        else:
            #avoid previous pinion
            escape_wheel_diameter = (pairs[len(pairs)-1].centre_distance - pairs[len(pairs)-2].pinion.get_max_radius() - 2) * 2

        #we might choose to override this
        if escape_wheel_max_d > 1 and escape_wheel_diameter > escape_wheel_max_d:
            escape_wheel_diameter = escape_wheel_max_d
        elif escape_wheel_max_d >0 and escape_wheel_max_d < 1:
            #treat as fraction of previous wheel
            escape_wheel_diameter = pairs[len(pairs) - 1].wheel.get_max_radius() * 2 * escape_wheel_max_d

        #little bit of a bodge
        self.escapement.set_diameter(escape_wheel_diameter)

        # chain wheel imaginary pinion (in relation to deciding which way the next wheel faces) is opposite to where teh chain is
        chain_wheel_imaginary_pinion_at_front = self.chain_at_back

        #this was an attempt to put the second wheel over the top of the powered wheel, if it fits, but now there are so many different setups I'm just disabling it
        second_wheel_r = pairs[1].wheel.get_max_radius()
        first_wheel_r = pairs[0].wheel.get_max_radius() + pairs[0].pinion.get_max_radius()
        powered_wheel_encasing_radius = self.powered_wheel.get_encasing_radius()#.ratchet.outsideDiameter/2
        space = first_wheel_r - powered_wheel_encasing_radius
        #logic is flawed and doesn't work with multiple powered wheels (eg 8 day spring)
        if second_wheel_r < space - 3:
            #the second wheel can actually fit on the same side as the ratchet
            chain_wheel_imaginary_pinion_at_front = not chain_wheel_imaginary_pinion_at_front
            print("Space to fit minute wheel in front of chain wheel - should result in smaller plate distance. check to ensure it does not clash with power mechanism")

        #this is a bit messy. leaving it alone for now, but basically we manually choose which way to have the escape wheel but by default it's at front (if the chain is also at the front)
        escape_wheel_pinion_at_front = self.escape_wheel_pinion_at_front

        #only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escape_wheel_clockwise = self.wheels %2 == 1

        escape_wheel_clockwise_from_pinion_side = escape_wheel_pinion_at_front == escape_wheel_clockwise

        pinion_at_front = chain_wheel_imaginary_pinion_at_front

        self.powered_wheel_arbors=[]
        self.powered_wheel_pairs=[]
        # chain_module_base = module_size
        chain_module_multiplier = 1
        #fits if we don't have any chain wheels, otherwise run the loop
        fits = self.powered_wheels == 0

        if override_powered_wheel_distance > 0 and self.powered_wheels == 1:
            #probably retrofitting a part
            print("overriding distance between powered wheel and second wheel")
            # fits=True
            #TODO this doesn't work, but I'm not sure what I've missed.
            chain_module = override_powered_wheel_distance / ((self.chain_wheel_ratios[0][0] + self.chain_wheel_ratios[0][1]) / 2)

            self.powered_wheel_pairs = [WheelPinionPair(self.chain_wheel_ratios[0][0], self.chain_wheel_ratios[0][1], chain_module, lantern=0 in lanterns)]
            print("chain module: ", chain_module)

        loop = 0
        while not fits and loop < 100:
            loop += 1
            self.powered_wheel_pairs = []
            for i in range(self.powered_wheels):
                #TODO review this
                # chain_module = chain_module_base * powered_wheel_module_increase ** (self.powered_wheels - i)
                chain_module = powered_wheel_module_sizes[i] * chain_module_multiplier
                # chain_wheel_space = chainModule * (self.chainWheelRatios[i][0] + self.chainWheelRatios[i][1]) / 2



                # #check if the chain wheel will fit next to the minute wheel
                # if i == 0 and chain_wheel_space < minuteWheelSpace:
                #     # calculate module for the chain wheel based on teh space available
                #     chainModule = 2 * minuteWheelSpace / (self.chainWheelRatios[0] + self.chainWheelRatios[1])
                #     print("Chain wheel module increased to {} in order to fit next to minute wheel".format(chainModule))
                # self.chainWheelPair = WheelPinionPair(self.chainWheelRatios[0], self.chainWheelRatios[1], chainModule)
                #only supporting one at the moment, but open to more in the future if needed
                pair = WheelPinionPair(self.chain_wheel_ratios[i][0], self.chain_wheel_ratios[i][1], chain_module, lantern=i in lanterns)
                self.powered_wheel_pairs.append(pair)

            minute_wheel_space = pairs[0].wheel.get_max_radius() + rod_diameters[1]
            last_chain_wheel_space = self.powered_wheel_pairs[-1].wheel.get_max_radius()
            if not self.powered_wheel.loose_on_rod:
                #TODO properly work out space on rod behind pwoered wheel - should be calculated by the powered wheel
                # need space for the steel rod as the wheel itself is loose on the threaded rod
                minute_wheel_space += 1

            if last_chain_wheel_space < minute_wheel_space:
                # calculate module for the chain wheel based on teh space available
                chain_module_multiplier *= 1.01
                print("Chain wheel module multiplier to {} in order to fit next to minute wheel".format(chain_module_multiplier))
            else:
                fits = True

        power_at_front = not self.chain_at_back
        first_chainwheel_clockwise = self.powered_wheels % 2 == 0
        for i in range(self.powered_wheels):



            if i == 0:
                clockwise_from_powered_side = first_chainwheel_clockwise and power_at_front
                #the powered wheel
                self.powered_wheel_arbors.append(Arbor(powered_wheel=self.powered_wheel, wheel = self.powered_wheel_pairs[i].wheel, wheel_thick=chain_wheel_thick, arbor_d=self.powered_wheel.arbor_d,
                                                       distance_to_next_arbour=self.powered_wheel_pairs[i].centre_distance, style=style, ratchet_screws=ratchet_screws,
                                                       use_ratchet=not self.huygens_maintaining_power, pinion_at_front=power_at_front, clockwise_from_pinion_side=clockwise_from_powered_side))
            else:
                #just a bog standard wheel and pinion TODO take into account direction of stacking?!? urgh, this will do for now
                clockwise_from_pinion_side = first_chainwheel_clockwise == (i %2 == 0)
                pinion_thick = self.powered_wheel_arbors[i - 1].wheel_thick * chain_wheel_pinion_thick_multiplier
                if pinion_thick_extra > 0 and chain_wheel_pinion_thick_multiplier < 0:
                    pinion_thick = self.powered_wheel_arbors[i - 1].wheel_thick + pinion_thick_extra
                cap_thick = gear_pinion_end_cap_thick
                wheel_thick = chain_wheel_thick * (thickness_reduction ** i)
                if self.powered_wheel_pairs[i-1].pinion.lantern:
                    cap_thick = wheel_thick
                self.powered_wheel_arbors.append(Arbor(wheel = self.powered_wheel_pairs[i].wheel, wheel_thick=wheel_thick, arbor_d=rod_diameters[i], pinion=self.powered_wheel_pairs[i - 1].pinion,
                                                       pinion_thick=pinion_thick, end_cap_thick=cap_thick,
                                                       distance_to_next_arbour=self.powered_wheel_pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front,
                                                       clockwise_from_pinion_side=clockwise_from_pinion_side))
                if i == 1:
                    #negate flipping the direction of the pinion
                    pinion_at_front = not pinion_at_front
            pinion_at_front = not pinion_at_front

        for i in range(self.wheels):
            clockwise = i % 2 == 0
            clockwise_from_pinion_side = clockwise == pinion_at_front

            pinion_extension = 0
            if i in pinion_extensions:
                pinion_extension = pinion_extensions[i]

            if i == 0:
                # == minute wheel ==
                if self.powered_wheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbor(powered_wheel=self.powered_wheel, wheel = pairs[i].wheel, wheel_thick=chain_wheel_thick, arbor_d=self.powered_wheel.arbor_d, distance_to_next_arbour=pairs[i].centre_distance,
                                   style=style, pinion_at_front=not self.chain_at_back, ratchet_screws=ratchet_screws, use_ratchet=not self.huygens_maintaining_power,
                                   clockwise_from_pinion_side=not self.chain_at_back)
                else:
                    # just a normal gear


                    if self.powered_wheels > 0:
                        pinion_thick = self.powered_wheel_arbors[-1].wheel_thick * chain_wheel_pinion_thick_multiplier
                    else:
                        pinion_thick = self.powered_wheel_arbors[-1].wheel_thick * pinion_thick_multiplier
                    if pinion_thick_extra > 0:
                        pinion_thick = self.powered_wheel_arbors[-1].wheel_thick + pinion_thick_extra
                    #occasionally useful on spring clocks to keep the minute wheel from bumping into the back part of a lantern wheel
                    #just make the pinino longer rather than actually add a pinion_extension
                    # pinion_thick += pinion_extension

                    cap_thick = lantern_pinion_end_cap_thick if self.powered_wheel_pairs[-1].pinion.lantern else gear_pinion_end_cap_thick
                    arbour = Arbor(wheel = pairs[i].wheel, pinion=self.powered_wheel_pairs[-1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], wheel_thick=thick, pinion_thick=pinion_thick, end_cap_thick=cap_thick,
                                   distance_to_next_arbour= pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=clockwise_from_pinion_side, pinion_extension=pinion_extension)

                arbours.append(arbour)
                if stack_away_from_powered_wheel:
                    #only the minute wheel behind teh chain wheel
                    pinion_at_front = not pinion_at_front

            elif i < self.wheels-1:
                ## == wheel-pinion pair ==
                pinion_thick = arbours[-1].wheel_thick * pinion_thick_multiplier
                if self.powered_wheels == 0 and i == 1:
                    #this pinion is for the chain wheel
                    pinion_thick = arbours[-1].wheel_thick * chain_wheel_pinion_thick_multiplier
                # if i == self.wheels-2 and self.has_second_hand_on_last_wheel() and stack_away_from_powered_wheel:
                #     #extend this pinion a bit to keep the giant pinion on the escape wheel from clashing
                #     #old bodge logic, use pinion_extensions instead now
                #     pinionExtension = pinion_thick*0.6

                if pinion_thick_extra > 0:
                    pinion_thick = arbours[-1].wheel_thick + pinion_thick_extra
                #intermediate wheels
                #no need to worry about front and back as they can just be turned around
                arbours.append(Arbor(wheel=pairs[i].wheel, pinion=pairs[i - 1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], wheel_thick=thick * (thickness_reduction ** i),
                                     pinion_thick=pinion_thick, end_cap_thick=gear_pinion_end_cap_thick, pinion_extension=pinion_extension,
                                     distance_to_next_arbour=pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=clockwise_from_pinion_side))
            else:
                # == escape wheel ==
                #Using the manual override to try and ensure that the anchor doesn't end up against the back plate (or front plate)
                #automating would require knowing how far apart the plates are, which we don't at this point, so just do it manually
                pinion_at_front = self.escape_wheel_pinion_at_front
                pinion_thick = arbours[-1].wheel_thick * pinion_thick_multiplier

                if pinion_thick_extra > 0:
                    pinion_thick = arbours[-1].wheel_thick + pinion_thick_extra
                #last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                #escape wheel has its thickness controlled by the escapement, but we control the arbour diameter
                arbours.append(Arbor(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], pinion_thick=pinion_thick, end_cap_thick=gear_pinion_end_cap_thick,
                                     distance_to_next_arbour=self.escapement.get_distance_beteen_arbours(), style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=escape_wheel_clockwise_from_pinion_side,
                                     pinion_extension=pinion_extension))
            if not stack_away_from_powered_wheel:
                pinion_at_front = not pinion_at_front

        #anchor is the last arbour
        #"pinion" is the direction of the extended arbour for fixing to pendulum
        #this doesn't need arbourD or thickness as this is controlled by the escapement
        arbours.append(Arbor(escapement=self.escapement, pinion_at_front=self.penulum_at_front, clockwise_from_pinion_side=escape_wheel_clockwise, arbor_d=rod_diameters[self.powered_wheels + self.wheels]))

        self.wheelPinionPairs = pairs
        self.arbors = arbours




        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

    def get_arbour_with_conventional_naming(self, i):
        '''
        Use the traditional naming of the chain wheel being zero
        if -ve, count from the anchor backwards (like array indexing in python, so -1 is the anchor, -2 is the escape wheel)
        '''
        if i < 0:
            i = i + len(self.arbors) + len(self.powered_wheel_arbors)
        return self.get_arbor(i - self.powered_wheels)

    def get_arbor(self, i):
        '''
        +ve is in direction of the anchor
        0 is minute wheel
        -ve is in direction of power ( so last chain wheel is -1, first chain wheel is -chainWheels)
        '''

        if i >= 0:
            return self.arbors[i]
        else:
            return self.powered_wheel_arbors[self.powered_wheels + i]


    # def getMinuteWheelPinionPair(self):
    #     return self.wheelPinionPairs[0]

    def output_STLs(self, name="clock", path="../out"):
        '''
        Going train soon will no longer need to generates shapes - it provides only basic Arbours for the plates to turn into printable objects
        '''
        #wheels, chainwheels
        for i in range(self.wheels + self.powered_wheels + 1):
            arbour = self.get_arbour_with_conventional_naming(i)
            out = os.path.join(path,"{}_wheel_{}.stl".format(name,i))
            print("Outputting ",out)
            exporters.export(arbour.get_shape(), out)
            extras = arbour.get_extras()
            for extraName in extras:
                out = os.path.join(path, "{}_wheel_{}_{}.stl".format(name, i, extraName))
                print("Outputting ", out)
                exporters.export(extras[extraName], out)

        self.powered_wheel.output_STLs(name, path)

        if self.escapement.type == EscapementType.GRASSHOPPER:
            self.escapement.output_STLs(name, path)

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

class MoonHolder:
    '''
    This might be worth splitting into different classes for each class of supported clock plate?

    bolts to the front of the front plate to hold the moon on a stick for the moon complication.
    needs both moon complication and SimpleClockPlates objects to calculate all the relevant dimensions
    highly coupled to both

    this needs to be able to be screwed into the front plate from the front - so i think space for the nuts behind the front plate

    current thinking: two peices. Print both with the bottom side facing forwards. One nearest the clock plates will have two branches on either side for the top of the dial to screw into
     and will be the moon spoon
    top peice will just be to clamp the steel tube in the right place.

    '''
    def __init__(self, plates, moon_complication, fixing_screws):
        self.plates = plates
        self.moon_complication = moon_complication
        self.fixing_screws = fixing_screws
        self.arbor_d = self.moon_complication.arbor_d
        self.moon_inside_dial = moon_complication.moon_inside_dial

        self.moon_extra_space = 1.5
        self.moon_spoon_thick = 1.6
        self.lid_thick = 6

        if self.plates.gear_train_layout == GearTrainLayout.ROUND:
            raise ValueError("TODO moon phase holder for round plates")

        if self.moon_inside_dial:
            if not isinstance(self.plates, RoundClockPlates):
                raise NotImplementedError("TODO support moon inside dial for other classes of plate")
            self.centre_y = self.plates.hands_position[1] + self.plates.radius
            self.height = self.plates.pillar_r*2
            self.moon_extra_space = 1
            # self.moon_spoon_thick = 1
        else:
            #sticking off the top of the clock, only used with SimpleClockPlates with a vertical gear train so far
            #assuming only one top pillar, or at least that htey're both at the same y
            max_y = self.plates.top_pillar_positions[0][1] + self.plates.top_pillar_r

            #top of the last wheel in the complication
            min_y = self.moon_complication.get_arbor_positions_relative_to_motion_works()[-1][1] + self.plates.hands_position[1] + self.moon_complication.pairs[2].wheel.get_max_radius()

            self.height = max_y - min_y
            self.centre_y = (max_y + min_y) / 2

        self.moon_y = self.centre_y + self.height/2 + self.moon_complication.moon_radius

        if self.moon_inside_dial:
            self.moon_y = self.plates.hands_position[1] + self.moon_complication.moon_from_hands


        print("Screw length for moon fixing: {}mm".format(self.moon_complication.get_relative_moon_z() + self.plates.get_plate_thick(back=False) + self.lid_thick))

    def get_moon_base_y(self):
        return self.moon_y - self.moon_complication.moon_radius

    def get_fixing_positions(self):
        #between pillar screws and anchor arbor
        top_fixing_y = (self.plates.top_pillar_positions[0][1] + self.plates.bearing_positions[-1][1]) / 2 - 1
        #just inside the dial, by fluke
        bottom_fixing_y = self.centre_y - self.height / 2 + 8
        return [(-self.plates.plate_width / 3, top_fixing_y), (self.plates.plate_width / 3, bottom_fixing_y)]

    def get_moon_holder_parts(self, for_printing=True):
        '''
        piece screwed onto the front of the front plate with a steel tube slotted into it to take the moon on a threaded rod

        combined "moon spoon" to cup aroudn the back of the moon and a part to screw into the plates
        '''

        lid_thick = self.lid_thick

        moon_z = self.moon_complication.get_relative_moon_z()# + self.plates.get_front_z()
        moon_r = self.moon_complication.moon_radius
        width = self.plates.plate_width
        # top_y = self.plates.top_pillar_positions[1] + self.plates.top_pillar_r



        # not a full spoon as i think this will be hard to print with the bridging
        # not so deep that it will be behind the front plates
        moon_spoon_deep = moon_z
        if moon_spoon_deep > moon_r * 0.75:
            # for smaller moons (likely moon-inside-plate) still limit to not being a full hemisphere
            moon_spoon_deep = moon_r * 0.75
        moon_centre_pos = (0, self.moon_y, moon_z)

        if self.moon_inside_dial:
            width = moon_r*2
            holder = (cq.Workplane("XY").moveTo(self.plates.hands_position[0], self.plates.hands_position[1]).circle(self.plates.radius + self.plates.plate_width/2).circle(self.plates.radius - self.plates.plate_width/2)
                      .extrude(moon_z).intersect(cq.Workplane("XY").moveTo(0, self.plates.hands_position[1] + self.plates.radius).rect(width,self.plates.radius).extrude(moon_z)))

            lid = (cq.Workplane("XY").moveTo(self.plates.hands_position[0], self.plates.hands_position[1]).circle(self.plates.radius + self.plates.plate_width / 2).circle(self.plates.radius - self.plates.plate_width / 2)
                      .extrude(moon_z).intersect(cq.Workplane("XY").moveTo(0, self.plates.hands_position[1] + self.plates.radius).rect(width,self.plates.radius).extrude(lid_thick)))
            lid = lid.translate((0, 0, moon_z))
            #something to link spoon with the holder, don't worry about overlapping as the moon hole will be cut out later
            link_height = self.centre_y - self.moon_y
            holder = holder.union(cq.Workplane("XY").rect(self.plates.plate_width, link_height).extrude(moon_spoon_deep).translate((0,(self.centre_y + self.moon_y)/2,moon_z - moon_spoon_deep)))
        else:
            r = self.moon_complication.get_last_wheel_r()
            sagitta = r - math.sqrt(r ** 2 - 0.25 * width ** 2)

            bottom_r = r + sagitta
            # designed to be inline with the top of the vertical clock plate
            holder = cq.Workplane("XY").moveTo(-width / 2, self.centre_y + self.height/2 -width/2).radiusArc((width/2, self.centre_y + self.height/2-width/2), width/2).lineTo(width/2,self.centre_y-self.height/2).\
                    radiusArc((-width/2, self.centre_y - self.height/2), -bottom_r).close().extrude(moon_z)

            lid = cq.Workplane("XY").moveTo(-width / 2, self.centre_y + self.height / 2 - width / 2).radiusArc((width / 2, self.centre_y + self.height / 2 - width / 2), width / 2).lineTo(width / 2, self.centre_y - self.height / 2). \
                radiusArc((-width / 2, self.centre_y - self.height / 2), -bottom_r).close().extrude(lid_thick)
            lid = lid.cut(cq.Workplane("XY").circle(moon_r + self.moon_extra_space).extrude(lid_thick).translate((0, moon_centre_pos[1], 0)))
            lid = lid.translate((0, 0, moon_z))

        moon_and_more = cq.Workplane("XY").sphere(moon_r + self.moon_extra_space + self.moon_spoon_thick)
        #just the back half
        moon_spoon = moon_and_more.cut(cq.Workplane("XY").rect(moon_r*4, moon_r*4).extrude(moon_r*4))
        moon_spoon = moon_spoon.translate(moon_centre_pos)

        moon_spoon = moon_spoon.intersect(cq.Workplane("XY").rect(moon_r*4,moon_r*4).extrude(moon_spoon_deep).translate(moon_centre_pos).translate((0,0,-moon_spoon_deep)))


        #moon spoon!
        holder = holder.union(moon_spoon)




        #moon hole
        cutter = cq.Workplane("XY").sphere(self.moon_complication.moon_radius + self.moon_extra_space).translate(moon_centre_pos)


        for screw_pos in self.get_fixing_positions():
            cutter = cutter.union(self.fixing_screws.get_cutter(with_bridging=True, layer_thick=self.plates.layer_thick).rotate((0, 0, 0), (1, 0, 0), 180).translate((screw_pos[0], screw_pos[1], moon_z + lid_thick)))

        #the steel tube
        cutter = cutter.add(cq.Workplane("XY").circle(STEEL_TUBE_DIAMETER/2).extrude(1000).translate((0,0,-500)).rotate((0,0,0),(1,0,0), 90).translate((0,0,moon_z)))

        # space_d = self.fixing_screws.get_washer_diameter()+1
        space_d = max(self.fixing_screws.get_nut_containing_diameter(), self.fixing_screws.get_washer_diameter()) + 1

        # space for the two nuts, spring washer and normal washer at the bottom of the moon and nut at the top of the moon
        # nut_space = cq.Workplane("XY").circle(space_d/2).extrude(moon_r)
        # #space for nuts at the top of the moon (like on the front of the hands)
        # nut_space = nut_space.union(cq.Workplane("XY").circle(self.fixing_screws.get_nut_containing_diameter() / 2 + 0.5).extrude(self.moon_complication.moon_radius * 2).translate((0, 0, moon_r)))
        nut_space = cq.Workplane("XY").circle(space_d/2).extrude(moon_r*2 + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT*2)
        #.faces(">Z").workplane().circle(self.fixing_screws.get_nut_containing_diameter()/2+0.5)).extrude(self.moon_complication.moon_radius*2)

        nut_space = nut_space.rotate((0,0,0),(1,0,0),-90).translate(moon_centre_pos).translate((0,-moon_r-TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT, 0))

        cutter = cutter.union(nut_space)

        if self.moon_inside_dial:
            final_wheel_pos = np_to_set3( np.add(self.moon_complication.get_arbor_positions_relative_to_motion_works()[2], (self.plates.hands_position[0], self.plates.hands_position[1], 0)))
            bevel_r = self.moon_complication.bevel_pair.wheel_teeth * self.moon_complication.bevel_pair.module / 2
            # bevel_gear_pair = self.moon_complication.bevel_pair.bevel_gear_pair
            # #from _build_tooth_faces
            # pc_h = np.cos(bevel_gear_pair.gamma_r) * bevel_gear_pair.gs_r  # pitch cone height
            # pc_f = pc_h / np.cos(bevel_gear_pair.gamma_f)  # extended pitch cone flank length
            # pc_rb = pc_f * np.sin(bevel_gear_pair.gamma_f)  # pitch cone base radius

            padding = 3
            increase_fraction = (bevel_r + padding)/bevel_r


            #using a sphere as a rough measure for not clashing with the bevel gear
            bevel_sphere = cq.Workplane("XY").sphere(bevel_r + 2)
            bevel_cone = cq.Solid.makeCone(radius2=0, radius1=bevel_r + padding, height=self.moon_complication.bevel_pair.bevel_gear_pair.gear.cone_h * increase_fraction)
            cutter = cutter.union(bevel_cone.translate(final_wheel_pos).translate((0,0,self.moon_complication.gear_thick)))
            # holder = holder.union(bevel_cone.translate(final_wheel_pos).translate((0,0,self.moon_complication.gear_thick)))

        #experiment, as it looks a bit clunky right now
        # lid = lid.edges(">Z").fillet(1)

        holder = holder.cut(cutter)
        lid = lid.cut(cutter)



        if for_printing:
            holder = holder.rotate((0,0,0),(0,1,0),180)
        else:
            lid = lid.translate((0,0,0.1))

        return [holder, lid]




class SimpleClockPlates:
    '''
    This took a while to settle - clocks before wall_clock_4 will be unlikely to work anymore.

    This produces viable simple wall clocks and also supports being extended for other types of clock plate

    This has become a monster of a class. I think it's better to try and simplify this class and extend it for new types of clock plate, rather than adding yet more options
    to this class.

    TODO in future abstract out just all the useful re-usable bits into a ClockPlatesBase?
    '''

    @staticmethod
    def fancy_pillar(r, length, clockwise=True):
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

    def __init__(self, going_train, motion_works, pendulum, gear_train_layout=GearTrainLayout.VERTICAL, default_arbor_d=3, pendulum_at_top=True, plate_thick=5, back_plate_thick=None,
                 pendulum_sticks_out=20, name="", heavy=False, extra_heavy=False, motion_works_above=False, pendulum_fixing = PendulumFixing.FRICTION_ROD,
                 pendulum_at_front=True, back_plate_from_wall=0, fixing_screws=None, escapement_on_front=False, chain_through_pillar_required=True,
                 centred_second_hand=False, pillars_separate=True, dial=None, direct_arbor_d=DIRECT_ARBOUR_D, huygens_wheel_min_d=15, allow_bottom_pillar_height_reduction=False,
                 bottom_pillars=1, top_pillars=1, centre_weight=False, screws_from_back=None, moon_complication=None, second_hand=True, motion_works_angle_deg=-1, endshake=1,
                 embed_nuts_in_plate=False, extra_support_for_escape_wheel=False, compact_zigzag=False, layer_thick=LAYER_THICK_EXTRATHICK, top_pillar_holds_dial=False,
                 override_bottom_pillar_r=-1, vanity_plate_radius=-1, small_fixing_screws=None, force_escapement_above_hands=False, style=PlateStyle.SIMPLE, fancy_pillars=False,
                 standoff_pillars_separate=False):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!

        escapement_on_front: if true the escapement is mounted on the front of teh clock (helps with laying out a grasshopper) and if false, inside the plates like the rest of the train
        vanity_plate_radius - if >0 then there's an extra "plate" on the front to hide the motion works
        '''
        self.fancy_pillars = fancy_pillars
        self.style = style
        #for raised edging style
        self.edging_wide = 3
        self.edging_thick=LAYER_THICK*2

        #for other clock plates to override
        self.text_on_standoffs = False
        self.standoff_pillars_separate = standoff_pillars_separate

        self.vanity_plate_fixing_positions = []
        #how the pendulum is fixed to the anchor arbour. TODO centralise this
        self.pendulum_fixing = pendulum_fixing
        self.pendulum_at_front = pendulum_at_front

        #if the dial would stick off the top of the front plate the default is to extend the front plate
        #however this can result in plates taht are too large, so instead have a little arm that sticks out the top pillar and extend the length of the dial pillar
        self.top_pillar_holds_dial = top_pillar_holds_dial

        self.layer_thick = layer_thick

        #diameter of the cylinder that forms the arbour that physically links pendulum holder (or crutch in future) and anchor
        self.direct_arbor_d = direct_arbor_d

        self.dial = dial

        #are the main pillars attached to the back plate or independent? currently needs backPlateFromWall to create wall standoffs in order to screw to back plate
        self.pillars_separate = pillars_separate

        #try and put the weight central to the clock. Only currently affects the compact style when using two pillars
        self.centre_weight = centre_weight

        #if the going train supports it, put a second hand on the clock
        self.second_hand = second_hand
        #second hand is centred on the motion works
        self.centred_second_hand = centred_second_hand

        #does the chain/rope/cord pass through the bottom pillar?
        self.chainThroughPillar = chain_through_pillar_required

        #None or a MoonComplication object
        self.moon_complication = moon_complication

        #if escapementOnFront then extend out the front plate to hold the bearing - reduces wobble when platedistance is low
        self.extra_support_for_escape_wheel = extra_support_for_escape_wheel

        # if this is powered by a spring barrel, do we want to support the pawl with a little extra sticky out bit?
        #TODO apply to cord power too?
        self.little_plate_for_pawl = True

        angles_from_minute = None
        anglesFromChain = None

        self.gear_train_layout=gear_train_layout
        self.compact_zigzag = compact_zigzag

        #to print on the back
        self.name = name

        # how much the arbours can wobble back and forth. aka End-shake.
        # 2mm seemed a bit much
        # I've been using 1mm for ages, but clock 12 seemed to have gears binding, but wondering if actually it was gears wedged between the bearings (keeping an eye on it)
        # after the plates flexed over time - new technique of m4 bolts all the way through the pillars may help, but maybe a bit more endshake too?
        self.endshake = endshake

        # override default position of the motion works (for example if it would be in the way of a keywind and it can't go above because there's a moon complication)
        self.motion_works_angle = degToRad(motion_works_angle_deg)

        self.little_arm_to_motion_works = True

        if self.motion_works_angle < 0:
            # is the motion works arbour above the cannon pinion? if centred_second_hand then this is not user-controllable (deprecated - motion_works_angle is more flexible)
            if motion_works_above:
                self.motion_works_angle = math.pi/2
            else:
                #below
                self.motion_works_angle = math.pi*1.5

        #escapement is on top of the front plate
        self.escapement_on_front = escapement_on_front
        self.front_anchor_holder_part_of_dial = False

        #many designs have thet escapement above the hands anyway, but do we force it? currently I think this is a 1:1 mapping with escapement_on_front
        self.force_escapement_above_hands = escapement_on_front or force_escapement_above_hands

        #if true, mount the escapment on the front of the clock (to show it off or help the grasshopper fit easily)
        #if false, it's between the plates like the rest of the gear train
        #not sure much actually needs to change for the plates?
        # self.escapementOnFront = goingTrain.escapementOnFront
        #use the weight on a pulley with a single loop of chain/rope, going over a ratchet on the front of the clock and a counterweight on the other side from the main weight
        #easiest to implement with a chain
        self.huygens_maintaining_power = going_train.huygens_maintaining_power
        #for plates with very little distance (eg grasshopper) the bottom pillar will be small - but we still need a largeish wheel for the chain
        self.huygens_wheel_min_d = huygens_wheel_min_d

        #is the weight heavy enough that we want to chagne the plate design?
        #will result in wider plates up to the chain wheel
        self.heavy = heavy
        #beef up the pillars as well
        self.extra_heavy = extra_heavy

        if self.extra_heavy:
            self.heavy = True

        #2 or 1?
        self.bottom_pillars = bottom_pillars
        self.top_pillars = top_pillars

        #make the bottom pillar long a thin rather than round?
        self.narrow_bottom_pillar = self.bottom_pillars > 1

        #is the weight danging from a pulley? (will affect screwhole and give space to tie other end of cord)
        self.using_pulley = going_train.use_pulley

        #how much space the crutch will need - used for work out where to put the bearing for the anchor
        self.crutch_space = 10

        self.motion_works = motion_works
        self.going_train = going_train
        #TODO this is deprecated, remove it
        self.pendulum=pendulum
        #up to and including the anchor
        self.angles_from_minute = angles_from_minute
        self.angles_from_chain=anglesFromChain
        self.plate_thick=plate_thick
        self.back_plate_thick = back_plate_thick
        if self.back_plate_thick is None:
            self.back_plate_thick = self.plate_thick
        #default for anchor, overriden by most arbours
        self.arbor_d=default_arbor_d
        #how chunky to make the bearing holders
        self.bearing_wall_thick = 4

        #for fixing to teh wall
        self.wall_fixing_screw_head_d = 11

        self.pendulum_at_top = pendulum_at_top
        #how far away from the relevant plate (front if pendulumAtFront) the pendulum should be
        self.pendulum_sticks_out = pendulum_sticks_out
        #if this is 0 then pendulumAtFront is going to be needed
        self.back_plate_from_wall = back_plate_from_wall
        self.fixing_screws = fixing_screws
        if self.fixing_screws is None:
            #PREVIOUSLY longest pozihead countersunk screws I can easily get are 25mm long. I have some 40mm flathead which could be deployed if really needed
            #now found supplies of pozihead countersunk screws up to 60mm, so planning to use two screws (each at top and bottom) to hold everything together
            self.fixing_screws = MachineScrew(metric_thread=3, countersunk=True)#, length=25)

        self.motion_works_screws = MachineScrew(metric_thread=self.arbor_d, countersunk=True)
        self.small_fixing_screws = small_fixing_screws
        if self.small_fixing_screws is None:
            #TODO switch over lots of the little bits that currently use motion_works_screws to use small_fixing_screws
            self.small_fixing_screws = MachineScrew(metric_thread=3, countersunk=True)

        self.vanity_plate_radius = vanity_plate_radius
        self.has_vanity_plate = self.vanity_plate_radius > 0
        self.vanity_plate_thick = 2
        self.vanity_plate_pillar_r = self.small_fixing_screws.metric_thread
        self.vanity_plate_base_z = self.front_of_motion_works_wheels_z()

        #for some dials (filled-in ones like tony) it won't be possible to get a screwdriver (or the screw!) in from the front, so instead screw in from the back
        #currently this also implies that the nuts will be sticking out the front plate (I don't want to embed them in the plate and weaken it)
        #originally just a boolean, now a list of booleans for each pillar, starting at hte top. eg top pillar only screws from back: [True, False]
        #now it's a list of list of booleans! [[top0, top1],[bottom0, bottom1]]
        #I should really re-think this.
        self.screws_from_back = screws_from_back
        if self.screws_from_back is None:
            self.screws_from_back = [[False, False], [False, False]]
        #plates try to put screws that hold the pillars together in the rear standoff, but can override to put them in the back plate (if there isn't a wall standoff)
        self.embed_nuts_in_plate = embed_nuts_in_plate

        # how thick the bearing holder out the back or front should be
        # can't use bearing from ArborForPlate yet as they haven't been generated
        # bit thicker than the front bearing thick because this may have to be printed with supports
        if pendulum_fixing == PendulumFixing.SUSPENSION_SPRING:
            self.rear_standoff_bearing_holder_thick = get_bearing_info(going_train.get_arbour_with_conventional_naming(-1).arbor_d).height + 2
        else:
            self.rear_standoff_bearing_holder_thick = self.plate_thick

        # how much space to leave around the edge of the gears for safety
        self.gear_gap = 3
        # if self.style == ClockPlateStyle.COMPACT:
        #     self.gearGap = 2
        self.small_gear_gap = 2

        self.ideal_key_length = 35

        #if the bottom pillar radius is increased to allow space for the chains to fit through, do we permit the gear wheel to cut into that pillar?
        self.allow_bottom_pillar_height_reduction = allow_bottom_pillar_height_reduction

        if self.allow_bottom_pillar_height_reduction and self.bottom_pillars > 1:
            raise ValueError("Does not support pillar height reduction with more than one pillar")

        self.weight_on_right_side = self.going_train.is_weight_on_the_right()

        self.calc_bearing_positions()
        self.generate_arbours_for_plate()

        if PowerType.is_weight(self.going_train.powered_wheel.type):
            self.weight_driven = True
            self.chain_hole_d = self.going_train.powered_wheel.getChainHoleD()
        else:
            self.weight_driven = False
        self.chain_hole_d =0

        if self.chain_hole_d < 4:
            self.chain_hole_d = 4

        #set in calc_winding_key_info()
        self.winding_key = None

        self.powered_wheel_r = self.going_train.get_arbor(-self.going_train.powered_wheels).get_max_radius() + self.gear_gap

        self.reduce_bottom_pillar_height = 0
        self.calc_pillar_info(override_bottom_pillar_r)


        #calcualte the positions of the bolts that hold the plates together
        self.calc_fixing_info()


        self.huygens_wheel = None
        #offset in y? This enables the plate to stay smaller (and fit on the print bed) while still offering a large huygens wheel
        self.huygens_wheel_y_offset = 0
        if self.huygens_maintaining_power:
            max_circumference = self.bottom_pillar_r * 1.25 * math.pi
            max_diameter = max_circumference/math.pi
            ratchetOuterD = self.bottom_pillar_r * 2

            if max_diameter < self.huygens_wheel_min_d:
                max_diameter = self.huygens_wheel_min_d
                max_circumference = max_diameter*math.pi
                ratchetOuterD = max_diameter+15
                if ratchetOuterD < self.bottom_pillar_r*2:
                    #have seen this happen, though I think it's rare
                    ratchetOuterD = self.bottom_pillar_r * 2
                self.huygens_wheel_y_offset = ratchetOuterD / 2 - self.bottom_pillar_r

            ratchetOuterThick = 3
            ratchet_thick=5
            #need a powered wheel and ratchet on the front!
            if self.going_train.powered_wheel.type == PowerType.CHAIN:

                self.huygens_wheel = PocketChainWheel(ratchet_thick=5, max_circumference=max_circumference, wire_thick=self.going_train.powered_wheel.chain_thick,
                                                      width=self.going_train.powered_wheel.chain_width, inside_length=self.going_train.powered_wheel.chain_inside_length,
                                                      tolerance=self.going_train.powered_wheel.tolerance, ratchetOuterD=self.bottom_pillar_r * 2, ratchetOuterThick=ratchetOuterThick)
            elif self.going_train.powered_wheel.type == PowerType.CHAIN2:
                self.huygens_wheel = PocketChainWheel2(ratchet_thick=5, max_diameter=max_diameter, chain=self.going_train.powered_wheel.chain, loose_on_rod=True,
                                                       ratchetOuterD=ratchetOuterD, ratchetOuterThick=ratchetOuterThick, arbor_d=self.going_train.powered_wheel.arbor_d)
            elif self.going_train.powered_wheel.type == PowerType.ROPE:
                huygens_diameter = max_diameter*0.95
                print("Huygens wheel diameter",huygens_diameter)
                self.huygens_wheel = RopeWheel(diameter=huygens_diameter, ratchet_thick=ratchet_thick, rope_diameter=self.going_train.powered_wheel.rope_diameter, o_ring_diameter=get_o_ring_thick(huygens_diameter - self.going_train.powered_wheel.rope_diameter * 2),
                                               hole_d=self.going_train.powered_wheel.hole_d, ratchet_outer_d=self.bottom_pillar_r * 2, ratchet_outer_thick=ratchetOuterThick)
            else:
                raise ValueError("Huygens maintaining power not currently supported with {}".format(self.going_train.powered_wheel.type.value))

        self.hands_position = self.bearing_positions[self.going_train.powered_wheels][:2]

        if self.centred_second_hand:

            seconds_arbor = -2
            if self.going_train.has_second_hand_on_last_wheel():
                seconds_arbor = -3

            self.hands_position = [self.bearing_positions[seconds_arbor][0], self.bearing_positions[seconds_arbor][1]]
            minute_wheel_pos = self.bearing_positions[self.going_train.powered_wheels][:2]

            #adjust motion works size
            minute_wheel_to_hands = np_to_set(np.subtract(minute_wheel_pos, self.hands_position))

            minute_wheel_to_hands_distance = np.linalg.norm(minute_wheel_to_hands)
            minute_wheel_to_hands_angle = math.atan2(minute_wheel_to_hands[1], minute_wheel_to_hands[0])

            arbor_distance = minute_wheel_to_hands_distance / 2

            if abs(self.motion_works_angle - minute_wheel_to_hands_angle) - math.pi > 0.01:
                #motion works angle will offset the centre arbor

                line_from_hands = Line(self.hands_position, angle=self.motion_works_angle)
                mid_line = Line(average_of_two_points(minute_wheel_pos, self.hands_position), angle=minute_wheel_to_hands_angle + math.pi / 2)

                mid_arbor_pos = line_from_hands.intersection(mid_line)
                arbor_distance = np.linalg.norm(np.subtract(mid_arbor_pos, minute_wheel_pos))


            self.motion_works.calculate_size(arbor_distance=arbor_distance)

            #override motion works position
            #note - new idea, allow this to function like the compact design of the plates
            # self.motion_works_angle = math.pi/2 if not self.pendulum_at_top else math.pi * 1.5





        motionWorksDistance = self.motion_works.get_arbor_distance()
        # get position of motion works relative to the minute wheel
        if gear_train_layout == GearTrainLayout.ROUND:
            # place the motion works on the same circle as the rest of the bearings
            angle = self.hands_on_side*2 * math.asin(motionWorksDistance / (2 * self.compact_radius))
            compactCentre = (0, self.compact_radius)
            minuteAngle = math.atan2(self.bearing_positions[self.going_train.powered_wheels][1] - compactCentre[1], self.bearing_positions[self.going_train.powered_wheels][0] - compactCentre[0])
            motionWorksPos = polar(minuteAngle - angle, self.compact_radius)
            motionWorksPos = (motionWorksPos[0] + compactCentre[0], motionWorksPos[1] + compactCentre[1])
            self.motion_works_relative_pos = (motionWorksPos[0] - self.bearing_positions[self.going_train.powered_wheels][0], motionWorksPos[1] - self.bearing_positions[self.going_train.powered_wheels][1])
        elif self.gear_train_layout == GearTrainLayout.COMPACT and motion_works_above and self.has_seconds_hand() and not self.centred_second_hand and self.extra_heavy:
            '''
            niche case maybe?
            put the motion works along the arm to the offset gear
            '''
            direction = np.subtract(self.bearing_positions[self.going_train.powered_wheels + 1][:2], self.bearing_positions[self.going_train.powered_wheels][:2])
            #make unit vector
            direction = np.multiply(direction, 1/np.linalg.norm(direction))

            self.motion_works_relative_pos = np_to_set(np.multiply(direction, motionWorksDistance))
        else:
            # motion works is directly below the minute rod by default, or whatever angle has been set
            self.motion_works_relative_pos = polar(self.motion_works_angle, motionWorksDistance)

        self.motion_works_pos = np_to_set(np.add(self.hands_position, self.motion_works_relative_pos))

        #calculate position even if it's not applicable to this clock
        friction_clip_dir = np.multiply(self.motion_works_relative_pos, -1/np.linalg.norm(self.motion_works_relative_pos))
        friction_clip_distance = self.motion_works.friction_ring_r*2.5
        self.cannon_pinion_friction_clip_pos = np_to_set(np.add(self.hands_position, np.multiply(friction_clip_dir, friction_clip_distance)))
        self.cannon_pinion_friction_clip_fixings_pos = [
            np_to_set(np.add(self.cannon_pinion_friction_clip_pos, (-self.plate_width / 5, -self.plate_width /  5))),
            np_to_set(np.add(self.cannon_pinion_friction_clip_pos, (self.plate_width / 5, self.plate_width / 5)))
        ]

        #even if it's not used:

        #TODO calculate so it's always just big enough?
        self.motion_works_holder_length = 30
        self.motion_works_holder_wide = self.plate_width
        self.motion_works_fixings_relative_pos = [(-self.plate_width / 4, self.motion_works_holder_length / 2) ,
                                                  (self.plate_width / 4, -(self.motion_works_holder_length / 2))]

        self.top_of_hands_z = self.motion_works.get_cannon_pinion_effective_height() + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT

        self.dial_top_above_front_plate = False
        self.dial_fixing_positions = []
        self.top_dial_fixing_y = -1

        if self.dial is not None:
            #calculate dial height after motion works gears have been generated, in case the height changed with the bearing
            # height of dial from top of front plate
            # previously given 8mm of clearance, but this was more than enough, so reducing down to 4
            # looks like I later reduced it to 3 (I think after clock 12?)
            self.dial_z = self.bottom_of_hour_hand_z() - self.dial.thick - self.dial.get_hand_space_z()
            if self.has_seconds_hand() and not self.centred_second_hand:
                #mini second hand! give a smidge more clearance
                self.dial_z -= 2

            print("dial z", self.dial_z)
            dial_support_d = self.plate_width

            if self.dial.is_full_dial():
                #free placement of the dial fixings
                if self.bottom_pillars > 1 and self.gear_train_layout == GearTrainLayout.COMPACT:
                    #put two fixings on either side of the chain wheel
                    #currently this is designed around tony the clock, and should be made more generic in the future
                    from_pillar_x = self.bottom_pillar_width if self.narrow_bottom_pillar else self.bottom_pillar_r * 1.5
                    dial_fixings = [
                        (abs(self.bottom_pillar_positions[0][0]) - from_pillar_x, self.bottom_pillar_positions[0][1]),
                        (-abs(self.bottom_pillar_positions[0][0]) + from_pillar_x, self.bottom_pillar_positions[0][1]),
                        (0, self.bearing_positions[-2][1])
                    ]

                    dial_fixings_relative_to_dial = []
                    dial_centre = tuple(self.bearing_positions[self.going_train.powered_wheels][:2])
                    # for fixing in dial_fixings:
                    #     relative_pos = npToSet(np.subtract(fixing, tuple(dial_centre)))
                    #     dial_fixings_relative_to_dial.append(relative_pos)
                    #array of arrays because we only want one screw per pillar here
                    dial_fixings_relative_to_dial = [[np_to_set(np.subtract(pos, dial_centre))] for pos in dial_fixings]

                    for dial_fixing in dial_fixings_relative_to_dial:
                        if np.linalg.norm(dial_fixing) > self.dial.outside_d*0.9:
                            #TODO actually relocate them, for now: cry
                            print("Dial fixings probably aren't inside dial!")

                    self.dial.override_fixing_positions(dial_fixings_relative_to_dial)
                    dial_support_d = 15


            if self.has_seconds_hand():
                second_hand_relative_pos = np_to_set(np.subtract(self.get_seconds_hand_position(), self.hands_position))

                if self.centred_second_hand:
                    # second_hand_mini_dial_d = -1
                    second_hand_relative_pos = None
                # else:
                    # distance_to_seconds = np.linalg.norm(second_hand_relative_pos)
                    #just overlapping a tiny bit
                    # second_hand_mini_dial_d = (self.dial.inner_r - distance_to_seconds + 2)*2
                    # print("second_hand_mini_dial_d: {}".format(second_hand_mini_dial_d))

                self.dial.configure_dimensions(support_length=self.dial_z, support_d=dial_support_d,second_hand_relative_pos=second_hand_relative_pos )
            else:
                self.dial.configure_dimensions(support_length=self.dial_z, support_d=dial_support_d)


              # [npToSet(np.add(pos, self.hands_position)) for pos in self.dial.get_fixing_positions()]
            for pos_list in self.dial.get_fixing_positions():
                for pos in pos_list:
                    # inverting x because dial is "backwards"
                    self.dial_fixing_positions.append(np_to_set(np.add((-pos[0], pos[1]), self.hands_position)))

            if len(self.dial_fixing_positions) > 0:
                self.top_dial_fixing_y = max([pos[1] for pos in self.dial_fixing_positions])

                self.dial_top_above_front_plate = self.top_dial_fixing_y > self.top_pillar_positions[0][1] and self.top_dial_fixing_y > self.bearing_positions[-1][1]
            else:
                self.dial_top_above_front_plate = False


            '''
            getting messy - if dial_top_above_front_plate then we need to lengthen the supports, but we couldn't do this when we called configure_dimensions because we
            didn't know where those supports were. could probably refactor, for now just hack it
            '''

            if self.dial_top_above_front_plate and self.top_pillar_holds_dial:
                front_plate_thick = self.get_plate_thick(back=False)
                self.dial.support_length += front_plate_thick
                #cut out for the front plate
                self.dial.subtract_from_supports = (cq.Workplane("XY").circle(self.top_pillar_r+0.5).extrude(front_plate_thick+0.5)
                                                    .translate(np_to_set(np.subtract(self.top_pillar_positions[0], self.hands_position)))
                                                    .translate((0,0, self.dial.thick + self.dial.support_length - front_plate_thick - 0.5)))






        # if this has a key (do after we've calculated the dial z)
        if (self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key) or not self.weight_driven:
            self.calc_winding_key_info()


        self.front_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)

        self.moon_holder = None

        if self.moon_complication is not None:
            self.moon_holder = MoonHolder(self, self.moon_complication, self.motion_works_screws)

        #cache stuff that's needed multiple times to speed up generating clock
        self.fixing_screws_cutter = None
        self.need_motion_works_holder = self.calc_need_motion_works_holder()


        self.texts = [
            self.name,
            "{}".format(datetime.date.today().strftime('%Y-%m-%d')),
            "Luke Wallin",
            "{:.1f}cm".format(self.going_train.pendulum_length * 100)
        ]
    def get_rod_lengths(self):
        '''
        TODO
        returns ([rod lengths, in same order as all_pillar_positions] , [base of rod z])
        '''
        return ([], [])

    def generate_arbours_for_plate(self):

        self.arbors_for_plate = []

        print("Plate distance", self.plate_distance)

        #configure stuff for the arbours, now we know their absolute positions
        # poweredWheel=self.goingTrain.getArbourWithConventionalNaming(0)
        # poweredWheelBracingR = poweredWheel.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(1).getMaxRadius() - self.gearGap
        #
        # #no need for it to be massive
        # poweredWheelBracingR = min(10,poweredWheelBracingR)
        # poweredWheel.setArbourExtensionInfo(rearSide=self.bearingPositions[0][2], maxR=poweredWheelBracingR)

        for i,bearingPos in enumerate(self.bearing_positions):
            arbour = self.going_train.get_arbour_with_conventional_naming(i)
            if i < self.going_train.wheels + self.going_train.powered_wheels - 2:
                maxR = arbour.distance_to_next_arbour - self.going_train.get_arbour_with_conventional_naming(i + 1).get_max_radius() - self.small_gear_gap
            else:
                maxR = 0

            #deprecated way of doing it - passing loads of info to the Arbour class. still used only for the chain wheel
            # arbour.setPlateInfo(rearSideExtension=bearingPos[2], maxR=maxR, frontSideExtension=self.plateDistance - self.endshake - bearingPos[2] - arbour.getTotalThickness(),
            #                     frontPlateThick=self.getPlateThick(back=False), pendulumSticksOut=self.pendulumSticksOut, backPlateThick=self.getPlateThick(back=True), endshake=self.endshake,
            #                     plateDistance=self.plateDistance, escapementOnFront=self.escapementOnFront)

            try:
                bearing = get_bearing_info(arbour.arbor_d)
            except:
                #mega bodge, TODO
                #for the spring barrel the arbor isn't a threaded rod, so isn't a nice number for a bearing.
                #need to work out what to do properly here
                bearing = get_bearing_info(round(arbour.arbor_d))
            front_anchor_from_plate = -1

            if self.escapement_on_front:
                if self.has_vanity_plate:
                    front_anchor_from_plate = self.vanity_plate_base_z + self.vanity_plate_thick + self.endshake + 2
                if self.going_train.escapement.get_anchor_thick() < 10:
                    #this won't be thick enough for the escape wheel to have much of a cylinder to grip the rod - so it might be wonky.
                    #so stick the esacpement out a bit further#
                    front_anchor_from_plate = 10


            #new way of doing it, new class for combining all this logic in once place
            arbourForPlate = ArborForPlate(arbour, self, bearing_position=bearingPos, arbour_extension_max_radius=maxR, pendulum_sticks_out=self.pendulum_sticks_out,
                                           pendulum_at_front=self.pendulum_at_front, bearing=bearing, escapement_on_front=self.escapement_on_front, back_from_wall=self.back_plate_from_wall,
                                           endshake=self.endshake, pendulum_fixing=self.pendulum_fixing, direct_arbor_d=self.direct_arbor_d, crutch_space=self.crutch_space,
                                           previous_bearing_position=self.bearing_positions[i - 1], front_anchor_from_plate=front_anchor_from_plate)
            self.arbors_for_plate.append(arbourForPlate)


    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        Calculate (and set) topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide, reduce_bottom_pillar_height
        '''


        bearingInfo = get_bearing_info(self.arbor_d)
        # width of thin bit
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        if self.heavy or self.extra_heavy:
            self.plate_width *= 1.2

        # original thinking was to make it the equivilant of a 45deg shelf bracket, but this is massive once cord wheels are used
        # so instead, make it just big enough to contain the holes for the chains/cord
        if self.weight_driven :
            furthest_x = max([abs(holePos[0][0]) for holePos in self.going_train.powered_wheel.get_chain_positions_from_top()])

            # juuust wide enough for the small bits on the edge of the bottom pillar to print cleanly
            min_distance_for_chain_holes = (furthest_x * 2 + self.chain_hole_d + 5) / 2
        else:
            min_distance_for_chain_holes = 0

        if self.heavy:
            self.bottom_pillar_r = self.plate_distance / 2
        else:
            self.bottom_pillar_r = min_distance_for_chain_holes

        if self.bottom_pillar_r < self.plate_width/2:
            #rare, but can happen
            self.bottom_pillar_r = self.plate_width / 2

        self.reduce_bottom_pillar_height = 0
        if self.bottom_pillar_r < min_distance_for_chain_holes and self.chainThroughPillar:
            if self.allow_bottom_pillar_height_reduction:
                self.reduce_bottom_pillar_height = min_distance_for_chain_holes - self.bottom_pillar_r
            self.bottom_pillar_r = min_distance_for_chain_holes

        #I've needed to reprint pillars more than I would like, this helps when changing endshake
        if override_bottom_pillar_r > 0:
            self.bottom_pillar_r = override_bottom_pillar_r

        print("bottom pillar r: {}".format(self.bottom_pillar_r))

        if self.narrow_bottom_pillar:
            self.bottom_pillar_height = self.bottom_pillar_r * 2
            # I hadn't measured an m4 nut, and now I've printed half the clock!
            #TODO fix this later!
            self.bottom_pillar_width = 14.46854441470986
            # self.bottom_pillar_width = self.fixingScrews.get_nut_containing_diameter() + 5
            print("bottom_pillar_width", self.bottom_pillar_width)

        self.top_pillar_r = self.plate_width / 2

        anchorSpace = bearingInfo.outer_d / 2 + self.gear_gap
        if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS:
            anchorSpace = self.direct_arbor_d*2 + self.gear_gap

        # find the Y position of the bottom of the top pillar
        topY = self.bearing_positions[0][1]
        if self.gear_train_layout == GearTrainLayout.ROUND:
            # find the highest point on the going train
            # TODO for potentially large gears this might be lower if they're spaced right
            for i in range(len(self.bearing_positions) - 1):
                y = self.bearing_positions[i][1] + self.going_train.get_arbour_with_conventional_naming(i).get_max_radius() + self.gear_gap
                if y > topY:
                    topY = y
        else:

            topY = self.bearing_positions[-1][1] + max(self.arbors_for_plate[-1].get_max_radius(above=True), bearingInfo.outer_d / 2) + self.gear_gap

        if self.bottom_pillars > 1:
            #TODO optimal placement of pillars, for now let's just get them working
            # #take into account the chain wheel might not be directly below the minute wheel
            # from_lowest_wheel = self.arboursForPlate[0].arbour.getMaxRadius() + self.bottomPillarR + self.gearGap
            # from_next_wheel = self.arboursForPlate[1].arbour.getMaxRadius() + self.bottomPillarR + self.gearGap
            # between_wheels = np.linalg.norm(np.subtract(self.bearingPositions[0][:2], self.bearingPositions[1][:2]))
            pillar_width = self.bottom_pillar_width if self.narrow_bottom_pillar else self.bottom_pillar_r * 2
            chain_wheel_r = self.arbors_for_plate[0].arbor.get_max_radius() + self.gear_gap
            self.bottom_pillar_positions=[
                (self.bearing_positions[0][0] - (chain_wheel_r + pillar_width / 2), self.bearing_positions[0][1]),
                (self.bearing_positions[0][0] + (chain_wheel_r + pillar_width / 2), self.bearing_positions[0][1]),
            ]
        else:
            self.bottom_pillar_positions = [[self.bearing_positions[0][0], self.bearing_positions[0][1] - self.powered_wheel_r - self.bottom_pillar_r + self.reduce_bottom_pillar_height]]
        
        self.top_pillar_positions = [(self.bearing_positions[0][0], topY + self.top_pillar_r)]

        if self.bottom_pillars > 1 and self.huygens_maintaining_power:
            raise ValueError("Don't currently support huygens with multiple bottom pillars")
        self.huygens_wheel_pos = self.bottom_pillar_positions[0]

    def calc_fixing_info(self):
        # fixing positions to plates and pillars together
        self.plate_top_fixings = []
        # (self.top_pillar_positions[0] - self.top_pillar_r / 2, self.top_pillar_positions[1]), (self.top_pillar_positions[0] + self.top_pillar_r / 2, self.top_pillar_positions[1])]
        for top_pillar_pos in self.top_pillar_positions:
            self.plate_top_fixings += [
                (top_pillar_pos[0] - self.top_pillar_r / 2, top_pillar_pos[1]),
                (top_pillar_pos[0] + self.top_pillar_r / 2, top_pillar_pos[1])
            ]

        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottom_pillar_positions:
            self.plate_bottom_fixings += [
                (bottom_pillar_pos[0], bottom_pillar_pos[1] + self.bottom_pillar_r * 0.5 - self.reduce_bottom_pillar_height / 3),
                (bottom_pillar_pos[0], bottom_pillar_pos[1] - self.bottom_pillar_r * 0.5)
            ]
        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings


    def calc_bearing_positions(self):
        '''
        TODO, with an overhaul of GoingTrain this should layout the gears in 2D, then lay them out vertically
        GoingTrain should then be free from figuring out all the pinion in front/rear and front/back powered wheel stuff


        '''
        # if angles are not given, assume clock is entirely vertical, unless overriden by style below

        if self.angles_from_minute is None:
            # assume simple pendulum at top
            angle = math.pi / 2 if self.pendulum_at_top else math.pi / 2

            # one extra for the anchor
            self.angles_from_minute = [angle for i in range(self.going_train.wheels + 1)]
        if self.angles_from_chain is None:
            angle = math.pi / 2 if self.pendulum_at_top else -math.pi / 2

            self.angles_from_chain = [angle for i in range(self.going_train.powered_wheels)]

        if self.gear_train_layout == GearTrainLayout.COMPACT:
            '''
            idea for even more compact: in a loop guess at the first angle, then do all the next angles such that it's as compact as possible without the wheels touching each other
            then see if it's possible to put the pendulum directly above the hands
            if it's not, tweak the first angle and try again
            
            current implementation: a line of gears vertically and then every other gear is just off to one side
            Not sure if peak compactness but keeps the plate design easier
            '''
            # if self.goingTrain.chainWheels > 0:

            #thoughts: make which side the gears stick out adjustable?
            on_side = +1

            if self.compact_zigzag:
                on_side = -1
            '''
            Have a line of gears vertical from hands to anchor, and any gears in between off to one side
            '''


            if self.going_train.powered_wheels == 2:
                first_powered_wheel_to_second_powered_wheel = self.going_train.get_arbour_with_conventional_naming(0).distance_to_next_arbour
                second_powered_wheel_to_minute_wheel = self.going_train.get_arbour_with_conventional_naming(1).distance_to_next_arbour
                first_powered_wheel_to_minute_wheel = self.going_train.get_arbour_with_conventional_naming(0).get_max_radius() + self.going_train.get_arbour_with_conventional_naming(2).pinion.get_max_radius() + self.small_gear_gap
                b = first_powered_wheel_to_second_powered_wheel
                c = second_powered_wheel_to_minute_wheel
                a = first_powered_wheel_to_minute_wheel
                # cosine law
                angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
                self.angles_from_chain[0] = math.pi / 2 + on_side * angle
                minute_wheel_relative_pos = (0,first_powered_wheel_to_minute_wheel)
                second_powered_wheel_pos =  polar(self.angles_from_chain[0], first_powered_wheel_to_second_powered_wheel)
                minute_wheel_from_second_powered_wheel = np_to_set(np.subtract(minute_wheel_relative_pos, second_powered_wheel_pos))
                self.angles_from_chain[1] = math.atan2(minute_wheel_from_second_powered_wheel[1], minute_wheel_from_second_powered_wheel[0])
                if self.compact_zigzag:
                    on_side *= -1

            '''
            4 wheels and escape wheel would not be directly above hands using above logic
            Place the escape wheel directly above the hands and then put the second and third wheel off to the side
            Trying putting the third wheel directly left of the escape wheel and using the normal compact logic to place the second wheel
            
            
            PLAN: when we don't have a second hand or need escapement above the hands we can do compact with 4 wheels better:
            basically rotate the third wheel and escape wheel around slightly to the right so they're both equidistant from the line above the hands
            this will be useful for the moon escapement (so the fixing doesn't clash with a bearing) and I think will result in an even more compact design
            '''
            forcing_escape_wheel_above_hands = self.going_train.wheels > 3 and self.force_escapement_above_hands
            forcing_escape_wheel_slightly_off_centre = self.going_train.wheels > 3 and not self.second_hand



            #if we're forcing the escapement above the hands and have more than 3 wheels, we don't want to default to this logic as the escape wheel
            #will be off to one side
            #if we do have 3 wheels then the escape wheel is above the hands
            minute_wheel_to_second_wheel = self.going_train.get_arbor(0).distance_to_next_arbour
            second_wheel_to_third_wheel = self.going_train.get_arbor(1).distance_to_next_arbour

            third_wheel_pinion_r = self.going_train.get_arbor(2).pinion.get_max_radius()
            #bit of hackery here, we should really work out exactly where all the pinions and wheels will line up, then we don't need to guess
            if self.going_train.get_arbor(1).pinion_extension > 0:
                #...this is guessing how thick the arbor extension will be, which is calcualted in ArborForPlate. TODO
                third_wheel_pinion_r = self.going_train.get_arbor(2).arbor_d

            minute_wheel_to_third_wheel = self.going_train.get_arbor(0).get_max_radius() + third_wheel_pinion_r + self.small_gear_gap
            minute_wheel_pos = (0, 0)
            if forcing_escape_wheel_above_hands or forcing_escape_wheel_slightly_off_centre:
                minute_wheel_r = self.going_train.get_arbor(0).get_max_radius()
                escape_wheel_arbor_r = self.going_train.get_arbor(3).get_arbor_extension_r()
                # #HACK HACK HACK TEMP instead of self.going_train.get_arbor(3).get_arbor_extension_r() use the old value of 2
                # escape_wheel_arbor_r = self.going_train.get_arbor(3).get_rod_d()
                # #MORE HACK TODO REMOVE ME
                # escape_wheel_arbor_r = 2
                minute_wheel_to_escape_wheel = self.going_train.get_arbor(0).get_max_radius() + escape_wheel_arbor_r + self.small_gear_gap
                third_wheel_to_escape_wheel = self.going_train.get_arbor(2).distance_to_next_arbour
                escape_wheel_to_anchor = self.going_train.get_arbor(3).distance_to_next_arbour

                if forcing_escape_wheel_slightly_off_centre:
                    escape_wheel_angle_from_hands = math.pi/2 - on_side*math.asin((third_wheel_to_escape_wheel/2)/minute_wheel_to_escape_wheel)
                    escape_wheel_relative_pos = polar(escape_wheel_angle_from_hands, minute_wheel_to_escape_wheel)
                    #arbitarily choosing mirror of escape wheel
                    third_wheel_pos = (-escape_wheel_relative_pos[0], escape_wheel_relative_pos[1])
                    # anchor is directly above minutes
                    #TODO does htis work if we're on the right hand side?
                    self.angles_from_minute[3] = math.pi - on_side*math.acos(escape_wheel_relative_pos[0]/escape_wheel_to_anchor)
                else:


                    escape_wheel_relative_pos = (0, minute_wheel_to_escape_wheel)

                    third_wheel_pos = ( -on_side*third_wheel_to_escape_wheel, minute_wheel_to_escape_wheel)
                    # anchor is directly above escape wheel
                    self.angles_from_minute[3] = math.pi / 2


                minute_wheel_to_third_wheel = distance_between_two_points(minute_wheel_pos, third_wheel_pos)
                #escape wheel is directly right of third wheel
                self.angles_from_minute[2] = math.pi if on_side < 0 else 0
            else:
                third_wheel_pos = (0, minute_wheel_to_third_wheel)

            #this is the same regardless of forcing_escape_wheel_location, only the position of the third wheel changes
            b = minute_wheel_to_second_wheel
            c = second_wheel_to_third_wheel
            a = minute_wheel_to_third_wheel
            # cosine law
            angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))

            # third_wheel_line = Line(minute_wheel_pos, anotherPoint=third_wheel_pos)
            # self.angles_from_minute[0] = third_wheel_line.getAngle() + on_side * angle
            third_wheel_angle = math.atan2(third_wheel_pos[1], third_wheel_pos[0])
            self.angles_from_minute[0] = third_wheel_angle + on_side * angle

            if self.compact_zigzag:
                on_side *= -1

            second_wheel_pos = polar(self.angles_from_minute[0], minute_wheel_to_second_wheel)
            third_wheel_from_second_wheel = np_to_set(np.subtract(third_wheel_pos, second_wheel_pos))
            self.angles_from_minute[1] = math.atan2(third_wheel_from_second_wheel[1], third_wheel_from_second_wheel[0])



            #TODO if the second wheel would clash with the powered wheel, push the third wheel up higher
            #
            if self.going_train.wheels > 3 and not (forcing_escape_wheel_above_hands or forcing_escape_wheel_slightly_off_centre):
                #stick the escape wheel out too
                third_wheel_to_escape_wheel = self.going_train.get_arbor(2).distance_to_next_arbour
                escape_wheel_to_anchor = self.going_train.get_arbor(3).distance_to_next_arbour
                #third_wheel_to_anchor is a bit tricky to calculate. going to try instead just choosing an angle
                #TODO could make anchor thinner and then it just needs to avoid the rod
                third_wheel_to_anchor = self.going_train.get_arbour_with_conventional_naming(-1).get_max_radius() + self.going_train.get_arbor(2).get_max_radius() + self.small_gear_gap

                b = third_wheel_to_escape_wheel
                c = escape_wheel_to_anchor
                a = third_wheel_to_anchor
                # cosine law
                angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
                self.angles_from_minute[2] = math.pi / 2 + on_side * angle

                # #choosing an angle manually:
                # self.anglesFromMinute[2] = math.pi/2 + on_side*self.goingTrain.escapement.escaping_arc*4

                escape_wheel_pos = polar(self.angles_from_minute[2], third_wheel_to_escape_wheel)
                angle = math.acos(abs(escape_wheel_pos[0])/escape_wheel_to_anchor)
                angle = abs(math.pi/2 - angle)
                self.angles_from_minute[3] = math.pi/2 - on_side*angle



            #aim: have pendulum directly above hands
            positions = [(0,0)]
            for i in range(1, self.going_train.wheels):
                positions.append(np_to_set(np.add(positions[i - 1], polar(self.angles_from_minute[i - 1], self.going_train.get_arbor(i - 1).distance_to_next_arbour))))

            escape_wheel_to_anchor = self.going_train.get_arbor(-2).distance_to_next_arbour
            if escape_wheel_to_anchor < abs(positions[-1][0]):
                #need to re-think how this works
                raise ValueError("Cannot put anchor above hands without tweaking")

            if self.bottom_pillars > 1 and not self.using_pulley and self.going_train.powered_wheels > 0 and self.centre_weight:
                #put chain in the centre. this works (although lots of things assume the bottom bearing is in the centre)
                #but I'm undecided if I actually want it - if we have two screwholes is that sufficient? the reduction in height is minimal
                x = self.going_train.powered_wheel.diameter / 2
                r = self.going_train.get_arbour_with_conventional_naming(0).distance_to_next_arbour
                angle = math.acos(x/r)
                if self.weight_on_right_side:
                    self.angles_from_chain[0] = math.pi - angle
                else:
                    self.angles_from_chain[0] = angle



        if self.gear_train_layout == GearTrainLayout.ROUND:

            # TODO decide if we want the train to go in different directions based on which side the weight is
            self.hands_on_side = -1 if self.going_train.is_weight_on_the_right() else 1
            arbours = [self.going_train.get_arbour_with_conventional_naming(arbour) for arbour in range(self.going_train.wheels + self.going_train.powered_wheels)]
            distances = [arbour.distance_to_next_arbour for arbour in arbours]
            maxRs = [arbour.get_max_radius() for arbour in arbours]
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
                    self.compact_radius = arcRadius
                else:
                    arcAngleDeg -= 1
            if not foundSolution:
                raise ValueError("Unable to calculate radius for gear ring, try a vertical clock instead")

            angleOnArc = -math.pi / 2
            lastPos = polar(angleOnArc, arcRadius)

            for i in range(-self.going_train.powered_wheels, self.going_train.wheels):
                '''
                Calculate angle of the isololese triangle with the distance at the base and radius as the other two sides
                then work around the arc to get the positions
                then calculate the relative angles so the logic for finding bearing locations still works
                bit over complicated
                '''
                # print("angle on arc: {}deg".format(radToDeg(angleOnArc)))
                nextAngleOnArc = angleOnArc + 2 * math.asin(distances[i + self.going_train.powered_wheels] / (2 * arcRadius)) * self.hands_on_side
                nextPos = polar(nextAngleOnArc, arcRadius)

                relativeAngle = math.atan2(nextPos[1] - lastPos[1], nextPos[0] - lastPos[0])
                if i < 0:
                    self.angles_from_chain[i + self.going_train.powered_wheels] = relativeAngle
                else:
                    self.angles_from_minute[i] = relativeAngle
                lastPos = nextPos
                angleOnArc = nextAngleOnArc

        # [[x,y,z],]
        # for everything, arbours and anchor
        self.bearing_positions = []
        # TODO consider putting the anchor on a bushing
        # self.bushingPositions=[]
        self.arbourThicknesses = []

        # height of the centre of the wheel that will drive the next pinion
        drivingZ = 0
        for i in range(-self.going_train.powered_wheels, self.going_train.wheels + 1):
            # print(str(i))
            if i == -self.going_train.powered_wheels:
                # the wheel with chain wheel ratchet
                # assuming this is at the very back of the clock
                # note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearing_positions.append(pos)
                # note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.going_train.get_arbor(i).get_wheel_centre_z()
                self.arbourThicknesses.append(self.going_train.get_arbor(i).get_total_thickness())
                # print("pinionAtFront: {} wheel {} drivingZ: {}".format(self.goingTrain.getArbour(i).pinionAtFront, i, drivingZ), pos)
            else:
                r = self.going_train.get_arbor(i - 1).distance_to_next_arbour
                # print("r", r)
                # all the other going wheels up to and including the escape wheel
                if i == self.going_train.wheels:
                    # the anchor
                    if self.escapement_on_front:
                        # there is nothing between the plates for this
                        self.arbourThicknesses.append(0)
                        # don't do anything else
                    else:
                        escapement = self.going_train.get_arbor(i).escapement
                        baseZ = drivingZ - self.going_train.get_arbor(i - 1).wheel_thick / 2 + escapement.get_wheel_base_to_anchor_base_z()
                        self.arbourThicknesses.append(escapement.get_anchor_thick())
                    # print("is anchor")
                else:
                    # any of the other wheels
                    # pinionAtBack = not pinionAtBack
                    # print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(), self.goingTrain.getArbour(i).getPinionCentreZ()))
                    pinionToWheel = self.going_train.get_arbor(i).get_pinion_to_wheel_z()
                    pinionZ = self.going_train.get_arbor(i).get_pinion_centre_z()
                    baseZ = drivingZ - pinionZ

                    drivingZ = drivingZ + pinionToWheel
                    # massive bodge here, the arbour doesn't know about the escapement being on the front yet
                    self.going_train.get_arbor(i).escapement_on_front = self.escapement_on_front
                    arbourThick = self.going_train.get_arbor(i).get_total_thickness()

                    self.arbourThicknesses.append(arbourThick)

                if i <= 0:
                    angle = self.angles_from_chain[i - 1 + self.going_train.powered_wheels]
                else:
                    angle = self.angles_from_minute[i - 1]
                v = polar(angle, r)
                # v = [v[0], v[1], baseZ]
                lastPos = self.bearing_positions[-1]
                # pos = list(np.add(self.bearingPositions[i-1],v))
                pos = [lastPos[0] + v[0], lastPos[1] + v[1], baseZ]
                # if i < self.goingTrain.wheels:
                #     print("pinionAtFront: {} wheel {} r: {} angle: {}".format( self.goingTrain.getArbour(i).pinionAtFront, i, r, angle), pos)
                # print("baseZ: ",baseZ, "drivingZ ", drivingZ)

                self.bearing_positions.append(pos)

        # print(self.bearingPositions)

        topZs = [self.arbourThicknesses[i] + self.bearing_positions[i][2] for i in range(len(self.bearing_positions))]

        bottomZs = [self.bearing_positions[i][2] for i in range(len(self.bearing_positions))]

        bottomZ = min(bottomZs)
        if bottomZ < 0:
            # positions are relative (chain at front), so readjust everything
            topZs = [z - bottomZ for z in topZs]
            # bottomZs = [z - bottomZ for z in bottomZs]
            for i in range(len(self.bearing_positions)):
                self.bearing_positions[i][2] -= bottomZ

        '''
        something is always pressed up against both the front and back plate. If it's a powered wheel that's designed for that (the chain/rope wheel is designed to use a washer,
        and the key-wound cord wheel is specially shaped) then that's not a problem.

        However if it's just a pinion (or a wheel - somehow?), or and anchor (although this should be avoided now by choosing where it goes) then that's extra friction

        TODO - I assumed that the chainwheel was alays the frontmost or backmost, but that isn't necessarily true.
        '''
        needExtraFront = False
        needExtraBack = False

        preliminaryPlateDistance = max(topZs)
        for i in range(len(self.bearing_positions)):
            # check front plate
            canIgnoreFront = False
            canIgnoreBack = False
            if self.going_train.get_arbour_with_conventional_naming(i).get_type() == ArborType.POWERED_WHEEL:
                if self.going_train.chain_at_back:
                    canIgnoreBack = True
                else:
                    # this is the part of the chain wheel with a washer, can ignore
                    canIgnoreFront = True
            # topZ = self.goingTrain.getArbourWithConventionalNaming(i).getTotalThickness() + self.bearingPositions[i][2]
            if topZs[i] >= preliminaryPlateDistance - LAYER_THICK * 2 and not canIgnoreFront:
                # something that matters is pressed up against the top plate
                # could optimise to only add the minimum needed, but this feels like a really rare edgecase and will only gain at most 0.4mm
                needExtraFront = True

            if self.bearing_positions[i][2] == 0 and not canIgnoreBack:
                needExtraBack = True

        extraFront = 0
        extraBack = 0
        if needExtraFront:
            extraFront = LAYER_THICK * 2
        if needExtraBack:
            extraBack = LAYER_THICK * 2

        for i in range(len(self.bearing_positions)):
            self.bearing_positions[i][2] += extraBack

        # print(self.bearingPositions)
        self.plate_distance = max(topZs) + self.endshake + extraFront + extraBack

    def bottom_of_hour_hand_z(self):
        '''
        relative to the front of the front plate
        '''
        return self.motion_works.get_hand_holder_height() + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base

    def front_of_motion_works_wheels_z(self):
        '''
        relative to the front of the front plate
        the closest something like a vanity plate could be to the front of the clock without causing problems for the motion works
        '''
        return TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base + self.motion_works.get_wheels_thick()

    def front_plate_has_flat_front(self):
        '''
        If there's nothing sticking out of the front plate it can be printed the other way up - better front surface and no hole-in-hole needed for bearings
        '''
        if self.pendulum_at_front and self.pendulum_sticks_out > 0:
            #arm that holds the bearing (old designs)
            return False
        if self.style in [PlateStyle.RAISED_EDGING]:
            return False

        if self.huygens_maintaining_power:
            #ratchet is on the front
            return False
        return True

    def get_seconds_hand_position(self):
        if self.centred_second_hand:
            return self.hands_position.copy()

        if self.going_train.has_seconds_hand_on_escape_wheel():
            return self.bearing_positions[-2][:2]

        if self.going_train.has_second_hand_on_last_wheel():
            #wheel before the escape wheel
            return self.bearing_positions[-3][:2]
        return None

    def has_seconds_hand(self):
        return self.second_hand and (self.going_train.has_seconds_hand_on_escape_wheel() or self.going_train.has_second_hand_on_last_wheel())

    def need_front_anchor_bearing_holder(self):
        #no longer supporting anything that doesn't (with the escapement on the front) - the large bearings have way too much friction so we have to hold the anchor arbour from both ends
        return self.escapement_on_front# and self.pendulumFixing == PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

    def get_front_anchor_bearing_holder_total_length(self, bearing_holder_thick=-1):
        '''
        full length (including bit that holds bearing) of the peice that sticks out the front of the clock to hold the bearing for a front mounted escapment
        '''
        if bearing_holder_thick < 0:
            bearing_holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arbors_for_plate[-1].bearing)

        if self.need_front_anchor_bearing_holder():
            holder_long = self.arbors_for_plate[-1].front_anchor_from_plate + self.arbors_for_plate[-1].arbor.escapement.get_anchor_thick() \
                          + bearing_holder_thick + SMALL_WASHER_THICK_M3
        else:
            holder_long = 0
        return holder_long


    @staticmethod
    def get_lone_anchor_bearing_holder_thick(bearing = None):
        '''
        static so it can be used to adjust the thickness of the frame
        '''
        if bearing is None:
            bearing = get_bearing_info(3)
        return bearing.height + 1

    def get_front_anchor_bearing_holder(self, for_printing=True):

        holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arbors_for_plate[-1].bearing)

        pillar_tall = self.get_front_anchor_bearing_holder_total_length() - holder_thick
        if self.top_pillars > 1:
            raise ValueError("front anchor bearing holder only supports one top pillar TODO")
        holder = cq.Workplane("XY").moveTo(-self.top_pillar_r, self.top_pillar_positions[0][1]).radiusArc((self.top_pillar_r, self.top_pillar_positions[0][1]), self.top_pillar_r)\
            .lineTo(self.top_pillar_r, self.bearing_positions[-1][1]).radiusArc((-self.top_pillar_r, self.bearing_positions[-1][1]), self.top_pillar_r).close().extrude(holder_thick)

        holder = holder.union(cq.Workplane("XY").moveTo(self.top_pillar_positions[0][0], self.top_pillar_positions[0][1]).circle(self.plate_width / 2 + 0.0001).extrude(pillar_tall + holder_thick))


        holder = holder.cut(self.get_bearing_punch(holder_thick, bearing=get_bearing_info(self.arbors_for_plate[-1].arbor.arbor_d)).translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1])))
        #rotate into position to cut fixing holes
        holder = holder.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, pillar_tall + holder_thick))
        holder= holder.cut(self.get_fixing_screws_cutter().translate((0,0,-self.front_z)))

        if for_printing:
            #rotate back
            holder = holder.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, pillar_tall + holder_thick))
            holder = holder.translate(np_to_set(np.multiply(self.top_pillar_positions[0], -1)))
        else:
            holder = holder.translate((0,0, self.front_z))

        return holder



    def calc_need_motion_works_holder(self):
        '''
        If we've got a centred second hand then there's a chance that the motino works arbour lines up with another arbour, so there's no easy way to hold it in plnace
        in this case we have a separate peice that is given a long screw and itself screws onto the front of the front plate
        '''

        if self.gear_train_layout ==GearTrainLayout.VERTICAL and self.has_seconds_hand() and self.centred_second_hand:
            #potentially

            motion_works_arbour_y = self.motion_works_pos[1]

            for i,bearing_pos in enumerate(self.bearing_positions):
                #just x,y
                bearing_pos_y = bearing_pos[1]
                bearing = get_bearing_info(self.going_train.get_arbour_with_conventional_naming(i).arbor_d)
                screw = MachineScrew(3, countersunk=True)
                if abs(bearing_pos_y - motion_works_arbour_y) < bearing.outer_d/2 + screw.get_head_diameter()/2:
                    print("motion works holder would clash with bearing holder for arbour", i)
                    return True

        return False

    def get_cannon_pinion_friction_clip(self):
        '''
        holds two "brake pads" - experimental sprung peice that can add a small amount of friction to the cannon pinion so the minute hand
        doesn't have too much slack when the second hand is centred. Without it the minute hand is about 30s fast on the half past and 30s slow on the half to.
        '''
        centre_z = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base + self.endshake / 2 - self.motion_works.friction_ring_thick/2

        #thick here being height as printed
        clip_thick = self.motion_works.friction_ring_thick/2
        total_thick = centre_z + clip_thick/2

        clip_holder_r = self.plate_width/2

        clip = cq.Workplane("XY").circle(clip_holder_r).extrude(total_thick)



        cannon_pinion_relative_pos = np_to_set(np.subtract(self.hands_position, self.cannon_pinion_friction_clip_pos))
        from_holder_to_cannon_pinion = Line(self.cannon_pinion_friction_clip_pos, anotherPoint=self.hands_position)
        angle_to_cannon_pinion = from_holder_to_cannon_pinion.get_angle()

        arc = math.pi/4
        brake_angles = [angle_to_cannon_pinion+math.pi/2, angle_to_cannon_pinion - math.pi/2]
        angle_pairs = [[angle - arc/2, angle + arc/2, angle] for angle in brake_angles]
        brake_pads = cq.Workplane("XY")

        #needs to be thicker than arm
        brake_pad_thick = 3
        #not sure what to name this - this is how far "inside" the cannon pinion the brake pads want to be
        # brake_pad_offset = 1.5
        # #thick here being width of arm (strength of spring)
        # arm_thick = 1.5 #0.8 seemed a bit weedy
        brake_pad_offset = 1
        arm_thick = 2.4

        inner_r = self.motion_works.friction_ring_r# - brake_pad_offset
        outer_r = inner_r + brake_pad_thick

        for angles in angle_pairs:

            '''
            new plan:
            build brake pad in the post-bend position, then rotate it into the pre-bend position by rotating around the mid point of the arm
            
            then when printed and bent into position the brake pad should line up properly - ideally want it to just be clamping the 
            cannon pinion, not pushing it downwards
            '''

            start_inner = polar(angles[0], inner_r)
            start_outer = polar(angles[0], outer_r)
            end_inner = polar(angles[1], inner_r)
            end_outer = polar(angles[1], outer_r)

            outer_radius_arc = (self.motion_works.friction_ring_r + brake_pad_thick)
            #sagitta - the outside arc isn't the outside radius as the brake pads are built, only once bent into place
            l = distance_between_two_points(start_outer, end_outer)
            r = (self.motion_works.friction_ring_r + brake_pad_thick)
            sagitta_1 = r - math.sqrt(r**2 - 0.25*l**2)
            sagitta_2 = outer_r - math.sqrt(outer_r**2 - 0.25*l**2)

            #the arm is at an angle, so taking this isn't account doesn't make it perfectly line up with the tangent of the outside the brake pad anyway, but it looks
            #better than not doing it.
            arm_start = polar(angles[2], outer_r - arm_thick/2 - abs(sagitta_2 - sagitta_1))
            arm_finish = np_to_set(np.add(np.multiply(cannon_pinion_relative_pos, -1), polar(angles[2], clip_holder_r - arm_thick/2)))

            arm_centre = average_of_two_points(arm_start, arm_finish)

            brake_pad = (cq.Workplane("XY").moveTo(start_inner[0], start_inner[1]).radiusArc(end_inner, -self.motion_works.friction_ring_r).lineTo(end_outer[0], end_outer[1])
                     .radiusArc(start_outer, outer_radius_arc).close().extrude(clip_thick))

            half_arm_length = np.linalg.norm(np.subtract(arm_centre, arm_start))


            relative_angle = rationalise_angle(angles[2]) - rationalise_angle(angle_to_cannon_pinion)
            quad = get_quadrant(relative_angle)

            bend_angle = brake_pad_offset/half_arm_length

            # if quad[0] > 0:
            if relative_angle > 0:
                #which direction to rotate?
                bend_angle *= -1

            arm_start_bent = np_to_set(np.add(arm_start, polar(angles[2]+math.pi, brake_pad_offset)))

            brake_pad = brake_pad.rotate((arm_centre[0], arm_centre[1], 0), (arm_centre[0], arm_centre[1], 1), radToDeg(bend_angle))

            arm = get_stroke_line([arm_start_bent, arm_finish], wide=arm_thick, thick=clip_thick)
            brake_pad = brake_pad.union(arm)

            brake_pads = brake_pads.union(brake_pad.translate(cannon_pinion_relative_pos).translate((0,0,total_thick-clip_thick)))

        # arms = cq.Workplane("XY")
        # for x in [-1,1]:
        #     arms = arms.union(get_stroke_line([(x*(outer_r -arm_thick/2), ),]))


        clip = clip.union(brake_pads)

        #cutting out screws afterwards so they don't overlap with the arms
        for pos in self.cannon_pinion_friction_clip_fixings_pos:
            relative_pos = np_to_set(np.subtract(pos, self.cannon_pinion_friction_clip_pos))
            clip = clip.cut(self.motion_works_screws.get_cutter().rotate((0, 0, 0), (0, 1, 0), 180).translate((relative_pos[0], relative_pos[1], total_thick)))

        return clip

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
        holder = holder.faces(">Z").workplane().circle(self.motion_works_screws.metric_thread).extrude(standoff_thick)

        holder = holder.cut(self.motion_works_screws.get_cutter(with_bridging=True, layer_thick=self.layer_thick, for_tap_die=True))

        for pos in self.motion_works_fixings_relative_pos:
            holder = holder.cut(self.motion_works_screws.get_cutter().rotate((0, 0, 0), (0, 1, 0), 180).translate((pos[0], pos[1], holder_thick)))

        return holder


    def get_plate_thick(self, back=True, standoff=False):
        if standoff:
            #TODO separate value
            return self.plate_thick
        if back:
            return self.back_plate_thick
        return self.plate_thick

    def get_plate_distance(self):
        '''
        how much space there is between the front and back plates
        '''
        return self.plate_distance

    def get_front_z(self):
        return self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance

    def get_screwhole_positions(self):
        '''
        returns [(x,y, supported),]
        for where the holes to fix the clock to the wall will be

        The older logic (when there is no wall standoff) is a bit of a mess, it was pulled out of the tangle in clock plates and could do with tidying up
        '''
        if self.back_plate_from_wall > 0:

            slotLength = 7

            # just above the pillar
            # TODO consider putting the screwhole INSIDE the pillar?
            topScrewHolePos = (self.bearing_positions[-1][0], self.top_pillar_positions[0][1] + self.top_pillar_r + self.wall_fixing_screw_head_d / 2 + slotLength)

            if self.bottom_pillars == 1:
                bottomScrewHolePos = (0, self.bottom_pillar_positions[0][1] + self.bottom_pillar_r + self.wall_fixing_screw_head_d / 2 + slotLength)
            else:
                bottomScrewHolePos = (0, self.bottom_pillar_positions[0][1])

            if self.heavy or True:
                return [topScrewHolePos, bottomScrewHolePos]
            else:
                return [topScrewHolePos]


        else:
            #old messy logic

            bottomScrewHoleY = self.bearing_positions[0][1] + (self.bearing_positions[1][1] - self.bearing_positions[0][1]) * 0.6

            extraSupport = True
            if self.using_pulley and self.heavy:
                # the back plate is wide enough to accomodate
                extraSupport = False

            weightX = 0
            weightOnSide = 1 if self.weight_on_right_side else -1
            if self.heavy and not self.using_pulley:
                # line up the hole with the big heavy weight
                weightX = weightOnSide * self.going_train.powered_wheel.diameter / 2

            if self.gear_train_layout == GearTrainLayout.ROUND:
                #screwHoleY = chainWheelR * 1.4
                #raise NotImplementedError("Haven't fixed this for round clocks")
                print("TODO: fix screwholes for round clocks properly")
                return [(weightX, self.compact_radius, True)]

            elif self.gear_train_layout == GearTrainLayout.VERTICAL:
                if self.extra_heavy:

                    # below anchor
                    topScrewHoleY = self.bearing_positions[-2][1] + (self.bearing_positions[-1][1] - self.bearing_positions[-2][1]) * 0.6
                    return [(weightX, bottomScrewHoleY, extraSupport), (weightX, topScrewHoleY, True)]
                else:
                    # just below anchor
                    screwHoleY = self.bearing_positions[-2][1] + (self.bearing_positions[-1][1] - self.bearing_positions[-2][1]) * 0.6

                    return [(weightX, screwHoleY, extraSupport)]

    def get_drill_template(self, drillHoleD=7, layer_thick=LAYER_THICK_EXTRATHICK):

        screwHoles = self.get_screwhole_positions()

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
        # text = cq.Workplane("XY").text(txt=self.name, fontsize=int(minWidth*0.5), distance=LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotate((0,0,0), (0,0,1),90).translate((0,0,thick))
        text = cq.Workplane("XY").text(self.name, fontsize=width*0.5, distance=layer_thick, cut=False, halign='center', valign='center', kind="bold").rotate((0, 0, 0), (0, 0, 1), 90).translate(((minX + maxX)/2, (minY + maxY)/2, thick))
        template = template.add(text)

        return template

    def cut_anchor_bearing_in_standoff(self, standoff):
        bearingInfo = self.arbors_for_plate[-1].bearing


        standoff = standoff.cut(self.getBearingPunchDeprecated(bearingOnTop=True, standoff=True, bearingInfo=bearingInfo).translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1], 0)))

        return standoff

    def get_wall_standoff(self, top=True, for_printing=True):
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

        pillarPositions = self.top_pillar_positions if top else self.bottom_pillar_positions
        pillarR = self.top_pillar_r if top else self.bottom_pillar_r

        pillarWallThick = 2
        pillarInnerR = pillarR-pillarWallThick

        standoff = cq.Workplane("XY").tag("base")

        back_thick = self.get_plate_thick(standoff=True)
        screwhole_back_thick = back_thick - 2
        if top:
            #assuming 1 pillar fow now


            standoff = standoff.add(self.get_pillar(top=top, flat=True).extrude(self.back_plate_from_wall).translate(pillarPositions[0]))
        else:
            if self.bottom_pillars > 1:
                # make back thinner, not needed for strength so much as stability
                back_thick = 5
                screwhole_back_thick = back_thick
                for pillarPos in pillarPositions:
                    standoff = standoff.union(self.get_pillar(top=top, flat=True).extrude(self.back_plate_from_wall).translate(pillarPos))
                standoff = standoff.union(get_stroke_line(pillarPositions, wide=pillarR, thick=back_thick, style=StrokeStyle.SQUARE))


            else:
                #round works fine, no need to copy the heavy duty lower pillar
                standoff = standoff.moveTo(pillarPositions[0][0], pillarPositions[0][1]).circle(pillarR).extrude(self.back_plate_from_wall)


        if top or self.heavy or True:

            #screwholes to hang on wall
            #originally only at the top, but now I think put them everywhere
            # #TODO consider putting the screwhole INSIDE the pillar?

            if top:
                screwHolePos = self.get_screwhole_positions()[0]
            else:
                #bottom pillar, heavy
                screwHolePos = self.get_screwhole_positions()[1]

            screwHoleSupportR = self.top_pillar_r  # (self.wallFixingScrewHeadD + 6)/2

            addExtraSupport = False

            #extend a back plate out to the screwhole
            if len(pillarPositions) == 1:
                screwhole_support_start = pillarPositions[0]
                standoff = standoff.union(get_stroke_line([screwhole_support_start, screwHolePos], wide=self.plate_width, thick=back_thick))
            else:
                #we have two pillars and the screwhole is in the link between them
                addExtraSupport = True

            #can't decide if to add backThick or not - it recesses the screw which looks nice in some situations but not convinced for teh standoff
            standoff = self.cut_wall_fixing_hole(standoff, screwHolePos, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=addExtraSupport, plate_thick=back_thick)#, backThick=screwhole_back_thick)

            if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING] and top:
                # extend a back plate out to the bearing holder and wall fixing
                #note assumes one top pillar, might not work with two
                bearingHolder = cq.Workplane("XY").tag("base").moveTo((screwHolePos[0] + self.bearing_positions[-1][0]) / 2, (self.bearing_positions[-1][1] + self.top_pillar_positions[0][1]) / 2). \
                    rect(self.top_pillar_r * 2, self.top_pillar_positions[0][1] - self.bearing_positions[-1][1]).extrude(self.rear_standoff_bearing_holder_thick)
                bearingHolder = bearingHolder.workplaneFromTagged("base").moveTo(self.bearing_positions[-1][0], self.bearing_positions[-1][1]).circle(screwHoleSupportR).extrude(self.rear_standoff_bearing_holder_thick)
                bearingHolder = self.cut_anchor_bearing_in_standoff(bearingHolder)

                z = 0
                if self.pendulum_fixing == PendulumFixing.SUSPENSION_SPRING:
                    #TODO
                    z = self.back_plate_from_wall - self.crutch_space - self.rear_standoff_bearing_holder_thick - self.endshake
                standoff = standoff.union(bearingHolder.translate((0,0,z)))

        #we're currently not in the right z position
        standoff = standoff.cut(self.get_fixing_screws_cutter().translate((0,0,self.back_plate_from_wall)))

        if for_printing:
            if not top:
                standoff = standoff.rotate((0,0,0), (1,0,0), 180)
            standoff = standoff.translate((-pillarPositions[0][0], -pillarPositions[0][1]))
        else:
            standoff = standoff.translate((0,0,-self.back_plate_from_wall))

        return standoff

    def get_text(self, top_standoff=False):

        all_text = cq.Workplane("XY")

        # (x,y,width,height, horizontal)
        spaces = self.get_text_spaces()

        max_text_size = min([textSpace.get_text_max_size() for textSpace in spaces])

        for space in spaces:
            space.set_size(max_text_size)
        any_text = False
        for space in spaces:
            if self.text_on_standoffs:
                if top_standoff and space.y < self.hands_position[1]:
                    continue
                if not top_standoff and space.y > self.hands_position[1]:
                    continue

            all_text = all_text.add(space.get_text_shape())
            any_text = True

        if not any_text:
            #would fail to cut shapes below and everything assumes text exists
            raise ValueError("No text available, something has gone wrong")

        if self.text_on_standoffs:
            all_text = all_text.cut(self.get_fixing_screws_cutter().translate((0,0,self.back_plate_from_wall)))
            all_text = all_text.translate((0, 0, -self.back_plate_from_wall))
        else:
            all_text = self.punch_bearing_holes(all_text, back=True, make_plate_bigger=False)



        return all_text

    def get_text_spaces(self):
        '''
        get a list of TextSpace objects with text assigned
        '''

        texts = self.texts

        #(x,y,width,height, horizontal)
        spaces = []



        if self.bottom_pillars > 1:
            #along the bottom of the plate between the two pillars

            pillar_wide_half = self.bottom_pillar_width / 2 if self.narrow_bottom_pillar else self.bottom_pillar_r
            bearing_wide_half = self.arbors_for_plate[0].bearing.outer_d / 2

            for pillarPos in self.bottom_pillar_positions:

                if pillarPos[0] > 0:
                    offset = bearing_wide_half - pillar_wide_half
                else:
                    offset = -(bearing_wide_half - pillar_wide_half)

                spaces.append(TextSpace(pillarPos[0] / 2 + offset, pillarPos[1] + self.bottom_pillar_height/4, abs(pillarPos[0]) - pillar_wide_half - bearing_wide_half, self.bottom_pillar_height, horizontal=True))
                spaces.append(TextSpace(pillarPos[0] / 2 + offset, pillarPos[1] - self.bottom_pillar_height/4, abs(pillarPos[0]) - pillar_wide_half - bearing_wide_half, self.bottom_pillar_height, horizontal=True))

        else:
            '''
            vertical long the plate between bearings
            '''
            #between bottom pillar and lowest bearing
            bottom_pos = (self.bottom_pillar_positions[0][0], self.bottom_pillar_positions[0][1] + self.bottom_pillar_r)
            chain_pos = self.bearing_positions[0][:2]
            first_arbour_pos = self.bearing_positions[1][:2]

            chain_space = self.arbors_for_plate[0].bearing.outer_d / 2
            arbour_space = self.arbors_for_plate[1].bearing.outer_d / 2

            if self.heavy:
                text_height = self.bottom_pillar_r * 2 * 0.3
                #three along the wide bit at the bottom and one above
                spaces.append(TextSpace(bottom_pos[0] - self.bottom_pillar_r + self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))
                spaces.append(TextSpace(bottom_pos[0], (bottom_pos[1] + (chain_pos[1]-chain_space)) / 2, text_height, chain_pos[1] - chain_space - bottom_pos[1], horizontal=False))
                spaces.append(TextSpace(bottom_pos[0] + self.bottom_pillar_r - self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))

                spaces.append(TextSpace(chain_pos[0], (first_arbour_pos[1]-arbour_space + chain_pos[1] + chain_space) / 2, self.plate_width * 0.9, first_arbour_pos[1] - arbour_space - (chain_pos[1] + chain_space), horizontal=False))
            else:
                #two and two
                spaces.append(TextSpace(bottom_pos[0] - self.plate_width / 4, (bottom_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, chain_pos[1] - bottom_pos[1], horizontal=False))
                spaces.append(TextSpace(bottom_pos[0] + self.plate_width / 4, (bottom_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, chain_pos[1] - bottom_pos[1], horizontal=False))

                spaces.append(TextSpace(chain_pos[0] - self.plate_width / 4, (first_arbour_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, first_arbour_pos[1] - chain_pos[1], horizontal=False))
                spaces.append(TextSpace(chain_pos[0] + self.plate_width / 4, (first_arbour_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, first_arbour_pos[1] - chain_pos[1], horizontal=False))


        for i,text in enumerate(texts):
            spaces[i].set_text(text)

        return spaces

    def get_plate_detail(self, back=True):
        '''
        For styles of clock plate which might have ornate detailing. Similar to dial detail or text, this is a separate 3d shape
        designed to be sliced as a multicolour object
        '''

        #undecided - might be easier to just not put this on the back plate? it's going to be hard to see and makes it harder to print and work out how to do standoffs
        if self.style == PlateStyle.RAISED_EDGING and not back:
            #not for printing so we know it's got its back on the plane with bearing holes facing up
            plate = self.get_plate(back = back, for_printing=False, just_basic_shape=True, thick_override=self.edging_wide*10)

            shell = plate.shell(-self.edging_wide)
            # return shell
            # return cq.Workplane("XY").rect(50000, 50000).extrude(self.edging_thick)
            edging = shell.translate((0,0,-self.edging_wide)).intersect(cq.Workplane("XY").rect(500, 500).extrude(self.edging_thick))
            # this is on the xy plane sticking up +ve z, will need translating to be useful
            return edging
            # return edging.translate((0,0,self.get_plate_thick(back=back)))

        return None
    def get_plate(self, back=True, for_printing=True, just_basic_shape=False, thick_override=-1):
        '''
        Two plates that are almost idential, with pillars at the very top and bottom to hold them together.
        Designed to be flat up against the wall, with everything offset to avoid the wall and picture rail

        styles: round or vertical
        round minimises total height by placing the gear train in a circle, so more complicated clocks can still fit on the print bed
        vertical just has everything directly above each other.

        The screwhole is placed directly above the weight to make the clock easier to hang straight

        '''
        top_pillar_positions, top_pillar_r, plate_width = (self.top_pillar_positions, self.top_pillar_r, self.plate_width)

        if self.top_pillars > 1:
            raise ValueError("simple clock plates don't yet support multiple top pillars")

        thick = self.get_plate_thick(back)
        if thick_override > 0:
            thick = thick_override

        #the bulk material that holds the bearings
        plate = cq.Workplane("XY").tag("base")
        if self.gear_train_layout==GearTrainLayout.ROUND:
            radius = self.compact_radius + plate_width / 2
            #the ring that holds the gears
            plate = plate.moveTo(self.bearing_positions[0][0], self.bearing_positions[0][1] + self.compact_radius).circle(radius).circle(radius - plate_width).extrude(thick)
        elif self.gear_train_layout in [GearTrainLayout.VERTICAL, GearTrainLayout.COMPACT]:
            #rectangle that just spans from the top bearing to the bottom pillar (so we can vary the width of the bottom section later)
            plate = plate.moveTo((self.bearing_positions[0][0] + self.bearing_positions[-1][0]) / 2, (self.bearing_positions[0][1] + self.bearing_positions[-1][1]) / 2).rect(plate_width, abs(self.bearing_positions[-1][1] - self.bearing_positions[0][1])).extrude(self.get_plate_thick(back))

        if self.gear_train_layout == GearTrainLayout.COMPACT:
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



            sticky_out_bearing_indexes = []
            if self.going_train.wheels == 4:
                sticky_out_bearing_indexes = [self.going_train.powered_wheels + 1, self.going_train.powered_wheels + 3]
            else:
                sticky_out_bearing_indexes = [self.going_train.powered_wheels + 1]

            if self.going_train.powered_wheels == 2:
                sticky_out_bearing_indexes += [1]

            for bearing_index in sticky_out_bearing_indexes:
                sticky_out_ness = abs(self.bearing_positions[self.going_train.powered_wheels][0] - self.bearing_positions[bearing_index][0])
                if sticky_out_ness > 30:
                    #a-frame arms
                    #reducing to thin arms and chunky circle around bearings
                    points = [ #bearing_pos[:2]for bearing_pos in self.bearing_positions[bearing_index - 1:bearing_index + 1 + 1 ]]
                        self.bearing_positions[bearing_index - 1][:2],
                        self.bearing_positions[bearing_index][:2],
                        self.bearing_positions[bearing_index + 1][:2]
                    ]
                    plate = plate.union(cq.Workplane("XY").circle(self.min_plate_width / 2).extrude(thick).translate(self.bearing_positions[bearing_index][:2]))
                    # points = [(x, y) for x, y, z in points]
                    plate = plate.union(get_stroke_line(points, self.min_plate_width / 2, thick))

                else:
                    #just stick a tiny arm out the side for each bearing
                    bearing_pos = self.bearing_positions[bearing_index]
                    points = [(0, bearing_pos[1]), (bearing_pos[0], bearing_pos[1])]
                    plate = plate.union(get_stroke_line(points, self.min_plate_width, thick))




        plate = plate.tag("top")

        bottom_pillar_joins_plate_pos = self.bearing_positions[0][:2]

        screwHolePositions = self.get_screwhole_positions()

        bottomScrewHoleY = min([hole[1] for hole in screwHolePositions])

        if self.heavy and self.using_pulley and back and self.back_plate_from_wall == 0:
            #instead of an extra circle around the screwhole, make the plate wider extend all the way up
            #because the screwhole will be central when heavy and using a pulley
            #don't do this if we're offset from the wall
            bottom_pillar_joins_plate_pos = (0, bottomScrewHoleY)

        #supports all the combinations of round/vertical and chainwheels or not
        bottom_pillar_link_has_rounded_top = self.gear_train_layout in [GearTrainLayout.VERTICAL, GearTrainLayout.COMPACT]
        #narrow = self.goingTrain.chainWheels == 0
        bottomBitWide = plate_width# if narrow else self.bottomPillarR*2

        if self.going_train.powered_wheels > 0:
            bottomBitWide = self.bottom_pillar_r * 2

        #link the bottom pillar to the rest of the plate
        if self.narrow_bottom_pillar and self.bottom_pillars == 2:
            #rectangle between the two and round off teh ends
            # plate = plate.union(cq.Workplane("XY").rect(abs(self.bottomPillarPositions[0][0] - self.bottomPillarPositions[1][0])), self.bottom_pillar_height)
            plate = plate.union(get_stroke_line(self.bottom_pillar_positions, wide=self.bottom_pillar_height, thick = thick, style=StrokeStyle.SQUARE))
            for bottomPillarPos in self.bottom_pillar_positions:
                plate = plate.union(get_stroke_line([(bottomPillarPos[0], bottomPillarPos[1] + self.bottom_pillar_height/2-self.bottom_pillar_width/2), (bottomPillarPos[0], bottomPillarPos[1] - self.bottom_pillar_height/2+self.bottom_pillar_width/2)], thick = thick, wide=self.bottom_pillar_width))
        else:
            for bottomPillarPos in self.bottom_pillar_positions:
                plate = plate.union(get_stroke_line([bottomPillarPos, bottom_pillar_joins_plate_pos], wide=bottomBitWide, thick = thick))
                plate = plate.union(cq.Workplane("XY").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(self.bottom_pillar_r - 0.00001).extrude(thick))




        if self.gear_train_layout == GearTrainLayout.ROUND:
            #centre of the top of the ring
            topOfPlate = (self.bearing_positions[0][0], self.bearing_positions[0][1] + self.compact_radius * 2)
        else:
            #topmost bearing
            topOfPlate = self.bearing_positions[-1]

        # link the top pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - top_pillar_r, topOfPlate[1]) \
            .lineTo(top_pillar_positions[0][0] - top_pillar_r, top_pillar_positions[0][1]).radiusArc((top_pillar_positions[0][0] + top_pillar_r, top_pillar_positions[0][1]), top_pillar_r) \
            .lineTo(topOfPlate[0] + top_pillar_r, topOfPlate[1]).close().extrude(thick)

        #not sure this will print well
        # if not back and self.front_plate_has_flat_front():
        #     plate = plate.edges(">Z").fillet(1)

        plate = plate.tag("top")
        # #for the screwhole
        # screwHeadD = 9
        # screwBodyD = 6
        # slotLength = 7

        if back:
            #the hole for holding the clock to the wall - can inset the head of the screw if the plate is thick enough
            screwHolebackThick = max(thick - 5, 4)


            if self.back_plate_from_wall == 0:
                for screwPos in screwHolePositions:
                    plate = self.cut_wall_fixing_hole(plate, (screwPos[0], screwPos[1]), back_thick=screwHolebackThick, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=screwPos[2])

            #the pillars
            if not self.pillars_separate:
                for bottomPillarPos in self.bottom_pillar_positions:
                    plate = plate.union(self.get_bottom_pillar().translate(bottomPillarPos).translate((0, 0, thick)))
                plate = plate.union(self.get_top_pillar().translate(self.top_pillar_positions[0]).translate((0, 0, thick)))

            plate = plate.cut(self.get_text())








        if not back:
            #front
            plate = self.front_additions_to_plate(plate, plate_thick=thick)


        if just_basic_shape:
            return plate

        plate = self.punch_bearing_holes(plate, back)

        #screws to fix the plates together, with embedded nuts in the pillars
        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())
        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0, 0, -self.get_plate_thick(back=True) - self.plate_distance)))

        plate = self.apply_style_to_plate(plate, back=back)

        if for_printing and not back and self.front_plate_has_flat_front():
            '''
            front plate is generated front-up, but we can flip it for printing
            '''
            plate = plate.rotate((0,0,0), (0,1,0),180).translate((0,0,thick))




        return plate

    def apply_style_to_plate(self, plate, back=True):
        #assuming here that plates are in the default orentation, with back plate back down and front plate front up

        if self.style == PlateStyle.RAISED_EDGING:
            detail = self.get_plate_detail(back=back)
            if detail is None:
                return plate
            z = - self.edging_thick
            if not back:
                z = self.get_plate_thick(back=False)
            return plate.union(detail.translate((0,0,z)))

        return plate

    def get_fixing_screw_length_info(self):
        bottom_total_length = self.back_plate_from_wall + self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)
        tal_length = self.back_plate_from_wall + self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)
        top_total_length = bottom_total_length + self.get_front_anchor_bearing_holder_total_length()

        if not self.screws_from_back[0][0] and self.back_plate_from_wall > 0:
            # space to embed the nut in the standoff
            top_screw_length = top_total_length - (top_total_length % 10)
        else:
            # nut will stick out the front or back
            top_screw_length = top_total_length + self.fixing_screws.get_nut_height() - (top_total_length + self.fixing_screws.get_nut_height()) % 10

        if not self.screws_from_back[1][0] and self.back_plate_from_wall > 0:
            # space to embed the nut in the standoff
            bottom_screw_length = bottom_total_length - (bottom_total_length % 10)
        else:
            # nut will stick out the front or back
            bottom_screw_length = bottom_total_length + self.fixing_screws.get_nut_height() - (bottom_total_length + self.fixing_screws.get_nut_height()) % 10

        # top and bottom screws are different lengths if there is a front-mounted escapement

        # TODO - could easily have a larger hole in the standoff so the screw or nut starts deeper and thus need shorter screws

        # hacky logic that shouldn't live here
        if top_screw_length > 100 and self.fixing_screws.metric_thread <= 4:
            print("top screw length exceeds 100mm, limiting to 100mm, check design to make sure it fits")
            top_screw_length = 100

        # TODO add option to use threaded rod with nuts on both sides. I've bodged this for tony by printing half with screws from back, and the rest with screws from front
        print(
            "Total length of front to back of clock is {}mm at top and {}mm at bottom. Assuming top screw length of {}mm and bottom screw length of {}mm".format(top_total_length, bottom_total_length, top_screw_length, bottom_screw_length))
        if top_screw_length > 60 and self.fixing_screws.metric_thread < 4:
            print("WARNING may not be able to source screws long enough, try M4")

        return (bottom_total_length, top_total_length, bottom_screw_length, top_screw_length)

    def get_fixing_screw_nut_info(self):
        bottom_total_length, top_total_length, bottom_screw_length, top_screw_length = self.get_fixing_screw_length_info()

        top_nut_base_z = -self.back_plate_from_wall
        bottom_nut_base_z = -self.back_plate_from_wall
        top_nut_hole_height = self.fixing_screws.get_nut_height()
        bottom_nut_hole_height = top_nut_hole_height

        if self.back_plate_from_wall > 0:
            # depth of the hole in the wall standoff before the screw head or nut, so specific sizes of screws can be used
            # extra nut height just in case
            top_nut_hole_height = (top_total_length - top_screw_length) + self.fixing_screws.get_nut_height() + 5
            bottom_nut_hole_height = (bottom_total_length - bottom_screw_length) + self.fixing_screws.get_nut_height() + 5

        return (bottom_nut_base_z, top_nut_base_z, bottom_nut_hole_height, top_nut_hole_height)

    def get_fixing_screws_cutter(self):
        '''
        in position, assuming back of back plate is resting on the XY plane

        Previously used two sets of screws: one to attach the front plate and one to attach the rear standoffs, both with embedded nuts.
        Now assumes you've got screws long enough to attach everything. This should make it stronger
        especially as the pillars are now separate and the new suspension spring will result in two bits of standoff

        bit messy since adding the option for screws_from_back to be different for each pillar (needed to make the moon clock assembleable and look neat)
        '''



        if self.fixing_screws_cutter is not None:
            #fetch from cache if possible
            return self.fixing_screws_cutter

        # bottom_total_length, top_total_length, bottom_screw_length, top_screw_length = self.get_fixing_screw_length_info()


        bottom_nut_base_z, top_nut_base_z, bottom_nut_hole_height, top_nut_hole_height = self.get_fixing_screw_nut_info()

        cutter = cq.Workplane("XY")
        # elif self.embed_nuts_in_plate:
        #     # unlikely I'll be printing any wall clocks without this standoff until I get to striking longcase-style clocks and then I can just use rod and nuts anyway
        #     print("you may have to cut the fixing screws to length in the case of no back standoff")
        #     if self.screws_from_back[0][0]:
        #         top_nut_base_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False) - self.fixing_screws.getNutHeight()
        #     if self.screws_from_back[1][0]:
        #         bottom_nut_base_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False) - self.fixing_screws.getNutHeight()


        for pillar in [0, 1]:



            if pillar == 0:
                plate_fixings = self.plate_top_fixings
                nut_base_z = top_nut_base_z
            else:
                plate_fixings = self.plate_bottom_fixings
                nut_base_z = bottom_nut_base_z

            for i,fixingPos in enumerate(plate_fixings):
                screws_from_back = self.screws_from_back[pillar][i]

                if self.embed_nuts_in_plate:
                    # unlikely I'll be printing any wall clocks without this standoff until I get to striking longcase-style clocks and then I can just use rod and nuts anyway
                    print("you may have to cut the fixing screws to length in the case of no back standoff")
                    if screws_from_back:
                        nut_base_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False) - self.fixing_screws.get_nut_height()

                z = self.front_z
                if self.embed_nuts_in_plate or (self.back_plate_from_wall > 0 and not screws_from_back):
                    #make a hole for the nut
                    if fixingPos in self.plate_top_fixings and self.need_front_anchor_bearing_holder():
                        z += self.get_front_anchor_bearing_holder_total_length()
                        cutter = cutter.union(self.fixing_screws.get_nut_cutter(height=top_nut_hole_height, with_bridging=True, layer_thick=self.layer_thick, rod_loose=True).translate(fixingPos).translate((0, 0, nut_base_z)))
                    else:
                        cutter = cutter.union(self.fixing_screws.get_nut_cutter(height=bottom_nut_hole_height, with_bridging=True, layer_thick=self.layer_thick, rod_loose=True).translate(fixingPos).translate((0, 0, nut_base_z)))
                # holes for the screws
                if screws_from_back:
                    if pillar == 0:
                        screw_start_z = top_nut_hole_height
                    else:
                        screw_start_z = bottom_nut_hole_height

                    cutter = cutter.add(self.fixing_screws.get_cutter(loose=True, layer_thick=self.layer_thick).translate(fixingPos).translate((0, 0, -self.back_plate_from_wall + screw_start_z)))
                else:
                    cutter = cutter.add(self.fixing_screws.get_cutter(loose=True, layer_thick=self.layer_thick).rotate((0, 0, 0), (1, 0, 0), 180).translate(fixingPos).translate((0, 0, z)))




        if self.huygens_maintaining_power:
            #screw to hold the ratchetted chainwheel

            #hold a nyloc nut
            nyloc = True
            bridging = False
            base_z = 0
            nutZ = self.get_plate_thick(back=True) + self.plate_distance - self.fixing_screws.get_nut_height(nyloc=True)

            if self.huygens_wheel_y_offset > self.bottom_pillar_r - self.fixing_screws.get_nut_containing_diameter()/2:
                #nut is in the back of the front plate rather than the top of the bottom pillar, but don't make it as deep as we need the strength
                #making it normal nut deep but will probably still use nyloc
                # nutZ = self.getPlateThick(back=True) + self.plateDistance - (self.fixingScrews.getNutHeight(nyloc=True) - self.fixingScrews.getNutHeight(nyloc=False))

                if self.huygens_wheel_y_offset > self.bottom_pillar_r:
                    #just the front plate
                    bridging = True
                    base_z = self.get_plate_thick(back=True) + self.plate_distance
                    nutZ = self.get_plate_thick(back=True) + self.plate_distance - (self.fixing_screws.get_nut_height(nyloc=True) - self.fixing_screws.get_nut_height(nyloc=False))

            cutter = cutter.add(cq.Workplane("XY").moveTo(self.huygens_wheel_pos[0], self.huygens_wheel_pos[1] + self.huygens_wheel_y_offset).circle(self.fixing_screws.metric_thread / 2).extrude(1000).translate((0, 0, base_z)))
            cutter = cutter.add(self.fixing_screws.get_nut_cutter(nyloc=nyloc, with_bridging=bridging, layer_thick=self.layer_thick).translate(self.huygens_wheel_pos).translate((0, self.huygens_wheel_y_offset, nutZ)))

        if self.moon_complication is not None:
            moon_screws = self.moon_holder.get_fixing_positions()

            for pos in moon_screws:
                pos = (pos[0], pos[1], self.get_plate_thick(back=True) + self.plate_distance)
                # cutter = cutter.add(self.motion_works_screws.getCutter(headSpaceLength=0).translate(pos))
                # putting nuts in the back of the plate so we can screw the moon holder on after the clock is mostly assembled
                cutter = cutter.add(self.motion_works_screws.get_nut_cutter().rotate((0, 0, 0), (0, 0, 1), 360 / 12).translate(pos))
                cutter = cutter.add(cq.Workplane("XY").circle(self.motion_works_screws.metric_thread / 2).extrude(1000).translate(pos))


        #cache to avoid re-calculating (this is reused all over the plates)
        self.fixing_screws_cutter = cutter

        return cutter

    def get_bottom_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane
        '''

        #for chainholes and things which assume one pillar
        bottomPillarPos = self.bottom_pillar_positions[0]
        if self.extra_heavy and self.bottom_pillars == 1:
            '''
            beef up the bottom pillar
            bottomPillarR^2 + x^2 = chainWheelR^2
            x = sqrt(chainWheelR^2 - bottomPilarR^2)
            
            assumes only one bottom pillar, below the chain wheel
            '''

            pillarTopY = self.bearing_positions[0][1] - math.sqrt(self.powered_wheel_r ** 2 - self.bottom_pillar_r ** 2) - bottomPillarPos[1]

            bottom_pillar = cq.Workplane("XY").moveTo(0 - self.bottom_pillar_r, 0).radiusArc((0 + self.bottom_pillar_r, 0), -self.bottom_pillar_r). \
                lineTo(0 + self.bottom_pillar_r, pillarTopY).radiusArc((0 - self.bottom_pillar_r, pillarTopY), self.powered_wheel_r).close()

            if flat:
                return bottom_pillar

            bottom_pillar = bottom_pillar.extrude(self.plate_distance)



        else:

            if self.narrow_bottom_pillar:
                bottom_pillar = cq.Workplane("XY").moveTo(-self.bottom_pillar_width/2, self.bottom_pillar_height/2 - self.bottom_pillar_width/2)\
                    .radiusArc((self.bottom_pillar_width/2,self.bottom_pillar_height/2 - self.bottom_pillar_width/2), self.bottom_pillar_width/2)\
                    .lineTo(self.bottom_pillar_width/2, -self.bottom_pillar_height/2 + self.bottom_pillar_width/2).\
                    radiusArc((-self.bottom_pillar_width/2,-self.bottom_pillar_height/2 + self.bottom_pillar_width/2),self.bottom_pillar_width/2).close()
            else:
                bottom_pillar = cq.Workplane("XY").moveTo(0, 0).circle(self.bottom_pillar_r)

            if flat:
                return bottom_pillar

            bottom_pillar = bottom_pillar.extrude(self.plate_distance)

            if self.reduce_bottom_pillar_height > 0:
                #assumes one pillar
                #bottom pillar has been moved upwards a smidge, cut out a space for the chain wheel
                r = abs(self.bearing_positions[0][1] - (self.bottom_pillar_positions[0][1] + self.bottom_pillar_r - self.reduce_bottom_pillar_height))
                bottom_pillar = bottom_pillar.cut(cq.Workplane("XY").moveTo(0, r - self.reduce_bottom_pillar_height + self.bottom_pillar_r).circle(r).extrude(self.plate_distance))

        if self.bottom_pillars == 1 and self.weight_driven:
            chainHoles = self.get_chain_holes()
            bottom_pillar = bottom_pillar.cut(chainHoles.translate((-bottomPillarPos[0], -bottomPillarPos[1], self.endshake / 2)))

        #hack - assume screws are in the same place for both pillars for now
        bottom_pillar = bottom_pillar.cut(self.get_fixing_screws_cutter().translate((-bottomPillarPos[0], -bottomPillarPos[1], -self.get_plate_thick(back=True))))
        return bottom_pillar

    def get_standoff_pillar(self, top=True, left=True):
        plate_thick = self.get_plate_thick(standoff=True)
        pillar_r = self.top_pillar_r if top else self.bottom_pillar_r
        if self.fancy_pillars:
            return SimpleClockPlates.fancy_pillar(pillar_r, self.back_plate_from_wall - plate_thick, clockwise=left)
        else:
            return cq.Workplane("XY").circle(pillar_r).extrude(self.back_plate_from_wall - plate_thick)

    def get_standoff_pillars(self, top=True):
        pillar_positions = self.top_pillar_positions if top else self.bottom_pillar_positions
        plate_thick = self.get_plate_thick(standoff=True)

        standoff = cq.Workplane("XY")

        clockwise = True
        for pillar_pos in pillar_positions:
            standoff = standoff.union(self.get_standoff_pillar(left=clockwise).translate(pillar_pos).translate((0, 0, plate_thick - self.back_plate_from_wall)))
            clockwise = not clockwise

        return standoff

    def get_pillar(self, top=True, flat=False):
        if top:
            return self.get_top_pillar(flat=flat)
        else:
            return self.get_bottom_pillar(flat=flat)

    def get_top_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane

        if flat returns a 2D shape

        TODO support two pillars?
        '''
        top_pillar_pos, top_pillar_r, bottom_pillar_pos, bottom_pillar_r, holder_wide = (self.top_pillar_positions[0], self.top_pillar_r, self.bottom_pillar_positions, self.bottom_pillar_r, self.plate_width)
        if self.extra_heavy:
            #sagitta looks nice, otherwise arbitrary at the moment, should really check it leaves enough space for the anchor
            sagitta = top_pillar_r * 0.25
            top_pillar = cq.Workplane("XY").moveTo(0 - top_pillar_r, 0).radiusArc((0 + top_pillar_r, 0), top_pillar_r)\
                .lineTo(0 + top_pillar_r, 0 - top_pillar_r - sagitta). \
                sagittaArc((0 - top_pillar_r, 0 - top_pillar_r - sagitta), -sagitta).close()#.extrude(self.plateDistance)
            if flat:
                return top_pillar

            top_pillar = top_pillar.extrude(self.plate_distance)
        else:
            top_pillar = cq.Workplane("XY").moveTo(0, 0).circle(top_pillar_r)
            if flat:
                return top_pillar
            top_pillar = top_pillar.extrude(self.plate_distance)

        if self.fancy_pillars and not flat:
            top_pillar = SimpleClockPlates.fancy_pillar(self.top_pillar_r, self.plate_distance)


        if not flat and self.dial and self.dial_top_above_front_plate and self.top_pillar_holds_dial:
            #this pillar also supports the dial!

            screws_apart = self.top_dial_fixing_y - top_pillar_pos[1]
            thick = self.get_plate_thick(back=False)

            dial_holder = cq.Workplane("XY").rect(top_pillar_r*2,screws_apart).extrude(thick).translate((0,screws_apart/2))
            dial_holder = dial_holder.union(cq.Workplane("XY").circle(top_pillar_r).extrude(thick).translate((0,screws_apart)))

            for pos in self.dial_fixing_positions:
                dial_holder = dial_holder.cut(self.dial.fixing_screws.get_cutter(loose=True, with_bridging=True, layer_thick=self.layer_thick).translate(np_to_set(np.subtract(pos, top_pillar_pos))))

            top_pillar = top_pillar.union(dial_holder.translate((0,0,self.plate_distance - thick)))

        top_pillar = top_pillar.cut(self.get_fixing_screws_cutter().translate((-top_pillar_pos[0], -top_pillar_pos[1], -self.get_plate_thick(back=True))))

        return top_pillar

    def get_chain_holes(self):
        '''
        These chain holes are relative to the front of the back plate - they do NOT take plate thickness or wobble into account
        '''

        holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()
        topZ = self.bearing_positions[0][2] + self.going_train.get_arbor(-self.going_train.powered_wheels).get_total_thickness()

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
                chainHole = cq.Workplane("XZ").moveTo(chainX, (chainZTop + chainZBottom)/2).rect(self.chain_hole_d, abs(chainZTop - chainZBottom)).extrude(1000)
                chainHoles.add(chainHole)
            else:
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + topZ).circle(self.chain_hole_d / 2).extrude(1000)
                chainHoles.add(chainHole)

        if self.using_pulley and self.going_train.powered_wheel.type == PowerType.CORD:
            #hole for cord to be tied in

            #not using a screw anymore, using a bit of steel rod so it won't cut the cord
            cord_holding_screw = MachineScrew(3, countersunk=True)

            chainX = holePositions[0][0][0]
            chainZTop = topZ + holePositions[0][0][1]
            pulleyX = -chainX
            # might want it as far back as possible?
            # for now, as far FORWARDS as possible, because the 4kg weight is really wide!
            pulleyZ = chainZTop - self.chain_hole_d / 2  # chainZBottom + self.chainHoleD/2#(chainZTop + chainZBottom)/2
            if self.back_plate_from_wall > 0:
                #centre it instead
                pulleyZ = topZ + (holePositions[0][0][1] + holePositions[0][1][1])/2
            # and one hole for the cord to be tied
            pulleyHole = cq.Workplane("XZ").moveTo(pulleyX, pulleyZ).circle(self.chain_hole_d / 2).extrude(1000)
            chainHoles.add(pulleyHole)
            # print("chainZ min:", chainZBottom, "chainZ max:", chainZTop)

            # original plan was a screw in from the side, but I think this won't be particularly strong as it's in line with the layers
            # so instead, put a screw in from the front
            pulleyY = self.bottom_pillar_positions[0][1]# + self.bottomPillarR / 2
            if self.extra_heavy:
                #bring it nearer the top, making it easier to tie the cord around it
                pulleyY = self.bottom_pillar_positions[0][1] + self.bottom_pillar_r - cord_holding_screw.metric_thread
            # this screw will provide something for the cord to be tied round
            #TODO there is a bug where the countersink isn't right - cannot fathmon how, but since I'm now using steel rod instead of a screw I'll leave it
            pulleyScrewHole = cord_holding_screw.get_cutter(length=self.plate_distance-5).rotate((0, 0, 0), (1, 0, 0), 180).translate((pulleyX, pulleyY, self.plate_distance))

            #but it's fiddly so give it a hole and protect the screw
            max_extra_space = self.bottom_pillar_r - pulleyX - 1
            if max_extra_space > cord_holding_screw.metric_thread*2:
                max_extra_space = cord_holding_screw.metric_thread*2
            extra_space = cq.Workplane("XY").circle(max_extra_space).extrude(self.chain_hole_d).translate((pulleyX, pulleyY, pulleyZ - self.chain_hole_d / 2))
            #make the space open to the top of the pillar
            extra_space = extra_space.union(cq.Workplane("XY").rect(max_extra_space*2, 1000).extrude(self.chain_hole_d).translate((pulleyX, pulleyY + 500, pulleyZ - self.chain_hole_d / 2)))
            #and keep it printable
            extra_space = extra_space.union(get_hole_with_hole(innerD=self.fixing_screws.metric_thread, outerD=max_extra_space * 2, deep=self.chain_hole_d, layerThick=self.layer_thick)
                                            .rotate((0,0,0),(0,0,1),90).translate((pulleyX, pulleyY, pulleyZ - self.chain_hole_d / 2)))

            #I'm worried about the threads cutting the thinner cord, but there's not quite enough space to add a printed bit around the screw
            # I could instead file off the threads for this bit of the screw?

            chainHoles.add(extra_space)


            chainHoles.add(pulleyScrewHole)
        return chainHoles

    def getBearingHolder(self, height, addSupport=True, bearingInfo=None):
        #height from base (outside) of plate, so this is inclusive of base thickness, not in addition to
        if bearingInfo is None:
            bearingInfo = get_bearing_info(self.arbor_d)
        wallThick = self.bearing_wall_thick
        # diameter = bearingInfo.outer_d + wallThick*2
        outerR = bearingInfo.outer_d/2 + wallThick
        innerInnerR = bearingInfo.outer_safe_d/2
        innerR = bearingInfo.outer_d/2
        holder = cq.Workplane("XY").circle(outerR).extrude(height)

        # holder = holder.faces(">Z").workplane().circle(diameter/2).circle(bearingInfo.outer_d/2).extrude(bearingInfo.height)
        # extra support?
        if addSupport:
            support = cq.Workplane("YZ").moveTo(0,0).lineTo(-height-outerR,0).lineTo(-outerR,height).lineTo(0,height).close().extrude(wallThick).translate((-wallThick/2,0,0))
            holder = holder.add(support)
        holder = holder.cut(cq.Workplane("XY").circle(innerInnerR).extrude(height))
        holder = holder.cut(cq.Workplane("XY").circle(innerR).extrude(bearingInfo.height).translate((0,0,height - bearingInfo.height)))

        return holder

    def get_bearing_punch(self, plate_thick, bearing, bearing_on_top=True , with_support=False):
        '''
        General purpose bearing punch
        '''
        if bearing.height >= plate_thick:
            raise ValueError("plate not thick enough to hold bearing: {}".format(bearing))

        if bearing_on_top:
            punch = cq.Workplane("XY").circle(bearing.outer_safe_d / 2).extrude(plate_thick - bearing.height)
            punch = punch.faces(">Z").workplane().circle(bearing.outer_d / 2).extrude(bearing.height)
        else:
            if with_support:
                punch = get_hole_with_hole(bearing.outer_safe_d, bearing.outer_d, bearing.height, layerThick=self.layer_thick).faces(">Z").workplane().circle(bearing.outer_safe_d / 2).extrude(
                    plate_thick - bearing.height)
            else:
                #no need for hole-in-hole!
                punch = cq.Workplane("XY").circle(bearing.outer_d / 2).extrude(bearing.height).faces(">Z").workplane().circle(bearing.outer_safe_d / 2).extrude(plate_thick - bearing.height)

        return punch



    def getBearingPunchDeprecated(self, bearingOnTop=True, bearingInfo=None, back=True, standoff=False):
        '''
        A shape that can be cut out of a clock plate to hold a bearing
        TODO use get_bearing_punch instead, the logic here is hard to follow as it's grown.
        '''



        if bearingInfo is None:
            bearingInfo = get_bearing_info(self.arbor_d)

        height = self.get_plate_thick(back)
        if standoff:
            height = self.rear_standoff_bearing_holder_thick#self.getPlateThick(standoff=True)

        if bearingInfo.height >= height:
            raise ValueError("{} plate not thick enough to hold bearing: {}".format("Back" if back else "Front",bearingInfo.get_string()))

        if bearingOnTop:
            punch = cq.Workplane("XY").circle(bearingInfo.outer_safe_d/2).extrude(height - bearingInfo.height)
            punch = punch.faces(">Z").workplane().circle(bearingInfo.outer_d/2).extrude(bearingInfo.height)
        else:
            if not back and self.front_plate_has_flat_front():
                #no need for hole-in-hole!
                punch = cq.Workplane("XY").circle(bearingInfo.outer_d/2).extrude(bearingInfo.height).faces(">Z").workplane().circle(bearingInfo.outer_safe_d/2).extrude(height - bearingInfo.height)
            else:
                punch = get_hole_with_hole(bearingInfo.outer_safe_d, bearingInfo.outer_d, bearingInfo.height, layerThick=LAYER_THICK_EXTRATHICK).faces(">Z").workplane().circle(bearingInfo.outer_safe_d / 2).extrude(height - bearingInfo.height)

        return punch

    def punch_bearing_holes(self, plate, back, make_plate_bigger=True):
        for i, pos in enumerate(self.bearing_positions):
            bearing_info = self.arbors_for_plate[i].bearing#get_bearing_info(self.going_train.get_arbour_with_conventional_naming(i).get_rod_d())
            bearing_on_top = back

            needs_plain_hole = False
            if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOUR, PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING] and i == len(self.bearing_positions)-1:
                #if true we just need a hole for the direct arbour to fit through

                if self.escapement_on_front and not back:
                    '''
                    need the bearings to be on the back of front plate and back of the back plate
                    so endshake will be between back of back plate and front of the wall standoff bearing holder
                    this way there doesn't need to be a visible bearing on the front
                    '''
                    needs_plain_hole = True

                if not self.pendulum_at_front and back:
                    needs_plain_hole = True


            outer_d =  bearing_info.outer_d
            if needs_plain_hole:
                outer_d = self.direct_arbor_d + 3

            if outer_d > self.plate_width - self.bearing_wall_thick*2 and make_plate_bigger and not needs_plain_hole:
                #this is a chunkier bearing, make the plate bigger
                try:
                    plate = plate.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(outer_d / 2 + self.bearing_wall_thick).extrude(self.get_plate_thick(back=back)))
                except:
                    print("wasn't able to make plate bigger for bearing")

            if needs_plain_hole:
                plate = plate.cut(cq.Workplane("XY").circle(outer_d/2).extrude(self.get_plate_thick(back=back)).translate((pos[0], pos[1], 0)))
            else:
                plate = plate.cut(self.getBearingPunchDeprecated(bearingOnTop=bearing_on_top, bearingInfo=bearing_info, back=back).translate((pos[0], pos[1], 0)))
        return plate

    def cut_wall_fixing_hole(self, plate, screwhole_pos, screw_head_d = 9, screw_body_d = 6, slot_length = 7, back_thick = -1, add_extra_support=False, plate_thick=-1):
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
            plate_thick = self.get_plate_thick(back=True)

        if add_extra_support:
            #a circle around the big hole to strengthen the plate
            #assumes plate has been tagged
            #removing all the old bodges and simplifying
            # extraSupportSize = screwHeadD*1.25
            extraSupportR = self.plate_width * 0.5
            supportCentre=[screwhole_pos[0], screwhole_pos[1] - slot_length]

            # if self.heavy:
            #     extraSupportSize*=1.5
            #     supportCentre[1] += slotLength / 2
            #     #bodge if the screwhole is off to one side
            #     if screwholePos[0] != 0:
            #         #this can be a bit finnickity - I think if something lines up exactly wrong with the bearing holes?
            #         supportCentre[0] += (-1 if screwholePos[0] > 0 else 1) * extraSupportSize*0.5
            #
            # plate = plate.workplaneFromTagged("base").moveTo(supportCentre[0], supportCentre[1] ).circle(extraSupportSize).extrude(plate_thick)
            plate = plate.union(get_stroke_line([(screwhole_pos[0], screwhole_pos[1] - slot_length), (screwhole_pos[0], screwhole_pos[1])], wide=extraSupportR * 2, thick=plate_thick))

        #big hole
        plate = plate.faces(">Z").workplane().tag("top").moveTo(screwhole_pos[0], screwhole_pos[1] - slot_length).circle(screw_head_d / 2).cutThruAll()
        #slot
        plate = plate.workplaneFromTagged("top").moveTo(screwhole_pos[0], screwhole_pos[1] - slot_length / 2).rect(screw_body_d, slot_length).cutThruAll()
        # small hole
        plate = plate.workplaneFromTagged("top").moveTo(screwhole_pos[0], screwhole_pos[1]).circle(screw_body_d / 2).cutThruAll()

        if back_thick > 0 and back_thick < plate_thick:
            extraY = screw_body_d * 0.5
            cutter = cq.Workplane("XY").moveTo(screwhole_pos[0], screwhole_pos[1] + extraY).circle(screw_head_d / 2).extrude(self.get_plate_thick(back=True) - back_thick).translate((0, 0, back_thick))
            cutter = cutter.add(cq.Workplane("XY").moveTo(screwhole_pos[0], screwhole_pos[1] - slot_length / 2 + extraY / 2).rect(screw_head_d, slot_length + extraY).extrude(plate_thick - back_thick).translate((0, 0, back_thick)))
            plate = plate.cut(cutter)

        return plate

    def front_additions_to_plate(self, plate, plate_thick=-1):
        '''
        stuff only needed to be added to the front plate
        '''
        if plate_thick < 0:
            plate_thick = self.get_plate_thick(back=False)
        # FRONT

        # note - works fine with the pendulum on the same rod as teh anchor, but I'm not sure about the long term use of ball bearings for just rocking back and forth
        # suspensionBaseThick=0.5
        # suspensionPoint = self.pendulum.getSuspension(False,suspensionBaseThick ).translate((self.bearingPositions[len(self.bearingPositions)-1][0], self.bearingPositions[len(self.bearingPositions)-1][1], plateThick-suspensionBaseThick))
        #         #
        #         # plate = plate.add(suspensionPoint)
        # new plan: just put the pendulum on the same rod as the anchor, and use nyloc nuts to keep both firmly on the rod.
        # no idea if it'll work without the rod bending!

        #not using anymore - don't want extra bearings on the pendulum (adds too much friction and it doesn't really droop much)
        #but unlikely to ever re-print a clock with the friction fitting pendulum anyway
        # if self.pendulumAtFront and self.pendulumSticksOut > 0 and self.pendulumFixing == PendulumFixing.FRICTION_ROD:
        #     #a cylinder that sticks out the front and holds a bearing on the end
        #     extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, False).translate((self.bearingPositions[len(self.bearingPositions) - 1][0], self.bearingPositions[len(self.bearingPositions) - 1][1], plateThick))
        #     plate = plate.add(extraBearingHolder)


        mini_arm_width = self.motion_works_screws.get_nut_containing_diameter() * 2

        if self.need_motion_works_holder:
            #screw would be on top of a bearing, so there's a separate peice to hold it
            for pos in self.motion_works_fixings_relative_pos:
                screw_pos = np_to_set(np.add(self.motion_works_pos, pos))
                plate = plate.cut(cq.Workplane("XY").circle(self.motion_works_screws.get_diameter_for_die_cutting()/2).extrude(plate_thick).translate(screw_pos))
        else:
            if self.little_arm_to_motion_works:
                #extra material in case the motion works is at an angle off to one side
                plate = plate.union(get_stroke_line([self.hands_position, self.motion_works_pos], wide=mini_arm_width, thick=plate_thick))
            #hole for screw to hold motion works arbour
            plate = plate.cut(self.motion_works_screws.get_cutter().translate(self.motion_works_pos))

        if self.motion_works.cannon_pinion_friction_ring:
            for pos in self.cannon_pinion_friction_clip_fixings_pos:
                plate = plate.cut(cq.Workplane("XY").circle(self.motion_works_screws.get_diameter_for_die_cutting()/2).extrude(plate_thick).translate(pos))

        #embedded nut on the front so we can tighten this screw in
        #decided against this - I think it's might make the screw wonky as there's less plate for it to be going through.
        #if it's loose, use superglue.
        # nutDeep =  self.fixingScrews.getNutHeight(half=True)
        # nutSpace = self.fixingScrews.getNutCutter(half=True).translate(motionWorksPos).translate((0,0,self.getPlateThick(back=False) - nutDeep))
        #
        # plate = plate.cut(nutSpace)

        if self.dial is not None:

            if self.dial_top_above_front_plate and not self.top_pillar_holds_dial:
                # need to extend the front plate off the top of teh clock to hold the dial
                # TODO make this more robust (assumes vertical or compact plates with one top pillar)

                dial_support_pos = (self.hands_position[0], self.hands_position[1] + self.dial.outside_d/2- self.dial.dial_width/2)
                # plate = plate.union(cq.Workplane("XY").circle(self.plate_width / 2).extrude(plate_thick).translate(dial_support_pos))
                # plate = plate.union(cq.Workplane("XY").rect(self.plate_width, dial_support_pos[1] - self.top_pillar_positions[0][1]).extrude(plate_thick).translate((self.bearing_positions[-1][0], (self.top_pillar_positions[0][1] + dial_support_pos[1]) / 2)))
                plate = plate.union(get_stroke_line([dial_support_pos, self.bearing_positions[-1][:2]], wide=self.plate_width, thick = plate_thick))

            #TODO bottom extension (am I ever going to want it?)


            for pos in self.dial_fixing_positions:
                plate = plate.cut(self.dial.fixing_screws.get_cutter(loose=True, with_bridging=True, layer_thick=self.layer_thick).translate(pos))

        if self.moon_complication is not None:

            #screw holes for the moon complication arbors
            for i, relative_pos in enumerate(self.moon_complication.get_arbor_positions_relative_to_motion_works()):
                pos = np_to_set(np.add(self.hands_position, relative_pos[:2]))
                # extra bits of plate to hold the screw holes for extra arbors

                #skip the second one if it's in the same place as the extra arm for the extraheavy compact plates
                if i != 1 or (self.gear_train_layout != GearTrainLayout.COMPACT and self.extra_heavy) or not self.moon_complication.on_left:

                    plate = plate.union(get_stroke_line([self.hands_position, pos], wide=mini_arm_width, thick=plate_thick))


                plate = plate.cut(self.motion_works_screws.get_cutter(with_bridging=True, layer_thick=self.layer_thick).translate(pos))


        # need an extra chunky hole for the big bearing that the key slots through
        if self.winding_key is not None:
            powered_wheel = self.going_train.powered_wheel

            if self.front_plate_has_flat_front():
                #can print front-side on the build plate, so the bearing holes are printed on top
                cord_bearing_hole = cq.Workplane("XY").circle(powered_wheel.key_bearing.outer_d / 2).extrude(powered_wheel.key_bearing.height)
            else:
                cord_bearing_hole = get_hole_with_hole(self.key_hole_d, powered_wheel.key_bearing.outer_d, powered_wheel.key_bearing.height, layerThick=self.layer_thick)

            cord_bearing_hole = cord_bearing_hole.faces(">Z").workplane().circle(self.key_hole_d / 2).extrude(plate_thick)

            plate = plate.cut(cord_bearing_hole.translate((self.bearing_positions[0][0], self.bearing_positions[0][1], 0)))

        #can't decide where the best place is to do this, currently it lives in the MantelClockPlates
        # if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and not self.going_train.powered_wheel.ratchet_at_back:
        #     #spring powered, need the ratchet!
        #     screw = self.going_train.powered_wheel.ratchet.fixing_screws
        #
        #     for relative_pos in self.going_train.powered_wheel.ratchet.get_screw_positions():
        #         pos = npToSet(np.add(self.bearing_positions[0][:2],relative_pos))
        #         plate = plate.cut(screw.get_cutter(for_tap_die=True, with_bridging=True).translate(pos))


        if self.huygens_maintaining_power:

            #designed with a washer to be put under the chain wheel to reduce friction (hopefully)


            #add an extra bit at the bottom so the chain can't easily fall off
            chainholeD = self.huygens_wheel.getChainHoleD()
            holePositions = self.huygens_wheel.get_chain_positions_from_top()
            relevantChainHoles = [ pair[0] for pair in holePositions ]

            minThickAroundChainHole = 2
            #make a fancy bit that sticks out the bottom with holes for the chain - this makes it hard for the chain to detatch from the wheel

            extraHeight = relevantChainHoles[0][1] + self.huygens_wheel.get_height() - self.huygens_wheel.ratchet.thick + chainholeD / 2 + minThickAroundChainHole
            ratchetD = self.huygens_wheel.ratchet.outsideDiameter
            # ratchet for the chainwheel on the front of the clock
            ratchet = self.huygens_wheel.ratchet.getOuterWheel(extraThick=WASHER_THICK_M3)

            ratchet = ratchet.faces(">Z").workplane().circle(ratchetD/2).circle(self.huygens_wheel.ratchet.toothRadius).extrude(extraHeight)

            totalHeight = extraHeight + WASHER_THICK_M3 + self.huygens_wheel.ratchet.thick


            cutter = cq.Workplane("YZ").moveTo(-ratchetD/2,totalHeight).spline(includeCurrent=True,listOfXYTuple=[(ratchetD/2, totalHeight-extraHeight)], tangents=[(1,0),(1,0)])\
                .lineTo(ratchetD/2,totalHeight).close().extrude(ratchetD).translate((-ratchetD/2,0,0))
            for holePosition in holePositions:
                #chainholes are relative to the assumed height of the chainwheel, which includes a washer
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + (self.huygens_wheel.get_height() + WASHER_THICK_M3)).circle(chainholeD / 2).extrude(1000)
                cutter.add(chainHole)


            ratchet = ratchet.cut(cutter)

            if self.bottom_pillars > 1:
                raise ValueError("Hyugens wheel not yet supported with more than 1 bottom pillar")
            #assumes single pillar
            huygens_pos = self.bottom_pillar_positions[0]
            plate = plate.union(ratchet.translate(huygens_pos).translate((0, self.huygens_wheel_y_offset, plate_thick)))
            if ratchetD > self.bottom_pillar_r:
                plate = plate.union(cq.Workplane("XY").circle(ratchetD/2).extrude(plate_thick).translate(huygens_pos).translate((0, self.huygens_wheel_y_offset)))

        if self.weight_driven and not self.escapement_on_front and not self.huygens_maintaining_power and not self.pendulum_at_front and self.bottom_pillars > 1 and not self.going_train.chain_at_back:
            #add a semicircular bit under the chain wheel (like on huygens) to stop chain from being able to fall off easily
            #TODO support cord wheels and chain at back

            powered_wheel = self.going_train.powered_wheel

            chainholeD = powered_wheel.getChainHoleD()
            holePositions = powered_wheel.get_chain_positions_from_top()
            relevantChainHoles = [pair[0] for pair in holePositions]


            minThickAroundChainHole = 3
            thick = 3


            outer_r = powered_wheel.ratchet.outsideDiameter / 2 + self.gear_gap + thick
            deep = powered_wheel.get_height()-powered_wheel.ratchet.thick/2

            extra_plate = cq.Workplane("XY").circle(outer_r).extrude(plate_thick)
            extra_plate = extra_plate.union(cq.Workplane("XY").circle(outer_r).circle(outer_r - thick).extrude(deep).translate((0,0,-deep)))

            extra_plate = extra_plate.intersect(cq.Workplane("XY").moveTo(0,-outer_r - self.bottom_pillar_height/2).rect(outer_r*2, outer_r*2).extrude(self.plate_distance + plate_thick).translate((0, 0, -self.plate_distance)))
            cutter = cq.Workplane("XY")
            for holePosition in relevantChainHoles:
                #chainholes are relative to the assumed height of the chainwheel, which includes a washer
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0], holePosition[1] - self.endshake/2).circle(chainholeD / 2).extrude(1000)
                cutter.add(chainHole)

            extra_plate = extra_plate.cut(cutter)

            plate = plate.union(extra_plate.translate(self.bearing_positions[0][:2]))



        if self.escapement_on_front and self.extra_support_for_escape_wheel:
            #this is a bearing extended out the front, helps maintain the geometry for a grasshopper on plates with a narrow plateDistance
            plate = plate.add(self.getBearingHolder(-self.going_train.escapement.get_wheel_base_to_anchor_base_z()).translate((self.bearing_positions[-2][0], self.bearing_positions[-2][1], self.get_plate_thick(back=False))))

        return plate

    def get_diameter_for_pulley(self):

        holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()

        if self.huygens_maintaining_power:

            chainWheelTopZ = self.bearing_positions[0][2] + self.going_train.get_arbor(-self.going_train.powered_wheels).get_total_thickness() + self.get_plate_thick(back=True) + self.endshake / 2
            chainWheelChainZ = chainWheelTopZ + holePositions[0][0][1]
            huygensChainPoses = self.huygens_wheel.get_chain_positions_from_top()
            #washer is under the chain wheel
            huygensChainZ = self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance + self.huygens_wheel.get_height() + WASHER_THICK_M3 + huygensChainPoses[0][0][1]

            return huygensChainZ - chainWheelChainZ
        else:
            return abs(holePositions[0][0] - holePositions[1][0])

    def key_is_inside_dial(self):
        '''
        Very crude, assumes user has ensured the key doesn't intersect with the dial
        '''
        if self.dial is None:
            return False

        key_pos = self.bearing_positions[0][:2]
        dial_centre = self.hands_position

        distance = np.linalg.norm(np.subtract(dial_centre, key_pos))

        return distance < self.dial.outside_d/2



    def calc_winding_key_info(self):
        '''
        set front_plate_has_key_hole and key_offset_from_front_plate

        hacky side effect: will set key length on cord wheel
        '''

        if (self.weight_driven and not (self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key)):
            raise ValueError("No winding key on this clock!")

        powered_wheel = self.going_train.powered_wheel
        key_bearing = powered_wheel.key_bearing


        self.key_hole_d = key_bearing.outer_safe_d

        #on the old cord wheel, which didn't know the plate thickness, account for how much of the square bit is within the plate
        key_within_front_plate = self.get_plate_thick(back=False) - key_bearing.height

        # self.key_hole_d = self.going_train.powered_wheel.keyWidth + 1.5
        if self.bottom_of_hour_hand_z() < 25 and (self.weight_driven or self.going_train.powered_wheel.ratchet_at_back):# and self.key_hole_d > front_hole_d and self.key_hole_d < key_bearing.outer_d - 1:
            # only if the key would otherwise be a bit too short (for dials very close to the front plate) make the hole just big enough to fit the key into
            #can't do this for spring driven as the ratchet is on the front (could move it to the back but it would make letting down the spring harder)
            print("Making the front hole just big enough for the cord key")
            #offset *into* the front plate
            self.key_offset_from_front_plate = -key_within_front_plate
        else:
            self.key_offset_from_front_plate = 1

        #HACK remove this once cord wheel works like the spring barrel (where ArborForPlate provides all the info about how long the key is)
        if not self.weight_driven:
            key_within_front_plate = 0

        if self.key_is_inside_dial():
            key_length = self.bottom_of_hour_hand_z() - 4 + key_within_front_plate
        else:
            key_length = key_within_front_plate + self.ideal_key_length
        #hack - set key size here
        #note - do this relative to the hour hand, not the dial, because there may be more space for the hour hand to avoid the second hand
        #TODO remove this for cord wheel

        self.going_train.powered_wheel.key_square_bit_height = key_length
        #the slightly less hacky way... (although now I think about it, is it actually? we're still reaching into an object to set something)
        self.arbors_for_plate[0].key_length = key_length

        #how much of the key sticks out the front of the front plate
        self.key_length = key_length - key_within_front_plate

        square_bit_inside_front_plate_length = self.get_plate_thick(back=False) - key_bearing.height
        key_hole_deep = key_length - (square_bit_inside_front_plate_length + self.key_offset_from_front_plate) - self.endshake



        if self.dial is not None and not self.key_is_inside_dial() and self.weight_driven:
            # just so the crank (only for weights) doesn't clip the dial (the key is outside the dial)
            cylinder_length = self.dial_z + self.dial.thick + 6 - self.key_offset_from_front_plate
            # reach to the centre of the dial (just miss the hands)
            handle_length = self.hands_position[1] - (self.dial.outside_d / 2 - self.dial.dial_width / 2) - self.bearing_positions[0][1] - 5
        else:
            # above the hands (the key is inside the dial)
            cylinder_length = self.top_of_hands_z + 6 - self.key_offset_from_front_plate
            # avoid the centre of the hands (but make as long as possible to ease winding)
            handle_length = self.hands_position[1] - self.bearing_positions[0][1] - 6  # 10

        crank = self.weight_driven
        key_wiggle_room = 0.75 # the default
        wall_thick = 2.5 # the default
        sideways = False
        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and not self.going_train.powered_wheel.ratchet_at_back:
            #take into accuont the ratchet on the front
            ratchet_thickness = self.going_train.powered_wheel.ratchet.thick + self.going_train.powered_wheel.ratchet_collet_thick
            key_hole_deep -= ratchet_thickness
            cylinder_length -= ratchet_thickness
            #trying a bit less for the hex key (now trying more again since I'm printing it sideways
            # key_wiggle_room = 0.5
            #this was a bit too much, going back to default
            # key_wiggle_room = 1

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL:
            wall_thick = 5
            sideways = True

        self.winding_key = WindingKey(key_containing_diameter=powered_wheel.get_key_size(), cylinder_length = cylinder_length, key_hole_deep=key_hole_deep,
                                      handle_length=handle_length, crank=crank, key_sides=powered_wheel.get_key_sides(), key_wiggle_room=key_wiggle_room, wall_thick=wall_thick,
                                      print_sideways=sideways)

        if self.key_offset_from_front_plate < 0:
            self.key_hole_d = self.winding_key.body_wide+1.5

        print("winding key length {:.1f}mm".format(key_length))

    def get_winding_key(self):
        return self.winding_key


    def get_assembled(self, one_peice = True):
        '''
        3D model of teh assembled plates
        '''
        bottom_plate = self.get_plate(True, for_printing=False)
        top_plate = self.get_plate(False, for_printing=False)
        front_of_clock_z = self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance

        plates = bottom_plate.add(top_plate.translate((0, 0, self.plate_distance + self.get_plate_thick(back=True))))

        pillars = cq.Workplane("XY")
        standoff_pillars = cq.Workplane("XY")
        if self.pillars_separate:
            for bottom_pillar_pos in self.bottom_pillar_positions:
                pillars = pillars.add(self.get_pillar(top=False).translate(bottom_pillar_pos).translate((0, 0, self.get_plate_thick(back=True))))
            for top_pillar_pos in self.top_pillar_positions:
                pillars = pillars.add(self.get_pillar(top=True).translate(top_pillar_pos).translate((0, 0, self.get_plate_thick(back=True))))



        if self.back_plate_from_wall > 0:
            # need wall standoffs
            plates = plates.add(self.get_wall_standoff(top=True, for_printing=False))
            plates = plates.add(self.get_wall_standoff(top=False, for_printing=False))
            if self.standoff_pillars_separate:
                standoff_pillars = standoff_pillars.add(self.get_standoff_pillars(top=True))
                standoff_pillars = standoff_pillars.add(self.get_standoff_pillars(top=False))

        if self.need_front_anchor_bearing_holder() and not self.front_anchor_holder_part_of_dial:
            plates = plates.add(self.get_front_anchor_bearing_holder(for_printing=False))

        if self.need_motion_works_holder:
            plates = plates.add(self.get_motion_works_holder().translate((self.motion_works_pos[0], self.motion_works_pos[1], front_of_clock_z)))

        detail = None
        if self.style in [PlateStyle.RAISED_EDGING]:
            detail = self.apply_style_to_plate(cq.Workplane("XY"), back=True).add(self.apply_style_to_plate(cq.Workplane("XY"), back=False)
                                                                                  .translate((0,0,self.get_plate_thick(back=True) + self.plate_distance)))

        if one_peice:
            whole =  plates.union(pillars)
            if detail is not None:
                whole= whole.union(detail)
            return whole

        return (plates, pillars, detail, standoff_pillars)


    def output_STLs(self, name="clock", path="../out"):

        if self.dial is not None:
            self.dial.output_STLs(name, path)

        out = os.path.join(path, "{}_plate_front.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_plate(False, for_printing=True), out)

        out = os.path.join(path, "{}_plate_back.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_plate(True, for_printing=True), out)

        if not self.text_on_standoffs:
            out = os.path.join(path, "{}_plate_back_text.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_text(), out)

        if self.pillars_separate:
            out = os.path.join(path, "{}_pillar_bottom.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_pillar(top=False), out)

            out = os.path.join(path, "{}_pillar_top.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_pillar(top=True), out)

        if self.motion_works.cannon_pinion_friction_ring:
            out = os.path.join(path, "{}_friction_clip.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_cannon_pinion_friction_clip(), out)

        if len(self.get_screwhole_positions()) > 1:
            #need a template to help drill the screwholes!
            out = os.path.join(path, "{}_drill_template_6mm.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_drill_template(6, layer_thick=0.4), out)

        if self.back_plate_from_wall > 0:
            # out = os.path.join(path, "{}_wall_standoff.stl".format(name))
            # print("Outputting ", out)
            # exporters.export(self.getCombinedWallStandOff(), out)

            out = os.path.join(path, "{}_wall_standoff_top.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_wall_standoff(top=True), out)

            out = os.path.join(path, "{}_wall_standoff_bottom.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_wall_standoff(top=False), out)
            if self.text_on_standoffs:
                out = os.path.join(path, "{}_wall_standoff_top_text.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.get_text(top_standoff=True), out)

                out = os.path.join(path, "{}_wall_standoff_bottom_text.stl".format(name))
                print("Outputting ", out)
                exporters.export(self.get_text(top_standoff=False), out)

            if self.standoff_pillars_separate:
                for left in [True, False]:
                    for top in [True, False]:
                        pillar_name = "{}_{}".format("left" if left else "right", "top" if top else "bottom")
                        out = os.path.join(path, "{}_wall_standoff_pillar_{}.stl".format(name, pillar_name))
                        print("Outputting ", out)
                        exporters.export(self.get_standoff_pillar(top=top, left=left), out)

        if self.huygens_maintaining_power:
            self.huygens_wheel.output_STLs(name + "_huygens", path)

        for i,arbourForPlate in enumerate(self.arbors_for_plate):
            shapes = arbourForPlate.get_shapes()
            #TODO maybe include powered wheel in shapes? not sure if it's worth the effort
            if arbourForPlate.type == ArborType.POWERED_WHEEL:
                arbourForPlate.arbor.powered_wheel.output_STLs(name + "_arbour_{}".format(i), path)
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

        key = self.get_winding_key()
        if key is not None:
            key.output_STLs(name, path)

        if self.need_front_anchor_bearing_holder():
            out = os.path.join(path, "{}_anchor_front_bearing_holder.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_front_anchor_bearing_holder(), out)

        if self.moon_holder is not None:
            holder_parts = self.moon_holder.get_moon_holder_parts()
            for i, holder in enumerate(holder_parts):
                out = os.path.join(path, "{}_moon_holder_part{}.stl".format(name,i))
                print("Outputting ", out)
                exporters.export(holder, out)

        # for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels + 1):
        #     for top in [True, False]:
        #         extensionShape=self.getArbourExtension(arbour, top=top)
        #         if extensionShape is not None:
        #             out = os.path.join(path, "{}_arbour_{}_{}_extension.stl".format(name, arbour, "top" if top else "bottom"))
        #             print("Outputting ", out)
        #             exporters.export(extensionShape, out)

class MantelClockPlates(SimpleClockPlates):
    '''
    Skeleton mantel clock
    '''
    def __init__(self, going_train, motion_works, plate_thick=8, back_plate_thick=None, pendulum_sticks_out=15, name="", centred_second_hand=False, dial=None,
                 moon_complication=None, second_hand=True, motion_works_angle_deg=-1, screws_from_back=None, layer_thick=LAYER_THICK_EXTRATHICK, escapement_on_front=False,
                 symetrical=False, style=PlateStyle.SIMPLE, fancy_pillars = False):
        self.symetrical = symetrical

        # enshake smaller because there's no weight dangling to warp the plates! (hopefully)
        #ended up having the escape wheel getting stuck, endshake larger again (errors from plate and pillar thickness printed with large layer heights?)
        super().__init__(going_train, motion_works, pendulum=None, gear_train_layout=GearTrainLayout.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
                         pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS,
                         pendulum_at_front=False, back_plate_from_wall=pendulum_sticks_out + 10 + plate_thick, fixing_screws=MachineScrew(4, countersunk=True),
                         centred_second_hand=centred_second_hand, pillars_separate=True, dial=dial, bottom_pillars=2, moon_complication=moon_complication,
                         second_hand=second_hand, motion_works_angle_deg=motion_works_angle_deg, endshake=1.5, compact_zigzag=True, screws_from_back=screws_from_back,
                         layer_thick=layer_thick, escapement_on_front=escapement_on_front, style=style, fancy_pillars = fancy_pillars)

        self.narrow_bottom_pillar = False
        self.foot_fillet_r = 2



        self.little_arm_to_motion_works = False

        if self.dial is not None:
            #hacky, cut away a bit from the top support so it won't crash into the anchor rod


            self.dial.subtract_from_supports = cq.Workplane("XY")
            #cut out bits from the pillars so they don't clash with any of the rods
            for arbor in self.arbors_for_plate:
                bearing_relative_to_dial = np_to_set(np.subtract(arbor.bearing_position[:2], self.hands_position))
                tall = 5
                #mirror because the dial is printed upside down
                bearing_relative_to_dial = (-bearing_relative_to_dial[0], bearing_relative_to_dial[1])
                self.dial.subtract_from_supports = self.dial.subtract_from_supports.add(cq.Workplane("XY").moveTo(bearing_relative_to_dial[0], bearing_relative_to_dial[1])\
                    .circle(arbor.bearing.outer_safe_d / 2).extrude(tall).translate((0, 0, self.dial.thick + self.dial.support_length - tall)))

            if self.centred_second_hand or True:
                #I'm not sure why this was only for centred second hand, it makes a lot of sense for all mantel dials?
                pillar_positions = []
                for side in [0,1]:
                    #relocate the pillars holding the dial
                    line = Line(self.bottom_pillar_positions[side], anotherPoint=self.top_pillar_positions[side])
                    intersections = line.intersection_with_circle(self.hands_position, self.dial.outside_d/2 - self.dial.dial_width/2)
                    pillar_positions += intersections
                #single screw in each pillar ought to be enoguh, hence putting each element in its own list
                #NOTE dial is "upside down" so invert x

                dial_fixing_positions = []

                for pos in pillar_positions:
                    pos_relative_to_hands = np_to_set(np.subtract(pos, self.hands_position))
                    dial_fixing_positions.append([(-pos_relative_to_hands[0], pos_relative_to_hands[1])])

                self.dial.override_fixing_positions(dial_fixing_positions)
                self.dial.support_d=15
                if self.style == PlateStyle.RAISED_EDGING:
                    self.dial.support_d = self.plate_width - self.edging_wide*2 - 1

    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        current plan: asymetric to be compact, with anchor arbor sticking out the top above the topmost pillar

        This is completely hard coded around a spring powered clock with 4 wheels and 2 powered wheels using the compact layout.
        if the spring clock is a success, it'll be worth making it more flexible
        '''

        bearingInfo = get_bearing_info(self.arbor_d)
        # TODO review this from old logic width of thin bit
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        if self.heavy or self.extra_heavy:
            self.plate_width *= 1.2

        self.bottom_pillar_positions = []
        self.top_pillar_positions = []
        self.bottom_pillar_r = self.plate_width/2
        self.top_pillar_r = self.min_plate_width/2
        # if self.fancy_pillars:
        #     self.top_pillar_r = self.bottom_pillar_r


        bottom_distance = self.arbors_for_plate[0].get_max_radius() + self.gear_gap + self.bottom_pillar_r
        #TODO check this doesn't collide with next wheel
        bottom_angle = -math.pi/4
        self.bottom_pillar_positions = [polar(math.pi - bottom_angle, bottom_distance), polar(bottom_angle, bottom_distance)]


        right_pillar_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.bearing_positions[1][:2])
        if self.symetrical:
            y = self.bearing_positions[-2][1] + self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r
            self.top_pillar_positions = [
                (self.bottom_pillar_positions[0][0], y),
                (self.bottom_pillar_positions[1][0], y)
            ]
        else:
            self.top_pillar_positions = [
                np_to_set(np.add(self.bearing_positions[self.going_train.powered_wheels + 1][:2], np.multiply(polar(math.pi * 0.525), self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
                np_to_set(np.add(self.bearing_positions[1][:2], np.multiply(right_pillar_line.dir, self.arbors_for_plate[1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
            ]
        print("top pillar distance gap: ", np.linalg.norm(np.subtract(self.top_pillar_positions[1], self.bearing_positions[-1][:2])) - self.top_pillar_r - self.arbors_for_plate[-1].get_max_radius())

    def calc_fixing_info(self):
        # fixing positions to plates and pillars together
        self.plate_top_fixings = []
        # (self.top_pillar_positions[0] - self.top_pillar_r / 2, self.top_pillar_positions[1]), (self.top_pillar_positions[0] + self.top_pillar_r / 2, self.top_pillar_positions[1])]
        for top_pillar_pos in self.top_pillar_positions:
            self.plate_top_fixings.append((top_pillar_pos[0], top_pillar_pos[1]))


        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottom_pillar_positions:
            self.plate_bottom_fixings.append((bottom_pillar_pos[0], bottom_pillar_pos[1]))

        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings

    def get_plate(self, back=True, for_printing=True, just_basic_shape=False, thick_override=-1):

        plate_thick = self.get_plate_thick(back=back)
        if thick_override > 0:
            plate_thick = thick_override

        plate = cq.Workplane("XY")

        main_arm_wide = self.plate_width
        medium_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2
        small_arm_wide = 8

        pillar_positions = self.top_pillar_positions + self.bottom_pillar_positions

        # for pillar in range(len(pillar_positions)):
        #     pillar_pos = pillar_positions[pillar]
        #     next_pillar_pos = pillar_positions[(pillar + 1)% len(pillar_positions)]
        #
        #link up the side pillars with each other
        for side in [0,1]:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bottom_pillar_positions[side]], wide=main_arm_wide, thick = plate_thick))
            plate = plate.union(get_stroke_line([self.bottom_pillar_positions[side], self.bearing_positions[0][:2]], wide=main_arm_wide, thick=plate_thick))

        # plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))
        if not back:
            #arch over the top
            #no point holding the bearing that isn't there for the anchor arbor!
            plate = plate.union(get_stroke_line([self.bearing_positions[-2][:2], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        if back:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1],self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        for foot_pos in self.bottom_pillar_positions:
            #give it little feet
            plate = plate.union(cq.Workplane("XY").rect(self.bottom_pillar_r*2, self.bottom_pillar_r).extrude(plate_thick).edges("|Z and <Y").fillet(self.foot_fillet_r)
                                .translate(foot_pos).translate((0,-self.bottom_pillar_r/2)))

        #barrel to minute wheel
        plate = plate.union(get_stroke_line([self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2]], wide=medium_arm_wide, thick=plate_thick))

        #across the front of the plate
        plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels+1][:2], self.bearing_positions[1][:2]], wide=medium_arm_wide, thick=plate_thick))

        #idea - 3 thin arms all linking to the second hand arbor? medium from barrel to minute wheel, thick just for the edges
        links = [self.bearing_positions[self.going_train.powered_wheels][:2],
                 self.bearing_positions[self.going_train.powered_wheels+3][:2],
                 self.top_pillar_positions[0]
                 ]
        for link_pos in links:
            plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels + 2][:2], link_pos], wide=small_arm_wide, thick=plate_thick))

        for i, pos in enumerate(self.bearing_positions):

            bearing_info = self.arbors_for_plate[i].bearing

            if not (i == len(self.bearing_positions)-1 and back):
                #only if not the back plate and the hole for the anchor arbor
                plate = plate.union(cq.Workplane("XY").circle(bearing_info.outer_d / 2 + self.bearing_wall_thick).extrude(plate_thick).translate(pos[:2]))

        plate = plate.union(cq.Workplane("XY").circle(self.going_train.powered_wheel.key_bearing.outer_d / 2 + self.bearing_wall_thick * 1.5).extrude(plate_thick))
        if just_basic_shape:
            return plate

        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())
            plate = plate.cut(self.get_text())
        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0, 0, -self.get_plate_thick(back=True) - self.plate_distance)))



        if not back:
            plate = self.front_additions_to_plate(plate, plate_thick)

        plate = self.punch_bearing_holes(plate, back)

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back == back:
            #spring powered, need the ratchet!
            screw = self.going_train.powered_wheel.ratchet.fixing_screws

            cutter = cq.Workplane("XY")

            for relative_pos in self.going_train.powered_wheel.ratchet.get_screw_positions() + self.going_train.powered_wheel.ratchet.get_little_plate_for_pawl_screw_positions():
                pos = np_to_set(np.add(self.bearing_positions[0][:2], relative_pos))
                #undecided if they need to be for tap die, they mgiht be enough without now there's a little plate for the pawl
                cutter = cutter.add(screw.get_cutter(with_bridging=True).translate(pos)) # for_tap_die=True,

            if back:
                cutter = cutter.rotate((0,0,0),(0,1,0),180).translate((0,0,plate_thick))

            plate = plate.cut(cutter)

        if for_printing:
            plate = self.apply_style_to_plate(plate, back=back)

        return plate

    def get_text_spaces(self):

        # (x,y,width,height, horizontal)
        spaces = []

        texts = [" ".join(self.texts[1:]), self.texts[0]]


        long_line = Line(self.bottom_pillar_positions[0], anotherPoint=self.top_pillar_positions[0])
        long_space_length = np.linalg.norm(np.subtract(self.top_pillar_positions[0], self.bottom_pillar_positions[0]))
        long_line_length = long_space_length - self.top_pillar_r - self.bottom_pillar_r - 1
        text_height = self.plate_width * 0.9
        long_centre = np_to_set(np.add(long_line.start, np.multiply(long_line.dir, long_space_length / 2)))
        long_angle = long_line.get_angle()

        short_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.top_pillar_positions[1])
        short_space_length = np.linalg.norm(np.subtract(self.bearing_positions[1][:2], self.bottom_pillar_positions[1]))
        short_line_length = short_space_length - 10
        short_centre = np_to_set(np.add(short_line.start, np.multiply(short_line.dir, short_space_length / 2)))
        short_angle = short_line.get_angle() + math.pi


        # three along the wide bit at the bottom and one above
        spaces.append(TextSpace(long_centre[0], long_centre[1], text_height,long_line_length, angle_rad=long_angle))
        spaces.append(TextSpace(short_centre[0], short_centre[1], text_height, short_line_length, angle_rad=short_angle))
        # spaces.append(TextSpace(bottom_pos[0], (bottom_pos[1] + (chain_pos[1] - chain_space)) / 2, text_height, chain_pos[1] - chain_space - bottom_pos[1], horizontal=False))
        # spaces.append(TextSpace(bottom_pos[0] + self.bottom_pillar_r - self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))
        #
        # spaces.append(TextSpace(chain_pos[0], (first_arbour_pos[1] - arbour_space + chain_pos[1] + chain_space) / 2, self.plate_width * 0.9, first_arbour_pos[1] - arbour_space - (chain_pos[1] + chain_space), horizontal=False))

        for i, text in enumerate(texts):
            spaces[i].set_text(text)
        return spaces

    def get_screwhole_positions(self):
        '''
        this doesn't hang on the wall, so no wall fixings
        '''
        return []

    def get_wall_standoff(self, top=True, for_printing=True):
        '''
        not really a wall standoff, but the bit that holds the pendulum at the top
        '''
        if not top:
            return cq.Workplane("XY")

        width = self.min_plate_width

        plate_thick = self.get_plate_thick(standoff=True)
        #to match the plate
        standoff = get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2], self.top_pillar_positions[1]], wide=width, thick=plate_thick)
        clockwise = True

        for pillar_pos in self.top_pillar_positions:
            if self.fancy_pillars:
                standoff = standoff.union(SimpleClockPlates.fancy_pillar(self.top_pillar_r, self.back_plate_from_wall - plate_thick, clockwise=clockwise).translate(pillar_pos).translate((0, 0, plate_thick)))
                clockwise = not clockwise
            else:
                standoff = standoff.union(cq.Workplane("XY").circle(self.top_pillar_r-0.0001).extrude(self.back_plate_from_wall-plate_thick).translate((0,0,plate_thick)).translate(pillar_pos))
        standoff = self.cut_anchor_bearing_in_standoff(standoff)

        standoff = standoff.translate((0,0,-self.back_plate_from_wall))
        standoff = standoff.cut(self.get_fixing_screws_cutter())

        return standoff

    def get_bottom_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane

        overriding default pillars to give ones with flat bottoms
        '''
        pillar = cq.Workplane("XY").moveTo(self.bottom_pillar_r,0).lineTo(self.bottom_pillar_r, -self.bottom_pillar_r + self.foot_fillet_r)\
            .radiusArc((self.bottom_pillar_r - self.foot_fillet_r, -self.bottom_pillar_r), self.foot_fillet_r).\
            lineTo(-self.bottom_pillar_r + self.foot_fillet_r, -self.bottom_pillar_r).radiusArc((-self.bottom_pillar_r, -self.bottom_pillar_r+self.foot_fillet_r), self.foot_fillet_r).\
            lineTo(-self.bottom_pillar_r, 0).radiusArc((self.bottom_pillar_r,0), self.bottom_pillar_r).close()



        if flat:
            return pillar


        if self.fancy_pillars:
            pillar = SimpleClockPlates.fancy_pillar(self.bottom_pillar_r, self.plate_distance)
        else:
            pillar = pillar.extrude(self.plate_distance)

        # hack - assume screws are in the same place for both pillars for now
        pillar = pillar.cut(self.get_fixing_screws_cutter().translate((-self.bottom_pillar_positions[0][0], -self.bottom_pillar_positions[0][1], -self.get_plate_thick(back=True))))


        return pillar

class RoundClockPlates(SimpleClockPlates):
    '''
    Plan for a traditional-ish movement shape on legs, so the pendulum will be visible below the dial.
    Inspired by some Brocot clocks I've seen

    Original plan was for a circular movement, but ended up with semicircular when adding legs, set fully_round True for fully round

    Only been designed to work well with springs so far - wouldn't be much work to support cord

    This was based on a copy of MantelClockPlates - I think it's going to be similar, but not similar enough to warrant extending or being a set of options
    '''
    def __init__(self, going_train, motion_works, plate_thick=8, back_plate_thick=None, pendulum_sticks_out=15, name="", centred_second_hand=False, dial=None,
                 moon_complication=None, second_hand=True, layer_thick=LAYER_THICK, escapement_on_front=False, vanity_plate_radius=-1, motion_works_angle_deg=-1,
                 leg_height=150, endshake=1.25, fully_round=False, style=PlateStyle.SIMPLE, fancy_pillars=False, standoff_pillars_separate=False):
        '''

        '''
        self.leg_height = leg_height
        #review this later, but for now at least its a different variable
        self.wall_mounted = leg_height == 0
        self.fully_round = fully_round
        # enshake smaller because there's no weight dangling to warp the plates! (hopefully)
        #ended up having the escape wheel getting stuck, endshake larger again (errors from plate and pillar thickness printed with large layer heights?)
        #was force_escapement_above_hands because the gear train looks better on a circular plate that way ( now got forcing_escape_wheel_slightly_off_centre in bearing placement)
        super().__init__(going_train, motion_works, pendulum=None, gear_train_layout=GearTrainLayout.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
                         pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS,
                         pendulum_at_front=False, back_plate_from_wall=pendulum_sticks_out + 10 + plate_thick, fixing_screws=MachineScrew(4, countersunk=True),
                         centred_second_hand=centred_second_hand, pillars_separate=True, dial=dial, bottom_pillars=2, moon_complication=moon_complication,
                         second_hand=second_hand, motion_works_angle_deg=motion_works_angle_deg, endshake=endshake, compact_zigzag=True, screws_from_back=None,
                         layer_thick=layer_thick, escapement_on_front=escapement_on_front, vanity_plate_radius=vanity_plate_radius, force_escapement_above_hands=escapement_on_front, style=style,
                         fancy_pillars=fancy_pillars, standoff_pillars_separate=standoff_pillars_separate)

        if self.wall_mounted:
            self.text_on_standoffs=True

        self.narrow_bottom_pillar = False
        self.foot_fillet_r = 2
        self.little_arm_to_motion_works = True
        self.little_plate_for_pawl = False
        fixings = 3
        # self.vanity_plate_fixing_positions = [polar(angle, self.vanity_plate_radius-self.vanity_plate_pillar_r) for angle in [math.pi/6 + i*(math.pi*2/fixings) for i in range(fixings)]]
        #ended up using pillar positions instead
        self.vanity_plate_fixing_positions = []#[(-self.radius,self.hands_position[1]), (self.radius, self.hands_position[1])]
        self.vanity_plate_pillar_r=self.pillar_r

        #front anchor holder will have little arms extended from the front plate
        anchor_distance = distance_between_two_points(self.hands_position, self.bearing_positions[-1][:2])
        self.anchor_holder_arc_angle = math.pi * 0.3
        self.anchor_holder_fixing_points = [np_to_set(np.add(self.hands_position, polar(math.pi/2 + i*self.anchor_holder_arc_angle/2, anchor_distance))) for i in [-1, 1]]


        # centre = self.bearing_positions[self.going_train.powered_wheels][:2]
        # self.radius = 1
        # for bearing_pos in self.bearing_positions:
        #     distance = distance_between_two_points(centre, bearing_pos[:2])
        #     if distance > self.radius:
        #         self.radius = distance
        '''
        TODO
        set ratchet and pawl angle here, rather than user config
        consider extra thick inside plate just to hold the screws for the ratchet? avoid the extra mini plate DONE
        
        '''

        if self.dial is not None and self.escapement_on_front:
            self.dial.add_to_back = self.get_front_anchor_bearing_holder().translate((-self.hands_position[0],-self.hands_position[1], self.dial.thick))


        if self.dial is not None:
            #TODO more general purpose support for different relative sizes of plates and dial and different pillar locations.
            #this works for now

            #not evenly space so we don't clash with pillars
            angles = [math.pi/2 + math.pi/8, math.pi/2 - math.pi/8, math.pi*1.5 + math.pi/8, math.pi*1.5 - math.pi/8]
            if self.gear_train_layout == GearTrainLayout.COMPACT and not self.escapement_on_front and self.going_train.wheels == 4 and not self.second_hand:
                #little bit brittle logic here, if we have two little arms on teh front because we're forcing_escape_wheel_slightly_off_centre
                #line up dial supports with the little arms
                for i in range(2):
                    bearing_relative_pos = np_to_set(np.subtract(self.bearing_positions[-3 + i][:2], self.hands_position))
                    bearing_angle = math.atan2(bearing_relative_pos[1], bearing_relative_pos[0])
                    angles[i] = bearing_angle

            dial_fixings_relative_to_dial = [polar(angle, self.radius) for angle in angles]

            self.dial_fixing_positions = [np_to_set(np.add(pos, self.hands_position)) for pos in dial_fixings_relative_to_dial]

            # array of arrays because we only want one screw per pillar here
            self.dial.override_fixing_positions([[pos] for pos in dial_fixings_relative_to_dial])
            self.dial.support_d = 15
            if self.style == PlateStyle.RAISED_EDGING:
                self.dial.support_d = self.plate_width - self.edging_wide * 2 - 1

        self.front_anchor_holder_part_of_dial = True

    # def need_front_anchor_bearing_holder(self):
    #     if self.escapement_on_front:
    #         #only need a separa
    #         return self.dial is None

    def get_pillar(self, top=True, flat=False):
        '''
        they're all the same on this design!
        '''

        pillar_length = self.plate_distance

        if self.fancy_pillars:
            pillar = SimpleClockPlates.fancy_pillar(self.pillar_r, pillar_length)
        else:
            pillar = cq.Workplane("XY").circle(self.pillar_r).circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).extrude(pillar_length)

        return pillar

    def get_legs_pillar(self):

        pillar_length = self.get_plate_thick(back=True) + self.get_plate_thick(back=False) + self.plate_distance

        pillar = cq.Workplane("XY").circle(self.pillar_r).extrude(pillar_length)
        pillar = pillar.union(cq.Workplane("XY").moveTo(0, -(self.pillar_r + self.foot_fillet_r)/2).rect(self.pillar_r*2, self.pillar_r + self.foot_fillet_r).extrude(pillar_length).edges("|Z and <Y").fillet(self.foot_fillet_r))

        pillar = pillar.faces(">Z").workplane().circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).cutThruAll()

        return pillar


    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        All pillars on this clock will be identical, with no real meanign behind top and bottom pillar, but to fit in with the other plate designs they'll still
        be divided into top and bottom pillars

        currently assumes spring powered with two powered wheels, TODO make more robust
        '''

        # can make it big enough to fully encompass everything, but we still barely have space for a bottom right pillar and then its' just lots of empty space
        # so instead, make it big enough to hold the barrel and I'll poke a bit out the top for the anchor, and just skip the bottom right pillar entirely
        # worth a shot, anyway
        #



        bearingInfo = get_bearing_info(self.arbor_d)
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        barrel_distance = distance_between_two_points(self.bearing_positions[self.going_train.powered_wheels][:2], self.bearing_positions[0][:2])

        # used in base class
        self.pillar_r = self.plate_width / 2
        # various shared bits expect these
        self.top_pillar_r = self.pillar_r
        self.bottom_pillar_r = self.pillar_r

        # self.radius = (self.arbors_for_plate[0].get_max_radius() + self.pillar_r + 3)
        self.bottom_pillar_distance = (self.arbors_for_plate[0].get_max_radius() + self.pillar_r + 3)*2
        self.radius = self.bottom_pillar_distance/2



        # self.radius = barrel_distance + self.arbors_for_plate[0].bearing.outer_d/2 + self.bearing_wall_thick - self.plate_width/2





        centre = self.bearing_positions[self.going_train.powered_wheels][:2]
        # lines_to_bearings = [Line(centre, anotherPoint=bearing_pos[:2]) for bearing_pos in self.bearing_positions]
        #
        # barrel_angle = self.arbors_for_plate[0].get_max_radius()/self.radius
        # pillar_angle = (self.pillar_r*2) / self.radius
        #
        # # #put the bottom pillar as close as we can (ish cba to calculate this exactly) to the barrel wheel
        # # bottom_pillar_angle = math.pi*1.5 - barrel_angle - pillar_angle*0.75
        # #above the second powered wheel
        # second_pillar_angle = lines_to_bearings[1].get_angle() * 0.5 + lines_to_bearings[5].get_angle() * 0.5

        #find where wheels 3 and 4 meet, then put the pillar in that direction
        points = get_circle_intersections(self.bearing_positions[3][:2], self.arbors_for_plate[3].get_max_radius(),
                                          self.bearing_positions[4][:2], self.arbors_for_plate[4].get_max_radius())
        #find furthest point
        if distance_between_two_points(points[0], centre) > distance_between_two_points(points[1], centre):
            point = points[0]
        else:
            point = points[1]
        line_to_point = Line(centre, anotherPoint=point)

        self.bottom_arm_wide = self.arbors_for_plate[0].bearing.outer_d + self.bearing_wall_thick*2


        barrel_pos = self.bearing_positions[0]

        y = barrel_pos[1] - self.bottom_arm_wide/2 + self.pillar_r
        pillar_distance = self.radius

        if self.fully_round:
            #pillars inline with the powered wheel
            y = barrel_pos[1]
            pillar_distance = self.bottom_pillar_distance/2

            if not self.going_train.powered_wheels > 1:
                raise ValueError("TODO calculate pillar positions for non eight day spring clocks")
            #assuming spring driven here
            b = self.arbors_for_plate[0].get_max_radius() + self.pillar_r + 1
            a = self.arbors_for_plate[0].arbor.distance_to_next_arbour
            c = self.arbors_for_plate[1].get_max_radius() + self.pillar_r + 1
            # cosine law
            angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
            second_wheel_from_first = np_to_set(np.subtract(self.bearing_positions[1][:2], self.bearing_positions[0][:2]))
            second_wheel_from_first_angle = math.atan2(second_wheel_from_first[1], second_wheel_from_first[0])
            final_angle = second_wheel_from_first_angle - angle
            bottom_pillar_pos = np_to_set(np.add(self.bearing_positions[0][:2], polar(final_angle, b)))
            self.radius = distance_between_two_points(bottom_pillar_pos, self.bearing_positions[self.going_train.powered_wheels][:2])
            self.bottom_pillar_positions = [
                bottom_pillar_pos,
                (-bottom_pillar_pos[0], bottom_pillar_pos[1]),
            ]
        else:

            self.bottom_pillar_positions = [
                (barrel_pos[0] - pillar_distance, y),
                (barrel_pos[0] + pillar_distance, y),
            ]



        #just above second power wheel
        # right_pillar_pos = np_to_set(np.add(centre, polar(second_pillar_angle, self.radius)))

        left_pillar_pos = np_to_set(np.add(centre, polar(line_to_point.get_angle(), self.radius)))

        #no real need to treat pillars differently, but the base class does so it makes some of the other logic easier
        self.top_pillar_positions = [
            #top two first because the anchor arbor holder assumes two top pillars
            #just above (ish) the second power wheel
            # try making them symetric instead
            (-left_pillar_pos[0], left_pillar_pos[1]),
            left_pillar_pos,


            # np_to_set(np.add(centre, polar(bottom_pillar_angle, self.radius))),
        ]


        self.all_pillar_positions = self.bottom_pillar_positions + self.top_pillar_positions
        if self.wall_mounted:
            self.leg_pillar_positions = []
        else:
            self.leg_pillar_positions = [np_to_set(np.add((0, -self.leg_height), pillar)) for pillar in self.bottom_pillar_positions]

    def get_fixing_screws_cutter(self):
        '''
        much more simple on this clock
        '''
        cutter = cq.Workplane("XY")

        # bottom_total_length = self.back_plate_from_wall + self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)
        # top_total_length = bottom_total_length + self.get_front_anchor_bearing_holder_total_length()
        bottom_total_length = top_total_length = 1000
        for pillar in self.all_pillar_positions:
            pillar_cutter = cq.Workplane("XY").circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).extrude(top_total_length).translate(pillar).translate((0,0,-top_total_length/2))
            cutter = cutter.add(pillar_cutter)

        # for screw_pos in self.anchor_holder_fixing_points:
        #     #these are symetric so don't need to worry much about mixing up which side they're on
        #     cutter = cutter.add(self.fi)

        if self.wall_mounted:
            #TODO make this more properly configurable for all plates, but for now we're using threaded rod rather than screws so we can attach the dial
            #and have shiny brass dome nuts on the front
            # bottom_nut_base_z, top_nut_base_z, bottom_nut_hole_height, top_nut_hole_height = self.get_fixing_screw_nut_info()
            top_nut_base_z = - self.back_plate_from_wall
            #THOUGHT: this might be thin enough that the standoff pillars could be seperate
            top_nut_hole_height = self.fixing_screws.get_nut_height() + 1
            for pos in self.all_pillar_positions:
                cutter = cutter.add(self.fixing_screws.get_nut_cutter(height=top_nut_hole_height, with_bridging=True).translate((pos[0], pos[1], top_nut_base_z)))

        return cutter

    def calc_fixing_info(self):
        #not sure if we actually need this in this class
        self.plate_top_fixings = self.top_pillar_positions[:]
        self.plate_bottom_fixings = self.bottom_pillar_positions[:]
        self.plate_fixings = self.all_pillar_positions[:]

    def get_vanity_plate(self, for_printing=True):

        centre_hole_r = self.motion_works.get_widest_radius() + 2

        plate = cq.Workplane("XY").circle(self.vanity_plate_radius).circle(centre_hole_r).extrude(self.vanity_plate_thick)

        # for pillar_pos in self.vanity_plate_fixing_positions:
        #     #invert x because we're upside down
        #     plate = plate.union(cq.Workplane("XY").moveTo(-pillar_pos[0] - self.hands_position[0], pillar_pos[1] - self.hands_position[1]).circle(self.vanity_plate_pillar_r).extrude(self.vanity_plate_base_z + self.vanity_plate_thick))
        #     plate = plate.faces(">Z").workplane().moveTo(-pillar_pos[0] - self.hands_position[0], pillar_pos[1] - self.hands_position[1]).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()

        hole_r = self.fixing_screws.get_rod_cutter_r(loose=True)
        #removing the front legs
        pillar_height = self.vanity_plate_base_z - self.plate_thick

        for pillar_pos in self.bottom_pillar_positions:
            pillar_pos = np_to_set(np.subtract(pillar_pos, self.hands_position))
            plate = plate.union(get_stroke_line([self.hands_position, pillar_pos], wide=self.pillar_r*2, thick=self.vanity_plate_thick))
            plate = plate.union(cq.Workplane("XY").circle(self.pillar_r).circle(hole_r).extrude(pillar_height + self.vanity_plate_thick).translate(pillar_pos))
            plate = plate.faces(">Z").workplane().moveTo(pillar_pos[0], pillar_pos[1]).circle(hole_r).cutThruAll()

        if self.escapement_on_front:
            #gaps for the front anchor holder
            for pos in self.anchor_holder_fixing_points:
                relative_pos = np_to_set(np.subtract(pos, self.hands_position))
                plate = plate.cut(cq.Workplane("XY").moveTo(relative_pos[0], relative_pos[1]).circle(self.pillar_r + 1).extrude(self.vanity_plate_thick))

        #key hole
        key_hole_d = self.winding_key.get_key_outer_diameter() + 4
        key_hole_pos = np_to_set(np.subtract(self.bearing_positions[0][:2], self.hands_position))
        plate = plate.faces(">Z").workplane().moveTo(key_hole_pos[0], key_hole_pos[1]).circle(key_hole_d/2).cutThruAll()

        #hole for escape wheel
        if self.escapement_on_front:
            escapement_hole_pos = np_to_set(np.subtract(self.bearing_positions[-2][:2], self.hands_position))
            anchor_pos = np_to_set(np.subtract(self.bearing_positions[-1][:2], self.hands_position))

            #bit hacky, just assuming we know the diameters
            plate = plate.faces(">Z").workplane().moveTo(escapement_hole_pos[0], escapement_hole_pos[1]).circle(self.arbors_for_plate[-2].arbor_d*2 + 1).cutThruAll()

            anchor_hole_d = self.arbors_for_plate[-1].direct_arbor_d + 2

            #slot rather than hole so it should always be possible to assemble the clock
            plate = plate.cut(get_stroke_line([anchor_pos, (anchor_pos[0], anchor_pos[1]+100)], wide=anchor_hole_d, thick=self.vanity_plate_thick))

        if not for_printing:
            # return cq.Workplane("XY").circle(100).extrude(10)
            plate = plate.rotate((0,0,0), (0,1,0), 180)
            plate = plate.translate((0,0,self.vanity_plate_base_z + self.vanity_plate_thick))

        return plate

    def get_plate(self, back=True, for_printing=True, just_basic_shape=False, thick_override=-1):

        plate_thick = self.get_plate_thick(back=back)
        if thick_override > 0:
            plate_thick = thick_override

        centre = self.bearing_positions[self.going_train.powered_wheels][:2]

        main_arm_wide = self.plate_width
        medium_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2
        # small_arm_wide = get_bearing_info(2).outer_d + self.bearing_wall_thick * 2
        small_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2 - 1

        # plate = cq.Workplane("XY").moveTo(self.hands_position[0], self.hands_position[1]).circle(self.radius+main_arm_wide/2).circle(self.radius-main_arm_wide/2).extrude(plate_thick)

        if self.fully_round:
            plate = cq.Workplane("XY").circle(self.radius + main_arm_wide/2).circle(self.radius - main_arm_wide/2).extrude(plate_thick).translate(self.hands_position)

            #if there isn't only going to be a tiny gap under the arm, just make the whole bit solid
            extra_width_at_bottom = 0
            bottom_of_arm_y = self.bearing_positions[0][1] - self.bottom_arm_wide/2
            top_of_circle_y = self.hands_position[1] - self.radius + main_arm_wide/2
            if bottom_of_arm_y - top_of_circle_y < 5:
                extra_width_at_bottom=5

            bottom_arm = cq.Workplane("XY").rect(self.radius * 2, self.bottom_arm_wide + extra_width_at_bottom).extrude(plate_thick).translate(self.bearing_positions[0][:2]).translate((0,-extra_width_at_bottom))
            plate = plate.union(bottom_arm.intersect(cq.Workplane("XY").circle(self.radius + main_arm_wide/2).extrude(plate_thick).translate(self.hands_position)))
        else:
            #semicircular with rectangle on the bottom
            plate = get_stroke_arc((self.radius,centre[1]), (-self.radius,centre[1]), self.radius, main_arm_wide, plate_thick)

            plate = plate.union(get_stroke_line([(self.radius,centre[1]), self.bottom_pillar_positions[1], self.bottom_pillar_positions[0], [-self.radius,centre[1]]], thick=plate_thick, wide=medium_arm_wide))

            #beef up bottom arm
            plate = plate.union(cq.Workplane("XY").rect(self.radius*2, self.bottom_arm_wide).extrude(plate_thick).translate(self.bearing_positions[0][:2]))

        #vertical link
        # plate = plate.union(cq.Workplane("XY").rect(medium_arm_wide, self.radius*2).extrude(plate_thick))
        line_wide = medium_arm_wide

        for i, bearing_pos in enumerate(self.bearing_positions):
            if i == self.going_train.powered_wheels:
                #the minute wheel, in the centre
                continue
            if i > self.going_train.powered_wheels:
                line_wide = small_arm_wide

            if distance_between_two_points(centre, bearing_pos[:2]) - self.arbors_for_plate[i].bearing.outer_d/2 > self.radius - self.pillar_r:
                #this bearing will be in the outer circle
                continue

            if i == len(self.bearing_positions) - 1 and not self.second_hand and not self.force_escapement_above_hands and back and self.going_train.wheels > 3:
                #don't need a bit of plate to support just a hole for the anchor
                #could do with better than repeating the logic in calc_bearing_positions, very brittle
                continue

            line = Line(centre, anotherPoint=bearing_pos[:2])
            end = np_to_set(np.add(polar(line.get_angle(), self.radius), centre))

            if i == len(self.bearing_positions) - 1 and not back and not self.escapement_on_front and distance_between_two_points(bearing_pos[:2], centre) > self.radius:
                #the anchor needs something to support it on the front plate
                end = bearing_pos[:2]

            plate = plate.union(get_stroke_line([centre, end], line_wide, plate_thick))

        if just_basic_shape:
            return plate

        self.beefed_up_pawl_thickness = 0

        plate = plate.cut(self.get_fixing_screws_cutter())
        if back:

            if not self.text_on_standoffs:
                plate = plate.cut(self.get_text())

            if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back:
                #beef up the plate where the pawl screw goes through so we don't need to have an extra plate on the back to make it strong enough
                #only possible at the back unless I change where the barrel is (TODO support power at back again...)
                pawl_pos = np_to_set(np.add(self.bearing_positions[0][:2], self.going_train.powered_wheel.ratchet.get_pawl_screw_position()))
                #should probably do somethign sensible like work out how much space there actually is between the nearby wheel and the plate
                self.beefed_up_pawl_thickness = 7.5


                plate = (plate.faces(">Z").workplane().moveTo(-pawl_pos[0], pawl_pos[1]).circle(self.plate_width/2)
                         .workplane(offset=self.beefed_up_pawl_thickness).moveTo(-pawl_pos[0], pawl_pos[1]).circle(self.plate_width*0.4).loft(combine=True))
        else:
            if self.need_front_anchor_bearing_holder():
                for pos in self.anchor_holder_fixing_points:
                    line = Line(centre, anotherPoint=pos)
                    start = np_to_set(np.add(centre, polar(line.get_angle(), self.radius)))
                    plate = plate.union(get_stroke_line([start, pos], wide=self.pillar_r*2, thick=plate_thick))
                    plate = plate.cut(self.small_fixing_screws.get_cutter().translate(pos))

            plate = self.front_additions_to_plate(plate)


        plate = self.punch_bearing_holes(plate, back)

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back == back:
            #spring powered, need the ratchet!
            screw = self.going_train.powered_wheel.ratchet.fixing_screws

            cutter = cq.Workplane("XY")

            #not using the little extra pawl plate on this plate, going to instead make the back plate thicker around the ratchet
            for relative_pos in self.going_train.powered_wheel.ratchet.get_screw_positions():
                extra_z = 0
                if relative_pos == self.going_train.powered_wheel.ratchet.get_pawl_screw_position():
                    extra_z = -self.beefed_up_pawl_thickness
                pos = np_to_set(np.add(self.bearing_positions[0][:2], relative_pos))
                pos = (pos[0], pos[1], extra_z)
                #undecided if they need to be for tap die, they mgiht be enough without now there's a little plate for the pawl
                cutter = cutter.add(screw.get_cutter(with_bridging=True).translate(pos)) # for_tap_die=True,

            if back:
                cutter = cutter.rotate((0,0,0),(0,1,0),180).translate((0,0,plate_thick))

            plate = plate.cut(cutter)

            if for_printing and not back:
                plate = plate.rotate((0,0,0),(0,1,0),180).translate((0,0,plate_thick))


        return plate

    def get_legs(self, back=True):
        '''

        '''
        thick = self.plate_thick
        width = self.pillar_r*2
        legs = get_stroke_line([self.bottom_pillar_positions[0], self.leg_pillar_positions[0], self.leg_pillar_positions[1], self.bottom_pillar_positions[1]], wide=width, thick=thick)

        for pos in self.leg_pillar_positions:
            legs = legs.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).rect(width,width+self.foot_fillet_r*2).extrude(thick).edges("|Z and <Y").fillet(self.foot_fillet_r))

        legs = legs.cut(self.get_fixing_screws_cutter())

        for pillar_pos in self.leg_pillar_positions:
            if back:
                legs = legs.faces(">Z").workplane().moveTo(pillar_pos[0], pillar_pos[1]).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()
            else:
                legs = legs.cut(self.fixing_screws.get_cutter(loose=True).rotate((0,0,0),(0,1,0),180).translate((pillar_pos[0], pillar_pos[1],thick)))



        return legs

    def get_text_spaces(self):
        spaces = []
        texts = self.texts
        if not self.wall_mounted:
            # (x,y,width,height, horizontal)


            texts = ["{}\n{}".format(self.texts[0], self.texts[1]), "{}\n{}".format(self.texts[2], self.texts[3])]

            y_offset = 0
            if self.leg_height > 0:
                # shift up to avoid join with legs
                y_offset = self.pillar_r - abs(self.bearing_positions[0][1] - self.bottom_pillar_positions[0][1])

            text_centre_y = average_of_two_points(self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2])[1] + y_offset/2
            text_length = distance_between_two_points(self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2]) - y_offset

            spaces.append(TextSpace(-self.radius, text_centre_y, self.plate_width*0.9, text_length, angle_rad=math.pi/2))
            spaces.append(TextSpace(self.radius, text_centre_y, self.plate_width*0.9, text_length, angle_rad=math.pi/2))

        else:
            top_width = math.fabs(self.top_pillar_positions[0][0]) - self.fixing_screws.get_nut_containing_diameter()/2 - self.wall_fixing_screw_head_d/2 - 1

            spaces.append(TextSpace(self.top_pillar_positions[0][0] / 2, self.top_pillar_positions[0][1], top_width, self.pillar_r * 1.8, horizontal=True))
            spaces.append(TextSpace(self.top_pillar_positions[1][0] / 2, self.top_pillar_positions[1][1], top_width, self.pillar_r * 1.8, horizontal=True))

            bottom_width = math.fabs(self.bottom_pillar_positions[0][0]) - self.fixing_screws.get_nut_containing_diameter()/2 - self.wall_fixing_screw_head_d/2 - 1

            spaces.append(TextSpace(self.bottom_pillar_positions[0][0] / 2, self.bottom_pillar_positions[0][1], bottom_width, self.pillar_r * 1.8, horizontal=True))
            spaces.append(TextSpace(self.bottom_pillar_positions[1][0] / 2, self.bottom_pillar_positions[1][1], bottom_width, self.pillar_r * 1.8, horizontal=True))

        for i, text in enumerate(texts):
            spaces[i].set_text(text)
        return spaces

    def get_screwhole_positions(self):
        '''
        returns [(x,y, supported),]
        '''
        if not self.wall_mounted:
            return []


        if self.bearing_positions[-1][1] - self.top_pillar_positions[0][1] < 20:
            top_y = self.top_pillar_positions[0][1]
        else:
            #halway between top pillar y and anchor bearing
            top_y = (self.bearing_positions[-1][1] + self.top_pillar_positions[0][1]) / 2

        return [(0, top_y, True), (0, self.bottom_pillar_positions[0][1], True)]

    def get_front_anchor_bearing_holder(self, for_printing=True):
        '''
        Sufficiently different fron back holder to be a different function.
        This will be printed as part of the dial and it must be possible to attach after the rest of teh clock
        has been assembled (including the vanity plate). Otherwise I think it will
        be impossible to assemble the clock


        note assumes that anchor_holder_fixing_points are symetric
        '''
        holder = cq.Workplane("XY")

        anchor_distance = distance_between_two_points(self.hands_position, self.bearing_positions[-1][:2])
        anchor_holder_fixing_points = self.anchor_holder_fixing_points

        holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arbors_for_plate[-1].bearing)

        top_z = self.get_front_anchor_bearing_holder_total_length()
        if self.dial is not None:
            #if a dial, butt up exactly to the bottom of the dial so the two peices can be combined
            if self.dial_z > top_z:
                need_extra = self.dial_z - top_z
                top_z = self.dial_z
                holder_thick += need_extra
            else:
                raise ValueError("Dial isn't far enough away to fit front anchor holder. Extend motion works extra_height by at least {}mm".format(top_z - self.dial_z))

        

        holder = get_stroke_arc(self.anchor_holder_fixing_points[0], self.anchor_holder_fixing_points[1], anchor_distance, self.pillar_r*2, holder_thick)

        holder = holder.cut(self.get_bearing_punch(holder_thick, bearing=get_bearing_info(self.arbors_for_plate[-1].arbor.arbor_d)).translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1])))
        
        # TODO NUTS - embedded or try slot in from the side?
        for pos in self.anchor_holder_fixing_points:
            #don't need to take into account holder thick because wer're unioning with it
            holder = holder.union(cq.Workplane("XY").circle(self.pillar_r).extrude(top_z).translate(pos))
            holder = holder.faces(">Z").workplane().moveTo(pos[0], pos[1]).circle(self.small_fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()
            nut_hole_deep = self.small_fixing_screws.get_nut_height()+1
            holder = holder.cut(self.small_fixing_screws.get_nut_cutter(height=nut_hole_deep, with_bridging=True, layer_thick=self.layer_thick).translate((pos[0], pos[1], top_z/2 - nut_hole_deep/2)))

        if not for_printing:

            holder = holder.rotate((0,0,0), (0,1,0),180).translate((0,0,self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance + top_z))

        return holder

    def get_wall_standoff(self, top=True, for_printing=True):
        if not top:
            if self.wall_mounted:
                return self.get_bottom_wall_standoff(for_printing=for_printing)
            else:
                return cq.Workplane("XY")
        return self.get_back_anchor_holder(for_printing=for_printing)


    def get_bottom_wall_standoff(self, for_printing=True):
        plate_thick = self.get_plate_thick(standoff=True)

        standoff = get_stroke_line(self.bottom_pillar_positions, wide=self.pillar_r*2, thick = plate_thick)

        wall_fixing_pos = self.get_screwhole_positions()[1][:2]#(0, self.bottom_pillar_positions[0][1])

        #filled in semicircle. I think it might be overkill:
        # standoff = get_stroke_arc(self.bottom_pillar_positions[0], self.bottom_pillar_positions[1], self.radius, wide=self.pillar_r*2, thick=plate_thick, fill_in=self.wall_mounted)
        #
        # # sagitta (copypasted from get_stroke_arc)
        # l = distance_between_two_points(self.bottom_pillar_positions[1], self.bottom_pillar_positions[0])
        # s = self.radius - math.sqrt(self.radius ** 2 - 0.25 * l ** 2)
        # wall_fixing_pos = (0, self.bottom_pillar_positions[0][1] - s / 2)

        standoff = self.cut_wall_fixing_hole(standoff, wall_fixing_pos, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=True, plate_thick=plate_thick)

        if not self.standoff_pillars_separate:
            standoff = standoff.union(self.get_standoff_pillars(top=False).translate((0,0,self.back_plate_from_wall)))



        standoff = standoff.translate((0, 0, -self.back_plate_from_wall))
        if self.text_on_standoffs:
            standoff = standoff.cut(self.get_text(top_standoff=False))
        standoff = standoff.cut(self.get_fixing_screws_cutter())

        return standoff
    def get_back_anchor_holder(self, for_printing=True):
        '''
        the bit that holds the pendulum at the top
        '''


        width = self.pillar_r*2

        anchor_distance = distance_between_two_points(self.hands_position, self.bearing_positions[-1][:2])


        anchor_holder_fixing_points = self.top_pillar_positions

        curve_ends = []
        for fixing_pos in anchor_holder_fixing_points:
            line_up = Line(fixing_pos, direction=(0,1))
            curve_ends += line_up.intersection_with_circle(circle_centre=self.hands_position, circle_r = anchor_distance)

        # curve_ends = [np_to_set(np.add(self.hands_position, polar(math.pi/2 + i*self.anchor_holder_arc_angle/2, anchor_distance))) for i in [-1, 1]]

        plate_thick = self.get_plate_thick(standoff=True)
        #
        # standoff = get_stroke_line([anchor_holder_fixing_points[0], curve_ends[0]], wide=width, thick=plate_thick)
        # standoff = standoff.union(get_stroke_line([anchor_holder_fixing_points[1], curve_ends[1]], wide=width, thick=plate_thick))
        # standoff = standoff.union(get_stroke_arc(curve_ends[0], curve_ends[1], anchor_distance, wide=width, thick=plate_thick))

        #using sagitta to work out radius of curve that links all points
        l = distance_between_two_points(anchor_holder_fixing_points[0], anchor_holder_fixing_points[1])
        s = abs(anchor_holder_fixing_points[0][1] - self.bearing_positions[-1][1])
        r = s/2 + (l**2)/(8*s)

        standoff = get_stroke_arc(anchor_holder_fixing_points[0], anchor_holder_fixing_points[1], r, wide=width, thick=plate_thick)#, fill_in=self.wall_mounted)


        if self.wall_mounted:
            standoff = standoff.union(get_stroke_line(anchor_holder_fixing_points, width, plate_thick))
            standoff = standoff.union(get_stroke_line([self.bearing_positions[-1][:2], (0, anchor_holder_fixing_points[0][1])], width*1.5, plate_thick, style=StrokeStyle.SQUARE))
            # wall_fixing_pos = (0, anchor_holder_fixing_points[0][1] + s/2)
            wall_fixing_pos = self.get_screwhole_positions()[0][:2]
            standoff = self.cut_wall_fixing_hole(standoff, wall_fixing_pos, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=True)

        if not self.standoff_pillars_separate:
            standoff = standoff.union(self.get_standoff_pillars(top=True).translate((0,0,self.back_plate_from_wall)))
        standoff = self.cut_anchor_bearing_in_standoff(standoff)



        standoff = standoff.translate((0,0,-self.back_plate_from_wall))

        if self.text_on_standoffs:
            standoff = standoff.cut(self.get_text(top_standoff=True))

        standoff = standoff.cut(self.get_fixing_screws_cutter())#.translate(np_to_set(np.multiply(-1, self.bearing_positions[-1][:2]))




        return standoff

    def get_rod_lengths(self):
        '''
        returns ([rod lengths, in same order as all_pillar_positions] , [base of rod z])
        '''

        total_plate_distance = self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance

        extra_length = self.fixing_screws.get_nut_height()*2 + 2

        bottom_pillar_length = total_plate_distance
        if self.leg_height > 0:
            bottom_pillar_length += self.plate_thick*2

        if self.has_vanity_plate:
            bottom_pillar_length += self.vanity_plate_base_z + self.vanity_plate_thick
            if self.leg_height > 0:
                #leg is included in the pillar that holds the vanity plate
                bottom_pillar_length -= self.plate_thick

        bottom_pillar_length += extra_length

        top_pillar_length = total_plate_distance + self.back_plate_from_wall + extra_length

        print("Need rod (M{}) of length {}mm for top pillars and {}mm for bottom pillars".format(self.fixing_screws.metric_thread, math.ceil(top_pillar_length), math.ceil(bottom_pillar_length)))

        lengths = [bottom_pillar_length for pillar in self.bottom_pillar_positions] + [top_pillar_length for pillar in self.top_pillar_positions]

        zs = [-self.plate_thick - extra_length/2 for pillar in self.bottom_pillar_positions] + [-self.back_plate_from_wall - extra_length/2 for pillar in self.top_pillar_positions]

        return (lengths, zs)


    def get_assembled(self, one_peice=True):
        plates, pillars, detail, standoff_pillars = super().get_assembled(one_peice=False)

        if not self.wall_mounted:
            plates = plates.add(self.get_legs(back=True).translate((0,0,-self.plate_thick)))

            plates = plates.add(self.get_legs(back=False).translate((0, 0, self.get_plate_thick(back=True) + self.get_plate_thick(back=False) + self.plate_distance)))

            for pillar_pos in self.leg_pillar_positions:
                pillars = pillars.add(self.get_legs_pillar().translate(pillar_pos))
        if one_peice:
            return plates.union(pillars).union(detail)
        return (plates, pillars, detail, standoff_pillars)

    def output_STLs(self, name="clock", path="../out"):
        super().output_STLs(name, path)

        if not self.wall_mounted:
            out = os.path.join(path, "{}_legs_back.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_legs(back=True), out)

            out = os.path.join(path, "{}_legs_front.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_legs(back=False), out)

            out = os.path.join(path, "{}_legs_pillar.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_legs_pillar(), out)

            out = os.path.join(path, "{}_anchor_holder_back.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_back_anchor_holder(), out)
        # else:
        #     out = os.path.join(path, "{}_wall_standoff_top.stl".format(name))
        #     print("Outputting ", out)
        #     exporters.export(self.get_wall_standoff(top=True, for_printing=True), out)
        #
        #     out = os.path.join(path, "{}_wall_standoff_bottom.stl".format(name))
        #     print("Outputting ", out)
        #     exporters.export(self.get_wall_standoff(top=False, for_printing=True), out)



        if self.has_vanity_plate:
            out = os.path.join(path, "{}_vanity_plate.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_vanity_plate(), out)

class RollingBallClock(SimpleClockPlates):
    '''
    Doing more than just the plates, this will create dials and hands and trains too
    '''


    def __init__(self, name="",layer_thick=0.4):
        '''
        plan:

        new type of motion works where the hands are fixed to the rod and we use a "clutch" to enable adjusting the hands
        then can use "real" arbors within the plates to hold the hour hand
        This will mean the motion works isn't visible on the front plate and the hands can be close to the front plate (so the dial can be printed as part of teh front plate)

        Assuming a user-provided going train we can then calculate the size required for the motion works so the seconds and hour dials are equally spaced

        Plan is to support two spring barrels, both at an angle underneath the minute wheel. I'll see if one spring is enough to power the clock, and if it isn't
        I can then easily double the power by adding in the second barrel

        I'm not worried about the exact timing of the ball on teh tray - since this clock has a second hand I can just adjust the ratio of the final wheel-pinion pair
        just like I would on a short pendulum clock.
        It would be ideal if the "escape wheel" rotated at 1rpm, then the plates could be more symetric. Maybe worth thinking about that a bit more.
        Or maybe have the esacpe wheel at 90deg below the seconds dial? or does it matter if the arbors aren't symetric so long as the plates are?


        TODO new fixing for hands with a nut embedded in teh back of the hands? one nut behind and a dome nut in front should be enough to fix them rigidly to the rod

        '''

        # super().__init__(self.gen_going_train(), motion_works=None, pendulum=None, style=ClockPlateStyle.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
        #                  pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS,
        #                  pendulum_at_front=False, back_plate_from_wall=0, fixing_screws=MachineScrew(4, countersunk=True),
        #                  centred_second_hand=False, pillars_separate=True, dial=None, bottom_pillars=2, top_pillars=2,
        #                  second_hand=second_hand, motion_works_angle_deg=math.pi, endshake=1.5, compact_zigzag=True, screws_from_back=None,
        #                  layer_thick=layer_thick)
        #
        # self.narrow_bottom_pillar=False
        # self.little_arm_to_motion_works=False
        # self.pillar_screwhole_r = self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)


    def gen_going_train(self):
        return None

    def gen_dials(self):
        #TODO work with generating the train to

        self.dial_minutes = Dial(150, DialStyle.ARABIC_NUMBERS, dial_width=20, font="Gill Sans Medium", font_scale=0.8, font_path="../fonts/GillSans/Gill Sans Medium.otf",
                                 inner_edge_style=DialStyle.LINES_RECT, minutes_only=True, top_fixing=False, bottom_fixing=False)
        # looks good for the hours
        self.dial_hours = Dial(100, DialStyle.ROMAN_NUMERALS, dial_width=15, font="Times New Roman", font_scale=0.6, inner_edge_style=DialStyle.LINES_RECT_LONG_INDICATORS, hours_only=True,
                               top_fixing=False, bottom_fixing=False)

        self.dial_seconds = Dial(100, dial_width=15, inner_edge_style=DialStyle.LINES_RECT_LONG_INDICATORS, style=DialStyle.ARABIC_NUMBERS, font="Gill Sans Medium", font_scale=0.9,
                                 font_path="../fonts/GillSans/Gill Sans Medium.otf", seconds_only=True, top_fixing=False, bottom_fixing=False)

    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        current plan: asymetric to be compact, with anchor arbor sticking out the top above the topmost pillar

        This is completely hard coded around a spring powered clock with 4 wheels and 2 powered wheels using the compact layout.
        if the spring clock is a success, it'll be worth making it more flexible
        '''

        bearingInfo = get_bearing_info(self.arbor_d)
        # TODO review this from old logic width of thin bit
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        self.pillar_r = self.plate_width/2

        self.bottom_pillar_positions = []
        self.top_pillar_positions = []
        self.bottom_pillar_r = self.pillar_r
        self.top_pillar_r = self.pillar_r

        bottom_distance = self.arbors_for_plate[0].get_max_radius() + self.gear_gap + self.bottom_pillar_r
        # TODO check this doesn't collide with next wheel
        bottom_angle = -math.pi / 4
        self.bottom_pillar_positions = [polar(math.pi - bottom_angle, bottom_distance), polar(bottom_angle, bottom_distance)]

        # right_pillar_line = Line(self.bearing_positions[1][:2], anotherPoint=self.bearing_positions[-2][:2])
        # #how far between the arbors 1 and -2
        # right_distance = np.linalg.norm(np.subtract(self.bearing_positions[1][:2], self.bearing_positions[-2][:2]))
        # #calculate how far along is "in the middle" of the empty space between them
        # right_bottom_distance = self.arbours_for_plate[1].get_max_radius()
        # along_distance = right_bottom_distance + (right_distance - self.arbours_for_plate[-2].get_max_radius() - right_bottom_distance)/2
        # right_bottom_equidistance_point = npToSet(np.add(self.bearing_positions[1][:2], np.multiply(right_pillar_line.dir, along_distance)))
        # #now go outwards from teh minute wheel along the line that goes through the minutewheel and this point
        # right_pillar_line2 = Line(self.bearing_positions[self.going_train.powered_wheels][:2], anotherPoint=right_bottom_equidistance_point)
        #
        # from_minute_wheel = self.arbours_for_plate[self.going_train.powered_wheels].get_max_radius() + self.gear_gap + self.top_pillar_r
        # right_pillar_pos = npToSet(np.add(right_pillar_line2.start,np.multiply(right_pillar_line2.dir, from_minute_wheel)))
        #
        # self.top_pillar_positions = [right_pillar_pos]
        right_pillar_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.bearing_positions[1][:2])
        # left_pillar_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.bearing_positions[self.going_train.powered_wheels+1][:2])
        self.top_pillar_positions = [
            np_to_set(
                np.add(self.bearing_positions[self.going_train.powered_wheels + 1][:2], np.multiply(polar(math.pi * 0.525), self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
            np_to_set(np.add(self.bearing_positions[1][:2], np.multiply(right_pillar_line.dir, self.arbors_for_plate[1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
        ]
        print("top pillar distance gap: ", np.linalg.norm(np.subtract(self.top_pillar_positions[1], self.bearing_positions[-1][:2])) - self.top_pillar_r - self.arbors_for_plate[-1].get_max_radius())

    def calc_fixing_info(self):
        # fixing positions to plates and pillars together
        self.plate_top_fixings = []
        # (self.top_pillar_positions[0] - self.top_pillar_r / 2, self.top_pillar_positions[1]), (self.top_pillar_positions[0] + self.top_pillar_r / 2, self.top_pillar_positions[1])]
        for top_pillar_pos in self.top_pillar_positions:
            self.plate_top_fixings.append((top_pillar_pos[0], top_pillar_pos[1]))

        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottom_pillar_positions:
            self.plate_bottom_fixings.append((bottom_pillar_pos[0], bottom_pillar_pos[1]))

        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings

    def get_plate(self, back=True, for_printing=True):

        plate_thick = self.get_plate_thick(back=back)

        plate = cq.Workplane("XY").rect(100,100).extrude(plate_thick)
        return plate

        main_arm_wide = self.plate_width
        medium_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2
        small_arm_wide = 8

        pillar_positions = self.top_pillar_positions + self.bottom_pillar_positions

        # for pillar in range(len(pillar_positions)):
        #     pillar_pos = pillar_positions[pillar]
        #     next_pillar_pos = pillar_positions[(pillar + 1)% len(pillar_positions)]
        #
        # link up the side pillars with each other
        for side in [0, 1]:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bottom_pillar_positions[side]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.bottom_pillar_positions[side], self.bearing_positions[0][:2]], wide=main_arm_wide, thick=plate_thick))

        # plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))
        if not back:
            # arch over the top
            # no point holding the bearing that isn't there for the anchor arbor!
            plate = plate.union(get_stroke_line([self.bearing_positions[-2][:2], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        if back:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        # barrel to minute wheel
        plate = plate.union(get_stroke_line([self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2]], wide=medium_arm_wide, thick=plate_thick))

        # across the front of the plate
        plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels + 1][:2], self.bearing_positions[1][:2]], wide=medium_arm_wide, thick=plate_thick))

        # idea - 3 thin arms all linking to the second hand arbor? medium from barrel to minute wheel, thick just for the edges
        links = [self.bearing_positions[self.going_train.powered_wheels][:2],
                 self.bearing_positions[self.going_train.powered_wheels + 3][:2],
                 self.top_pillar_positions[0]
                 ]
        for link_pos in links:
            plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels + 2][:2], link_pos], wide=small_arm_wide, thick=plate_thick))

        for i, pos in enumerate(self.bearing_positions):

            bearing_info = self.arbors_for_plate[i].bearing

            if not (i == len(self.bearing_positions) - 1 and back):
                # only if not the back plate and the hole for the anchor arbor
                plate = plate.union(cq.Workplane("XY").circle(bearing_info.outer_d / 2 + self.bearing_wall_thick).extrude(plate_thick).translate(pos[:2]))

        plate = plate.union(cq.Workplane("XY").circle(self.going_train.powered_wheel.key_bearing.outer_d / 2 + self.bearing_wall_thick * 1.5).extrude(plate_thick))

        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())
            if not self.text_on_standoffs:
                plate = plate.cut(self.get_text())
        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0, 0, -self.get_plate_thick(back=True) - self.plate_distance)))

        if not back:
            plate = self.front_additions_to_plate(plate)

        plate = self.punch_bearing_holes(plate, back)

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back == back:
            # spring powered, need the ratchet!
            screw = self.going_train.powered_wheel.ratchet.fixing_screws

            cutter = cq.Workplane("XY")

            for relative_pos in self.going_train.powered_wheel.ratchet.get_screw_positions() + self.going_train.powered_wheel.ratchet.get_little_plate_for_pawl_screw_positions():
                pos = np_to_set(np.add(self.bearing_positions[0][:2], relative_pos))
                # undecided if they need to be for tap die, they mgiht be enough without now there's a little plate for the pawl
                cutter = cutter.add(screw.get_cutter(with_bridging=True).translate(pos))  # for_tap_die=True,

            if back:
                cutter = cutter.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, plate_thick))

            plate = plate.cut(cutter)

        return plate

    def get_text(self, top_standoff=False):

        all_text = cq.Workplane("XY")

        # (x,y,width,height, horizontal)
        spaces = []

        texts = [" ".join(self.texts[1:]), self.texts[0]]

        long_line = Line(self.bottom_pillar_positions[0], anotherPoint=self.top_pillar_positions[0])
        long_space_length = np.linalg.norm(np.subtract(self.top_pillar_positions[0], self.bottom_pillar_positions[0]))
        long_line_length = long_space_length - self.top_pillar_r - self.bottom_pillar_r - 1
        text_height = self.plate_width * 0.9
        long_centre = np_to_set(np.add(long_line.start, np.multiply(long_line.dir, long_space_length / 2)))
        long_angle = long_line.get_angle()

        short_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.top_pillar_positions[1])
        short_space_length = np.linalg.norm(np.subtract(self.bearing_positions[1][:2], self.bottom_pillar_positions[1]))
        short_line_length = short_space_length - 10
        short_centre = np_to_set(np.add(short_line.start, np.multiply(short_line.dir, short_space_length / 2)))
        short_angle = short_line.get_angle() + math.pi

        # three along the wide bit at the bottom and one above
        spaces.append(TextSpace(long_centre[0], long_centre[1], text_height, long_line_length, angle_rad=long_angle))
        spaces.append(TextSpace(short_centre[0], short_centre[1], text_height, short_line_length, angle_rad=short_angle))
        # spaces.append(TextSpace(bottom_pos[0], (bottom_pos[1] + (chain_pos[1] - chain_space)) / 2, text_height, chain_pos[1] - chain_space - bottom_pos[1], horizontal=False))
        # spaces.append(TextSpace(bottom_pos[0] + self.bottom_pillar_r - self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))
        #
        # spaces.append(TextSpace(chain_pos[0], (first_arbour_pos[1] - arbour_space + chain_pos[1] + chain_space) / 2, self.plate_width * 0.9, first_arbour_pos[1] - arbour_space - (chain_pos[1] + chain_space), horizontal=False))

        for i, text in enumerate(texts):
            spaces[i].set_text(text)

        max_text_size = min([textSpace.get_text_max_size() for textSpace in spaces])

        for space in spaces:
            space.set_size(max_text_size)

        for space in spaces:
            all_text = all_text.add(space.get_text_shape())

        all_text = self.punch_bearing_holes(all_text, back=True, make_plate_bigger=False)

        return all_text

    def get_screwhole_positions(self):
        '''
        this doesn't hang on the wall, so no wall fixings
        '''
        return []

    def get_wall_standoff(self, top=True, for_printing=True):
        '''
        not really a wall standoff, but the bit that holds the pendulum at the top
        '''
        return None

    def get_pillar(self,top=True, flat=True):
        '''
        this is a pillar in teh sense of the simple clock plate - this holds the front and back plates together
        we'll have front pillars that hold the base of the clock (with the marble run) to the movement, need to think of a new name for those
        '''



        return cq.Workplane("XY").circle(self.pillar_r).circle(self.pillar_screwhole_r).extrude(self.plate_distance)

    def get_top_pillar(self):
        return self.get_pillar()

    def get_bottom_pillar(self):
        return self.get_pillar()

class StrikingClockPlates(SimpleClockPlates):
    '''
    Striking clock plates, undecided yet if they'll be shelf mounted or wall mounted. I'll see how large they end up being first
    '''

    def __init__(self, going_train, motion_works, plate_thick=8, back_plate_thick=None, pendulum_sticks_out=15, name="", centred_second_hand=False, dial=None,
                 moon_complication=None, second_hand=True, motion_works_angle_deg=-1, screws_from_back=None, layer_thick=LAYER_THICK_EXTRATHICK):
        super().__init__(going_train, motion_works, pendulum=None, gear_train_layout=GearTrainLayout.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
                         pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS,
                         pendulum_at_front=False, back_plate_from_wall=pendulum_sticks_out + 10 + plate_thick, fixing_screws=MachineScrew(4, countersunk=True),
                         centred_second_hand=centred_second_hand, pillars_separate=True, dial=dial, bottom_pillars=2, moon_complication=moon_complication,
                         second_hand=second_hand, motion_works_angle_deg=motion_works_angle_deg, endshake=1.5, compact_zigzag=True, screws_from_back=screws_from_back,
                         layer_thick=layer_thick)

class Assembly:
    '''
    Produce a fully (or near fully) assembled clock
    likely to be fragile as it will need to delve into the detail of basically everything

    currently assumes pendulum and chain wheels are at front - doesn't listen to their values
    '''
    def __init__(self, plates, hands=None, time_mins=10, time_hours=10, time_seconds=0, pulley=None, weights=None, pretty_bob=None, pendulum=None):
        self.plates = plates
        self.hands = hands
        self.dial= plates.dial
        self.going_train = plates.going_train
        #+1 for the anchor
        self.arbour_count = self.going_train.powered_wheels + self.going_train.wheels + 1
        self.pendulum = pendulum
        self.motion_works = self.plates.motion_works
        self.time_mins = time_mins
        self.time_hours = time_hours
        self.time_seconds = time_seconds
        self.pulley=pulley
        self.moon_complication = self.plates.moon_complication
        #weights is a list of weights, first in the list is the main weight and second is the counterweight (if needed)
        self.weights=weights
        if self.weights is None:
            self.weights = []

        #cosmetic parts taht override the defaults

        self.pretty_bob = pretty_bob


        # =============== shared geometry (between clock model and show_clock) ================
        self.front_of_clock_z = self.plates.get_plate_thick(True) + self.plates.get_plate_thick(False) + self.plates.plate_distance

        self.hands_pos = self.plates.bearing_positions[self.going_train.powered_wheels][:2]

        # where the nylock nut and spring washer would be (6mm = two half size m3 nuts and a spring washer + some slack)
        self.motion_works_z_offset = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base + self.plates.endshake / 2
        self.motion_works_z = self.front_of_clock_z + self.motion_works_z_offset

        self.motion_works_pos = self.plates.hands_position.copy()
        self.second_hand_pos = None
        # total, not relative, height because that's been taken into accounr with motionworksZOffset
        self.minute_hand_z = self.front_of_clock_z + self.motion_works_z_offset + self.motion_works.get_cannon_pinion_total_height() - self.hands.thick
        if self.plates.has_seconds_hand():
            self.second_hand_pos = self.plates.get_seconds_hand_position()
            self.second_hand_pos.append(self.front_of_clock_z + self.hands.second_fixing_thick)

        self.minuteAngle = - 360 * (self.time_mins / 60)
        self.hourAngle = - 360 * (self.time_hours + self.time_mins / 60) / 12
        self.secondAngle = -360 * (self.time_seconds / 60)

        if self.plates.dial is not None:
            if self.plates.has_seconds_hand():
                self.second_hand_pos[2] = self.front_of_clock_z + self.plates.dial.support_length + self.plates.dial.thick + self.plates.endshake / 2 + 0.5

            #position of the front centre of the dial
            self.dial_pos = (self.plates.hands_position[0], self.plates.hands_position[1], self.plates.dial_z + self.dial.thick + self.front_of_clock_z)
            #for eyes
            self.wire_to_arbor_fixer_pos = (self.plates.bearing_positions[-1][0], self.plates.bearing_positions[-1][1], self.front_of_clock_z + self.plates.endshake + 1)
        if self.plates.centred_second_hand:
            self.second_hand_pos = self.plates.hands_position.copy()
            self.second_hand_pos.append(self.minute_hand_z - self.motion_works.hour_hand_slot_height)# + self.hands.thick + self.hands.secondFixing_thick)
        if self.plates.pendulum_at_front:

            pendulumRodCentreZ = self.plates.get_plate_thick(back=True) + self.plates.get_plate_thick(back=False) + self.plates.plate_distance + self.plates.pendulum_sticks_out
        else:
            pendulumRodCentreZ = -self.plates.pendulum_sticks_out

        pendulumBobCentreY = self.plates.bearing_positions[-1][1] - self.going_train.pendulum_length * 1000

        self.pendulum_bob_centre_pos = (self.plates.bearing_positions[-1][0], pendulumBobCentreY, pendulumRodCentreZ)

        self.ring_pos = [0,0,self.pendulum_bob_centre_pos[2]]
        self.has_ring = False

        self.ratchet_on_plates = None

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL:
            #rotated so the screwhole lines up - can't decide where that should be done
            self.ratchet_on_plates = self.going_train.powered_wheel.get_ratchet_gear_for_arbor().rotate((0, 0, 0), (0, 0, 1), 180)\
                .add(self.going_train.powered_wheel.ratchet.get_pawl()).add(self.going_train.powered_wheel.ratchet.get_click())
            if self.plates.little_plate_for_pawl:
                self.ratchet_on_plates = self.ratchet_on_plates.add(self.going_train.powered_wheel.ratchet.get_little_plate_for_pawl()).translate(self.plates.bearing_positions[0][:2])
            if self.going_train.powered_wheel.ratchet_at_back:
                self.ratchet_on_plates = self.ratchet_on_plates.rotate((0,0,0),(0,1,0),180).translate((0,0,-self.plates.endshake/2))
            else:
                self.ratchet_on_plates = self.ratchet_on_plates.translate((0, 0, self.front_of_clock_z + self.plates.endshake/2))

        if self.plates.pendulum_at_front:
            # if the hands are directly below the pendulum pivot point (not necessarily true if this isn't a vertical clock)
            if self.plates.gear_train_layout != GearTrainLayout.ROUND:
                # centre around the hands by default
                self.ring_pos[1] = self.plates.bearing_positions[self.going_train.powered_wheels][1]
                if self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key:
                    # centre between the hands and the winding key
                    self.ring_pos[1] = (self.plates.bearing_positions[self.going_train.powered_wheels][1] + self.plates.bearing_positions[0][1]) / 2

                # ring is over the minute wheel/hands
                self.ring_pos[2] = pendulumRodCentreZ - self.pendulum.hand_avoider_thick / 2
                self.has_ring = True
        else:
            # pendulum is at the back, hand avoider is around the bottom pillar (unless this proves too unstable) if the pendulum is long enough to need it
            if len(self.plates.bottom_pillar_positions) == 1 and np.linalg.norm(np.subtract(self.plates.bearing_positions[-1][:2], self.plates.bottom_pillar_positions[0][:2])) < self.going_train.pendulum_length*1000:
                self.ring_pos = (self.plates.bottom_pillar_positions[0][0], self.plates.bottom_pillar_positions[0][1], -self.plates.pendulum_sticks_out - self.pendulum.hand_avoider_thick / 2)
                self.has_ring = True
        self.weight_positions = []
        if len(self.weights) > 0:
            for i, weight in enumerate(self.weights):
                #line them up so I can see if they'll bump into each other
                weightTopY = self.pendulum_bob_centre_pos[1] + weight.height

                holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()

                #side the main weight is on
                side = 1 if self.going_train.is_weight_on_the_right() else -1

                if i == 1:
                    #counterweight
                    side*=-1

                #in X,Y,Z
                weightPos = None

                for holeInfo in holePositions:
                    if (holeInfo[0][0] > 0) == (side > 0):
                        #hole for the weight
                        weightPos = (holeInfo[0][0], weightTopY - weight.height, self.plates.bearing_positions[0][2] + self.plates.get_plate_thick(back=True) + self.going_train.powered_wheel.get_height() + holeInfo[0][1])
                        self.weight_positions.append(weightPos)

        self.pulley_model = None
        if self.pulley is not None:
            #put the pulley model in position
            chainWheelTopZ = self.plates.bearing_positions[0][2] + self.going_train.get_arbor(-self.going_train.powered_wheels).get_total_thickness() + self.plates.get_plate_thick(back=True) + self.plates.endshake / 2

            chainZ = chainWheelTopZ + self.going_train.powered_wheel.get_chain_positions_from_top()[0][0][1]

            # TODO for two bottom pillars
            pulleyY = self.plates.bottom_pillar_positions[0][1] - self.plates.bottom_pillar_r - self.pulley.diameter

            if self.plates.huygens_maintaining_power:
                pulley = self.pulley.get_assembled().translate((0, 0, -self.pulley.getTotalThick() / 2)).rotate((0, 0, 0), (0, 1, 0), 90)
                self.pulley_model = pulley.translate((self.going_train.powered_wheel.diameter / 2, pulleyY, chainZ + self.going_train.powered_wheel.diameter / 2))
                if self.going_train.powered_wheel.type == PowerType.ROPE:
                    # second pulley for the counterweight
                    self.pulley_model = self.pulley_model.add(pulley.translate((-self.going_train.powered_wheel.diameter / 2, pulleyY, chainZ + self.going_train.powered_wheel.diameter / 2)))
            else:

                self.pulley_model = self.pulley.get_assembled().rotate((0, 0, 0), (0, 0, 1), 90).translate((0, pulleyY, chainZ - self.pulley.getTotalThick() / 2))


        key = self.plates.get_winding_key()
        self.key_model = None
        if key is not None:
            key_model = key.get_assembled()
            #put the winding key on the end of the key shape, should be most simple way of getting it in the right place!
            self.key_model = key_model.translate(
                (self.plates.bearing_positions[0][0],
                 self.plates.bearing_positions[0][1],
                 self.front_of_clock_z + self.plates.key_length + self.plates.endshake / 2 - key.key_hole_deep)
            )

        self.vanity_plate = None
        if self.plates.has_vanity_plate:
            self.vanity_plate = self.plates.get_vanity_plate(for_printing=False).translate((self.hands_pos[0], self.hands_pos[1], self.front_of_clock_z))


    def printInfo(self):

        for holeInfo in self.going_train.powered_wheel.get_chain_positions_from_top():
            #TODO improve this a bit for cordwheels which have a slot rather than just a hole
            z = self.plates.bearing_positions[0][2] + self.plates.get_plate_thick(back=True) + self.going_train.powered_wheel.get_height() + self.plates.endshake / 2 + holeInfo[0][1]
            print("{} hole from wall = {}mm".format(self.going_train.powered_wheel.type.value, z))

    def get_arbour_rod_lengths(self):
        '''
        Calculate the lengths to cut the steel rods - stop me just guessing wrong all the time!
        '''

        # for i,arbor in enumerate(self.plates.arbors_for_plate):
        #     if arbor.type in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL] and arbor.arbor.pinion.lantern:
        #         #calculate length of lantern pinion
        #         diameter = arbor.arbor.pinion.trundle_r*2
        #         min_length = arbor.arbor.pinion_thick
        #         #assumed knowledge, the default value of offset in get_lantern_cap is 1. TODO improve this
        #         max_lenth = arbor.arbor.pinion_thick + (arbor.arbor.end_cap_thick - 1) +  (arbor.arbor.wheel_thick - 1)
        #
        #         print("for arbor {} need lantern trundles of diameter {:.2f}mm and length {:.1f}-{:.1f}mm".format(i, diameter, min_length, max_lenth))


        total_plate_thick = self.plates.plate_distance + self.plates.get_plate_thick(True) + self.plates.get_plate_thick(False)
        plate_distance =self.plates.plate_distance
        front_plate_thick = self.plates.get_plate_thick(back=False)
        back_plate_thick = self.plates.get_plate_thick(back=True)



        #how much extra to extend out the bearing
        #used to be 3mm, but when using thinner plates this isn't ideal.
        spare_rod_length_beyond_bearing=self.plates.endshake*2
        #extra length out the front of hands, or front-mounted escapements
        spare_rod_length_in_front=2
        rod_lengths = []
        rod_zs = []
        #for measuring where to put the arbour on the rod, how much empty rod should behind the back of the arbour?
        beyond_back_of_arbours = []



        for i in range(self.arbour_count):

            rod_length = -1

            arbor_for_plate = self.plates.arbors_for_plate[i]
            arbor = arbor_for_plate.arbor
            bearing = arbor_for_plate.bearing
            bearing_thick = bearing.height

            rod_in_front_of_hands = WASHER_THICK_M3 + get_nut_height(arbor.arbor_d) + M3_DOMED_NUT_THREAD_DEPTH - 1

            length_up_to_inside_front_plate = spare_rod_length_beyond_bearing + bearing_thick + plate_distance

            beyond_back_of_arbour = spare_rod_length_beyond_bearing + bearing_thick# + self.plates.endshake
            #true for nearly all of it
            rod_z = back_plate_thick - (bearing_thick + spare_rod_length_beyond_bearing)

            #"normal" arbour that does not extend out the front or back
            simple_arbour_length = length_up_to_inside_front_plate + bearing_thick + spare_rod_length_beyond_bearing
            # hand_arbor_length = length_up_to_inside_front_plate + front_plate_thick + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT + self.plates.motionWorks.get_cannon_pinion_effective_height() + getNutHeight(arbour.arbourD) * 2 + spare_rod_length_in_front
            hand_arbor_length = length_up_to_inside_front_plate + front_plate_thick + (self.minute_hand_z + self.hands.thick - total_plate_thick) + rod_in_front_of_hands

            #trying to arrange all the additions from back to front to make it easy to check
            if arbor.type == ArborType.POWERED_WHEEL:
                powered_wheel = arbor.powered_wheel
                if powered_wheel.type == PowerType.CORD:
                    if powered_wheel.use_key:
                        square_bit_out_front = powered_wheel.key_square_bit_height - (front_plate_thick - powered_wheel.key_bearing.height) - self.plates.endshake / 2
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + square_bit_out_front
                elif powered_wheel.type == PowerType.SPRING_BARREL:
                    rod_length=-1
                else:
                    #assume all other types of powered wheel lack a key and thus are just inside the plates
                    rod_length = simple_arbour_length


            elif self.plates.second_hand and ((arbor.type == ArborType.ESCAPE_WHEEL and self.plates.going_train.has_seconds_hand_on_escape_wheel()) or (
                    i == self.going_train.wheels + self.going_train.powered_wheels - 2 and self.plates.going_train.has_second_hand_on_last_wheel())):
                #this has a second hand on it
                if self.plates.escapement_on_front:
                    raise ValueError("TODO calculate rod lengths for escapement on front")
                elif self.plates.centred_second_hand:
                    #safe to assume mutually exclusive with escapement on front?
                    rod_length = hand_arbor_length + self.hands.second_fixing_thick + CENTRED_SECOND_HAND_BOTTOM_FIXING_HEIGHT
                else:
                    if self.dial is not None and self.dial.has_seconds_sub_dial():
                        #if the rod doesn't go all the way through the second hand
                        hand_thick_accounting = self.hands.second_thick - self.hands.second_rod_end_thick
                        if self.hands.seconds_hand_through_hole:
                            hand_thick_accounting = self.hands.second_thick
                        #rod_length = length_up_to_inside_front_plate + front_plate_thick + self.dial.support_length + self.dial.thick + self.hands.secondFixing_thick + hand_thick_accounting
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + (self.second_hand_pos[2] - total_plate_thick )+ hand_thick_accounting
                    else:
                        #little seconds hand just in front of the plate
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + self.hands.second_fixing_thick + self.hands.second_thick
            elif arbor.type == ArborType.WHEEL_AND_PINION:
                if i == self.going_train.powered_wheels:
                    #minute wheel
                    if self.plates.centred_second_hand:
                        #only goes up to the canon pinion with hand turner
                        minimum_rod_length = (length_up_to_inside_front_plate + front_plate_thick + self.plates.endshake / 2 + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT +
                                              self.plates.motion_works.get_cannon_pinion_pinion_thick() + rod_in_front_of_hands)
                                              # + WASHER_THICK_M3 + getNutHeight(arbour.arbor_d, halfHeight=True) * 2)
                        # if self.plates.dial is not None:
                        #     #small as possible as it might need to fit behind the dial (...not sure what I was talking about here??)
                        #     rod_length = minimum_rod_length + 1.5
                        # else:
                        #     rod_length = minimum_rod_length + spare_rod_length_in_front
                        rod_length = minimum_rod_length
                    else:
                        rod_length = hand_arbor_length
                else:
                    # "normal" arbour
                    rod_length = simple_arbour_length#length_up_to_inside_front_plate + bearing_thick + spare_rod_length_beyond_bearing

            elif arbor.type == ArborType.ESCAPE_WHEEL:
                if self.plates.escapement_on_front:
                    rod_length = length_up_to_inside_front_plate + front_plate_thick + arbor_for_plate.front_anchor_from_plate - arbor.escapement.get_wheel_base_to_anchor_base_z() + arbor.wheel_thick + get_nut_height(round(arbor_for_plate.bearing.inner_d)) + 1
                else:
                    #"normal" arbour
                    rod_length = simple_arbour_length
            elif arbor.type == ArborType.ANCHOR:
                if self.plates.escapement_on_front:
                    holder_thick = self.plates.get_lone_anchor_bearing_holder_thick(self.plates.arbors_for_plate[-1].bearing)
                    out_front = self.plates.get_front_anchor_bearing_holder_total_length() - holder_thick
                    out_back = self.plates.back_plate_from_wall - self.plates.get_plate_thick(standoff=True)
                    extra = spare_rod_length_beyond_bearing
                    if self.plates.dial is not None:
                        #make smaller since there's not much space on the front
                        extra = self.plates.endshake
                    rod_length = out_back + total_plate_thick + out_front + self.plates.arbors_for_plate[-1].bearing.height*2 + extra*2
                    rod_z = -out_back - self.plates.arbors_for_plate[-1].bearing.height - extra
                elif self.plates.back_plate_from_wall > 0 and not self.plates.pendulum_at_front:
                    rod_length_to_back_of_front_plate = spare_rod_length_beyond_bearing + bearing_thick + (self.plates.back_plate_from_wall - self.plates.get_plate_thick(standoff=True)) + self.plates.get_plate_thick(back=True) + plate_distance

                    if self.dial is not None and self.dial.has_eyes():
                        rod_length = rod_length_to_back_of_front_plate + front_plate_thick + self.plates.endshake + 1 + self.dial.get_wire_to_arbor_fixer_thick() + 5
                    else:
                        rod_length = rod_length_to_back_of_front_plate + bearing_thick + spare_rod_length_beyond_bearing
                    rod_z = -self.plates.back_plate_from_wall + (self.plates.get_plate_thick(standoff=True) - bearing_thick - spare_rod_length_beyond_bearing)
                else:
                    raise ValueError("TODO calculate rod lengths for pendulum on front")
            rod_lengths.append(rod_length)
            rod_zs.append(rod_z)
            beyond_back_of_arbours.append(beyond_back_of_arbour)
            if rod_length > 0:
                print("Arbor {} rod (M{}) length: {}mm with {:.1f}mm beyond the arbour".format(i, self.plates.arbors_for_plate[i].bearing.inner_d, round(rod_length), beyond_back_of_arbour))
            if arbor.pinion is not None and arbor.pinion.lantern:
                diameter = arbor.pinion.trundle_r * 2
                min_length = arbor.pinion_thick
                # assumed knowledge, the default value of offset in get_lantern_cap is 1. TODO improve this
                max_lenth = arbor.pinion_thick + (arbor.end_cap_thick - 1) + (arbor.wheel_thick - 1)
                print("Arbor {} has a lantern pinion and needs steel rod of diameter {:.2f}mm and length {:.1f}-{:.1f}mm".format(i,  diameter, min_length, max_lenth))


        return rod_lengths, rod_zs

    def get_pendulum_rod_lengths(self):
        '''
        Calculate lengths of threaded rod needed to make the pendulum
        '''


    def get_clock(self, with_rods=False, with_key=False, with_pendulum=False):
        '''
        Probably fairly intimately tied in with the specific clock plates, which is fine while there's only one used in anger
        '''

        clock = self.plates.get_assembled()

        for a,arbour in enumerate(self.plates.arbors_for_plate):
            clock = clock.add(arbour.get_assembled())


        time_min = self.time_mins
        time_hour = self.time_hours




        motionWorksModel = self.motion_works.get_assembled(motionWorksRelativePos=self.plates.motion_works_relative_pos, minuteAngle=self.minuteAngle)

        clock = clock.add(motionWorksModel.translate((self.plates.hands_position[0], self.plates.hands_position[1], self.motion_works_z)))

        if self.moon_complication is not None:
            clock = clock.add(self.moon_complication.get_assembled().translate((self.motion_works_pos[0], self.motion_works_pos[1], self.front_of_clock_z)))
            moon = self.moon_complication.get_moon_half()
            moon = moon.add(moon.rotate((0,0,0),(0,1,0),180))
            clock = clock.add(moon.translate((0, self.plates.moon_holder.get_moon_base_y() + self.moon_complication.moon_radius, self.moon_complication.get_relative_moon_z() + self.front_of_clock_z)))

        if self.plates.centred_second_hand:
            #the bit with a knob to set the time
            clock = clock.add(self.motion_works.get_cannon_pinion_pinion(standalone=True).translate((self.plates.bearing_positions[self.going_train.powered_wheels][0], self.plates.bearing_positions[self.going_train.powered_wheels][1], self.motion_works_z)))


        if self.dial is not None:
            dial = self.dial.get_assembled()#get_dial().rotate((0,0,0),(0,1,0),180)
            clock = clock.add(dial.translate(self.dial_pos))
            if self.dial.has_eyes():
                clock = clock.add(self.dial.get_wire_to_arbor_fixer(for_printing=False).translate((self.plates.bearing_positions[-1][0], self.plates.bearing_positions[-1][1], self.front_of_clock_z + self.plates.endshake + 1)))


        #hands on the motion work, showing the time
        hands = self.hands.get_assembled(time_minute = time_min, time_hour=time_hour, include_seconds=False, gap_size =self.motion_works.hour_hand_slot_height - self.hands.thick)


        # clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], minuteHandZ)))

        clock = clock.add(hands.translate((self.plates.hands_position[0], self.plates.hands_position[1],
                                           self.minute_hand_z - self.motion_works.hour_hand_slot_height)))

        if self.plates.has_seconds_hand():
            #second hand!! yay
            secondHand = self.hands.get_hand(hand_type=HandType.SECOND).mirror().translate((0, 0, self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), self.secondAngle)

            clock = clock.add(secondHand.translate(self.second_hand_pos))

        if with_key:
            if self.key_model is not None:
                clock = clock.add(self.key_model)



        if with_pendulum:
            bob = self.pendulum.get_bob(hollow=False)

            if self.pretty_bob is not None:
                bob = self.pretty_bob.get_model()

            clock = clock.add(bob.rotate((0, 0, self.pendulum.bob_thick / 2), (0, 1, self.pendulum.bob_thick / 2), 180).translate(self.pendulum_bob_centre_pos))

            clock = clock.add(self.pendulum.get_bob_nut().translate((0, 0, -self.pendulum.bob_nut_thick / 2)).rotate((0, 0, 0), (1, 0, 0), 90).translate(self.pendulum_bob_centre_pos))


        if len(self.weights) > 0:
            for i, weight in enumerate(self.weights):
                #line them up so I can see if they'll bump into each other
                weightTopY = self.pendulum_bob_centre_pos[1]

                holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()

                #side the main weight is on
                side = 1 if self.going_train.is_weight_on_the_right() else -1

                if i == 1:
                    #counterweight
                    side*=-1

                #in X,Y,Z
                weightPos = None

                for holeInfo in holePositions:
                    if (holeInfo[0][0] > 0) == (side > 0):
                        #hole for the weight
                        weightPos = (holeInfo[0][0], weightTopY - weight.height, self.plates.bearing_positions[0][2] + self.plates.get_plate_thick(back=True) + self.going_train.powered_wheel.get_height() + holeInfo[0][1])

                if weightPos is not None:
                    weightShape = weight.getWeight().rotate((0,0,0), (1,0,0),-90)

                    clock = clock.add(weightShape.translate(weightPos))


        #vector from minute wheel to the pendulum
        minuteToPendulum = (self.plates.bearing_positions[-1][0] - self.plates.bearing_positions[self.going_train.powered_wheels][0], self.plates.bearing_positions[-1][1] - self.plates.bearing_positions[self.going_train.powered_wheels][1])

        if abs(minuteToPendulum[0]) < 50:
            ring = self.pendulum.get_hand_avoider()
            if self.plates.pendulum_at_front:
                #if the hands are directly below the pendulum pivot point (not necessarily true if this isn't a vertical clock)

                #centre around the hands by default
                ringY = self.plates.bearing_positions[self.going_train.powered_wheels][1]
                if self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key:
                    #centre between the hands and the winding key
                    ringY = (self.plates.bearing_positions[self.going_train.powered_wheels][1] + self.plates.bearing_positions[0][1]) / 2


                handAvoiderExtraZ = (self.pendulum.pendulumTopThick - self.pendulum.hand_avoider_thick) / 2
                #ring is over the minute wheel/hands
                clock = clock.add(ring.translate((self.plates.bearing_positions[self.going_train.powered_wheels][0], ringY, self.plates.get_plate_thick(back=True) + self.plates.get_plate_thick(back=False) + self.plates.plate_distance + self.plates.pendulum_sticks_out + handAvoiderExtraZ)))
            else:
                #pendulum is at the back, hand avoider is around the bottom pillar (unless this proves too unstable)
                if len(self.plates.bottom_pillar_positions) == 1:
                    ringCentre = self.plates.bottom_pillar_positions[0]
                    clock = clock.add(ring.translate(ringCentre).translate((0, 0, -self.plates.pendulum_sticks_out - self.pendulum.hand_avoider_thick / 2)))


        if self.pulley is not None:
            clock = clock.add(self.pulley_model)


        if self.plates.huygens_maintaining_power:
            #assumes one pillar
            clock = clock.add(self.plates.huygens_wheel.get_assembled().translate(self.plates.bottom_pillar_positions[0]).translate((0, self.plates.huygens_wheel_y_offset, self.plates.get_plate_thick(True) + self.plates.get_plate_thick(False) + self.plates.plate_distance + WASHER_THICK_M3)))

        #TODO pendulum bob and nut?

        #TODO weight?

        if with_rods:
            rod_lengths, rod_zs = self.get_arbour_rod_lengths()
            for i in range(len(rod_lengths)):
                if rod_lengths[i] <= 0:
                    continue
                rod = cq.Workplane("XY").circle(self.going_train.get_arbour_with_conventional_naming(i).arbor_d / 2 - 0.2).extrude(rod_lengths[i]).translate((self.plates.bearing_positions[i][0], self.plates.bearing_positions[i][1], rod_zs[i]))
                clock = clock.add(rod)

        return clock


    def show_clock(self, show_object, gear_colours=None, dial_colours=None, plate_colours=None, hand_colours=None,
                   bob_colours=None, motion_works_colours=None, with_pendulum=True, ring_colour=None, huygens_colour=None, weight_colour=Colour.PURPLE,
                   text_colour=Colour.WHITE, with_rods=False, with_key=False, key_colour=Colour.PURPLE, pulley_colour=Colour.PURPLE, ratchet_colour=None,
                   moon_complication_colour=Colour.BRASS, vanity_plate_colour=Colour.WHITE):
        '''
        use show_object with colours to display a clock, will only work in cq-editor, useful for playing about with colour schemes!
        hoping to re-use some of this to produce coloured SVGs
        '''
        if gear_colours is None:
            gear_colours = Colour.RAINBOW
        if dial_colours is None:
            dial_colours = ["white", "black"]
        if hand_colours is None:
            #main hand, outline, second hand if different
            hand_colours = ["white", "black"]
        if motion_works_colours is None:
            #cannonpinion, hour holder, arbor, time-setting pinion
            motion_works_colours = [gear_colours[self.going_train.wheels]]
        if ring_colour is None:
            ring_colour = gear_colours[(self.going_train.wheels + self.going_train.powered_wheels + 1) % len(gear_colours)]
        if huygens_colour is None:
            huygens_colour = gear_colours[(self.going_train.wheels + self.going_train.powered_wheels + 2) % len(gear_colours)]
        if bob_colours is None:
            offset = 2
            if self.going_train.huygens_maintaining_power:
                offset = 3
            default_bob_colour = gear_colours[(self.going_train.wheels + self.going_train.powered_wheels + offset) % len(gear_colours)]
            #default to bob and nut are same colour and any text is black
            bob_colours = [default_bob_colour,default_bob_colour, Colour.BLACK]

        if plate_colours is None:
            plate_colours = [Colour.LIGHTGREY]

        if not isinstance(plate_colours, list):
            #backwards compatibility
            plate_colours = [plate_colours]

        if ratchet_colour is None:
            ratchet_colour = plate_colours[0]

        plates, pillars, plate_detail, standoff_pillars = self.plates.get_assembled(one_peice=False)

        show_object(plates, options={"color":plate_colours[0]}, name= "Plates")
        show_object(pillars, options={"color": plate_colours[1 % len(plate_colours)]}, name="Pillars")
        show_object(standoff_pillars, options={"color": plate_colours[1 % len(plate_colours)]}, name="Standoff Pillars")
        if plate_detail is not None:
            show_object(plate_detail, options={"color": plate_colours[2 % len(plate_colours)]}, name="Plate Detail")

        if not self.plates.text_on_standoffs:
            show_object(self.plates.get_text(), options={"color":text_colour}, name="Text")
        else:
            show_object(self.plates.get_text(top_standoff=True), options={"color": text_colour}, name="Top Standoff Text")
            show_object(self.plates.get_text(top_standoff=False), options={"color": text_colour}, name="Bottom Standoff Text")


        for a, arbor in enumerate(self.plates.arbors_for_plate):
            show_object(arbor.get_assembled(), options={"color": gear_colours[(len(self.plates.arbors_for_plate) - 1 - a) % len(gear_colours)]}, name="Arbour {}".format(a))

        # # motionWorksModel = self.motionWorks.get_assembled(motionWorksRelativePos=self.plates.motionWorksRelativePos, minuteAngle=self.minuteAngle)
        # #
        # # show_object(motionWorksModel.translate((self.plates.hands_position[0], self.plates.hands_position[1], self.motionWorksZ)), options={"color":motion_works_colour})
        motion_works_parts = self.motion_works.get_parts_in_situ(motionWorksRelativePos=self.plates.motion_works_relative_pos, minuteAngle=self.minuteAngle)
        for i,part in enumerate(motion_works_parts):
            colour = motion_works_colours[i % len(motion_works_colours)]
            show_object(motion_works_parts[part].translate((self.plates.hands_position[0], self.plates.hands_position[1], self.motion_works_z)), options={"color":colour}, name="Motion Works {}".format(i))

        if self.motion_works.cannon_pinion_friction_ring:
            show_object(self.plates.get_cannon_pinion_friction_clip().translate(self.plates.cannon_pinion_friction_clip_pos).translate((0,0,self.front_of_clock_z)), options={"color":plate_colours}, name="Friction Clip")

        if self.moon_complication is not None:
            #TODO colours of moon complication arbors
            show_object(self.moon_complication.get_assembled().translate((self.motion_works_pos[0], self.motion_works_pos[1], self.front_of_clock_z)), name="Moon Complication", options={"color":moon_complication_colour})
            moon = self.moon_complication.get_moon_half()
            # moon = moon.add(moon.rotate((0,0,0),(0,1,0),180))
            show_object(moon.translate((0, self.plates.moon_holder.get_moon_base_y() + self.moon_complication.moon_radius, self.moon_complication.get_relative_moon_z() + self.front_of_clock_z)),
                        options={"color":"gray"}, name="Light Side of the Moon")
            show_object(moon.rotate((0,0,0),(0,1,0),180).translate((0, self.plates.moon_holder.get_moon_base_y() + self.moon_complication.moon_radius, self.moon_complication.get_relative_moon_z() + self.front_of_clock_z)),
                        options={"color":"black"}, name="Dark Side of the Moon")

            holder_parts = self.plates.moon_holder.get_moon_holder_parts(for_printing=False)
            for i,holder in enumerate(holder_parts):
                show_object(holder.translate((0, 0, self.front_of_clock_z)), name="moon_holder_part{}".format(i), options={"color":plate_colours[0]})

        if self.dial is not None:
            dial = self.dial.get_dial().rotate((0,0,0),(0,1,0),180).translate(self.dial_pos)
            detail = self.dial.get_all_detail().rotate((0,0,0),(0,1,0),180).translate(self.dial_pos)

            show_object(dial, options={"color": dial_colours[0]}, name="Dial")
            show_object(detail, options={"color": dial_colours[1]}, name="Dial Detail")

            if self.dial.style == DialStyle.TONY_THE_CLOCK:
                extras = self.dial.get_extras()
                #TODO - excessive since I'm probably never going to print tony again?

            if self.dial.has_eyes():
                show_object(self.dial.get_wire_to_arbor_fixer(for_printing=False).translate(self.wire_to_arbor_fixer_pos), options={"color": gear_colours[0]}, name="Eye Wire Fixer")
                eye, pupil = self.dial.get_eye()

                for i,eye_pos in enumerate(self.dial.get_eye_positions()):
                    show_object(eye.translate(eye_pos).translate(self.dial_pos).translate((0,0,-self.dial.thick - self.dial.eye_pivot_z)), options={"color": "white"}, name="Eye {} Whites".format(i))
                    show_object(pupil.translate(eye_pos).translate(self.dial_pos).translate((0,0,-self.dial.thick - self.dial.eye_pivot_z)), options={"color": "black"}, name="Eye Pupil".format(i))

        if self.vanity_plate is not None:
            show_object(self.vanity_plate, options={"color": vanity_plate_colour}, name="Vanity Plate")

        #hands on the motion work, showing the time
        #mirror them so the outline is visible (consistent with second hand)
        hands_position = (self.plates.hands_position[0], self.plates.hands_position[1], self.minute_hand_z - self.motion_works.hour_hand_slot_height)
        self.hands.show_hands(show_object, hand_colours=hand_colours, position=hands_position, second_hand_pos=self.second_hand_pos, hour_hand_slot_height=self.motion_works.hour_hand_slot_height,
                              time_hours=self.time_hours, time_minutes=self.time_mins, time_seconds=self.time_seconds, show_second_hand=self.plates.has_seconds_hand())
        # hands = self.hands.get_in_situ(time_minute=self.timeMins, time_hour=self.timeHours, time_seconds=self.timeSeconds, gap_size=self.motion_works.hourHandSlotHeight - self.hands.thick)
        #
        # for type in HandType:
        #     for colour in hands[type]:
        #         show_colour = colour
        #         description="{} Hand{}".format(type.value.capitalize(), " "+colour.capitalize() if colour is not None else "")
        #         if show_colour is None:
        #             show_colour = hand_colours[0]
        #             if type == HandType.SECOND:
        #                 show_colour = hand_colours[2 % len(hand_colours)]
        #         if show_colour == "outline":
        #             show_colour = hand_colours[1 % len(hand_colours)]
        #
        #         show_colour = Colour.colour_tidier(show_colour)
        #
        #         if type != HandType.SECOND:
        #             show_object(hands[type][colour].translate((self.plates.hands_position[0], self.plates.hands_position[1],
        #                                           self.minuteHandZ - self.motion_works.hourHandSlotHeight)), options={"color": show_colour}, name=description)
        #         elif self.plates.has_seconds_hand():
        #             #second hand!! yay
        #             secondHand = hands[type][colour].translate(self.second_hand_pos)
        #             show_object(secondHand, options={"color": show_colour}, name=description)

        if self.has_ring:

            show_object(self.pendulum.get_hand_avoider().translate(self.ring_pos), options={"color": ring_colour}, name="Pendulum Ring")

        if self.plates.huygens_maintaining_power:
            #assumes one pillar
            show_object(self.plates.huygens_wheel.get_assembled().translate(self.plates.bottom_pillar_positions[0]).
                        translate((0, self.plates.huygens_wheel_y_offset, self.front_of_clock_z + WASHER_THICK_M3)), options={"color": huygens_colour}, name="Huygens Wheel")

        if self.ratchet_on_plates is not None:
            show_object(self.ratchet_on_plates, options={"color": ratchet_colour}, name="ratchet")

        if with_pendulum:
            # bob_colour = gear_colours[len(self.plates.bearingPositions) % len(gear_colours)]
            bob_colour = bob_colours[0]
            nut_colour = bob_colours[ 1 % len(bob_colours)]
            text_colour = bob_colours[ 2 % len(bob_colours)]
            bob = self.pendulum.get_bob(hollow=False)

            if self.pretty_bob is not None:
                bob = self.pretty_bob.get_model()

            bob_text = self.pendulum.get_bob_text()
            if bob_text is not None:
                show_object(bob_text.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, self.pendulum.bob_thick / 2)).translate(self.pendulum_bob_centre_pos), options={"color": text_colour}, name="Pendulum Bob Text")

            show_object(bob.rotate((0,0,0),(0,1,0),180).translate((0, 0, self.pendulum.bob_thick / 2)).translate(self.pendulum_bob_centre_pos), options={"color": bob_colour}, name="Pendulum Bob")

            show_object(self.pendulum.get_bob_nut().translate((0, 0, -self.pendulum.bob_nut_thick / 2)).rotate((0, 0, 0), (1, 0, 0), 90).translate(self.pendulum_bob_centre_pos), options={"color": nut_colour}, name="Pendulum Bob Nut")


        if len(self.weights) > 0:
            for i, weight_pos in enumerate(self.weight_positions):

                weightShape = self.weights[i].getWeight().rotate((0,0,0), (1,0,0),-90)

                show_object(weightShape.translate(weight_pos), options={"color": weight_colour}, name="Weight_{}".format(i))

        if with_rods:
            #show with diameter slightly smaller so it's clearer on the render what's rod and what's hole
            rod_colour = Colour.SILVER
            rod_lengths, rod_zs = self.get_arbour_rod_lengths()
            for i in range(len(rod_lengths)):
                if rod_lengths[i] <= 0:
                    continue
                rod = cq.Workplane("XY").circle(self.going_train.get_arbour_with_conventional_naming(i).arbor_d / 2 - 0.2).extrude(rod_lengths[i]).translate((self.plates.bearing_positions[i][0], self.plates.bearing_positions[i][1], rod_zs[i]))
                show_object(rod, options={"color": rod_colour}, name="Arbor Rod {}".format(i))
            pillar_rod_lengths, pillar_rod_zs = self.plates.get_rod_lengths()
            for p, length in enumerate(pillar_rod_lengths):
                pos = self.plates.all_pillar_positions[p]
                rod = cq.Workplane("XY").circle(self.plates.fixing_screws.metric_thread/2 - 0.2).extrude(length).translate((pos[0], pos[1], pillar_rod_zs[p]))
                show_object(rod, options={"color": rod_colour}, name="Fixing Rod {}".format(p))

        if with_key:
            if self.key_model is not None:
                show_object(self.key_model, options={"color": key_colour}, name="Key")

        if self.pulley is not None:
            show_object(self.pulley_model, options={"color": pulley_colour}, name="Pulley")

    def output_STLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_clock(), out)

    def outputSVG(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.svg".format(name))
        print("Outputting ", out)
        exportSVG(self.get_clock(), out, opts={"width":720, "height":1280})


def get_hand_demo(just_style=None, length = 120, per_row=3, assembled=False, time_min=10, time_hour=10, time_sec=0, chunky=False, outline=1, include_seconds=True):
    demo = cq.Workplane("XY")

    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensate_loose_arbour=True)
    print("motion works r", motionWorks.get_widest_radius())

    space = length

    if assembled:
        space = length*2

    for i,style in enumerate(HandStyle):

        if just_style is not None and style != just_style:
            continue

        hands = Hands(style=style, chunky=chunky, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=length, thick=motionWorks.minute_hand_slot_height, outline=outline,
                      outline_same_as_body=False, second_length=25)

        x = 0
        y = 0
        if just_style is None:
            x = space*(i % per_row)
            y = (space)*math.floor(i / per_row)

        secondsHand = None
        try:
            secondsHand =hands.get_hand(hand_type=HandType.SECOND)
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
            demo = demo.add(hands.get_assembled(include_seconds=False, time_seconds=time_sec, time_minute=time_min, time_hour=time_hour).translate((x, y, 0)))

            if secondsHand is not None and include_seconds:
                secondsHand = secondsHand.translate((x, y + length * 0.3))

                if not hands.second_hand_centred:
                    secondsHand = secondsHand.rotate((0,0,0),(0,1,0),180)
                demo = demo.add(secondsHand)


        else:
            demo = demo.add(hands.get_hand(hand_type=HandType.HOUR).translate((x, y)))
            demo = demo.add(hands.get_hand(hand_type=HandType.MINUTE).translate((x + length * 0.3, y)))
            if secondsHand is not None and include_seconds:
                demo = demo.add(secondsHand.translate((x - length * 0.3, y)))


    return demo

def show_hand_demo(show_object, length = 120, per_row=3, time_min=10, time_hour=10, time_sec=0, chunky=False, outline=1, include_seconds=True, second_length=25,
                   just_style = None):
    motion_works = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensate_loose_arbour=True)
    print("motion works r", motion_works.get_widest_radius())

    space = length * 2
    i = 0
    for style in HandStyle:
        if just_style is None or style == just_style:
            hands = Hands(style=style, chunky=chunky, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                          length=length, thick=motion_works.minute_hand_slot_height, outline=outline, outline_same_as_body=False, second_length=second_length)

            x = space * (i % per_row)
            y = (space) * math.floor(i / per_row)

            i+=1

            hands.show_hands(show_object, time_hours=time_hour, time_minutes=time_min, time_seconds=time_sec, position=(x,y))

def getAnchorDemo(style=AnchorStyle.STRAIGHT):
    escapment = AnchorEscapement(style=style)
    return escapment.getAnchor()


def get_ratchet_demo():
    min_outer_d = 40
    max_outer_d = 80



def get_gear_demo(module=1, just_style=None, one_gear=False):
    demo = cq.Workplane("XY")

    train = GoingTrain(pendulum_period=2, fourth_wheel=False, max_weight_drop=1000, use_pulley=True, chain_at_back=False, chain_wheels=1, runtime_hours=7.5 * 24)

    moduleReduction = 0.9

    train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)
    # train.setChainWheelRatio([93, 10])

    train.gen_cord_wheels(ratchet_thick=4, rod_metric_thread=4, cord_thick=1.5, cord_coil_thick=14, style=None, use_key=True, prefered_diameter=30)
    # override default until it calculates an ideally sized wheel
    train.calculate_powered_wheel_ratios(wheel_max=100)

    train.gen_gears(module_size=module, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, chain_wheel_thick=4, pinion_thick_multiplier=3, style=None, powered_wheel_module_increase=1, chain_wheel_pinion_thick_multiplier=2)

    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensate_loose_arbour=True)

    demoArboursNums = [0, 1, 3]

    #get a chain wheel, a normal wheel, an escape wheel and part of the motion works for a good spread of sizes and inner radii
    demoArbours = [train.get_arbour_with_conventional_naming(i) for i in demoArboursNums]
    demoArbours.append(motionWorks.get_motion_arbour())

    gap = 5
    space = max([arbour.get_max_radius() * 2 for arbour in demoArbours]) + gap

    if one_gear and just_style is not None:
        demoArbours[1].style = just_style
        return demoArbours[1].get_shape()

    x=0

    for i,style in enumerate(GearStyle):
        if just_style is not None and style != just_style:
            continue
        print(style.value)
        # try:
        y=0
        for arbour in demoArbours:
            arbour.style = style
            y += arbour.get_max_radius() + gap
            demo = demo.add(arbour.get_shape().translate((x, y, 0)))
            y += arbour.get_max_radius()

        x += space
        # except Exception as e:
        #     print("Failed to generate demo for {}: {}".format(style.value, e))

    return demo