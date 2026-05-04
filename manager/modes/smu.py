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


_modes = {'dir': 0,  # Режимы прямо и обратно
          'rev': 1}


def get_smu_iv_dc(
    params: dict,
    terminate: dict,
    blank_type:str,
    logger=None
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_iv_dc.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_iv_dc_gen, logger=logger)
    
    
def get_smu_std(
    params: dict,
    terminate: dict,
    blank_type: str,
    logger=None
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_std (режимы 7 и 9).

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_std_gen, logger=logger)
    
    
def get_smu_pulsed_retention(
    params: dict,
    terminate: dict,
    blank_type: str,
    logger=None
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_pulsed_retention.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_pulsed_retention_gen, logger=logger)
    
    
def get_smu_endurance(
    params: dict, 
    terminate: dict,
    blank_type: str,
    logger=None
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_endurance.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_endurance_gen, logger=logger)
    
    
def get_visa_crossbar_scan(
    params: dict, 
    terminate: dict,
    blank_type: str,
    logger=None
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_endurance.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _visa_crossbar_scan_gen, 
                             connect_cell_before_main_gen=False, logger=logger)


def smu_generator(
    params: dict,
    terminate: dict,
    blank_type: str,
    main_task_generator: Generator,
    connect_cell_before_main_gen: bool = True,
    logger = None
) -> Generator[list, None, None]:
    """Глобальный генератор тасков для инструметов с SMU.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).
        main_task_generator (Generator[list, None, None]): Main task generator.
        connect_cell_before_main_gen (bool, optional): If True, connects cell specified in `params`
            before executing `main_task_generator`.

    Yields:
        Generator[list, None, None]: Task generator
    """
    interrupt_flag = False
    terminator = terminators[terminate['type']](terminate['value'])

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
        # Подключаем нужную ячейку
        if connect_cell_before_main_gen:
            bl = params['bl']
            wl = params['wl']
            task = {'mode_flag': 'connect_cell',
                    'wl': wl, 'bl': bl, 'id': 0}
            yield [task, terminator]
        
        # Генерация основных тасков
        yield from main_task_generator(params, n_points, v_arrays, double, terminator, blank_type)
        
        # Отключаем все ячейки в кроссбаре от источника
        task = {'mode_flag': 'standby', 'id': 0}
        yield [task, terminator]
    except Exception as ex: # для корректного завершения работы плат
        if logger is not None:
            logger.info(f'Task_generator: {type(ex).__name__}: {ex}')
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
        
        
def _smu_iv_dc_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
    # Генерация основных тасков
    for _ in range(params['count']):
        # порядок dir-rev
        sequence = ['rev', 'dir'] if params['reverse'] else ['dir', 'rev']
        for dir in sequence:
            for _ in range(params[f'{dir}_inc_countr']):
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
                    'sign': 1,
                    'triggered': True}
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
        # порядок dir-rev
        sequence = ['rev', 'dir'] if params['reverse'] else ['dir', 'rev']
        for dir in sequence:
            config_data = {'mode_flag': 'config_std',
                            'vol': 0,
                            't_ms': params[f't_{dir}_msec_inc'],
                            't_us': params[f't_{dir}_usec_inc'],
                            'id': params['id'],
                            'sign': _modes[dir],
                            'current_compliance': params[f'{dir}_cc']}
            pulse_sequence = []
            for _ in range(params[f'{dir}_inc_countr']):  # One config per direction
                if n_points[dir] == 0:
                    pulse_sequence.append('read')
                else:
                    for v in v_arrays[dir]:
                        if v != 0:
                            pulse_sequence.append(v)    
                        pulse_sequence.append('read')
                    if double[dir]:
                        for v in v_arrays[dir][::-1]:
                            if v != 0:
                                pulse_sequence.append(v)
                            pulse_sequence.append('read')
            if len(pulse_sequence) != 0:
                config_data['pulse_sequence'] = pulse_sequence
                yield [config_data, terminator]  # Config task
                sense_data = {'mode_flag': 'sense',
                            'vol': 0,
                            't_ms': params[f't_{dir}_msec_inc'],
                            't_us': params[f't_{dir}_usec_inc'],
                            'id': params['id'],
                            'sign': _modes[dir],
                            'triggered': True}
                for pulse in pulse_sequence:
                    if pulse == 'read':
                        sense_data['mode_flag'] = 'sense'  # Read pulse by trigger
                        yield [sense_data, terminator]
                        sense_data['vol'] = 0
                    else:
                        sense_data['mode_flag'] = 'trigger'  # Apply pulse by trigger
                        sense_data['vol'] = abs(int(pulse))
                        yield [sense_data, terminator]
                            
                            
def _smu_pulsed_retention_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
    """Генератор для режима pulsed_retention: Игнорируются все напряжения, которые тикет пытается подать, 
    подаются только импульсы чтения. Очистка буффера устройства проводится на каждый Set-Reset цикл.

    Yields:
        Generator[list, None, None]: Task generator for smu_pulsed_retention mode.
    """
    # Генерация основных тасков
    n_pulses = params['dir_inc_countr'] + params['dir_dec_countr'] + \
               params['rev_inc_countr'] + params['rev_dec_countr']
    for _ in range(params['count']):
        data = {'mode_flag': 'config_pulsed_retention',
                'vol': 0,
                't_ms': params['t_dir_msec_inc'],
                't_us': params['t_dir_usec_inc'],
                'id': params['id'],
                'sign': 1,
                'n_pulses': n_pulses,
                'current_compliance': params['dir_cc']}
        if 'wl' in params and 'bl' in params:
            data['wl'] = params['wl']
            data['bl'] = params['bl']
        if 'dir_interval' in params and 'rev_interval' in params:
            data['dir_interval'] = params['dir_interval']
            data['rev_interval'] = params['rev_interval']
        yield [data, terminator]  # Config task
        sense_data = {'mode_flag': 'sense',
                      'vol': 0,
                      't_ms': params['t_dir_msec_inc'],
                      't_us': params['t_dir_usec_inc'],
                      'id': params['id'],
                      'sign': 1}
        for _ in range(n_pulses):
            yield [sense_data, terminator]  # Sense task
            
            
def _smu_endurance_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
    """Endurance generator (async).

    Yields:
        Generator[list, None, None]: Main task generator.
    """
    data = {'mode_flag': 'config_endurance',
            'v_dir': params['v_dir_stop_inc'],
            'v_rev': params['v_rev_stop_inc'],
            't_ms': params['t_dir_msec_inc'],
            't_us': params['t_dir_usec_inc'],
            'id': params['id'],
            'n_cycles': params['count'],
            'dir_cc': params['dir_cc'],
            'rev_cc': params['rev_cc']}
    if 'wl' in params and 'bl' in params:
        data['wl'] = params['wl']
        data['bl'] = params['bl']
    if 'dir_interval' in params:
        data['trigger_interval'] = params['dir_interval']
    yield [data, terminator]  # Config task
    sense_data = {'mode_flag': 'sense',
                  'vol': 0,
                  't_ms': params['t_dir_msec_inc'],
                  't_us': params['t_dir_usec_inc'],
                  'id': params['id'],
                  'sign': 1,
                  'skip_one': True}
    for _ in range(params['count']):
        yield [sense_data, terminator]
        yield [sense_data, terminator]  # Two sense tasks for each cycle
        
        
def _visa_crossbar_scan_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
    """Crossbar resistance scan generator (async).

    Yields:
        Generator[list, None, None]: Main task generator.
    """
    if params['dir_inc_countr'] != 0:
        dir = 'dir'
    else:
        dir = 'rev'
    config_task = {'mode_flag': 'config_std',
                   'vol': 0,
                   't_ms': params[f't_{dir}_msec_inc'],
                   't_us': params[f't_{dir}_usec_inc'],
                   'id': params['id'],
                   'sign': _modes[dir],
                   'current_compliance': params[f'{dir}_cc'],
                   'pulse_sequence': ['read' for _ in range(params['col_num'] * params['row_num'])]}
    yield [config_task, terminator]
    sense_data = {'mode_flag': 'sense',
                  'vol': 0,
                  't_ms': params['t_dir_msec_inc'],
                  't_us': params['t_dir_usec_inc'],
                  'id': params['id'],
                  'sign': 1,
                  'triggered': True,
                  'crossbar_scan': True}
    for wl in range(params['col_num']):
        for bl in range(params['row_num']):
            task = {'mode_flag': 'connect_cell',
                    'wl': wl, 'bl': bl, 'id': 0}
            yield [task, terminator]  # Connecting
            sense_data['wl'] = wl
            sense_data['bl'] = bl
            yield [sense_data, terminator]  # Reading