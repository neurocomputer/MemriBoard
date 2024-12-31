"""
Тестовый генератор-декомпозитор
"""

from typing import Generator
from manager.blanks import blanks, fill_blank
from manager.terminate import terminators

def get_tst(params: dict, terminate: dict, blank_type: str) -> Generator[list, None, None]:
    """
    Тестовый генератор-декомпозитор
    """

    terminator = terminators[terminate['type']](terminate['value'])
    params['id'] = 1
    for _ in range(params['count']):
        task = []
        task.append(fill_blank(blanks[blank_type], params))
        task.append(terminator)
        params['id'] += 1
        yield task
