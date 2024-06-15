from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *

# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


start_angle = 0
end_angle = math.pi*2
steps = 500



chain = COUSINS_1_5MM_CHAIN
chain = REGULA_8_DAY_1_05MM_CHAIN

pocket_wheel = PocketChainWheel2(chain=chain, max_diameter=30)
radius = pocket_wheel.radius

circumference = chain.pitch*6
radius = circumference/(math.pi*2)
extra_space = 0.2

if outputSTL:
    sprocket = cq.Workplane("XY").circle(radius+chain.width).extrude(chain.width - chain.wire_thick*3)

    link_length = chain.inside_length + chain.wire_thick*2

    links = 20


    one_link = get_stroke_line([(0, link_length/2 - chain.width/2 - extra_space), (0, -link_length/2 + chain.width/2 + extra_space)], wide=chain.width+extra_space*2,thick=5)
    chain_cutter = cq.Workplane("XY")
    for i in range(links):
        chain_cutter = chain_cutter.add(one_link.translate((-radius, chain.pitch/2 + (i - links/2)*chain.pitch)))
    # chain_cutter = chain_cutter.translate((-radius, chain.pitch/2)).add(chain_cutter.translate((-radius, -chain.pitch/2)))
    # show_object(chain_cutter)


    angle_diff = (end_angle - start_angle)/steps
    for i in range(steps):
        angle = start_angle + i*angle_diff

        y = -angle_diff*i* radius
        sprocket = sprocket.rotate((0,0,0), (0,0,1), rad_to_deg(angle_diff))
        sprocket = sprocket.cut(chain_cutter.translate((0,y )))
        # show_object(chain_cutter.translate((0, y)))


    show_object(sprocket)
# show_object(chain_cutter.translate((0, y)))


    assembly = cq.Assembly()
    assembly.add(sprocket)
    assembly.save("sprocket.step")

else:
    result = cq.importers.importStep("sprocket.step")
    show_object(result)

pair = WheelPinionPair(wheelTeeth=100000, pinionTeeth=6, module=4)

show_object(pair.pinion.get2D().rotate((0,0,0), (0,0,1), 8.25))

# cqsprocket = Sprocket(
#     num_teeth=6,
#     clearance=0.05,
#     bolt_circle_diameter=30 * MM,
#     num_mount_bolts=4,
#     mount_bolt_diameter=3 * MM,
#     bore_diameter=4 * MM,
#     chain_pitch=chain.pitch,
#     #this is the bodge bit
#     roller_diameter = chain.wire_thick*2 + extra_space*2
# )
# show_object(cqsprocket)