'''
Обработчик тикета c ticket['mode'] == 'std' для устройств с board_type == 'VISA'
'''

from typing import Generator
from manager.blanks import blanks, fill_blank
from manager.terminate import terminators

def get_visa(params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
    """
    Стандартный генератор-декомпозитор
    """
    bl = params['bl']
    wl = params['wl']

    modes = {'dir': 0,
             'rev': 1}
    terminator = terminators[terminate['type']](terminate['value'])

    # 1 открытие ячейки
    task = {'mode_flag': 12,
            'request': f'открыть ячейку bl={bl} wl={wl}',
            'id': 0}
    yield [task, terminator]

    # 2 посылка положительной части
    # формирование положительной части

    task = {'mode_flag': 13,
            'request': f'полное описание задачи в нотации visa для положительной части',
            'id': 0}
    counter = 5 # определение того, сколько запросить ответов
    yield [task, terminator]

    # 3 запрос ответа
    data = {'vol': 0,
            't_ms': params['t_dir_msec_inc'],
            't_us': params['t_dir_usec_inc'],
            'id': params['id'],
            'sign': modes['dir']}
    if 'wl' in params and 'bl' in params:
        data['wl'] = params['wl']
        data['bl'] = params['bl']
    for _ in range(counter):
        task = []
        data['vol'] = 1
        task.append(fill_blank(blanks[blank_type], data))
        task.append(terminator)
        yield task

    # 4 посылка отрицательной части
    task = {'mode_flag': 13,
            'request': f'полное описание задачи в нотации visa для отрицательной части',
            'id': 0}
    counter = 5 # определение того, сколько запросить ответов
    yield [task, terminator]

    # 5 запрос ответа
    data = {'vol': 0,
            't_ms': params['t_dir_msec_inc'],
            't_us': params['t_dir_usec_inc'],
            'id': params['id'],
            'sign': modes['rev']}
    if 'wl' in params and 'bl' in params:
        data['wl'] = params['wl']
        data['bl'] = params['bl']
    for _ in range(counter):
        task = []
        data['vol'] = 1
        task.append(fill_blank(blanks[blank_type], data))
        task.append(terminator)
        yield task

    # 6 закрытие ячейки
    task = {'mode_flag': 12,
            'request': f'закрыть ячейку bl={bl} wl={wl}',
            'id': 0}
    yield [task, terminator]
