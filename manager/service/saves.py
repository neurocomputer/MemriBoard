"""
Функции сохранения
"""

from typing import BinaryIO

def save_list_to_bytearray(file: BinaryIO, dac: int, adc: int, bts: int = 2) -> None:
    """
    Потоковое сохранение в файл в формате байт

    Arguments:
        file -- открытый файл для записи
        data -- список данных (функция расчитана на 2 числа и 4 байта)

    Keyword Arguments:
        bts -- размер одного числа в байтах (default: {2})
    """
    results = []
    dac = dac.to_bytes(bts, 'big', signed=True)
    adc = adc.to_bytes(bts, 'big', signed=True)
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
