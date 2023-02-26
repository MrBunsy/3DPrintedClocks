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
                for option in options:
                    #each item in options is a list, we just want a single value
                    clean_options[option] = options[option][0]
                print(clean_options)

                default_options={
                    "pendulum_period_s":2,
                    "has_dial":True,
                    "dial_style":DialStyle.LINES_ARC.value,
                    "dial_seconds_style":DialStyle.CONCENTRIC_CIRCLES.value,
                    "gear_style": GearStyle.CURVES.value,
                    "hand_style": HandStyle.SIMPLE_ROUND.value,
                    "hand_has_outline":True,
                    "escapement_style": AnchorStyle.CURVED_MATCHING_WHEEL.value,
                    "days": 8,
                    "centred_second_hand":True,
                }

                default_options.update(clean_options)
                print(default_options)

                clock = AutoWallClock(dial_style=DialStyle(default_options["dial_style"]),
                                      dial_seconds_style=DialStyle(default_options["dial_seconds_style"]),
                                      has_dial=bool(default_options["has_dial"]),
                                      gear_style=GearStyle(default_options["gear_style"]),
                                      hand_style=HandStyle(default_options["hand_style"]),
                                      hand_has_outline=bool(default_options["hand_has_outline"]),
                                      pendulum_period_s=int(default_options["pendulum_period_s"]),
                                      escapement_style=AnchorStyle(default_options["escapement_style"]),
                                      days=int(default_options["days"]),
                                      centred_second_hand=bool(default_options["centred_second_hand"]))
                print("Generating SVG")
                self.wfile.write(clock.get_svg_text().encode())
                print("Finished get request")



httpd = HTTPServer(('0.0.0.0', 8000), AutoclockHTTPHandler)



httpd.serve_forever()