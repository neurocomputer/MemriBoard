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
from manager.blanks import blanks, fill_blank


_modes = {'dir': 0,  # Режимы прямо и обратно
          'rev': 1}


def get_smu_iv_dc(
    params: dict,
    terminate: dict,
    blank_type:str
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_iv_dc

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_iv_dc_gen)
    
    
def get_smu_std(
    params: dict,
    terminate: dict,
    blank_type:str
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_std (режимы 7 и 9)

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_std_gen)


def smu_generator(
    params: dict,
    terminate: dict,
    blank_type: str,
    main_task_generator: Generator) -> Generator[list, None, None]:
    """Глобальный генератор тасков для инструметов с SMU.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).
        main_task_generator (Generator[list, None, None]): Main task generator

    Yields:
        Generator[list, None, None]: Task generator
    """
    interrupt_flag = False
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
        yield from main_task_generator(params, n_points, v_arrays, double, terminator, blank_type)
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
    if not ('crossbar_scan' in params and params['crossbar_scan']): # Если сканируем весь кроссбар, то не отключаем
        task = {'mode_flag': 'standby', 'id': 0}
        yield [task, terminator]
        
        
def _smu_iv_dc_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
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
                                'sign': _modes[dir],
                                'v_start': v_arrays[dir][0],
                                'v_stop': v_arrays[dir][-1],
                                'n_points': n_points[dir],
                                'double': double[dir],
                                'current_compliance': params[f'{dir}_cc']}
                yield [config_data, terminator]  # Config task
                sense_data = {'mode_flag': 'sense',
                                'vol': 0,
                                't_ms': params[f't_{dir}_msec_inc'],
                                't_us': params[f't_{dir}_usec_inc'],
                                'id': params['id'],
                                'sign': _modes[dir]}
                for _ in range(params[f'{dir}_inc_countr']):
                    for vol in v_arrays[dir]:
                        sense_data['vol'] = abs(int(vol))
                        yield [sense_data, terminator]  # Sense task
                    if double[dir]:
                        for vol in v_arrays[dir][::-1]:
                            sense_data['vol'] = abs(int(vol))
                            yield [sense_data, terminator]  # Sense task
    # Reading after the experiment
    read_config = {'mode_flag': 'read',
                    'vol': 0,
                    't_ms': params['t_rev_msec_inc'],
                    't_us': params['t_rev_usec_inc'],
                    'id': params['id'],
                    'sign': 1,
                    'current_compliance': params['rev_cc']}  # Reset
    yield [read_config, terminator]  # Read after experiment task
    sense_data = {'mode_flag': 'sense',
                    'vol': 0,
                    't_ms': params['t_rev_msec_inc'],
                    't_us': params['t_rev_usec_inc'],
                    'id': params['id'],
                    'sign': 1}
    yield [sense_data, terminator]
        
        
def _smu_std_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
    """Генератор для режима std (режимы 7 и 9).

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list]: Task generator for smu_iv_dc mode
    """
    # Генерация основных тасков
    for _ in range(params['count']):
        # Порядок dir-rev
        sequence = ['rev', 'dir'] if params['reverse'] else ['dir', 'rev']
        for dir in sequence:
            data = {'vol': 0,
                    't_ms': params[f't_{dir}_msec_inc'],
                    't_us': params[f't_{dir}_usec_inc'],
                    'id': params['id'],
                    'sign': _modes[dir]}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params[f'{dir}_inc_countr']):
                if n_points[dir] == 0:
                    data['vol'] = 0
                    yield [fill_blank(blanks[blank_type], data), terminator]
                else:
                    for vol in v_arrays[dir]:
                        data['vol'] = abs(int(vol))
                        yield [fill_blank(blanks[blank_type], data), terminator]
                    if double:
                        for vol in v_arrays[dir][::-1]:
                            data['vol'] = abs(int(vol))
                            yield [fill_blank(blanks[blank_type], data), terminator]