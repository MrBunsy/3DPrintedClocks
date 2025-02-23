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

dial = Dial(210, DialStyle.ARABIC_NUMBERS, font=CustomFont(FancyFrenchArabicNumbers),
            outer_edge_style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, inner_edge_style=None, dial_width=40)

# dial = Dial(180, DialStyle.LINES_INDUSTRIAL, raised_detail=False)
dial_diameter=205
# dial = Dial(dial_diameter, DialStyle.ROMAN_NUMERALS, romain_numerals_style=RomanNumeralStyle.SIMPLE_ROUNDED, dial_width=dial_diameter/6,
#             outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, seconds_style=DialStyle.LINES_RECT)

# dial = Dial(dial_diameter, DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
#                   outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_diameter/6, seconds_style=DialStyle.LINES_MAJOR_ONLY,
#                   bottom_fixing=False, top_fixing=False)


dial.configure_dimensions(support_length=10, support_d=21.7)#, second_hand_relative_pos=(0,-40))
# dial = Dial(200, DialStyle.ARABIC_NUMBERS, font="Miriam CLM", outer_edge_style=DialStyle.RING, inner_edge_style=DialStyle.DOTS)
# dial = Dial(200, DialStyle.ROMAN_NUMERALS, font="Times New Roman", outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None)
# dial = Dial(200, DialStyle.ROMAN_NUMERALS, font=None, outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, inner_edge_style=DialStyle.RING)

dial.override_fixing_positions([[polar(math.pi/4 + i*math.pi/2,dial.outside_d/2-dial.dial_width/2)] for i in range(4)])

# show_object(dial.get_dial().rotate((0, 0, 0), (0, 1, 0), 180), options={"color": "white"})
# show_object(dial.get_main_dial_detail().rotate((0, 0, 0), (0, 1, 0), 180), options={"color": Colour.BRASS})
# seconds_detail = dial.get_seconds_dial_detail()
show_object(dial.get_dial(), options={"color": "white"}, name="Dial")
show_object(dial.get_all_detail(), options={"color": Colour.BLACK}, name="Detail")
# if seconds_detail is not None:
#     show_object(seconds_detail.rotate((0, 0, 0), (0, 1, 0), 180), options={"color": Colour.BRASS})

show_object(dial.get_supports(), options={"color": Colour.BRASS}, name="Support")

motionWorks = MotionWorks(compensate_loose_arbour=True, compact=True, bearing=get_bearing_info(3))
