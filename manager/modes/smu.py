"""
Генераторы тасков для измерения при помощи SMU на VISA-инструментах. 
Создается три типа тасков:
1. Конфигурационный (config) - для конфигурации эксперимента на оборудовании, 
2. Таск чтения (sense) - для считывания текущего значения 
тока в процессе измерения,
3. Таск окончания тикета (ticket_end) для сброса оборудования. 
Тип таска указывается в поле mode_flag.

Типовик запроса:
params =  {
    "v_dir_strt_inc": 0,
    "v_dir_stop_inc": 819,
    "v_dir_step_inc": 410,
    "t_dir_msec_inc": 0,
    "t_dir_usec_inc": 100,
    "dir_inc_countr": 1,
    
    "v_dir_strt_dec": 819,
    "v_dir_stop_dec": 0,
    "v_dir_step_dec": 410,
    "t_dir_msec_dec": 0,
    "t_dir_usec_dec": 100,
    "dir_dec_countr": 1,
    
    "v_rev_strt_inc": 0,
    "v_rev_stop_inc": 819,
    "v_rev_step_inc": 410,
    "t_rev_msec_inc": 0,
    "t_rev_usec_inc": 100,
    "rev_inc_countr": 1,
    
    "v_rev_strt_dec": 819,
    "v_rev_stop_dec": 0,
    "v_rev_step_dec": 410,
    "t_rev_msec_dec": 0,
    "t_rev_usec_dec": 100,
    "rev_dec_countr": 1,
    
    "count": 1,
    "reverse": 0,
    
    "id": 0,
    "wl": 0,
    "bl": 0,
    
    "dir_soft_cc": 0.0003,
    "rev_soft_cc": 0.1
}
"""

import numpy as np
from typing import Generator
from manager.terminate import terminators

def get_smu_iv_dc(
    params: dict,
    terminate: dict,
    blank_type: str
) -> Generator[list, None, None]:
    """Генератор для режима SMU_IV_DC.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list]: Task generator for smu_iv_dc mode
    """
    interrupt_flag = False
    modes = {'dir': 0,
             'rev': 1}
    terminator = terminators[terminate['type']](terminate['value'])

    # Подключаем нужную ячейку
    bl = params['bl']
    wl = params['wl']
    task = {'mode_flag': 'connect_cell',
            'wl': wl, 'bl': bl, 'id': 0}
    yield [task, terminator]

    # Рассчитываем параметры
    n_points = {}
    v_arrays = {}
    double = {}
    for dir in ['dir', 'rev']:
        try:
            v_arrays[dir] = np.arange(
                params[f'v_{dir}_strt_inc'],
                params[f'v_{dir}_stop_inc'] + params[f'v_{dir}_step_inc'],
                params[f'v_{dir}_step_inc']
            )
            n_points[dir] = len(v_arrays[dir])
            double[dir] = True if params[f'v_{dir}_strt_dec'] != 0 else False
        except ZeroDivisionError:
            n_points[dir] = 0
            
    try:
        # Генерация основных тасков
        for _ in range(params['count']):
            # порядок dir-rev
            sequence = ['rev', 'dir'] if params['reverse'] else ['dir', 'rev']
            for dir in sequence:
                sense_data = {}
                sense_data['id'] = 0
                if n_points[dir] != 0:
                    config_data = {'mode_flag': 'config_iv_dc',
                                'vol': 0,
                                't_ms': params[f't_{dir}_msec_inc'],
                                't_us': params[f't_{dir}_usec_inc'],
                                'id': params['id'],
                                'sign': modes[dir],
                                'v_start': v_arrays[dir][0],
                                'v_stop': v_arrays[dir][-1],
                                'n_points': n_points[dir],
                                'double': double[dir],
                                'current_compliance': params[f'{dir}_cc']}
                    if 'wl' in params and 'bl' in params:
                        config_data['wl'] = params['wl']
                        config_data['bl'] = params['bl']
                    else:
                        config_data['wl'] = 0
                        config_data['bl'] = 0
                    yield [config_data, terminator]  # Config task
                    sense_data = {'mode_flag': 'sense',
                                'vol': 0,
                                't_ms': params[f't_{dir}_msec_inc'],
                                't_us': params[f't_{dir}_usec_inc'],
                                'id': params['id'],
                                'sign': modes[dir]}
                    for _ in range(params[f'{dir}_inc_countr']):
                        for vol in v_arrays[dir]:
                            sense_data['vol'] = abs(int(vol))
                            yield [sense_data, terminator]  # Sense task
                        if double[dir]:
                            for vol in v_arrays[dir][::-1]:
                                sense_data['vol'] = abs(int(vol))
                                yield [sense_data, terminator]  # Sense task
                # else: # напряжение не подается, просто мерием сопротивление ячейки
                #     config_data = {'mode_flag': 'config_iv_dc',
                #                 'vol': 0,
                #                 't_ms': 0,
                #                 't_us': 0,
                #                 'id': 0,
                #                 'sign': 0,
                #                 'v_start': 0,
                #                 'v_stop': 0,
                #                 'n_points': 0,
                #                 'double': 0,
                #                 'current_compliance': 0}
                #     if 'wl' in params and 'bl' in params:
                #         config_data['wl'] = params['wl']
                #         config_data['bl'] = params['bl']
                #     else:
                #         config_data['wl'] = 0
                #         config_data['bl'] = 0
                #     yield [config_data, terminator]  # Config task
                #     sense_data = {'mode_flag': 'sense',
                #                 'vol': 0,
                #                 't_ms': 0,
                #                 't_us': 0,
                #                 'id': 0,
                #                 'sign': 0}
                #     yield [sense_data, terminator]  # Sense task
                #     break
    except Exception as ex: # для корректного завершения работы плат
        print(ex)
        interrupt_flag = True
        exception = ex
        yield
    if interrupt_flag:
        if exception == 'interrupt':
            task = {'mode_flag': 'interrupt', 'id': 0}
            yield [task, terminator]
        else:
            task = {'mode_flag': 'panic', 'id': 0}
            yield [task, terminator]
    # Отключаем все ячейки в кроссбаре от источника
    task = {'mode_flag': 'standby', 'id': 0}
    yield [task, terminator]