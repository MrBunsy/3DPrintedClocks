from clocks.escapements import *

class AnchorEscapementBox2D:
    # def __init__(self, teeth=30, diameter=100, anchor_teeth=None, type=EscapementType.DEADBEAT, lift=4, drop=2, run=10, lock=2,
    #              tooth_height_fraction=0.2, tooth_tip_angle=5, tooth_base_angle=4, wheel_thick=3, force_diameter=False, anchor_thick=12,
    #              style=AnchorStyle.CURVED_MATCHING_WHEEL, arbor_d=3):
    #     super().__init__(teeth=teeth, diameter=diameter, anchor_teeth=anchor_teeth, type=type, lift=lift, drop=drop, run=run, lock=lock,
    #              tooth_height_fraction=tooth_height_fraction, tooth_tip_angle=tooth_tip_angle, tooth_base_angle=tooth_base_angle, wheel_thick=wheel_thick, force_diameter=force_diameter, anchor_thick=anchor_thick,
    #              style=style, arbor_d=arbor_d)

    def __init__(self, anchor, box2d_world, friction=0.1, density=1):
        self.anchor = anchor
        self.box2d_world = box2d_world
        self.friction = friction
        self.density = density

    def add_anchor_to_body(self, body, offset_y):
        '''
        no curves in box2d and no concave shapes, so going to break this into bits
        assumes pivot point is at 0,0 (TODO check this is sensible)
        '''

        #
        # vertices = []
        # body.CreatePolygonFixture(vertices=vertices, density=self.density, friction=self.friction)
        pallet_r = self.anchor.pallet_r/2
        if self.anchor.type == EscapementType.BROCOT:
            #entry_pallet_stone_centre
            #pallet_r
            for pos in [self.anchor.entry_pallet_stone_centre, self.anchor.exit_pallet_stone_centre]:
                body.CreateCircleFixture(radius=pallet_r/1000, density=self.density, friction=self.friction,
                                         pos=(pos[0]/1000, pos[1]/1000 - self.anchor.anchor_centre_distance/1000 + offset_y))

    def add_escape_wheel_to_body(self, body, scale):
        '''
        copypaste from get_wheel_2d
        '''
        dA = -math.pi * 2 / self.anchor.teeth
        toothTipArcAngle = self.anchor.tooth_tip_width / self.anchor.diameter

        if self.anchor.type == EscapementType.RECOIL:
            # based on the angle of the tooth being 20deg, but I want to calculate everyting in angles from the cetnre of the wheel
            # lazily assume arc along edge of inner wheel is a straight line
            toothAngle = math.pi * 20 / 180
            toothTipAngle = 0
            toothBaseAngle = -math.atan(math.tan(toothAngle) * self.anchor.tooth_height / self.anchor.inner_radius)
        elif self.anchor.type in [EscapementType.DEADBEAT]:
            # done entirely by eye rather than working out the maths to adapt the book's geometry.
            toothTipAngle = -self.anchor.tooth_tip_angle  # -math.pi*0.05
            toothBaseAngle = -self.anchor.tooth_base_angle  # -math.pi*0.03
            toothTipArcAngle *= -1
        elif self.anchor.type in [EscapementType.BROCOT]:
            '''
            This needs a little explaination - I want the "front" edge of the tooth to be exactly radial (if that's the word for sticking straight out) from the wheel
            but since this needs the tooth tip taking into account for the current code, I'm doing it internally here and so the BrocotEscapement class only needs
            to set tooth_tip_angle
            '''
            toothTipAngle = - self.anchor.tooth_tip_angle
            toothBaseAngle = -self.anchor.tooth_tip_angle - toothTipArcAngle
            toothTipArcAngle *= -1

        # print("tooth tip angle: {} tooth base angle: {}".format(radToDeg(toothTipAngle), radToDeg(toothBaseAngle)))
        body.CreateCircleFixture(radius=(self.anchor.inner_radius)/1000, density=self.density, friction=self.friction)

        for i in range(self.anchor.teeth):
            angle = dA * i
            basePos = (math.cos(angle) * self.anchor.inner_radius, math.sin(angle) * self.anchor.inner_radius)
            tipPosStart = (math.cos(angle + toothTipAngle) * self.anchor.diameter / 2, math.sin(angle + toothTipAngle) * self.anchor.diameter / 2)
            tipPosEnd = (math.cos(angle + toothTipAngle + toothTipArcAngle) * self.anchor.diameter / 2, math.sin(angle + toothTipAngle + toothTipArcAngle) * self.anchor.diameter / 2)
            nextbasePos = (math.cos(angle + dA) * self.anchor.inner_radius, math.sin(angle + dA) * self.anchor.inner_radius)
            endPos = (math.cos(angle + toothBaseAngle) * self.anchor.inner_radius, math.sin(angle + toothBaseAngle) * self.anchor.inner_radius)

            # wheel = wheel.lineTo(tipPosStart[0], tipPosStart[1]).lineTo(tipPosEnd[0], tipPosEnd[1]).lineTo(endPos[0], endPos[1]).radiusArc(nextbasePos, self.anchor.inner_diameter)
            vertices = [basePos, tipPosStart, tipPosEnd, endPos]

            vertices_scaled = [(v[0]/1000, v[1]/1000) for v in vertices]

            body.CreatePolygonFixture(vertices=vertices_scaled, density=self.density, friction=self.friction)
            # body.CreateCircleFixture(radius=0.03, density=self.density, friction=self.friction, pos=vertices_scaled[0])






