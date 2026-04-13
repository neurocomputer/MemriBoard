"""
Режимы работы с платой
"""

from manager.modes.tst import get_tst
from manager.modes.std import get_std # mode_7 (или mode_2)
from manager.modes.smu import (  # Modes for SMUs
    get_smu_iv_dc, 
    get_smu_std,
    get_smu_pulsed_retention,
    get_smu_endurance
)

# todo: по правильному mode_9 и mode_mvm должны быть тоже здесь
