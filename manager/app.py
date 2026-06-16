"""
Application
"""

# pylint: disable=W0401,W0614,R0902,C0321

import logging
import os
from copy import deepcopy
from configparser import ConfigParser
from logging import Logger
from io import StringIO
from typing import Union
from manager.menu import menu
from manager.model.db import DBOperate
from manager.service.templates import TEMPLATE_INI
from manager.service.global_settings import LOG_PATH, SETTINGS_PATH, DB_LOG_PATH
from manager.service.prepare import prepare

class Application():
    """
    Application
    """

    ap_log_path: str # путь к логу
    ap_config_path: str # путь к конфигу
    ap_config: ConfigParser # конфиг
    ap_logger: Logger # логгер
    dac_bit: int # разрядность ЦАП
    vol_ref_dac: float # опорное напряжение ЦАП
    res_load: int # нагрузочный резистор
    vol_read: float # напряжение чтения
    adc_bit: int # разрядность АЦП
    vol_ref_adc: float # опорное напряжение АЦП
    res_switches: float # сопротивление переключателей
    gain: int # усиление
    sum_gain: int # сопротивление ОС
    menu: dict # меню режимов
    board_type: str # тип платы
    connected_port: str # com порт
    db: DBOperate
    status_db_connect: bool
    backup: str
    writable_cells: str
    language: str
    lock_board_type: bool
    database_mode: str
    new_config_keys: Union[None, list] = None

    def __init__(self) -> None:
        # это выполняется везде где есть наследование от Application и super().__init__()
        prepare()
        # чтение настроек
        self.ap_config_path = SETTINGS_PATH
        self.ap_config = ConfigParser() # создаём объекта парсера
        self.read_settings() # читаем настройки
        # настраиваем логгер приложения
        self.ap_log_path = LOG_PATH
        self.ap_logger = logging.getLogger(__name__)
        self.ap_logger.setLevel(self.ap_config['logging']['app_logging_level'].strip().upper())
        if eval(self.ap_config['logging']['app_log_rewrite_on_start']):  # Rewrite mode
            if os.path.isfile(self.ap_log_path):
                os.remove(self.ap_log_path)
            ap_log_path = self.ap_log_path
        else:
            ap_log_path = self.new_log_path(self.ap_log_path)
        handler = logging.FileHandler(ap_log_path, mode='w')
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.ap_logger.addHandler(handler)
        # настраиваем логгер базы данных
        self.db_log_path = DB_LOG_PATH
        self.db_logger = logging.getLogger('db_logger')
        self.db_logger.setLevel(self.ap_config['logging']['database_logging_level'].strip().upper())
        if eval(self.ap_config['logging']['database_log_rewrite_on_start']):  # Rewrite mode
            if os.path.isfile(self.db_log_path):
                os.remove(self.db_log_path)
            db_log_path = self.db_log_path    
        else:
            db_log_path = self.new_log_path(self.db_log_path)
        handler = logging.FileHandler(db_log_path, mode='w')
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.db_logger.addHandler(handler)
        # другие нужные подготовки
        self.menu = menu
        self.db = DBOperate(parent=self)
        status_db_connect = self.db.db_connect('app.__init__()')
        if not status_db_connect:
            assert 0 # нет подключения к БД
        self.db.db_disconnect('app.__init__()')

    def read_settings(self) -> None:
        """
        Прочитать настройки платы
        """
        self.ap_config.read(self.ap_config_path, encoding="utf-8")  # читаем конфиг
        # Сравниваем с template
        self.compare_settings_with_template()
        # для отдельных настроек создаем алиасы
        self.connected_port = self.ap_config['connector']['com_port']
        self.board_type = self.ap_config['board']['board_type']
        self.backup = self.ap_config['database']['backup_path']
        self.dac_bit = int(self.ap_config['board']['dac_bit'])
        self.vol_ref_dac = float(self.ap_config['board']['vol_ref_dac'])
        self.res_load = int(self.ap_config['board']['res_load'])
        self.vol_read = float(self.ap_config['board']['vol_read'])
        self.adc_bit = int(self.ap_config['board']['adc_bit'])
        self.vol_ref_adc = float(self.ap_config['board']['vol_ref_adc'])
        self.res_switches = float(self.ap_config['board']['res_switches'])
        self.gain = float(self.ap_config['board']['gain'])
        self.sum_gain = int(self.ap_config['board']['sum_gain'])
        self.soft_cc = float(self.ap_config['board']['soft_cc'])
        self.writable_cells = self.ap_config['gui']['writable_cells']
        self.language = self.ap_config['gui']['language']
        self.lock_board_type = eval(self.ap_config['gui']['lock_board_type'])
        self.database_mode = self.ap_config['database']['database_mode']

    def save_settings(self, **kwargs):
        """
        Сохранить настройки
        """
        if "adc_bit" in kwargs:
            self.ap_config['board']['adc_bit'] = kwargs["adc_bit"]
        if "gain" in kwargs:
            self.ap_config['board']['gain'] = kwargs["gain"]
        if "sum_gain" in kwargs:
            self.ap_config['board']['sum_gain'] = kwargs["sum_gain"]
        if "soft_cc" in kwargs:
            self.ap_config['board']['soft_cc'] = kwargs["soft_cc"]
        if "last_crossbar_serial" in kwargs:
            self.ap_config['gui']['last_crossbar_serial'] = kwargs["last_crossbar_serial"]
        if "com_port" in kwargs:
            self.ap_config['connector']['com_port'] = kwargs["com_port"]
        if "board_type" in kwargs:
            self.ap_config['board']['board_type'] = kwargs["board_type"]
        if "backup" in kwargs:
            self.ap_config['database']['backup_path'] = kwargs["backup"]
        if "writable_cells" in kwargs:
            self.ap_config['gui']['writable_cells'] = kwargs["writable_cells"]
        if "language" in kwargs:
            self.ap_config['gui']['language'] = kwargs["language"]
        if "lock_board_type" in kwargs:
            self.ap_config['gui']['lock_board_type'] = kwargs["lock_board_type"]
        if 'app_logging_level' in kwargs:
            self.ap_config['logging']['app_logging_level'] = kwargs['app_logging_level']
            if hasattr(self, 'ap_logger'):
                self.ap_logger.setLevel(kwargs['app_logging_level'])
        if 'db_logging_level' in kwargs:
            self.ap_config['logging']['database_logging_level'] = kwargs['db_logging_level']
            if hasattr(self, 'db_logger'):
                self.db_logger.setLevel(kwargs['db_logging_level'])
        if 'app_log_rewrite_on_start' in kwargs:
            self.ap_config['logging']['app_log_rewrite_on_start'] = kwargs['app_log_rewrite_on_start']
        if 'db_log_rewrite_on_start' in kwargs:
            self.ap_config['logging']['database_log_rewrite_on_start'] = kwargs['db_log_rewrite_on_start']
        if "database_mode" in kwargs:
            self.ap_config['database']['database_mode'] = kwargs["database_mode"]
        # запись в файл
        with open(self.ap_config_path, 'w', encoding='utf-8') as configfile:
            self.ap_config.write(configfile)
        self.read_settings()
        
    def compare_settings_with_template(self) -> None:
        """
        Сравниваем настройки с template и дополняем, если не хватает
        """
        # Creating config object from template
        buffer = StringIO(TEMPLATE_INI)
        template_config = ConfigParser()
        template_config.read_file(buffer)
        buffer.close()
        # Comparing configs
        new_keys = []  # List of new keys to put in the warning
        for section in template_config.sections():
            if section not in self.ap_config.sections():
                self.ap_config.add_section(section)
            for key in template_config[section]:
                if key not in self.ap_config[section]:
                    val = template_config[section][key]
                    self.ap_config[section][key] = val
                    new_keys.append(f'[{section}] {key} = {val}')
        if len(new_keys) != 0:
            self.new_config_keys = new_keys
            # Перезаписываем settings.ini
            with open(self.ap_config_path, 'w', encoding='utf-8') as file:
                self.ap_config.write(file)

    def get_meta_info(self):
        """
        Вернуть словарь с метаинформацией
        """
        meta_info = {}
        meta_info['board_type'] = self.board_type
        meta_info['dac_bit'] = self.dac_bit
        meta_info['adc_bit'] = self.adc_bit
        meta_info['gain'] = self.gain
        meta_info['sum_gain'] = self.sum_gain
        meta_info['soft_cc'] = self.soft_cc
        meta_info['vol_ref_dac'] = self.vol_ref_dac
        meta_info['vol_ref_adc'] = self.vol_ref_adc
        meta_info['vol_read'] = self.vol_read
        meta_info['res_load'] = self.res_load
        meta_info['res_switches'] = self.res_switches
        meta_info['connected_port'] = self.connected_port
        meta_info['backup'] = self.backup
        meta_info['writable_cells'] = self.writable_cells
        meta_info['language'] = self.language
        meta_info['lock_board_type'] = self.lock_board_type
        meta_info['app_logging_level'] = self.ap_config['logging']['app_logging_level'].strip().upper()
        meta_info['db_logging_level'] = self.ap_config['logging']['database_logging_level'].strip().upper()
        meta_info['app_log_rewrite_on_start'] = self.ap_config['logging']['app_log_rewrite_on_start']
        meta_info['db_log_rewrite_on_start'] = self.ap_config['logging']['database_log_rewrite_on_start']
        meta_info['database_mode'] = self.database_mode
        return deepcopy(meta_info)
    
    def new_log_path(self, log_path: str) -> str:
        """
        Find last log index and return index of the new log
        """
        last_name = 0
        keyword = os.path.basename(log_path).rsplit('.', 1)[0]
        for name in os.listdir(os.path.dirname(log_path)):
            if name.endswith('.log') and name.startswith(keyword):
                name_spl = name.rsplit('.', 2)  # ['app', '2', 'log'] or ['app', 'log']
                if len(name_spl) == 3:
                    try:
                        if int(name_spl[1]) > last_name:
                            last_name = int(name_spl[1])
                    except Exception:
                        pass
        return os.path.join(os.path.dirname(log_path), f'{keyword}.{last_name+1}.log')
    