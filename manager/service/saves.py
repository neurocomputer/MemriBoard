"""
Функции сохранения
"""

from typing import BinaryIO
import struct

def save_list_to_bytearray(file: BinaryIO, sign: int, dac: int, adc: int, bts: int = 2) -> None:  # TODO remove
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

def results_from_bytes(result: bytearray, bts: int = 2) -> list:  # TODO: remove
    """
    Перевод сохраненных результатов из байт в int
    """
    results = []
    for i in range(0, len(result), bts):
        results.append(int.from_bytes(result[i:i+bts],
                                      byteorder='big',
                                      signed=True))
    return results

def save_list_to_bytearray_float(file: BinaryIO, sign: int, voltage: float, resistance: int, *args: float) -> None:
    """
    Потоковое сохранение в файл в формате байт
    
    Arguments:
        file: открытый файл для записи.
        sign (int): знак напряжения (0 +, 1 -), сохраняется как unsigned char (1 byte).
        voltage (float): напряжение, сохраняется как float (4 байта).
        resistance (float): сопротивление (в Ом), сохраняется как float (4 байта).
        args (float): все сохраняются как float.
    """
    fmt = 'Bff' + 'f' * len(args)  # Format: Unsigned char, float, unsigned short, floats
    file.write(struct.pack(fmt, sign, voltage, resistance, *args))
    
def results_from_float_bytes(result: bytes, additional_items_size: int = 0) -> list:
    """
    Get result from the bytearray
    
    Args:
        result (bytes): result bytearray.
        additional_items_size (int, optional): Amount of additional items save to the bytearray. Defaults to 0.
        
    Returns:
        [(sign, voltage, resistance, *args), (sign2, voltage2, resistance2, *args2), ...] 
    """
    fmt = 'Bff' + 'f' * additional_items_size
    return list(struct.iter_unpack(fmt, result))
