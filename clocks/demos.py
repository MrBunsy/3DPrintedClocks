import cadquery as cq

from .plates import *
from .escapements import *
from .gearing import *
from .hands import *
from .types import *
from .utility import *

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