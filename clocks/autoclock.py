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

def gen_gear_previews(out_path="autoclock", module=1):
    #lots copy pasted from gearDemo
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

    # get a chain wheel, a normal wheel, an escape wheel and part of the motion works for a good spread of sizes and inner radii
    demoArbours = [train.getArbourWithConventionalNaming(i) for i in demoArboursNums]
    demoArbours.append(motionWorks.getMotionArbour())
    gap = 5

    for gear_style in GearStyle:
        demo_file_name = "gear_demo_{}.svg".format( gear_style.value)
        preview_file_name = "gear_preview_{}.svg".format(gear_style.value)

        # demo = getGearDemo(justStyle=gear_style)
        demo = cq.Workplane("XY")
        y = 0
        for arbour in demoArbours:
            arbour.style = gear_style
            y += arbour.getMaxRadius() + gap
            demo = demo.add(arbour.getShape().translate((0, y, 0)))
            y += arbour.getMaxRadius()

        print("Exporting gear demo for {}".format(gear_style.value))
        # exporters.export(demo, os.path.join(out_path,demo_file_name),  opt={"width":480,"height":1024, "showAxes":False, "strokeWidth":0.2, "showHidden":False,"marginLeft": 480*0.125, "marginTop": 1024*0.125,})
        exportSVG(demo, os.path.join(out_path,demo_file_name),  opts={"width":500,"height":500, "showAxes":False, "strokeWidth":0.5, "showHidden":False})

        preview = demoArbours[1].getShape()#getGearDemo(justStyle=gear_style, oneGear=True)
        exportSVG(preview, os.path.join(out_path,preview_file_name),  opts={"width":150,"height":150, "showAxes":False, "strokeWidth":0.5,
                                                                                  "showHidden":False, "projectionDir": (0, 0, 1)})

def gen_anchor_previews(out_path="autoclock"):
    for style in AnchorStyle:
        file_name = "anchor_preview_{}.svg".format(style.value)
        print("Exporting Anchor {}".format(style.value))
        demo = getAnchorDemo(style)
        exportSVG(demo, os.path.join(out_path, file_name), opts={"width": 300, "height": 300, "showAxes": False, "strokeWidth": 0.5,
                                                                                  "showHidden": False, "projectionDir": (0, 0, 1)})

def gen_hand_previews(out_path="autoclock", length=120):
    motionWorks = MotionWorks(extra_height=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)

    for style in HandStyle:
        for centred_seconds in [True, False]:
            for outline in [0, 1]:

                outline_string="_with_outline" if outline > 0 else ""
                seconds_string = "_centred_seconds" if centred_seconds else ""

                print("Generating preview for {}{}{}".format(style.value, outline_string.replace("_"," "), seconds_string.replace("_", " ")))

                hands = Hands(style=style, length=length, outline=outline, second_hand_centred=centred_seconds,
                              thick=3, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(),
                              hourfixing_d=motionWorks.getHourHandHoleD())
                demo = hands.getAssembled()#include_seconds=centred_seconds

                file_name = "hands_{}{}{}.svg".format(style.value,outline_string, seconds_string)

                exportSVG(demo, os.path.join(out_path, file_name), opts={"width": 600, "height": 600, "showAxes": False, "strokeWidth": 0.5,
                                                                           "showHidden": False, "projectionDir": (0, 0, 1)})

def gen_dial_previews(out_path="autoclock", diameter=180):
    for style in DialStyle:
        dial = Dial(diameter, style=style)

        print("Generating preview for {} dial".format(style.value))
        file_name = "dial_{}.svg".format(style.value)
        exportSVG(dial.get_dial(), os.path.join(out_path, file_name),opts={"width": 300, "height": 300, "showAxes": False, "strokeWidth": 0.5,
                                                                           "showHidden": False, "projectionDir": (0, 0, -1)})

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



        self.train = GoingTrain(pendulum_period=self.pendulum_period_s, fourth_wheel=False, escapement=self.escapement, maxWeightDrop=self.weight_drop,
                           usePulley=True, chainAtBack=False, chainWheels=1, hours=self.hours, huygensMaintainingPower=self.huygens)

        self.moduleReduction = 0.85
        self.train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=self.moduleReduction)

        self.train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=self.gear_style, useKey=True, preferedDiameter=25, looseOnRod=False, prefer_small=True)



        self.train.genGears(module_size=self.module_size, moduleReduction=self.moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=self.gear_style,
                       chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, pendulumFixing=self.pendulumFixing)

        bearing = None
        if self.centred_second_hand:
            bearing = getBearingInfo(3)

        self.motionWorks = MotionWorks(style=self.gear_style, thick=3, compensateLooseArbour=False, bearing=bearing, compact=True, module=1)

        self.pendulum = Pendulum(self.train.escapement, self.train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, handAvoiderInnerD=self.ring_d,
                                  bobD=self.bob_d, bobThick=10, useNylocForAnchor=False)
        self.dial = None


        if self.has_dial:
            bottom_fixing = False
            top_fixing = True
            # clock 12 (and roughly clock 19)
            dial_diameter = 180

            if not self.centred_second_hand:
                dial_diameter = 200
                bottom_fixing = True
                if self.train.has_seconds_hand():
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

        self.plates = SimpleClockPlates(self.train, self.motionWorks, self.pendulum, plateThick=front_thick, backPlateThick=back_thick, pendulumSticksOut=self.pendulumSticksOut, name="auto", style="vertical",
                                         motionWorksAbove=motionWorksAbove, heavy=heavy, extraHeavy=extraHeavy, pendulumFixing=self.pendulumFixing, pendulumAtFront=False,
                                         backPlateFromWall=self.pendulumSticksOut * 2, fixingScrews=MachineScrew(metric_thread=3, countersunk=True, length=40),
                                         chainThroughPillarRequired=True, dial=self.dial, centred_second_hand=self.centred_second_hand, pillars_separate=True)

        if self.has_dial and not self.centred_second_hand and self.train.has_seconds_hand():
            self.second_hand_length = self.dial.second_hand_mini_dial_d*0.5

        outline = 1 if self.hand_has_outline else 0
        minute_fixing = "circle" if bearing is not None else "square"
        outlineSameAsBody = False
        if self.hand_style == HandStyle.XMAS_TREE:
            outlineSameAsBody = True
        self.hands = Hands(style=self.hand_style, minuteFixing=minute_fixing, minuteFixing_d1=self.motionWorks.getMinuteHandSquareSize(), hourfixing_d=self.motionWorks.getHourHandHoleD(),
                            length=self.hand_length, thick=self.motionWorks.minuteHandSlotHeight, outline=outline, outlineSameAsBody=outlineSameAsBody,
                           second_hand_centred=self.centred_second_hand, chunky=True, secondLength=self.second_hand_length)

        self.pulley = BearingPulley(diameter=self.train.poweredWheel.diameter, bearing=getBearingInfo(4), wheel_screws=MachineScrew(2, countersunk=True, length=8))

        self.model = Assembly(self.plates, hands=self.hands, timeSeconds=30, pulley=self.pulley)




    def get_svg_text(self):
        if not self.clock_generated:
            self.gen_clock()
        return exportSVG(self.model.getClock(), None, opts={"width": 720, "height": 720, "strokeWidth": 0.2, "showHidden": False})

    def output_svg(self, path):
        if not self.clock_generated:
            self.gen_clock()
        basename =  os.path.join(path, self.name)
        out = basename + ".svg"

        print("Exporting {}".format(out))
        svg = exportSVG(self.model.getClock(), out, opts={"width":720, "height":720, "strokeWidth": 0.2, "showHidden": False})
        svg2png(url=out, write_to=basename+".png", background_color="rgb(255,255,255)", output_width=1440)
        svg2png(url=out, write_to=basename + "_small.png", background_color="rgb(255,255,255)", output_width=720)
        return svg