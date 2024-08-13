from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass



# dial = Dial(200, DialStyle.ROMAN_NUMERALS, font="Comic Sans MS", outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, inner_edge_style=DialStyle.RING)
# these three look good:
# Arial looks neat, mono looks typewritten! Miriam CLM possibly better than Arial
# dial = Dial(155, DialStyle.ARABIC_NUMBERS, font="Miriam Mono CLM", inner_edge_style=None, outer_edge_style=DialStyle.DOTS)
# dial = Dial(180, DialStyle.ARABIC_NUMBERS, font="Gill Sans Medium", font_scale=0.8, font_path="../fonts/GillSans/Gill Sans Medium.otf", outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, inner_edge_style=None)
# dial = Dial(155, DialStyle.ARABIC_NUMBERS, font="Wingding", font_scale=0.8, font_path="C:\\WINDOWS\\FONTS\\WINGDING.TFF", inner_edge_style=DialStyle.LINES_ARC, outer_edge_style=None)

dial = Dial(180, DialStyle.LINES_INDUSTRIAL)


dial.configure_dimensions(support_length=10, support_d=21.7)
# dial = Dial(200, DialStyle.ARABIC_NUMBERS, font="Miriam CLM", outer_edge_style=DialStyle.RING, inner_edge_style=DialStyle.DOTS)
# dial = Dial(200, DialStyle.ROMAN_NUMERALS, font="Times New Roman", outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None)
# dial = Dial(200, DialStyle.ROMAN_NUMERALS, font=None, outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, inner_edge_style=DialStyle.RING)

show_object(dial.get_dial().rotate((0, 0, 0), (0, 1, 0), 180), options={"color": "white"})
show_object(dial.get_main_dial_detail().rotate((0, 0, 0), (0, 1, 0), 180), options={"color": Colour.BRASS})

motionWorks = MotionWorks(compensate_loose_arbour=True, compact=True, bearing=get_bearing_info(3))
