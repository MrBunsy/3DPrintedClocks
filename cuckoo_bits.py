import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


def chain_plate():
    '''
    I cut the chain holes in the wrong place for Frankencuckoo, so now there needs to be something in place to stop the weights falling furtehr than they should
    so this is just a simple new plate to put over the top
    :return:
    '''

    width= 80
    length=40
    thick = 2
    #two centre chains are 1.4cm apart, end two chains are 5.3cm
    chain1=14/2
    chain2=53/2

    chain_d = 8



    return (cq.Workplane("front").box(width, length, thick).pushPoints([(-chain2, 0), (-chain1, 0),(chain1, 0), (chain2, 0)])
    .circle(chain_d/2).cutThruAll())


rod_width = 10
rod_thick = 3.5

def pendulum_rod(length=110, max_length=170, hook_type="normal", fixing="simple"):
    '''

    :param length: aprox lenght from tip of rod to bob
    :param max_length: max length bob could be adjusted down
    :param hook_type: how the rod fixes to the pendulum leader ("normal" or "toy")
    :param fixing: How the bob fixes to the rod. Simple is slide-friction fit, thread is an attempt at a mantle-style pendulum adjustment
    :return:
    '''

    normal_hook_width = 5.5
    hook_gap=1.5

    hook_thick = 2
    hook_height=10

    rod = cq.Workplane("XY").tag("base")

    #lieing on its side, x is therefore thickness, z is width and y is height
    #top centre of rod is at 0,0 fixing is +ve y, rest of rod is -ve y

    if fixing == "simple":
        #just a rectangular length
        rod = rod.workplaneFromTagged("base").move(0,-max_length/2).box(rod_thick,max_length,rod_width)
        rod = rod.faces(">X").workplane().transformed(offset=(0,0,-rod_thick)).move(-max_length,rod_width/2).lineTo(-max_length-rod_width/2,0).lineTo(-max_length,-rod_width/2).close().extrude(rod_thick)

    if hook_type == "normal":
        # rod = rod.faces(">Y").workplane().rect(hook_thick,normal_hook_width).extrude(hook_height)
        # rod = rod.faces(">Y").workplane().transformed(offset=cq.Vector(0,0,-hook_thick/2),rotate=cq.Vector(0,130,0)).rect(hook_thick, normal_hook_width).extrude(hook_height/2)

        hook_top_thick = hook_thick * 2 + hook_gap
        rod = rod.workplaneFromTagged("base").transformed(offset=(hook_gap/2,0,(rod_width-normal_hook_width)/2-rod_width/2)).tag("hook_base").moveTo(0,hook_height/2).rect(hook_thick,hook_height).extrude(normal_hook_width)

        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick/2+hook_thick/2,hook_height).circle(radius=hook_top_thick/2).extrude(normal_hook_width)

        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick / 2 + hook_thick / 2, hook_height-hook_top_thick/4).rect(hook_top_thick,hook_top_thick/2).extrude(normal_hook_width)

        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick/2+hook_thick/2,hook_height).circle(radius=hook_gap/2).cutThruAll()
        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick / 2 + hook_thick / 2, hook_height - hook_top_thick / 4).rect(hook_gap, hook_top_thick / 2).cutThruAll()

    return rod


def pendulum_bob_fixing():
    '''
    Bit that can glue onto the back of a pretty pendulum bob and be used to adjust its height on the pendulum rod
    :return:
    '''

    width = rod_width*2
    length = width*2
    thick = rod_thick*3
    back_thick = 2

    rod_thick_hole = rod_thick+1

    wire_hole_d = 1.5

    fixing = cq.Workplane("XY").tag("base")

    fixing = fixing.rect(width,length).extrude(thick)

    wire_z = (thick - (back_thick + rod_thick_hole)) / 2

    fixing = fixing.faces(">Y").workplane().moveTo(0,thick - (back_thick + rod_thick_hole/2)).rect(rod_width+1,rod_thick_hole).cutThruAll()

    fixing = fixing.faces(">Y").workplane().moveTo(0, wire_z).circle(radius=wire_hole_d/2).cutThruAll()

    # fixing = fixing.faces(">X").workplane().moveTo(0,1.7).circle(radius=wire_hole_d / 2).cutThruAll()



    #why is 0,0 suddenly in the corner?
    # fixing = fixing.faces(">X").workplane().moveTo(0, (thick - rod_thick)/4).rect(wire_hole_d,wire_hole_d).cutThruAll()
    fixing = fixing.faces(">X").workplane().moveTo(0, wire_z).circle(wire_hole_d*0.6).cutThruAll()
    fixing = fixing.faces(">X").workplane().moveTo(-length,wire_z).circle(wire_hole_d * 0.6).cutThruAll()

    slot = cq.Workplane("XY").box(length*0.8,width*0.8,thick)
    # return slot

    fixing = fixing.cut(slot)

    # fixing = cq.selectors.SubtractSelector(fixing,slot)

    return fixing

plate = chain_plate()
rod = pendulum_rod()
fixing = pendulum_bob_fixing()

# show_object(plate)
# show_object(rod)
show_object(fixing)

# exporters.export(plate, "out/cuckoo_chain_plate.stl", tolerance=0.001, angularTolerance=0.01)
exporters.export(rod, "out/cuckoo_pendulum_rod.stl", tolerance=0.001, angularTolerance=0.01)
exporters.export(fixing, "out/cuckoo_pendulum_fixing.stl", tolerance=0.001, angularTolerance=0.01)