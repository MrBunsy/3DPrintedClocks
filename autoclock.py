from clocks.autoclock import *
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass
'''
Plan is two scripts (or arguments?) - generate cache and typescript, and run the server
'''

# gen_gear_previews()
# gen_anchor_previews()
# gen_hand_previews()
#
# #clock = AutoWallClock(centred_second_hand=True, dial_style=DialStyle.LINES_ARC, has_dial=True, gear_style=GearStyle.CURVES)
# clock = AutoWallClock(dial_style=DialStyle.ROMAN, dial_seconds_style=DialStyle.LINES_ARC, has_dial=True, gear_style=GearStyle.ARCS, hand_style=HandStyle.BAROQUE, hand_has_outline=False,
#                       pendulum_period_s=1.25)
# if outputSTL:
#     clock.output_svg("autoclock")
# else:
#     show_object(clock.model.getClock(with_pendulum=True))


# print(enum_to_typescript(GearStyle))
if outputSTL:
    gen_typescript_enums("autoclock/web/autoclock-app/src/app/models/types.ts")
    gen_gear_previews("autoclock/web/autoclock-app/src/assets")
    gen_anchor_previews("autoclock/web/autoclock-app/src/assets")
    gen_hand_previews("autoclock/web/autoclock-app/src/assets")
    gen_dial_previews("autoclock/web/autoclock-app/src/assets")
    #5.5 days approx to run this, maybe not
    # gen_clock_previews("autoclock/web/autoclock-app/src/assets")