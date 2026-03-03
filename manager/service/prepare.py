"""
Подготовка программы при первом запуске
"""

# pylint: disable=W0401

import os
from manager.service.global_settings import SETTINGS_PATH
from manager.service.templates import TEMPLATE_INI

def prepare():
    """
    Подготовка
    """
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as file:
            file.write(TEMPLATE_INI)