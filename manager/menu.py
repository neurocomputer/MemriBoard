"""
Меню режимов
"""
from manager.modes import get_tst, get_std, get_smu_iv_dc

menu: dict = {
        'tst': get_tst,
        'std': get_std,
        'smu_iv_dc': get_smu_iv_dc
    }
