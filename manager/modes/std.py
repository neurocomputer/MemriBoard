"""
Стандартный генератор-декомпозитор импульсных последовательностей
Позволяет генерировать стандартные режимы: ВАХ, эндюранс, ретеншн, 
пластичность, сет, ресет, программирование и т.д.

Типовик запроса:
params = {
    'v_dir_strt_inc': 0,
    'v_dir_stop_inc': 0,
    'v_dir_step_inc': 0,
    't_dir_msec_inc': 0,
    't_dir_usec_inc': 0,
    'dir_inc_countr': 0,

    'v_dir_strt_dec': 0,
    'v_dir_stop_dec': 0,
    'v_dir_step_dec': 0,
    't_dir_msec_dec': 0,
    't_dir_usec_dec': 0,
    'dir_dec_countr': 0,

    'v_rev_strt_inc': 0,
    'v_rev_stop_inc': 0,
    'v_rev_step_inc': 0,
    't_rev_msec_inc': 0,
    't_rev_usec_inc': 0,
    'rev_inc_countr': 0,

    'v_rev_strt_dec': 0,
    'v_rev_stop_dec': 0,
    'v_rev_step_dec': 0,
    't_rev_msec_dec': 0,
    't_rev_usec_dec': 0,
    'rev_dec_countr': 0,

    'count': 0,
    'reverse': 0,
    'id': 0,

    'wl': 0,
    'bl':0
}
"""

import numpy as np
from typing import Generator
from manager.blanks import blanks, fill_blank
from manager.terminate import terminators

def get_std(params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
    """
    Стандартный генератор-декомпозитор
    """
    modes = {'dir': 0,
             'rev': 1}
    terminator = terminators[terminate['type']](terminate['value'])
    # инкремент dir
    try:
        dir_inc = np.arange(params['v_dir_strt_inc'],
                            params['v_dir_stop_inc'] + params['v_dir_step_inc'],
                            params['v_dir_step_inc'])
        dir_inc = [int(item) for item in dir_inc]
    except ZeroDivisionError:
        dir_inc = [0]
    # декремент dir
    try:
        dir_dec = np.arange(params['v_dir_strt_dec'],
                            params['v_dir_stop_dec'] + params['v_dir_step_dec'],
                            -params['v_dir_step_dec'])
        dir_dec = [int(item) for item in dir_dec]
    except ZeroDivisionError:
        dir_dec = [0]
    # инкремент rev
    try:
        rev_inc = np.arange(params['v_rev_strt_inc'],
                            params['v_rev_stop_inc'] + params['v_rev_step_inc'],
                            params['v_rev_step_inc'])
        rev_inc = [int(item) for item in rev_inc]
    except ZeroDivisionError:
        rev_inc = [0]
    # декремент rev
    try:
        rev_dec = np.arange(params['v_rev_strt_dec'],
                            params['v_rev_stop_dec'] + params['v_rev_step_dec'],
                            -params['v_rev_step_dec'])
        rev_dec = [int(item) for item in rev_dec]
    except ZeroDivisionError:
        rev_dec = [0]
    for _ in range(params['count']):
        # порядок dir-rev
        if not params['reverse']:
            # инкремент dir
            data = {'vol': 0,
                    't_ms': params['t_dir_msec_inc'],
                    't_us': params['t_dir_usec_inc'],
                    'id': params['id'],
                    'sign': modes['dir']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['dir_inc_countr']):
                for vol in dir_inc:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # декремент dir
            data = {'vol': 0,
                    't_ms': params['t_dir_msec_dec'],
                    't_us': params['t_dir_usec_dec'],
                    'id': params['id'],
                    'sign': modes['dir']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['dir_dec_countr']):
                for vol in dir_dec:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # инкремент rev
            data = {'vol': 0,
                    't_ms': params['t_rev_msec_inc'],
                    't_us': params['t_rev_usec_inc'],
                    'id': params['id'],
                    'sign': modes['rev']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['rev_inc_countr']):
                for vol in rev_inc:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # декремент rev
            data = {'vol': 0,
                    't_ms': params['t_rev_msec_dec'],
                    't_us': params['t_rev_usec_dec'],
                    'id': params['id'],
                    'sign': modes['rev']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['rev_dec_countr']):
                for vol in rev_dec:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
        # порядок rev-dir
        else:
            # инкремент rev
            data = {'vol': 0,
                    't_ms': params['t_rev_msec_inc'],
                    't_us': params['t_rev_usec_inc'],
                    'id': params['id'],
                    'sign': modes['rev']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['rev_inc_countr']):
                for vol in rev_inc:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # декремент rev
            data = {'vol': 0,
                    't_ms': params['t_rev_msec_dec'],
                    't_us': params['t_rev_usec_dec'],
                    'id': params['id'],
                    'sign': modes['rev']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['rev_dec_countr']):
                for vol in rev_dec:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # инкремент dir
            data = {'vol': 0,
                    't_ms': params['t_dir_msec_inc'],
                    't_us': params['t_dir_usec_inc'],
                    'id': params['id'],
                    'sign': modes['dir']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['dir_inc_countr']):
                for vol in dir_inc:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # декремент dir
            data = {'vol': 0,
                    't_ms': params['t_dir_msec_dec'],
                    't_us': params['t_dir_usec_dec'],
                    'id': params['id'],
                    'sign': modes['dir']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            for _ in range(params['dir_dec_countr']):
                for vol in dir_dec:
                    task = []
                    data['vol'] = vol
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
