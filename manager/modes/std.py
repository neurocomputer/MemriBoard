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
from collections.abc import Generator
from manager.blanks import blanks, fill_blank
from manager.terminate import terminators

def get_std(signal_mode: str, params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
    """
    Стандартный генератор-декомпозитор
    """
    modes = {'dir': 0,
             'rev': 1}
    terminator = terminators[terminate['type']](terminate['value'])
    
    # Preparing based on the mode
    if signal_mode == 'volt_sweep':
        # инкремент dir
        try:
            dir_inc = np.arange(params['start_dir'],
                                params['stop_dir'] + params['step_dir'],
                                params['step_dir'])
        except ZeroDivisionError:
            dir_inc = [0]
        # декремент dir
        if params['double_dir']:
            dir_dec = dir_inc[::-1]
        else:
            dir_dec = []
        # инкремент rev
        try:
            rev_inc = np.arange(params['start_rev'],
                                params['stop_rev'] + params['step_rev'],
                                params['step_rev'])
        except ZeroDivisionError:
            rev_inc = [0]
        # декремент rev
        if params['double_rev']:
            rev_dec = rev_inc[::-1]
        else:
            rev_dec = []
        # Other parameters
        pulse_width_dir = params['pulse_width_dir']
        pulse_width_rev = params['pulse_width_rev']
        amount_dir = params['amount_dir']
        amount_rev = params['amount_rev']
    elif signal_mode in ['endurance', 'pot-dep']:
        dir_inc = [params['amplitude_dir']]
        dir_dec = []
        rev_inc = [params['amplitude_rev']]
        rev_dec = []
        pulse_width_dir = params['pulse_width_dir']
        pulse_width_rev = params['pulse_width_rev']
        amount_dir = params['amount_dir']
        amount_rev = params['amount_rev']
    elif signal_mode == 'retention':
        dir_inc = [0]
        dir_dec = []
        rev_inc = []
        rev_dec = []
        pulse_width_dir = 0
        pulse_width_rev = 0
        amount_dir = 1
        amount_rev = 0
    else:
        raise RuntimeError(f'std Generator: unknown signal mode {signal_mode}')
        
    # Generating
    
    for _ in range(params['count']):
        # порядок dir-rev
        if not params['reverse']:
            data = {'vol': 0,
                    'pulse_width': pulse_width_dir,
                    'id': params['id'],
                    'sign': modes['dir']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            # dir
            for _ in range(amount_dir):
                # inc dir
                for vol in dir_inc:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
                # dec dir
                for vol in dir_dec:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # rev
            data['vol'] = 0
            data['pulse_width'] = pulse_width_rev
            data['sign'] = modes['rev']
            for _ in range(amount_rev):
                # inc rev
                for vol in rev_inc:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
                # dec rev
                for vol in rev_dec:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
                    
        # порядок rev-dir
        else:
            data = {'vol': 0,
                    'pulse_width': pulse_width_rev,
                    'id': params['id'],
                    'sign': modes['rev']}
            if 'wl' in params and 'bl' in params:
                data['wl'] = params['wl']
                data['bl'] = params['bl']
            # rev
            for _ in range(amount_rev):
                # inc rev
                for vol in rev_inc:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
                # dec rev
                for vol in rev_dec:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
            # dir
            data['vol'] = 0
            data['pulse_width'] = pulse_width_dir
            data['sign'] = modes['dir']
            for _ in range(amount_dir):
                # inc dir
                for vol in dir_inc:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
                # dec dir
                for vol in dir_dec:
                    task = []
                    data['vol'] = abs(vol)
                    task.append(fill_blank(blanks[blank_type], data))
                    task.append(terminator)
                    yield task
