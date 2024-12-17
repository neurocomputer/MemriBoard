"""
Меню режимов
"""
from manager.modes import get_tst, get_std

menu: dict = {
        'tst': get_tst,
        'std': get_std
    }
