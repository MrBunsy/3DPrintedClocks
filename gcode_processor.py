import sys
import os

if __name__ == "__main__":

    '''
    expects arguments: prusaslicer_version [optional] gcode/file/path
    
    optional:
    - firstm600
    - dialfix
    - wipefix
    '''

    #multicolour print will start with the right colour loaded manually, don't need the initial tool change
    remove_first_m600 = False
    #can I re-order the dial detail so it doesn't string so horrendously?
    rearrange_dial_bits = False
    #prusaslicer > 2.5 changes tool before moving to the wipe tower, leaving unsightly blobs
    reorder_nozzle_change = False

    if len(sys.argv) < 3:
        raise ValueError("Need more arguments - prusaslicer versaion and the path to the gcode file")

    prusaslicer_version = sys.argv[1]
    relevant_args = sys.argv[2:-1]

    remove_first_m600 = "firstm600" in relevant_args
    rearrange_dial_bits = "dialfix" in relevant_args
    reorder_nozzle_change = "wipefix" in relevant_args

    #file prusaslicer expects to be edited in situ
    gcode_temp_file = sys.argv[-1]

    gcode_in = []


    found_first_m600 = False

    with open(gcode_temp_file, 'r') as input_file:
        for line in input_file:
            gcode_in.append(line)

    print(gcode_in)

    gcode_out = []

    for line in gcode_in:
        keepline = True
        if "M600" in line and remove_first_m600 and not found_first_m600:
            keepline = False
            found_first_m600 = True

        if keepline:
            gcode_out.append(line)

    with open(gcode_temp_file, 'w') as out_file:
        out_file.writelines(gcode_out)