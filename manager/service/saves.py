"""
Функции сохранения
"""

from typing import BinaryIO
from datetime import datetime
import os
import csv

def save_list_to_bytearray(file: BinaryIO, sign: int, dac: int, adc: int, bts: int = 2) -> None:
    """
    Потоковое сохранение в файл в формате байт

    Arguments:
        file -- открытый файл для записи
        data -- список данных (функция рассчитана на 3 числа и 6 байт)

    Keyword Arguments:
        bts -- размер одного числа в байтах (default: {2})
    """
    results = []
    sign = sign.to_bytes(bts, 'big', signed=True)
    dac = dac.to_bytes(bts, 'big', signed=True)
    adc = adc.to_bytes(bts, 'big', signed=True)
    results.append(sign[0])
    results.append(sign[1])
    results.append(dac[0])
    results.append(dac[1])
    results.append(adc[0])
    results.append(adc[1])
    file.write(bytearray(results))

def results_from_bytes(result: bytearray, bts: int = 2) -> list:
    """
    Перевод сохраненных результатов из байт в int
    """
    results = []
    for i in range(0, len(result), bts):
        results.append(int.from_bytes(result[i:i+bts],
                                      byteorder='big',
                                      signed=True))
    return results

def init_csv_apply(csv_save_path, exp_name, crossbar_id, wl, bl, csv_header) -> str:
    date = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
    filename = f'{date}_{exp_name}_{crossbar_id}_{wl}-{bl}.csv'
    filepath = os.path.join(csv_save_path, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        file_wr = csv.writer(file, delimiter=';')
        file_wr.writerow(csv_header)
    return filepath
    
    