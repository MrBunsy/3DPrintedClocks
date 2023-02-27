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


    def sanitise_options(self, options):
        clean_options = {}
        # sanitise input
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

        if "width" in options:
            clean_options["width"] = int(options["width"][0])
            if clean_options["width"] < 100:
                clean_options["width"] = 100
            if clean_options["width"] > 2000:
                clean_options["width"] = 2000

        return clean_options

    def svg_dial(self, clean_options):



        dial = DialWithHands(style=clean_options["dial_style"],
                             hand_style=clean_options["hand_style"],
                             hand_has_outline=clean_options["hand_has_outline"],
                             centred_second_hand=clean_options["centred_second_hand"]
                             )

        cache_file = os.path.join("autoclock", dial.name + ".svg")
        svg_binary = None
        if os.path.exists(cache_file):
            print("{} exists in cache".format(cache_file))
            with open(cache_file, "rb") as file:
                svg_binary = file.read()
        else:
            print("Generating SVG")
            svg_binary = dial.output_svg("autoclock").encode()
        self.wfile.write(svg_binary)
        print("Finished get request")

    def svg_clock(self, clean_options):

        # for option in options:
        #     #each item in options is a list, we just want a single value
        #     clean_options[option] = options[option][0]
        # print(clean_options)

        

        clock = AutoWallClock(dial_style=clean_options["dial_style"],
                              dial_seconds_style=clean_options["dial_seconds_style"],
                              has_dial=clean_options["has_dial"],
                              gear_style=clean_options["gear_style"],
                              hand_style=clean_options["hand_style"],
                              hand_has_outline=clean_options["hand_has_outline"],
                              pendulum_period_s=clean_options["pendulum_period_s"],
                              escapement_style=clean_options["escapement_style"],
                              days=clean_options["days"],
                              centred_second_hand=clean_options["centred_second_hand"])

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

    def do_GET(self):
        '''
        THIS IS NOT (very) SAFE
        '''
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.end_headers()
        print("Get request: {}".format(self.path) )
        parsed_path = urllib.parse.urlparse(self.path)
        path_list = os.path.split(parsed_path.path)
        print("path_list", path_list)

        if len(path_list) > 0:
            #processed path never has / at end

            if path_list[0].startswith("/generate_clock"):
                print("Request for SVG generation")

                options = urllib.parse.parse_qs(parsed_path.query)
                print(options)
                clean_options = self.sanitise_options(options)

                default_options = {
                    "pendulum_period_s": 2,
                    "has_dial": True,
                    "dial_style": DialStyle.LINES_ARC,
                    "dial_seconds_style": DialStyle.CONCENTRIC_CIRCLES,
                    "gear_style": GearStyle.CURVES,
                    "hand_style": HandStyle.SIMPLE_ROUND,
                    "hand_has_outline": True,
                    "escapement_style": AnchorStyle.CURVED_MATCHING_WHEEL,
                    "days": 8,
                    "centred_second_hand": True,
                    "width": 300,
                }

                default_options.update(clean_options)
                print(default_options)
                
                
                if len(path_list) == 1 or path_list[1].endswith("clock") or len(path_list[1]) == 0:
                    print("Request for autoclock")
                    self.svg_clock(default_options)
                elif path_list[1].endswith("dial"):
                    print("Request for dial")
                    self.svg_dial(default_options)



httpd = HTTPServer(('0.0.0.0', 8000), AutoclockHTTPHandler)



httpd.serve_forever()