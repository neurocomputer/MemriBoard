"""
Считываем текущие веса
"""
from gui.src import choose_cells

dop_mod = 0

#!!!!!! ограничить диапазон
diap = 0
diap_min = 100 # Ohm
diap_max = 100000 # Ohm

#!!!!!! ограничить работоспособными
cells, _ = choose_cells('good_cells.csv', 8, 32)
cells_filter = 0

import os
import numpy as np
import pickle

from MemriCORE.rpi_modes import RPI_modes
import RPi.GPIO as gpio

model_path = 'models/model_pid_3'

def convert_res_to_weight(res: int) -> float:
    """
    Конвертер сопротивления в вес
    """
    weight = 3000/(3000 + res)
    return weight

gpio.setwarnings(False)
conn = RPI_modes()

wl_all = 8
bl_all = 32

# прочитать все веса в сети
all_mem_weights = np.zeros(shape=(bl_all, wl_all), dtype=float)

for wl in range(wl_all):
    for bl in range(bl_all):
        adc = conn.mode_7(0,0,0,0,1,wl,bl)
        # повторный запрос
        if adc[0] < 10:
            adc = conn.mode_7(0,0,0,0,1,wl,bl)
        adc_value = adc[0]
        if adc_value < 50:
            adc_value = 50
        res = (11.11 * 3000 * 0.3 * (2**14)) / (adc_value*5) - 10 - 3000
        if res <= 0:
            res = 0.00000001
        if dop_mod:
            if diap:
                if diap_min > res or res > diap_max:
                    all_mem_weights[bl][wl] = 1000000
                else:
                    print(f'wl {wl} bl {bl} = {int(res)}')
                    all_mem_weights[bl][wl] = convert_res_to_weight(int(res))
            if cells_filter:
                if not (wl, bl) in cells:
                    all_mem_weights[bl][wl] = 1000000
                else:
                    print(f'wl {wl} bl {bl} = {int(res)}')
                    all_mem_weights[bl][wl] = convert_res_to_weight(int(res))
        else:
            print(f'wl {wl} bl {bl} = {int(res)}')
            all_mem_weights[bl][wl] = convert_res_to_weight(int(res))

with open(os.path.join(model_path, 'all_mem_weights.pkl'), 'wb') as fp:
    pickle.dump(all_mem_weights, fp)
