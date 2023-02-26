import os.path

from clocks.autoclock import *
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# #clock = AutoWallClock(centred_second_hand=True, dial_style=DialStyle.LINES_ARC, has_dial=True, gear_style=GearStyle.CURVES)
# clock = AutoWallClock(dial_style=DialStyle.ROMAN, dial_seconds_style=DialStyle.LINES_ARC, has_dial=True, gear_style=GearStyle.ARCS, hand_style=HandStyle.BAROQUE, hand_has_outline=False,
#                       pendulum_period_s=1.25)
# if outputSTL:
#     clock.output_svg("autoclock")
# else:
#     show_object(clock.model.getClock(with_pendulum=True))


class AutoclockHTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        '''
        THIS IS NOT SAFE
        '''
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.end_headers()
        print("Get request: {}".format(self.path) )

        if self.path.startswith("/generate_clock"):
            print("Request for a clock")
            if len(self.path)  > 2:
                options = urllib.parse.parse_qs(self.path[2:])
                clean_options={}
                # for option in options:
                #     #each item in options is a list, we just want a single value
                #     clean_options[option] = options[option][0]
                # print(clean_options)

                default_options={
                    "pendulum_period_s":2,
                    "has_dial":True,
                    "dial_style":DialStyle.LINES_ARC,
                    "dial_seconds_style":DialStyle.CONCENTRIC_CIRCLES,
                    "gear_style": GearStyle.CURVES,
                    "hand_style": HandStyle.SIMPLE_ROUND,
                    "hand_has_outline":True,
                    "escapement_style": AnchorStyle.CURVED_MATCHING_WHEEL,
                    "days": 8,
                    "centred_second_hand":True,
                }
                #sanitise input
                if "pendulum_period_s" in options:
                    clean_options["pendulum_period_s"] = int(options["pendulum_period_s"][0])
                if "has_dial" in options:
                    clean_options["has_dial"] = options["has_dial"][0].lower() == "true"
                if "dial_style" in options:
                    try:
                        clean_options["dial_style"] = DialStyle(options["dial_style"][0])
                    except:
                        print("dial style not recognised")
                if "dial_seconds_style" in options:
                    try:
                        clean_options["dial_seconds_style"] = DialStyle(options["dial_seconds_style"][0])
                    except:
                        print("dial seconds style not recognised")

                if "gear_style" in options:
                    gear_string = options["gear_style"][0]
                    if gear_string == "None":
                        gear_string = None
                    try:
                        clean_options["gear_style"] = GearStyle(gear_string)
                    except:
                        print("gear style not recognised")

                if "hand_style" in options:
                    try:
                        clean_options["hand_style"] = HandStyle(options["hand_style"][0])
                    except:
                        print("hand style not recognised")

                if "hand_has_outline" in options:
                    clean_options["hand_has_outline"] = options["hand_has_outline"][0].lower() == "true"

                if "escapement_style" in options:
                    try:
                        clean_options["escapement_style"] = AnchorStyle(options["escapement_style"][0])
                    except:
                        print("escapement style not recognised")

                if "days" in options:
                    clean_options["days"] = int(options["days"][0])

                if "centred_second_hand" in options:
                    clean_options["centred_second_hand"] = options["centred_second_hand"][0].lower() == "true"

                default_options.update(clean_options)
                print(default_options)

                clock = AutoWallClock(dial_style=default_options["dial_style"],
                                      dial_seconds_style=default_options["dial_seconds_style"],
                                      has_dial=default_options["has_dial"],
                                      gear_style=default_options["gear_style"],
                                      hand_style=default_options["hand_style"],
                                      hand_has_outline=default_options["hand_has_outline"],
                                      pendulum_period_s=default_options["pendulum_period_s"],
                                      escapement_style=default_options["escapement_style"],
                                      days=default_options["days"],
                                      centred_second_hand=default_options["centred_second_hand"])

                cache_file = os.path.join("autoclock", clock.name + ".svg")
                svg_binary = None
                if os.path.exists(cache_file):
                    print("{} exists in cache".format(cache_file))
                    with open(cache_file, "rb") as file:
                        svg_binary = file.read()
                else:
                    print("Generating SVG")
                    svg_binary = clock.output_svg("autoclock").encode()
                self.wfile.write(svg_binary)
                print("Finished get request")



httpd = HTTPServer(('0.0.0.0', 8000), AutoclockHTTPHandler)



httpd.serve_forever()