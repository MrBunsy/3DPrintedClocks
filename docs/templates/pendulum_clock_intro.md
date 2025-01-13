# $title
This is $duration pendulum clock, so it needs winding once a $winding_period. The $weight weight falls $weight_drop to power the clock. With a period of $period the pendulum ticks every $tick_period.

This is an Open Hardware project and is licensed under the CERN-OHL-S v2. This means you're free to do with it what you want: make it, sell it, give it away, but you must provide the source code for the clock with the physical clock under the same terms. For those familiar with software, this is like the GPL, but for hardware.

The project is written in Python and uses CadQuery to generate 3D models. [The source code is available on github](https://github.com/MrBunsy/3DPrintedClocks).

I have printed most of my clocks entirely in PETG and the oldest have been running for three years without issue. However, as an experiment some clocks have been printed in PLA and appear to work fine, but I don't know how well this will hold up long term. Regardless of material used, your printer will need to be well calibrated and able to produce clean strong prints for the gears to work reliably.

## Slicing
It is vital to get the slicing right for the gears, as any extra friction introduced from printing artefacts will severely impact the reliability of the clock. I used seam painting for the gears to ensure that seams do not start on the teeth, springs or pallets of the anchor.

Nearly everything needs to be strong, so I sliced with 3 perimeters, 6 bottom and top layers and 40% gyroid infill. If you have larger nozzles, I would recommend printing the plates and pillars with 0.6mm.

PETG strings really quite a lot. This is exacerbated by any small bits of perimeter that can occur. I had to disable Gap Fill for the gears and then tweak the extrusion width for the pinion on gear 1. See gears.3mf and the slicing screenshots. If I didn't do this then I didn't get a clean surface on the gear teeth, which meant a much heavier weight was required to overcome this friction.

The STL files are almost all in the correct orientation for printing. The lids for the pendulum bob and weight will need rotating so the larger side is on the bottom.

The bottom plate is designed to have print-in-place nuts inside the pillars. I found that using “Change Colour” rather than “Pause Print” works best, as it keeps the nozzle heated and does a mini-purge afterwards, so you don't end up with a gap in the print.