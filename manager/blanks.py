"""
Бланки задач

Можно под конкретную плату задать новый тип бланка
и заполнить его данными и сформировать команду для платы
"""

def fill_blank(blank: dict, data: dict) -> dict:
    """
    Заполнить бланк

    Arguments:
        blank -- пустой бланк
        data -- данные для внесения в бланк

    Returns:
        task -- заполненный бланк
    """
    task = blank.copy()
    for key in task:
        if key in data.keys():
            task[key] = data[key]
    return task

def gather(blank: dict) -> str:
    """
    Собрать из словаря строковую команду
    ВАЖНО! Потенциальный источнк ошибки, поскольку словарь
    не упорядоченный тип данных и команда может собраться не в том порядке :-(

    Arguments:
        blank -- заполненный бланк тикета

    Returns:
        строковая команда
    """
    return ','.join(map(str, list(blank.values()))) + '\n'

blanks = {
    'memardboard': { # бланк задачи для платы MemArdBoard
    'mode_flag': 2,
    'vol': 0,
    't_ms': 0,
    't_us': 0,
    'sign': 0,
    'id': 0},

    'memardboard_crossbar': { # бланк задачи для кроссбара
    'mode_flag': 7,
    'vol': 0,
    't_ms': 0,
    't_us': 0,
    'sign': 0,
    'id': 0,
    'wl': 0,
    'bl': 0},

    'debug': { # бланк задачи для отладки
    'mode_flag': 2,
    'vol': 0,
    't_ms': 0,
    't_us': 0,
    'sign': 0,
    'id': 0},

    'debug_crossbar': { # бланк задачи для отладки кроссбара
    'mode_flag': 7,
    'vol': 0,
    't_ms': 0,
    't_us': 0,
    'sign': 0,
    'id': 0,
    'wl': 0,
    'bl': 0},

    }
