from MemriCORE.rpi_modes import RPI_modes
import RPi.GPIO as gpio
import matplotlib.pyplot as plt
import time
import numpy as np
test = RPI_modes()

wl = 0
start = time.time()

#for i in range(4):
#    adc = test.mode_7(0,0,0,0,1,0,1)
#    print(adc)
#print(time.time() - start)

dacmas = [0,0,0,0,0,0,0,0,
          0,0,0,0,0,0,0,0,
          0,0,0,0,0,0,0,0,
          0,0,0,0,0,0,0,0]
dacmas = [40 for i in range(32)]
res = test.mode_mvm(dacmas, 0, 0, 0, 0, wl, 777)
print(res)