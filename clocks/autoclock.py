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
import math
import cadquery as cq
from cadquery import exporters
from .power import *
from .escapements import *
from .striking import *
from .clock import *
from .utility import *
from .leaves import HollyLeaf, Wreath, HollySprig
from .cosmetics import *
from .dial import *
from .cq_svg import exportSVG
import os

try:
    from cairosvg import svg2png
except:
    pass

'''
Tools for a configurable clock, destined to be driven by a web GUI
'''

DEFAULT_SVG_EXPORT_OPTIONS = {"width": 300, "height": 300, "showAxes": False, "strokeWidth": 0.5,
            "showHidden": False}

def gen_gear_previews(out_path="autoclock", module=1):
    #lots copy pasted from gearDemo
    train = GoingTrain(pendulum_period=2, fourth_wheel=False, max_weight_drop=1200, use_pulley=True, chain_at_back=False, chain_wheels=1, runtime_hours=7.5 * 24)

    moduleReduction = 0.9

    train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)
    # train.setChainWheelRatio([93, 10])

    train.gen_cord_wheels(ratchet_thick=4, rod_metric_thread=4, cord_thick=1.5, cord_coil_thick=14, style=None, use_key=True, prefered_diameter=25)
    # override default until it calculates an ideally sized wheel
    train.calculate_powered_wheel_ratios(wheel_max=100)

    train.gen_gears(module_size=module, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, useNyloc=False, pinionThickMultiplier=3, style=None, chain_module_increase=1, chainWheelPinionThickMultiplier=2)

    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)

    demoArboursNums = [0, 1, 3]

    # get a chain wheel, a normal wheel, an escape wheel and part of the motion works for a good spread of sizes and inner radii
    demoArbours = [train.get_arbour_with_conventional_naming(i) for i in demoArboursNums]
    demoArbours.append(motionWorks.getMotionArbour())
    gap = 5

    for gear_style in GearStyle:
        demo_file_name = "gear_demo_{}.svg".format( gear_style.value)
        preview_file_name = "gear_preview_{}.svg".format(gear_style.value)
        preview_3d_file_name = "gear_preview_{}.tjs".format(gear_style.value)

        # demo = getGearDemo(justStyle=gear_style)
        demo = cq.Workplane("XY")
        y = 0
        for arbour in demoArbours:
            arbour.style = gear_style
            y += arbour.get_max_radius() + gap
            demo = demo.add(arbour.get_shape().translate((0, y, 0)))
            y += arbour.get_max_radius()

        print("Exporting gear demo for {}".format(gear_style.value))
        # exporters.export(demo, os.path.join(out_path,demo_file_name),  opt={"width":480,"height":1024, "showAxes":False, "strokeWidth":0.2, "showHidden":False,"marginLeft": 480*0.125, "marginTop": 1024*0.125,})
        exportSVG(demo, os.path.join(out_path,demo_file_name),  opts={"width":500,"height":500, "showAxes":False, "strokeWidth":0.5, "showHidden":False})

        preview = demoArbours[1].get_shape()#getGearDemo(justStyle=gear_style, oneGear=True)
        exportSVG(preview, os.path.join(out_path,preview_file_name),  opts={"width":150,"height":150, "showAxes":False, "strokeWidth":0.5,
                                                                                  "showHidden":False, "projectionDir": (0, 0, 1)})
        cq.exporters.export(preview,os.path.join(out_path, preview_3d_file_name))

def gen_anchor_previews(out_path="autoclock", two_d = True):
    for style in AnchorStyle:
        file_name = "anchor_preview_{}.svg".format(style.value)
        print("Exporting Anchor {}".format(style.value))
        demo = getAnchorDemo(style)
        opts = {"width": 300, "height": 300, "showAxes": False, "strokeWidth": 0.5,
                "showHidden": False}
        if two_d:
            opts["projectionDir"]= (0, 0, 1)

        exportSVG(demo, os.path.join(out_path, file_name), opts=opts)

def gen_grasshopper_previews(out_path="autoclock", two_d = True):
    file_name="grasshopper_preview.svg"
    print("Exporting {}".format(file_name))
    demo = GrasshopperEscapement.get_harrison_compliant_grasshopper().get_assembled()

    opts = DEFAULT_SVG_EXPORT_OPTIONS.copy()
    if two_d:
        opts["projectionDir"] = (0, 0, 1)

    exportSVG(demo, os.path.join(out_path, file_name), opts=opts)

def gen_shape_preview(demo, name, out_path="autoclock", size=300):

    opts = DEFAULT_SVG_EXPORT_OPTIONS.copy()

    opts["width"] = size
    opts["height"] = size

    file_name = "{}.svg".format(name)

    exportSVG(demo, os.path.join(out_path, file_name), opts=opts)

def gen_hand_previews(out_path="autoclock", length=120, size=600, only_these=None):
    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)

    for style in HandStyle:
        if only_these is None or style in only_these:
            for centred_seconds in [True, False]:
                for outline in [0, 1]:

                    outline_string="_with_outline" if outline > 0 else ""
                    seconds_string = "_centred_seconds" if centred_seconds else ""

                    print("Generating preview for {}{}{}".format(style.value, outline_string.replace("_"," "), seconds_string.replace("_", " ")))

                    hands = Hands(style=style, length=length, outline=outline, second_hand_centred=centred_seconds,
                                  thick=3, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(),
                                  hourfixing_d=motionWorks.getHourHandHoleD())
                    demo = hands.get_assembled()#include_seconds=centred_seconds

                    file_name = "hands_{}{}{}.svg".format(style.value,outline_string, seconds_string)

                    exportSVG(demo, os.path.join(out_path, file_name), opts={"width": size, "height": size, "showAxes": False, "strokeWidth": 0.5,
                                                                               "showHidden": False, "projectionDir": (0, 0, 1)})

def gen_dial_previews(out_path="autoclock", diameter=180, image_size=300):
    for style in DialStyle:
        dial = Dial(diameter, style=style)

        print("Generating preview for {} dial".format(style.value))
        file_name = "dial_{}.svg".format(style.value)
        exportSVG(dial.get_dial(), os.path.join(out_path, file_name),opts={"width": image_size, "height": image_size, "showAxes": False, "strokeWidth": 0.5,
                                                                           "showHidden": False, "projectionDir": (0, 0, -1)})
def gen_motion_works_preview(out_path="autoclock", motion_works=None, image_size=300):
    if motion_works is None:
        motion_works = MotionWorks(compact=False)

    name = "{}{}".format("_compact" if motion_works.compact else "", "_bearing" if motion_works.bearing is not None else "")

    file_name = "motion_works{}.svg".format(name)
    exportSVG(motion_works.get_assembled(), os.path.join(out_path, file_name), opts={"width": image_size, "height": image_size, "showAxes": False, "strokeWidth": 0.5,
                                                                        "showHidden": False})


def gen_clock_previews(out_path="autoclock"):
    days=8
    pendulum_period_s=2
    dial_seconds_style = DialStyle.CONCENTRIC_CIRCLES
    total = len(DialStyle) * 2 * len(GearStyle) * len(HandStyle) * 2 * len(AnchorStyle) * 2
    print("total combos", total)
    return False
    for dial_style in DialStyle:
        for has_dial in [True, False]:
            for gear_style in GearStyle:
                for hand_style in HandStyle:
                    for hand_has_outline in [True, False]:
                        for escapement_style in AnchorStyle:
                            for centred_second_hand in [True, False]:
                                clock = AutoWallClock(dial_style=dial_style,
                                                      dial_seconds_style=dial_seconds_style,
                                                      has_dial=has_dial,
                                                      gear_style=gear_style,
                                                      hand_style=hand_style,
                                                      hand_has_outline=hand_has_outline,
                                                      pendulum_period_s=pendulum_period_s,
                                                      escapement_style=escapement_style,
                                                      days=days,
                                                      centred_second_hand=centred_second_hand)

def enum_to_typescript(enum):
    name = enum.__name__

    contents=["{} = \"{}\"".format(data.name, data.value) for data in enum]
    contents_list = ["{}.{}".format(name,data.name) for data in enum]

    typescript="""export enum {name}{{
    {contents}
}}
export let {name}_list: {name}[] = [{contents_list}]
""".format(name=name, contents=",\n    ".join(contents), contents_list=",".join(contents_list))

    return typescript

def gen_typescript_enums(outpath):

    with open(outpath,"w") as outfile:
        outfile.write("""
/**
THIS FILE IS AUTOGENERATED FROM PYTHON, DO NOT EDIT MANUALLY
*/
""")
        outfile.writelines(enum_to_typescript(EscapementType))
        outfile.writelines("\n")
        outfile.writelines(enum_to_typescript(GearStyle))
        outfile.writelines("\n")
        outfile.writelines(enum_to_typescript(HandStyle))
        outfile.writelines("\n")
        outfile.writelines(enum_to_typescript(AnchorStyle))
        outfile.writelines("\n")
        outfile.writelines(enum_to_typescript(DialStyle))

class DialWithHands:
    def __init__(self, diameter=180, style=DialStyle.LINES_ARC, hand_style=HandStyle.SIMPLE_ROUND, centred_second_hand=False, hand_has_outline=True):
        self.diameter = diameter
        self.style = style
        self.hand_style = hand_style
        self.centred_second_hand = centred_second_hand
        self.hand_has_outline = hand_has_outline

        centred_string = "_centred_second" if centred_second_hand else ""
        outline_string = "_outline" if hand_has_outline else ""

        self.name = f"dial_{diameter}_{style.value}_{hand_style.value}{centred_string}{outline_string}"
        self.generated = False

    def gen_dial(self):
        self.generated = True
        self.dial = Dial(outside_d= self.diameter, style=self.style)

        outline = 1 if self.hand_has_outline else 0
        minute_fixing = "square"
        outlineSameAsBody = False
        if self.hand_style == HandStyle.XMAS_TREE:
            outlineSameAsBody = True

        self.hands = Hands(style=self.hand_style, minuteFixing=minute_fixing, minuteFixing_d1=5.2, hourfixing_d=11.5,
                           length=self.diameter*0.45, thick=3, outline=outline, outlineSameAsBody=outlineSameAsBody,
                           second_hand_centred=self.centred_second_hand, chunky=True, secondLength=30)
        #on second thoughts, generating it ourselves is easier, don't have to worry about seconds hands or taking lots of time to generate motion works
        # self.autoclock = AutoWallClock(centred_second_hand=self.centred_second_hand, has_dial=True, dial_style=self.style,hand_style=self.hand_style,hand_has_outline=self.hand_has_outline)
        # self.autoclock.gen_clock()

        self.dial_demo = self.dial.get_dial().rotate((0,0,0), (0,1,0),180).add(self.hands.get_assembled(include_seconds=self.centred_second_hand))

    def output_svg(self, path, width=-1):
        if not self.generated:
            self.gen_dial()
        basename =  os.path.join(path, self.name)
        out = basename + ".svg"
        if width < 0:
            width = 400
        print("Exporting {}".format(out))
        svg = exportSVG(self.dial_demo, out, opts={"width":width, "strokeWidth": 0.25, "showHidden": False, "projectionDir": (0, 0, 1)})
        svg2png(url=out, write_to=basename+".png", background_color="rgb(255,255,255)", output_width=600)
        svg2png(url=out, write_to=basename + "_small.png", background_color="rgb(255,255,255)", output_width=300)
        return svg


class AutoWallClock:

    def __init__(self, pendulum_period_s=2, days=8, centred_second_hand=False, has_dial=False, gear_style=GearStyle.CIRCLES,
                 escapement_style=AnchorStyle.CURVED_MATCHING_WHEEL, dial_style=DialStyle.LINES_ARC, dial_seconds_style=None, hand_style=HandStyle.SIMPLE_ROUND, hand_has_outline=True):
        '''
        Attempt to automatically configure a valid wall clock
        '''

        # currently based on clock 12
        self.hours = max(1,days-1) * 24 + 6
        self.pendulum_period_s = pendulum_period_s
        self.pendulumFixing = PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS
        self.weight_drop = 1200
        self.huygens = False
        self.module_size=1
        self.ring_d = 100
        self.bob_d = 100
        #will be overriden if we have a dial
        self.hand_length = 120
        self.gear_style = gear_style
        self.second_hand_length=25
        self.hand_style = hand_style
        self.hand_has_outline = hand_has_outline
        self.centred_second_hand = centred_second_hand
        self.dial_style = dial_style
        self.dial_seconds_style = dial_seconds_style
        self.escapement_style = escapement_style
        self.has_dial = has_dial
        self.days = days

        self.pendulumSticksOut = 20

        if pendulum_period_s < 2:
            self.bob_d = 75

        if days < 8:
            self.module_size = 1.25

        dial_style_string = ""
        if has_dial:
            dial_style_string = "_" + dial_style.value
            if dial_seconds_style is not None:# and self.train.has_seconds_hand():
                #record the second style regardless of if its present - we want to get this name without doing any heavy processing
                dial_style_string += "_" + dial_seconds_style.value
        self.name = "autoclock_{period}s_{days}day{centred_second}_{dial}{dial_style}_{gear}_{escapement}_{hands}".format(period=pendulum_period_s,
                                                                                                                          days=days,
                                                                                                                          centred_second="centred_second" if centred_second_hand else "",
                                                                                                                          dial="dial" if has_dial else "nodial",
                                                                                                                          gear=gear_style.value,
                                                                                                                          escapement=escapement_style.value,
                                                                                                                          dial_style=dial_style_string,
                                                                                                                          hands=hand_style.value + ("_outline" if hand_has_outline else ""))

        self.clock_generated = False

    def gen_clock(self):
        self.clock_generated = True
        #TODO auto optimal pallets
        if self.pendulum_period_s > 1.5:
            #viable for second hand with 2s pendulum
            lift = 4
            drop = 2
            lock = 2
            self.escapement = AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, toothBaseAngle=4, style=self.escapement_style)
        else:
            # for period 1.5 with second hand, but viable for all short pendulums
            drop = 1.5
            lift = 3
            lock = 1.5
            self.escapement = AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, style=self.escapement_style)



        self.train = GoingTrain(pendulum_period=self.pendulum_period_s, fourth_wheel=False, escapement=self.escapement, max_weight_drop=self.weight_drop,
                                use_pulley=True, chain_at_back=False, chain_wheels=1, runtime_hours=self.hours, huygens_maintaining_power=self.huygens)

        self.moduleReduction = 0.85
        self.train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=self.moduleReduction)

        self.train.gen_cord_wheels(ratchet_thick=4, rod_metric_thread=4, cord_thick=1, cord_coil_thick=14, style=self.gear_style, use_key=True, prefered_diameter=25, loose_on_rod=False, prefer_small=True)



        self.train.gen_gears(module_size=self.module_size, moduleReduction=self.moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=self.gear_style,
                             chain_module_increase=1, chainWheelPinionThickMultiplier=2, pendulumFixing=self.pendulumFixing)

        bearing = None
        if self.centred_second_hand:
            bearing = get_bearing_info(3)

        self.motionWorks = MotionWorks(style=self.gear_style, thick=3, compensateLooseArbour=False, bearing=bearing, compact=True, module=1)

        self.pendulum = Pendulum(self.train.escapement, self.train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, hand_avoider_inner_d=self.ring_d,
                                 bob_d=self.bob_d, bob_thick=10, useNylocForAnchor=False)
        self.dial = None


        if self.has_dial:
            bottom_fixing = False
            top_fixing = True
            # clock 12 (and roughly clock 19)
            dial_diameter = 180

            if not self.centred_second_hand:
                dial_diameter = 200
                bottom_fixing = True
                if self.train.has_seconds():
                    #need sub dial for second hand so this dial has to be large (and will print in two pieces)
                    dial_diameter=245
                    #second hand length calculated after plates have reconfigured the dial

            self.dial = Dial(outside_d=dial_diameter, bottom_fixing=bottom_fixing, top_fixing=top_fixing, seconds_style=self.dial_seconds_style, style=self.dial_style)
            self.hand_length = self.dial.outside_d * 0.45

        front_thick = 9
        back_thick = 11
        motionWorksAbove = True
        heavy = True
        extraHeavy = True
        if self.days < 8:
            front_thick = 6
            back_thick = 6
            motionWorksAbove = False
            heavy = False
            extraHeavy = False

        if self.centred_second_hand:
            motionWorksAbove = False

        self.plates = SimpleClockPlates(self.train, self.motionWorks, self.pendulum, plate_thick=front_thick, back_plate_thick=back_thick, pendulum_sticks_out=self.pendulumSticksOut, name="auto", style=ClockPlateStyle.VERTICAL,
                                        motion_works_above=motionWorksAbove, heavy=heavy, extra_heavy=extraHeavy, pendulum_fixing=self.pendulumFixing, pendulum_at_front=False,
                                        back_plate_from_wall=self.pendulumSticksOut * 2, fixing_screws=MachineScrew(metric_thread=3, countersunk=True, length=40),
                                        chain_through_pillar_required=True, dial=self.dial, centred_second_hand=self.centred_second_hand, pillars_separate=True)

        if self.has_dial and not self.centred_second_hand and (self.train.has_seconds_hand_on_escape_wheel() or self.train.has_second_hand_on_last_wheel()):
            self.second_hand_length = self.dial.second_hand_mini_dial_d*0.5

        outline = 1 if self.hand_has_outline else 0
        minute_fixing = "circle" if bearing is not None else "square"
        outlineSameAsBody = False
        if self.hand_style == HandStyle.XMAS_TREE:
            outlineSameAsBody = True
        self.hands = Hands(style=self.hand_style, minuteFixing=minute_fixing, minuteFixing_d1=self.motionWorks.getMinuteHandSquareSize(), hourfixing_d=self.motionWorks.getHourHandHoleD(),
                            length=self.hand_length, thick=self.motionWorks.minuteHandSlotHeight, outline=outline, outlineSameAsBody=outlineSameAsBody,
                           second_hand_centred=self.centred_second_hand, chunky=True, secondLength=self.second_hand_length)

        self.pulley = BearingPulley(diameter=self.train.powered_wheel.diameter, bearing=get_bearing_info(4), wheel_screws=MachineScrew(2, countersunk=True, length=8))

        self.model = Assembly(self.plates, hands=self.hands, timeSeconds=30, pulley=self.pulley, pendulum=self.pendulum)




    def get_svg_text(self):
        if not self.clock_generated:
            self.gen_clock()
        return exportSVG(self.model.get_clock(), None, opts={"width": 720, "height": 720, "strokeWidth": 0.2, "showHidden": False})

    def output_svg(self, path):
        if not self.clock_generated:
            self.gen_clock()
        basename =  os.path.join(path, self.name)
        out = basename + ".svg"

        print("Exporting {}".format(out))
        svg = exportSVG(self.model.get_clock(), out, opts={"width":720, "height":720, "strokeWidth": 0.2, "showHidden": False})
        svg2png(url=out, write_to=basename+".png", background_color="rgb(255,255,255)", output_width=1440)
        svg2png(url=out, write_to=basename + "_small.png", background_color="rgb(255,255,255)", output_width=720)
        return svg
