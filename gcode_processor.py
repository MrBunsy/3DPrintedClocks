import sys
import os
import datetime
import shutil
import traceback

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

def apply_dialfix(gcode_in, log, layers_to_fix=2, extruder_to_fix=1):
    '''
    for small objects on the dial, attempt to re-order to reduce total distance travelled (and thus stringing)
    '''

    gcode_out = []

    current_z = 0
    current_z_10 = 0
    layer = -1
    current_tool = -1
    inside_a_shape = False
    current_shape = []
    current_shape_type = None
    last_shape_type = None
    changing_tool = False

    relevant_shapes_in_layer = []

    for i,line in enumerate(gcode_in):
        if line.strip() == ";LAYER_CHANGE":
            current_z = float(gcode_in[i+1].strip().split(":")[1])
            current_z_10 = int(current_z*10)
            log.write("Processing layer {}\n".format(current_z))
            layer+=1
            log.write("previous relevant_shapes_in_layer: {}\n".format(len(relevant_shapes_in_layer)))
            relevant_shapes_in_layer = []
            current_shape_type = None
            last_shape_type = None

        if line.strip() == "M600":
            current_tool = int(gcode_in[i + 1].strip()[1:])
            log.write("Current tool: T{}\n".format(current_tool))
            changing_tool = True

        if line.startswith("; printing object"):
            #assume this means we've dealt with all the toolchange and wipe tower and are back to printing proper
            changing_tool = False

        if layer < layers_to_fix and current_tool == extruder_to_fix and not changing_tool:
            '''
            this is the layer and tool we want to tinker with
            '''
            if line.startswith("G1 Z."):
                #are we raising up or lowering down?
                #TODO last shape in layer doesn't end with raising the nozzle - check for ";stop printing object" ?
                #also TODO seeing 73 unique shapes on a layer - since we've missed the last shape we've seen two too many. how?
                #I think the two bonus shapes are the inside circles in the 9 and 6, so if we fix the last shape everything's accounted for!
                z10 = int(line.strip().split(" ")[1].split(".")[1])
                starting_shape = z10 == current_z_10
                if starting_shape and not inside_a_shape:
                    inside_a_shape = True
                    #keep the previous line which was to move to the start position
                    current_shape = [gcode_in[i-1]]
                if inside_a_shape and not starting_shape:
                    #finished a shape
                    actually_same_shape = False
                    if ((current_shape_type == "Solid infill" and last_shape_type == "External perimeter") or
                            (current_shape_type == "External perimeter" and last_shape_type == "Perimeter") or
                            (current_shape_type == "Solid infill" and last_shape_type == "Solid infill")):
                        #this is actually part of the same shape
                        actually_same_shape = True
                        # log.write("current {}, last {}, assuming same shape line: {}\n".format(current_shape_type, last_shape_type, i))

                    if current_shape_type not in ["External perimeter", "Perimeter", "Solid infill"]:
                        #"Skirt/Brim" or something else entirely, ignore
                        continue

                    # if not actually_same_shape:
                    inside_a_shape = False
                    current_shape.append(line)
                    if actually_same_shape:
                        if len(relevant_shapes_in_layer) == 0:
                            log.write("somehow actually_same_shape but there is no previous shape. current_shape_type= {} last_shape_type = {}\n".format(current_shape_type,last_shape_type))
                            continue
                        relevant_shapes_in_layer[-1].extend(current_shape)
                    else:
                        relevant_shapes_in_layer.append(current_shape)
                    # log.write("finished processing shape type {} line: {}\n".format(current_shape_type, i))
                    last_shape_type = current_shape_type

            if line.startswith("; stop printing object"):
                current_shape.append(line)
                relevant_shapes_in_layer.append(current_shape)
                log.write("finished processing shape LAST IN LAYER type {} line: {}\n".format(current_shape_type, i))
            if inside_a_shape:
                current_shape.append(line)
                if line.startswith(";TYPE:"):
                    # last_shape_type = current_shape_type
                    current_shape_type = line.strip().split(":")[1]

    return gcode_in

if __name__ == "__main__":

    '''
    expects arguments: prusaslicer_version [optional] gcode/file/path
    
    optional:
    - firstm600
    - dialfix
    - wipefix
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

    prusaslicer_version = sys.argv[1]
    relevant_args = sys.argv[2:-1]

    remove_first_m600 = "firstm600" in relevant_args
    need_dialfix = "dialfix" in relevant_args
    need_wipefix = "wipefix" in relevant_args

    #file prusaslicer expects to be edited in situ
    gcode_temp_file = sys.argv[-1]

    gcode_in = []


    found_first_m600 = False

    shutil.copyfile(gcode_temp_file, backup)

    with open(gcode_temp_file, 'r') as input_file:
        for line in input_file:
            gcode_in.append(line)

    print(gcode_in)

    gcode_out = []
    with open(logfile, "a+") as log:
        try:
            log.write("\n=======Post processing {} on {}===========\n".format(gcode_temp_file, datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
            log.write("remove_first_m600: {}, rearrange_dial_bits:{}, need_wipefix:{}\n".format(remove_first_m600, need_dialfix, need_wipefix))
            line_number = 1
            for line in gcode_in:
                keepline = True
                if "M600" in line and remove_first_m600 and not found_first_m600:
                    keepline = False
                    found_first_m600 = True
                    log.write("removed first M600 from line {}\n".format(line_number))

                if keepline:
                    gcode_out.append(line)

                line_number+=1

            if need_wipefix:
                gcode_out = apply_wipefix(gcode_out, log)
            if need_dialfix:
                gcode_out = apply_dialfix(gcode_out, log)
        except Exception as error:
            log.write("Exception: {}\n{}".format(error, traceback.format_exc()))

    with open(gcode_temp_file, 'w') as out_file:
        out_file.writelines(gcode_out)