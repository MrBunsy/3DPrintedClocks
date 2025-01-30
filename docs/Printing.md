# Printing Parts
An FDM printer is assumed. I have not tried resin printing, I suspect it would not be strong enough. I use a Prusa Mk3s and Mk4. PETG doesn't always print especially well on a mini (bowden extruder) but I expect any well calibrated machine to be suitable.

Most parts are best printed in PETG as it's strong and doesn't warp easily. Some decorative parts (hands, dial) could probably be printed in PLA without any issue, but I have used PETG so I can print them on a textured sheet.

I've experimented printing in ASA for strength but this seems to wear badly so I've stuck with PETG, even for spring driven clocks.

I have Prusa printers and use PrusaSlicer, so these instructions assume that. I think these principles should apply to most slicers and printers, but you may need to do some investigation to find the exact names of settings in other slicers.

# Wheels (gears)
The wheels and pinions are by far the hardest part to print. If you want to print a clock I recommend starting with an arbor to check your printer is up to the task.

You need to be able to print PETG with minimal stringing. I've discovered lower temperatures and decent filament to be the best way to reduce stringing from the printer, and carefully slicing to avoid too many stops and starts to reduce stringing from the gcode.

Only printing one object at once also helps reduce stringing and blobbing. "Complete Individual Objects" works very well for printing multiple parts of an arbor at the same time.

## Slicing Tips
The teeth of both the wheels (big gears) and leaves of pinions (teeth of the small gears) need to be printed in continuous perimeter. If there are small bits filling gaps, this is very lightly to produce stringing. 
![Clock 07 Photo](../images/slicing-to-avoid-small-bits-in-the-teeth.webp "Slicing Pinions")

Most gears should print fine simply by disabling Gap Fill in Prusaslicer, however a few can still require some tweaking, usually the pinions. Each pinion has a corresponding "pinion_STL_modifier" file which can be imported to change slicing settings for just one section of the model. In Prusaslicer this is by right clicking on a shape, Add Modifier -> Load. Then you want to set the infil to 0, the top and bottom layers to 0 and the perimeter to 1. This will result in a hollow pinion with just the inner and outer perimeter. Alternatively you can tweak the perimeter and external perimeter width ever so slightly.

# Multicolour

TODO find the original blog I sourced this from.

It is possible to configure PrusaSlicer for simple multicolour prints without an MMU or AMS. I assume this works similarly with other slicers. It works best for prints with colour changes only in the first two layers - otherwise you have to babysit your printer for a long time.

Configure your printer so it has multiple extruders, then set custom g-code for tool change:
```
{if layer_num >= 0}G1 E-4 F2400 ; Retraction
{if max_layer_z < max_print_height}G1 Z{z_offset+min(max_layer_z+1, max_print_height)} F720 ; Move print head up{endif}
G1 X211 Y0 F3600 ; Parking position
M600
{endif}
```
This will:
 - Only perform the tool change if we've started printing (removing an unnecessary change at the very start).
 - Move the print head up and away from the print before (and thus after) initiating filament change - avoiding a blob on your print
 - Use M600 to initiate a manual filament swap

Note that this does not add in the gcode to provide a countdown timer before the next filament swap, so you will have to estimate this from the slicer yourself.

When printing I recommend using a piece of tissue to clean the nozzle just after a filament has been unloaded. 

Be ready with a pair of tweezers to hold the purged filament after loading the new colour. Don't pull the purged material away until after the print starts again, you want to wait for the last moment as the nozzle lowers itself to continue printing.

I also recommend increasing the z-hop (needs to be done for both extruder and filament to take effect), to avoid any snagging of strings on other parts of the print.