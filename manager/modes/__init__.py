"""
Режимы работы с платой
"""

from manager.modes.tst import get_tst  # noqa: F401
from manager.modes.std import get_std # mode_7 (или mode_2)  # noqa: F401
from manager.modes.smu import (  # Modes for SMUs  # noqa: F401
    get_smu_iv_dc, 
    get_smu_std,
    get_smu_pulsed_retention,
    get_smu_endurance,
    get_visa_crossbar_scan,
)

# todo: по правильному mode_9 и mode_mvm должны быть тоже здесь
