"""
Режимы работы с платой
"""

from manager.modes.tst import get_tst  # noqa: F401
from manager.modes.std import get_std  # mode_7 (или mode_2)  # noqa: F401
from manager.modes.smu import SMUGen  # Modes for SMUs  # noqa: F401

# todo: по правильному mode_9 и mode_mvm должны быть тоже здесь
