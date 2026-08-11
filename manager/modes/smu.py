"""
Генераторы тасков для измерения при помощи SMU на VISA-инструментах. 
Создается три типа тасков:
1. Конфигурационный (config) - для конфигурации эксперимента на оборудовании, 
2. Таск чтения (sense) - для считывания текущего значения 
тока в процессе измерения,
3. Таск окончания тикета (ticket_end) для сброса оборудования. 
Тип таска указывается в поле mode_flag.
"""

import numpy as np
from collections.abc import Generator
from manager.terminate import terminators
from logging import Logger


_signs = {'dir': 0,  # Режимы прямо и обратно
          'rev': 1}

DIR_REV = 'dir'  # Global variable
 
def dr(key: str) -> str:
    """Helper function that appends 'dir' or 'rev' to the end of the key"""
    return f'{key}_{DIR_REV}'

class SMUGen:
    def __init__(self, parent, logger: Logger) -> None:
        self.parent = parent  # Menu
        self.logger = logger
        
        
    def _prepare(self, terminate: dict) -> None:
        """Prepare parameters before generating tasks"""
        self.interrupt_flag = False
        self.terminator = terminators[terminate['type']](terminate['value'])
        
        
    def _connect_cell(self, params: dict) -> Generator[list, None, None]:
        """Connect cell before generating main sequence"""
        task = {
            'mode_flag': 'connect_cell',
            'wl': params['wl'], 
            'bl': params['bl'], 
            'id': 0
        }
        yield [task, self.terminator]
        
        
    def _disconnect_cell(self) -> Generator[list, None, None]:
        """Closing all cells"""
        task = {'mode_flag': 'standby', 'id': 0}
        yield [task, self.terminator]
        
        
    def _handle_exception(self, e: Exception) -> Generator[list, None, None]:
        """Handle exeption while generating"""
        self.logger.warning(f'Task_generator: {type(e).__name__}: {e}')
        self.interrupt_flag = True
        yield
        
        
    def _check_interruption(self) -> Generator[list, None, None]:
        """Check if the experiment was interrupted and send panic flag"""
        if self.interrupt_flag:
            task = {'mode_flag': 'panic', 'id': 0}
            yield [task, self.terminator]
            
            
    def _create_sweep_array(self, params: dict) -> dict:
        """Create sweep array based on sweep parameters"""
        arrays = {}
        for dir_rev in ['dir', 'rev']:
            try:
                arrays[dir_rev] = np.arange(
                    params[f'start_{dir_rev}'],
                    params[f'stop_{dir_rev}'] + params[f'step_{dir_rev}'],
                    params[f'step_{dir_rev}']
                )
            except ZeroDivisionError:
                arrays[dir_rev] = []
        return arrays  # {dir: array_dir, rev: array_rev}
    
    
    def smu_prog_sync(self, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
        pass
    

    def smu_iv_dc(self, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
        """Generator for IV DC mode"""
        global DIR_REV
        # Preparing
        self._prepare(terminate)
        # dir-rev sequence
        sequence = ['rev', 'dir'] if params['reverse'] else ['dir', 'rev']
        arrays = self._create_sweep_array(params)
        sense_task = {  # Sense task template
            'mode_flag': 'sense',
            'vol': 0,
            'id': params['id'],
            'sign': 'dir'
        }
        # Generating
        try:
            yield from self._connect_cell(params)
            for _ in range(params['count']):  # Outer cycle
                for dir_rev in sequence:  # dir and rev
                    DIR_REV = dir_rev
                    for _ in range(params[f'amount_{dir_rev}']):
                        if len(arrays[dir_rev]) != 0:
                            config_task = {
                                'mode_flag': 'config_iv_dc',
                                'vol': 0,
                                'time_interval': params[dr('interval')],
                                'id': params['id'],
                                'sign': _signs[dir_rev],
                                'v_start': params[dr('start')],
                                'v_stop': params[dr('stop')],
                                'n_points': len(arrays[dir_rev]),
                                'double': params[dr('double')],
                                'current_compliance': params[dr('compliance')]
                            }
                            yield [config_task, self.terminator]  # Config task
                            
                            sense_task['sign'] = _signs[dir_rev]
                            for vol in arrays[dir_rev]:
                                sense_task['vol'] = vol
                                yield [sense_task, self.terminator]  # Sense tasks
                            if params[dr('double')]:
                                for vol in arrays[dir_rev][::-1]:
                                    sense_task['vol'] = vol
                                    yield [sense_task, self.terminator]  # Sense tasks
            # Reading after sweep
            measure_ticket = self.parent.get_measure_ticket()
            config_task = {  # FIXME
                'mode_flag': 'config_smu_pulsed_retention',
                'current_compliance': measure_ticket['params']['compliance'],
                'pulse_width': measure_ticket['params']['pulse_width'],
                'pulse_period': measure_ticket['params']['pulse_period'],
                'read_voltage': measure_ticket['params']['read_voltage'],
                'sign': _signs[measure_ticket['params']['read_direction']],
                'count': 1,
                'id': params['id']
            }
            yield [config_task, self.terminator]  # Config measure
            del sense_task['vol']
            sense_task['sign'] = _signs[measure_ticket['params']['read_direction']]
            yield [sense_task, self.terminator]  # Read measure
            
            yield from self._disconnect_cell()
        except Exception as e:
            yield from self._handle_exception(e)
        yield from self._check_interruption()
            

    def smu_pulsed_retention(self, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
        pass
    

    def smu_endurance(self, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
        pass
    

    def smu_pot_dep(self, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
        pass


    def crossbar_scan(self, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
        pass


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
    
    
def get_smu_pot_dep(
    params: dict, 
    terminate: dict,
    blank_type: str,
    logger=None
) -> Generator[list, None, None]:
    """Генератор тасков для режима smu_pot_dep.

    Args:
        params (dict): Experiment params.
        terminate (dict): Terminator type and value.
        blank_type (str): Blank type (blanks.py).

    Yields:
        Generator[list, None, None]: Task generator
    """
    yield from smu_generator(params, terminate, blank_type, _smu_pot_dep_gen, logger=logger)
    
    
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
                                    # 'sign': _modes[dir],
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
                                    'id': params['id']}
                                    # 'sign': _modes[dir]}
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
                  'read': True,
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
                            # 'sign': _modes[dir],
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
                              'read': False,
                            'vol': 0,
                            't_ms': params[f't_{dir}_msec_inc'],
                            't_us': params[f't_{dir}_usec_inc'],
                            'id': params['id'],
                            # 'sign': _modes[dir],
                            'triggered': True}
                for pulse in pulse_sequence:
                    if pulse == 'read':
                        sense_data['mode_flag'] = 'sense'  # Read pulse by trigger
                        sense_data['vol'] = 0
                        sense_data['read'] = True
                        yield [sense_data, terminator]
                    else:
                        sense_data['mode_flag'] = 'trigger'  # Apply pulse by trigger
                        sense_data['vol'] = abs(int(pulse))
                        sense_data['read'] = False
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
                      'read': True,
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
    sense_data_dir = {'mode_flag': 'sense',  # Sensing dir pulse
                      'read': True,
                      'vol': params['v_dir_stop_inc'],
                      't_ms': params['t_dir_msec_inc'],
                      't_us': params['t_dir_usec_inc'],
                      'id': params['id'],
                      'sign': 1,
                      'skip_one': True}
    sense_data_rev = {'mode_flag': 'sense',  # Sensing rev pulse
                      'read': True,
                      'vol': params['v_rev_stop_inc'],
                      't_ms': params['t_dir_msec_inc'],
                      't_us': params['t_dir_usec_inc'],
                      'id': params['id'],
                      'sign': 1,
                      'skip_one': True}
    for _ in range(params['count']):
        yield [sense_data_dir, terminator]
        yield [sense_data_rev, terminator]  # Two sense tasks for each cycle
        
        
def _smu_pot_dep_gen(params, n_points, v_arrays, double, terminator, blank_type) -> Generator[list, None, None]:
    """Const pulse generator (async): potentiation/depression.

    Yields:
        Generator[list, None, None]: Main task generator.
    """
    if params['dir_inc_countr'] == 1:  # Potentiation
        vol = params['v_dir_stop_inc']
        sign = 0
        t_ms = params['t_dir_msec_inc']
        t_us = params['t_dir_usec_inc']
        data = {'mode_flag': 'config_pot_dep',
                'vol': vol,
                't_ms': t_ms,
                't_us': t_us,
                'id': params['id'],
                'n_pulses': params['count'],
                'compliance': params['dir_cc'],
                'sign': sign}
        if 'dir_interval' in params:
            data['trigger_interval'] = params['dir_interval']
    elif params['rev_inc_countr'] == 1:
        vol = params['v_rev_stop_inc']
        sign = 1
        t_ms = params['t_rev_msec_inc']
        t_us = params['t_rev_usec_inc']
        data = {'mode_flag': 'config_pot_dep',
                'vol': vol,
                't_ms': t_ms,
                't_us': t_us,
                'id': params['id'],
                'n_pulses': params['count'],
                'compliance': params['rev_cc'],
                'sign': sign}
        if 'rev_interval' in params:
            data['trigger_interval'] = params['rev_interval']
    else:
        raise ChildProcessError('Bad config for pot/dep: dir or rev amount must be equal to 1')
    if 'wl' in params and 'bl' in params:
        data['wl'] = params['wl']
        data['bl'] = params['bl']
    yield [data, terminator]  # Config task
    sense_data = {'mode_flag': 'sense',
                  'vol': vol,
                  't_ms': t_ms,
                  't_us': t_us,
                  'id': params['id'],
                  'sign': sign}
    for _ in range(params['count']):
        yield [sense_data, terminator]
        
        
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
                #    'sign': _modes[dir],
                   'current_compliance': params[f'{dir}_cc'],
                   'pulse_sequence': ['read' for _ in range(params['col_num'] * params['row_num'])]}
    yield [config_task, terminator]
    sense_data = {'mode_flag': 'sense',
                  'vol': 0,
                  'read': True,
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