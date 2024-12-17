"""
Подготовка программы при первом запуске
"""

# pylint: disable=W0401

import os
from manager.service.global_settings import SETTINGS_PATH, DB_PATH, RESULTS_PATH
from manager.model.src import create_empty_db
from manager.service.templates import TEMPLATE_INI

def prepare():
    """
    Подготовка
    """
    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as file:
            file.write(TEMPLATE_INI)
    if not os.path.exists(DB_PATH):
        create_empty_db(DB_PATH)
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError
    # if not os.path.exists(RESULTS_PATH):
    #     os.mkdir(RESULTS_PATH)
