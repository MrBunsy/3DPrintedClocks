import math

import sys
import os
import datetime
import shutil
import traceback

# from clocks import radToDeg

def radToDeg(rad):
    return rad * 180 / math.pi

def apply_wipefix(gcode_in, log):
    '''
    Find toolchanges:

;--------------------
; CP TOOLCHANGE START
; toolchange #1
; material : PETG -> PETG
;--------------------

    and make sure that the nozzle has moved to the wipe tower before M600 is called


    need to move:
M600
T1
M900 K0.08 ; Filament gcode LA 1.5
M900 K45 ; Filament gcode LA 1.0


latest idea - copy the first G1 line to before M600

    '''
    gcode_out = []

    toolchanges_left = True

    #{index: {"start", "m600", "end"}}
    toolchanges = {}
    max_tool_change = -1

    for i, line in enumerate(gcode_in):
        if line.strip() =="; CP TOOLCHANGE START" and "; toolchange #" in gcode_in[i + 1]:
            toolchange_id_line = gcode_in[i + 1].strip()
            toolchange_id = int(toolchange_id_line.split("#")[1])
            if toolchange_id > max_tool_change:
                max_tool_change = toolchange_id
            # log.write("Found toolchange #{} at line {}\n".format(toolchange_id,i))

            start_line = i-1
            end_line = -1
            m600_line = -1
            first_g_after_m600 = "notfound"
            for j, line2 in enumerate(gcode_in[i:]):
                if line2.strip() == "M600":
                    m600_line = j + i
                if m600_line > 0 and line2.startswith("G1") and first_g_after_m600 == "notfound":
                    first_g_after_m600 = line2
                if line2.strip() == "; CP TOOLCHANGE END":
                    end_line = j+1 + i
                    break

            toolchanges[toolchange_id] = {"start":start_line, "m600":m600_line, "end":end_line, "gline": first_g_after_m600}
    #log.write("{}\n".format(toolchanges))

    for toolchange_id in toolchanges:
        log.write("processing toolchange {}\n".format(toolchanges[toolchange_id]))
        start_line = 0
        if toolchange_id > 1:
            start_line = toolchanges[toolchange_id-1]["end"]
        #copy everything up to the start of the tool change
        gcode_out.extend(gcode_in[start_line:toolchanges[toolchange_id]["m600"]])
        #duplicate the first G1 command that would come after M600
        gcode_out.append(toolchanges[toolchange_id]["gline"])
        #copy up to the end of the tool change
        gcode_out.extend(gcode_in[toolchanges[toolchange_id]["m600"]: toolchanges[toolchange_id]["end"]])

        if toolchange_id == max_tool_change:
            #copy the rest
            gcode_out.extend(gcode_in[toolchanges[toolchange_id]["end"]:])




    return gcode_out

def get_position(line):
    '''
    returns None if no position in line of gcode
    '''

    if line.startswith("G1") and "X" in line and "Y" in line and "E" in line:
        # do we need to care if we're extruding?
        parts = line.strip().split(" ")
        x = 0
        y = 0
        for part in parts:
            if part.startswith("X"):
                x += float(part[1:])
            if part.startswith("Y"):
                y += float(part[1:])

        return (x,y)
    return None

def get_average_position(gcode):

    x=0
    y=0
    found=0

    for line in gcode:
        pos = get_position(line)
        if pos is not None:
            x += pos[0]
            y += pos[1]
            found += 1
        # if line.startswith("G1") and "X" in line and "Y" in line and "E" in line:
        #     #do we need to care if we're extruding?
        #     parts = line.strip().split(" ")
        #     for part in parts:
        #         if part.startswith("X"):
        #             x += float(part[1:])
        #         if part.startswith("Y"):
        #             y += float(part[1:])
        #     found +=1
    return (x/found, y/found)

def get_shape_type(gcode):
    '''
    get the type of part being printed - should only see Perimeter, External perimeter and Solid infill
    '''
    current_shape_type = None
    for line in gcode:
        if line.startswith(";TYPE:"):
            # last_shape_type = current_shape_type
            current_shape_type = line.strip().split(":")[1]

    return current_shape_type

def re_arrange_shapes(shapes, log, start_pos = None):
    '''
    give a list of lists of gcode, re-order the first list to reduce travelling

    could do this with a general purpose proper minimum-distance-travelled algorithm
    or i could cheat and use the fact I know it's a dial to simply use polar coordinates to ensure we print everything anticlockwise

    '''

    if start_pos is None:
        start_pos = (-1,0)

    shapes_processed = []

    all_shape_gcode = []
    for shape_gcode in shapes:
        all_shape_gcode.extend(shape_gcode)
    #assume this is the centre of the dial
    centre = get_average_position(all_shape_gcode)

    log.write("Assuming centre of dial is: {}\n".format(centre))

    #we want to start the dial shapes with as little travel as possible, find the angle of the last known position of the nozzle
    start_angle = math.atan2(start_pos[1] - centre[1], start_pos[0] - centre[0])
    log.write("assuming attempting to start at angle {:.1f}deg\n".format(radToDeg(start_angle)))
    for shape_gcode in shapes:

        shape_centre = get_average_position(shape_gcode)
        diff = (shape_centre[0] - centre[0], shape_centre[1] - centre[1])
        angle = math.atan2(diff[1], diff[0])
        #want the most -ve angle to be the one nearest the start angle so the sort will put that first


        type = get_shape_type(shape_gcode)
        if type == "External perimeter":
            #ever so slightly prioritise so we don't do the infil of numbers with inner circles before the outline
            angle-=1*2*math.pi/360

        if angle < start_angle:
            angle += math.pi*2

        # if angle < 0:
        #     angle += math.pi*2

        shape_info = {"gcode":shape_gcode, "angle":angle, "type": type}
        shapes_processed.append(shape_info)


    shapes_processed.sort(key=lambda x: x["angle"])

    gcode_out = []
    for shape_info in shapes_processed:
        gcode_out.extend(shape_info["gcode"])
        log.write("adding shape with angle: {:.2f}={:.1f}deg, {}\n".format(shape_info["angle"], radToDeg(shape_info["angle"]), shape_info['type']))

    return gcode_out

def apply_dialfix(gcode_in, log, printer_version=None, layers_to_fix=2, extruder_to_fix=1, detail_printed_first=False):
    '''
    for small objects on the dial, attempt to re-order to reduce total distance travelled (and thus stringing)
    '''

    gcode_out = []

    current_z = 0
    # current_z_100 = 0
    layer = -1
    current_tool = -1
    inside_a_shape = False
    current_shape = []
    current_shape_type = None
    last_shape_type = None
    changing_tool = False

    if detail_printed_first:
        #bodgetastic time
        current_tool = extruder_to_fix

    last_known_pos = None

    relevant_shape_types = ["External perimeter", "Perimeter", "Solid infill"]

    relevant_shapes_in_layer = []

    for i,line in enumerate(gcode_in):
        if line.strip() == ";LAYER_CHANGE":
            current_z = float(gcode_in[i+1].strip().split(":")[1])
            # current_z_100 = int(current_z*100)
            # log.write("Processing layer {}\n".format(current_z))
            layer+=1
            # log.write("previous relevant_shapes_in_layer: {}\n".format(len(relevant_shapes_in_layer)))
            # log.write("extending gcode out starting at line {}\n".format(len(gcode_out)))
            # gcode_out.extend(re_arrange_shapes(relevant_shapes_in_layer))
            relevant_shapes_in_layer = []
            current_shape_type = None
            last_shape_type = None

        if line.strip() == "M600":
            if gcode_in[i+1].startswith("T"):
                current_tool = int(gcode_in[i + 1].strip()[1:])
                log.write("Start changing to tool: T{} line {}\n".format(current_tool, i))
                changing_tool = True
            #if it doesn't say T[int] then it's probably a manual layer filament change

        if line.startswith("; printing object") and changing_tool:
            #assume this means we've dealt with all the toolchange and wipe tower and are back to printing proper
            #THIS DOESN'T HAPPEN with prusaslicer 2.7.2 targetting the mk4
            changing_tool = False
            log.write("Finished changing to tool: T{} line {}\n".format(current_tool, i))

        if printer_version == "MK4" and line.startswith(";TYPE:") and changing_tool:
            #we don't seem to get the nice "printing object [blah]" for the mk4 :(
            #so instead stop when we see we're printing something proper
            current_shape_type = line.strip().split(":")[1]
            if current_shape_type in relevant_shape_types:
                log.write("Finished changing to tool: T{} line {}\n".format(current_tool, i))
                changing_tool = False

        if layer < layers_to_fix and current_tool == extruder_to_fix and not changing_tool:
            '''
            this is the layer and tool we want to tinker with
            
            
            on the mk3 we raise after an object and lower just before printing with G1 Z.
            on the mk4 we raise as part of a move after the last object, so the line won't start G1 Z.
            it will be a standard move with a Z as well like:
            
            G1 X203.226 Y79.155 Z.359 F18000 <- finish last object
            G1 Z.2 F720 <- lower to start next
            
            '''
            if line.startswith("G1") and " Z." in line:
                #are we raising up or lowering down?
                #TODO last shape in layer doesn't end with raising the nozzle - check for ";stop printing object" ?
                #also TODO seeing 73 unique shapes on a layer - since we've missed the last shape we've seen two too many. how?
                #I think the two bonus shapes are the inside circles in the 9 and 6, so if we fix the last shape everything's accounted for!
                #eg G1 Z.45 F720
                #want the "0.45" bit THIS DOESN'T WORK ON THE MK4, which doesn't appear to raise and lower the head for printing
                #z = float(line.strip().split(" ")[1][1:])
                axes = line.split(" ")
                for axis in axes:
                    if axis.startswith("Z."):
                        z = float(axis[1:])

                starting_shape = abs(z - current_z) < 0.01
                if starting_shape and not inside_a_shape:
                    inside_a_shape = True
                    #keep the previous line which was to move to the start position
                    current_shape = [gcode_in[i-1]]
                    #scratch previous line from gcode
                    gcode_out = gcode_out[:-1]
                if inside_a_shape and not starting_shape:
                    #finished a shape
                    actually_same_shape = False
                    inside_a_shape = False
                    current_shape.append(line)
                    if ((current_shape_type == "Solid infill" and last_shape_type == "External perimeter") or
                            (current_shape_type == "External perimeter" and last_shape_type == "Perimeter") or
                            (current_shape_type == "Solid infill" and last_shape_type == "Solid infill")):
                        #this is actually part of the same shape
                        actually_same_shape = True
                        # log.write("current {}, last {}, assuming same shape line: {}\n".format(current_shape_type, last_shape_type, i))

                    if current_shape_type not in relevant_shape_types:
                        #"Skirt/Brim" or something else entirely, sent directly to gcode_out without re-arranging
                        gcode_out.extend(current_shape)
                        log.write("current shape not being processed: {} line in {} line out {} \n{}\n\n".format(current_shape_type, i,len(gcode_out), current_shape))
                        continue

                    if actually_same_shape:
                        if len(relevant_shapes_in_layer) == 0:
                            log.write("somehow actually_same_shape but there is no previous shape. current_shape_type= {} last_shape_type = {}\n".format(current_shape_type,last_shape_type))
                            continue
                        relevant_shapes_in_layer[-1].extend(current_shape)
                    else:
                        relevant_shapes_in_layer.append(current_shape)
                    log.write("finished processing shape type {} line: {}\n".format(current_shape_type, i))
                    last_shape_type = current_shape_type
                    #don't add this line to gcode out
                    continue

            if line.startswith("; stop printing object"):
                current_shape.append(line)
                relevant_shapes_in_layer.append(current_shape)
                inside_a_shape = False
                log.write("finished processing shape LAST IN LAYER type {} line: {}\n".format(current_shape_type, i))

                log.write("previous relevant_shapes_in_layer: {}\n".format(len(relevant_shapes_in_layer)))
                log.write("extending gcode out starting at line {}\n".format(len(gcode_out)))
                if len(relevant_shapes_in_layer) > 1:
                    gcode_out.extend(re_arrange_shapes(relevant_shapes_in_layer, log, last_known_pos))
                else:
                    print("insufficient relevant_shapes_in_layer, only found: {}".format(len(relevant_shapes_in_layer)))
                relevant_shapes_in_layer = []
                current_shape_type = None
                last_shape_type = None




            if inside_a_shape:
                current_shape.append(line)
                if line.startswith(";TYPE:"):
                    # last_shape_type = current_shape_type
                    current_shape_type = line.strip().split(":")[1]
            else:
                gcode_out.append(line)
                pos = get_position(line)
                if pos is not None:
                    last_known_pos = pos

        else:
            gcode_out.append(line)

    return gcode_out

if __name__ == "__main__":

    '''
    expects arguments: prusaslicer_version [optional] gcode/file/path
    
    optional:
    - firstm600 - remove the first M600 so we don't change filament immediately before the print
    - dialfix - re-arrange the dial detail elements so there's less travel
    - wipefix - re-arrange so the nozzle moves to the wipe tower BEFORE M600
    - detailfirst - the dial is printed with the detail first (default is detail second)
    
    
    C:/Python311_2023/python.exe C:/Users/Luke/Documents/Clocks/3DPrintedClocks/gcode_processor.py 2.7.2 firstm600 wipefix
    '''

    logfile = "C:/Users/Luke/Documents/Clocks/3DPrintedClocks/postprocesslog.txt"
    backup = "C:/Users/Luke/Documents/Clocks/3DPrintedClocks/postprocessbackup.gcode"

    #multicolour print will start with the right colour loaded manually, don't need the initial tool change
    remove_first_m600 = False
    #can I re-order the dial detail so it doesn't string so horrendously?
    need_dialfix = False
    #prusaslicer > 2.5 changes tool before moving to the wipe tower, leaving unsightly blobs
    need_wipefix = False

    if len(sys.argv) < 3:
        raise ValueError("Need more arguments - prusaslicer versaion and the path to the gcode file")

    #haven't ended up actually using this...
    prusaslicer_version = sys.argv[1].upper()
    relevant_args = sys.argv[2:-1]

    remove_first_m600 = "firstm600" in relevant_args
    need_dialfix = "dialfix" in relevant_args
    need_wipefix = "wipefix" in relevant_args
    detail_printed_first = "detailfirst" in relevant_args

    #file prusaslicer expects to be edited in situ
    gcode_temp_file = sys.argv[-1]

    gcode_in = []


    found_first_m600 = False

    shutil.copyfile(gcode_temp_file, backup)

    with open(gcode_temp_file, 'r') as input_file:
        for line in input_file:
            gcode_in.append(line)

    print(gcode_in)

    printer_version = None

    gcode_out = []
    with open(logfile, "a+") as log:
        try:
            log.write("\n=======Post processing {} on {}===========\n".format(gcode_temp_file, datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
            log.write("remove_first_m600: {}, rearrange_dial_bits:{}, need_wipefix:{} Prusaslicer {}\n".format(remove_first_m600, need_dialfix, need_wipefix, prusaslicer_version))
            line_number = 1
            for line in gcode_in:
                keepline = True
                if "M600" in line and remove_first_m600 and not found_first_m600:
                    keepline = False
                    found_first_m600 = True
                    log.write("removed first M600 from line {}\n".format(line_number))
                if line.startswith("M862.3 P ") and printer_version is None:
                    printer_version = line.split("\"")[1]
                    log.write("Found printer: {}\n".format(printer_version))

                if keepline:
                    gcode_out.append(line)
                line_number+=1

            if need_wipefix:
                gcode_out = apply_wipefix(gcode_out, log)
            if need_dialfix:
                gcode_out = apply_dialfix(gcode_out, log, printer_version, detail_printed_first=detail_printed_first)
        except Exception as error:
            log.write("Exception: {}\n{}".format(error, traceback.format_exc()))

    with open(gcode_temp_file, 'w') as out_file:
        out_file.writelines(gcode_out)