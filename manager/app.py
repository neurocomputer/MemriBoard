"""
Application
"""

# pylint: disable=W0401,W0614,R0902,C0321

import logging
from copy import deepcopy
from configparser import ConfigParser
from logging import Logger
from manager.menu import menu
from manager.model.db import DBOperate
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
    backup: str
    writable_cells: str
    lock_board_type: bool
    database_mode: str

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
        self.ap_logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(self.ap_log_path, mode=self.ap_config["logging"]["filemode"], encoding='utf-8')
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.ap_logger.addHandler(handler)
        # настраиваем логгер базы данных
        self.db_log_path = DB_LOG_PATH
        self.db_logger = logging.getLogger('db_logger')
        self.db_logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(self.db_log_path, mode=self.ap_config["logging"]["filemode"], encoding='utf-8')
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.db_logger.addHandler(handler)
        # другие нужные подготовки
        self.menu = menu
        self.db = DBOperate(parent=self)

    def read_settings(self) -> None:
        """
        Прочитать настройки платы
        """
        self.ap_config.read(self.ap_config_path, encoding="utf-8")  # читаем конфиг
        self.connected_port = self.ap_config['connector']['com_port']
        self.board_type = self.ap_config['board']['board_type']
        self.backup = self.ap_config['database']['backup_path']
        # для отдельных настроек создаем алиасы
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
        if "lock_board_type" in kwargs:
            self.ap_config['gui']['lock_board_type'] = kwargs["lock_board_type"]
        if "database_mode" in kwargs:
            self.ap_config['database']['database_mode'] = kwargs["database_mode"]
        # запись в файл
        with open(self.ap_config_path, 'w', encoding='utf-8') as configfile:
            self.ap_config.write(configfile)
        self.read_settings()

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
        meta_info['lock_board_type'] = self.lock_board_type
        meta_info['database_mode'] = self.database_mode
        return deepcopy(meta_info)
