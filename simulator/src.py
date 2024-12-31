"""
Вспомогательные функции симулятора
"""

# pylint: disable=W0212, C0301

import pickle
import random
from typing import Union
import numpy as np
from simulator.memristor import MemristorModel

def create_crossbar_array(serial: str, row_num: int, col_num: int) -> None:
    """
    Создание модели кроссбара для симулятора
    """
    crossbar = []
    for _ in range(row_num):
        crossbar_row = []
        for _ in range(col_num):
            memristor = MemristorModel()
            # заполняем переменные состояния случайным образом
            memristor.state_variable = random.randint(0,11) / 10
            memristor.fi_ion += np.random.normal(loc=0, scale=0.1)
            crossbar_row.append(memristor)
        crossbar.append(crossbar_row)
    save_crossbar_array(serial, crossbar)

def load_crossbar_array(serial: str) -> Union[int, list]:
    """
    Загрузка модели кроссбара для симулятора
    """
    status = 0
    crossbar = []
    try:
        with open(serial+'.cb', 'rb') as file:
            crossbar = pickle.load(file)
            status = 1
    except FileNotFoundError:
        print('файл не найден!')
    return status, crossbar

def save_crossbar_array(serial: str, crossbar: list) -> None:
    """
    Сохранение модели кроссбара для симулятора
    """
    with open(serial+'.cb', 'wb') as file:
        pickle.dump(crossbar, file)

def send_task_to_crossbar(serial: str, crossbar: list, **kwargs) -> int:
    """
    Послать задачу в модель кроссбара в симуляторе
    """
    # запись
    if kwargs['vol'] != 0:
        for _ in range(int(kwargs['duration'])):
            crossbar[kwargs['bl']][kwargs['wl']].apply_voltage(kwargs['vol'])
        save_crossbar_array(serial, crossbar)
    # чтение
    current = crossbar[kwargs['bl']][kwargs['wl']].apply_voltage(kwargs['vol_read'])
    # переводим ток так, как если бы работала плата
    model_resistance = kwargs['vol_read'] / current
    v_out = kwargs['vol_read'] * kwargs['res_load'] / (model_resistance + kwargs['res_switches'] + kwargs['res_load'])
    v_out = v_out * kwargs['gain']
    res = int(2**kwargs['adc_bit'] * v_out / kwargs['vol_ref_adc'])
    return res
