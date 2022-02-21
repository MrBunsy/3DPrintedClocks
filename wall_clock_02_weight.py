import clocks.clock as clock


'''
Just a new printed weight for the original flawed (but functional) clock
'''

clockName="wall_clock_02"
clockOutDir="out"

weight = clock.Weight(height=110, diameter=40)
weight.outputSTLs(clockName, clockOutDir)
weight.printInfo()