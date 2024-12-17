"""
Конвертеры значений
"""

# pylint: disable=W0212

from typing import Union

def convert_volt_to_dac(parent, vol_value: float) -> int:
    """
    Конвертация напряжения в число для ЦАП

    Arguments:
        vol_value -- желаемое значение в вольтах

    Returns:
        dac_value -- число для ЦАП
    """
    dac_value = int(round(vol_value*(2**parent._dac_bit-1)/parent._vol_ref_dac,0))
    return dac_value

def convert_dac_to_volt(parent, dac_value: int) -> float:
    """
    Конвертация числа для ЦАП в напряжение

    Arguments:
        dac_value -- число для ЦАП

    Returns:
        vol_value -- значение в вольтах
    """
    vol_value = round(dac_value/((2**parent._dac_bit-1)/parent._vol_ref_dac),3)
    return vol_value

def convert_adc_to_volt(parent, adc_value: int) -> float:
    """
    Конвертация числа с АЦП в напряжение
    """
    vol_value = round(((adc_value * parent._vol_ref_adc) / ((2 ** parent._adc_bit)-1)) / parent._gain, 5)
    return vol_value

def convert_adc_to_res(parent, adc_value: Union[str, int]) -> float:
    """
    Функция для перевода из АЦП в сопротивление. Если значение АЦП
    равно 0, то возвращает 2 МОм. Если с АЦП пришло не корректное
    значение и сопротивление получается отрицательное то оно заменяется
    на 1 Ом.

    Arguments:
        adc_value -- значение с АЦП

    Returns:
        res -- сопротивление мемристора
    """
    adc_value = int(adc_value)
    try:
        res = (parent._gain*parent._res_load*parent._vol_read*(2**parent._adc_bit))/ \
            (adc_value*parent._vol_ref_adc) - parent._res_switches - parent._res_load
        res = round(res, 2)
    except ZeroDivisionError:
        res = 2000000
    if res <= 0:
        res = 1
    return res

def convert_res_to_adc(parent, res: int) -> int:
    """
    Функция для перевода из сопротивления в АЦП

    Arguments:
        res -- сопротивление мемристора

    Returns:
        adc_value -- значение с АЦП
    """
    adc_value = int(round((parent._gain*parent._res_load*parent._vol_read*2**parent._adc_bit)/ \
            (parent._vol_ref_adc*(parent._res_switches + parent._res_load + res)), 0))

    return adc_value

def convert_res_to_weight(parent, res: int) -> float:
    """
    Конвертер сопротивления в вес
    """
    weight = parent._res_load/(parent._res_load + res)
    return weight

def convert_weight_to_res(parent, weight: float) -> int:
    """
    Конвертер веса в сопротивление
    """
    res = round(parent._res_load/weight - parent._res_load, 0)
    return int(res)
