
from clocks.autoclock import *
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

def xmas_pub(pendulum):
    leaf_thick = 1
    pud = ChristmasPudding(thick=leaf_thick, diameter=pendulum.bobR * 2, cut_rect_width=pendulum.gapWidth + 0.1, cut_rect_height=pendulum.gapHeight + 0.1)

    pretty_bob = ItemWithCosmetics(pendulum.getBob(hollow=True), name="bob_pud", background_colour="brown", cosmetics=pud.get_cosmetics(), colour_thick_overrides={"green": leaf_thick})

    return pretty_bob.get_model().rotate((0,0,pendulum.bobThick/2), (0,1,pendulum.bobThick/2), 180)

if outputSTL:
    # gen_dial_previews("images/", image_size=125)
    out_dir = "images/"
    # gen_motion_works_preview(out_dir)
    # motion_works = MotionWorks(compact=True, bearing=getBearingInfo(3), extra_height=20)
    # motion_works.calculateGears(arbourDistance=30)
    # gen_motion_works_preview(out_dir, motion_works)
    # gen_anchor_previews(out_dir, two_d=False)
    # gen_grasshopper_previews(out_dir, two_d=False)

    # pendulum = Pendulum(bobD=80)
    # demo = pendulum.getBob()
    # gen_shape_preview(demo, "bob_preview", out_dir)
    # gen_shape_preview(xmas_pub(pendulum), "xmas_pub_bob_preview", out_dir)

    # gen_hand_previews("images/", size=200, only_these=[HandStyle.BAROQUE, HandStyle.SIMPLE_ROUND])

    pulley = BearingPulley(diameter=35, bearing=get_bearing_info(4), wheel_screws=MachineScrew(2, countersunk=True, length=8))
    lightweight_pulley = LightweightPulley(diameter=35, use_steel_rod=False)

    gen_shape_preview(pulley.get_assembled().rotate((0,0,0),(0,0,1),90), "pulley_preview", out_dir)
    gen_shape_preview(lightweight_pulley.get_assembled(), "lightweight_pulley_preview", out_dir)

