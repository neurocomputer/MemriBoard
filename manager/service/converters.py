"""
Конвертеры значений
"""

# pylint: disable=W0212

from typing import Union

def convert_volt_to_dac(dac_bit: int, vol_ref_dac: float, vol_value: float) -> int:
    """
    Конвертация напряжения в число для ЦАП

    Arguments:
        vol_value -- желаемое значение в вольтах

    Returns:
        dac_value -- число для ЦАП
    """
    dac_value = int(round(vol_value*(2**dac_bit-1)/vol_ref_dac,0))
    return dac_value

def convert_dac_to_volt(dac_bit: int, vol_ref_dac: float, dac_value: int, **kwargs) -> float:
    """
    Конвертация числа для ЦАП в напряжение

    Arguments:
        dac_value -- число для ЦАП
        kwargs -- знак напряжения

    Returns:
        vol_value -- значение в вольтах
    """
    vol_value = round(dac_value/((2**dac_bit-1)/vol_ref_dac),3)
    if 'sign' in kwargs:
        if kwargs['sign']: # если есть знак
            vol_value = -vol_value
    return vol_value

def convert_adc_to_current(dac_bit: int,
                           vol_ref_dac: float,
                           gain: float,
                           res_load: float,
                           vol_read: float,
                           adc_bit: int,
                           vol_ref_adc: float,
                           res_switches: float,
                           adc_value: Union[str, int],
                           dac_value: int,
                           sign: int):
    """
    Конвертация значения АЦП в ток
    """
    current = 0
    vol = convert_dac_to_volt(dac_bit, vol_ref_dac, dac_value, sign=sign)
    res = convert_adc_to_res(gain,
                             res_load,
                             vol_read,
                             adc_bit,
                             vol_ref_adc,
                             res_switches,
                             adc_value)
    if res != 0:
        current = vol/res
    return current

def convert_adc_to_volt(gain: float,
                        adc_bit: int,
                        vol_ref_adc: float,
                        adc_value: int) -> float:
    """
    Конвертация числа с АЦП в напряжение
    """
    vol_value = round(((adc_value * vol_ref_adc) / ((2 ** adc_bit)-1)) / gain, 5)
    return vol_value

def convert_adc_to_res(gain: float,
                       res_load: float,
                       vol_read: float,
                       adc_bit: int,
                       vol_ref_adc: float,
                       res_switches: float,
                       adc_value: Union[str, int]) -> float:
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
        res = (gain*res_load*vol_read*(2**adc_bit))/ \
            (adc_value*vol_ref_adc) - res_switches - res_load
        res = round(res, 2)
    except ZeroDivisionError:
        res = 2000000
    if res <= 0:
        res = 0.00000001
    return res

def convert_res_to_adc(gain: float,
                       res_load: float,
                       vol_read: float,
                       adc_bit: int,
                       vol_ref_adc: float,
                       res_switches: float,
                       res: int) -> int:
    """
    Функция для перевода из сопротивления в АЦП

    Arguments:
        res -- сопротивление мемристора

    Returns:
        adc_value -- значение с АЦП
    """
    adc_value = int(round((gain*res_load*vol_read*2**adc_bit)/ \
            (vol_ref_adc*(res_switches + res_load + res)), 0))

    return adc_value

def convert_res_to_weight(res_load: float, res: int) -> float:
    """
    Конвертер сопротивления в вес
    """
    weight = res_load/(res_load + res)
    return weight

def convert_weight_to_res(res_load: float, weight: float) -> int:
    """
    Конвертер веса в сопротивление
    """
    res = round(res_load/weight - res_load, 0)
    return int(res)
